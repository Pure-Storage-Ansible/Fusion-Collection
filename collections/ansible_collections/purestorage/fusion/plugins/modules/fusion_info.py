#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: fusion_info
version_added: '1.0.0'
short_description: Collect information from Pure Fusion
description:
  - Collect information from a Pure Fusion environment.
  - By default, the module will collect basic
    information including counts for arrays, availabiliy_zones, volunmes, snapshots
    . Fleet capacity and data reduction rates are also provided.
  - Additional information can be collected based on the configured set of arguements.
author:
  - Pure Storage ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  gather_subset:
    description:
      - When supplied, this argument will define the information to be collected.
        Possible values for this include all, minimum, appliances, subscriptions,
        contracts
    type: list
    elements: str
    required: false
    default: minimum
extends_documentation_fragment:
  - purestorage.fusion.purestorage.fusion
"""

EXAMPLES = r"""
- name: collect default set of information
  fusion_info:
    app_id: key_name
    key_file: "az-admin-private-key.pem"
    register: fusion_info

- name: show default information
  debug:
    msg: "{{ fusion_info['fusion_info']['default'] }}"

- name: collect all information
  fusion_info:
    gather_subset:
      - all
    app_id: key_name
    key_file: "az-admin-private-key.pem"

- name: show all information
  debug:
    msg: "{{ fusion_info['fusion_info'] }}"
"""

RETURN = r"""
fusion_info:
  description: Returns the information collected from Fusion
  returned: always
  type: complex
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
import datetime
import time


def generate_default_dict(fusion):
    default_info = {}

    arrays_api_instance = purefusion.ArraysApi(fusion)
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    default_api_instance = purefusion.DefaultApi(fusion)
    hw_api_instance = purefusion.HardwareTypesApi(fusion)
    host_access_api_instance = purefusion.HostAccessPoliciesApi(fusion)
    id_api_instance = purefusion.IdentityManagerApi(fusion)
    nic_api_instance = purefusion.NetworkInterfacesApi(fusion)
    nig_api_instance = purefusion.NetworkInterfaceGroupsApi(fusion)
    plgrp_api_instance = purefusion.PlacementGroupsApi(fusion)
    protpol_api_instance = purefusion.ProtectionPoliciesApi(fusion)
    regions_api_instance = purefusion.RegionsApi(fusion)
    role_assign_api_instance = purefusion.RoleAssignmentsApi(fusion)
    roles_api_instance = purefusion.RolesApi(fusion)
    snapshot_api_instance = purefusion.SnapshotsApi(fusion)
    send_api_instance = purefusion.StorageEndpointsApi(fusion)
    storage_srv_api_instance = purefusion.StorageServicesApi(fusion)
    storage_class_api_instance = purefusion.StorageClassesApi(fusion)
    tenant_api_instance = purefusion.TenantsApi(fusion)
    tenantspace_api_instance = purefusion.TenantSpacesApi(fusion)
    vol_api_instance = purefusion.VolumesApi(fusion)
    volsnap_api_instance = purefusion.VolumeSnapshotsApi(fusion)

    default_info["version"] = default_api_instance.get_version().version

    storage_services = storage_srv_api_instance.list_storage_services()
    default_info["storage_services"] = len(storage_services.items)
    sclass = 0
    for storserv in range(0, len(storage_services.items)):
        sclass = sclass + len(
            storage_class_api_instance.list_storage_classes(
                storage_service_name=storage_services.items[storserv].name
            ).items
        )
    default_info["storage_classes"] = sclass

    protection_policies = protpol_api_instance.list_protection_policies()
    default_info["protection_policies"] = len(protection_policies.items)

    users = id_api_instance.list_users()
    default_info["users"] = len(users)

    host_access_policies = host_access_api_instance.list_host_access_policies()
    default_info["host_access_policies"] = len(host_access_policies.items)

    hw_types = hw_api_instance.list_hardware_types()
    default_info["hardware_types"] = len(hw_types.items)

    tenants = tenant_api_instance.list_tenants()
    default_info["tenants"] = len(tenants.items)
    tenant_spaces = 0
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenant_spaces + len(
            tenantspace_api_instance.list_tenant_spaces(
                tenant_name=tenants.items[tenant].name
            ).items
        )
    default_info["tenant_spaces"] = tenant_spaces

    #    roles = roles_api_instance.list_roles()
    #    assignments = 0
    #    default_info["roles"] = len(roles)
    #    for role in range(0, len(roles)):
    #        assignments = assignments + len(
    #            role_assign_api_instance.list_role_assignments(role_name=roles[role].name)
    #        )
    #    default_info["role_assignments"] = assignments

    regions = regions_api_instance.list_regions()
    default_info["regions"] = len(regions.items)
    azs = 0
    for count in range(0, len(regions.items)):
        azs = azs + len(
            az_api_instance.list_availability_zones(
                region_name=regions.items[count].name
            ).items
        )
    default_info["availability_zones"] = azs

    arrays = nigs = sendpoints = nics = 0
    for count in range(0, len(regions.items)):
        azones = az_api_instance.list_availability_zones(
            region_name=regions.items[count].name
        )
        for azone in range(0, len(azones.items)):
            array_details = arrays_api_instance.list_arrays(
                availability_zone_name=azones.items[azone].name,
                region_name=regions.items[count].name,
            )
            for array_detail in range(0, len(array_details.items)):
                nics = nics + len(
                    nic_api_instance.list_network_interfaces(
                        availability_zone_name=azones.items[azone].name,
                        region_name=regions.items[count].name,
                        array_name=array_details.items[array_detail].name,
                    ).items
                )
            nigs = nigs + len(
                nig_api_instance.list_network_interface_groups(
                    availability_zone_name=azones.items[azone].name,
                    region_name=regions.items[count].name,
                ).items
            )
            sendpoints = sendpoints + len(
                send_api_instance.list_storage_endpoints(
                    availability_zone_name=azones.items[azone].name,
                    region_name=regions.items[count].name,
                ).items
            )
            arrays = arrays + len(array_details.items)
    default_info["appiiances"] = arrays
    default_info["network_interfaces"] = nics
    default_info["network_interface_groups"] = nigs

    volumes = placement_grps = snapshots = 0
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenantspace_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            volumes = volumes + len(
                vol_api_instance.list_volumes(
                    tenant_name=tenants.items[tenant].name,
                    tenant_space_name=tenant_spaces[tenant_space].name,
                ).items
            )
            placement_grps = placement_grps + len(
                plgrp_api_instance.list_placement_groups(
                    tenant_name=tenants.items[tenant].name,
                    tenant_space_name=tenant_spaces[tenant_space].name,
                ).items
            )
            snapshots = snapshots + len(
                snapshot_api_instance.list_snapshots(
                    tenant_name=tenants.items[tenant].name,
                    tenant_space_name=tenant_spaces[tenant_space].name,
                ).items
            )
    default_info["volumes"] = volumes
    default_info["placements_groups"] = placement_grps
    default_info["snapshots"] = snapshots

    return default_info


def generate_nics_dict(fusion):
    nics_info = {}
    nic_api_instance = purefusion.NetworkInterfacesApi(fusion)
    arrays_api_instance = purefusion.ArraysApi(fusion)
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    regions_api_instance = purefusion.RegionsApi(fusion)
    regions = regions_api_instance.list_regions()
    for region in range(0, len(regions.items)):
        azs = az_api_instance.list_availability_zones(
            region_name=regions.items[region].name
        )
        for count in range(0, len(azs.items)):
            array_details = arrays_api_instance.list_arrays(
                availability_zone_name=azs.items[count].name,
                region_name=regions.items[region].name,
            )
            for array_detail in range(0, len(array_details.items)):
                array_name = (
                    azs.items[count].name + "/" + array_details.items[array_detail].name
                )
                nics_info[array_name] = {}
                nics = nic_api_instance.list_network_interfaces(
                    availability_zone_name=azs.items[count].name,
                    region_name=regions.items[region].name,
                    array_name=array_details.items[array_detail].name,
                )

                for nic in range(0, len(nics.items)):
                    nics_info[array_name][nics.items[nic].name] = {
                        "enabled": nics.items[nic].enabled,
                        "display_name": nics.items[nic].display_name,
                        "interface_type": nics.items[nic].interface_type,
                        "services": nics.items[nic].services,
                        "max_speed": nics.items[nic].max_speed,
                        "vlan": nics.items[nic].eth.vlan,
                        "address": nics.items[nic].eth.address,
                        "mac_address": nics.items[nic].eth.mac_address,
                        "gateway": nics.items[nic].eth.gateway,
                        "mtu": nics.items[nic].eth.mtu,
                        "network_interface_group": nics.items[
                            nic
                        ].network_interface_group.name,
                        "availability_zone": nics.items[nic].availability_zone.name,
                    }
    return nics_info


def generate_hap_dict(fusion):
    hap_info = {}
    api_instance = purefusion.HostAccessPoliciesApi(fusion)
    hosts = api_instance.list_host_access_policies()
    for host in range(0, len(hosts.items)):
        name = hosts.items[host].name
        hap_info[name] = {
            "personality": hosts.items[host].personality,
            "display_name": hosts.items[host].display_name,
            "iqn": hosts.items[host].iqn,
        }
    return hap_info


def generate_array_dict(fusion):
    array_info = {}
    array_api_instance = purefusion.ArraysApi(fusion)
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    regions_api_instance = purefusion.RegionsApi(fusion)
    regions = regions_api_instance.list_regions()
    for region in range(0, len(regions.items)):
        azs = az_api_instance.list_availability_zones(
            region_name=regions.items[region].name
        )
        for az in range(0, len(azs.items)):
            arrays = array_api_instance.list_arrays(
                availability_zone_name=azs.items[az].name,
                region_name=regions.items[region].name,
            )
            for array in range(0, len(arrays.items)):
                array_name = arrays.items[array].name
                array_space = array_api_instance.get_array_space(
                    availability_zone_name=azs.items[az].name,
                    array_name=array_name,
                    region_name=regions.items[region].name,
                )
                array_perf = array_api_instance.get_array_performance(
                    availability_zone_name=azs.items[az].name,
                    array_name=array_name,
                    region_name=regions.items[region].name,
                )
                array_info[array_name] = {
                    "region": regions.items[region].name,
                    "availability_zone": azs.items[az].name,
                    "host_name": arrays.items[array].host_name,
                    "display_name": arrays.items[array].display_name,
                    "hardware_type": arrays.items[array].hardware_type.name,
                    "appliance_id": arrays.items[array].appliance_id,
                    "apartment_id": getattr(arrays.items[array], "apartment_id", None),
                    "space": {
                        "total_physical_space": array_space.total_physical_space,
                    },
                    "performance": {
                        "read_bandwidth": array_perf.read_bandwidth,
                        "read_latency_us": array_perf.read_latency_us,
                        "reads_per_sec": array_perf.reads_per_sec,
                        "write_bandwidth": array_perf.write_bandwidth,
                        "write_latency_us": array_perf.write_latency_us,
                        "writes_per_sec": array_perf.writes_per_sec,
                    },
                }
    return array_info


def generate_pg_dict(fusion):
    pg_info = {}
    tenant_api_instance = purefusion.TenantsApi(fusion)
    tenantspace_api_instance = purefusion.TenantSpacesApi(fusion)
    pg_api_instance = purefusion.PlacementGroupsApi(fusion)
    tenants = tenant_api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenantspace_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            groups = pg_api_instance.list_placement_groups(
                tenant_name=tenants.items[tenant].name,
                tenant_space_name=tenant_spaces[tenant_space].name,
            )
            for group in range(0, len(groups.items)):
                group_name = (
                    tenants.items[tenant].name
                    + "/"
                    + tenant_spaces[tenant_space].name
                    + "/"
                    + groups.items[group].name
                )
                pg_info[group_name] = {
                    "tenant": groups.items[group].tenant.name,
                    "display_name": groups.items[group].display_name,
                    "placement_engine": groups.items[group].placement_engine,
                    "tenant_space": groups.items[group].tenant_space.name,
                    "az": groups.items[group].availability_zone.name,
                    "array": getattr(groups.items[group].array, "name", None),
                }
    return pg_info


def generate_placements_dict(fusion):
    pl_info = {}
    tenant_api_instance = purefusion.TenantsApi(fusion)
    tenantspace_api_instance = purefusion.TenantSpacesApi(fusion)
    pl_api_instance = purefusion.PlacementsApi(fusion)
    tenants = tenant_api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenantspace_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            placements = pl_api_instance.list_placements(
                tenant_name=tenants.items[tenant].name,
                tenant_space_name=tenant_spaces[tenant_space].name,
            )
            for placement in range(0, len(placements.items)):
                pl_name = (
                    tenants.items[tenant].name
                    + "/"
                    + tenant_spaces[tenant_space].name
                    + "/"
                    + placements.items[placement].name
                )
                pl_info[pl_name] = {
                    "tenant": tenants.items[tenant].name,
                    "tenant_space": tenant_spaces[tenant_space].name,
                    "display_name": placements.items[placement].display_name,
                    "placement_group": placements.items[placement].placement_group.name,
                    "storage_class": placements.items[placement].storage_class.name,
                    "array": placements.items[placement].array.name,
                    "protocols": {
                        "iscsi": {},
                        "fc": {},
                        "nvme": {},
                    },
                }
                if placements.items[placement].protocols.iscsi:
                    pl_info[pl_name]["protocols"]["iscsi"] = {
                        "iqn": placements.items[placement].protocols.iscsi.iqn,
                        "addresses": placements.items[
                            placement
                        ].protocols.iscsi.addresses,
                    }
    return pl_info


def generate_ts_dict(fusion):
    ts_info = {}
    tenant_api_instance = purefusion.TenantsApi(fusion)
    tenantspace_api_instance = purefusion.TenantSpacesApi(fusion)
    tenants = tenant_api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenantspace_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            ts_name = (
                tenants.items[tenant].name + "/" + tenant_spaces[tenant_space].name
            )
            ts_info[ts_name] = {
                "tenant": tenants.items[tenant].name,
                "display_name": tenant_spaces[tenant_space].display_name,
            }
    return ts_info


def generate_pp_dict(fusion):
    pp_info = {}
    api_instance = purefusion.ProtectionPoliciesApi(fusion)
    policies = api_instance.list_protection_policies()
    for policy in range(0, len(policies.items)):
        policy_name = policies.items[policy].name
        pp_info[policy_name] = {
            "objectives": policies.items[policy].objectives,
        }
    return pp_info


def generate_tenant_dict(fusion):
    tenant_info = {}
    api_instance = purefusion.TenantsApi(fusion)
    tenants = api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        name = tenants.items[tenant].name
        tenant_info[name] = {
            "display_name": tenants.items[tenant].display_name,
        }
    return tenant_info


def generate_zones_dict(fusion):
    zones_info = {}
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    regions_api_instance = purefusion.RegionsApi(fusion)
    regions = regions_api_instance.list_regions()
    for region in range(0, len(regions.items)):
        zones = az_api_instance.list_availability_zones(
            region_name=regions.items[region].name
        )
        for zone in range(0, len(zones.items)):
            az_name = zones.items[zone].name
            zones_info[az_name] = {
                "display_name": zones.items[zone].display_name,
                "region": zones.items[zone].region.name,
            }
    return zones_info


def generate_roles_dict(fusion):
    roles_info = {}
    api_instance = purefusion.RolesApi(fusion)
    roles = api_instance.list_roles()
    for role in range(0, len(roles)):
        name = roles[role].name
        roles_info[name] = {
            "display_name": roles[role].display_name,
            "scopes": roles[role].assignable_scopes,
        }
    return roles_info


def generate_users_dict(fusion):
    users_info = {}
    api_instance = purefusion.IdentityManagerApi(fusion)
    users = api_instance.list_users()
    for user in range(0, len(users)):
        name = users[user].name
        users_info[name] = {
            "display_name": users[user].display_name,
            "email": users[user].email,
            "id": users[user].id,
        }
    return users_info


def generate_hardware_dict(fusion):
    hardware_info = {}
    api_instance = purefusion.HardwareTypesApi(fusion)
    hw_types = api_instance.list_hardware_types()
    for hw_type in range(0, len(hw_types.items)):
        type_name = hw_types.items[hw_type].name
        hardware_info[type_name] = {
            "array_type": hw_types.items[hw_type].array_type,
            "display_name": hw_types.items[hw_type].display_name,
            "media_type": hw_types.items[hw_type].media_type,
        }
    return hardware_info


def generate_storageclass_dict(fusion):
    sc_info = {}
    ss_api_instance = purefusion.StorageServicesApi(fusion)
    sc_api_instance = purefusion.StorageClassesApi(fusion)
    services = ss_api_instance.list_storage_services()
    for service in range(0, len(services.items)):
        classes = sc_api_instance.list_storage_classes(
            storage_service_name=services.items[service].name,
        )
        for s_class in range(0, len(classes.items)):
            sc_name = classes.items[s_class].name
            sc_info[sc_name] = {
                "bandwidth_limit": getattr(
                    classes.items[s_class], "bandwidth_limit", None
                ),
                "iops_limit": getattr(classes.items[s_class], "iops_limit", None),
                "size_limit": getattr(classes.items[s_class], "size_limit", None),
                "display_name": classes.items[s_class].display_name,
                "storage_service": services.items[service].name,
            }
    return sc_info


def generate_storserv_dict(fusion):
    ss_dict = {}
    return ss_dict


def generate_se_dict(fusion):
    se_dict = {}
    return se_dict


def generate_nig_dict(fusion):
    nig_dict = {}
    return nig_dict


def generate_snap_dict(fusion):
    snap_dict = {}
    return snap_dict


def generate_volumes_dict(fusion):
    volume_info = {}

    tenant_api_instance = purefusion.TenantsApi(fusion)
    vol_api_instance = purefusion.VolumesApi(fusion)
    tenant_space_api_instance = purefusion.TenantSpacesApi(fusion)

    tenants = tenant_api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenant_space_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            volumes = vol_api_instance.list_volumes(
                tenant_name=tenants.items[tenant].name,
                tenant_space_name=tenant_spaces[tenant_space].name,
            )
            for volume in range(0, len(volumes.items)):
                vol_name = (
                    tenants.items[tenant].name
                    + "/"
                    + tenant_spaces[tenant_space].name
                    + "/"
                    + volumes.items[volume].name
                )
                volume_info[vol_name] = {
                    "tenant": tenants.items[tenant].name,
                    "tenant_space": tenant_spaces[tenant_space].name,
                    "name": volumes.items[volume].name,
                    "size": volumes.items[volume].size,
                    "display_name": volumes.items[volume].display_name,
                    "array": volumes.items[volume].array.name,
                    "placement": volumes.items[volume].placement.name,
                    "placement_group": volumes.items[volume].placement_group.name,
                    "source_volume_snapshot": getattr(
                        volumes.items[volume].source_volume_snapshot, "name", None
                    ),
                    "protection_policy": getattr(
                        volumes.items[volume].protection_policy, "name", None
                    ),
                    "storage_class": volumes.items[volume].storage_class.name,
                    "serial_number": volumes.items[volume].serial_number,
                    "target": {},
                }
                volume_info[vol_name]["target"] = {
                    "iscsi": {
                        "addresses": volumes.items[volume].target.iscsi.addresses,
                        "iqn": volumes.items[volume].target.iscsi.iqn,
                    },
                    "nvme": {
                        "addresses": None,
                        "nqn": None,
                    },
                    "fc": {
                        "addresses": None,
                        "wwns": None,
                    },
                }
    return volume_info


def main():
    argument_spec = fusion_argument_spec()
    argument_spec.update(
        dict(gather_subset=dict(default="minimum", type="list", elements="str"))
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)
    if not HAS_FUSION:
        module.fail_json(msg="fusion SDK required for this module")

    fusion = get_fusion(module)

    subset = [test.lower() for test in module.params["gather_subset"]]
    valid_subsets = (
        "all",
        "minimum",
        "roles",
        "users",
        "placements",
        "arrays",
        "hardware",
        "volumes",
        "hosts",
        "storageclass",
        "protection_policies",
        "placement_groups",
        "interfaces",
        "zones",
        "snapshots",
        "storage_services",
        "tenants",
        "tenant_spaces",
        "network_interface_groups",
    )
    subset_test = (test in valid_subsets for test in subset)
    if not all(subset_test):
        module.fail_json(
            msg="value must gather_subset must be one or more of: %s, got: %s"
            % (",".join(valid_subsets), ",".join(subset))
        )

    info = {}

    if "minimum" in subset or "all" in subset:
        info["default"] = generate_default_dict(fusion)
    if "hardware" in subset or "all" in subset:
        info["hardware"] = generate_hardware_dict(fusion)
    if "users" in subset or "all" in subset:
        info["users"] = generate_users_dict(fusion)
    if "zones" in subset or "all" in subset:
        info["zones"] = generate_zones_dict(fusion)
    #    if "roles" in subset or "all" in subset:
    #        info["roles"] = generate_roles_dict(fusion)
    if "storage_services" in subset or "all" in subset:
        info["storage_services"] = generate_storserv_dict(fusion)
    if "volumes" in subset or "all" in subset:
        info["volumes"] = generate_volumes_dict(fusion)
    if "protection_policies" in subset or "all" in subset:
        info["protection_policies"] = generate_pp_dict(fusion)
    if "placement_groups" in subset or "all" in subset:
        info["placement_groups"] = generate_pg_dict(fusion)
    if "storageclass" in subset or "all" in subset:
        info["storageclass"] = generate_storageclass_dict(fusion)
    if "interfaces" in subset or "all" in subset:
        info["interfaces"] = generate_nics_dict(fusion)
    if "hosts" in subset or "all" in subset:
        info["hosts"] = generate_hap_dict(fusion)
    if "arrays" in subset or "all" in subset:
        info["arrays"] = generate_array_dict(fusion)
    if "tenants" in subset or "all" in subset:
        info["tenants"] = generate_tenant_dict(fusion)
    if "tenant_spaces" in subset or "all" in subset:
        info["tenant_spaces"] = generate_ts_dict(fusion)
    if "storage_endpoint" in subset or "all" in subset:
        info["storage_endpoint"] = generate_se_dict(fusion)
    if "network_interface_groups" in subset or "all" in subset:
        info["network_interface_groups"] = generate_nig_dict(fusion)
    if "snapshots" in subset or "all" in subset:
        info["snapshots"] = generate_snap_dict(fusion)

    module.exit_json(changed=False, fusion_info=info)


if __name__ == "__main__":
    main()
