from threading import Thread
from time import sleep
from typing import List

from .display import Display
from .file_observer import FileObserver
from .log_parser import Parser
from .metrics import MetricsAggregator


class HTTPMonitor:
    def __init__(
        self,
        path: str,
        reporting_window: float,
        alert_threshold: float,
        bucket_size: float,
        alert_error_rate: float,
        alert_monitoring_window: float,
        ddos_threshold: float,
    ):
        # Initial configuration
        self.file = path
        self.alert_threshold = alert_threshold
        self.reporting_window = reporting_window
        self.bucket_size = bucket_size
        self.alert_monitoring_window = alert_monitoring_window

        # Child objects
        self.parser = Parser.make_parser()
        self.display = Display()
        self.metrics = MetricsAggregator(
            reporting_window,
            alert_threshold,
            bucket_size,
            alert_error_rate,
            ddos_threshold,
        )

        # Initialize observers
        self._metrics_reporting_thread = Thread(target=self.report_metrics)
        self.file_observer = FileObserver(path, self)
        self._alerts_reporting_thread = Thread(target=self.report_alerts)

    def start(self):
        self._metrics_reporting_thread.start()
        self.file_observer.start()
        self._alerts_reporting_thread.start()

    def report_metrics(self):
        try:
            while True:
                sleep(self.reporting_window)
                stats = self.metrics.get_stats()
                self.display.send_stats(stats, self.reporting_window)
        except KeyboardInterrupt:
            pass

    def report_alerts(self):
        try:
            while True:
                sleep(self.alert_monitoring_window)
                for alert in self.metrics.get_alerts():
                    self.display.send_alert(alert)
        except KeyboardInterrupt:
            pass

    def add_lines(self, lines: List[str]):
        for line in lines:
            if not line:
                continue

            try:
                data = self.parser(line)
                self.metrics.add(data)
            except Exception as e:
                self.display.warn("Error in log parsing:", e)
