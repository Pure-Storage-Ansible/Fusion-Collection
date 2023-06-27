# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import fusion as purefusion

from http import HTTPStatus


class ApiExceptionsMockGenerator:
    @staticmethod
    def create_permission_denied():
        status = HTTPStatus.FORBIDDEN
        return purefusion.rest.ApiException(status=status, reason=status.phrase)

    @staticmethod
    def create_conflict():
        status = HTTPStatus.CONFLICT
        return purefusion.rest.ApiException(status=status, reason=status.phrase)

    @staticmethod
    def create_not_found():
        status = HTTPStatus.NOT_FOUND
        return purefusion.rest.ApiException(status=status, reason=status.phrase)


class OperationResultsDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
