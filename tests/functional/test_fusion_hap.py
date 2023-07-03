# -*- coding: utf-8 -*-

# (c) 2023, Andrej Pajtas (apajtas@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, patch

import fusion
import fusion as purefusion
import pytest
from ansible.module_utils import basic
from ansible_collections.purestorage.fusion.plugins.module_utils.errors import (
    OperationException,
)
from ansible_collections.purestorage.fusion.plugins.modules import fusion_hap
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
fusion_hap.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@pytest.fixture
def module_args():
    """Module arguments to create new HAP."""
    return {
        "state": "present",
        "name": "hap_new",
        "display_name": "Host Access Policy New",
        "iqn": "iqn.2023-05.com.purestorage:420qp2c0699",
        "personality": "aix",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }


@pytest.fixture
def current_hap_list():
    return fusion.HostAccessPolicyList(
        count=3,
        more_items_remaining=False,
        items=[
            fusion.HostAccessPolicy(
                id="1",
                self_link="self_link_value",
                name="hap1",
                display_name="Host Access Policy 1",
                iqn="iqn.2023-05.com.purestorage:420qp2c0261",
                personality="aix",
            ),
            fusion.HostAccessPolicy(
                id="2",
                self_link="self_link_value",
                name="hap2",
                display_name="Host Access Policy 2",
                iqn="iqn.2023-05.com.purestorage:420qp2c0262",
                personality="windows",
            ),
            fusion.HostAccessPolicy(
                id="3",
                self_link="self_link_value",
                name="hap3",
                display_name="Host Access Policy 3",
                iqn="iqn.2023-05.com.purestorage:420qp2c0263",
                personality="solaris",
            ),
        ],
    )


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'name` is missing
        {
            "state": "present",
            "display_name": "Host Access Policy 1",
            "iqn": "iqn.2023-05.com.purestorage:420qp2c0261",
            "personality": "aix",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # 'state' is 'present' but 'iqn' is not provided
        {
            "state": "present",
            "name": "hap1",
            "display_name": "Host Access Policy 1",
            "personality": "aix",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "hap1",
            "display_name": "Host Access Policy 1",
            "iqn": "iqn.2023-05.com.purestorage:420qp2c0261",
            "personality": "aix",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "hap1",
            "display_name": "Host Access Policy 1",
            "iqn": "iqn.2023-05.com.purestorage:420qp2c0261",
            "personality": "aix",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
        # parameter 'personality` has incorrect value
        {
            "state": "present",
            "name": "hap1",
            "display_name": "Host Access Policy 1",
            "iqn": "iqn.2023-05.com.purestorage:420qp2c0261",
            "personality": "cool",
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        },
    ],
)
def test_module_fails_on_wrong_parameters(
    m_hap_api, m_op_api, module_args, current_hap_list
):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_hap_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_hap.main()

    # check api was not called at all
    api_obj.list_host_access_policies.assert_not_called()
    api_obj.get_host_access_policy.assert_not_called()
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
@pytest.mark.parametrize(
    "name",
    [
        "",
        "space space",
        "toolongname_toolongname_toolongname_toolongname_toolongname_toolongname",
        "end_with_underscore_",
        "_start_with_underscore",
    ],
)
def test_hap_fail_on_invalid_name(
    m_hap_api, m_op_api, module_args, current_hap_list, name
):
    module_args["name"] = name
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_hap_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_hap.main()

    # check api was not called at all
    api_obj.list_host_access_policies.assert_not_called()
    api_obj.get_host_access_policy.assert_not_called()
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
@pytest.mark.parametrize(
    "iqn",
    [
        "qn.2023-05.com.purestorage:420qp2c0261",
        "iqn2023-05.com.purestorage:420qp2c0261",
        "iqn.202305.com.purestorage:420qp2c0261",
        "iqn.2023-05com.purestorage:420qp2c0261",
        "iqn.2023-05.com.purestorage:",
        "iqn.2023-05..purestorage:420qp2c0261",
        ".2023-05.com.purestorage:420qp2c0261",
        "2023-05.com.purestorage:420qp2c0261",
    ],
)
def test_hap_fail_on_invalid_iqn(
    m_hap_api, m_op_api, module_args, current_hap_list, iqn
):
    module_args["iqn"] = iqn
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(
        side_effect=purefusion.rest.ApiException
    )
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_hap_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_hap.main()

    # check api was not called at all
    api_obj.list_host_access_policies.assert_not_called()
    api_obj.get_host_access_policy.assert_not_called()
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_create(m_hap_api, m_op_api, module_args, current_hap_list):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_hap.main()

    assert exc.value.changed is True
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_called_once_with(
        purefusion.HostAccessPoliciesPost(
            iqn=module_args["iqn"],
            personality=module_args["personality"],
            name=module_args["name"],
            display_name=module_args["display_name"],
        )
    )
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_create_without_display_name(
    m_hap_api, m_op_api, module_args, current_hap_list
):
    del module_args["display_name"]
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_hap.main()

    assert exc.value.changed is True
    assert exc.value.id == FAKE_RESOURCE_ID

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_called_once_with(
        purefusion.HostAccessPoliciesPost(
            iqn=module_args["iqn"],
            personality=module_args["personality"],
            name=module_args["name"],
            display_name=module_args["name"],
        )
    )
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_create_iqn_exists(m_hap_api, m_op_api, module_args, current_hap_list):
    module_args["iqn"] = current_hap_list.items[0].iqn
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleFailJson) as exc:
        fusion_hap.main()

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_hap_create_exception(
    m_hap_api, m_op_api, exec_original, exec_catch, module_args, current_hap_list
):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(side_effect=exec_original)
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_hap.main()

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_called_once_with(
        purefusion.HostAccessPoliciesPost(
            iqn=module_args["iqn"],
            personality=module_args["personality"],
            name=module_args["name"],
            display_name=module_args["display_name"],
        )
    )
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_create_op_fails(m_hap_api, m_op_api, module_args, current_hap_list):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_hap.main()

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_called_once_with(
        purefusion.HostAccessPoliciesPost(
            iqn=module_args["iqn"],
            personality=module_args["personality"],
            name=module_args["name"],
            display_name=module_args["display_name"],
        )
    )
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_hap_create_op_exception(
    m_hap_api, m_op_api, exec_original, exec_catch, module_args, current_hap_list
):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_hap.main()

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_called_once_with(
        purefusion.HostAccessPoliciesPost(
            iqn=module_args["iqn"],
            personality=module_args["personality"],
            name=module_args["name"],
            display_name=module_args["display_name"],
        )
    )
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_hap_list_exception(
    m_hap_api, m_op_api, exec_original, exec_catch, module_args, current_hap_list
):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(side_effect=exec_original)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(side_effect=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_hap.main()

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_update(m_hap_api, m_op_api, module_args, current_hap_list):
    # NOTE: Host Access Policy does not have PATCH method, thus no action is expected
    current_hap = current_hap_list.items[0]
    module_args["name"] = current_hap.name
    module_args["display_name"] = "New Display Name"
    module_args["iqn"] = current_hap.iqn
    module_args["personality"] = (
        "windows" if current_hap.personality != "windows" else "linux"
    )
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(return_value=current_hap)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_hap.main()

    assert exc.value.changed is False

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_present_not_changed(m_hap_api, m_op_api, module_args, current_hap_list):
    current_hap = current_hap_list.items[0]
    module_args["name"] = current_hap.name
    module_args["display_name"] = current_hap.display_name
    module_args["iqn"] = current_hap.iqn
    module_args["personality"] = current_hap.personality
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(return_value=current_hap)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_hap.main()

    assert exc.value.changed is False

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_absent_not_changed(m_hap_api, m_op_api, module_args, current_hap_list):
    module_args["state"] = "absent"
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_hap.main()

    assert exc.value.changed is False

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_delete(m_hap_api, m_op_api, module_args, current_hap_list):
    current_hap = current_hap_list.items[0]
    module_args["state"] = "absent"
    module_args["name"] = current_hap.name
    module_args["display_name"] = current_hap.display_name
    module_args["iqn"] = current_hap.iqn
    module_args["personality"] = current_hap.personality
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(return_value=current_hap)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_hap.main()

    assert exc.value.changed is True

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_hap_delete_exception(
    m_hap_api, m_op_api, exec_original, exec_catch, module_args, current_hap_list
):
    current_hap = current_hap_list.items[0]
    module_args["state"] = "absent"
    module_args["name"] = current_hap.name
    module_args["display_name"] = current_hap.display_name
    module_args["iqn"] = current_hap.iqn
    module_args["personality"] = current_hap.personality
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(return_value=current_hap)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(side_effect=exec_original)
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_hap.main()

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
def test_hap_delete_op_fails(m_hap_api, m_op_api, module_args, current_hap_list):
    current_hap = current_hap_list.items[0]
    module_args["state"] = "absent"
    module_args["name"] = current_hap.name
    module_args["display_name"] = current_hap.display_name
    module_args["iqn"] = current_hap.iqn
    module_args["personality"] = current_hap.personality
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(return_value=current_hap)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_hap.main()

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.HostAccessPoliciesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_hap_delete_op_exception(
    m_hap_api, m_op_api, exec_original, exec_catch, module_args, current_hap_list
):
    current_hap = current_hap_list.items[0]
    module_args["state"] = "absent"
    module_args["name"] = current_hap.name
    module_args["display_name"] = current_hap.display_name
    module_args["iqn"] = current_hap.iqn
    module_args["personality"] = current_hap.personality
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_host_access_policies = MagicMock(return_value=current_hap_list)
    api_obj.get_host_access_policy = MagicMock(return_value=current_hap)
    api_obj.create_host_access_policy = MagicMock(return_value=OperationMock(1))
    api_obj.update_host_access_policy = MagicMock(return_value=OperationMock(2))
    api_obj.delete_host_access_policy = MagicMock(return_value=OperationMock(3))
    m_hap_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_hap.main()

    # check api was called correctly
    api_obj.list_host_access_policies.assert_called_once_with()
    api_obj.get_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    api_obj.create_host_access_policy.assert_not_called()
    api_obj.update_host_access_policy.assert_not_called()
    api_obj.delete_host_access_policy.assert_called_once_with(
        host_access_policy_name=module_args["name"]
    )
    op_obj.get_operation.assert_called_once_with(3)
