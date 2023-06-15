# -*- coding: utf-8 -*-

# (c) 2023, Andrej Pajtas (apajtas@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
from itertools import combinations
from unittest.mock import MagicMock, call, patch

import fusion as purefusion
import pytest
from ansible.module_utils import basic
from ansible_collections.purestorage.fusion.plugins.modules import fusion_info
from ansible_collections.purestorage.fusion.tests.functional.utils import (
    AnsibleExitJson,
    exit_json,
    fail_json,
    set_module_args,
)
from ansible_collections.purestorage.fusion.tests.helpers import (
    ApiExceptionsMockGenerator,
)
from urllib3.exceptions import HTTPError
import time

# GLOBAL MOCKS
fusion_info.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json

VALID_SUBSETS = {
    "all",
    "minimum",
    "roles",
    "users",
    "arrays",
    "hardware_types",
    "volumes",
    "host_access_policies",
    "storage_classes",
    "protection_policies",
    "placement_groups",
    "network_interfaces",
    "availability_zones",
    "storage_endpoints",
    "snapshots",
    "storage_services",
    "tenants",
    "tenant_spaces",
    "network_interface_groups",
    "api_clients",
    "regions",
}

EXPECTED_KEYS = {
    "all": {
        "default",
        "hardware_types",
        "users",
        "availability_zones",
        "roles",
        "role_assignments",
        "storage_services",
        "volumes",
        "protection_policies",
        "placement_groups",
        "storage_classes",
        "network_interfaces",
        "host_access_policies",
        "tenants",
        "tenant_spaces",
        "storage_endpoints",
        "api_clients",
        "network_interface_groups",
        "volume_snapshots",
        "snapshots",
        "arrays",
        "regions",
    },
    "minimum": {"default"},
    "arrays": {"arrays"},
    "hardware_types": {"hardware_types"},
    "users": {"users"},
    "availability_zones": {"availability_zones"},
    "roles": {"roles", "role_assignments"},
    "storage_services": {"storage_services"},
    "volumes": {"volumes"},
    "protection_policies": {"protection_policies"},
    "placement_groups": {"placement_groups"},
    "storage_classes": {"storage_classes"},
    "network_interfaces": {"network_interfaces"},
    "host_access_policies": {"host_access_policies"},
    "tenants": {"tenants"},
    "tenant_spaces": {"tenant_spaces"},
    "storage_endpoints": {"storage_endpoints"},
    "api_clients": {"api_clients"},
    "network_interface_groups": {"network_interface_groups"},
    "snapshots": {"snapshots", "volume_snapshots"},
    "regions": {"regions"},
}

RESP_VERSION = purefusion.Version(version=1)
RESP_AS = purefusion.Space(
    resource=purefusion.ResourceReference(
        id="333",
        name="res_ref_name",
        kind="kind_value",
        self_link="self_link_value",
    ),
    total_physical_space=1,
    unique_space=1,
    snapshot_space=1,
)
RESP_AP = purefusion.Performance(
    resource=purefusion.ResourceReference(
        id="222",
        name="res_ref_name",
        kind="kind_value",
        self_link="self_link_value",
    ),
    reads_per_sec=12345,
    read_latency_us=1000,
    read_bandwidth=5000000,
    writes_per_sec=12611,
    write_latency_us=2000,
    write_bandwidth=4000000,
)
RESP_LU = [
    purefusion.User(
        id="390",
        name="username1",
        self_link="self_link_value",
        display_name="User's Name 1",
        email="user1@email.com",
    ),
    purefusion.User(
        id="391",
        name="username2",
        self_link="self_link_value",
        display_name="User's Name 2",
        email="user2@email.com",
    ),
]
RESP_PP = purefusion.ProtectionPolicyList(
    count=2,
    more_items_remaining=False,
    items=[
        purefusion.ProtectionPolicy(
            id="098",
            name="pp1",
            self_link="self_link_value",
            display_name="Protection Policy 1",
            objectives=[],
        ),
        purefusion.ProtectionPolicy(
            id="099",
            name="pp2",
            self_link="self_link_value",
            display_name="Protection Policy 2",
            objectives=[],
        ),
    ],
)
RESP_HAP = purefusion.HostAccessPolicyList(
    count=2,
    more_items_remaining=False,
    items=[
        purefusion.HostAccessPolicy(
            id="900",
            name="hap1",
            self_link="self_link_value",
            display_name="Host Access Policy 1",
            iqn="iqn.2023-05.com.purestorage:420qp2c0261",
            personality="aix",
        ),
        purefusion.HostAccessPolicy(
            id="901",
            name="hap2",
            self_link="self_link_value",
            display_name="Host Access Policy 2",
            iqn="iqn.2023-05.com.purestorage:420qp2c0262",
            personality="linux",
        ),
    ],
)
RESP_HT = purefusion.HardwareTypeList(
    count=2,
    more_items_remaining=False,
    items=[
        purefusion.HardwareType(
            id="500",
            name="ht1",
            self_link="self_link_value",
            display_name="Hardware Type 1",
            array_type="FA//X",
            media_type="whatever",
        ),
        purefusion.HardwareType(
            id="501",
            name="ht2",
            self_link="self_link_value",
            display_name="Hardware Type 2",
            array_type="FA//C",
            media_type="whatever",
        ),
    ],
)
RESP_SS = purefusion.StorageServiceList(
    count=2,
    more_items_remaining=False,
    items=[
        purefusion.StorageService(
            id="502",
            name="ss1",
            self_link="self_link_value",
            display_name="Storage Service 1",
            hardware_types=[
                purefusion.HardwareTypeRef(
                    id="910",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                purefusion.HardwareTypeRef(
                    id="911",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
            ],
        ),
        purefusion.StorageService(
            id="503",
            name="ss2",
            self_link="self_link_value",
            display_name="Storage Service 3",
            hardware_types=[
                purefusion.HardwareTypeRef(
                    id="912",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                )
            ],
        ),
    ],
)
RESP_TENANTS = purefusion.TenantList(
    count=2,
    more_items_remaining=False,
    items=[
        purefusion.Tenant(
            id="504",
            name="t1",
            self_link="self_link_value",
            display_name="Tenant 1",
            tenant_spaces_link="ts_link",
        ),
        purefusion.Tenant(
            id="505",
            name="t2",
            self_link="self_link_value",
            display_name="Tenant 2",
            tenant_spaces_link="ts_link",
        ),
    ],
)
RESP_REGIONS = purefusion.RegionList(
    count=2,
    more_items_remaining=False,
    items=[
        purefusion.Region(
            id="506",
            name="region1",
            self_link="self_link_value",
            display_name="Region 1",
        ),
        purefusion.Region(
            id="507",
            name="region2",
            self_link="self_link_value",
            display_name="Region 2",
        ),
    ],
)
RESP_ROLES = [
    purefusion.Role(
        id="902",
        name="role1",
        self_link="self_link_value",
        display_name="Role 1",
        description="nice description",
        assignable_scopes=["scope1", "scope2"],
    ),
    purefusion.Role(
        id="903",
        name="role2",
        self_link="self_link_value",
        display_name="Role 2",
        description="not so nice description",
        assignable_scopes=["scope3", "scope2"],
    ),
]
RESP_SC = purefusion.StorageClassList(
    count=2,
    more_items_remaining=False,
    items=[
        purefusion.StorageClass(
            id="508",
            name="sc1",
            self_link="self_link_value",
            display_name="Storage Class 1",
            storage_service=purefusion.StorageServiceRef(
                id="509",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            size_limit=12345678,
            iops_limit=10000,
            bandwidth_limit=2000000,
        ),
        purefusion.StorageClass(
            id="510",
            name="sc2",
            self_link="self_link_value",
            display_name="Storage Class 2",
            storage_service=purefusion.StorageServiceRef(
                id="511",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            size_limit=12345679,
            iops_limit=10001,
            bandwidth_limit=2000001,
        ),
    ],
)
RESP_RA = [
    purefusion.RoleAssignment(
        id="904",
        name="ra1",
        self_link="self_link_value",
        display_name="Role Assignment 1",
        role=purefusion.RoleRef(
            id="512",
            name="res_ref_name",
            kind="kind_value",
            self_link="self_link_value",
        ),
        scope=purefusion.ResourceReference(
            id="513",
            name="res_ref_name",
            kind="kind_value",
            self_link="self_link_value",
        ),
        principal="user1",
    ),
    purefusion.RoleAssignment(
        id="905",
        name="ra2",
        self_link="self_link_value",
        display_name="Role Assignment 2",
        role=purefusion.RoleRef(
            id="513",
            name="res_ref_name",
            kind="kind_value",
            self_link="self_link_value",
        ),
        scope=purefusion.ResourceReference(
            id="514",
            name="res_ref_name",
            kind="kind_value",
            self_link="self_link_value",
        ),
        principal="user2",
    ),
]
RESP_TS = purefusion.TenantSpaceList(
    count=2,
    more_items_remaining=False,
    items=[
        purefusion.TenantSpace(
            id="515",
            name="ts1",
            self_link="self_link_value",
            display_name="Tenant Space 1",
            tenant=RESP_TENANTS.items[0].name,
            volumes_link="link_value1",
            snapshots_link="link_value2",
            placement_groups_link="link_value3",
        ),
        purefusion.TenantSpace(
            id="516",
            name="ts2",
            self_link="self_link_value",
            display_name="Tenant Space 2",
            tenant=RESP_TENANTS.items[1].name,
            volumes_link="link_value4",
            snapshots_link="link_value5",
            placement_groups_link="link_value6",
        ),
    ],
)
RESP_VOLUMES = purefusion.VolumeList(
    count=1,
    more_items_remaining=False,
    items=[
        purefusion.Volume(
            id="517",
            name="volume1",
            self_link="self_link_value",
            display_name="Volume 1",
            size=4000000,
            tenant=purefusion.TenantRef(
                id="518",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="519",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            storage_class=purefusion.StorageClassRef(
                id="520",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            protection_policy=purefusion.ProtectionPolicyRef(
                id="521",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            placement_group=purefusion.PlacementGroupRef(
                id="522",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            array=purefusion.ArrayRef(
                id="905",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            created_at=485743825,
            source_volume_snapshot=purefusion.VolumeSnapshotRef(
                id="523",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            host_access_policies=[
                purefusion.HostAccessPolicyRef(
                    id="524",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                )
            ],
            serial_number="123923482034",
            target=purefusion.Target(
                iscsi=purefusion.Iscsi(
                    iqn="iqn.2023-05.com.purestorage:420qp2c0222",
                    addresses=["125.1.2.4"],
                )
            ),
            time_remaining=1000000,
            destroyed=False,
        )
    ],
)
RESP_PG = purefusion.PlacementGroupList(
    count=1,
    more_items_remaining=False,
    items=[
        purefusion.PlacementGroup(
            id="525",
            name="pg1",
            self_link="self_link_value",
            display_name="Placement Group 1",
            tenant=purefusion.TenantRef(
                id="526",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="527",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            placement_engine=purefusion.PlacementEngine(),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="528",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            protocols=purefusion.Target(
                iscsi=purefusion.Iscsi(
                    iqn="iqn.2023-05.com.purestorage:420qp2c0211",
                    addresses=["125.1.2.5"],
                )
            ),
            storage_service=purefusion.StorageServiceRef(
                id="529",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            array=purefusion.ArrayRef(
                id="530",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
        )
    ],
)
RESP_SNAPSHOTS = purefusion.SnapshotList(
    count=1,
    more_items_remaining=False,
    items=[
        purefusion.Snapshot(
            id="531",
            name="snapshot1",
            self_link="self_link_value",
            display_name="Snapshot 1",
            tenant=purefusion.TenantRef(
                id="531",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="532",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            volume_snapshots_link="link_to_volume_snapshot",
            protection_policy=purefusion.ProtectionPolicyRef(
                id="533",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            time_remaining=23432,
            destroyed=False,
        )
    ],
)
RESP_AZ = purefusion.AvailabilityZoneList(
    count=3,
    more_items_remaining=False,
    items=[
        purefusion.AvailabilityZone(
            id="534",
            name="az1",
            self_link="self_link_value",
            display_name="Availability Zone 1",
            region=purefusion.RegionRef(
                id="535",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
        ),
        purefusion.AvailabilityZone(
            id="536",
            name="az2",
            self_link="self_link_value",
            display_name="Availability Zone 2",
            region=purefusion.RegionRef(
                id="537",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
        ),
        purefusion.AvailabilityZone(
            id="537",
            name="az3",
            self_link="self_link_value",
            display_name="Availability Zone 3",
            region=purefusion.RegionRef(
                id="538",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
        ),
    ],
)
RESP_NIG = purefusion.NetworkInterfaceGroupList(
    count=1,
    more_items_remaining=False,
    items=[
        purefusion.NetworkInterfaceGroup(
            id="538",
            name="nig1",
            self_link="self_link_value",
            display_name="Network Interface Group 1",
            region=purefusion.RegionRef(
                id="539",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="540",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            group_type="eth",
            eth=purefusion.NetworkInterfaceGroupEth(
                prefix="10.21.200.0/24", gateway="10.21.200.1", vlan=None, mtu=1600
            ),
        )
    ],
)
RESP_SE = purefusion.StorageEndpointList(
    count=1,
    more_items_remaining=False,
    items=[
        purefusion.StorageEndpoint(
            id="541",
            name="se1",
            self_link="self_link_value",
            display_name="Storage Endpoint 1",
            region=purefusion.RegionRef(
                id="542",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="543",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            endpoint_type="iscsi",
            iscsi=purefusion.StorageEndpointIscsi(
                discovery_interfaces=[
                    purefusion.StorageEndpointIscsiDiscoveryInterface(
                        address="10.21.200.5/24",
                        gateway="10.21.200.0",
                        mtu=2000,
                        network_interface_groups=[
                            purefusion.NetworkInterfaceGroupRef(
                                id="544",
                                name="res_ref_name",
                                kind="kind_value",
                                self_link="self_link_value",
                            ),
                        ],
                    ),
                    purefusion.StorageEndpointIscsiDiscoveryInterface(
                        address="10.21.200.6/24",
                        gateway="10.21.200.0",
                        mtu=2100,
                        network_interface_groups=[],
                    ),
                ]
            ),
        )
    ],
)
RESP_NI = purefusion.NetworkInterfaceList(
    count=1,
    more_items_remaining=False,
    items=[
        purefusion.NetworkInterface(
            id="545",
            name="ni1",
            self_link="self_link_value",
            display_name="Network Interface 1",
            region=purefusion.RegionRef(
                id="546",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="547",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            array=purefusion.ArrayRef(
                id="548",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            interface_type="eth",
            eth=purefusion.NetworkInterfaceEth(
                address="10.21.200.6/24",
                gateway="10.21.200.0",
                mac_address="E3-18-55-D8-8C-F4",
                mtu=1233,
                vlan=2,
            ),
            services=["a", "b"],
            enabled=True,
            network_interface_group=purefusion.NetworkInterfaceGroupRef(
                id="906",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            max_speed=3224232,
        )
    ],
)
RESP_ARRAYS = purefusion.ArrayList(
    count=1,
    more_items_remaining=False,
    items=[
        purefusion.Array(
            id="549",
            name="array1",
            self_link="self_link_value",
            display_name="Array 1",
            apartment_id="234214351",
            hardware_type=purefusion.HardwareTypeRef(
                id="550",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            region=purefusion.RegionRef(
                id="551",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            availability_zone=purefusion.AvailabilityZoneRef(
                id="552",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            appliance_id="2734298849",
            host_name="super_host",
            maintenance_mode=False,
            unavailable_mode=False,
        )
    ],
)
RESP_AC = [
    purefusion.APIClient(
        id="553",
        name="client1",
        self_link="self_link_value",
        display_name="API Client 1",
        issuer="apikey:name:thisisnotreal",
        public_key="0123456789",
        last_key_update=1684421184201,
        last_used=1684421290201,
        creator_id="1234",
    ),
    purefusion.APIClient(
        id="554",
        name="client2",
        self_link="self_link_value",
        display_name="API Client 2",
        issuer="apikey:name:thisissuperreal",
        public_key="0987654321",
        last_key_update=1684421184201,
        last_used=1684421290201,
        creator_id="4321",
    ),
]
RESP_VS = purefusion.VolumeSnapshotList(
    count=1,
    more_items_remaining=False,
    items=[
        purefusion.VolumeSnapshot(
            id="555",
            name="vs1",
            self_link="self_link_value",
            display_name="Volume Snapshot 1",
            serial_number="235235235345",
            volume_serial_number="544236456346345",
            created_at=1684421184201,
            consistency_id="666666",
            destroyed=False,
            time_remaining=1684421290201,
            size=19264036,
            tenant=purefusion.TenantRef(
                id="556",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            tenant_space=purefusion.TenantSpaceRef(
                id="557",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            snapshot=purefusion.VolumeSnapshotRef(
                id="558",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            volume=purefusion.VolumeRef(
                id="559",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            protection_policy=purefusion.ProtectionPolicyRef(
                id="560",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
            placement_group=purefusion.PlacementGroupRef(
                id="561",
                name="res_ref_name",
                kind="kind_value",
                self_link="self_link_value",
            ),
        )
    ],
)


@patch.dict(os.environ, {"TZ": "UTC"})
@patch.dict(os.environ, {"LC_TIME": "en_US.utf8"})
@patch("fusion.DefaultApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.ProtectionPoliciesApi")
@patch("fusion.HostAccessPoliciesApi")
@patch("fusion.HardwareTypesApi")
@patch("fusion.StorageServicesApi")
@patch("fusion.TenantsApi")
@patch("fusion.RegionsApi")
@patch("fusion.RolesApi")
@patch("fusion.StorageClassesApi")
@patch("fusion.RoleAssignmentsApi")
@patch("fusion.TenantSpacesApi")
@patch("fusion.VolumesApi")
@patch("fusion.VolumeSnapshotsApi")
@patch("fusion.PlacementGroupsApi")
@patch("fusion.SnapshotsApi")
@patch("fusion.AvailabilityZonesApi")
@patch("fusion.ArraysApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@patch("fusion.StorageEndpointsApi")
@patch("fusion.NetworkInterfacesApi")
@pytest.mark.parametrize(
    # all single options + all subsets of two options
    "gather_subset",
    [
        *combinations(
            VALID_SUBSETS,
            2,
        ),
        *[[option] for option in VALID_SUBSETS],
    ],
)
def test_info_gather_subset(
    # API mocks
    m_ni_api,
    m_se_api,
    m_nig_api,
    m_array_api,
    m_az_api,
    m_snapshot_api,
    m_pg_api,
    m_vs_api,
    m_volume_api,
    m_ts_api,
    m_ra_api,
    m_sc_api,
    m_role_api,
    m_region_api,
    m_tenant_api,
    m_ss_api,
    m_hw_api,
    m_hap_api,
    m_pp_api,
    m_im_api,
    m_default_api,
    # test parameters
    gather_subset,
):
    """
    Test that fusion_info module accepts single 'gather_subset' options and all subsets of two 'gather_subset' options.
    """
    # NOTE: here we use the same MagicMock object for all APIs to make the test simpler, this has no harm to the logic of the test
    api_obj = MagicMock()
    api_obj.get_version = MagicMock(return_value=RESP_VERSION)
    api_obj.get_array_space = MagicMock(return_value=RESP_AS)
    api_obj.get_array_performance = MagicMock(return_value=RESP_AP)
    api_obj.list_users = MagicMock(return_value=RESP_LU)
    api_obj.list_protection_policies = MagicMock(return_value=RESP_PP)
    api_obj.list_host_access_policies = MagicMock(return_value=RESP_HAP)
    api_obj.list_hardware_types = MagicMock(return_value=RESP_HT)
    api_obj.list_storage_services = MagicMock(return_value=RESP_SS)
    api_obj.list_tenants = MagicMock(return_value=RESP_TENANTS)
    api_obj.list_regions = MagicMock(return_value=RESP_REGIONS)
    api_obj.list_roles = MagicMock(return_value=RESP_ROLES)
    api_obj.list_storage_classes = MagicMock(return_value=RESP_SC)
    api_obj.list_role_assignments = MagicMock(return_value=RESP_RA)
    api_obj.list_tenant_spaces = MagicMock(return_value=RESP_TS)
    api_obj.list_volumes = MagicMock(return_value=RESP_VOLUMES)
    api_obj.list_placement_groups = MagicMock(return_value=RESP_PG)
    api_obj.list_snapshots = MagicMock(return_value=RESP_SNAPSHOTS)
    api_obj.list_availability_zones = MagicMock(return_value=RESP_AZ)
    api_obj.list_network_interface_groups = MagicMock(return_value=RESP_NIG)
    api_obj.list_storage_endpoints = MagicMock(return_value=RESP_SE)
    api_obj.list_network_interfaces = MagicMock(return_value=RESP_NI)
    api_obj.list_arrays = MagicMock(return_value=RESP_ARRAYS)
    api_obj.list_api_clients = MagicMock(return_value=RESP_AC)
    api_obj.list_volume_snapshots = MagicMock(return_value=RESP_VS)
    m_ni_api.return_value = api_obj
    m_se_api.return_value = api_obj
    m_nig_api.return_value = api_obj
    m_array_api.return_value = api_obj
    m_az_api.return_value = api_obj
    m_snapshot_api.return_value = api_obj
    m_pg_api.return_value = api_obj
    m_vs_api.return_value = api_obj
    m_volume_api.return_value = api_obj
    m_ts_api.return_value = api_obj
    m_ra_api.return_value = api_obj
    m_sc_api.return_value = api_obj
    m_role_api.return_value = api_obj
    m_region_api.return_value = api_obj
    m_tenant_api.return_value = api_obj
    m_ss_api.return_value = api_obj
    m_hw_api.return_value = api_obj
    m_hap_api.return_value = api_obj
    m_pp_api.return_value = api_obj
    m_im_api.return_value = api_obj
    m_default_api.return_value = api_obj

    time.tzset()

    set_module_args(
        {
            "gather_subset": gather_subset,
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        }
    )

    with pytest.raises(AnsibleExitJson) as exc:
        fusion_info.main()

    assert exc.value.changed is False

    expected_keys = {}
    for option in gather_subset:
        expected_keys = {*expected_keys, *EXPECTED_KEYS[option]}

    assert exc.value.fusion_info.keys() == expected_keys

    if "hardware_types" in gather_subset or "all" in gather_subset:
        api_obj.list_hardware_types.assert_called_with()
        assert "hardware_types" in exc.value.fusion_info
        assert exc.value.fusion_info["hardware_types"] == {
            hw_type.name: {
                "array_type": hw_type.array_type,
                "display_name": hw_type.display_name,
                "media_type": hw_type.media_type,
            }
            for hw_type in RESP_HT.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_hardware_types.assert_called_with()
        assert "default" in exc.value.fusion_info
        assert "hardware_types" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["hardware_types"] == len(RESP_HT.items)
    else:
        api_obj.list_hardware_types.assert_not_called()

    if "users" in gather_subset or "all" in gather_subset:
        api_obj.list_users.assert_called_with()
        assert "users" in exc.value.fusion_info
        assert exc.value.fusion_info["users"] == {
            user.name: {
                "display_name": user.display_name,
                "email": user.email,
                "id": user.id,
            }
            for user in RESP_LU
        }
    elif "minimum" in gather_subset:
        api_obj.list_users.assert_called_with()
        assert "default" in exc.value.fusion_info
        assert "users" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["users"] == len(RESP_LU)
    else:
        api_obj.list_users.assert_not_called()

    if "availability_zones" in gather_subset or "all" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        assert "availability_zones" in exc.value.fusion_info
        assert exc.value.fusion_info["availability_zones"] == {
            zone.name: {
                "display_name": zone.display_name,
                "region": zone.region.name,
            }
            for zone in RESP_AZ.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "availability_zones" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["availability_zones"] == len(
            RESP_REGIONS.items
        ) * len(RESP_AZ.items)

    if "roles" in gather_subset or "all" in gather_subset:
        api_obj.list_roles.assert_called_with()
        api_obj.list_role_assignments.assert_has_calls(
            [call(role_name=role.name) for role in RESP_ROLES],
            any_order=True,
        )
        assert "roles" in exc.value.fusion_info
        assert "role_assignments" in exc.value.fusion_info
        assert exc.value.fusion_info["roles"] == {
            role.name: {
                "display_name": role.display_name,
                "scopes": role.assignable_scopes,
            }
            for role in RESP_ROLES
        }
        assert exc.value.fusion_info["role_assignments"] == {
            ra.name: {
                "display_name": ra.display_name,
                "role": ra.role.name,
                "scope": ra.scope.name,
            }
            for ra in RESP_RA
        }
    elif "minimum" in gather_subset:
        api_obj.list_roles.assert_called_with()
        api_obj.list_role_assignments.assert_has_calls(
            [call(role_name=role.name) for role in RESP_ROLES],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "roles" in exc.value.fusion_info["default"]
        assert "role_assignments" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["roles"] == len(RESP_ROLES)
        assert exc.value.fusion_info["default"]["role_assignments"] == len(
            RESP_ROLES
        ) * len(RESP_RA)
    else:
        api_obj.list_roles.assert_not_called()
        api_obj.list_role_assignments.assert_not_called()

    if "storage_services" in gather_subset or "all" in gather_subset:
        api_obj.list_storage_services.assert_called_with()
        assert "storage_services" in exc.value.fusion_info
        assert exc.value.fusion_info["storage_services"] == {
            service.name: {
                "display_name": service.display_name,
                "hardware_types": [hwtype.name for hwtype in service.hardware_types],
            }
            for service in RESP_SS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_storage_services.assert_called_with()
        assert "default" in exc.value.fusion_info
        assert "storage_services" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["storage_services"] == len(
            RESP_SS.items
        )

    if "volumes" in gather_subset or "all" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        api_obj.list_tenant_spaces.assert_has_calls(
            [call(tenant_name=tenant.name) for tenant in RESP_TENANTS.items],
            any_order=True,
        )
        api_obj.list_volumes.assert_has_calls(
            [
                call(
                    tenant_name=tenant.name,
                    tenant_space_name=ts.name,
                )
                for ts in RESP_TS.items
                for tenant in RESP_TENANTS.items
            ],
            any_order=True,
        )
        assert "volumes" in exc.value.fusion_info
        assert exc.value.fusion_info["volumes"] == {
            tenant.name
            + "/"
            + tenant_space.name
            + "/"
            + volume.name: {
                "tenant": tenant.name,
                "tenant_space": tenant_space.name,
                "name": volume.name,
                "size": volume.size,
                "display_name": volume.display_name,
                "placement_group": volume.placement_group.name,
                "source_volume_snapshot": getattr(
                    volume.source_volume_snapshot, "name", None
                ),
                "protection_policy": getattr(volume.protection_policy, "name", None),
                "storage_class": volume.storage_class.name,
                "serial_number": volume.serial_number,
                "target": {
                    "iscsi": {
                        "addresses": volume.target.iscsi.addresses,
                        "iqn": volume.target.iscsi.iqn,
                    },
                    "nvme": {
                        "addresses": None,
                        "nqn": None,
                    },
                    "fc": {
                        "addresses": None,
                        "wwns": None,
                    },
                },
                "array": volume.array.name,
            }
            for volume in RESP_VOLUMES.items
            for tenant_space in RESP_TS.items
            for tenant in RESP_TENANTS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        api_obj.list_tenant_spaces.assert_has_calls(
            [call(tenant_name=tenant.name) for tenant in RESP_TENANTS.items],
            any_order=True,
        )
        api_obj.list_volumes.assert_has_calls(
            [
                call(
                    tenant_name=tenant.name,
                    tenant_space_name=ts.name,
                )
                for ts in RESP_TS.items
                for tenant in RESP_TENANTS.items
            ],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "volumes" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["volumes"] == len(
            RESP_TENANTS.items
        ) * len(RESP_TS.items) * len(RESP_VOLUMES.items)
    else:
        api_obj.list_volumes.assert_not_called()

    if "protection_policies" in gather_subset or "all" in gather_subset:
        api_obj.list_protection_policies.assert_called_with()
        assert "protection_policies" in exc.value.fusion_info
        assert exc.value.fusion_info["protection_policies"] == {
            policy.name: {
                "objectives": policy.objectives,
            }
            for policy in RESP_PP.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_protection_policies.assert_called_with()
        assert "default" in exc.value.fusion_info
        assert "protection_policies" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["protection_policies"] == len(
            RESP_PP.items
        )
    else:
        api_obj.list_protection_policies.assert_not_called()

    if "storage_classes" in gather_subset or "all" in gather_subset:
        api_obj.list_storage_services.assert_called_with()
        api_obj.list_storage_classes.assert_has_calls(
            [call(storage_service_name=service.name) for service in RESP_SS.items],
            any_order=True,
        )
        assert "storage_classes" in exc.value.fusion_info
        assert exc.value.fusion_info["storage_classes"] == {
            s_class.name: {
                "bandwidth_limit": getattr(s_class, "bandwidth_limit", None),
                "iops_limit": getattr(s_class, "iops_limit", None),
                "size_limit": getattr(s_class, "size_limit", None),
                "display_name": s_class.display_name,
                "storage_service": service.name,
            }
            for s_class in RESP_SC.items
            for service in RESP_SS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_storage_services.assert_called_with()
        api_obj.list_storage_classes.assert_has_calls(
            [call(storage_service_name=service.name) for service in RESP_SS.items],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "storage_classes" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["storage_classes"] == len(
            RESP_SC.items
        ) * len(RESP_SS.items)
    else:
        api_obj.list_storage_classes.assert_not_called()

    if "network_interfaces" in gather_subset or "all" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        api_obj.list_arrays.assert_has_calls(
            [
                call(
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
            ],
            any_order=True,
        )
        api_obj.list_network_interfaces.assert_has_calls(
            [
                call(
                    array_name=array.name,
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
                for array in RESP_ARRAYS.items
            ],
            any_order=True,
        )
        assert "network_interfaces" in exc.value.fusion_info
        assert exc.value.fusion_info["network_interfaces"] == {
            az.name
            + "/"
            + array.name: {
                nic.name: {
                    "enabled": nic.enabled,
                    "display_name": nic.display_name,
                    "interface_type": nic.interface_type,
                    "services": nic.services,
                    "max_speed": nic.max_speed,
                    "vlan": nic.eth.vlan,
                    "address": nic.eth.address,
                    "mac_address": nic.eth.mac_address,
                    "gateway": nic.eth.gateway,
                    "mtu": nic.eth.mtu,
                    "network_interface_group": nic.network_interface_group.name,
                    "availability_zone": nic.availability_zone.name,
                }
                for nic in RESP_NI.items
            }
            for region in RESP_REGIONS.items
            for az in RESP_AZ.items
            for array in RESP_ARRAYS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        api_obj.list_arrays.assert_has_calls(
            [
                call(
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
            ],
            any_order=True,
        )
        api_obj.list_network_interfaces.assert_has_calls(
            [
                call(
                    array_name=array.name,
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
                for array in RESP_ARRAYS.items
            ],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "network_interfaces" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["network_interfaces"] == len(
            RESP_REGIONS.items
        ) * len(RESP_AZ.items) * len(RESP_ARRAYS.items) * len(RESP_NI.items)
    else:
        api_obj.list_network_interfaces.assert_not_called()

    if "host_access_policies" in gather_subset or "all" in gather_subset:
        api_obj.list_host_access_policies.assert_called_with()
        assert "host_access_policies" in exc.value.fusion_info
        assert exc.value.fusion_info["host_access_policies"] == {
            host.name: {
                "personality": host.personality,
                "display_name": host.display_name,
                "iqn": host.iqn,
            }
            for host in RESP_HAP.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_host_access_policies.assert_called_with()
        assert "default" in exc.value.fusion_info
        assert "host_access_policies" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["host_access_policies"] == len(
            RESP_HAP.items
        )
    else:
        api_obj.list_host_access_policies.assert_not_called()

    if "arrays" in gather_subset or "all" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        api_obj.list_arrays.assert_has_calls(
            [
                call(
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
            ],
            any_order=True,
        )
        api_obj.get_array_space.assert_has_calls(
            [
                call(
                    array_name=array.name,
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
                for array in RESP_ARRAYS.items
            ],
            any_order=True,
        )
        api_obj.get_array_performance.assert_has_calls(
            [
                call(
                    array_name=array.name,
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
                for array in RESP_ARRAYS.items
            ],
            any_order=True,
        )
        assert "arrays" in exc.value.fusion_info
        assert exc.value.fusion_info["arrays"] == {
            array.name: {
                "region": region.name,
                "availability_zone": az.name,
                "host_name": array.host_name,
                "maintenance_mode": array.maintenance_mode,
                "unavailable_mode": array.unavailable_mode,
                "display_name": array.display_name,
                "hardware_type": array.hardware_type.name,
                "appliance_id": array.appliance_id,
                "apartment_id": getattr(array, "apartment_id", None),
                "space": {
                    "total_physical_space": RESP_AS.total_physical_space,
                },
                "performance": {
                    "read_bandwidth": RESP_AP.read_bandwidth,
                    "read_latency_us": RESP_AP.read_latency_us,
                    "reads_per_sec": RESP_AP.reads_per_sec,
                    "write_bandwidth": RESP_AP.write_bandwidth,
                    "write_latency_us": RESP_AP.write_latency_us,
                    "writes_per_sec": RESP_AP.writes_per_sec,
                },
            }
            for region in RESP_REGIONS.items
            for az in RESP_AZ.items
            for array in RESP_ARRAYS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        api_obj.list_arrays.assert_has_calls(
            [
                call(
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
            ],
            any_order=True,
        )
        api_obj.get_array_space.assert_not_called()
        api_obj.get_array_performance.assert_not_called()
        assert "default" in exc.value.fusion_info
        assert "arrays" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["arrays"] == len(
            RESP_REGIONS.items
        ) * len(RESP_AZ.items) * len(RESP_ARRAYS.items)
    else:
        api_obj.get_array_space.assert_not_called()
        api_obj.get_array_performance.assert_not_called()

    if "tenants" in gather_subset or "all" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        assert "tenants" in exc.value.fusion_info
        assert exc.value.fusion_info["tenants"] == {
            tenant.name: {
                "display_name": tenant.display_name,
            }
            for tenant in RESP_TENANTS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        assert "default" in exc.value.fusion_info
        assert "tenants" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["tenants"] == len(RESP_TENANTS.items)

    if "tenant_spaces" in gather_subset or "all" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        api_obj.list_tenant_spaces.assert_has_calls(
            [call(tenant_name=tenant.name) for tenant in RESP_TENANTS.items],
            any_order=True,
        )
        assert "tenant_spaces" in exc.value.fusion_info
        assert exc.value.fusion_info["tenant_spaces"] == {
            tenant.name
            + "/"
            + ts.name: {
                "tenant": tenant.name,
                "display_name": ts.display_name,
            }
            for tenant in RESP_TENANTS.items
            for ts in RESP_TS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        api_obj.list_tenant_spaces.assert_has_calls(
            [call(tenant_name=tenant.name) for tenant in RESP_TENANTS.items],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "tenant_spaces" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["tenant_spaces"] == len(
            RESP_TENANTS.items
        ) * len(RESP_TS.items)

    if "storage_endpoints" in gather_subset or "all" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        api_obj.list_storage_endpoints.assert_has_calls(
            [
                call(
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
            ],
            any_order=True,
        )
        assert "storage_endpoints" in exc.value.fusion_info
        assert exc.value.fusion_info["storage_endpoints"] == {
            region.name
            + "/"
            + az.name
            + "/"
            + endpoint.name: {
                "display_name": endpoint.display_name,
                "endpoint_type": endpoint.endpoint_type,
                "iscsi_interfaces": [
                    {
                        "address": iface.address,
                        "gateway": iface.gateway,
                        "mtu": iface.mtu,
                        "network_interface_groups": [
                            nig.name for nig in iface.network_interface_groups
                        ],
                    }
                    for iface in endpoint.iscsi.discovery_interfaces
                ],
            }
            for region in RESP_REGIONS.items
            for az in RESP_AZ.items
            for endpoint in RESP_SE.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        api_obj.list_storage_endpoints.assert_has_calls(
            [
                call(
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
            ],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "storage_endpoints" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["storage_endpoints"] == len(
            RESP_REGIONS.items
        ) * len(RESP_AZ.items) * len(RESP_SE.items)
    else:
        api_obj.list_storage_endpoints.assert_not_called()

    if "api_clients" in gather_subset or "all" in gather_subset:
        api_obj.list_api_clients.assert_called_with()
        assert "api_clients" in exc.value.fusion_info
        assert exc.value.fusion_info["api_clients"] == {
            client.name: {
                "display_name": client.display_name,
                "issuer": client.issuer,
                "public_key": client.public_key,
                "creator_id": client.creator_id,
                "last_key_update": "Thu, 18 May 2023 14:46:24 UTC",
                "last_used": "Thu, 18 May 2023 14:48:10 UTC",
            }
            for client in RESP_AC
        }
    elif "minimum" in gather_subset:
        # api_clients is not in default dict
        api_obj.list_api_clients.assert_not_called()
        assert "default" in exc.value.fusion_info
        assert "api_clients" not in exc.value.fusion_info["default"]
    else:
        api_obj.list_api_clients.assert_not_called()

    if "snapshots" in gather_subset or "all" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        api_obj.list_tenant_spaces.assert_has_calls(
            [call(tenant_name=tenant.name) for tenant in RESP_TENANTS.items],
            any_order=True,
        )
        api_obj.list_snapshots.assert_has_calls(
            [
                call(
                    tenant_name=tenant.name,
                    tenant_space_name=ts.name,
                )
                for ts in RESP_TS.items
                for tenant in RESP_TENANTS.items
            ],
            any_order=True,
        )
        api_obj.list_volume_snapshots.assert_has_calls(
            [
                call(
                    tenant_name=tenant.name,
                    tenant_space_name=ts.name,
                    snapshot_name=snap.name,
                )
                for snap in RESP_SNAPSHOTS.items
                for ts in RESP_TS.items
                for tenant in RESP_TENANTS.items
            ],
            any_order=True,
        )
        assert "snapshots" in exc.value.fusion_info
        assert "volume_snapshots" in exc.value.fusion_info
        assert exc.value.fusion_info["snapshots"] == {
            tenant.name
            + "/"
            + ts.name
            + "/"
            + snap.name: {
                "display_name": snap.display_name,
                "protection_policy": snap.protection_policy,
                "time_remaining": "0 hours, 0 mins, 23 secs",
                "volume_snapshots_link": snap.volume_snapshots_link,
            }
            for snap in RESP_SNAPSHOTS.items
            for ts in RESP_TS.items
            for tenant in RESP_TENANTS.items
        }

        assert exc.value.fusion_info["volume_snapshots"] == {
            tenant.name
            + "/"
            + ts.name
            + "/"
            + snap.name
            + "/"
            + vsnap.name: {
                "size": vsnap.size,
                "display_name": vsnap.display_name,
                "protection_policy": vsnap.protection_policy,
                "serial_number": vsnap.serial_number,
                "created_at": "Thu, 18 May 2023 14:46:24 UTC",
                "time_remaining": "14 hours, 48 mins, 10 secs",
                "placement_group": vsnap.placement_group.name,
            }
            for vsnap in RESP_VS.items
            for snap in RESP_SNAPSHOTS.items
            for ts in RESP_TS.items
            for tenant in RESP_TENANTS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        api_obj.list_tenant_spaces.assert_has_calls(
            [call(tenant_name=tenant.name) for tenant in RESP_TENANTS.items],
            any_order=True,
        )
        api_obj.list_snapshots.assert_has_calls(
            [
                call(
                    tenant_name=tenant.name,
                    tenant_space_name=ts.name,
                )
                for ts in RESP_TS.items
                for tenant in RESP_TENANTS.items
            ],
            any_order=True,
        )
        api_obj.list_volume_snapshots.assert_not_called()
        assert "default" in exc.value.fusion_info
        assert "snapshots" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["snapshots"] == len(
            RESP_TENANTS.items
        ) * len(RESP_TS.items) * len(RESP_SNAPSHOTS.items)
    else:
        api_obj.list_snapshots.assert_not_called()
        api_obj.list_volume_snapshots.assert_not_called()

    if "network_interface_groups" in gather_subset or "all" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        api_obj.list_network_interface_groups.assert_has_calls(
            [
                call(
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
            ],
            any_order=True,
        )
        assert "network_interface_groups" in exc.value.fusion_info
        assert exc.value.fusion_info["network_interface_groups"] == {
            region.name
            + "/"
            + az.name
            + "/"
            + nig.name: {
                "display_name": nig.display_name,
                "gateway": nig.eth.gateway,
                "prefix": nig.eth.prefix,
                "mtu": nig.eth.mtu,
            }
            for nig in RESP_NIG.items
            for region in RESP_REGIONS.items
            for az in RESP_AZ.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_regions.assert_called_with()
        api_obj.list_availability_zones.assert_has_calls(
            [call(region_name=region.name) for region in RESP_REGIONS.items],
            any_order=True,
        )
        api_obj.list_network_interface_groups.assert_has_calls(
            [
                call(
                    availability_zone_name=az.name,
                    region_name=region.name,
                )
                for region in RESP_REGIONS.items
                for az in RESP_AZ.items
            ],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "network_interface_groups" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["network_interface_groups"] == len(
            RESP_NIG.items
        ) * len(RESP_REGIONS.items) * len(RESP_AZ.items)
    else:
        api_obj.list_network_interface_groups.assert_not_called()

    if "placement_groups" in gather_subset or "all" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        api_obj.list_tenant_spaces.assert_has_calls(
            [call(tenant_name=tenant.name) for tenant in RESP_TENANTS.items],
            any_order=True,
        )
        api_obj.list_volumes.list_placement_groups(
            [
                call(
                    tenant_name=tenant.name,
                    tenant_space_name=ts.name,
                )
                for ts in RESP_TS.items
                for tenant in RESP_TENANTS.items
            ],
            any_order=True,
        )
        assert "placement_groups" in exc.value.fusion_info
        assert exc.value.fusion_info["placement_groups"] == {
            tenant.name
            + "/"
            + ts.name
            + "/"
            + group.name: {
                "tenant": group.tenant.name,
                "display_name": group.display_name,
                "placement_engine": group.placement_engine,
                "tenant_space": group.tenant_space.name,
                "az": group.availability_zone.name,
                "array": getattr(group.array, "name", None),
            }
            for group in RESP_PG.items
            for ts in RESP_TS.items
            for tenant in RESP_TENANTS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_tenants.assert_called_with()
        api_obj.list_tenant_spaces.assert_has_calls(
            [call(tenant_name=tenant.name) for tenant in RESP_TENANTS.items],
            any_order=True,
        )
        api_obj.list_volumes.list_placement_groups(
            [
                call(
                    tenant_name=tenant.name,
                    tenant_space_name=ts.name,
                )
                for ts in RESP_TS.items
                for tenant in RESP_TENANTS.items
            ],
            any_order=True,
        )
        assert "default" in exc.value.fusion_info
        assert "placement_groups" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["placement_groups"] == len(
            RESP_PG.items
        ) * len(RESP_TENANTS.items) * len(RESP_TS.items)
    else:
        api_obj.list_placement_groups.assert_not_called()

    if "regions" in gather_subset or "all" in gather_subset:
        api_obj.list_regions.assert_called_with()
        assert "regions" in exc.value.fusion_info
        assert exc.value.fusion_info["regions"] == {
            region.name: {
                "display_name": region.display_name,
            }
            for region in RESP_REGIONS.items
        }
    elif "minimum" in gather_subset:
        api_obj.list_regions.assert_called_with()
        assert "default" in exc.value.fusion_info
        assert "regions" in exc.value.fusion_info["default"]
        assert exc.value.fusion_info["default"]["regions"] == len(RESP_REGIONS.items)


@patch("fusion.DefaultApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.ProtectionPoliciesApi")
@patch("fusion.HostAccessPoliciesApi")
@patch("fusion.HardwareTypesApi")
@patch("fusion.StorageServicesApi")
@patch("fusion.TenantsApi")
@patch("fusion.RegionsApi")
@patch("fusion.RolesApi")
@patch("fusion.StorageClassesApi")
@patch("fusion.RoleAssignmentsApi")
@patch("fusion.TenantSpacesApi")
@patch("fusion.VolumesApi")
@patch("fusion.VolumeSnapshotsApi")
@patch("fusion.PlacementGroupsApi")
@patch("fusion.SnapshotsApi")
@patch("fusion.AvailabilityZonesApi")
@patch("fusion.ArraysApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@patch("fusion.StorageEndpointsApi")
@patch("fusion.NetworkInterfacesApi")
@pytest.mark.parametrize("subset", VALID_SUBSETS)
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
        (ApiExceptionsMockGenerator.create_permission_denied(), AnsibleExitJson),
    ],
)
def test_info_exception(
    # API mocks
    m_ni_api,
    m_se_api,
    m_nig_api,
    m_array_api,
    m_az_api,
    m_snapshot_api,
    m_pg_api,
    m_vs_api,
    m_volume_api,
    m_ts_api,
    m_ra_api,
    m_sc_api,
    m_role_api,
    m_region_api,
    m_tenant_api,
    m_ss_api,
    m_hw_api,
    m_hap_api,
    m_pp_api,
    m_im_api,
    m_default_api,
    # test parameter
    subset,
    # exceptions
    exec_original,
    exec_catch,
):
    """
    Test that fusion_info propagates exceptions correctly.
    """
    # NOTE: here we use the same MagicMock object for all APIs to make the test simpler, this has no harm to the logic of the test
    api_obj = MagicMock()
    api_obj.get_version = MagicMock(
        return_value=RESP_VERSION, side_effect=exec_original
    )
    api_obj.get_array_space = MagicMock(return_value=RESP_AS, side_effect=exec_original)
    api_obj.get_array_performance = MagicMock(
        return_value=RESP_AP, side_effect=exec_original
    )
    api_obj.list_users = MagicMock(return_value=RESP_LU, side_effect=exec_original)
    api_obj.list_protection_policies = MagicMock(
        return_value=RESP_PP, side_effect=exec_original
    )
    api_obj.list_host_access_policies = MagicMock(
        return_value=RESP_HAP, side_effect=exec_original
    )
    api_obj.list_hardware_types = MagicMock(
        return_value=RESP_HT, side_effect=exec_original
    )
    api_obj.list_storage_services = MagicMock(
        return_value=RESP_SS, side_effect=exec_original
    )
    api_obj.list_tenants = MagicMock(
        return_value=RESP_TENANTS, side_effect=exec_original
    )
    api_obj.list_regions = MagicMock(
        return_value=RESP_REGIONS, side_effect=exec_original
    )
    api_obj.list_roles = MagicMock(return_value=RESP_ROLES, side_effect=exec_original)
    api_obj.list_storage_classes = MagicMock(
        return_value=RESP_SC, side_effect=exec_original
    )
    api_obj.list_role_assignments = MagicMock(
        return_value=RESP_RA, side_effect=exec_original
    )
    api_obj.list_tenant_spaces = MagicMock(
        return_value=RESP_TS, side_effect=exec_original
    )
    api_obj.list_volumes = MagicMock(
        return_value=RESP_VOLUMES, side_effect=exec_original
    )
    api_obj.list_placement_groups = MagicMock(
        return_value=RESP_PG, side_effect=exec_original
    )
    api_obj.list_snapshots = MagicMock(
        return_value=RESP_SNAPSHOTS, side_effect=exec_original
    )
    api_obj.list_availability_zones = MagicMock(
        return_value=RESP_AZ, side_effect=exec_original
    )
    api_obj.list_network_interface_groups = MagicMock(
        return_value=RESP_NIG, side_effect=exec_original
    )
    api_obj.list_storage_endpoints = MagicMock(
        return_value=RESP_SE, side_effect=exec_original
    )
    api_obj.list_network_interfaces = MagicMock(
        return_value=RESP_NI, side_effect=exec_original
    )
    api_obj.list_arrays = MagicMock(return_value=RESP_ARRAYS, side_effect=exec_original)
    api_obj.list_api_clients = MagicMock(
        return_value=RESP_AC, side_effect=exec_original
    )
    api_obj.list_volume_snapshots = MagicMock(
        return_value=RESP_VS, side_effect=exec_original
    )
    m_ni_api.return_value = api_obj
    m_se_api.return_value = api_obj
    m_nig_api.return_value = api_obj
    m_array_api.return_value = api_obj
    m_az_api.return_value = api_obj
    m_snapshot_api.return_value = api_obj
    m_pg_api.return_value = api_obj
    m_vs_api.return_value = api_obj
    m_volume_api.return_value = api_obj
    m_ts_api.return_value = api_obj
    m_ra_api.return_value = api_obj
    m_sc_api.return_value = api_obj
    m_role_api.return_value = api_obj
    m_region_api.return_value = api_obj
    m_tenant_api.return_value = api_obj
    m_ss_api.return_value = api_obj
    m_hw_api.return_value = api_obj
    m_hap_api.return_value = api_obj
    m_pp_api.return_value = api_obj
    m_im_api.return_value = api_obj
    m_default_api.return_value = api_obj

    set_module_args(
        {
            "gather_subset": [subset],
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        }
    )

    with pytest.raises(exec_catch) as exc:
        fusion_info.main()

    # in case of permission denied error, check correct output
    if exec_catch == AnsibleExitJson:
        assert exc.value.changed is False

        expected_keys = EXPECTED_KEYS[subset]
        assert exc.value.fusion_info.keys() == expected_keys
        for key in expected_keys:
            if key == "default":
                for k in exc.value.fusion_info[key]:
                    assert exc.value.fusion_info[key][k] is None
            else:
                assert exc.value.fusion_info[key] is None


@patch("fusion.StorageServicesApi")
def test_info_hidden_fields_storage_services(m_ss_api):
    set_module_args(
        {
            "gather_subset": ["storage_services"],
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        }
    )

    response = purefusion.StorageServiceList(
        count=1,
        more_items_remaining=False,
        items=[
            purefusion.StorageService(
                id="503",
                name="ss2",
                self_link="self_link_value",
                display_name="Storage Service 3",
                hardware_types=None,  # can be None if not enough permissions
            ),
        ],
    )

    api_obj = MagicMock()
    api_obj.list_storage_services = MagicMock(return_value=response)
    m_ss_api.return_value = api_obj

    with pytest.raises(AnsibleExitJson) as exc:
        fusion_info.main()

    expected = {
        "storage_services": {
            service.name: {
                "display_name": service.display_name,
                "hardware_types": None,
            }
            for service in response.items
        },
    }
    assert exc.value.fusion_info == expected


@patch("fusion.RegionsApi")
@patch("fusion.AvailabilityZonesApi")
@patch("fusion.StorageEndpointsApi")
def test_info_hidden_fields_storage_endpoints(m_ss_api, m_az_api, m_region_api):
    set_module_args(
        {
            "gather_subset": ["storage_endpoints"],
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        }
    )

    response = purefusion.StorageEndpointList(
        count=1,
        more_items_remaining=False,
        items=[
            purefusion.StorageEndpoint(
                id="541",
                name="se1",
                self_link="self_link_value",
                display_name="Storage Endpoint 1",
                region=purefusion.RegionRef(
                    id="542",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                availability_zone=purefusion.AvailabilityZoneRef(
                    id="543",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                endpoint_type="iscsi",
                iscsi=purefusion.StorageEndpointIscsi(
                    discovery_interfaces=[
                        purefusion.StorageEndpointIscsiDiscoveryInterface(
                            address="10.21.200.5/24",
                            gateway="10.21.200.0",
                            mtu=2000,
                            network_interface_groups=None,
                        ),
                    ]
                ),
            )
        ],
    )

    api_obj = MagicMock()
    api_obj.list_regions = MagicMock(return_value=RESP_REGIONS)
    api_obj.list_availability_zones = MagicMock(return_value=RESP_AZ)
    api_obj.list_storage_endpoints = MagicMock(return_value=response)
    m_ss_api.return_value = api_obj
    m_az_api.return_value = api_obj
    m_region_api.return_value = api_obj

    with pytest.raises(AnsibleExitJson) as exc:
        fusion_info.main()

    expected = {
        "storage_endpoints": {
            region.name
            + "/"
            + az.name
            + "/"
            + endpoint.name: {
                "display_name": endpoint.display_name,
                "endpoint_type": endpoint.endpoint_type,
                "iscsi_interfaces": [
                    {
                        "address": iface.address,
                        "gateway": iface.gateway,
                        "mtu": iface.mtu,
                        "network_interface_groups": None,
                    }
                    for iface in endpoint.iscsi.discovery_interfaces
                ],
            }
            for region in RESP_REGIONS.items
            for az in RESP_AZ.items
            for endpoint in response.items
        },
    }
    assert exc.value.fusion_info == expected


@patch("fusion.TenantsApi")
@patch("fusion.TenantSpacesApi")
@patch("fusion.VolumesApi")
def test_info_hidden_fields_volumes(m_ss_api, m_az_api, m_region_api):
    set_module_args(
        {
            "gather_subset": ["volumes"],
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        }
    )

    response = purefusion.VolumeList(
        count=1,
        more_items_remaining=False,
        items=[
            purefusion.Volume(
                id="517",
                name="volume1",
                self_link="self_link_value",
                display_name="Volume 1",
                size=4000000,
                tenant=purefusion.TenantRef(
                    id="518",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                tenant_space=purefusion.TenantSpaceRef(
                    id="519",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                storage_class=purefusion.StorageClassRef(
                    id="520",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                protection_policy=purefusion.ProtectionPolicyRef(
                    id="521",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                placement_group=purefusion.PlacementGroupRef(
                    id="522",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                array=None,
                created_at=485743825,
                source_volume_snapshot=purefusion.VolumeSnapshotRef(
                    id="523",
                    name="res_ref_name",
                    kind="kind_value",
                    self_link="self_link_value",
                ),
                host_access_policies=[
                    purefusion.HostAccessPolicyRef(
                        id="524",
                        name="res_ref_name",
                        kind="kind_value",
                        self_link="self_link_value",
                    )
                ],
                serial_number="123923482034",
                target=purefusion.Target(
                    iscsi=purefusion.Iscsi(
                        iqn="iqn.2023-05.com.purestorage:420qp2c0222",
                        addresses=["125.1.2.4"],
                    )
                ),
                time_remaining=1000000,
                destroyed=False,
            )
        ],
    )

    api_obj = MagicMock()
    api_obj.list_tenants = MagicMock(return_value=RESP_TENANTS)
    api_obj.list_tenant_spaces = MagicMock(return_value=RESP_TS)
    api_obj.list_volumes = MagicMock(return_value=response)
    m_ss_api.return_value = api_obj
    m_az_api.return_value = api_obj
    m_region_api.return_value = api_obj

    with pytest.raises(AnsibleExitJson) as exc:
        fusion_info.main()

    expected = {
        "volumes": {
            tenant.name
            + "/"
            + tenant_space.name
            + "/"
            + volume.name: {
                "tenant": tenant.name,
                "tenant_space": tenant_space.name,
                "name": volume.name,
                "size": volume.size,
                "display_name": volume.display_name,
                "placement_group": volume.placement_group.name,
                "source_volume_snapshot": getattr(
                    volume.source_volume_snapshot, "name", None
                ),
                "protection_policy": getattr(volume.protection_policy, "name", None),
                "storage_class": volume.storage_class.name,
                "serial_number": volume.serial_number,
                "target": {
                    "iscsi": {
                        "addresses": volume.target.iscsi.addresses,
                        "iqn": volume.target.iscsi.iqn,
                    },
                    "nvme": {
                        "addresses": None,
                        "nqn": None,
                    },
                    "fc": {
                        "addresses": None,
                        "wwns": None,
                    },
                },
                "array": None,
            }
            for volume in response.items
            for tenant_space in RESP_TS.items
            for tenant in RESP_TENANTS.items
        }
    }
    assert exc.value.fusion_info == expected


@patch("fusion.DefaultApi")
@patch("fusion.IdentityManagerApi")
@patch("fusion.ProtectionPoliciesApi")
@patch("fusion.HostAccessPoliciesApi")
@patch("fusion.HardwareTypesApi")
@patch("fusion.StorageServicesApi")
@patch("fusion.TenantsApi")
@patch("fusion.RegionsApi")
@patch("fusion.RolesApi")
@patch("fusion.StorageClassesApi")
@patch("fusion.RoleAssignmentsApi")
@patch("fusion.TenantSpacesApi")
@patch("fusion.VolumesApi")
@patch("fusion.VolumeSnapshotsApi")
@patch("fusion.PlacementGroupsApi")
@patch("fusion.SnapshotsApi")
@patch("fusion.AvailabilityZonesApi")
@patch("fusion.ArraysApi")
@patch("fusion.NetworkInterfaceGroupsApi")
@patch("fusion.StorageEndpointsApi")
@patch("fusion.NetworkInterfacesApi")
def test_info_permission_denied_minimum(
    m_ni_api,
    m_se_api,
    m_nig_api,
    m_array_api,
    m_az_api,
    m_snapshot_api,
    m_pg_api,
    m_vs_api,
    m_volume_api,
    m_ts_api,
    m_ra_api,
    m_sc_api,
    m_role_api,
    m_region_api,
    m_tenant_api,
    m_ss_api,
    m_hw_api,
    m_hap_api,
    m_pp_api,
    m_im_api,
    m_default_api,
):
    """
    Test that default dict works correctly with permission denied errors.
    """
    exec = ApiExceptionsMockGenerator.create_permission_denied()

    api_obj = MagicMock()
    api_obj.get_version = MagicMock(return_value=RESP_VERSION, side_effect=exec)
    api_obj.get_array_space = MagicMock(return_value=RESP_AS, side_effect=exec)
    api_obj.get_array_performance = MagicMock(return_value=RESP_AP, side_effect=exec)
    api_obj.list_users = MagicMock(return_value=RESP_LU, side_effect=exec)
    api_obj.list_protection_policies = MagicMock(return_value=RESP_PP, side_effect=exec)
    api_obj.list_host_access_policies = MagicMock(
        return_value=RESP_HAP, side_effect=exec
    )
    api_obj.list_hardware_types = MagicMock(return_value=RESP_HT, side_effect=exec)
    api_obj.list_storage_services = MagicMock(return_value=RESP_SS, side_effect=exec)
    api_obj.list_tenants = MagicMock(return_value=RESP_TENANTS, side_effect=exec)
    api_obj.list_regions = MagicMock(return_value=RESP_REGIONS, side_effect=exec)
    api_obj.list_roles = MagicMock(return_value=RESP_ROLES, side_effect=exec)
    api_obj.list_storage_classes = MagicMock(return_value=RESP_SC, side_effect=exec)
    api_obj.list_role_assignments = MagicMock(return_value=RESP_RA, side_effect=exec)
    api_obj.list_tenant_spaces = MagicMock(return_value=RESP_TS, side_effect=exec)
    api_obj.list_volumes = MagicMock(return_value=RESP_VOLUMES, side_effect=exec)
    api_obj.list_placement_groups = MagicMock(return_value=RESP_PG, side_effect=exec)
    api_obj.list_snapshots = MagicMock(return_value=RESP_SNAPSHOTS, side_effect=exec)
    api_obj.list_availability_zones = MagicMock(return_value=RESP_AZ, side_effect=exec)
    api_obj.list_network_interface_groups = MagicMock(
        return_value=RESP_NIG, side_effect=exec
    )
    api_obj.list_storage_endpoints = MagicMock(return_value=RESP_SE, side_effect=exec)
    api_obj.list_network_interfaces = MagicMock(return_value=RESP_NI, side_effect=exec)
    api_obj.list_arrays = MagicMock(return_value=RESP_ARRAYS, side_effect=exec)
    api_obj.list_api_clients = MagicMock(return_value=RESP_AC, side_effect=exec)
    api_obj.list_volume_snapshots = MagicMock(return_value=RESP_VS, side_effect=exec)
    m_ni_api.return_value = api_obj
    m_se_api.return_value = api_obj
    m_nig_api.return_value = api_obj
    m_array_api.return_value = api_obj
    m_az_api.return_value = api_obj
    m_snapshot_api.return_value = api_obj
    m_pg_api.return_value = api_obj
    m_vs_api.return_value = api_obj
    m_volume_api.return_value = api_obj
    m_ts_api.return_value = api_obj
    m_ra_api.return_value = api_obj
    m_sc_api.return_value = api_obj
    m_role_api.return_value = api_obj
    m_region_api.return_value = api_obj
    m_tenant_api.return_value = api_obj
    m_ss_api.return_value = api_obj
    m_hw_api.return_value = api_obj
    m_hap_api.return_value = api_obj
    m_pp_api.return_value = api_obj
    m_im_api.return_value = api_obj
    m_default_api.return_value = api_obj

    set_module_args(
        {
            "gather_subset": ["minimum"],
            "app_id": "ABCD1234",
            "key_file": "private-key.pem",
        }
    )

    with pytest.raises(AnsibleExitJson) as exc:
        fusion_info.main()

    assert exc.value.changed is False
    assert "default" in exc.value.fusion_info
    assert {
        "version": None,
        "users": None,
        "protection_policies": None,
        "host_access_policies": None,
        "hardware_types": None,
        "storage_services": None,
        "tenants": None,
        "regions": None,
        "storage_classes": None,
        "roles": None,
        "role_assignments": None,
        "tenant_spaces": None,
        "volumes": None,
        "placement_groups": None,
        "snapshots": None,
        "availability_zones": None,
        "arrays": None,
        "network_interfaces": None,
        "network_interface_groups": None,
        "storage_endpoints": None,
    } == exc.value.fusion_info["default"]
