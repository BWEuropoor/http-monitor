def test_parse_log(parser):
    data = parser(
        """127.0.0.1 - jill [09/May/2018:16:00:41 +0000] "GET /api/user HTTP/1.0" 200 234"""
    )

    expected = {
        "remote_host": "127.0.0.1",
        "remote_logname": "jill",
        "request_method": "GET",
        "request_url_path": "/api/user",
        "request_url_subpath": "/api",
        "status": "200",
        "response_bytes_clf": "234",
        "time_received": "[09/May/2018:16:00:41 +0000]",
    }

    for key, value in expected.items():
        assert value == data[key]
