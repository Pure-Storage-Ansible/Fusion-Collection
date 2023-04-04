# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import fusion as purefusion

from unittest.mock import Mock, MagicMock, patch, call
import pytest

from ansible_collections.purestorage.fusion.tests.unit.mocks.operation_mock import (
    OperationMock,
    OperationStatus,
)
from ansible_collections.purestorage.fusion.tests.unit.mocks.module_mock import (
    ModuleMock,
    ModuleSucceeded,
)
from ansible_collections.purestorage.fusion.tests.unit.mocks.exceptions_mock import (
    ApiExceptionsMockGenerator,
)
from ansible_collections.purestorage.fusion.plugins.module_utils.errors import (
    OperationException,
)
from ansible_collections.purestorage.fusion.tests.unit.mocks.array_mock import (
    MockArray,
)

from urllib3.exceptions import HTTPError
from ansible_collections.purestorage.fusion.plugins.modules import fusion_array

fusion_array.setup_fusion = MagicMock()
current_module = (
    "ansible_collections.purestorage.fusion.tests.unit.modules.test_fusion_array"
)


def default_module_array_params(state="present", display_name="foo_array_disp"):
    module_params = {
        "state": state,
        "name": "foo",
        "availability_zone": "az1",
        "region": "region1",
        "hardware_type": "flash-array-x",
        "host_name": "foo_array",
        "display_name": display_name,
        "appliance_id": "1227571-198887878-35016350232000707",
        "maintenance_mode": None,
        "unavailable_mode": None,
        "app_id": "ABCD12345",
        "key_file": "az-admin-private-key.pem",
    }
    return module_params


class TestArrayWorkflow:
    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_delete_array_successfully(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should delete array successfully
        """

        # Mock getters
        get_array.return_value = MagicMock()

        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.delete_array = MagicMock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("absent")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module
        mock_module.exit_json = Mock(side_effect=ModuleSucceeded())

        with pytest.raises(ModuleSucceeded) as module_finished:
            # Test function
            fusion_array.main()

            # Assertions
            get_array.assert_called_once()
            mock_array_api_obj.delete_array.assert_called_once_with(
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
                array_name=module_params["name"],
            )
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_create_array_without_disp_name_successfully(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should create array successfully
        """

        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.create_array = MagicMock(return_value=op)
        mock_array_api.update_array = MagicMock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present", None)
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module
        mock_module.exit_json = Mock(side_effect=ModuleSucceeded())

        # Mock getters
        get_array.side_effect = [None, MockArray(module_params)]

        with pytest.raises(ModuleSucceeded) as module_finished:
            # Test function
            fusion_array.main()

            # Assertions
            assert type(module_finished) == ModuleSucceeded
            get_array.assert_called_once()
            array = purefusion.ArrayPost(
                hardware_type=module_params["hardware_type"],
                display_name=module_params["name"],
                host_name=module_params["host_name"],
                name=module_params["name"],
                appliance_id=module_params["appliance_id"],
            )
            mock_array_api_obj.create_array.assert_called_once_with(
                array,
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
            )
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_create_array_with_disp_name_successfully(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should create array successfully
        """

        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.create_array = MagicMock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module
        mock_module.exit_json = Mock(side_effect=ModuleSucceeded())

        # Mock getters
        get_array.side_effect = [None, MockArray(module_params)]

        with pytest.raises(ModuleSucceeded) as module_finished:
            # Test function
            fusion_array.main()

            # Assertions
            assert type(module_finished) == ModuleSucceeded
            get_array.assert_called_once()
            array = purefusion.ArrayPost(
                hardware_type=module_params["hardware_type"],
                display_name=module_params["display_name"],
                host_name=module_params["host_name"],
                name=module_params["name"],
                appliance_id=module_params["appliance_id"],
            )
            mock_array_api_obj.create_array.assert_called_once_with(
                array,
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
            )
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_create_array_op_fails(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise OperationException
        """

        # Mock getters
        get_array.return_value = None

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        op_exception = OperationException(op, None)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.create_array = MagicMock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        with pytest.raises(OperationException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            get_array.assert_called_once()
            array = purefusion.ArrayPost(
                hardware_type=module_params["hardware_type"],
                display_name=module_params["display_name"],
                host_name=module_params["host_name"],
                name=module_params["name"],
                appliance_id=module_params["appliance_id"],
            )
            mock_array_api_obj.create_array.assert_called_once_with(
                array,
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_create_array_array_api_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise ApiException
        """

        # Mock getters
        get_array.return_value = None

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        exceptions_factory = ApiExceptionsMockGenerator()
        api_exception = exceptions_factory.create_conflict()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.create_array = Mock(
            return_value=op, side_effect=api_exception
        )

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        with pytest.raises(purefusion.rest.ApiException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            get_array.assert_called_once()
            array = purefusion.ArrayPost(
                hardware_type=module_params["hardware_type"],
                display_name=module_params["display_name"],
                host_name=module_params["host_name"],
                name=module_params["name"],
                appliance_id=module_params["appliance_id"],
            )
            mock_array_api_obj.create_array.assert_called_once_with(
                array,
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_create_array_op_api_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise ApiException
        """

        # Mock getters
        get_array.return_value = None

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        exceptions_factory = ApiExceptionsMockGenerator()
        api_exception = exceptions_factory.create_not_found()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op, side_effect=api_exception)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.create_array = Mock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        with pytest.raises(purefusion.rest.ApiException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            get_array.assert_called_once()
            array = purefusion.ArrayPost(
                hardware_type=module_params["hardware_type"],
                display_name=module_params["display_name"],
                host_name=module_params["host_name"],
                name=module_params["name"],
                appliance_id=module_params["appliance_id"],
            )
            mock_array_api_obj.create_array.assert_called_once_with(
                array,
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_create_array_op_http_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise OperationException
        """

        # Mock getters
        get_array.return_value = None

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        http_error = HTTPError()
        op_exception = OperationException(op, http_error)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op, side_effect=http_error)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.create_array = Mock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        with pytest.raises(OperationException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            get_array.assert_called_once()
            array = purefusion.ArrayPost(
                hardware_type=module_params["hardware_type"],
                display_name=module_params["display_name"],
                host_name=module_params["host_name"],
                name=module_params["name"],
                appliance_id=module_params["appliance_id"],
            )
            mock_array_api_obj.create_array.assert_called_once_with(
                array,
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_create_array_array_http_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise HTTPError
        """

        # Mock getters
        get_array.return_value = None

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        http_error = HTTPError()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.create_array = Mock(return_value=op, side_effect=http_error)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        with pytest.raises(HTTPError) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(http_error)
                and exception.args == http_error.args
            )
            get_array.assert_called_once()
            array = purefusion.ArrayPost(
                hardware_type=module_params["hardware_type"],
                display_name=module_params["display_name"],
                host_name=module_params["host_name"],
                name=module_params["name"],
                appliance_id=module_params["appliance_id"],
            )
            mock_array_api_obj.create_array.assert_called_once_with(
                array,
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_delete_az_op_fails(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise OperationException
        """

        # Mock getters
        get_array.return_value = MagicMock()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        op_exception = OperationException(op, None)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.delete_array = MagicMock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("absent")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        with pytest.raises(OperationException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            get_array.assert_called_once()
            mock_array_api_obj.delete_array.assert_called_once_with(
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
                array_name=module_params["name"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_delete_az_az_api_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise ApiException
        """

        # Mock getters
        get_array.return_value = MagicMock()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        exceptions_factory = ApiExceptionsMockGenerator()
        api_exception = exceptions_factory.create_conflict()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.delete_array = Mock(
            return_value=op, side_effect=api_exception
        )

        # Mock Module
        module_params = default_module_array_params("absent")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module
        with pytest.raises(purefusion.rest.ApiException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            get_array.assert_called_once()
            mock_array_api_obj.delete_array.assert_called_once_with(
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
                array_name=module_params["name"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_delete_az_op_api_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise ApiException
        """

        # Mock getters
        get_array.return_value = MagicMock()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        exceptions_factory = ApiExceptionsMockGenerator()
        api_exception = exceptions_factory.create_not_found()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op, side_effect=api_exception)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.delete_array = Mock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("absent")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        with pytest.raises(purefusion.rest.ApiException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            get_array.assert_called_once()
            mock_array_api_obj.delete_array.assert_called_once_with(
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
                array_name=module_params["name"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_delete_az_op_http_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise OperationException
        """

        # Mock getters
        get_array.return_value = MagicMock()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        http_error = HTTPError()
        op_exception = OperationException(op, http_error)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op, side_effect=http_error)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.delete_array = Mock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("absent")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module
        with pytest.raises(OperationException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            get_array.assert_called_once()
            mock_array_api_obj.delete_array.assert_called_once_with(
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
                array_name=module_params["name"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_delete_az_az_http_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise HTTPError
        """

        # Mock getters
        get_array.return_value = MagicMock()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        http_error = HTTPError()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.delete_array = Mock(return_value=op, side_effect=http_error)

        # Mock Module
        module_params = default_module_array_params("absent")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module
        with pytest.raises(HTTPError) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(http_error)
                and exception.args == http_error.args
            )
            get_array.assert_called_once()
            mock_array_api_obj.delete_array.assert_called_once_with(
                availability_zone_name=module_params["availability_zone"],
                region_name=module_params["region"],
                array_name=module_params["name"],
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_update_array_successfully(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should update array successfully
        """

        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.update_array = MagicMock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present")

        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module
        mock_module.exit_json = Mock(side_effect=ModuleSucceeded())

        # Mock getters
        get_array.return_value = MockArray(module_params)

        module_params["maintenance_mode"] = False
        module_params["unavailable_mode"] = True
        module_params["host_name"] = "new_host_name"
        module_params["display_name"] = "new_display_name"

        with pytest.raises(ModuleSucceeded) as module_finished:
            # Test function
            fusion_array.main()

            # Assertions
            assert type(module_finished) == ModuleSucceeded
            get_array.assert_called()
            calls = [
                call(
                    purefusion.ArrayPatch(
                        display_name=purefusion.NullableString(
                            module_params["display_name"]
                        ),
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
                call(
                    patch=purefusion.ArrayPatch(
                        host_name=purefusion.NullableString(module_params["host_name"])
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
                call(
                    patch=purefusion.ArrayPatch(
                        maintenance_mode=purefusion.NullableString(
                            module_params["maintenance_mode"]
                        )
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
                call(
                    patch=purefusion.ArrayPatch(
                        unavailable_mode=purefusion.NullableString(
                            module_params["unavailable_mode"]
                        )
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
            ]
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_array_api_obj.update_array.assert_has_calls(calls)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_update_array_op_fails(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise OperationException
        """

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        op_exception = OperationException(op, None)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.update_array = MagicMock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        get_array.return_value = MockArray(module_params)

        module_params["maintenance_mode"] = False
        module_params["unavailable_mode"] = True
        module_params["host_name"] = "new_host_name"
        module_params["display_name"] = "new_display_name"

        with pytest.raises(OperationException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            get_array.assert_called()
            calls = [
                call(
                    purefusion.ArrayPatch(
                        display_name=purefusion.NullableString(
                            module_params["display_name"]
                        ),
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
            ]
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_array_api_obj.update_array.assert_has_calls(calls)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_update_array_array_api_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise ApiException
        """

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        exceptions_factory = ApiExceptionsMockGenerator()
        api_exception = exceptions_factory.create_conflict()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.update_array = Mock(
            return_value=op, side_effect=api_exception
        )

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        get_array.return_value = MockArray(module_params)

        module_params["maintenance_mode"] = False
        module_params["unavailable_mode"] = True
        module_params["host_name"] = "new_host_name"
        module_params["display_name"] = "new_display_name"

        with pytest.raises(purefusion.rest.ApiException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            get_array.assert_called()
            calls = [
                call(
                    purefusion.ArrayPatch(
                        display_name=purefusion.NullableString(
                            module_params["display_name"]
                        ),
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
            ]
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_array_api_obj.update_array.assert_has_calls(calls)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_update_array_op_api_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise ApiException
        """

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        exceptions_factory = ApiExceptionsMockGenerator()
        api_exception = exceptions_factory.create_not_found()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op, side_effect=api_exception)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.update_array = Mock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        get_array.return_value = MockArray(module_params)

        module_params["maintenance_mode"] = False
        module_params["unavailable_mode"] = True
        module_params["host_name"] = "new_host_name"
        module_params["display_name"] = "new_display_name"

        with pytest.raises(purefusion.rest.ApiException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            get_array.assert_called()
            calls = [
                call(
                    purefusion.ArrayPatch(
                        display_name=purefusion.NullableString(
                            module_params["display_name"]
                        ),
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
            ]
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_array_api_obj.update_array.assert_has_calls(calls)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_update_array_op_http_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise OperationException
        """

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        http_error = HTTPError()
        op_exception = OperationException(op, http_error)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op, side_effect=http_error)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.update_array = Mock(return_value=op)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        get_array.return_value = MockArray(module_params)

        module_params["maintenance_mode"] = False
        module_params["unavailable_mode"] = True
        module_params["host_name"] = "new_host_name"
        module_params["display_name"] = "new_display_name"

        with pytest.raises(OperationException) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            get_array.assert_called()
            calls = [
                call(
                    purefusion.ArrayPatch(
                        display_name=purefusion.NullableString(
                            module_params["display_name"]
                        ),
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
            ]
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_array_api_obj.update_array.assert_has_calls(calls)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.fusion_array.purefusion.OperationsApi.__new__")
    @patch(f"{current_module}.fusion_array.purefusion.ArraysApi.__new__")
    @patch(f"{current_module}.fusion_array.AnsibleModule")
    @patch(f"{current_module}.fusion_array.get_array")
    def test_create_array_array_http_exception(
        self, get_array, mock_ansible, mock_array_api, mock_op_api
    ):
        """
        Should raise HTTPError
        """

        # Mock getters
        get_array.return_value = None

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        http_error = HTTPError()

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock array api
        mock_array_api_obj = MagicMock()
        mock_array_api.return_value = mock_array_api_obj
        mock_array_api_obj.update_array = Mock(return_value=op, side_effect=http_error)

        # Mock Module
        module_params = default_module_array_params("present")
        mock_module = ModuleMock(module_params)
        mock_ansible.return_value = mock_module

        get_array.return_value = MockArray(module_params)

        module_params["maintenance_mode"] = False
        module_params["unavailable_mode"] = True
        module_params["host_name"] = "new_host_name"
        module_params["display_name"] = "new_display_name"
        with pytest.raises(HTTPError) as exception:
            # Test function
            fusion_array.main()

            # Assertions
            assert (
                type(exception) is type(http_error)
                and exception.args == http_error.args
            )
            get_array.assert_called()
            calls = [
                call(
                    purefusion.ArrayPatch(
                        display_name=purefusion.NullableString(
                            module_params["display_name"]
                        ),
                    ),
                    availability_zone_name=module_params["availability_zone"],
                    region_name=module_params["region"],
                    array_name=module_params["name"],
                ),
            ]
            mock_module.exit_json.assert_called_once_with(changed=True)
            mock_array_api_obj.update_array.assert_has_calls(calls)
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)
