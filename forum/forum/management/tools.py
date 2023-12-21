"""
A custom type for argparse, to facilitate validation of email addresses.
Inspired by this SO question: https://stackoverflow.com/questions/14665234/argparse-choices-structure-of-allowed-values
and this gist: https://gist.github.com/gurunars/449edbccd0de1449b71524c89d61e1c5
"""
import argparse
import re


class EmailType(object):
    """
    Supports checking email agains different patterns. The current available patterns is:
    RFC5322 (https://www.ietf.org/rfc/rfc5322.txt)
    """

    patterns = {
        "RFC5322": re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"),
    }

    def __init__(self, pattern="RFC5322"):
        if pattern not in self.patterns:
            raise KeyError(
                "{} is not a supported email pattern, choose from:" " {}".format(pattern, ",".join(self.patterns))
            )
        self._rules = pattern
        self._pattern = self.patterns[pattern]

    def __call__(self, value):
        if not self._pattern.match(value):
            raise argparse.ArgumentTypeError(
                "'{}' is not a valid email - does not match {} rules".format(value, self._rules)
            )
        return value
