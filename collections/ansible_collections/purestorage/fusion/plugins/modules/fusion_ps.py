#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Simon Dodsley (simon@purestorage.com)
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
module: fusion_ps
version_added: '1.0.0'
short_description:  Manage Provider Subnets in Pure Storage Fusion
description:
- Create, delete and modify provider subnets in Pure Storage Fusion.
- Currently this only supports a single tenant subnet per tenant network
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  name:
    description:
    - The name of the provier subnet.
    type: str
    required: true
  display_name:
    description:
    - The human name of the provider subnet.
    - If not provided, defaults to `name`
    type: str
  state:
    description:
    - Define whether the provider subnet should exist or not.
    type: str
    default: present
    choices: [ absent, present ]
  availability_zone:
    aliases: [ az ]
    description:
    - The name of the availability zone for the povider subnet.
    type: str
    required: true
  gateway:
    description:
    - Address of the subnet gateway
    type: str
  mtu:
    description:
    - MTYU setting for the subnet
    default: 1500
    type: int
  prefix:
    description:
    - Network prefix in CIDR format
    type: str
extends_documentation_fragment:
- purestorage.fusion.purestorage.fusion
"""

EXAMPLES = r"""
- name: Create new tenant network foo in AZ bar
  purestorage.fusion.fusion_tn:
    name: foo
    availability_zone: bar
    mtu: 9000
    gateway: 10.21.200.1
    addresses:
      - 10.21.200.124/24
      - 10.21.200.36/24
    provider_subnets:
      - subnet-0
    state: present
    app_id: key_name
    key_file: "az-admin-private-key.pem"

- name: Delete tenant network foo in AZ bar
  purestorage.fusion.fusion_tn:
    name: foo
    availability_zone: bar
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


def get_ps(module, fusion):
    """Check Provider Subnets"""
    ps_api_instance = purefusion.ProviderSubnetsApi(fusion)
    try:
        return ps_api_instance.get_provider_subnet(
            availability_zone_name=module.params["availability_zone"],
            provider_subnet=module.params["name"],
        )
    except purefusion.rest.ApiException:
        return None


def get_az(module, fusion):
    """Availability Zone or None"""
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    try:
        return az_api_instance.get_availability_zone(
            availability_zone_name=module.params["availability_zone"],
        )
    except purefusion.rest.ApiException:
        return None


def create_ps(module, fusion):
    """Create Provider Subnet"""

    ps_api_instance = purefusion.ProviderSubnetsApi(fusion)

    changed = True
    if module.params["gateway"] and module.params["gateway"] not in IPNetwork(
        module.params["prefix"]
    ):
        module.fail_json(msg="Gateway and subnet prefix are not compatible.")

    if not module.check_mode:
        if not module.params["display_name"]:
            display_name = module.params["name"]
        else:
            display_name = module.params["display_name"]
        try:
            subnet = purefusion.ProviderSubnetPost(
                prefix=module.params["prefix"],
                gateway=module.params["gateway"],
                mtu=module.params["mtu"],
                name=module.params["name"],
            )
            ps_api_instance.create_provider_subnet(
                subnet,
                availability_zone_name=module.params["availability_zone"],
            )
        except purefusion.rest.ApiException as err:
            module.fail_json(
                msg="Provider Subnet {0} creation failed.: {1}".format(
                    module.params["name"], err
                )
            )

    module.exit_json(changed=changed)


def delete_ps(module, fusion):
    """Delete Provider Subnet"""
    changed = True
    ps_api_instance = purefusion.ProviderSubnetsApi(fusion)
    if not module.check_mode:
        try:
            ps_api_instance.delete_provider_subnet(
                availability_zone_name=module.params["availability_zone"],
                provider_subnet=module.params["name"],
            )
        except purefusion.rest.ApiException:
            module.fail_json(
                msg="Delete Provider Subnet {0} failed.".format(module.params["name"])
            )
    module.exit_json(changed=changed)


def update_ps(module, fusion, subnet):
    """Update Provider Subnet"""
    changed = False
    ps_api_instance = purefusion.ProviderSubnetsApi(fusion)
    current_subnet = {
        "display_name": subnet.display_name,  # Currently not modifiable
        "mtu": subnet.mtu,
        "prefix": subnet.prefix,
        "gateway": subnet.gateway,
        "vlan": subnet.vlan,  # Currently not modifiable
    }
    new_subnet = {
        "display_name": subnet.display_name,  # Currently not modifiable
        "mtu": subnet.mtu,
        "prefix": subnet.prefix,
        "gateway": subnet.gateway,
        "vlan": subnet.vlan,  # Currently not modifiable
    }
    if module.params["mtu"] != current_subnet["mtu"]:
        new_subnet["mtu"] = module.params["mtu"]
    if module.params["prefix"] != current_subnet["prefix"]:
        new_subnet["prefix"] = module.params["prefix"]
    if module.params["gateway"] != current_subnet["gateway"]:
        new_subnet["gateway"] = module.params["gateway"]
    if new_subnet != current_subnet:
        changed = True
    if changed and not module.check_mode:
        subnet = purefusion.ProviderSubnetPatch(
            prefix=new_subnet["prefix"],
            mtu=new_subnet["mtu"],
            gateway=new_subnet["gateway"],
        )
        try:
            ps_api_instance.update_provider_subnet(
                subnet,
                availability_zone_name=module.params["availability_zone"],
                provider_subnet=module.params["name"],
            )
        except purefusion.rest.ApiException as err:
            module.fail_json(
                msg="Provider Subnet {0} update failed.: {1}".format(
                    module.params["name"], err
                )
            )

    module.exit_json(changed=changed)


def main():
    """Main code"""
    argument_spec = fusion_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type="str", required=True),
            display_name=dict(type="str"),
            availability_zone=dict(type="str", required=True, aliases=["az"]),
            prefix=dict(type="str"),
            gateway=dict(type="str"),
            mtu=dict(type="int", default=1500),
            state=dict(type="str", default="present", choices=["absent", "present"]),
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_NETADDR:
        module.fail_json(msg="netaddr module is required")

    state = module.params["state"]
    fusion = get_fusion(module)
    if module.params["prefix"]:
        if "/" not in module.params["prefix"]:
            module.fail_json(msg="Prefix must be in a CIDR format")
        if 8 > int(module.params["prefix"].split("/")[1]) > 32:
            module.fail_json(
                msg="An invalid CIDR notation has been provided: {0}".format(
                    module.params["prefix"]
                )
            )

    if not get_az(module, fusion):
        module.fail_json(msg="Availability Zone {0} does not exist")

    subnet = get_ps(module, fusion)

    if state == "present" and not subnet:
        if not (module.params["gateway"] and module.params["prefix"]):
            module.fail_json(
                msg="When creating a new provider subnet "
                "`gateway` and `prefix` must be provided"
            )
        create_ps(module, fusion)
    elif state == "present" and subnet:
        # TODO: re-add this when SDK bug fixed
        module.exit_json(changed=False)
        # update_ps(module, fusion, subnet)
    elif state == "absent" and subnet:
        delete_ps(module, fusion)

    module.exit_json(changed=False)


if __name__ == "__main__":
    main()
