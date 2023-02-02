#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: fusion_volume
version_added: '1.0.0'
short_description:  Manage volumes in Pure Storage Fusion
description:
- Create, update or delete a volume in Pure Storage Fusion.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
notes:
- Supports C(check mode).
options:
  name:
    description:
    - The name of the volume.
    type: str
    required: true
  display_name:
    description:
    - The human name of the volume.
    - If not provided, defaults to I(name).
    type: str
  state:
    description:
    - Define whether the volume should exist or not.
    type: str
    default: present
    choices: [ absent, present ]
  tenant:
    description:
    - The name of the tenant.
    type: str
    required: true
  tenant_space:
    description:
    - The name of the tenant space.
    type: str
    required: true
  eradicate:
    description:
    - Define whether to eradicate the volume on delete or leave in trash.
    type: bool
    default: 'no'
  size:
    description:
    - Volume size in M, G, T or P units.
    type: str
  storage_class:
    description:
    - The name of the storage class.
    type: str
  placement_group:
    description:
    - The name of the placement group.
    type: str
  protection_policy:
    description:
    - The name of the protection policy.
    type: str
  host_access_policies:
    description:
    - 'A list of host access policies to connect the volume to.
        To clear, assign empty list: host_access_policies: []'
    type: list
    elements: str
  rename:
    description:
    - New name for volume.
    type: str
extends_documentation_fragment:
- purestorage.fusion.purestorage.fusion
"""

EXAMPLES = r"""
- name: Create new volume named foo in storage_class fred
  purestorage.fusion.fusion_volume:
    name: foo
    storage_class: fred
    size: 1T
    tenant: test
    tenant_space: space_1
    state: present
    app_id: key_name
    key_file: "az-admin-private-key.pem"

- name: Extend the size of an existing volume named foo
  purestorage.fusion.fusion_volume:
    name: foo
    size: 2T
    tenant: test
    tenant_space: space_1
    state: present
    app_id: key_name
    key_file: "az-admin-private-key.pem"

- name: Rename volume named foo to bar
  purestorage.fusion.fusion_volume:
    name: foo
    rename: bar
    tenant: test
    tenant_space: space_1
    state: absent
    app_id: key_name
    key_file: "az-admin-private-key.pem"

- name: Delete volume named foo
  purestorage.fusion.fusion_volume:
    name: foo
    tenant: test
    tenant_space: space_1
    state: absent
    app_id: key_name
    key_file: "az-admin-private-key.pem"
"""

RETURN = r"""
"""

HAS_FUSION = True
try:
    import fusion as purefusion
except ImportError:
    HAS_FUSION = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.purestorage.fusion.plugins.module_utils.fusion import (
    get_fusion,
    fusion_argument_spec,
)
from ansible_collections.purestorage.fusion.plugins.module_utils.parsing import (
    parse_number_with_suffix,
    print_number_with_suffix,
)
from ansible_collections.purestorage.fusion.plugins.module_utils.operations import (
    await_operation,
)


def get_volume(module, fusion):
    """Return Volume or None"""
    volume_api_instance = purefusion.VolumesApi(fusion)
    try:
        return volume_api_instance.get_volume(
            tenant_name=module.params["tenant"],
            tenant_space_name=module.params["tenant_space"],
            volume_name=module.params["name"],
        )
    except purefusion.rest.ApiException:
        return None


def get_sc(module, fusion):
    """Return Storage Class or None"""
    pg_api_instance = purefusion.PlacementGroupsApi(fusion)
    pg = pg_api_instance.get_placement_group(
        tenant_name=module.params["tenant"],
        tenant_space_name=module.params["tenant_space"],
        placement_group_name=module.params["placement_group"],
    )
    sc_api_instance = purefusion.StorageClassesApi(fusion)
    try:
        return sc_api_instance.get_storage_class(
            storage_service_name=pg.storage_service.name,
            storage_class_name=module.params["storage_class"],
        )
    except purefusion.rest.ApiException:
        return None


def get_pg(module, fusion):
    """Return Placement Group or None"""
    pg_api_instance = purefusion.PlacementGroupsApi(fusion)
    try:
        return pg_api_instance.get_placement_group(
            tenant_name=module.params["tenant"],
            tenant_space_name=module.params["tenant_space"],
            placement_group_name=module.params["placement_group"],
        )
    except purefusion.rest.ApiException:
        return None


def get_pp(module, fusion):
    """Return Protection Policy or None"""
    pp_api_instance = purefusion.ProtectionPoliciesApi(fusion)
    try:
        return pp_api_instance.get_protection_policy(
            protection_policy_name=module.params["protection_policy"]
        )
    except purefusion.rest.ApiException:
        return None


def create_volume(module, fusion):
    """Create Volume"""

    volume_api_instance = purefusion.VolumesApi(fusion)

    if not module.params["size"]:
        module.fail_json(msg="Size for a new volume must be specified")
    size = parse_number_with_suffix(module, module.params["size"])
    sc_size_limit = get_sc(module, fusion).size_limit
    if size > sc_size_limit:
        module.fail_json(
            msg="Requested size {0} exceeds the storage class limit of {1}".format(
                module.params["size"], print_number_with_suffix(sc_size_limit)
            )
        )

    changed = True
    if not module.check_mode:
        if not module.params["display_name"]:
            display_name = module.params["name"]
        else:
            display_name = module.params["display_name"]
        try:
            volume = purefusion.VolumePost(
                size=size,
                storage_class=module.params["storage_class"],
                placement_group=module.params["placement_group"],
                name=module.params["name"],
                display_name=display_name,
            )
            op = volume_api_instance.create_volume(
                volume,
                tenant_name=module.params["tenant"],
                tenant_space_name=module.params["tenant_space"],
            )
            await_operation(module, fusion, op.id)
        except purefusion.rest.ApiException as err:
            module.fail_json(
                msg="Volume {0} creation failed: {1}".format(module.params["name"], err)
            )
    if module.params["host_access_policies"]:
        try:
            op = volume_api_instance.update_volume(
                purefusion.VolumePatch(
                    host_access_policies=purefusion.NullableString(
                        ",".join(module.params["host_access_policies"])
                    )
                ),
                volume_name=module.params["name"],
                tenant_name=module.params["tenant"],
                tenant_space_name=module.params["tenant_space"],
            )
            await_operation(module, fusion, op.id)
        except purefusion.rest.ApiException as err:
            module.fail_json(
                msg="Assigning host access policies to volume failed: {0}".format(err)
            )

    module.exit_json(changed=changed)


def update_volume(module, fusion):
    """Update Volume size, placement group, protection policy, storage class, HAPs"""
    volume_api_instance = purefusion.VolumesApi(fusion)

    current = volume_api_instance.get_volume(
        tenant_name=module.params["tenant"],
        tenant_space_name=module.params["tenant_space"],
        volume_name=module.params["name"],
    )
    wanted = module.params
    patches = []

    if wanted["display_name"] and wanted["display_name"] != current.display_name:
        patch = purefusion.VolumePatch(
            display_name=purefusion.NullableString(wanted["display_name"])
        )
        patches.append(patch)

    if wanted["size"]:
        wanted_size = parse_number_with_suffix(module, wanted["size"])
        if wanted_size != current.size:
            patch = purefusion.VolumePatch(size=purefusion.NullableSize(wanted_size))
            patches.append(patch)

    if (
        wanted["storage_class"]
        and wanted["storage_class"] != current.storage_class.name
    ):
        patch = purefusion.VolumePatch(
            storage_class=purefusion.NullableString(wanted["storage_class"])
        )
        patches.append(patch)

    if (
        wanted["placement_group"]
        and wanted["placement_group"] != current.placement_group.name
    ):
        patch = purefusion.VolumePatch(
            placement_group=purefusion.NullableString(wanted["placement_group"])
        )
        patches.append(patch)

    if (
        wanted["protection_policy"]
        and wanted["protection_policy"] != current.protection_policy.name
    ):
        patch = purefusion.VolumePatch(
            protection_policy=purefusion.NullableString(wanted["protection_policy"])
        )
        patches.append(patch)

    # 'wanted[...] is not None' to differentiate between empty list and no list
    if wanted["host_access_policies"] is not None:
        hap_api_instance = purefusion.HostAccessPoliciesApi(fusion)
        all_haps = hap_api_instance.list_host_access_policies()
        all_haps = set([hap.name for hap in all_haps.items])
        current_haps = (
            current.host_access_policies if current.host_access_policies else []
        )
        current_haps = set([hap.name for hap in current_haps])
        wanted_haps = set(
            [hap.strip() for hap in wanted["host_access_policies"]]
        )  # looks like yaml parsing can leave in spaces if coma-delimited
        if not wanted_haps <= all_haps:
            module.fail_json(msg="Some new host access policies don't exist")
        if not (wanted_haps <= current_haps and current_haps <= wanted_haps):
            patch = purefusion.VolumePatch(
                host_access_policies=purefusion.NullableString(",".join(wanted_haps))
            )
            patches.append(patch)

    if not module.check_mode:
        for patch in patches:
            try:
                op = volume_api_instance.update_volume(
                    patch,
                    volume_name=module.params["name"],
                    tenant_name=module.params["tenant"],
                    tenant_space_name=module.params["tenant_space"],
                )
                await_operation(module, fusion, op.id)
                changed = True
            except purefusion.rest.ApiException as err:
                module.fail_json(msg="Updating volume failed: {0}".format(err))

    changed = len(patches) != 0

    module.exit_json(changed=changed)


def delete_volume(module, fusion):
    """Delete Volume"""
    changed = False
    volume_api_instance = purefusion.VolumesApi(fusion)
    current = volume_api_instance.get_volume(
        tenant_name=module.params["tenant"],
        tenant_space_name=module.params["tenant_space"],
        volume_name=module.params["name"],
    )

    if current.host_access_policies:
        module.fail_json(
            """Please first manually unassign any host access policies from the volume before deleting it, like so:
            purestorage.fusion.fusion_volume:
                name: {0}
                tenant: {1}
                tenant_space: {2}
                host_access_policies: []
                state: present
            """.format(
                module.params["name"],
                module.params["tenant"],
                module.params["tenant_space"],
            )
        )

    hap_api_instance = purefusion.HostAccessPoliciesApi(fusion)
    all_haps = hap_api_instance.list_host_access_policies()
    if not module.check_mode:
        try:
            op = volume_api_instance.delete_volume(
                volume_name=module.params["name"],
                tenant_name=module.params["tenant"],
                tenant_space_name=module.params["tenant_space"],
            )
            await_operation(module, fusion, op.id)
        except purefusion.rest.ApiException:
            module.fail_json(
                msg="Delete volume {0} failed.".format(module.params["name"])
            )

    changed = True
    module.exit_json(changed=changed)


def main():
    """Main code"""
    argument_spec = fusion_argument_spec()
    deprecated_hosts = dict(
        name="hosts", date="2023-07-26", collection_name="purefusion.fusion"
    )
    argument_spec.update(
        dict(
            name=dict(type="str", required=True),
            display_name=dict(type="str"),
            rename=dict(
                type="str",
                removed_at_date="2023-07-26",
                removed_from_collection="purestorage.fusion",
            ),
            tenant=dict(type="str", required=True),
            tenant_space=dict(type="str", required=True),
            placement_group=dict(type="str"),
            storage_class=dict(type="str"),
            protection_policy=dict(type="str"),
            host_access_policies=dict(
                type="list", elements="str", deprecated_aliases=[deprecated_hosts]
            ),
            eradicate=dict(
                type="bool",
                default=False,
                removed_at_date="2023-07-26",
                removed_from_collection="purestorage.fusion",
            ),
            state=dict(type="str", default="present", choices=["absent", "present"]),
            size=dict(type="str"),
        )
    )

    required_if = [
        ("state", "present", ("size", "storage_class", "placement_group"), False),
    ]
    required_by = {
        "placement_group": "storage_class",
    }

    module = AnsibleModule(
        argument_spec,
        required_if=required_if,
        required_by=required_by,
        supports_check_mode=True,
    )

    size = module.params["size"]
    state = module.params["state"]
    fusion = get_fusion(module)
    volume = get_volume(module, fusion)

    if module.params["placement_group"] and not get_pg(module, fusion):
        module.fail_json(
            msg="Placement Group {0} does not exist in the provide "
            "tenant and tenant name space".format(module.params["placement_group"])
        )

    if module.params["storage_class"] and not get_sc(module, fusion):
        module.fail_json(
            msg="Storage Class {0} does not exist".format(
                module.params["storage_class"]
            )
        )

    if module.params["protection_policy"] and not get_pp(module, fusion):
        module.fail_json(
            msg="Protection Policy {0} does not exist".format(
                module.params["protection_policy"]
            )
        )

    if state == "present" and not volume:
        create_volume(module, fusion)
    elif state == "present" and volume:
        update_volume(module, fusion)
    elif state == "absent" and volume:
        delete_volume(module, fusion)

    module.exit_json(changed=False)


if __name__ == "__main__":
    main()
