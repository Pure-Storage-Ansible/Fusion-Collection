# -*- coding: utf-8 -*-

# (c) 2023 Pure Storage, Inc.
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, patch, call

import fusion as purefusion
import pytest
from ansible.module_utils import basic
from ansible_collections.purestorage.fusion.plugins.module_utils.errors import (
    OperationException,
)
from ansible_collections.purestorage.fusion.plugins.modules import fusion_pg
from ansible_collections.purestorage.fusion.tests.functional.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    OperationMock,
    FAKE_RESOURCE_ID,
    exit_json,
    fail_json,
    set_module_args,
    side_effects_with_exceptions,
)
from urllib3.exceptions import HTTPError

# GLOBAL MOCKS
fusion_pg.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@pytest.fixture
def module_args_present():
    return {
        "name": "placement_group1",
        "tenant": "tenant1",
        "tenant_space": "tenant_space1",
        "region": "region1",
        "availability_zone": "availability_zone1",
        "storage_service": "storage_service1",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@pytest.fixture
def module_args_absent():
    return {
        "name": "placement_group1",
        "tenant": "tenant1",
        "tenant_space": "tenant_space1",
        "state": "absent",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
@pytest.mark.parametrize(
    ("module_args", "get_not_called"),
    [
        # 'name` is missing
        (
            {
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "region": "region1",
                "availability_zone": "availability_zone1",
                "storage_service": "storage_service1",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            True,
        ),
        # 'tenant` is missing
        (
            {
                "name": "placement_group1",
                "tenant_space": "tenant_space1",
                "region": "region1",
                "availability_zone": "availability_zone1",
                "storage_service": "storage_service1",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            True,
        ),
        # 'tenant space` is missing
        (
            {
                "name": "placement_group1",
                "tenant": "tenant1",
                "region": "region1",
                "availability_zone": "availability_zone1",
                "storage_service": "storage_service1",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            True,
        ),
        # 'region` is missing
        (
            {
                "name": "placement_group1",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "availability_zone": "availability_zone1",
                "storage_service": "storage_service1",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
        # 'availability_zone` is missing
        (
            {
                "name": "placement_group1",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "region": "region1",
                "storage_service": "storage_service1",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
        # 'storage_service` is missing
        (
            {
                "name": "placement_group1",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "region": "region1",
                "availability_zone": "availability_zone1",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
        # 'state` is invalid
        (
            {
                "name": "placement_group1",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "region": "region1",
                "availability_zone": "availability_zone1",
                "storage_service": "storage_service1",
                "state": "past",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            False,
        ),
    ],
)
def test_module_args_wrong(pg_api_init, op_api_init, module_args, get_not_called):
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(side_effect=purefusion.rest.ApiException)
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=purefusion.rest.ApiException)
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleFailJson):
        fusion_pg.main()

    if get_not_called:
        pg_mock.get_placement_group.assert_not_called()
    elif pg_mock.get_placement_group.called:
        pg_mock.get_placement_group.assert_called_with(
            tenant_name="tenant1",
            tenant_space_name="tenant_space1",
            placement_group_name="placement_group1",
        )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_create_ok(pg_api_init, op_api_init, module_args_present):
    module_args = module_args_present
    module_args["display_name"] = "some_display_name"
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(side_effect=purefusion.rest.ApiException)
    pg_mock.create_placement_group = MagicMock(return_value=OperationMock("op1"))
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=True))
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pg.main()
    assert excinfo.value.changed
    assert excinfo.value.id == FAKE_RESOURCE_ID

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_called_with(
        purefusion.PlacementGroupPost(
            name="placement_group1",
            display_name="some_display_name",
            availability_zone="availability_zone1",
            region="region1",
            storage_service="storage_service1",
        ),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
    )
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_create_without_display_name_ok(
    pg_api_init, op_api_init, module_args_present
):
    module_args = module_args_present
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(side_effect=purefusion.rest.ApiException)
    pg_mock.create_placement_group = MagicMock(return_value=OperationMock("op1"))
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=True))
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pg.main()
    assert excinfo.value.changed
    assert excinfo.value.id == FAKE_RESOURCE_ID

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_called_with(
        purefusion.PlacementGroupPost(
            name="placement_group1",
            display_name="placement_group1",
            availability_zone="availability_zone1",
            region="region1",
            storage_service="storage_service1",
        ),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
    )
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_pg_create_exception(
    pg_api_init, op_api_init, raised_exception, expected_exception, module_args_present
):
    set_module_args(module_args_present)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(side_effect=purefusion.rest.ApiException)
    pg_mock.create_placement_group = MagicMock(side_effect=raised_exception)
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception):
        fusion_pg.main()

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_called_with(
        purefusion.PlacementGroupPost(
            name="placement_group1",
            display_name="placement_group1",
            availability_zone="availability_zone1",
            region="region1",
            storage_service="storage_service1",
        ),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
    )
    pg_mock.delete_placement_group.assert_not_called()
    pg_mock.update_placement_group.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_create_op_fails(pg_api_init, op_api_init, module_args_present):
    module_args = module_args_present
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(side_effect=purefusion.rest.ApiException)
    pg_mock.create_placement_group = MagicMock(return_value=OperationMock(id="op1"))
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=False))
    op_api_init.return_value = op_mock

    with pytest.raises(OperationException):
        fusion_pg.main()

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_called_with(
        purefusion.PlacementGroupPost(
            name="placement_group1",
            display_name="placement_group1",
            availability_zone="availability_zone1",
            region="region1",
            storage_service="storage_service1",
        ),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
    )
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_create_triggers_update_ok(pg_api_init, op_api_init):
    module_args = {
        "name": "placement_group1",
        "display_name": "some_display_name",
        "tenant": "tenant1",
        "tenant_space": "tenant_space1",
        "region": "region1",
        "availability_zone": "availability_zone1",
        "storage_service": "storage_service1",
        "array": "array2",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    get_placement_group_effects = [
        purefusion.rest.ApiException(),
        purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="some_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        ),
    ]

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        side_effect=side_effects_with_exceptions(get_placement_group_effects)
    )
    pg_mock.create_placement_group = MagicMock(return_value=OperationMock("op1"))
    pg_mock.update_placement_group = MagicMock(return_value=OperationMock("op2"))
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=True))
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pg.main()
    assert excinfo.value.changed
    assert excinfo.value.id == FAKE_RESOURCE_ID

    pg_mock.get_placement_group.assert_has_calls(
        [
            call(
                tenant_name="tenant1",
                tenant_space_name="tenant_space1",
                placement_group_name="placement_group1",
            ),
            call(
                tenant_name="tenant1",
                tenant_space_name="tenant_space1",
                placement_group_name="placement_group1",
            ),
        ],
        any_order=True,
    )
    pg_mock.create_placement_group.assert_called_with(
        purefusion.PlacementGroupPost(
            name="placement_group1",
            display_name="some_display_name",
            availability_zone="availability_zone1",
            region="region1",
            storage_service="storage_service1",
        ),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
    )
    pg_mock.update_placement_group.assert_called_with(
        purefusion.PlacementGroupPatch(array=purefusion.NullableString(value="array2")),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_has_calls([call("op1"), call("op2")], any_order=True)


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_pg_create_triggers_update_exception(
    pg_api_init, op_api_init, raised_exception, expected_exception
):
    module_args = {
        "name": "placement_group1",
        "display_name": "some_display_name",
        "tenant": "tenant1",
        "tenant_space": "tenant_space1",
        "region": "region1",
        "availability_zone": "availability_zone1",
        "storage_service": "storage_service1",
        "array": "array2",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    get_placement_group_effects = [
        purefusion.rest.ApiException(),
        purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="some_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        ),
    ]

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        side_effect=side_effects_with_exceptions(get_placement_group_effects)
    )
    pg_mock.create_placement_group = MagicMock(return_value=OperationMock("op1"))
    pg_mock.update_placement_group = MagicMock(side_effect=raised_exception)
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(return_value=OperationMock("op1", success=True))
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception):
        fusion_pg.main()

    pg_mock.get_placement_group.assert_has_calls(
        [
            call(
                tenant_name="tenant1",
                tenant_space_name="tenant_space1",
                placement_group_name="placement_group1",
            ),
            call(
                tenant_name="tenant1",
                tenant_space_name="tenant_space1",
                placement_group_name="placement_group1",
            ),
        ],
        any_order=True,
    )
    pg_mock.create_placement_group.assert_called_with(
        purefusion.PlacementGroupPost(
            name="placement_group1",
            display_name="some_display_name",
            availability_zone="availability_zone1",
            region="region1",
            storage_service="storage_service1",
        ),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
    )
    pg_mock.update_placement_group.assert_called_with(
        purefusion.PlacementGroupPatch(array=purefusion.NullableString(value="array2")),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_create_triggers_update_op_fails(pg_api_init, op_api_init):
    module_args = {
        "name": "placement_group1",
        "display_name": "some_display_name",
        "tenant": "tenant1",
        "tenant_space": "tenant_space1",
        "region": "region1",
        "availability_zone": "availability_zone1",
        "storage_service": "storage_service1",
        "array": "array2",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    get_placement_group_effects = [
        purefusion.rest.ApiException(),
        purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="some_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        ),
    ]

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        side_effect=side_effects_with_exceptions(get_placement_group_effects)
    )
    pg_mock.create_placement_group = MagicMock(return_value=OperationMock("op1"))
    pg_mock.update_placement_group = MagicMock(return_value=OperationMock("op2"))
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        side_effect=[
            OperationMock("op1", success=True),
            OperationMock("op2", success=False),
        ]
    )
    op_api_init.return_value = op_mock

    with pytest.raises(OperationException):
        fusion_pg.main()

    pg_mock.get_placement_group.assert_has_calls(
        [
            call(
                tenant_name="tenant1",
                tenant_space_name="tenant_space1",
                placement_group_name="placement_group1",
            ),
            call(
                tenant_name="tenant1",
                tenant_space_name="tenant_space1",
                placement_group_name="placement_group1",
            ),
        ],
        any_order=True,
    )
    pg_mock.create_placement_group.assert_called_with(
        purefusion.PlacementGroupPost(
            name="placement_group1",
            display_name="some_display_name",
            availability_zone="availability_zone1",
            region="region1",
            storage_service="storage_service1",
        ),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
    )
    pg_mock.update_placement_group.assert_called_with(
        purefusion.PlacementGroupPatch(array=purefusion.NullableString(value="array2")),
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_has_calls([call("op1"), call("op2")])


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
@pytest.mark.parametrize(
    "test_case",
    [
        # patch 'display_name`
        {
            "current_state": purefusion.PlacementGroup(
                id="placement_group1_id",
                name="placement_group1",
                display_name="placement_group1_display_name",
                self_link="test_self_link",
                tenant=purefusion.TenantRef(
                    id="tenant1_id",
                    name="tenant1",
                    kind="Tenant",
                    self_link="some_self_link",
                ),
                tenant_space=purefusion.TenantSpaceRef(
                    id="tenant_space1_id",
                    name="tenant_space1",
                    kind="TenantSpace",
                    self_link="some_self_link",
                ),
                availability_zone=purefusion.AvailabilityZoneRef(
                    id="availability_zone1_id",
                    name="availability_zone1",
                    kind="AvailabilityZone",
                    self_link="some_self_link",
                ),
                placement_engine="heuristics",
                protocols=[],
                storage_service=purefusion.StorageServiceRef(
                    id="storage_service1_id",
                    name="storage_service",
                    kind="StorageService",
                    self_link="some_self_link",
                ),
                array=purefusion.ArrayRef(
                    id="array1_id",
                    name="array1",
                    kind="Array",
                    self_link="some_self_link",
                ),
            ),
            "module_args": {
                "name": "placement_group1",
                "display_name": "different_display_name",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "region": "region1",
                "availability_zone": "availability_zone1",
                "storage_service": "storage_service1",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            "patches": [
                purefusion.PlacementGroupPatch(
                    display_name=purefusion.NullableString(
                        value="different_display_name"
                    ),
                ),
            ],
        },
        # patch 'array`
        {
            "current_state": purefusion.PlacementGroup(
                id="placement_group1_id",
                name="placement_group1",
                display_name="placement_group1",
                self_link="test_self_link",
                tenant=purefusion.TenantRef(
                    id="tenant1_id",
                    name="tenant1",
                    kind="Tenant",
                    self_link="some_self_link",
                ),
                tenant_space=purefusion.TenantSpaceRef(
                    id="tenant_space1_id",
                    name="tenant_space1",
                    kind="TenantSpace",
                    self_link="some_self_link",
                ),
                availability_zone=purefusion.AvailabilityZoneRef(
                    id="availability_zone1_id",
                    name="availability_zone1",
                    kind="AvailabilityZone",
                    self_link="some_self_link",
                ),
                placement_engine="heuristics",
                protocols=[],
                storage_service=purefusion.StorageServiceRef(
                    id="storage_service1_id",
                    name="storage_service",
                    kind="StorageService",
                    self_link="some_self_link",
                ),
                array=purefusion.ArrayRef(
                    id="array1_id",
                    name="array1",
                    kind="Array",
                    self_link="some_self_link",
                ),
            ),
            "module_args": {
                "name": "placement_group1",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "region": "region1",
                "availability_zone": "availability_zone1",
                "storage_service": "storage_service1",
                "array": "array2",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            "patches": [
                purefusion.PlacementGroupPatch(
                    array=purefusion.NullableString(value="array2"),
                ),
            ],
        },
        # patch all
        {
            "current_state": purefusion.PlacementGroup(
                id="placement_group1_id",
                name="placement_group1",
                display_name="placement_group1_display_name",
                self_link="test_self_link",
                tenant=purefusion.TenantRef(
                    id="tenant1_id",
                    name="tenant1",
                    kind="Tenant",
                    self_link="some_self_link",
                ),
                tenant_space=purefusion.TenantSpaceRef(
                    id="tenant_space1_id",
                    name="tenant_space1",
                    kind="TenantSpace",
                    self_link="some_self_link",
                ),
                availability_zone=purefusion.AvailabilityZoneRef(
                    id="availability_zone1_id",
                    name="availability_zone1",
                    kind="AvailabilityZone",
                    self_link="some_self_link",
                ),
                placement_engine="heuristics",
                protocols=[],
                storage_service=purefusion.StorageServiceRef(
                    id="storage_service1_id",
                    name="storage_service",
                    kind="StorageService",
                    self_link="some_self_link",
                ),
                array=purefusion.ArrayRef(
                    id="array1_id",
                    name="array1",
                    kind="Array",
                    self_link="some_self_link",
                ),
            ),
            "module_args": {
                "name": "placement_group1",
                "display_name": "different_display_name",
                "tenant": "tenant1",
                "tenant_space": "tenant_space1",
                "region": "region1",
                "availability_zone": "availability_zone1",
                "storage_service": "storage_service1",
                "array": "array2",
                "state": "present",
                "issuer_id": "ABCD1234",
                "private_key_file": "private-key.pem",
            },
            "patches": [
                purefusion.PlacementGroupPatch(
                    display_name=purefusion.NullableString(
                        value="different_display_name"
                    ),
                ),
                purefusion.PlacementGroupPatch(
                    array=purefusion.NullableString(value="array2"),
                ),
            ],
        },
    ],
)
def test_pg_update_ok(pg_api_init, op_api_init, test_case):
    module_args = test_case["module_args"]
    set_module_args(module_args)

    get_operation_calls = [
        call("op{0}".format(i)) for i in range(len(test_case["patches"]))
    ]
    update_placement_group_return_vals = [
        OperationMock(id="op{0}".format(i)) for i in range(len(test_case["patches"]))
    ]
    update_placement_group_calls = [
        call(
            p,
            tenant_name="tenant1",
            tenant_space_name="tenant_space1",
            placement_group_name="placement_group1",
        )
        for p in test_case["patches"]
    ]

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(return_value=test_case["current_state"])
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(
        side_effect=update_placement_group_return_vals
    )
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        side_effect=lambda op_id: OperationMock(id=op_id, success=True)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pg.main()
    assert excinfo.value.changed
    assert excinfo.value.id == test_case["current_state"].id

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.update_placement_group.assert_has_calls(
        update_placement_group_calls, any_order=True
    )
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_has_calls(get_operation_calls, any_order=True)


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
@pytest.mark.parametrize("failing_patch", [0, 1])
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_pg_update_exception(
    pg_api_init, op_api_init, failing_patch, raised_exception, expected_exception
):
    module_args = {
        "name": "placement_group1",
        "display_name": "different_display_name",
        "tenant": "tenant1",
        "tenant_space": "tenant_space1",
        "region": "region1",
        "availability_zone": "availability_zone1",
        "storage_service": "storage_service1",
        "array": "array2",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    patches = [
        purefusion.PlacementGroupPatch(
            display_name=purefusion.NullableString(value="different_display_name"),
        ),
        purefusion.PlacementGroupPatch(
            array=purefusion.NullableString(value="array2"),
        ),
    ]

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        return_value=purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="placement_group1_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        )
    )
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(
        side_effect=throw_on_specific_patch(patches, failing_patch, raised_exception, 0)
    )
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        side_effect=lambda op_id: OperationMock(id=op_id, success=True)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception):
        fusion_pg.main()

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
@pytest.mark.parametrize("failing_patch", [0, 1])
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_pg_update_exception(
    pg_api_init, op_api_init, failing_patch, raised_exception, expected_exception
):
    module_args = {
        "name": "placement_group1",
        "display_name": "different_display_name",
        "tenant": "tenant1",
        "tenant_space": "tenant_space1",
        "region": "region1",
        "availability_zone": "availability_zone1",
        "storage_service": "storage_service1",
        "array": "array2",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    patches = [
        purefusion.PlacementGroupPatch(
            display_name=purefusion.NullableString(value="different_display_name"),
        ),
        purefusion.PlacementGroupPatch(
            array=purefusion.NullableString(value="array2"),
        ),
    ]

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        return_value=purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="placement_group1_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        )
    )
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(
        side_effect=throw_on_specific_patch(patches, failing_patch, raised_exception, 0)
    )
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        side_effect=lambda op_id: OperationMock(id=op_id, success=True)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception) as excinfo:
        fusion_pg.main()

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
@pytest.mark.parametrize("failing_patch", [0, 1])
def test_pg_update_op_fails(pg_api_init, op_api_init, failing_patch):
    module_args = {
        "name": "placement_group1",
        "display_name": "different_display_name",
        "tenant": "tenant1",
        "tenant_space": "tenant_space1",
        "region": "region1",
        "availability_zone": "availability_zone1",
        "storage_service": "storage_service1",
        "array": "array2",
        "state": "present",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    patches = [
        purefusion.PlacementGroupPatch(
            display_name=purefusion.NullableString(value="different_display_name"),
        ),
        purefusion.PlacementGroupPatch(
            array=purefusion.NullableString(value="array2"),
        ),
    ]
    ops = ["op0", "op1"]

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        return_value=purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="placement_group1_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        )
    )
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(
        side_effect=lambda patch, tenant_name, tenant_space_name, placement_group_name: OperationMock(
            id="op{0}".format(patches.index(patch))
        )
    )
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        side_effect=lambda id: OperationMock(
            id=id, success=ops.index(id) != failing_patch
        )
    )
    op_api_init.return_value = op_mock

    with pytest.raises(OperationException):
        fusion_pg.main()

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_delete_ok(pg_api_init, op_api_init, module_args_absent):
    module_args = module_args_absent
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        return_value=purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="placement_group1_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        )
    )
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(return_value=OperationMock(id="op1"))
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        return_value=OperationMock(id="op1", success=True)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pg.main()
    assert excinfo.value.changed

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
@pytest.mark.parametrize(
    ("raised_exception", "expected_exception"),
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_pg_delete_exception(
    pg_api_init, op_api_init, raised_exception, expected_exception, module_args_absent
):
    module_args = module_args_absent
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        return_value=purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="placement_group1_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        )
    )
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(side_effect=raised_exception)
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(expected_exception):
        fusion_pg.main()

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_delete_op_fails(pg_api_init, op_api_init, module_args_absent):
    module_args = module_args_absent
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        return_value=purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="placement_group1_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        )
    )
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(return_value=OperationMock(id="op1"))
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(
        return_value=OperationMock(id="op1", success=False)
    )
    op_api_init.return_value = op_mock

    with pytest.raises(OperationException):
        fusion_pg.main()

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    op_mock.get_operation.assert_called_with("op1")


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_present_not_changed(pg_api_init, op_api_init, module_args_present):
    module_args = module_args_present
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(
        return_value=purefusion.PlacementGroup(
            id="placement_group1_id",
            name="placement_group1",
            display_name="placement_group1_display_name",
            self_link="test_self_link",
            tenant=purefusion.TenantRef(
                id="tenant1_id",
                name="tenant1",
                kind="Tenant",
                self_link="some_self_link",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="tenant_space1_id",
                name="tenant_space1",
                kind="TenantSpace",
                self_link="some_self_link",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="availability_zone1_id",
                name="availability_zone1",
                kind="AvailabilityZone",
                self_link="some_self_link",
            ),
            placement_engine="heuristics",
            protocols=[],
            storage_service=purefusion.StorageServiceRef(
                id="storage_service1_id",
                name="storage_service",
                kind="StorageService",
                self_link="some_self_link",
            ),
            array=purefusion.ArrayRef(
                id="array1_id", name="array1", kind="Array", self_link="some_self_link"
            ),
        )
    )
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pg.main()
    assert not excinfo.value.changed

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.PlacementGroupsApi")
def test_pg_absent_not_changed(pg_api_init, op_api_init, module_args_absent):
    module_args = module_args_absent
    set_module_args(module_args)

    pg_mock = MagicMock()
    pg_mock.get_placement_group = MagicMock(side_effect=purefusion.rest.ApiException)
    pg_mock.create_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.update_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_mock.delete_placement_group = MagicMock(side_effect=NotImplementedError())
    pg_api_init.return_value = pg_mock

    op_mock = MagicMock()
    op_mock.get_operation = MagicMock(side_effect=NotImplementedError())
    op_api_init.return_value = op_mock

    with pytest.raises(AnsibleExitJson) as excinfo:
        fusion_pg.main()
    assert not excinfo.value.changed

    pg_mock.get_placement_group.assert_called_with(
        tenant_name="tenant1",
        tenant_space_name="tenant_space1",
        placement_group_name="placement_group1",
    )
    pg_mock.create_placement_group.assert_not_called()
    pg_mock.update_placement_group.assert_not_called()
    pg_mock.delete_placement_group.assert_not_called()
    op_mock.get_operation.assert_not_called()


def throw_on_specific_patch(patches, failing_patch_idx, raised_exception, op_offset):
    patches = patches.copy()

    def _update_side_effect(patch, **kwargs):
        idx = patches.index(patch)
        if idx == failing_patch_idx:
            raise raised_exception()
        return OperationMock(id="op{0}".format(op_offset + idx))

    return _update_side_effect
