import argparse
import os
import random
import time


def validate_path(path):
    if not isinstance(path, str):
        raise argparse.ArgumentTypeError("Path should be of str type.")

    if not path.endswith(".log"):
        raise argparse.ArgumentTypeError("Output file should have '.log' extension.")

    folder_path = path.rsplit("/", 1)[0]
    if not os.path.exists(folder_path):
        raise argparse.ArgumentTypeError(
            "Output folder '{}' doesn't exist.".format(folder_path)
        )
    return path


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        default="./access.log",
        type=validate_path,
        help="Path to the log file",
    )
    parser.add_argument(
        "-r",
        "--reporting-window",
        default=120,
        type=float,
        help="Reporting time between statistics display (seconds)",
    )
    parser.add_argument(
        "-t",
        "--alert-threshold",
        default=10,
        type=float,
        help="High traffic alert threshold (requests/seconds)",
    )
    parser.add_argument(
        "-d",
        "--ddos-threshold",
        default=2.5,
        type=float,
        help="DDOS alert threshold (requests/seconds)",
    )
    parser.add_argument(
        "-w",
        "--alert-monitoring-window",
        default=1,
        type=float,
        help="Window for monitoring changes in alerts status (seconds)",
    )
    parser.add_argument(
        "-b",
        "--bucket-size",
        default=1,
        type=float,
        help="Size of the bucket we'll aggregate traffic numbers into (seconds)",
    )
    parser.add_argument(
        "-e",
        "--alert-error-rate",
        default=0.05,
        type=float,
        help="High errors alert threshold (ko/(ok + ko))",
    )
    parser.add_argument(
        "-g", "--give-me-traffic", action="store_true", help="Simulate traffic"
    )

    return parser.parse_args()


def simulate_traffic(file_path: str):
    """Simulate real-life traffic.

    Every second we'll add a random list of 0-20 entries to provided file's path.

    Args:
        file_path (str): Path to the log file.

    """
    print("Starting traffic simulation", flush=True)
    ips = [".".join(str(random.randint(0, 255)) for _ in range(4)) for i in range(20)]
    logins = [
        "king-arthur",
        "black-knight",
        "bridgekeeper",
        "african-swallow",
        "european-swallow",
        "lancelot",
        "sir-robin",
    ]
    endpoints = [
        "/api",
        "/",
        "/users/list",
        "/api/v2",
        "/list",
    ]
    status_codes = ["200", "201", "300", "301", "400", "500"]

    while True:
        time.sleep(1)
        with open(file_path, "a+") as f:
            current_time = time.strftime("%d/%b/%Y:%H:%M:%S %z")
            lines = [
                """{} - {} [{}] "GET {} HTTP/1.0" {} 234\n""".format(
                    random.choice(ips),
                    random.choice(logins),
                    current_time,
                    random.choice(endpoints),
                    random.choice(status_codes),
                )
                for i in range(0, random.randint(0, 20))
            ]
            f.writelines(lines)
