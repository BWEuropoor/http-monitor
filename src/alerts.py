import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .metrics import MetricBucket


class AlertBase:
    ALERT = "ALERT"
    RECOVERED = "RECOVERED"

    def __init__(self):
        self.status = None
        self.message = None

    @property
    def is_active(self):
        return self.status == AlertBase.ALERT

    def get_alert_status(self, stats: "MetricBucket"):
        raise NotImplementedError

    def as_message(self):
        return {
            "type": self.TYPE,
            "status": self.status,
            "message": self.message,
            "time": time.strftime("%H:%M:%S"),
        }


class TrafficAlert(AlertBase):
    TYPE = "TRAFFIC_ALERT"

    def __init__(self, reporting_window: float, alert_threshold: float):
        super().__init__()
        self.alert_threshold = alert_threshold
        self.reporting_window = reporting_window

    def get_alert_status(self, stats):
        if stats.traffic >= self.alert_threshold * self.reporting_window:
            if not self.is_active:
                self.status = TrafficAlert.ALERT
                self.message = (
                    "Traffic above threshold - {} hits in the last {} seconds".format(
                        stats.traffic,
                        self.reporting_window,
                    )
                )
                return self.as_message()

        elif self.is_active:
            self.status = TrafficAlert.RECOVERED
            self.message = "Traffic returned to normal range"
            return self.as_message()


class ErrorRateAlert(AlertBase):
    TYPE = "ERROR_RATE_ALERT"

    def __init__(self, reporting_window: float, error_threshold: float):
        super().__init__()
        self.reporting_window = reporting_window
        self.error_threshold = error_threshold

    def get_alert_status(self, stats):
        if not stats.traffic:
            return

        error_rate = stats.traffic_by_status_code.get("500s", 0) / stats.traffic
        if error_rate >= self.error_threshold:
            if not self.is_active:
                self.status = ErrorRateAlert.ALERT
                self.message = (
                    "Error rate above threshold - {} ({:.0f}%)"
                    " errors in the last {} seconds"
                ).format(
                    stats.traffic_by_status_code["500s"],
                    error_rate * 100,
                    self.reporting_window,
                )
                return self.as_message()

        elif self.is_active:
            self.status = ErrorRateAlert.RECOVERED
            self.message = "Error rate returned to normal range"
            return self.as_message()


class DdosAlert(AlertBase):
    TYPE = "DDOS_ALERT"

    def __init__(self, reporting_window: float, visits_threshold: float):
        super().__init__()
        self.reporting_window = reporting_window
        self.visits_threshold = visits_threshold

    def get_alert_status(self, stats: "MetricBucket"):
        if not stats.traffic:
            return

        most_popular_ip = max(stats.traffic_by_ip.keys(), key=stats.traffic_by_ip.get)
        if stats.traffic_by_ip[most_popular_ip] >= self.visits_threshold:
            if not self.is_active:
                self.status = DdosAlert.ALERT
                self.message = (
                    "{} requests above threshold - {} ({:.0f}%"
                    " total traffic) in the last {} seconds"
                ).format(
                    most_popular_ip,
                    stats.traffic_by_ip[most_popular_ip],
                    (stats.traffic_by_ip[most_popular_ip] / stats.traffic) * 100,
                    self.reporting_window,
                )
                return self.as_message()

        elif self.is_active:
            self.status = DdosAlert.RECOVERED
            self.message = "User-specific requests returned to normal range"
            return self.as_message()
