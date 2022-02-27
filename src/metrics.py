import time
from collections import Counter, defaultdict, deque
from typing import Deque, Dict, List, Type, Union

from .alerts import DdosAlert, ErrorRateAlert, TrafficAlert

StatsDictValues = Union[int, Dict[str, int]]


def get_status_code_bucket(status: str) -> str:
    """Match status code with it's bucket.

    Example:
        '200' => '200s',
        '204' => '200s',
        '301' => '300s',

    """
    return "{}00s".format(status[0])


class MetricBucket:
    def __init__(
        self,
        timestamp: float = 0,
        traffic: int = 0,
        traffic_by_status_code: Dict[str, int] = None,
        traffic_by_endpoint: Dict[str, int] = None,
        traffic_by_ip: Dict[str, int] = None,
    ):
        self.timestamp = timestamp
        self.traffic = traffic
        self.traffic_by_status_code = (
            defaultdict(int) if not traffic_by_status_code else traffic_by_status_code
        )
        self.traffic_by_endpoint = (
            defaultdict(int) if not traffic_by_endpoint else traffic_by_endpoint
        )
        self.traffic_by_ip = defaultdict(int) if not traffic_by_ip else traffic_by_ip

    def __add__(self, other):
        return MetricBucket(
            max(self.timestamp, other.timestamp),
            self.traffic + other.traffic,
            dict(
                Counter(self.traffic_by_status_code)
                + Counter(other.traffic_by_status_code)
            ),
            dict(
                Counter(self.traffic_by_endpoint) + Counter(other.traffic_by_endpoint)
            ),
            dict(Counter(self.traffic_by_ip) + Counter(other.traffic_by_ip)),
        )

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return MetricBucket(
            max(self.timestamp, other.timestamp),
            self.traffic - other.traffic,
            defaultdict(
                int,
                Counter(self.traffic_by_status_code)
                - Counter(other.traffic_by_status_code),
            ),
            defaultdict(
                int,
                Counter(self.traffic_by_endpoint) - Counter(other.traffic_by_endpoint),
            ),
            defaultdict(
                int, Counter(self.traffic_by_ip) - Counter(other.traffic_by_ip)
            ),
        )

    def __rsub__(self, other):
        return self.__rsub__(other)

    def as_dict(self) -> Dict[str, StatsDictValues]:
        return {
            "traffic": self.traffic,
            "traffic_by_status_code": self.traffic_by_status_code,
            "traffic_by_endpoint": self.traffic_by_endpoint,
            "traffic_by_ip": self.traffic_by_ip,
        }

    def add_user(self, data: Dict[str, str]):
        self.traffic += 1
        status_code = get_status_code_bucket(data["status"])
        self.traffic_by_status_code[status_code] += 1
        self.traffic_by_endpoint[data["request_url_subpath"]] += 1
        self.traffic_by_ip[data["remote_host"]] += 1


def remove_outdated_data(func):
    def wrapper(instance, *args, **kwargs):
        instance._remove_outdated_data()
        return func(instance, *args, **kwargs)

    return wrapper


class MetricsAggregator:
    def __init__(
        self,
        reporting_window: float,
        alert_threshold: float,
        bucket_size: float,
        alert_error_rate: float,
        ddos_threshold: float,
    ):
        # Initial configuration
        self.alert_threshold = alert_threshold
        self.reporting_window = reporting_window
        self.bucket_size = bucket_size

        # Session-specific variables
        self.traffic_queue: Deque[Type[MetricBucket]] = deque()
        self.stats = MetricBucket()

        # Register all active alerts
        self.alerts = [
            TrafficAlert(reporting_window, alert_threshold),
            ErrorRateAlert(reporting_window, alert_error_rate),
            DdosAlert(reporting_window, ddos_threshold),
        ]

    @remove_outdated_data
    def get_stats(self) -> Dict[str, StatsDictValues]:
        return self.stats.as_dict()

    def get_aggregated_timestamp(self, timestamp: float) -> int:
        """Get bucket for a timestamp.

        We aggregate events to reduce memory usage/computation. Default aggregation is every 1s,
        however it can be configured via `bucket-size` parameter.

        Args:
            timestamp (int): Epoch of HTTP log.

        Example:
            We aggregate logs every 5 seconds, then consider following epoch's :
            - 8 falls into 5 bucket
            - 23 if falls into 20 bucket
            - n fallls into n - n % self.bucket_size

        """
        return int(timestamp - timestamp % self.bucket_size)

    @remove_outdated_data
    def add(self, data):
        timestamp = self.get_aggregated_timestamp(
            data["time_received_utc_datetimeobj"].timestamp()
        )
        if not self.traffic_queue or self.traffic_queue[-1].timestamp != timestamp:
            # If time is 5, and our bucket_size is
            self.traffic_queue.append(MetricBucket(timestamp * self.bucket_size))

        # Double addition as self.stats is a sum of all objects inside self.traffic.queue
        # It'll be faster this way than substracting old, and then adding new object to self.stats
        self.traffic_queue[-1].add_user(data)
        self.stats.add_user(data)

    @remove_outdated_data
    def get_alerts(self) -> List[Dict[str, str]]:
        alerts = []
        for alert in self.alerts:
            alert_status_changed = alert.get_alert_status(self.stats)
            if alert_status_changed:
                alerts.append(alert_status_changed)

        return alerts

    def get_current_timestamp(self) -> float:
        return time.time()

    def _remove_outdated_data(self):
        while (
            self.traffic_queue
            and (self.get_current_timestamp() - self.traffic_queue[0].timestamp)
            > self.reporting_window
        ):
            outdated_data = self.traffic_queue.popleft()
            self.stats -= outdated_data
