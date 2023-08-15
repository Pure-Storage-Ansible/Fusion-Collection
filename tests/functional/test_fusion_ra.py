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
from ansible_collections.purestorage.fusion.plugins.modules import fusion_ra
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
fusion_ra.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@pytest.fixture
def module_args_present():
    return {
        "state": "present",
        "role": "az-admin",
        "user": "user1",
        "scope": "organization",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@pytest.fixture
def module_args_absent():
    return {
        "state": "absent",
        "role": "az-admin",
        "user": "user1",
        "scope": "organization",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # 'role` is missing
        {
            "state": "present",
            "tenant": "tenant1",
            "tenant_space": "tenant_space1",
            "user": "user1",
            "scope": "tenant_space",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # 'user` is missing
        {
            "state": "present",
            "role": "tenant-space-admin",
            "tenant": "tenant1",
            "tenant_space": "tenant_space1",
            "scope": "tenant_space",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # 'scope` is invalid
        {
            "state": "present",
            "role": "tenant-space-admin",
            "tenant": "tenant1",
            "tenant_space": "tenant_space1",
            "user": "user1",
            "scope": "bikini_bottom",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # 'state` is invalid
        {
            "state": "past",
            "role": "tenant-space-admin",
            "tenant": "tenant1",
            "tenant_space": "tenant_space1",
            "user": "user1",
            "scope": "tenant_space",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # 'tenant` is missing #1
        {
            "state": "present",
            "role": "tenant-space-admin",
            "tenant_space": "tenant_space1",
            "user": "user1",
            "scope": "tenant_space",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # 'tenant` is missing #2
        {
            "state": "present",
            "role": "tenant-space-admin",
            "tenant_space": "tenant_space1",
            "user": "user1",
            "scope": "tenant",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # 'tenant_space` is missing
        {
            "state": "present",
            "role": "tenant-space-admin",
            "tenant": "tenant1",
            "user": "user1",
            "scope": "tenant_space",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # both 'principal` and `user` are specified
        {
            "state": "present",
            "role": "tenant-space-admin",
            "tenant": "tenant1",
            "user": "user1",
            "principal": "123456",
            "scope": "tenant_space",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # both 'principal` and `api_client_key` are specified
        {
            "state": "present",
            "role": "tenant-space-admin",
            "tenant": "tenant1",
            "api_client_key": "pure1:apikey:asdf123XYZ",
            "principal": "123456",
            "scope": "tenant_space",
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
    ],
)
def test_module_args_wrong(ra_api_init, im_api_init, op_api_init, module_args):
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(side_effect=NotImplementedError())
    ra_mock.create_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_mock.delete_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=purefusion.rest.ApiException)
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleFailJson):
        fusion_ra.main()

    ra_mock.list_role_assignments.assert_not_called()
    ra_mock.create_role_assignment.assert_not_called()
    ra_mock.delete_role_assignment.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
def test_ra_user_does_not_exist(
    ra_api_init, im_api_init, op_api_init, module_args_present
):
    module_args = module_args_present
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(side_effect=purefusion.rest.ApiException)
    ra_mock.create_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_mock.delete_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(return_value=[])
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=purefusion.rest.ApiException)
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleFailJson):
        fusion_ra.main()

    ra_mock.list_role_assignments.assert_not_called()
    ra_mock.create_role_assignment.assert_not_called()
    ra_mock.delete_role_assignment.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
@pytest.mark.parametrize(
    "args_and_scope",
    [
        # organization scope
        (
            {
                "state": "present",
                "role": "az-admin",
                "user": "user1",
                "scope": "organization",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            "/",
        ),
        # tenant scope
        (
            {
                "state": "present",
                "role": "tenant-admin",
                "user": "user1",
                "scope": "tenant",
                "tenant": "tenant1",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            "/tenants/tenant1",
        ),
        # tenant space scope
        (
            {
                "state": "present",
                "role": "tenant-space-admin",
                "user": "user1",
                "scope": "tenant_space",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            "/tenants/tenant1/tenant-spaces/tenant_space1",
        ),
        # principal instead of user
        (
            {
                "state": "present",
                "role": "az-admin",
                "principal": "principal1",
                "scope": "organization",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            "/",
        ),
        # api_client_key instead of user
        (
            {
                "state": "present",
                "role": "az-admin",
                "api_client_key": "pure1:apikey:asdf123XYZ",
                "scope": "organization",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            "/",
        ),
    ],
)
def test_ra_create_ok(ra_api_init, im_api_init, op_api_init, args_and_scope):
    module_args = args_and_scope[0]
    ra_scope = args_and_scope[1]
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(return_value=[])
    ra_mock.create_role_assignment = MagicMock(return_value=OperationMock("op1"))
    ra_mock.delete_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=True))
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_ra.main()
    assert excinfo.value.changed
    assert excinfo.value.id == FAKE_RESOURCE_ID

    ra_mock.list_role_assignments.assert_called_with(
        role_name=module_args["role"], principal="principal1"
    )
    ra_mock.create_role_assignment.assert_called_with(
        purefusion.RoleAssignmentPost(scope=ra_scope, principal="principal1"),
        role_name=module_args["role"],
    )
    ra_mock.delete_role_assignment.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_ra_create_exception(
    ra_api_init,
    im_api_init,
    op_api_init,
    raised_exception,
    expected_exception,
    module_args_present,
):
    module_args = module_args_present
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(return_value=[])
    ra_mock.create_role_assignment = MagicMock(side_effect=raised_exception)
    ra_mock.delete_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception):
        fusion_ra.main()

    ra_mock.list_role_assignments.assert_called_with(
        role_name="az-admin", principal="principal1"
    )
    ra_mock.create_role_assignment.assert_called_with(
        purefusion.RoleAssignmentPost(scope="/", principal="principal1"),
        role_name="az-admin",
    )
    ra_mock.delete_role_assignment.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
def test_ra_create_op_fails(ra_api_init, im_api_init, op_api_init, module_args_present):
    module_args = module_args_present
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(return_value=[])
    ra_mock.create_role_assignment = MagicMock(return_value=OperationMock(id="op1"))
    ra_mock.delete_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=False))
    op_api_init.return_value = op_mock

    with pytest.raises(OperationException):
        fusion_ra.main()

    ra_mock.list_role_assignments.assert_called_with(
        role_name="az-admin", principal="principal1"
    )
    ra_mock.create_role_assignment.assert_called_with(
        purefusion.RoleAssignmentPost(scope="/", principal="principal1"),
        role_name="az-admin",
    )
    ra_mock.delete_role_assignment.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
@pytest.mark.parametrize(
    "args_and_scope",
    [
        # organization scope
        (
            {
                "state": "absent",
                "role": "az-admin",
                "user": "user1",
                "scope": "organization",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            purefusion.ResourceMetadata(
                id="org_id",
                name="org",
                self_link="/",
            ),
        ),
        # tenant scope
        (
            {
                "state": "absent",
                "role": "tenant-admin",
                "user": "user1",
                "scope": "tenant",
                "tenant": "tenant1",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            purefusion.ResourceMetadata(
                id="tenant1_id",
                name="tenant1",
                self_link="/tenants/tenant1",
            ),
        ),
        # tenant space scope
        (
            {
                "state": "absent",
                "role": "tenant-space-admin",
                "user": "user1",
                "scope": "tenant_space",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            purefusion.ResourceMetadata(
                id="tenant_space1_id",
                name="tenant_space1",
                self_link="/tenants/tenant1/tenant-spaces/tenant_space1",
            ),
        ),
    ],
)
def test_ra_delete_ok(ra_api_init, im_api_init, op_api_init, args_and_scope):
    module_args = args_and_scope[0]
    ra_scope = args_and_scope[1]
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(
        return_value=[
            purefusion.RoleAssignment(
                id="ra1_id",
                name="ra1",
                self_link="test_value",
                role=purefusion.RoleRef(
                    id="role1_id",
                    name=module_args["role"],
                    kind="Role",
                    self_link="test_value",
                ),
                scope=ra_scope,
                principal="principal1",
            )
        ]
    )
    ra_mock.create_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_mock.delete_role_assignment = MagicMock(return_value=OperationMock(id="op1"))
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        return_value=OperationMock(id="op1", success=True)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_ra.main()
    assert excinfo.value.changed

    ra_mock.list_role_assignments.assert_called_with(
        role_name=module_args["role"], principal="principal1"
    )
    ra_mock.create_role_assignment.assert_not_called()
    ra_mock.delete_role_assignment.assert_called_with(
        role_name=module_args["role"], role_assignment_name="ra1"
    )
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_ra_delete_exception(
    ra_api_init,
    im_api_init,
    op_api_init,
    raised_exception,
    expected_exception,
    module_args_absent,
):
    module_args = module_args_absent
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(
        return_value=[
            purefusion.RoleAssignment(
                id="ra1_id",
                name="ra1",
                self_link="test_value",
                role=purefusion.RoleRef(
                    id="role1_id",
                    name=module_args["role"],
                    kind="Role",
                    self_link="test_value",
                ),
                scope=purefusion.ResourceMetadata(
                    id="org_id",
                    name="org",
                    self_link="/",
                ),
                principal="principal1",
            )
        ]
    )
    ra_mock.create_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_mock.delete_role_assignment = MagicMock(side_effect=raised_exception)
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception):
        fusion_ra.main()

    ra_mock.list_role_assignments.assert_called_with(
        role_name=module_args["role"], principal="principal1"
    )
    ra_mock.create_role_assignment.assert_not_called()
    ra_mock.delete_role_assignment.assert_called_with(
        role_name=module_args["role"], role_assignment_name="ra1"
    )
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
def test_ra_delete_op_fails(ra_api_init, im_api_init, op_api_init, module_args_absent):
    module_args = module_args_absent
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(
        return_value=[
            purefusion.RoleAssignment(
                id="ra1_id",
                name="ra1",
                self_link="test_value",
                role=purefusion.RoleRef(
                    id="role1_id",
                    name=module_args["role"],
                    kind="Role",
                    self_link="test_value",
                ),
                scope=purefusion.ResourceMetadata(
                    id="org_id",
                    name="org",
                    self_link="/",
                ),
                principal="principal1",
            )
        ]
    )
    ra_mock.create_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_mock.delete_role_assignment = MagicMock(return_value=OperationMock(id="op1"))
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        return_value=OperationMock(id="op1", success=False)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(OperationException):
        fusion_ra.main()

    ra_mock.list_role_assignments.assert_called_with(
        role_name=module_args["role"], principal="principal1"
    )
    ra_mock.create_role_assignment.assert_not_called()
    ra_mock.delete_role_assignment.assert_called_with(
        role_name=module_args["role"], role_assignment_name="ra1"
    )
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
def test_ra_present_not_changed(
    ra_api_init, im_api_init, op_api_init, module_args_present
):
    module_args = module_args_present
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(
        return_value=[
            purefusion.RoleAssignment(
                id="ra1_id",
                name="ra1",
                self_link="test_value",
                role=purefusion.RoleRef(
                    id="role1_id",
                    name=module_args["role"],
                    kind="Role",
                    self_link="test_value",
                ),
                scope=purefusion.ResourceMetadata(
                    id="org_id",
                    name="org",
                    self_link="/",
                ),
                principal="principal1",
            )
        ]
    )
    ra_mock.create_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_mock.delete_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_ra.main()
    assert not excinfo.value.changed

    ra_mock.list_role_assignments.assert_called_with(
        role_name=module_args["role"], principal="principal1"
    )
    ra_mock.create_role_assignment.assert_not_called()
    ra_mock.delete_role_assignment.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.RoleAssignmentsApi")
def test_ra_absent_not_changed(
    ra_api_init, im_api_init, op_api_init, module_args_absent
):
    module_args = module_args_absent
    set_module_args(module_args)

    ra_mock = MagicMock()
    ra_mock.list_role_assignments = MagicMock(return_value=[])
    ra_mock.create_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_mock.delete_role_assignment = MagicMock(side_effect=NotImplementedError())
    ra_api_init.return_value = ra_mock

    im_mock = MagicMock()
    im_mock.list_users = MagicMock(
        return_value=[
            purefusion.User(
                id="principal1",
                self_link="test_value",
                name="user1",
                email="example@example.com",
            )
        ]
    )
    im_api_init.return_value = im_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_ra.main()
    assert not excinfo.value.changed

    ra_mock.list_role_assignments.assert_called_with(
        role_name=module_args["role"], principal="principal1"
    )
    ra_mock.create_role_assignment.assert_not_called()
    ra_mock.delete_role_assignment.assert_not_called()
    op_mock.get_operation.assert_not_called()
