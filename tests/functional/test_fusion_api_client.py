# -*- coding: utf-8 -*-

# (c) 2023, Andrej Pajtas (apajtas@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from dataclasses import asdict, dataclass
from unittest.mock import MagicMock, patch

import fusion as purefusion
import pytest
from ansible.module_utils import basic
from ansible_collections.purestorage.fusion.plugins.modules import fusion_api_client
from ansible_collections.purestorage.fusion.tests.functional.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    exit_json,
    fail_json,
    set_module_args,
)
from urllib3.exceptions import HTTPError

# GLOBAL MOCKS
fusion_api_client.setup_fusion = MagicMock(
    return_value=purefusion.api_client.ApiClient()
)
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@dataclass
class FakeApiClient:
    id: str
    self_link: str
    name: str
    display_name: str
    issuer: str
    public_key: str
    last_key_update: float
    last_used: float
    creator_id: str


@pytest.fixture
def current_clients():
    return [
        FakeApiClient(
            "1",
            "self_link_value",
            "client1",
            "client1",
            "apikey:name:thisisnotreal",
            "0123456789",
            12345,
            12345,
            "1234",
        ),
        FakeApiClient(
            "2",
            "self_link_value",
            "client2",
            "client2",
            "apikey:name:thisisnotreal",
            "0123456789",
            12345,
            12345,
            "1234",
        ),
        FakeApiClient(
            "3",
            "self_link_value",
            "client3",
            "client3",
            "apikey:name:thisisnotreal",
            "0123456789",
            12345,
            12345,
            "1234",
        ),
    ]


@patch("fusion.IdentityManagerApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'name` is missing
        {
            "state": "present",
            "public_key": "0123456789",
        },
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "client1",
            "public_key": "0123456789",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "client1",
            "public_key": "0123456789",
        },
    ],
)
def test_module_fails_on_wrong_parameters(m_im_api, module_args, current_clients):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_api_clients = MagicMock(return_value=current_clients)
    api_obj.get_api_client = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_api_client = MagicMock()
    api_obj.delete_api_client = MagicMock()
    m_im_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_api_client.main()

    # check api was not called at all
    api_obj.list_api_clients.assert_not_called()
    api_obj.get_api_client.assert_not_called()
    api_obj.create_api_client.assert_not_called()
    api_obj.delete_api_client.assert_not_called()


@patch("fusion.IdentityManagerApi")
def test_api_client_create(m_im_api, current_clients):
    module_args = {
        "state": "present",
        "name": "new_client",
        "public_key": "0123456789",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_api_clients = MagicMock(return_value=current_clients)
    api_obj.get_api_client = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_api_client = MagicMock(
        return_value=FakeApiClient(
            "321321",
            "self_link_value",
            "client_test",
            "client_test",
            "apikey:name:test",
            "321321",
            321321,
            321321,
            "321321",
        )
    )
    api_obj.delete_api_client = MagicMock()
    m_im_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_api_client.main()

    assert exc.value.changed is True
    assert exc.value.id == "321321"

    # check api was called correctly
    api_obj.list_api_clients.assert_called_once_with()
    api_obj.get_api_client.assert_not_called()
    api_obj.create_api_client.assert_called_once_with(
        purefusion.APIClientPost(
            public_key=module_args["public_key"],
            display_name=module_args["name"],
        )
    )
    api_obj.delete_api_client.assert_not_called()


@patch("fusion.IdentityManagerApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_api_client_create_exception(
    m_im_api, exec_original, exec_catch, current_clients
):
    module_args = {
        "state": "present",
        "name": "new_client",
        "public_key": "0123456789",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_api_clients = MagicMock(return_value=current_clients)
    api_obj.get_api_client = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_api_client = MagicMock(side_effect=exec_original)
    api_obj.delete_api_client = MagicMock()
    m_im_api.return_value = api_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_api_client.main()

    # check api was called correctly
    api_obj.list_api_clients.assert_called_once_with()
    api_obj.get_api_client.assert_not_called()
    api_obj.create_api_client.assert_called_once_with(
        purefusion.APIClientPost(
            public_key=module_args["public_key"],
            display_name=module_args["name"],
        )
    )
    api_obj.delete_api_client.assert_not_called()


@patch("fusion.IdentityManagerApi")
def test_api_client_present_not_changed(m_im_api, current_clients):
    current_api_client = current_clients[0]
    module_args = {
        "state": "present",
        "name": current_api_client.display_name,
        "public_key": current_api_client.public_key,
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_api_clients = MagicMock(return_value=current_clients)
    api_obj.get_api_client = MagicMock(
        return_value=purefusion.APIClient(**asdict(current_api_client))
    )
    api_obj.create_api_client = MagicMock()
    api_obj.delete_api_client = MagicMock()
    m_im_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_api_client.main()

    assert exc.value.changed is False

    # check api was called correctly
    api_obj.list_api_clients.assert_called_once_with()
    api_obj.get_api_client.assert_not_called()
    api_obj.create_api_client.assert_not_called()
    api_obj.delete_api_client.assert_not_called()


@patch("fusion.IdentityManagerApi")
def test_api_client_absent_not_changed(m_im_api, current_clients):
    module_args = {
        "state": "absent",
        "name": "non_existing_client",
        "public_key": "0123456789",
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_api_clients = MagicMock(return_value=current_clients)
    api_obj.get_api_client = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_api_client = MagicMock()
    api_obj.delete_api_client = MagicMock()
    m_im_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_api_client.main()

    assert exc.value.changed is False

    # check api was called correctly
    api_obj.list_api_clients.assert_called_once_with()
    api_obj.get_api_client.assert_not_called()
    api_obj.create_api_client.assert_not_called()
    api_obj.delete_api_client.assert_not_called()


@patch("fusion.IdentityManagerApi")
def test_api_client_delete(m_im_api, current_clients):
    current_api_client = current_clients[0]
    module_args = {
        "state": "absent",
        "name": current_api_client.display_name,
        "public_key": current_api_client.public_key,
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_api_clients = MagicMock(return_value=current_clients)
    api_obj.get_api_client = MagicMock(
        return_value=purefusion.APIClient(**asdict(current_api_client))
    )
    api_obj.create_api_client = MagicMock()
    api_obj.delete_api_client = MagicMock()
    m_im_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_api_client.main()

    assert exc.value.changed is True

    # check api was called correctly
    api_obj.list_api_clients.assert_called_once_with()
    api_obj.get_api_client.assert_not_called()
    api_obj.create_api_client.assert_not_called()
    api_obj.delete_api_client.assert_called_once_with(
        api_client_id=current_api_client.id
    )


@patch("fusion.IdentityManagerApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_api_client_delete_exception(
    m_im_api, exec_original, exec_catch, current_clients
):
    current_api_client = current_clients[0]
    module_args = {
        "state": "absent",
        "name": current_api_client.display_name,
        "public_key": current_api_client.public_key,
        "app_id": "ABCD1234",
        "key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.list_api_clients = MagicMock(return_value=current_clients)
    api_obj.get_api_client = MagicMock(
        return_value=purefusion.APIClient(**asdict(current_api_client))
    )
    api_obj.create_api_client = MagicMock()
    api_obj.delete_api_client = MagicMock(side_effect=exec_original)
    m_im_api.return_value = api_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_api_client.main()

    # check api was called correctly
    api_obj.list_api_clients.assert_called_once_with()
    api_obj.get_api_client.assert_not_called()
    api_obj.create_api_client.assert_not_called()
    api_obj.delete_api_client.assert_called_once_with(
        api_client_id=current_api_client.id
    )
