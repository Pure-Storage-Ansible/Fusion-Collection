# -*- coding: utf-8 -*-

# (c) 2023, Andrej Pajtas (apajtas@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock

import fusion as purefusion
import pytest
from ansible.module_utils import basic
from ansible_collections.purestorage.fusion.plugins.modules import fusion_hw
from ansible_collections.purestorage.fusion.tests.functional.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    exit_json,
    fail_json,
    set_module_args,
)

# GLOBAL MOCKS
fusion_hw.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@pytest.mark.parametrize(
    "module_args",
    [
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "hw1",
            "display_name": "Hardware Type 1",
            "array_type": "FA//X",
            "media_type": "random",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "hw1",
            "display_name": "Hardware Type 1",
            "array_type": "FA//X",
            "media_type": "random",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # parameter 'state` has incorrect value
        {
            "state": "absent",
            "name": "hw1",
            "display_name": "Hardware Type 1",
            "array_type": "FA//X",
            "media_type": "random",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # parameter 'array_type` has incorrect value
        {
            "state": "present",
            "name": "hw1",
            "display_name": "Hardware Type 1",
            "array_type": "wrong",
            "media_type": "random",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
    ],
)
def test_module_fails_on_wrong_parameters(module_args):
    set_module_args(module_args)

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_hw.main()


@pytest.mark.parametrize("state", [None, "present"])
@pytest.mark.parametrize("name", [None, "hw_type_name1"])
@pytest.mark.parametrize("display_name", [None, "Super weird    Display Name 12 3"])
@pytest.mark.parametrize("array_type", [None, "FA//X", "FA//C"])
@pytest.mark.parametrize("media_type", [None, "random"])
def test_hw_does_not_call_api(state, name, display_name, array_type, media_type):
    module_args = {
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    if state is not None:
        module_args["state"] = state
    if name is not None:
        module_args["name"] = name
    if display_name is not None:
        module_args["display_name"] = display_name
    if array_type is not None:
        module_args["array_type"] = array_type
    if media_type is not None:
        module_args["media_type"] = media_type
    set_module_args(module_args)

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_hw.main()

    assert exc.value.changed is False

    # NOTE: api call assertion is handled by global mock
