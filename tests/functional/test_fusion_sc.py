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
from ansible_collections.purestorage.fusion.plugins.modules import fusion_sc
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
fusion_sc.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'name` is missing
        {
            "state": "present",
            "display_name": "Storage Class 1",
            "iops_limit": "2000000",
            "bw_limit": "256G",
            "size_limit": "2P",
            "storage_service": "ss1",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # required parameter 'storage_service` is missing
        {
            "state": "present",
            "name": "sc1",
            "display_name": "Storage Class 1",
            "iops_limit": "2000000",
            "bw_limit": "256G",
            "size_limit": "2P",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "sc1",
            "display_name": "Storage Class 1",
            "iops_limit": "2000000",
            "bw_limit": "256G",
            "size_limit": "2P",
            "storage_service": "ss1",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "sc1",
            "display_name": "Storage Class 1",
            "iops_limit": "2000000",
            "bw_limit": "256G",
            "size_limit": "2P",
            "storage_service": "ss1",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
    ],
)
def test_module_fails_on_wrong_parameters(m_sc_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_sc_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_sc.main()

    # check api was not called at all
    api_obj.get_storage_class.assert_not_called()
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize(
    "iops_arg,iops_exp",
    [("2000000", 2_000_000), (None, 100_000_000)],
)
@pytest.mark.parametrize(
    "bw_arg,bw_exp",
    [("256G", 274877906944), (None, 549755813888)],
)
@pytest.mark.parametrize(
    "size_arg,size_exp",
    [("2P", 2251799813685248), (None, 4503599627370496)],
)
def test_sc_create(
    m_sc_api, m_op_api, iops_arg, iops_exp, bw_arg, bw_exp, size_arg, size_exp
):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": iops_arg,
        "bw_limit": bw_arg,
        "size_limit": size_arg,
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_sc.main()

    assert exc.value.changed
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_called_once_with(
        purefusion.StorageClassPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            iops_limit=iops_exp,
            bandwidth_limit=bw_exp,
            size_limit=size_exp,
        ),
        storage_service_name=module_args["storage_service"],
    )
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_create_without_display_name(m_sc_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "sc1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    parsed_size = 2251799813685248
    parsed_bandwidth = 274877906944
    parsed_iops = 2000000
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_sc.main()

    assert exc.value.changed
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_called_once_with(
        purefusion.StorageClassPost(
            name=module_args["name"],
            display_name=module_args["name"],
            iops_limit=parsed_iops,
            bandwidth_limit=parsed_bandwidth,
            size_limit=parsed_size,
        ),
        storage_service_name=module_args["storage_service"],
    )
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize("iops_arg", [-100, 99, 100_000_001])
def test_sc_create_iops_out_of_range(m_sc_api, m_op_api, iops_arg):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": iops_arg,
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize("bw_arg", ["1023K", "513G"])
def test_sc_create_bw_out_of_range(m_sc_api, m_op_api, bw_arg):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": bw_arg,
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize("size_arg", ["1023K", "5P"])
def test_sc_create_size_out_of_range(m_sc_api, m_op_api, size_arg):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": size_arg,
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_sc_create_exception(m_sc_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    parsed_size = 2251799813685248
    parsed_bandwidth = 274877906944
    parsed_iops = 2000000
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(side_effect=exec_original)
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_called_once_with(
        purefusion.StorageClassPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            iops_limit=parsed_iops,
            bandwidth_limit=parsed_bandwidth,
            size_limit=parsed_size,
        ),
        storage_service_name=module_args["storage_service"],
    )
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_create_op_fails(m_sc_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    parsed_size = 2251799813685248
    parsed_bandwidth = 274877906944
    parsed_iops = 2000000
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_called_once_with(
        purefusion.StorageClassPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            iops_limit=parsed_iops,
            bandwidth_limit=parsed_bandwidth,
            size_limit=parsed_size,
        ),
        storage_service_name=module_args["storage_service"],
    )
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_sc_create_op_exception(m_sc_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    parsed_size = 2251799813685248
    parsed_bandwidth = 274877906944
    parsed_iops = 2000000
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_called_once_with(
        purefusion.StorageClassPost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            iops_limit=parsed_iops,
            bandwidth_limit=parsed_bandwidth,
            size_limit=parsed_size,
        ),
        storage_service_name=module_args["storage_service"],
    )
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_update(m_sc_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_sc.main()

    assert exc.value.changed
    assert exc.value.id == current_sc["id"]

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_called_once_with(
        purefusion.StorageClassPatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_sc_update_exception(m_sc_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(side_effect=exec_original)
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_called_once_with(
        purefusion.StorageClassPatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_update_op_fails(m_sc_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_called_once_with(
        purefusion.StorageClassPatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_sc_update_op_exception(m_sc_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_called_once_with(
        purefusion.StorageClassPatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_present_not_changed(m_sc_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": module_args["display_name"],
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_sc.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_absent_not_changed(m_sc_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_sc.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_update_limits_not_changed(m_sc_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": module_args["display_name"],
        "iops_limit": "1500000",  # does not match but shouldn't be updated!
        "bandwidth_limit": "300G",  # does not match but shouldn't be updated!
        "size_limit": "1P",  # does not match but shouldn't be updated!
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_sc.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_delete(m_sc_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_sc.main()

    assert exc.value.changed

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_sc_delete_exception(m_sc_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "absent",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(side_effect=exec_original)
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
def test_sc_delete_op_fails(m_sc_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.StorageClassesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_sc_delete_op_exception(m_sc_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "absent",
        "name": "sc1",
        "display_name": "Storage Class 1",
        "iops_limit": "2000000",
        "bw_limit": "256G",
        "size_limit": "2P",
        "storage_service": "ss1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_sc = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "iops_limit": "2000000",
        "bandwidth_limit": "256G",
        "size_limit": "2P",
        "storage_service": module_args["storage_service"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_class = MagicMock(
        return_value=purefusion.StorageClass(**current_sc)
    )
    api_obj.create_storage_class = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_class = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_class = MagicMock(return_value=OperationMock(3))
    m_sc_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_sc.main()

    # check api was called correctly
    api_obj.get_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    api_obj.create_storage_class.assert_not_called()
    api_obj.update_storage_class.assert_not_called()
    api_obj.delete_storage_class.assert_called_once_with(
        storage_class_name=module_args["name"],
        storage_service_name=module_args["storage_service"],
    )
    op_obj.get_operation.assert_called_once_with(3)
