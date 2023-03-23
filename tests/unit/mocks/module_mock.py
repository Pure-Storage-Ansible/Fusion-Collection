# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock


class ModuleSucceeded(Exception):
    pass


class ModuleFailed(Exception):
    pass


class ModuleMock(MagicMock):
    def __init__(self, params, check_mode=False, exit_json=None, fail_json=None):
        super().__init__()

        self.params = params
        self.check_mode = check_mode

        if exit_json is None:
            self.exit_json = MagicMock()
        else:
            self.exit_json = exit_json

        if fail_json is None:
            self.fail_json = MagicMock()
        else:
            self.fail_json = fail_json
