import os.path
from typing import Dict

import apache_log_parser

LOG_FORMAT = """%h - %l %t \"%r\" %>s %b"""


class Parser(apache_log_parser.Parser):
    def parse(self, line: str) -> Dict[str, str]:
        results = super().parse(line)
        results["request_url_subpath"] = (
            "/" + results["request_url_path"][1:].split("/")[0]
        )
        return results

    @staticmethod
    def make_parser(log_format: str = LOG_FORMAT):
        return Parser(log_format).parse
