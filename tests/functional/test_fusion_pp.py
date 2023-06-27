# -*- coding: utf-8 -*-

# (c) 2023 Pure Storage, Inc.
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
from ansible_collections.purestorage.fusion.plugins.modules import fusion_pp
from ansible_collections.purestorage.fusion.tests.functional.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    OperationMock,
    FAKE_RESOURCE_ID,
    exit_json,
    fail_json,
    set_module_args,
)
from urllib3.exceptions import HTTPError

# GLOBAL MOCKS
fusion_pp.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@pytest.fixture
def module_args_present():
    return {
        "name": "protection_policy1",
        "local_rpo": "1H43M",
        "local_retention": "2H",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@pytest.fixture
def module_args_absent():
    return {
        "name": "protection_policy1",
        "state": "absent",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
@pytest.mark.parametrize(
    ("module_args", "get_not_called"),
    [
        # 'name` is missing
        (
            {
                "local_rpo": 10,
                "local_retention": "10M",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            True,
        ),
        # 'local_rpo` is missing
        (
            {
                "name": "protection_policy1",
                "local_retention": "10M",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
        # 'local_retention` is missing
        (
            {
                "name": "protection_policy1",
                "local_rpo": 10,
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
        # 'local_rpo` is invalid
        (
            {
                "name": "protection_policy1",
                "local_rpo": 10,
                "local_retention": "10yen",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
        # 'local_retention` is invalid
        (
            {
                "name": "protection_policy1",
                "local_rpo": "10bread",
                "local_retention": "bre",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
        # 'state` is invalid
        (
            {
                "name": "protection_policy1",
                "local_rpo": 10,
                "local_retention": 10,
                "state": "past",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
    ],
)
def test_module_args_wrong(pp_api_init, op_api_init, module_args, get_not_called):
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    pp_mock.create_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_mock.delete_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=purefusion.rest.ApiException)
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleFailJson):
        fusion_pp.main()

    if get_not_called:
        pp_mock.get_protection_policy.assert_not_called()
    if pp_mock.get_protection_policy.called:
        pp_mock.get_protection_policy.assert_called_with(
            protection_policy_name="protection_policy1"
        )
    pp_mock.create_protection_policy.assert_not_called()
    pp_mock.delete_protection_policy.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
def test_pp_create_ok(pp_api_init, op_api_init, module_args_present):
    module_args = module_args_present
    module_args["display_name"] = "some_display_name"

    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    pp_mock.create_protection_policy = MagicMock(return_value=OperationMock("op1"))
    pp_mock.delete_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=True))
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pp.main()
    assert excinfo.value.changed
    assert excinfo.value.id == FAKE_RESOURCE_ID

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_called_with(
        purefusion.ProtectionPolicyPost(
            name="protection_policy1",
            display_name="some_display_name",
            objectives=[
                purefusion.RPO(type="RPO", rpo="PT103M"),
                purefusion.Retention(type="Retention", after="PT120M"),
            ],
        )
    )
    pp_mock.delete_protection_policy.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
def test_pp_create_without_display_name_ok(
    pp_api_init, op_api_init, module_args_present
):
    module_args = module_args_present
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    pp_mock.create_protection_policy = MagicMock(return_value=OperationMock("op1"))
    pp_mock.delete_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=True))
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pp.main()
    assert excinfo.value.changed
    assert excinfo.value.id == FAKE_RESOURCE_ID

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_called_with(
        purefusion.ProtectionPolicyPost(
            name="protection_policy1",
            display_name="protection_policy1",
            objectives=[
                purefusion.RPO(type="RPO", rpo="PT103M"),
                purefusion.Retention(type="Retention", after="PT120M"),
            ],
        )
    )
    pp_mock.delete_protection_policy.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_pp_create_exception(
    pp_api_init, op_api_init, raised_exception, expected_exception, module_args_present
):
    module_args = module_args_present
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    pp_mock.create_protection_policy = MagicMock(side_effect=raised_exception)
    pp_mock.delete_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception):
        fusion_pp.main()

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_called_with(
        purefusion.ProtectionPolicyPost(
            name="protection_policy1",
            display_name="protection_policy1",
            objectives=[
                purefusion.RPO(type="RPO", rpo="PT103M"),
                purefusion.Retention(type="Retention", after="PT120M"),
            ],
        )
    )
    pp_mock.delete_protection_policy.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
def test_pp_create_op_fails(pp_api_init, op_api_init, module_args_present):
    module_args = module_args_present
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    pp_mock.create_protection_policy = MagicMock(return_value=OperationMock(id="op1"))
    pp_mock.delete_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=False))
    op_api_init.return_value = op_mock

    with pytest.raises(OperationException):
        fusion_pp.main()

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_called_with(
        purefusion.ProtectionPolicyPost(
            name="protection_policy1",
            display_name="protection_policy1",
            objectives=[
                purefusion.RPO(type="RPO", rpo="PT103M"),
                purefusion.Retention(type="Retention", after="PT120M"),
            ],
        )
    )
    pp_mock.delete_protection_policy.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
def test_pp_delete_ok(pp_api_init, op_api_init, module_args_absent):
    module_args = module_args_absent
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(
        return_value=purefusion.ProtectionPolicy(
            id="protection_policy1_id",
            name="protection_policy1",
            display_name="protection_policy1_display_name",
            self_link="test_self_link",
            objectives=[
                purefusion.RPO(type="RPO", rpo="PT103M"),
                purefusion.Retention(type="Retention", after="PT120M"),
            ],
        )
    )
    pp_mock.create_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_mock.delete_protection_policy = MagicMock(return_value=OperationMock(id="op1"))
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        return_value=OperationMock(id="op1", success=True)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pp.main()
    assert excinfo.value.changed

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_not_called()
    pp_mock.delete_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_pp_delete_exception(
    pp_api_init, op_api_init, raised_exception, expected_exception, module_args_absent
):
    module_args = module_args_absent
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(
        return_value=purefusion.ProtectionPolicy(
            id="protection_policy1_id",
            name="protection_policy1",
            display_name="protection_policy1_display_name",
            self_link="test_self_link",
            objectives=[
                purefusion.RPO(type="RPO", rpo="PT103M"),
                purefusion.Retention(type="Retention", after="PT120M"),
            ],
        )
    )
    pp_mock.create_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_mock.delete_protection_policy = MagicMock(side_effect=raised_exception)
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception):
        fusion_pp.main()

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_not_called()
    pp_mock.delete_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
def test_pp_delete_op_fails(pp_api_init, op_api_init, module_args_absent):
    module_args = module_args_absent
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(
        return_value=purefusion.ProtectionPolicy(
            id="protection_policy1_id",
            name="protection_policy1",
            display_name="protection_policy1_display_name",
            self_link="test_self_link",
            objectives=[
                purefusion.RPO(type="RPO", rpo="PT103M"),
                purefusion.Retention(type="Retention", after="PT120M"),
            ],
        )
    )
    pp_mock.create_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_mock.delete_protection_policy = MagicMock(return_value=OperationMock(id="op1"))
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        return_value=OperationMock(id="op1", success=False)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(OperationException):
        fusion_pp.main()

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_not_called()
    pp_mock.delete_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
def test_pp_present_not_changed(pp_api_init, op_api_init):
    module_args = {
        "name": "protection_policy1",
        "display_name": "some_display_name",
        "local_rpo": "43M",
        "local_retention": "2H",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(
        return_value=purefusion.ProtectionPolicy(
            id="protection_policy1_id",
            name="protection_policy1",
            display_name="some_display_name",
            self_link="test_self_link",
            objectives=[
                purefusion.RPO(type="RPO", rpo="PT43M"),
                purefusion.Retention(type="Retention", after="PT120M"),
            ],
        )
    )
    pp_mock.create_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_mock.delete_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pp.main()
    assert not excinfo.value.changed

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_not_called()
    pp_mock.delete_protection_policy.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.ProtectionPoliciesApi")
def test_pp_absent_not_changed(pp_api_init, op_api_init, module_args_absent):
    module_args = module_args_absent
    set_module_args(module_args)

    pp_mock = MagicMock()
    pp_mock.get_protection_policy = MagicMock(side_effect=purefusion.rest.ApiException)
    pp_mock.create_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_mock.delete_protection_policy = MagicMock(side_effect=NotImplementedError())
    pp_api_init.return_value = pp_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pp.main()
    assert not excinfo.value.changed

    pp_mock.get_protection_policy.assert_called_with(
        protection_policy_name="protection_policy1"
    )
    pp_mock.create_protection_policy.assert_not_called()
    pp_mock.delete_protection_policy.assert_not_called()
    op_mock.get_operation.assert_not_called()
