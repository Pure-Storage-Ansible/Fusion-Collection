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
from ansible_collections.purestorage.fusion.plugins.modules import fusion_se
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
fusion_se.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@pytest.fixture
def module_args():
    return {
        "state": "present",
        "name": "se1",
        "display_name": "Storage Endpoint 1",
        "region": "region1",
        "availability_zone": "az1",
        "iscsi": [
            {
                "address": "10.21.200.124/24",
                "gateway": "10.21.200.1",
                "network_interface_groups": ["subnet-0", "subnet-1"],
            }
        ],
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@pytest.fixture
def current_se(module_args):
    return {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],
        "display_name": module_args["display_name"],
        "region": module_args["region"],
        "availability_zone": module_args["availability_zone"],
        "endpoint_type": "iscsi",
        "iscsi": [
            dict(discovery_interface) for discovery_interface in module_args["iscsi"]
        ],
    }


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'name` is missing
        {
            "state": "present",
            "display_name": "Storage Endpoint 1",
            "region": "region1",
            "availability_zone": "az1",
            "iscsi": [
                {
                    "address": "10.21.200.124/24",
                    "gateway": "10.21.200.1",
                    "network_interface_groups": ["subnet-0", "subnet-1"],
                }
            ],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # required parameter 'region` is missing
        {
            "state": "present",
            "name": "se1",
            "display_name": "Storage Endpoint 1",
            "availability_zone": "az1",
            "iscsi": [
                {
                    "address": "10.21.200.124/24",
                    "gateway": "10.21.200.1",
                    "network_interface_groups": ["subnet-0", "subnet-1"],
                }
            ],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # required parameter 'availability_zone` is missing
        {
            "state": "present",
            "name": "se1",
            "display_name": "Storage Endpoint 1",
            "region": "region1",
            "iscsi": [
                {
                    "address": "10.21.200.124/24",
                    "gateway": "10.21.200.1",
                    "network_interface_groups": ["subnet-0", "subnet-1"],
                }
            ],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "se1",
            "display_name": "Storage Endpoint 1",
            "region": "region1",
            "availability_zone": "az1",
            "iscsi": [
                {
                    "address": "10.21.200.124/24",
                    "gateway": "10.21.200.1",
                    "network_interface_groups": ["subnet-0", "subnet-1"],
                }
            ],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "se1",
            "display_name": "Storage Endpoint 1",
            "region": "region1",
            "availability_zone": "az1",
            "iscsi": [
                {
                    "address": "10.21.200.124/24",
                    "gateway": "10.21.200.1",
                    "network_interface_groups": ["subnet-0", "subnet-1"],
                }
            ],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # parameter 'iscsi` and 'cbs_azure_iscsi' are used at the same time
        {
            "state": "present",
            "name": "se1",
            "display_name": "Storage Endpoint 1",
            "region": "region1",
            "availability_zone": "az1",
            "iscsi": [
                {
                    "address": "10.21.200.124/24",
                    "gateway": "10.21.200.1",
                    "network_interface_groups": ["subnet-0", "subnet-1"],
                }
            ],
            "cbs_azure_iscsi": {
                "storage_endpoint_collection_identity": "/subscriptions/sub/resourcegroups/sec/providers/ms/userAssignedIdentities/secId",
                "load_balancer": "/subscriptions/sub/resourcegroups/sec/providers/ms/loadBalancers/sec-lb",
                "load_balancer_addresses": [],
            },
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # parameter 'cbs_azure_iscsi' has invalid address
        {
            "state": "present",
            "name": "se1",
            "display_name": "Storage Endpoint 1",
            "region": "region1",
            "availability_zone": "az1",
            "cbs_azure_iscsi": {
                "storage_endpoint_collection_identity": "/subscriptions/sub/resourcegroups/sec/providers/ms/userAssignedIdentities/secId",
                "load_balancer": "/subscriptions/sub/resourcegroups/sec/providers/ms/loadBalancers/sec-lb",
                "load_balancer_addresses": ["not an address"],
            },
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # parameter 'iscsi' has invalid 'gateway' address
        {
            "state": "present",
            "name": "se1",
            "display_name": "Storage Endpoint 1",
            "region": "region1",
            "availability_zone": "az1",
            "iscsi": [
                {
                    "address": "10.21.200.124/24",
                    "gateway": "not an address",
                    "network_interface_groups": ["subnet-0", "subnet-1"],
                }
            ],
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # parameter 'iscsi' has invalid 'address' address
        {
            "state": "present",
            "name": "se1",
            "display_name": "Storage Endpoint 1",
            "region": "region1",
            "availability_zone": "az1",
            "iscsi": [
                {
                    "address": "not an address",
                    "gateway": "10.21.200.1",
                    "network_interface_groups": ["subnet-0", "subnet-1"],
                }
            ],
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
    ],
)
def test_module_fails_on_wrong_parameters(m_se_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_se_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_se.main()

    # check api was not called at all
    api_obj.get_storage_endpoint.assert_not_called()
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_create_iscsi(m_se_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_se.main()

    assert exc.value.changed
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            endpoint_type="iscsi",
            iscsi=purefusion.StorageEndpointIscsiPost(
                discovery_interfaces=[
                    purefusion.StorageEndpointIscsiDiscoveryInterfacePost(**endpoint)
                    for endpoint in module_args["iscsi"]
                ]
            ),
        ),
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_create_cbs_azure_iscsi(m_se_api, m_op_api, module_args):
    del module_args["iscsi"]
    module_args["cbs_azure_iscsi"] = {
        "storage_endpoint_collection_identity": "/subscriptions/sub/resourcegroups/sec/providers/ms/userAssignedIdentities/secId",
        "load_balancer": "/subscriptions/sub/resourcegroups/sec/providers/ms/loadBalancers/sec-lb",
        "load_balancer_addresses": ["234.1.2.3"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_se.main()

    assert exc.value.changed is True
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            endpoint_type="cbs-azure-iscsi",
            cbs_azure_iscsi=purefusion.StorageEndpointCbsAzureIscsiPost(
                storage_endpoint_collection_identity=module_args["cbs_azure_iscsi"][
                    "storage_endpoint_collection_identity"
                ],
                load_balancer=module_args["cbs_azure_iscsi"]["load_balancer"],
                load_balancer_addresses=module_args["cbs_azure_iscsi"][
                    "load_balancer_addresses"
                ],
            ),
        ),
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_create_without_display_name(m_se_api, m_op_api, module_args):
    del module_args["display_name"]
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_se.main()

    assert exc.value.changed
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPost(
            name=module_args["name"],
            display_name=module_args["name"],
            endpoint_type="iscsi",
            iscsi=purefusion.StorageEndpointIscsiPost(
                discovery_interfaces=[
                    purefusion.StorageEndpointIscsiDiscoveryInterfacePost(**endpoint)
                    for endpoint in module_args["iscsi"]
                ]
            ),
        ),
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_se_create_exception(
    m_se_api, m_op_api, exec_original, exec_catch, module_args
):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_endpoint = MagicMock(side_effect=exec_original)
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            endpoint_type="iscsi",
            iscsi=purefusion.StorageEndpointIscsiPost(
                discovery_interfaces=[
                    purefusion.StorageEndpointIscsiDiscoveryInterfacePost(**endpoint)
                    for endpoint in module_args["iscsi"]
                ]
            ),
        ),
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_create_op_fails(m_se_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            endpoint_type="iscsi",
            iscsi=purefusion.StorageEndpointIscsiPost(
                discovery_interfaces=[
                    purefusion.StorageEndpointIscsiDiscoveryInterfacePost(**endpoint)
                    for endpoint in module_args["iscsi"]
                ]
            ),
        ),
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_se_create_op_exception(
    m_se_api, m_op_api, exec_original, exec_catch, module_args
):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            endpoint_type="iscsi",
            iscsi=purefusion.StorageEndpointIscsiPost(
                discovery_interfaces=[
                    purefusion.StorageEndpointIscsiDiscoveryInterfacePost(**endpoint)
                    for endpoint in module_args["iscsi"]
                ]
            ),
        ),
        region_name=module_args["region"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_update(m_se_api, m_op_api, module_args, current_se):
    current_se["display_name"] = None
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_se.main()

    assert exc.value.changed
    assert exc.value.id == current_se["id"]

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_se_update_exception(
    m_se_api, m_op_api, exec_original, exec_catch, module_args, current_se
):
    current_se["display_name"] = None
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(side_effect=exec_original)
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_update_op_fails(m_se_api, m_op_api, module_args, current_se):
    current_se["display_name"] = None
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_se_update_op_exception(
    m_se_api, m_op_api, exec_original, exec_catch, module_args, current_se
):
    current_se["display_name"] = None
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_called_once_with(
        purefusion.StorageEndpointPatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_present_not_changed(m_se_api, m_op_api, module_args, current_se):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_se.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_absent_not_changed(m_se_api, m_op_api, module_args, current_se):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_se.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_delete(m_se_api, m_op_api, module_args, current_se):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_se.main()

    assert exc.value.changed

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_se_delete_exception(
    m_se_api, m_op_api, exec_original, exec_catch, module_args, current_se
):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(side_effect=exec_original)
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
def test_se_delete_op_fails(m_se_api, m_op_api, module_args, current_se):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.StorageEndpointsApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_se_delete_op_exception(
    m_se_api, m_op_api, exec_original, exec_catch, module_args, current_se
):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_endpoint = MagicMock(
        return_value=purefusion.StorageEndpoint(**current_se)
    )
    api_obj.create_storage_endpoint = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_endpoint = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_endpoint = MagicMock(return_value=OperationMock(3))
    m_se_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_se.main()

    # check api was called correctly
    api_obj.get_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    api_obj.create_storage_endpoint.assert_not_called()
    api_obj.update_storage_endpoint.assert_not_called()
    api_obj.delete_storage_endpoint.assert_called_once_with(
        region_name=module_args["region"],
        storage_endpoint_name=module_args["name"],
        availability_zone_name=module_args["availability_zone"],
    )
    op_obj.get_operation.assert_called_once_with(3)
