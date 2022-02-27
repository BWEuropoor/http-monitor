import datetime

from src.alerts import DdosAlert, ErrorRateAlert, TrafficAlert

from .conftest import START_TIME, make_requests


def test_metrics_aggregation(metrics):
    """Basic usecase - check if metrics aggregate correctly."""
    for data in make_requests(success=15, redirect=3, not_found=2, error=5):
        metrics.add(data)

    expected = {
        "traffic": 25,
        "traffic_by_status_code": {
            "200s": 15,
            "300s": 3,
            "400s": 2,
            "500s": 5,
        },
    }
    actual = metrics.get_stats()

    assert actual["traffic"] == expected["traffic"]
    for (k, v) in expected["traffic_by_status_code"].items():
        assert actual["traffic_by_status_code"][k] == v


def test_metrics_no_alert(metrics):
    """Basic usecase - no alert."""
    for data in make_requests(success=15, redirect=3, not_found=2, error=0):
        metrics.add(data)

    assert len(metrics.get_alerts()) == 0


def test_metrics_traffic_alert(metrics):
    """Submit 145 requests within 5 seconds and check for TrafficAlert."""
    for data in make_requests(success=90, redirect=30, not_found=20, error=5):
        metrics.add(data)

    alerts = metrics.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["type"] == TrafficAlert.TYPE
    assert alerts[0]["status"] == TrafficAlert.ALERT


def test_metrics_error_alert(metrics):
    """Report 20% requests with 500s andd check for ErrorRateAlert"""
    for data in make_requests(success=20, redirect=0, not_found=0, error=5):
        metrics.add(data)

    alerts = metrics.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["type"] == ErrorRateAlert.TYPE
    assert alerts[0]["status"] == ErrorRateAlert.ALERT


def test_metrics_ddos_alert(metrics):
    """Make 40 requests from the same IP and check if the DDOS alert goes on."""
    for data in make_requests(
        success=40, redirect=0, not_found=0, error=1, random_ip=False
    ):
        metrics.add(data)

    alerts = metrics.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["type"] == DdosAlert.TYPE
    assert alerts[0]["status"] == DdosAlert.ALERT


def test_metrics_alert_recoveres_without_traffic(metrics):
    for data in make_requests(success=90, redirect=30, not_found=20, error=0):
        metrics.add(data)

    alerts = metrics.get_alerts()
    assert (
        len(alerts) == 1
        and alerts[0]["type"] == TrafficAlert.TYPE
        and alerts[0]["status"] == TrafficAlert.ALERT
    )

    # Move 5 seconds forward
    metrics.get_current_timestamp = lambda: (
        START_TIME + datetime.timedelta(seconds=5)
    ).timestamp()

    alerts = metrics.get_alerts()
    assert (
        len(alerts) == 1
        and alerts[0]["type"] == TrafficAlert.TYPE
        and alerts[0]["status"] == TrafficAlert.RECOVERED
    )


def test_metrics_alert_recoveres_with_traffic(metrics):
    # 1st second, submit 25 requests
    for data in make_requests(success=20, redirect=3, not_found=2):
        metrics.add(data)

    # 2nd second, submit 15 requests
    for data in make_requests(success=10, redirect=3, not_found=2, timedelta=1):
        metrics.add(data)

    # 3rd second, submit 10 requests
    for data in make_requests(success=5, redirect=3, not_found=2, timedelta=2):
        metrics.add(data)

    # 4th second, submit 5 requests
    for data in make_requests(success=0, redirect=3, not_found=2, timedelta=3):
        metrics.add(data)

    # 5th second, submit 0 requests
    # Currently we've got 55 requests/5s, which should trigger an alert
    assert metrics.get_stats()["traffic"] == 55
    alerts = metrics.get_alerts()
    assert (
        len(alerts) == 1
        and alerts[0]["type"] == TrafficAlert.TYPE
        and alerts[0]["status"] == TrafficAlert.ALERT
    )

    # Move forward another second, add 10 requests
    for data in make_requests(success=5, redirect=3, not_found=2, timedelta=5):
        metrics.add(data)

    # Mock current function to show a timestamp at the 6th second
    metrics.get_current_timestamp = lambda: (
        START_TIME + datetime.timedelta(seconds=5)
    ).timestamp()

    # 25 requests from the irst second should become outdated by now,
    # and the alert should recover.
    assert metrics.get_stats()["traffic"] == 40
    alerts = metrics.get_alerts()
    assert (
        len(alerts) == 1
        and alerts[0]["type"] == TrafficAlert.TYPE
        and alerts[0]["status"] == TrafficAlert.RECOVERED
    )
