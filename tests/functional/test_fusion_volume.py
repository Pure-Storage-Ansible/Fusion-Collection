# -*- coding: utf-8 -*-

# (c) 2023, Dmitriy Li (dmli@purestorage.com)
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
from ansible_collections.purestorage.fusion.plugins.modules import (
    fusion_volume,
)
from ansible_collections.purestorage.fusion.tests.functional.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    OperationMock,
    SuccessfulOperationMock,
    FAKE_RESOURCE_ID,
    exit_json,
    fail_json,
    set_module_args,
)
from urllib3.exceptions import HTTPError

# GLOBAL MOCKS
fusion_volume.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@pytest.fixture
def module_args():
    return {
        "name": "volume_1",
        "state": "present",
        "display_name": "Volume 1",
        "tenant": "t1",
        "tenant_space": "ts1",
        "placement_group": "pg1",
        "storage_class": "sc1",
        "protection_policy": "pp1",
        "host_access_policies": ["hap1"],
        "eradicate": False,
        "size": "1M",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }


@pytest.fixture
def absent_module_args(module_args):
    module_args.update(
        {"host_access_policies": [], "eradicate": True, "state": "absent"}
    )
    return module_args


@pytest.fixture
def volume():
    return {
        "name": "volume_1",
        "display_name": "Volume 1",
        "tenant": "t1",
        "tenant_space": "ts1",
        "storage_class": purefusion.StorageClassRef(
            name="sc1", id="id_1", kind="storage_class", self_link="self_link"
        ),
        "placement_group": purefusion.PlacementGroupRef(
            name="pg1", id="id_1", kind="placement_group", self_link="self_link"
        ),
        "protection_policy": purefusion.ProtectionPolicyRef(
            name="pp1", id="id_1", kind="protection_policy", self_link="self_link"
        ),
        "host_access_policies": [
            purefusion.HostAccessPolicyRef(
                name="hap1", id="id_1", kind="host_access_policy", self_link="self_link"
            )
        ],
        "serial_number": "sn1",
        "destroyed": False,
        "size": 1048576,
        "id": "id_1",
        "self_link": "self_link",
    }


@pytest.fixture
def destroyed_volume(volume):
    volume.update({"host_access_policies": [], "destroyed": True})
    return volume


@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "field,expected_exception_regex",
    [
        (
            "name",
            "missing required arguments: name",
        ),
        (
            "tenant",
            "missing required arguments: tenant",
        ),
        (
            "tenant_space",
            "missing required arguments: tenant_space",
        ),
        (
            "storage_class",
            "missing parameter\\(s\\) required by 'placement_group': storage_class",
        ),
        (
            "placement_group",
            "missing required arguments: placement_group",
        ),
        (
            "size",
            "Either `size`, `source_volume` or `source_snapshot` parameter is required when creating a volume.",
        ),
    ],
)
def test_module_fails_on_missing_parameters(
    mock_volumes_api, field, expected_exception_regex, module_args
):
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    mock_volumes_api.return_value = volumes_api
    del module_args[field]
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleFailJson) as ansible_error:
        fusion_volume.main()
    assert ansible_error.match(expected_exception_regex)


@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "dict_update,expected_exception_regex",
    [
        (
            {"extra": "value"},
            "Unsupported parameters for.*module: extra",
        ),
        (
            {"state": "absent"},
            "Volume must have no host access policies when destroyed",
        ),
        (
            {"eradicate": True},
            "'eradicate: true' cannot be used together with 'state: present'",
        ),
        (
            {"size": "1K"},
            "Size is not within the required range",
        ),
        (
            {"source_volume": "vol_name"},
            "parameters are mutually exclusive: source_volume|source_snapshot|size",
        ),
        (
            {"source_snapshot": "snap_name"},
            "parameters are mutually exclusive: source_volume|source_snapshot|size",
        ),
        (
            {"source_volume_snapshot": "vol_snap_name"},
            "parameters are required together: source_snapshot, source_volume_snapshot",
        ),
    ],
)
def test_module_fails_on_incorrect_parameters(
    mock_volumes_api, dict_update, expected_exception_regex, module_args
):
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    mock_volumes_api.return_value = volumes_api
    module_args.update(dict_update)
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleFailJson) as ansible_error:
        fusion_volume.main()
    assert ansible_error.match(expected_exception_regex)


@patch("fusion.VolumesApi")
def test_module_not_existent_volume_with_state_absent_not_changed(
    mock_volumes_api, module_args
):
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    mock_volumes_api.return_value = volumes_api
    del module_args["host_access_policies"]
    module_args["state"] = "absent"
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.changed is False
    volumes_api.get_volume.assert_called_once_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_create_successfully(mock_volumes_api, mock_operations_api, module_args):
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    volumes_api.create_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.changed is True
    assert exception.value.id == FAKE_RESOURCE_ID

    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.create_volume.assert_called_once_with(
        purefusion.VolumePost(
            size=1048576,
            storage_class=module_args["storage_class"],
            placement_group=module_args["placement_group"],
            name=module_args["name"],
            display_name=module_args["display_name"],
            protection_policy=module_args["protection_policy"],
        ),
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_create_from_volume_successfully(
    mock_volumes_api, mock_operations_api, module_args
):
    del module_args["size"]
    module_args["source_volume"] = "source_volume_name"

    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    volumes_api.create_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.changed is True
    assert exception.value.id == FAKE_RESOURCE_ID
    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.create_volume.assert_called_once_with(
        purefusion.VolumePost(
            source_link=f"/tenants/{module_args['tenant']}/tenant-spaces/{module_args['tenant_space']}/volumes/{module_args['source_volume']}",
            storage_class=module_args["storage_class"],
            placement_group=module_args["placement_group"],
            name=module_args["name"],
            display_name=module_args["display_name"],
            protection_policy=module_args["protection_policy"],
        ),
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_create_from_volume_snapshot_successfully(
    mock_volumes_api, mock_operations_api, module_args
):
    del module_args["size"]
    module_args["source_snapshot"] = "source_snapshot_name"
    module_args["source_volume_snapshot"] = "source_volume_snapshot_name"

    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    volumes_api.create_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.changed is True
    assert exception.value.id == FAKE_RESOURCE_ID
    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.create_volume.assert_called_once_with(
        purefusion.VolumePost(
            source_link=f"/tenants/{module_args['tenant']}/tenant-spaces/{module_args['tenant_space']}/snapshots/"
            f"{module_args['source_snapshot']}/volume-snapshots/{module_args['source_volume_snapshot']}",
            storage_class=module_args["storage_class"],
            placement_group=module_args["placement_group"],
            name=module_args["name"],
            display_name=module_args["display_name"],
            protection_policy=module_args["protection_policy"],
        ),
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_create_without_display_name_successfully(
    mock_volumes_api, mock_operations_api, module_args
):
    del module_args["display_name"]
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    volumes_api.create_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.changed is True
    assert exception.value.id == FAKE_RESOURCE_ID
    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.create_volume.assert_called_with(
        purefusion.VolumePost(
            size=1048576,
            storage_class=module_args["storage_class"],
            placement_group=module_args["placement_group"],
            name=module_args["name"],
            display_name=module_args["name"],
            protection_policy=module_args["protection_policy"],
        ),
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_volume_create_throws_exception(
    mock_volumes_api, mock_operations_api, exec_original, exec_catch, module_args
):
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    volumes_api.create_volume = MagicMock(side_effect=exec_original)
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()
    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.create_volume.assert_called_once_with(
        purefusion.VolumePost(
            size=1048576,
            storage_class=module_args["storage_class"],
            placement_group=module_args["placement_group"],
            name=module_args["name"],
            display_name=module_args["display_name"],
            protection_policy=module_args["protection_policy"],
        ),
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "updated_volume,called_with",
    [
        (
            {"destroyed": True},
            purefusion.VolumePatch(destroyed=purefusion.NullableBoolean(False)),
        ),
        (
            {"size": 1000000},
            purefusion.VolumePatch(size=purefusion.NullableSize(1048576)),
        ),
        (
            {
                "protection_policy": purefusion.ProtectionPolicyRef(
                    name="pp2",
                    id="id_1",
                    kind="protection_policy",
                    self_link="self_link",
                )
            },
            purefusion.VolumePatch(protection_policy=purefusion.NullableString("pp1")),
        ),
        (
            {"display_name": "Volume"},
            purefusion.VolumePatch(display_name=purefusion.NullableString("Volume 1")),
        ),
        (
            {
                "storage_class": purefusion.StorageClassRef(
                    name="sc2", id="id_1", kind="storage_class", self_link="self_link"
                )
            },
            purefusion.VolumePatch(storage_class=purefusion.NullableString("sc1")),
        ),
        (
            {
                "placement_group": purefusion.PlacementGroupRef(
                    name="pg2", id="id_1", kind="placement_group", self_link="self_link"
                )
            },
            purefusion.VolumePatch(placement_group=purefusion.NullableString("pg1")),
        ),
        (
            {
                "host_access_policies": [
                    purefusion.HostAccessPolicyRef(
                        name="hap2",
                        id="id_1",
                        kind="host_access_policy",
                        self_link="self_link",
                    )
                ]
            },
            purefusion.VolumePatch(
                host_access_policies=purefusion.NullableString("hap1")
            ),
        ),
    ],
)
def test_volume_update_with_state_present_executed_correctly(
    mock_volumes_api,
    mock_operations_api,
    updated_volume,
    called_with,
    module_args,
    volume,
):
    volume.update(updated_volume)
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.changed is True
    assert exception.value.id == volume["id"]
    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_called_once_with(
        called_with,
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "updated_volume,called_with",
    [
        (
            {"destroyed": False, "host_access_policies": []},
            purefusion.VolumePatch(destroyed=purefusion.NullableBoolean(True)),
        )
    ],
)
def test_volume_update_with_state_absent_executed_correctly(
    mock_volumes_api,
    mock_operations_api,
    updated_volume,
    called_with,
    module_args,
    volume,
):
    module_args["state"] = "absent"
    del module_args["host_access_policies"]
    volume.update(updated_volume)
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.changed is True
    assert exception.value.id == volume["id"]
    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_called_once_with(
        called_with,
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_volume_update_throws_exception(
    mock_volumes_api,
    mock_operations_api,
    exec_original,
    exec_catch,
    module_args,
    volume,
):
    module_args["display_name"] = "volume"
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(side_effect=exec_original)
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()

    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_called_once_with(
        purefusion.VolumePatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_volume_update_operation_throws_exception(
    mock_volumes_api,
    mock_operations_api,
    exec_original,
    exec_catch,
    module_args,
    volume,
):
    module_args["display_name"] = "volume"
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(side_effect=exec_original)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()

    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_called_once_with(
        purefusion.VolumePatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_delete_throws_validation_error(
    mock_volumes_api, mock_operations_api, absent_module_args, volume
):
    volume["host_access_policies"] = []
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    volumes_api.delete_volume = MagicMock(return_value=OperationMock(2))

    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(absent_module_args)
    # run module
    with pytest.raises(AnsibleFailJson) as ansible_fail:
        fusion_volume.main()
    assert ansible_fail.match(regexp="BUG: inconsistent state, eradicate_volume")
    volumes_api.get_volume.assert_called_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_called_once_with(
        purefusion.VolumePatch(destroyed=purefusion.NullableBoolean(True)),
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )
    volumes_api.delete_volume.assert_not_called()
    operations_api.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_delete_executed_correctly(
    mock_volumes_api, mock_operations_api, absent_module_args, destroyed_volume
):
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(
        return_value=purefusion.Volume(**destroyed_volume)
    )
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    volumes_api.delete_volume = MagicMock(return_value=OperationMock(2))

    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(absent_module_args)
    # run module
    with pytest.raises(AnsibleExitJson):
        fusion_volume.main()
    volumes_api.get_volume.assert_called_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_not_called()
    volumes_api.delete_volume.assert_called_once_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_volume_delete_throws_exception(
    mock_volumes_api,
    mock_operations_api,
    exec_original,
    exec_catch,
    absent_module_args,
    destroyed_volume,
):
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(
        return_value=purefusion.Volume(**destroyed_volume)
    )
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    volumes_api.delete_volume = MagicMock(side_effect=exec_original)

    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(absent_module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()
    volumes_api.get_volume.assert_called_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_not_called()
    volumes_api.delete_volume.assert_called_once_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )

    operations_api.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_volume_delete_operation_throws_exception(
    mock_volumes_api,
    mock_operations_api,
    exec_original,
    exec_catch,
    absent_module_args,
    destroyed_volume,
):
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(
        return_value=purefusion.Volume(**destroyed_volume)
    )
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    volumes_api.delete_volume = MagicMock(return_value=OperationMock(2))

    operations_api.get_operation = MagicMock(side_effect=exec_original)
    mock_volumes_api.return_value = volumes_api
    mock_operations_api.return_value = operations_api
    set_module_args(absent_module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()
    volumes_api.get_volume.assert_called_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_not_called()
    volumes_api.delete_volume.assert_called_once_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_module_updates_on_empty_array_of_haps(
    mock_volumes_api, mock_operations_api, module_args, volume
):
    volumes_api = purefusion.VolumesApi()
    operations_api = purefusion.OperationsApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    mock_operations_api.return_value = operations_api
    mock_volumes_api.return_value = volumes_api
    module_args.update({"state": "absent", "host_access_policies": []})
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.changed is True
    assert exception.value.id == volume["id"]
    volumes_api.get_volume.assert_called_with(
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    volumes_api.update_volume.assert_has_calls(
        [
            call(
                purefusion.VolumePatch(
                    host_access_policies=purefusion.NullableString(",".join([]))
                ),
                volume_name=volume["name"],
                tenant_name=volume["tenant"],
                tenant_space_name=volume["tenant_space"],
            ),
            call(
                purefusion.VolumePatch(destroyed=purefusion.NullableBoolean(True)),
                volume_name=volume["name"],
                tenant_name=volume["tenant"],
                tenant_space_name=volume["tenant_space"],
            ),
        ]
    )
