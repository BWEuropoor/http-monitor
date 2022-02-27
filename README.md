<div align="center">
  <h1>HTTP Monitor</h1>
</div>

## Table of Contents

- [Problem](#Problem)
- [Architecture](#architecture)
- [Features](#features)
- [Best practices](#best-practices)
- [Installation and Usage](#installation)
- [Configuration](#configuration)

## Problem 

Consume an actively written-to CLF HTTP access log (https://en.wikipedia.org/wiki/Common_Log_Format). It should default to reading /tmp/access.log and be overrideable

Example log lines:

127.0.0.1 - james [09/May/2018:16:00:39 +0000] "GET /report HTTP/1.0" 200 123

127.0.0.1 - jill [09/May/2018:16:00:41 +0000] "GET /api/user HTTP/1.0" 200 234

127.0.0.1 - frank [09/May/2018:16:00:42 +0000] "POST /api/user HTTP/1.0" 200 34

127.0.0.1 - mary [09/May/2018:16:00:42 +0000] "POST /api/user HTTP/1.0" 503 12

Display stats every 10s about the traffic during those 10s: the sections of the web site with the most hits, as well as interesting summary statistics on the traffic as a whole. A section is defined as being what's before the second `/` in the resource section of the log line. For example, the section for `/pages/create` is `/pages`
Make sure a user can keep the app running and monitor the log file continuously
Whenever total traffic for the past 2 minutes exceeds a certain number on average, print or display a message saying that `High traffic generated an alert - hits = {value}, triggered at {time}`. The default threshold should be 10 requests per second, and should be overridable
Whenever the total traffic drops again below that value on average for the past 2 minutes, print or display another message detailing when the alert recovered

## Architecture

<img src="https://i.imgur.com/eS6DPu9.png"/>

### Display

Abstract layer for displaying the alerts / stats. Current minimalistic reporting prints straight to the terminal, with a bit of coloring to distinguish between alerts/recovery messages.

As an improvement point we could move the reporting to the REST API and serve it in a real-time chart, preferably in JS due to, or use a terminal library that'd allow us to split the screen on multiple sections.

### Controller

#### FileObserver

We faced a decision choice on how to observer our log file. I hesitated between polling and OS notifications, and in the end went with the second one due to lower waste of resources and quicker alert triggering. If our logs are updated often, and we don't need immediate alerts the polling option might work better - ie. read the logs file once every 5 minutes.

We subscribe to OS notifications via [watchdog](https://pypi.org/project/watchdog/) library, to read from the file we keep the track of a number of currently read lines, after each event we take a new number of lines, and then we 'tail' the number of added lines to the file.

It comes obviously with limitations, we assume file will only grow in size, and never be cleaned during the runtime. An alternative would be to keep the track of all seen lines, and compare them 1-by-1 after the modification, however that'd be inefficient both computation and memory wise.

After obtaining new lines we send them to `HTTPMonitor` controller which parses them and reports new data points to `MetricsAggregator`

Follow ups:

- Lock the resource when accessing it.

#### HTTPMonitor

- Requests current stats from `MetricsAggregator` and submits messages to `Display`
- Requests current alerts status and submits messages to `Display`
- Reports new data points to `MetricsAggregator` every time `FileObserver` provides data

#### Parser

I've leveraged [apache-log-parser](https://pypi.org/project/apache-log-parser/) package and customised it to our usecase.

### Model Layer

<img src="https://i.imgur.com/Cxgbcj0.png"/>

#### MetricsAggregator

Our monitoring is a time-series of logs, we store the data points in a queue data structure. It gives us a flexibility to keep a track of items expiring without having to recalculate everything whenever new data point is added.

As a storage/computing optimisation we aggregate logs into buckets, keeping the track of the most important data (hits per IP address, hits per status code, hits per endpoint). Default aggregation size is 1s, however it's fully customisable via `bucket-size` parameter.

#### MetricsBucket

Single data point representing a part of the time-series.

#### Alerts

Alerts are fully customisable, as a MVP I've defined 3 of them:

- TrafficAlert - alert whenever avg traffic over the last `report_window` exceeds `alert_threshold` requests/s.
- ErrorRateAlert - alert whenever % of 500s exceeds the `alert_error_rate`.
- DdosAlert - alert whenever a single IP address exceeds the `ddos_threshold` requests/s.

Alerts are registered inside `MetricsAggregator` class' `alerts` property. To go a step further we could implement alerts for:

- Endpoint-specific error rate (high amount of 500s/400s)
- Endpoint-specific traffic
- Response size

## Features

### Done

- Report breakdown of status codes
- Report TOP 5 endpoint paths by traffic
- Report TOP 5 users ips by number of requests
- Setup custom alerts within minutes
- Fully configurable setup

### Follow ups

For monitoring to be complete we need much more than basic reporting, ideally we'd have a chance to zoom in on:

- Breakdown of status codes per endpoint
- Breakdown of user agents
- Breakdown of node/datacenter informations

For infrastructure:

- We store the logs only for `reporting-window` time, then we drop them from memory. Historical data could be moved to a lower cost storage options, like Hadoop. Furthermore, depending on the data type we could optimise the cost/storage by increasing the aggregation interval, ie from seconds to minutes

For logic of the solution:

- How to handle logs in non chronological order? IE what if one node reports logs with a significant delay. Do we report on them? Do we drop them?

## Best practices

### Done

As our project might grow tremendously, it's best to implement the best coding standards immediately, so far we've got:

- Static type checking by `mypy`
- Unit tests setup with `Pytest`
- Separate list of Python package dependencies for dev / production environments
- Automated code formatting via `black`
- Test coverage raport via `coverage`
- Automated import sorting by `isort`
- Automated removal of unused variables / imports via `autoflake`
- Documentation style checking via `pydocstyle`

### Follow ups

- CI setup on GitHub, ie [Travis CI](https://github.com/marketplace/travis-ci)
- Integration tests
- Dockerize

## Installation and Usage

We require Python 3.8, pip and.. UNIX-like system. The main reason of that is performance optimisation of file observing. We'll use both `tail` and `ws` command to avoid loading the whole file into the memory every time it's updated. In ideal world, we'd make this code platform agnostic and implement fallbacks for other OS.

To install all the dependencies:

`pip install -r requirements.txt`

For local development we've got a list of useful tools in `requirements_dev.txt`

Note: If you don't have Python on your machine, or you're not using virtualenv yet, please consider doing so. It's awesome and you'll love it. Please follow [this guide](https://docs.python-guide.org/dev/virtualenvs/).

To start the program with traffic simulation run

`python main.py --give-me-traffic`

To run the tests run `pytest` in the highest level folder.

## Configuration
One can configure everything from reporting window time, through alert thresholds to size of the bucket's we'll aggregate the traffic into. For full specification please run `python main.py -h`

Out of the box I provide a traffic simulation mechanism (`--give-me-traffic`) - we take 5 api endpoints, 7 Monthy Python's Holy Grail characters and 6 HTTP status codes to replicate wanna-be-random logs inside our file, adding from 0 to 20 entries every second.
