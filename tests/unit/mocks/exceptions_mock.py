# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import fusion as purefusion

from http import HTTPStatus
from dataclasses import dataclass


@dataclass
class HttpResponseMock:
    status: int
    reason: str
    body: str
    headers: list = None


class ApiExceptionsMockGenerator:
    def create_permission_denied(self, body_message="User doesn't have access"):
        body = {"msg": body_message}
        status = HTTPStatus.FORBIDDEN
        reason = status.phrase
        http_response = HttpResponseMock(status, reason, body)

        return purefusion.rest.ApiException(http_response)

    def create_conflict(self, body_message="Conflict"):
        body = {"msg": body_message}
        status = HTTPStatus.CONFLICT
        reason = status.phrase
        http_response = HttpResponseMock(status, reason, body)

        return purefusion.rest.ApiException(http_response)

    def create_not_found(self, body_message="Item not found"):
        body = {"msg": body_message}
        status = HTTPStatus.NOT_FOUND
        reason = status.phrase
        http_response = HttpResponseMock(status, reason, body)

        return purefusion.rest.ApiException(http_response)
