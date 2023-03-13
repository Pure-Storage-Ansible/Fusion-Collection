# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class MockArray:
    def __init__(self, params):
        self.name = params["name"]

        self.display_name = params["display_name"] or params["name"]

        self.host_name = params["host_name"]
        self.region = params["region"]
        self.availability_zone = params["availability_zone"]
        self.hardware_type = params["hardware_type"]
        self.appliance_id = params["appliance_id"]

        if "maintenance_mode" not in params:
            self.maintenance_mode = True
        else:
            self.maintenance_mode = params["maintenance_mode"]

        if "unavailable_mode" not in params:
            self.unavailable_mode = False
        else:
            self.unavailable_mode = params["unavailable_mode"]
