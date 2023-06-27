# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, Mock, patch

import fusion as purefusion
import pytest
from ansible_collections.purestorage.fusion.plugins.module_utils.errors import (
    OperationException,
)
from ansible_collections.purestorage.fusion.plugins.modules import fusion_az
from ansible_collections.purestorage.fusion.tests.helpers import (
    ApiExceptionsMockGenerator,
)
from ansible_collections.purestorage.fusion.tests.unit.mocks.module_mock import (
    ModuleMock,
)
from ansible_collections.purestorage.fusion.tests.unit.mocks.operation_mock import (
    OperationMock,
    OperationStatus,
)

fusion_az.setup_fusion = MagicMock()
current_module = (
    "ansible_collections.purestorage.fusion.tests.unit.modules.test_fusion_az"
)


def default_module_az_params(state="present", display_name="foo_az"):
    module_params = {
        "state": state,
        "name": "foo",
        "region": "region1",
        "display_name": display_name,
        "issuer_id": "ABCD12345",
        "private_key_file": "az-admin-private-key.pem",
    }
    return module_params


class TestCreateAZ:
    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_create_az_without_disp_name(self, await_operation_mock, mock_az_api):
        """
        Should create az successfully
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.create_availability_zone = MagicMock(return_value=op)

        # Mock await operation
        await_operation_mock.return_value = op

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("present", None)
        moduleMock = ModuleMock(module_params)

        # Test function
        fusion_az.create_az(moduleMock, fusion_mock)

        # Assertions
        azone = purefusion.AvailabilityZonePost(
            name=module_params["name"],
            display_name=module_params["name"],
        )
        mock_az_api_obj.create_availability_zone.assert_called_with(
            azone, region_name=module_params["region"]
        )
        await_operation_mock.assert_called_once_with(fusion_mock, op)
        moduleMock.exit_json.assert_called_once_with(
            changed=True, id=op.result.resource.id
        )

    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_create_az_check_mode(self, await_operation_mock, mock_az_api):
        """
        Should only exit_json
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.create_availability_zone = MagicMock(return_value=op)

        # Mock await operation
        await_operation_mock.return_value = op

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("present")
        moduleMock = ModuleMock(module_params, check_mode=True)

        # Test function
        fusion_az.create_az(moduleMock, fusion_mock)

        # Assertions
        mock_az_api_obj.create_availability_zone.assert_not_called()
        await_operation_mock.assert_not_called()
        moduleMock.exit_json.assert_called_once_with(changed=True, id=None)

    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_create_az_with_disp_name(self, await_operation_mock, mock_az_api):
        """
        Should create az successfully
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.create_availability_zone = MagicMock(return_value=op)

        # Mock await operation
        await_operation_mock.return_value = op

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("present")
        moduleMock = ModuleMock(module_params)

        # Test function
        fusion_az.create_az(moduleMock, fusion_mock)

        # Assertions
        azone = purefusion.AvailabilityZonePost(
            name=module_params["name"],
            display_name=module_params["display_name"],
        )
        mock_az_api_obj.create_availability_zone.assert_called_with(
            azone, region_name=module_params["region"]
        )
        await_operation_mock.assert_called_once_with(fusion_mock, op)
        moduleMock.exit_json.assert_called_once_with(
            changed=True, id=op.result.resource.id
        )

    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_create_az_conflict(self, await_operation_mock, mock_az_api):
        """
        Should raise api exception
        """
        # Mock exceptions
        api_exception = ApiExceptionsMockGenerator.create_conflict()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.create_availability_zone = Mock(side_effect=api_exception)

        # Mock await operation
        await_operation_mock.return_value = op

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("present")
        moduleMock = ModuleMock(module_params)

        # Test function
        with pytest.raises(purefusion.rest.ApiException) as exception:
            fusion_az.create_az(moduleMock, fusion_mock)
            azone = purefusion.AvailabilityZonePost(
                name=module_params["name"],
                display_name=module_params["display_name"],
            )

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            mock_az_api_obj.create_availability_zone.assert_called_with(
                azone, region_name=module_params["region"]
            )
            await_operation_mock.assert_not_called()
            moduleMock.exit_json.assert_not_called()

    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_create_az_not_found(self, await_operation_mock, mock_az_api):
        """
        Should raise api exception
        """
        # Mock exceptions
        api_exception = ApiExceptionsMockGenerator.create_not_found()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.create_availability_zone = Mock(side_effect=api_exception)

        # Mock await operation
        await_operation_mock.return_value = op

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("present")
        moduleMock = ModuleMock(module_params)

        # Test function
        with pytest.raises(purefusion.rest.ApiException) as exception:
            fusion_az.create_az(moduleMock, fusion_mock)
            azone = purefusion.AvailabilityZonePost(
                name=module_params["name"],
                display_name=module_params["display_name"],
            )

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            mock_az_api_obj.create_availability_zone.assert_called_with(
                azone, region_name=module_params["region"]
            )
            await_operation_mock.assert_not_called()
            moduleMock.exit_json.assert_not_called()

    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_create_az_op_fails(self, await_operation_mock, mock_az_api):
        """
        Should raise operation exception
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        op_exception = OperationException(op, None)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.create_availability_zone = MagicMock(return_value=op)

        # Mock await operation
        await_operation_mock.side_effect = op_exception

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("present")
        moduleMock = ModuleMock(module_params)

        # Test function
        with pytest.raises(Exception) as exception:
            fusion_az.create_az(moduleMock, fusion_mock)
            azone = purefusion.AvailabilityZonePost(
                name=module_params["name"],
                display_name=module_params["display_name"],
            )

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            mock_az_api_obj.create_availability_zone.assert_called_with(
                azone, region_name=module_params["region"]
            )
            await_operation_mock.assert_called_once(fusion_mock, op)
            moduleMock.exit_json.assert_not_called()


class TestDeleteAZ:
    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_delete_az_successfully(self, await_operation_mock, mock_az_api):
        """
        Should delete az successfully
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.delete_availability_zone = MagicMock(return_value=op)

        # Mock await operation
        await_operation_mock.return_value = op

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("absent")
        moduleMock = ModuleMock(module_params)

        # Test function
        fusion_az.delete_az(moduleMock, fusion_mock)

        # Assertions
        mock_az_api_obj.delete_availability_zone.assert_called_with(
            availability_zone_name=module_params["name"],
            region_name=module_params["region"],
        )
        await_operation_mock.assert_called_once_with(fusion_mock, op)
        moduleMock.exit_json.assert_called_once_with(changed=True)

    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_create_az_conflict(self, await_operation_mock, mock_az_api):
        """
        Should raise api exception
        """
        # Mock exceptions
        api_exception = ApiExceptionsMockGenerator.create_conflict()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.delete_availability_zone = Mock(side_effect=api_exception)

        # Mock await operation
        await_operation_mock.return_value = op

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("absent")
        moduleMock = ModuleMock(module_params)

        # Test function
        with pytest.raises(purefusion.rest.ApiException) as exception:
            fusion_az.delete_az(moduleMock, fusion_mock)

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            mock_az_api_obj.delete_availability_zone.assert_called_with(
                region_name=module_params["region"],
                availability_zone_name=module_params["name"],
            )
            await_operation_mock.assert_not_called()
            moduleMock.exit_json.assert_not_called()

    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_create_az_op_fails(self, await_operation_mock, mock_az_api):
        """
        Should raise operation exception
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        op_exception = OperationException(op, None)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.delete_availability_zone = MagicMock(return_value=op)

        # Mock await operation
        await_operation_mock.side_effect = op_exception

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("absent")
        moduleMock = ModuleMock(module_params)

        # Test function
        with pytest.raises(OperationException) as exception:
            fusion_az.delete_az(moduleMock, fusion_mock)
            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            mock_az_api_obj.delete_availability_zone.assert_called_with(
                region_name=module_params["region"],
                availability_zone_name=module_params["name"],
            )
            await_operation_mock.assert_called_once(fusion_mock, op)
            moduleMock.exit_json.assert_not_called()

    @patch(f"{current_module}.fusion_az.purefusion.AvailabilityZonesApi.__new__")
    @patch(f"{current_module}.fusion_az.await_operation")
    def test_delete_az_check_mode(self, await_operation_mock, mock_az_api):
        """
        Should only exit_json
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock az api
        mock_az_api_obj = MagicMock()
        mock_az_api.return_value = mock_az_api_obj
        mock_az_api_obj.delete_availability_zone = MagicMock(return_value=op)

        # Mock await operation
        await_operation_mock.return_value = op

        # Mock fusion
        fusion_mock = MagicMock()

        # Mock Module
        module_params = default_module_az_params("absent")
        moduleMock = ModuleMock(module_params, check_mode=True)

        # Test function
        fusion_az.delete_az(moduleMock, fusion_mock)

        # Assertions
        mock_az_api_obj.delete_availability_zone.assert_not_called()
        await_operation_mock.assert_not_called()
        moduleMock.exit_json.assert_called_once_with(changed=True)
