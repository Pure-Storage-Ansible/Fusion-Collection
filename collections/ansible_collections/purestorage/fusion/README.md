# Pure Storage Fusion Collection

The Pure Storage Fusion collection consists of the latest versions of the Fusion modules.

## Modules

## Requirements

- Ansible 2.11 or later
- Authorized API Application ID for Pure Storage Pure1 and associated Private Key
  - Refer to Pure Storage documentation on how to create these. 
- purefusion
- netaddr
- time
- datetime

## Available Modules

    - fusion_api_client: Manage API clients in Pure Storage Fusion
    - fusion_array: Manage arrays in Pure Storage Fusion
    - fusion_az: Create Availability Zones in Pure Storage Fusion
    - fusion_hap: Manage host access policies in Pure Storage Fusion
    - fusion_hw: Create hardware types in Pure Storage Fusion
    - fusion_info: Collect information from Pure Fusion
    - fusion_nig: Manage Network Interface Groups in Pure Storage Fusion
    - fusion_pg: Manage placement groups in Pure Storage Fusion
    - fusion_pp: Manage protection policies in Pure Storage Fusion
    - fusion_ra: Manage role assignments in Pure Storage Fusion
    - fusion_sc: Manage storage classes in Pure Storage Fusion
    - fusion_ss: Manage storage services in Pure Storage Fusion
    - fusion_tenant: Manage tenants in Pure Storage Fusion
    - fusion_tn: Manage tenant networks in Pure Storage Fusion
    - fusion_ts: Manage tenant spaces in Pure Storage Fusion
    - fusion_volume: Manage volumes in Pure Storage Fusion

## Instructions

Install the Pure Storage Fusion collection on your Ansible management host.

- Using ansible-galaxy:
```
ansible-galaxy collection install purestorage.fusion -p ~/.ansible/collections
```

## Example Playbook
```yaml
- hosts: localhost
  tasks:
  - name: Collect information for Pure Storage fleet in Pure1
    purestorage.fusion.fusion_info:
      gather_subset: all
      app_id: <Pure1 API Application ID>
      key_file: <private key file name>
```

## License

[BSD-2-Clause](https://directory.fsf.org/wiki?title=License:FreeBSD)
[GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0.en.html)

## Author

This collection was created in 2022 by [Simon Dodsley](@sdodsley) for, and on behalf of, the [Pure Storage Ansible Team](pure-ansible-team@purestorage.com)
