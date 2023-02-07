#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2023, Simon Dodsley (simon@purestorage.com), Jan Kodera (jkodera@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: fusion_se
version_added: '1.0.0'
short_description:  Manage storage endpoints in Pure Storage Fusion
description:
- Create or delete storage endpoints in Pure Storage Fusion.
notes:
- Supports C(check_mode).
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  name:
    description:
    - The name of the storage endpoint.
    type: str
    required: true
  display_name:
    description:
    - The human name of the storage endpoint.
    - If not provided, defaults to I(name).
    type: str
  state:
    description:
    - Define whether the storage endpoint should exist or not.
    type: str
    default: present
    choices: [ absent, present ]
  region:
    description:
    - The name of the region the availability zone is in
    type: str
    required: true
  availability_zone:
    aliases: [ az ]
    description:
    - The name of the availability zone for the storage endpoint.
    type: str
    required: true
  endpoint_type:
    description:
    - Type of the storage endpoint. Only iSCSI is available at the moment.
    type: str
    default: iscsi
    choices: [ iscsi ]
  network_interface_groups:
    description:
    - List of network interface groups to assign to the storage endpoints.
    type: list
    elements: str
  addresses:
    description:
    - List of IP addresses to be used in the subnet of the storage endpoint.
    - IP addresses must include a CIDR notation.
    - IPv4 and IPv6 are fully supported.
    type: list
    elements: str
  gateway:
    description:
    - Address of the subnet gateway.
    - Currently this must be provided.
    type: str
extends_documentation_fragment:
- purestorage.fusion.purestorage.fusion
"""

EXAMPLES = r"""
- name: Create new storage endpoint foo in AZ bar
  purestorage.fusion.fusion_se:
    name: foo
    availability_zone: bar
    gateway: 10.21.200.1
    region: us-west
    addresses:
      - 10.21.200.124/24
      - 10.21.200.36/24
    network_interface_groups:
      - subnet-0
    state: present
    app_id: key_name
    key_file: "az-admin-private-key.pem"

- name: Delete storage endpoint foo in AZ bar
  purestorage.fusion.fusion_se:
    name: foo
    availability_zone: bar
    region: us-west
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

try:
    from netaddr import IPNetwork

    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.purestorage.fusion.plugins.module_utils.fusion import (
    get_fusion,
    fusion_argument_spec,
)

from ansible_collections.purestorage.fusion.plugins.module_utils.operations import (
    await_operation,
)


def get_nifg(module, fusion):
    """Check all Network Interface Groups"""
    nifg_api_instance = purefusion.NetworkInterfaceGroupsApi(fusion)
    for group in range(0, len(module.params["network_interface_groups"])):
        try:
            nifg_api_instance.get_network_interface_group(
                region_name=module.params["region"],
                availability_zone_name=module.params["availability_zone"],
                provider_subnet=module.params["network_interface_groups"][group],
            )
        except purefusion.rest.ApiException:
            return False
    return True


def get_az(module, fusion):
    """Availability Zone or None"""
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    try:
        return az_api_instance.get_availability_zone(
            availability_zone_name=module.params["availability_zone"],
            region_name=module.params["region"],
        )
    except purefusion.rest.ApiException:
        return None


def get_se(module, fusion):
    """Storage Endpoint or None"""
    se_api_instance = purefusion.StorageEndpointsApi(fusion)
    try:
        return se_api_instance.get_storage_endpoint(
            region_name=module.params["region"],
            storage_endpoint_name=module.params["name"],
            availability_zone_name=module.params["availability_zone"],
        )
    except purefusion.rest.ApiException:
        return None


def create_se(module, fusion):
    """Create Storage Endpoint"""

    se_api_instance = purefusion.StorageEndpointsApi(fusion)

    changed = True

    if not module.check_mode:
        if not module.params["display_name"]:
            display_name = module.params["name"]
        else:
            display_name = module.params["display_name"]
        try:
            ifaces = []
            for address in module.params["addresses"]:
                if module.params["gateway"]:
                    iface = purefusion.StorageEndpointIscsiDiscoveryInterfacePost(
                        address=address,
                        gateway=module.params["gateway"],
                        network_interface_groups=module.params[
                            "network_interface_groups"
                        ],
                    )
                else:
                    iface = purefusion.StorageEndpointIscsiDiscoveryInterfacePost(
                        address=address,
                        network_interface_groups=module.params[
                            "network_interface_groups"
                        ],
                    )
                ifaces.append(iface)
            sendp = purefusion.StorageEndpointPost(
                endpoint_type=module.params["endpoint_type"],
                iscsi=purefusion.StorageEndpointIscsiPost(
                    discovery_interfaces=ifaces,
                ),
                name=module.params["name"],
                display_name=display_name,
            )
            op = se_api_instance.create_storage_endpoint(
                sendp,
                region_name=module.params["region"],
                availability_zone_name=module.params["availability_zone"],
            )
            await_operation(module, fusion, op.id)
        except purefusion.rest.ApiException as err:
            module.fail_json(
                msg="Storage Endpoint {0} creation failed.: {1}".format(
                    module.params["name"], err
                )
            )

    module.exit_json(changed=changed)


def delete_se(module, fusion):
    """Delete Storage Endpoint"""
    changed = True
    se_api_instance = purefusion.StorageEndpointsApi(fusion)
    if not module.check_mode:
        try:
            op = se_api_instance.delete_storage_endpoint(
                region_name=module.params["region"],
                availability_zone_name=module.params["availability_zone"],
                storage_endpoint_name=module.params["name"],
            )
            await_operation(module, fusion, op.id)
        except purefusion.rest.ApiException:
            module.fail_json(
                msg="Delete Storage Endpoint {0} failed.".format(module.params["name"])
            )
    module.exit_json(changed=changed)


def update_se(module, fusion, storage_endpoint):
    """Update Storage Endpoint"""
    changed = False
    module.exit_json(changed=changed)


def main():
    """Main code"""
    argument_spec = fusion_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type="str", required=True),
            display_name=dict(type="str"),
            region=dict(type="str", required=True),
            availability_zone=dict(type="str", required=True, aliases=["az"]),
            endpoint_type=dict(type="str", default="iscsi", choices=["iscsi"]),
            addresses=dict(type="list", elements="str"),
            gateway=dict(type="str"),
            network_interface_groups=dict(type="list", elements="str"),
            state=dict(type="str", default="present", choices=["absent", "present"]),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_NETADDR:
        module.fail_json(msg="netaddr module is required")

    state = module.params["state"]
    fusion = get_fusion(module)
    if not get_az(module, fusion):
        module.fail_json(msg="Availability Zone {0} does not exist")
    if module.params["network_interface_groups"] and not get_nifg(module, fusion):
        module.fail_json(
            msg="Not all of the network interface groups exist in the specified AZ"
        )
    for address in range(0, len(module.params["addresses"])):
        if "/" not in module.params["addresses"][address]:
            module.fail_json(msg="All addresses must include a CIDR notation")
        if 8 > int(module.params["addresses"][address].split("/")[1]) > 32:
            module.fail_json(
                msg="An invalid CIDR notation has been provided: {0}".format(
                    module.params["addresses"][address]
                )
            )

    sendp = get_se(module, fusion)

    if state == "present" and not sendp:
        if not (
            module.params["addresses"]
            and module.params["gateway"]  # Soon to be optional
            and module.params["network_interface_groups"]
        ):
            module.fail_json(
                msg="When creating a new storage endpoint, the following "
                "parameters must be supplied: `gateway`, `addresses` "
                "and `network_interface_groups`"
            )
        create_se(module, fusion)
    elif state == "present" and sendp:
        update_se(module, fusion, sendp)
    elif state == "absent" and sendp:
        delete_se(module, fusion)

    module.exit_json(changed=False)


if __name__ == "__main__":
    main()
