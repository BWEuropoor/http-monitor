import datetime
import random

import pytest

from src.log_parser import Parser
from src.metrics import MetricsAggregator

# Freeze the start time at the package load time, we don't want tests randomly
# failing if some operations take abnormally long.
START_TIME = datetime.datetime.now(datetime.timezone.utc)
BASE_DATA_POINT = {
    "remote_host": "127.0.0.1",
    "remote_logname": "jill",
    "request_method": "GET",
    "request_url": "/api/user",
    "request_url_path": "/api/user",
    "request_url_subpath": "/api",
    "response_bytes_clf": "234",
    "status": "200",
    "time_received_utc_datetimeobj": START_TIME,
}


@pytest.fixture
def parser():
    return Parser.make_parser()


@pytest.fixture
def metrics():
    return MetricsAggregator(
        reporting_window=5,
        alert_threshold=10,
        bucket_size=1,
        alert_error_rate=0.05,
        ddos_threshold=7.5,
    )


def make_requests(
    success=0, redirect=0, not_found=0, error=0, timedelta=0, random_ip=True
):
    """Helper for mass producing parsed HTTP logs."""
    return [
        {
            **BASE_DATA_POINT,
            **{
                "remote_host": (
                    ".".join(str(random.randint(0, 255)) for _ in range(4))
                    if random_ip
                    else "127.0.0.1"
                ),
                "status": status,
                "time_received_utc_datetimeobj": BASE_DATA_POINT[
                    "time_received_utc_datetimeobj"
                ]
                + datetime.timedelta(seconds=timedelta),
            },
        }
        for (status, count) in zip(
            ["200", "300", "400", "500"], [success, redirect, not_found, error]
        )
        for i in range(count)
    ]
