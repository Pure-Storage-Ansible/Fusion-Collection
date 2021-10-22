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
    register: fusion_info

- name: show default information
  debug:
    msg: "{{ fusion_info['fusion_info']['default'] }}"

- name: collect all information
  fusion_info:
    gather_subset:
      - all
- name: show all information
  debug:
    msg: "{{ fusion_info['fusion_info'] }}"
"""

RETURN = r"""
fusion_info:
  description: Returns the information collected from Fusion
  returned: always
  type: complex
  sample: {
        "appliances": {
            "FlashArray": {
                "CBS-AZURE": {
                    "bandwidth (read) [MB/s]": 0.0,
                    "bandwidth (write) [MB/s]": 0.0,
                    "fqdn": "",
                    "iops (read)": 0,
                    "iops (write)": 0,
                    "latency (read) [ms]": 0.0,
                    "latency (write) [ms]": 0.0,
                    "model": "CBS-V10MUR1",
                    "os_version": "6.1.4"
                },
                "pure-fa1": {
                    "bandwidth (read) [MB/s]": 2.525,
                    "bandwidth (write) [MB/s]": 0.156,
                    "fqdn": "pure-fa1.acme.com",
                    "iops (read)": 587,
                    "iops (write)": 844,
                    "latency (read) [ms]": 1.17,
                    "latency (write) [ms]": 0.55,
                    "load [%]": 35.88,
                    "model": "FA-405",
                    "os_version": "5.3.12"
                },
                "pure-fa2": {
                    "bandwidth (read) [MB/s]": 11.324,
                    "bandwidth (write) [MB/s]": 7.349,
                    "fqdn": "pure-fa2.acme.com",
                    "iops (read)": 1019,
                    "iops (write)": 2313,
                    "latency (read) [ms]": 0.06,
                    "latency (write) [ms]": 0.32,
                    "load [%]": 13.67,
                    "model": "FA-C60",
                    "os_version": "6.1.6"
                }
            },
            "FlashBlade": {
                "pure-fb1": {
                    "bandwidth (read) [MB/s]": 0.313,
                    "bandwidth (write) [MB/s]": 0.001,
                    "fqdn": "pure-fb1.acme.com",
                    "iops (read)": 209,
                    "iops (write)": 447,
                    "latency (read) [ms]": 0.6,
                    "latency (write) [ms]": 0.59,
                    "model": "FlashBlade",
                    "os_version": "3.2.3"
                }
            }
        },
        "contracts": {
            "pure-fa1": {
                "contract_end": "2024-10-12",
                "contract_start": "2019-10-13",
                "contract_state": "Active"
            },
            "pure-fa2": {
                "contract_end": "2021-02-17",
                "contract_start": "2015-01-06",
                "contract_state": "Expired"
            },
            "pure-fa3": {
                "contract_end": "2021-10-07",
                "contract_start": "2015-01-06",
                "contract_state": "Grace Period"
            }
        },
        "default": {
            "FlashArrays": 3,
            "FlashBlades": 1,
            "ObjectEngines": 0,
            "buckets": 45,
            "directories": 7,
            "filesystem_snapshots": 272,
            "filesystems": 295,
            "object_store_accounts": 25,
            "pods": 30,
            "volume_snapshots": 20501,
            "volumes": 1748
        }
    }
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.purestorage.fusion.plugins.module_utils.fusion import (
    get_fusion,
    pure1_argument_spec,
)
import datetime
import time


def generate_default_dict(fusion):
    default_info = {}
    fb_count = fa_count = os_count = 0
    appliances = list(fusion.list_arrays().items)
    for appliance in range(0, len(appliances)):
        if appliances[appliance].os in ["Purity//FA", "Purity"]:
            fa_count += 1
        elif appliances[appliance].os == "Purity//FB":
            fb_count += 1
        elif appliances[appliance].os == "Elasticity":
            os_count += 1
    default_info["FlashArrays"] = fa_count
    default_info["FlashBlades"] = fb_count
    default_info["ObjectEngines"] = os_count
    default_info["volumes"] = pure_1.get_volumes().total_item_count
    default_info["volume_snapshots"] = pure_1.get_volume_snapshots().total_item_count
    default_info["filesystems"] = pure_1.get_file_systems().total_item_count
    default_info[
        "filesystem_snapshots"
    ] = pure_1.get_file_system_snapshots().total_item_count
    default_info["buckets"] = pure_1.get_buckets().total_item_count
    default_info["directories"] = pure_1.get_directories().total_item_count
    default_info["pods"] = pure_1.get_pods().total_item_count
    default_info[
        "object_store_accounts"
    ] = pure_1.get_object_store_accounts().total_item_count
    return default_info


def generate_subscriptions_dict(pure_1):
    subscriptions_info = {}
    subscriptions = list(pure_1.get_subscriptions().items)
    if subscriptions:
        for subscription in range(0, len(subscriptions)):
            name = subscriptions[subscription].name
            start_time = time.strftime(
                "%Y-%m-%d %H:%M:%S UTC",
                time.gmtime(subscriptions[subscription].start_date / 1000),
            )
            end_time = time.strftime(
                "%Y-%m-%d %H:%M:%S UTC",
                time.gmtime(subscriptions[subscription].expiration_date / 1000),
            )
            subscriptions_info[name] = {
                "start_date": start_time,
                "expiration_date": end_time,
                "service": subscriptions[subscription].service,
                "status": subscriptions[subscription].status,
            }
    return subscriptions_info


def generate_contract_dict(pure_1):
    contract_info = {}
    grace_period = 2592000000  # 30 days in ms
    contract_start_epoch = None
    contract_end_epoch = None
    current_date = int(time.time() * 1000)
    appliances = list(pure_1.get_arrays().items)
    for appliance in range(0, len(appliances)):
        contract_state = "Expired"
        name = appliances[appliance].name
        contract_info[name] = {}
        contract_data = list(
            pure_1.get_arrays_support_contracts(
                filter="resource.name='" + name + "'"
            ).items
        )
        if contract_data:
            contract_start_epoch = getattr(contract_data[0], "start_date", None)
            contract_end_epoch = getattr(contract_data[0], "end_date", None)
            if contract_start_epoch:
                contract_start = datetime.datetime.fromtimestamp(
                    int(contract_start_epoch / 1000)
                ).strftime("%Y-%m-%d")
            if contract_end_epoch:
                contract_end = datetime.datetime.fromtimestamp(
                    int(contract_end_epoch / 1000)
                ).strftime("%Y-%m-%d")
            contract_info[name]["contract_start"] = contract_start
            contract_info[name]["contract_end"] = contract_end
            if contract_end_epoch:
                if current_date <= contract_end_epoch:
                    contract_state = "Active"
                elif contract_end_epoch + grace_period >= current_date:
                    contract_state = "Grace Period"
        contract_info[name]["contract_state"] = contract_state
    return contract_info


def generate_appliances_dict(module, pure_1):
    names_info = {"FlashArray": {}, "FlashBlade": {}, "ObjectEngine": {}}
    appliances = list(pure_1.get_arrays().items)
    for appliance in range(0, len(appliances)):
        name = appliances[appliance].name
        try:
            fqdn = appliances[appliance].fqdn
        except AttributeError:
            fqdn = ""
        if appliances[appliance].os in ["Purity//FA", "Purity"]:
            names_info["FlashArray"][name] = {
                "os_version": appliances[appliance].version,
                "model": appliances[appliance].model,
                "fqdn": fqdn,
            }
            try:
                names_info["FlashArray"][name]["bandwidth (read) [MB/s]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_read_bandwidth"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    / 104857600,
                    3,
                )
            except IndexError:
                pass
            try:
                names_info["FlashArray"][name]["bandwidth (write) [MB/s]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_write_bandwidth"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    / 104857600,
                    3,
                )
            except IndexError:
                pass
            try:
                names_info["FlashArray"][name]["latency (read) [ms]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_read_latency_us"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    / 1000,
                    2,
                )
            except IndexError:
                pass
            try:
                names_info["FlashArray"][name]["latency (write) [ms]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_write_latency_us"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    / 1000,
                    2,
                )
            except IndexError:
                pass
            try:
                names_info["FlashArray"][name]["iops (read)"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_read_iops"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                )
            except IndexError:
                pass
            try:
                names_info["FlashArray"][name]["iops (write)"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_write_iops"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                )
            except IndexError:
                pass
            try:
                names_info["FlashArray"][name]["load [%]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_total_load"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    * 100,
                    3,
                )
            except IndexError:
                pass
        elif appliances[appliance].os == "Elasticity":
            names_info["ObjectEngine"][name] = {
                "os_version": appliances[appliance].version,
                "model": appliances[appliance].model,
                "fqdn": fqdn,
            }
        elif appliances[appliance].os == "Purity//FB":
            names_info["FlashBlade"][name] = {
                "os_version": appliances[appliance].version,
                "model": appliances[appliance].model,
                "fqdn": fqdn,
            }
            try:
                names_info["FlashBlade"][name]["bandwidth (read) [MB/s]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_read_bandwidth"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    / 104857600,
                    3,
                )
            except IndexError:
                pass
            try:
                names_info["FlashBlade"][name]["bandwidth (write) [MB/s]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_write_bandwidth"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    / 104857600,
                    3,
                )
            except IndexError:
                pass
            try:
                names_info["FlashBlade"][name]["iops (read)"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_read_iops"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                )
            except IndexError:
                pass
            try:
                names_info["FlashBlade"][name]["iops (write)"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_write_iops"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                )
            except IndexError:
                pass
            try:
                names_info["FlashBlade"][name]["latency (read) [ms]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_read_latency_us"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    / 1000,
                    2,
                )
            except IndexError:
                pass
            try:
                names_info["FlashBlade"][name]["latency (write) [ms]"] = round(
                    list(
                        pure_1.get_metrics_history(
                            names=["array_write_latency_us"],
                            resource_names=[name],
                            aggregation="max",
                            resolution=180000,
                            end_time=int(time.time()) * 1000,
                            start_time=(int(time.time()) * 1000) - 18000000,
                        ).items
                    )[0].data[-1][1]
                    / 1000,
                    2,
                )
            except IndexError:
                pass
        else:
            module.warning(
                "Unknown operating system detected: {0}.".format(
                    appliances[appliance].os
                )
            )
    return names_info


def main():
    argument_spec = fusion_argument_spec()
    argument_spec.update(
        dict(gather_subset=dict(default="minimum", type="list", elements="str"))
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)
    fusion = get_fusion(module)

    subset = [test.lower() for test in module.params["gather_subset"]]
    valid_subsets = (
        "all",
        "minimum",
        "appliances",
        "subscriptions",
        "contracts",
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
    if "appliances" in subset or "all" in subset:
        info["appliances"] = generate_appliances_dict(module, fusion)
    if "subscriptions" in subset or "all" in subset:
        info["subscriptions"] = generate_subscriptions_dict(fusion)
    if "contracts" in subset or "all" in subset:
        info["contracts"] = generate_contract_dict(fusion)

    module.exit_json(changed=False, fusion_info=info)


if __name__ == "__main__":
    main()
