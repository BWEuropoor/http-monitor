import time
from typing import Dict

from colorama import Fore, Style

from .alerts import AlertBase


class Display:
    TOP_IP = 5
    TOP_ENDPOINTS = 5

    def warn(self, msg, e):
        print(
            "{time} {formatting_start}{alert_type}{formatting_end}: {error}".format(
                time=time.strftime("%H:%M:%S"),
                formatting_start=Fore.YELLOW,
                alert_type=msg,
                formatting_end=Style.RESET_ALL,
                error=e,
            ),
            flush=True,
        )

    def send_stats(self, stats, reporting_window: float):
        message = [
            "STATS:",
            " - total traffic in the last {time}s: {hits}".format(
                time=reporting_window, hits=stats["traffic"]
            ),
            " - by status code:",
        ]

        for status_code, hits in sorted(stats["traffic_by_status_code"].items()):
            message.append(f"    {status_code} - {hits}")

        message.append(f" - TOP {Display.TOP_ENDPOINTS} by endpoint:".format())
        for i, (endpoint, hits) in enumerate(
            sorted(
                stats["traffic_by_endpoint"].items(),
                key=lambda endpoint_hits: -endpoint_hits[1],
            )
        ):
            if i == Display.TOP_ENDPOINTS:
                break
            message.append(f"    {endpoint} - {hits}")

        message.append(f" - TOP {Display.TOP_IP} by ip:".format())
        for i, (ip, hits) in enumerate(
            sorted(
                stats["traffic_by_ip"].items(), key=lambda hits_per_ip: -hits_per_ip[1]
            )
        ):
            if i == Display.TOP_IP:
                break
            message.append(f"    {ip} - {hits}")

        print("\n".join(message), flush=True)

    def send_alert(self, alert: Dict[str, str]):
        print(
            "{time} - {alert_color}{alert_type}{alert_color_end} {alert_message}".format(
                time=alert["time"],
                alert_color=(
                    Fore.GREEN if alert["status"] == AlertBase.RECOVERED else Fore.RED
                ),
                alert_type=alert["status"],
                alert_color_end=Style.RESET_ALL,
                alert_message=alert["message"],
            ),
            flush=True,
        )
