# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from enum import Enum


class OperationStatus(str, Enum):
    PENDING = "Pending"
    ABORTING = "Aborting"
    FAILED = "Failed"
    SUCCEDED = "Succeeded"


class OperationMock:
    def __init__(self, id, status, retry_in=1):
        self.id = id
        self.status = status
        self.retry_in = retry_in
