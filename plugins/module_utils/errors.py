# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json


class ApiExceptionWrapper(Exception):
    def __init__(self, api_exception, operation=None, json_indent=4):
        self.reason = api_exception.reason
        self.status = api_exception.status
        self.headers = api_exception.headers
        self.operation = operation
        self.json_indent = json_indent

        self.body = None
        if api_exception.body:
            self.body = json.loads(api_exception.body)

    def __str__(self):
        """Custom error messages for exception"""
        error_message = ""
        if self.operation:
            error_message += "Operation {0} failed\n".format(self.operation)

        error_message += "Status: {0}\n" "Reason: {1}\n".format(
            self.status, self.reason
        )

        if self.headers:
            error_message += "HTTP response headers:\n{0}\n".format(
                json.dumps(self.headers.__dict__, indent=self.json_indent)
            )

        if self.body:
            error_message += "HTTP response body:\n{0}".format(
                json.dumps(self.body, indent=self.json_indent)
            )

        return error_message

    def pretty_message(self):
        """Short user friendly message"""
        error_message = ""
        if self.operation:
            error_message += "Operation {0} failed; ".format(self.operation)

        error_message += "Reason: {0}; ".format(self.reason)

        if self.body:
            error_message += "Message: {0}".format(self.body["error"]["message"])

        return error_message
