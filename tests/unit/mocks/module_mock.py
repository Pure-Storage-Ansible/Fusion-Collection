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
    def __init__(self, params, check_mode=False):
        super().__init__()

        self.params = params
        self.check_mode = check_mode

        # mocking exit_json function, so we can check if it was successfully called
        self.exit_json = MagicMock()

    def fail_json(self, **kwargs):
        raise ModuleFailed(str(kwargs))

    def fail_on_missing_params(self, required_params=None):
        if required_params is not None:
            for param in required_params:
                if param not in self.params:
                    raise ModuleFailed(f"Parameter '{param}' is missing")
