# -*- coding: utf-8 -*-

# (c) 2023, Andrej Pajtas (apajtas@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, call, patch

import fusion as purefusion
import pytest
from ansible.module_utils import basic
from ansible_collections.purestorage.fusion.plugins.module_utils.errors import (
    OperationException,
)
from ansible_collections.purestorage.fusion.plugins.modules import fusion_array
from ansible_collections.purestorage.fusion.tests.functional.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    FailedOperationMock,
    OperationMock,
    SuccessfulOperationMock,
    FAKE_RESOURCE_ID,
    exit_json,
    fail_json,
    set_module_args,
)
from urllib3.exceptions import HTTPError

# GLOBAL MOCKS
fusion_array.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@pytest.fixture
def module_args():
    return {
        "state": "present",
        "name": "array1",
        "display_name": "Array 1",
        "region": "region1",
        "availability_zone": "az1",
        "appliance_id": "23984573498573",
        "apartment_id": "76586785687",
        "host_name": "array_1",
        "hardware_type": "flash-array-x",
        "maintenance_mode": False,
        "unavailable_mode": False,
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@pytest.fixture
def current_array(module_args):
    return {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],
        "display_name": module_args["display_name"],
        "region": module_args["region"],
        "availability_zone": module_args["availability_zone"],
        "appliance_id": module_args["appliance_id"],
        "apartment_id": module_args["apartment_id"],
        "host_name": module_args["host_name"],
        "hardware_type": module_args["hardware_type"],
        "maintenance_mode": module_args["maintenance_mode"],
        "unavailable_mode": module_args["unavailable_mode"],
    }


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'name` is missing
        {
            "state": "present",
            "display_name": "Array 1",
            "region": "region1",
            "availability_zone": "az1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "hardware_type": "flash-array-x",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # required parameter 'region` is missing
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "availability_zone": "az1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "hardware_type": "flash-array-x",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # required parameter 'availability_zone` is missing
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "region": "region1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "hardware_type": "flash-array-x",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "availability_zone": "az1",
            "region": "region1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "hardware_type": "flash-array-x",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "array1",
            "display_name": "Array 1",
            "availability_zone": "az1",
            "region": "region1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "hardware_type": "flash-array-x",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # parameter 'hardware_type` has incorrect value
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "availability_zone": "az1",
            "region": "region1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "hardware_type": "hdd-array-x",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # parameter 'maintenance_mode` has incorrect value
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "availability_zone": "az1",
            "region": "region1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "hardware_type": "flash-array-x",
            "maintenance_mode": "string",
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # parameter 'unavailable_mode` has incorrect value
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "availability_zone": "az1",
            "region": "region1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "hardware_type": "flash-array-x",
            "maintenance_mode": False,
            "unavailable_mode": "string",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
    ],
)
def test_module_fails_on_wrong_parameters(m_array_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_array_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_array.main()

    # check api was not called at all
    api_obj.get_array.assert_not_called()
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'hardware_type` for creating resource is missing
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "region": "region1",
            "availability_zone": "az1",
            "appliance_id": "23984573498573",
            "host_name": "array_1",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # required parameter 'host_name` for creating resource is missing
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "region": "region1",
            "availability_zone": "az1",
            "appliance_id": "23984573498573",
            "hardware_type": "flash-array-x",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # required parameter 'appliance_id` for creating resource is missing
        {
            "state": "present",
            "name": "array1",
            "display_name": "Array 1",
            "region": "region1",
            "availability_zone": "az1",
            "host_name": "array_1",
            "hardware_type": "flash-array-x",
            "maintenance_mode": False,
            "unavailable_mode": False,
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
    ],
)
def test_array_create_fails_on_wrong_parameters(m_array_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_array_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_array.main()

    # check api was not called at all
    api_obj.get_array.assert_called_once_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "hw_type",
    [
        "flash-array-x",
        "flash-array-c",
        "flash-array-x-optane",
        "flash-array-xl",
    ],
)
@pytest.mark.parametrize("main_m", [True, False])
@pytest.mark.parametrize("unav_m", [True, False])
def test_array_create(m_array_api, m_op_api, hw_type, main_m, unav_m, module_args):
    module_args["hardware_type"] = hw_type
    module_args["maintenance_mode"] = main_m
    module_args["unavailable_mode"] = unav_m
    created_array = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],
        "display_name": module_args["display_name"],
        "region": module_args["region"],
        "availability_zone": module_args["availability_zone"],
        "appliance_id": module_args["appliance_id"],
        "apartment_id": module_args["apartment_id"],
        "host_name": module_args["host_name"],
        "hardware_type": module_args["hardware_type"],
        "maintenance_mode": not module_args[
            "maintenance_mode"
        ],  # so we can test patching
        "unavailable_mode": not module_args[
            "unavailable_mode"
        ],  # so we can test patching
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(
        side_effect=[purefusion.rest.ApiException, purefusion.Array(**created_array)]
    )
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_array.main()

    assert exc.value.changed
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_called_once_with(
        purefusion.ArrayPost(
            hardware_type=module_args["hardware_type"],
            display_name=module_args["display_name"],
            host_name=module_args["host_name"],
            name=module_args["name"],
            appliance_id=module_args["appliance_id"],
            apartment_id=module_args["apartment_id"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_array.assert_has_calls(
        [
            call(
                purefusion.ArrayPatch(
                    maintenance_mode=purefusion.NullableBoolean(
                        module_args["maintenance_mode"]
                    )
                ),
                availability_zone_name=module_args["availability_zone"],
                region_name=module_args["region"],
                array_name=module_args["name"],
            ),
            call(
                purefusion.ArrayPatch(
                    unavailable_mode=purefusion.NullableBoolean(
                        module_args["unavailable_mode"]
                    )
                ),
                availability_zone_name=module_args["availability_zone"],
                region_name=module_args["region"],
                array_name=module_args["name"],
            ),
        ],
        any_order=True,
    )
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_has_calls(
        [
            call(1),
            call(2),
            call(2),
        ]
    )


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_create_without_display_name(m_array_api, m_op_api, module_args):
    del module_args["display_name"]
    created_array = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],
        "display_name": module_args["name"],
        "region": module_args["region"],
        "availability_zone": module_args["availability_zone"],
        "appliance_id": module_args["appliance_id"],
        "apartment_id": module_args["apartment_id"],
        "host_name": module_args["host_name"],
        "hardware_type": module_args["hardware_type"],
        "maintenance_mode": not module_args["maintenance_mode"],
        "unavailable_mode": not module_args["unavailable_mode"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(
        side_effect=[purefusion.rest.ApiException, purefusion.Array(**created_array)]
    )
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_array.main()

    assert exc.value.changed
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_called_once_with(
        purefusion.ArrayPost(
            hardware_type=module_args["hardware_type"],
            display_name=module_args["name"],
            host_name=module_args["host_name"],
            name=module_args["name"],
            appliance_id=module_args["appliance_id"],
            apartment_id=module_args["apartment_id"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_array.assert_has_calls(
        [
            call(
                purefusion.ArrayPatch(
                    maintenance_mode=purefusion.NullableBoolean(
                        module_args["maintenance_mode"]
                    )
                ),
                availability_zone_name=module_args["availability_zone"],
                region_name=module_args["region"],
                array_name=module_args["name"],
            ),
            call(
                purefusion.ArrayPatch(
                    unavailable_mode=purefusion.NullableBoolean(
                        module_args["unavailable_mode"]
                    )
                ),
                availability_zone_name=module_args["availability_zone"],
                region_name=module_args["region"],
                array_name=module_args["name"],
            ),
        ],
        any_order=True,
    )
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_has_calls(
        [
            call(1),
            call(2),
            call(2),
        ]
    )


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_array_create_exception(
    m_array_api, m_op_api, exec_original, exec_catch, module_args
):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_array = MagicMock(side_effect=exec_original)
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_once_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_called_once_with(
        purefusion.ArrayPost(
            hardware_type=module_args["hardware_type"],
            display_name=module_args["display_name"],
            host_name=module_args["host_name"],
            name=module_args["name"],
            appliance_id=module_args["appliance_id"],
            apartment_id=module_args["apartment_id"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_array_create_second_exception(
    m_array_api, m_op_api, exec_original, exec_catch, module_args
):
    created_array = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],
        "display_name": module_args["name"],
        "region": module_args["region"],
        "availability_zone": module_args["availability_zone"],
        "appliance_id": module_args["appliance_id"],
        "apartment_id": module_args["apartment_id"],
        "host_name": module_args["host_name"],
        "hardware_type": module_args["hardware_type"],
        "maintenance_mode": not module_args["maintenance_mode"],
        "unavailable_mode": not module_args["unavailable_mode"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(
        side_effect=[purefusion.rest.ApiException, purefusion.Array(**created_array)]
    )
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(side_effect=exec_original)
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_called_once_with(
        purefusion.ArrayPost(
            hardware_type=module_args["hardware_type"],
            display_name=module_args["display_name"],
            host_name=module_args["host_name"],
            name=module_args["name"],
            appliance_id=module_args["appliance_id"],
            apartment_id=module_args["apartment_id"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_array.assert_called_once()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_create_op_fails(m_array_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_once_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_called_once_with(
        purefusion.ArrayPost(
            hardware_type=module_args["hardware_type"],
            display_name=module_args["display_name"],
            host_name=module_args["host_name"],
            name=module_args["name"],
            appliance_id=module_args["appliance_id"],
            apartment_id=module_args["apartment_id"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_create_second_op_fails(m_array_api, m_op_api, module_args):
    created_array = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],
        "display_name": module_args["name"],
        "region": module_args["region"],
        "availability_zone": module_args["availability_zone"],
        "appliance_id": module_args["appliance_id"],
        "apartment_id": module_args["apartment_id"],
        "host_name": module_args["host_name"],
        "hardware_type": module_args["hardware_type"],
        "maintenance_mode": not module_args["maintenance_mode"],
        "unavailable_mode": not module_args["unavailable_mode"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(
        side_effect=[purefusion.rest.ApiException, purefusion.Array(**created_array)]
    )
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(
        side_effect=[SuccessfulOperationMock, FailedOperationMock]
    )
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_called_once_with(
        purefusion.ArrayPost(
            hardware_type=module_args["hardware_type"],
            display_name=module_args["display_name"],
            host_name=module_args["host_name"],
            name=module_args["name"],
            appliance_id=module_args["appliance_id"],
            apartment_id=module_args["apartment_id"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_array.assert_called_once()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_has_calls(
        [
            call(1),
            call(2),
        ]
    )


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_array_create_op_exception(
    m_array_api, m_op_api, exec_original, exec_catch, module_args
):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_once_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_called_once_with(
        purefusion.ArrayPost(
            hardware_type=module_args["hardware_type"],
            display_name=module_args["display_name"],
            host_name=module_args["host_name"],
            name=module_args["name"],
            appliance_id=module_args["appliance_id"],
            apartment_id=module_args["apartment_id"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_array_create_second_op_exception(
    m_array_api, m_op_api, exec_original, exec_catch, module_args
):
    created_array = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],
        "display_name": module_args["name"],
        "region": module_args["region"],
        "availability_zone": module_args["availability_zone"],
        "appliance_id": module_args["appliance_id"],
        "apartment_id": module_args["apartment_id"],
        "host_name": module_args["host_name"],
        "hardware_type": module_args["hardware_type"],
        "maintenance_mode": not module_args["maintenance_mode"],
        "unavailable_mode": not module_args["unavailable_mode"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(
        side_effect=[purefusion.rest.ApiException, purefusion.Array(**created_array)]
    )
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(
        side_effect=[SuccessfulOperationMock, exec_original]
    )
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_called_once_with(
        purefusion.ArrayPost(
            hardware_type=module_args["hardware_type"],
            display_name=module_args["display_name"],
            host_name=module_args["host_name"],
            name=module_args["name"],
            appliance_id=module_args["appliance_id"],
            apartment_id=module_args["apartment_id"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_array.assert_called_once()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_has_calls(
        [
            call(1),
            call(2),
        ]
    )


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_update(m_array_api, m_op_api, module_args, current_array):
    current_array["display_name"] = None
    current_array["host_name"] = "something"
    current_array["maintenance_mode"] = not current_array["maintenance_mode"]
    current_array["unavailable_mode"] = not current_array["unavailable_mode"]
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_array.main()

    assert exc.value.changed
    assert exc.value.id == current_array["id"]

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_has_calls(
        [
            call(
                purefusion.ArrayPatch(
                    display_name=purefusion.NullableString(module_args["display_name"])
                ),
                availability_zone_name=module_args["availability_zone"],
                region_name=module_args["region"],
                array_name=module_args["name"],
            ),
            call(
                purefusion.ArrayPatch(
                    host_name=purefusion.NullableString(module_args["host_name"])
                ),
                availability_zone_name=module_args["availability_zone"],
                region_name=module_args["region"],
                array_name=module_args["name"],
            ),
            call(
                purefusion.ArrayPatch(
                    unavailable_mode=purefusion.NullableBoolean(
                        module_args["unavailable_mode"]
                    )
                ),
                availability_zone_name=module_args["availability_zone"],
                region_name=module_args["region"],
                array_name=module_args["name"],
            ),
            call(
                purefusion.ArrayPatch(
                    maintenance_mode=purefusion.NullableBoolean(
                        module_args["maintenance_mode"]
                    )
                ),
                availability_zone_name=module_args["availability_zone"],
                region_name=module_args["region"],
                array_name=module_args["name"],
            ),
        ],
        any_order=True,
    )
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_has_calls(
        [
            call(2),
            call(2),
            call(2),
            call(2),
        ]
    )


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_array_update_exception(
    m_array_api, m_op_api, exec_original, exec_catch, module_args, current_array
):
    current_array["display_name"] = None
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(side_effect=exec_original)
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_called_once()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_update_op_fails(m_array_api, m_op_api, module_args, current_array):
    current_array["display_name"] = None
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_called_once()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_array_update_op_exception(
    m_array_api, m_op_api, exec_original, exec_catch, module_args, current_array
):
    current_array["display_name"] = None
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_called_once()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_present_not_changed(m_array_api, m_op_api, module_args, current_array):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_array.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_absent_not_changed(m_array_api, m_op_api, module_args):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_array.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_array.assert_called_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_delete(m_array_api, m_op_api, module_args, current_array):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_array.main()

    assert exc.value.changed

    # check api was called correctly
    api_obj.get_array.assert_called_once_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_called_once_with(
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
        array_name=module_args["name"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_array_delete_exception(
    m_array_api, m_op_api, exec_original, exec_catch, module_args, current_array
):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(side_effect=exec_original)
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_once_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_called_once_with(
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
        array_name=module_args["name"],
    )
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
def test_array_delete_op_fails(m_array_api, m_op_api, module_args, current_array):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_once_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_called_once_with(
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
        array_name=module_args["name"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.ArraysApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_array_delete_op_exception(
    m_array_api, m_op_api, exec_original, exec_catch, module_args, current_array
):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_array = MagicMock(return_value=purefusion.Array(**current_array))
    api_obj.create_array = MagicMock(return_value=OperationMock(1))
    api_obj.update_array = MagicMock(return_value=OperationMock(2))
    api_obj.delete_array = MagicMock(return_value=OperationMock(3))
    m_array_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_array.main()

    # check api was called correctly
    api_obj.get_array.assert_called_once_with(
        array_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.create_array.assert_not_called()
    api_obj.update_array.assert_not_called()
    api_obj.delete_array.assert_called_once_with(
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
        array_name=module_args["name"],
    )
    op_obj.get_operation.assert_called_once_with(3)
