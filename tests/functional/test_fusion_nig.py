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
from ansible_collections.purestorage.fusion.plugins.modules import fusion_nig
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
fusion_nig.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'name` is missing
        {
            "state": "present",
            "display_name": "Network Interface Group 1",
            "availability_zone": "az1",
            "region": "region1",
            "prefix": "10.21.200.0/24",
            "gateway": "10.21.200.1",
            "mtu": 1300,
            "group_type": "eth",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # required parameter 'availability_zone` is missing
        {
            "state": "present",
            "name": "nig1",
            "display_name": "Network Interface Group 1",
            "region": "region1",
            "prefix": "10.21.200.0/24",
            "gateway": "10.21.200.1",
            "mtu": 1300,
            "group_type": "eth",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # required parameter 'region` is missing
        {
            "state": "present",
            "name": "nig1",
            "display_name": "Network Interface Group 1",
            "availability_zone": "az1",
            "prefix": "10.21.200.0/24",
            "gateway": "10.21.200.1",
            "mtu": 1300,
            "group_type": "eth",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "nig1",
            "display_name": "Network Interface Group 1",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "nig1",
            "display_name": "Network Interface Group 1",
            "availability_zone": "az1",
            "region": "region1",
            "prefix": "10.21.200.0/24",
            "gateway": "10.21.200.1",
            "mtu": 1300,
            "group_type": "eth",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # parameter 'group_type` has incorrect value
        {
            "state": "present",
            "name": "nig1",
            "display_name": "Network Interface Group 1",
            "availability_zone": "az1",
            "region": "region1",
            "prefix": "10.21.200.0/24",
            "gateway": "10.21.200.1",
            "mtu": 1300,
            "group_type": "supergroup",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
    ],
)
def test_module_fails_on_wrong_parameters(m_nig_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_nig_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_nig.main()

    # check api was not called at all
    api_obj.get_network_interface_group.assert_not_called()
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_create_fails_on_missing_prefix(m_nig_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "nig1",
        "display_name": "Network Interface Group 1",
        "availability_zone": "az1",
        "region": "region1",
        "gateway": "10.21.200.1",
        "mtu": 1300,
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_nig_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_nig.main()

    # check api was not called at all
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_create(m_nig_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "nig1",
        "display_name": "Network Interface Group 1",
        "availability_zone": "az1",
        "region": "region1",
        "prefix": "10.21.200.0/24",
        "gateway": "10.21.200.1",
        "mtu": 1300,
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_nig.main()

    assert exc.value.changed is True
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPost(
            group_type="eth",
            eth=purefusion.NetworkInterfaceGroupEthPost(
                prefix=module_args["prefix"],
                gateway=module_args["gateway"],
                mtu=module_args["mtu"],
            ),
            name=module_args["name"],
            display_name=module_args["display_name"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_create_without_display_name(m_nig_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "nig1",
        "availability_zone": "az1",
        "region": "region1",
        "prefix": "10.21.200.0/24",
        "gateway": "10.21.200.1",
        "mtu": 1300,
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_nig.main()

    assert exc.value.changed is True
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPost(
            group_type="eth",
            eth=purefusion.NetworkInterfaceGroupEthPost(
                prefix=module_args["prefix"],
                gateway=module_args["gateway"],
                mtu=module_args["mtu"],
            ),
            name=module_args["name"],
            display_name=module_args["name"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_create_without_gateway(m_nig_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "nig1",
        "display_name": "Network Interface Group 1",
        "availability_zone": "az1",
        "region": "region1",
        "prefix": "10.21.200.0/24",
        "mtu": 1300,
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_nig.main()

    assert exc.value.changed is True
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPost(
            group_type="eth",
            eth=purefusion.NetworkInterfaceGroupEthPost(
                prefix=module_args["prefix"],
                mtu=module_args["mtu"],
            ),
            name=module_args["name"],
            display_name=module_args["display_name"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_nig_create_exception(m_nig_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "nig1",
        "display_name": "Network Interface Group 1",
        "availability_zone": "az1",
        "region": "region1",
        "prefix": "10.21.200.0/24",
        "mtu": 1300,
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(side_effect=exec_original)
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPost(
            group_type="eth",
            eth=purefusion.NetworkInterfaceGroupEthPost(
                prefix=module_args["prefix"],
                mtu=module_args["mtu"],
            ),
            name=module_args["name"],
            display_name=module_args["display_name"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_create_op_fails(m_nig_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "nig1",
        "display_name": "Network Interface Group 1",
        "availability_zone": "az1",
        "region": "region1",
        "prefix": "10.21.200.0/24",
        "mtu": 1300,
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPost(
            group_type="eth",
            eth=purefusion.NetworkInterfaceGroupEthPost(
                prefix=module_args["prefix"],
                mtu=module_args["mtu"],
            ),
            name=module_args["name"],
            display_name=module_args["display_name"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_nig_create_op_exception(m_nig_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "nig1",
        "display_name": "Network Interface Group 1",
        "availability_zone": "az1",
        "region": "region1",
        "prefix": "10.21.200.0/24",
        "mtu": 1300,
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPost(
            group_type="eth",
            eth=purefusion.NetworkInterfaceGroupEthPost(
                prefix=module_args["prefix"],
                mtu=module_args["mtu"],
            ),
            name=module_args["name"],
            display_name=module_args["display_name"],
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
    )
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_update(m_nig_api, m_op_api):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name=None,
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "present",
        "name": current_nig.name,  # must match
        "display_name": "New Name",  # should be updated
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "prefix": "12.19.150.0/23",  # should not be updated
        "mtu": current_nig.eth.mtu + 100,  # should not be updated
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_nig.main()

    assert exc.value.changed is True
    assert exc.value.id == current_nig.id

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPatch(
            display_name=purefusion.NullableString(module_args["display_name"]),
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_nig_update_exception(m_nig_api, m_op_api, exec_original, exec_catch):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name=None,
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "present",
        "name": current_nig.name,  # must match
        "display_name": "New Name",  # should be updated
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "prefix": "12.19.150.0/23",  # should not be updated
        "mtu": current_nig.eth.mtu + 100,  # should not be updated
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(side_effect=exec_original)
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPatch(
            display_name=purefusion.NullableString(module_args["display_name"]),
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_update_op_fails(m_nig_api, m_op_api):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name=None,
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "present",
        "name": current_nig.name,  # must match
        "display_name": "New Name",  # should be updated
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "prefix": "12.19.150.0/23",  # should not be updated
        "mtu": current_nig.eth.mtu + 100,  # should not be updated
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPatch(
            display_name=purefusion.NullableString(module_args["display_name"]),
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_nig_update_op_exception(m_nig_api, m_op_api, exec_original, exec_catch):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name=None,
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "present",
        "name": current_nig.name,  # must match
        "display_name": "New Name",  # should be updated
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "prefix": "12.19.150.0/23",  # should not be updated
        "mtu": current_nig.eth.mtu + 100,  # should not be updated
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_called_once_with(
        purefusion.NetworkInterfaceGroupPatch(
            display_name=purefusion.NullableString(module_args["display_name"]),
        ),
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_present_not_changed(m_nig_api, m_op_api):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name="Display Name",
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "present",
        "name": current_nig.name,  # must match
        "display_name": current_nig.display_name,  # should not be updated
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "prefix": "12.19.150.0/23",  # should not be updated
        "mtu": current_nig.eth.mtu + 100,  # should not be updated
        "group_type": "eth",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_nig.main()

    assert exc.value.changed is False

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_absent_not_changed(m_nig_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "nig1",
        "display_name": "Network Interface Group 1",
        "availability_zone": "az1",
        "region": "region1",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_nig.main()

    assert exc.value.changed is False

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_delete(m_nig_api, m_op_api):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name="Display Name",
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "absent",
        "name": current_nig.name,  # must match
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_nig.main()

    assert exc.value.changed is True

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_nig_delete_exception(m_nig_api, m_op_api, exec_original, exec_catch):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name="Display Name",
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "absent",
        "name": current_nig.name,  # must match
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(side_effect=exec_original)
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
def test_nig_delete_op_fails(m_nig_api, m_op_api):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name="Display Name",
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "absent",
        "name": current_nig.name,  # must match
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_nig_delete_op_exception(m_nig_api, m_op_api, exec_original, exec_catch):
    current_nig = purefusion.NetworkInterfaceGroup(
        id="1",
        self_link="self_link_value",
        name="nig1",
        display_name="Display Name",
        region="region1",
        availability_zone="az1",
        group_type="eth",
        eth=purefusion.NetworkInterfaceGroupEth(
            prefix="str",
            gateway="str",
            vlan=3,
            mtu=1300,
        ),
    )
    module_args = {
        "state": "absent",
        "name": current_nig.name,  # must match
        "availability_zone": current_nig.availability_zone,  # must match
        "region": current_nig.region,  # must match
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_network_interface_group = MagicMock(return_value=current_nig)
    api_obj.create_network_interface_group = MagicMock(return_value=OperationMock(1))
    api_obj.update_network_interface_group = MagicMock(return_value=OperationMock(2))
    api_obj.delete_network_interface_group = MagicMock(return_value=OperationMock(3))
    m_nig_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_nig.main()

    # check api was called correctly
    api_obj.get_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    api_obj.create_network_interface_group.assert_not_called()
    api_obj.update_network_interface_group.assert_not_called()
    api_obj.delete_network_interface_group.assert_called_once_with(
        availability_zone_name=module_args["availability_zone"],
        region_name=module_args["region"],
        network_interface_group_name=module_args["name"],
    )
    op_obj.get_operation.assert_called_once_with(3)
