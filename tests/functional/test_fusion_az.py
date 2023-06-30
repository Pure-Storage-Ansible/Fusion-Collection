# -*- coding: utf-8 -*-

# (c) 2023, Andrej Pajtas (apajtas@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, patch

import fusion as purefusion
import pytest
from ansible.module_utils import basic
from ansible_collections.purestorage.fusion.plugins.module_utils.errors import (
    OperationException,
)
from ansible_collections.purestorage.fusion.plugins.modules import fusion_az
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
fusion_az.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'name` is missing
        {
            "state": "present",
            "region": "region1",
            "display_name": "Availability Zone 1",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # required parameter 'region` is missing
        {
            "state": "present",
            "name": "az1",
            "display_name": "Availability Zone 1",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "az1",
            "region": "region1",
            "display_name": "Availability Zone 1",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "az1",
            "region": "region1",
            "display_name": "Availability Zone 1",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
    ],
)
def test_module_op_fails_on_wrong_parameters(m_az_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_az.main()

    # check api was not called at all
    api_obj.get_region.assert_not_called()
    api_obj.create_availability_zone.assert_not_called()
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
def test_az_create(m_az_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "az1",
        "region": "region1",
        "display_name": "Availability Zone 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_az.main()

    assert exc.value.changed
    assert exc.value.id == FAKE_RESOURCE_ID

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_called_once_with(
        purefusion.AvailabilityZonePost(
            name=module_args["name"],
            display_name=module_args["display_name"],
        ),
        region_name=module_args["region"],
    )
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
def test_az_create_without_display_name(m_az_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "az1",
        "region": "region1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_az.main()

    assert exc.value.changed
    assert exc.value.id == FAKE_RESOURCE_ID

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_called_once_with(
        purefusion.AvailabilityZonePost(
            name=module_args["name"],
            display_name=module_args["name"],
        ),
        region_name=module_args["region"],
    )
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_az_create_exception(m_az_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "az1",
        "region": "region1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_availability_zone = MagicMock(side_effect=exec_original)
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_az.main()

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_called_once_with(
        purefusion.AvailabilityZonePost(
            name=module_args["name"],
            display_name=module_args["name"],
        ),
        region_name=module_args["region"],
    )
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
def test_az_create_op_fails(m_az_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "az1",
        "region": "region1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_az.main()

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_called_once_with(
        purefusion.AvailabilityZonePost(
            name=module_args["name"],
            display_name=module_args["name"],
        ),
        region_name=module_args["region"],
    )
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_az_create_op_exception(m_az_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "az1",
        "region": "region1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_az.main()

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_called_once_with(
        purefusion.AvailabilityZonePost(
            name=module_args["name"],
            display_name=module_args["name"],
        ),
        region_name=module_args["region"],
    )
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
def test_az_update(m_az_api, m_op_api):
    # NOTE: Availability Zone does not have PATCH method, thus no action is expected
    module_args = {
        "state": "present",
        "name": "az1",
        "region": "region1",
        "display_name": "Availability Zone 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_az = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "region": module_args["region"],  # region must match
        "display_name": None,
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(
        return_value=purefusion.AvailabilityZone(**current_az)
    )
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_az.main()

    assert not exc.value.changed

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_not_called()
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
def test_az_present_not_changed(m_az_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "az1",
        "region": "region1",
        "display_name": "Availability Zone 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_az = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "region": module_args["region"],  # region must match
        "display_name": module_args["display_name"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(
        return_value=purefusion.AvailabilityZone(**current_az)
    )
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_az.main()

    assert not exc.value.changed

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_not_called()
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
def test_az_absent_not_changed(m_az_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "az1",
        "region": "region1",
        "display_name": "Availability Zone 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_az.main()

    assert not exc.value.changed

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_not_called()
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
def test_az_delete(m_az_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "az1",
        "region": "region1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_az = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "region": module_args["region"],  # region must match
        "display_name": None,
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(
        return_value=purefusion.AvailabilityZone(**current_az)
    )
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_az.main()

    assert exc.value.changed

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_not_called()
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_called_once_with(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_az_delete_exception(m_az_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "absent",
        "name": "az1",
        "region": "region1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_az = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "region": module_args["region"],  # region must match
        "display_name": None,
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(
        return_value=purefusion.AvailabilityZone(**current_az)
    )
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(side_effect=exec_original)
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_az.main()

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_not_called()
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_called_once_with(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
def test_az_delete_op_fails(m_az_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "az1",
        "region": "region1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_az = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "region": module_args["region"],  # region must match
        "display_name": None,
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(
        return_value=purefusion.AvailabilityZone(**current_az)
    )
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_az.main()

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_not_called()
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_called_once_with(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.AvailabilityZonesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_az_delete_op_exception(m_az_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "absent",
        "name": "az1",
        "region": "region1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_az = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "region": module_args["region"],  # region must match
        "display_name": None,
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_availability_zone = MagicMock(
        return_value=purefusion.AvailabilityZone(**current_az)
    )
    api_obj.create_availability_zone = MagicMock(return_value=OperationMock(1))
    api_obj.update_availability_zone = MagicMock(return_value=OperationMock(2))
    api_obj.delete_availability_zone = MagicMock(return_value=OperationMock(3))
    m_az_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_az.main()

    api_obj.get_region.get_availability_zone(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    api_obj.create_availability_zone.assert_not_called()
    api_obj.update_availability_zone.assert_not_called()
    api_obj.delete_availability_zone.assert_called_once_with(
        availability_zone_name=module_args["name"],
        region_name=module_args["region"],
    )
    op_obj.get_operation.assert_called_once_with(3)
