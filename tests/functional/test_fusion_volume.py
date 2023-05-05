# -*- coding: utf-8 -*-

# (c) 2023, Dmitriy Li (dmli@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, Mock, patch

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
    FailedOperationMock,
    OperationMock,
    SuccessfulOperationMock,
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
def storage_class():
    return {
        "name": "sc1",
        "display_name": "Storage Class 1",
        "storage_service": "storage_service_1",
        "size_limit": 4096,
        "iops_limit": 100,
        "bandwidth_limit": 1024,
        "self_link": "self_link",
        "id": "id_1",
    }


@pytest.fixture
def placement_group():
    return {
        "name": "pg1",
        "display_name": "pg1",
        "tenant": "t1",
        "tenant_space": "ts1",
        "availability_zone": "az1",
        "storage_service": "ss1",
        "self_link": "self_link",
        "id": "id_1",
    }


@pytest.fixture
def protection_policy():
    return {
        "name": "pp1",
        "display_name": "pp1",
        "self_link": "self_link",
        "id": "id_1",
        "objectives": "objectives",
    }


@pytest.fixture
def host_access_policies():
    return {
        "name": "hap1",
        "display_name": "hap1",
        "iqn": "iqn1",
        "personality": "linux",
        "self_link": "self_link",
        "id": "id_1",
    }


@pytest.fixture
def volume(storage_class, placement_group, protection_policy, host_access_policies):
    return {
        "name": "volume_1",
        "display_name": "Volume 1",
        "tenant": "t1",
        "tenant_space": "ts1",
        "storage_class": purefusion.StorageClass(**storage_class),
        "placement_group": purefusion.PlacementGroup(**placement_group),
        "protection_policy": purefusion.ProtectionPolicy(**protection_policy),
        "host_access_policies": [purefusion.HostAccessPolicy(**host_access_policies)],
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
            "missing parameter\(s\) required by 'placement_group': storage_class",
        ),
        (
            "placement_group",
            "missing required arguments: placement_group",
        ),
        (
            "size",
            "missing required arguments: size",
        ),
    ],
)
def test_module_fails_on_missing_parameters(
    volumes_api, field, expected_exception_regex, module_args
):
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
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
    ],
)
def test_module_fails_on_incorrect_parameters(
    volumes_api, dict_update, expected_exception_regex, module_args
):
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    module_args.update(dict_update)
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleFailJson) as ansible_error:
        fusion_volume.main()
    assert ansible_error.match(expected_exception_regex)


@patch("fusion.VolumesApi")
def test_module_not_existent_volume_with_state_absent_not_changed(
    volumes_api, module_args
):
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    del module_args["host_access_policies"]
    module_args["state"] = "absent"
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.args[0]["changed"] is False


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_create_successfully(volumes_api, operations_api, module_args):
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    volumes_api.create_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.args[0]["changed"] is True
    volumes_api.create_volume.assert_called_once()
    volumes_api.create_volume.assert_called_with(
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


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_create_without_display_name_successfully(
    volumes_api, operations_api, module_args
):
    del module_args["display_name"]
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    volumes_api.create_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.args[0]["changed"] is True
    volumes_api.create_volume.assert_called_once()
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
    volumes_api, operations_api, exec_original, exec_catch, module_args
):
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(side_effect=purefusion.rest.ApiException)
    volumes_api.create_volume = MagicMock(side_effect=exec_original)
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    set_module_args(module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()
    volumes_api.create_volume.assert_called_once()
    volumes_api.create_volume.assert_called_with(
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
                "protection_policy": purefusion.ProtectionPolicy(
                    **{
                        "name": "pp2",
                        "display_name": "pp2",
                        "self_link": "self_link",
                        "id": "id_1",
                        "objectives": "objectives",
                    }
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
                "storage_class": purefusion.StorageClass(
                    **{
                        "name": "sc2",
                        "display_name": "Storage Class 1",
                        "storage_service": "storage_service_1",
                        "size_limit": 4096,
                        "iops_limit": 100,
                        "bandwidth_limit": 1024,
                        "self_link": "self_link",
                        "id": "id_1",
                    }
                )
            },
            purefusion.VolumePatch(storage_class=purefusion.NullableString("sc1")),
        ),
        (
            {
                "placement_group": purefusion.PlacementGroup(
                    **{
                        "name": "pg2",
                        "display_name": "pg1",
                        "tenant": "t1",
                        "tenant_space": "ts1",
                        "availability_zone": "az1",
                        "storage_service": "ss1",
                        "self_link": "self_link",
                        "id": "id_1",
                    }
                )
            },
            purefusion.VolumePatch(placement_group=purefusion.NullableString("pg1")),
        ),
        (
            {
                "host_access_policies": [
                    purefusion.HostAccessPolicy(
                        **{
                            "name": "hap2",
                            "display_name": "hap2",
                            "iqn": "iqn1",
                            "personality": "linux",
                            "self_link": "self_link",
                            "id": "id_1",
                        }
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
    volumes_api, operations_api, updated_volume, called_with, module_args, volume
):
    volume.update(updated_volume)
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.args[0]["changed"] is True

    volumes_api.update_volume.assert_called_once()
    volumes_api.update_volume.assert_called_with(
        called_with,
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once()
    operations_api.get_operation.assert_called_with(1)


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
    volumes_api, operations_api, updated_volume, called_with, module_args, volume
):
    module_args["state"] = "absent"
    del module_args["host_access_policies"]
    volume.update(updated_volume)
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    set_module_args(module_args)
    # run module
    with pytest.raises(AnsibleExitJson) as exception:
        fusion_volume.main()
    assert exception.value.args[0]["changed"] is True

    volumes_api.update_volume.assert_called_once()
    volumes_api.update_volume.assert_called_with(
        called_with,
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once()
    operations_api.get_operation.assert_called_with(1)


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
    volumes_api, operations_api, exec_original, exec_catch, module_args, volume
):
    module_args["display_name"] = "volume"
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(side_effect=exec_original)
    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    set_module_args(module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()

    volumes_api.update_volume.assert_called_once()
    volumes_api.update_volume.assert_called_with(
        purefusion.VolumePatch(display_name=purefusion.NullableString("volume")),
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
    volumes_api, operations_api, exec_original, exec_catch, module_args, volume
):
    module_args["display_name"] = "volume"
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    operations_api.get_operation = MagicMock(side_effect=exec_original)
    set_module_args(module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()

    volumes_api.update_volume.assert_called_once()
    volumes_api.update_volume.assert_called_with(
        purefusion.VolumePatch(display_name=purefusion.NullableString("volume")),
        volume_name=module_args["name"],
        tenant_name=module_args["tenant"],
        tenant_space_name=module_args["tenant_space"],
    )
    operations_api.get_operation.assert_called_once()


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_delete_throws_validation_error(
    volumes_api, operations_api, absent_module_args, volume
):
    volume["host_access_policies"] = []
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(return_value=purefusion.Volume(**volume))
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    volumes_api.delete_volume = MagicMock(return_value=OperationMock(2))

    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    set_module_args(absent_module_args)
    # run module
    with pytest.raises(AnsibleFailJson) as ansible_fail:
        fusion_volume.main()
    assert ansible_fail.match(regexp="BUG: inconsistent state, eradicate_volume")
    volumes_api.delete_volume.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.VolumesApi")
def test_volume_delete_executed_correctly(
    volumes_api, operations_api, absent_module_args, destroyed_volume
):
    operations_api = purefusion.OperationsApi()
    volumes_api = purefusion.VolumesApi()
    volumes_api.get_volume = MagicMock(
        return_value=purefusion.Volume(**destroyed_volume)
    )
    volumes_api.update_volume = MagicMock(return_value=OperationMock(1))
    volumes_api.delete_volume = MagicMock(return_value=OperationMock(2))

    operations_api.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    set_module_args(absent_module_args)
    # run module
    with pytest.raises(AnsibleExitJson):
        fusion_volume.main()
    volumes_api.delete_volume.assert_called_once()
    volumes_api.delete_volume.assert_called_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )

    operations_api.get_operation.assert_called_once()


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
    volumes_api,
    operations_api,
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
    set_module_args(absent_module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()
    volumes_api.delete_volume.assert_called_once()
    volumes_api.delete_volume.assert_called_with(
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
    volumes_api,
    operations_api,
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
    set_module_args(absent_module_args)
    # run module
    with pytest.raises(exec_catch):
        fusion_volume.main()
    volumes_api.delete_volume.assert_called_once()
    volumes_api.delete_volume.assert_called_with(
        volume_name=absent_module_args["name"],
        tenant_name=absent_module_args["tenant"],
        tenant_space_name=absent_module_args["tenant_space"],
    )

    operations_api.get_operation.assert_called_once()
