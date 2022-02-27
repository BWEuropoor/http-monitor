import os
from time import sleep

from src.helpers import parse_command_line, simulate_traffic
from src.http_monitor import HTTPMonitor


def main():
    args = parse_command_line()

    controller = HTTPMonitor(
        path=args.path,
        reporting_window=args.reporting_window,
        alert_threshold=args.alert_threshold,
        bucket_size=args.bucket_size,
        alert_error_rate=args.alert_error_rate,
        alert_monitoring_window=args.alert_monitoring_window,
        ddos_threshold=args.ddos_threshold,
    )
    controller.start()
    print("HTTPMonitoring started.")

    if args.give_me_traffic:
        try:
            simulate_traffic(args.path)
        except KeyboardInterrupt:
            print("Traffic simulation stopped.", flush=True)

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Stopping the HTTPMonitoring.", flush=True)
        os._exit(0)


if __name__ == "__main__":
    main()
