# -*- coding: utf-8 -*-

# (c) 2023, Denys Denysyev (ddenysyev@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible_collections.purestorage.fusion.plugins.module_utils.errors import (
    OperationException,
)
from ansible_collections.purestorage.fusion.tests.unit.mocks.exceptions_mock import (
    ApiExceptionsMockGenerator,
)
from ansible_collections.purestorage.fusion.tests.unit.mocks.operation_mock import (
    OperationMock,
    OperationStatus,
)

__metaclass__ = type

import fusion as purefusion
from urllib3.exceptions import HTTPError

from unittest.mock import Mock, MagicMock, call, patch
import pytest
from ansible_collections.purestorage.fusion.plugins.module_utils import operations

current_module = (
    "ansible_collections.purestorage.fusion.tests.unit.module_utils.test_operations"
)


class TestAwaitOperations:
    @patch(f"{current_module}.operations.purefusion.OperationsApi.__new__")
    def test_await_success_op(self, mock_op_api):
        """
        Should return operation
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock fusion
        fusion_mock = MagicMock()

        # Test function
        op1 = operations.await_operation(fusion_mock, op)

        # Assertions
        assert op == op1
        mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.operations.purefusion.OperationsApi.__new__")
    def test_await_failed_op(self, mock_op_api):
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

        # Mock fusion
        fusion_mock = MagicMock()

        # Test function
        with pytest.raises(Exception) as exception:
            operations.await_operation(fusion_mock, op)

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op.id)

    @patch(f"{current_module}.operations.purefusion.OperationsApi.__new__")
    def test_await_pending_op(self, mock_op_api):
        """
        Should return operation
        """
        # Mock operation
        op1 = OperationMock("1", OperationStatus.PENDING)
        op2 = OperationMock("1", OperationStatus.SUCCEDED)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(side_effect=[op1, op2])

        # Mock fusion
        fusion_mock = MagicMock()

        # Test function
        op = operations.await_operation(fusion_mock, op1)

        # Assertions
        assert op == op2
        calls = [call(op1.id), call(op1.id)]
        mock_op_api_obj.get_operation.assert_has_calls(calls)

    @patch(f"{current_module}.operations.purefusion.OperationsApi.__new__")
    def test_await_failed_pending_op(self, mock_op_api):
        """
        Should raise OperationException
        """
        # Mock operation
        op1 = OperationMock("1", OperationStatus.PENDING)
        op2 = OperationMock("1", OperationStatus.FAILED)

        # Mock exception
        op_exception = OperationException(op2, None)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(side_effect=[op1, op2])

        # Mock fusion
        fusion_mock = MagicMock()

        # Test function
        with pytest.raises(Exception) as exception:
            operations.await_operation(fusion_mock, op1)

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            calls = [call(op1.id), call(op1.id)]
            mock_op_api_obj.get_operation.assert_has_calls(calls)

    @patch(f"{current_module}.operations.purefusion.OperationsApi.__new__")
    def test_await_api_exception(self, mock_op_api):
        """
        Should raise ApiException
        """
        # Mock exceptions
        exceptions_factory = ApiExceptionsMockGenerator()
        api_exception = exceptions_factory.create_conflict()

        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(side_effect=api_exception)

        # Mock fusion
        fusion_mock = MagicMock()

        # Test function
        with pytest.raises(purefusion.rest.ApiException) as exception:
            operations.await_operation(fusion_mock, op)

            # Assertions
            assert (
                type(exception) is type(api_exception)
                and exception.args == api_exception.args
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op)

    @patch(f"{current_module}.operations.purefusion.OperationsApi.__new__")
    def test_await_http_exception(self, mock_op_api):
        """
        Should raise OperationException
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock exceptions
        http_error = HTTPError()
        op_exception = OperationException(op, http_error)
        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(side_effect=http_error)

        # Mock fusion
        fusion_mock = MagicMock()

        # Test function
        with pytest.raises(OperationException) as exception:
            operations.await_operation(fusion_mock, op)

            # Assertions
            assert (
                type(exception) is type(op_exception)
                and exception.args == op_exception.args
            )
            mock_op_api_obj.get_operation.assert_called_once_with(op)

    @patch(f"{current_module}.operations.purefusion.OperationsApi.__new__")
    def test_await_failed_op_without_failing(self, mock_op_api):
        """
        Should return failed operation
        """
        # Mock operation
        op = OperationMock("1", OperationStatus.FAILED)

        # Mock operations api
        mock_op_api_obj = MagicMock()
        mock_op_api.return_value = mock_op_api_obj
        mock_op_api_obj.get_operation = Mock(return_value=op)

        # Mock fusion
        fusion_mock = MagicMock()

        # Test function
        op_res = operations.await_operation(
            fusion_mock, op, fail_playbook_if_operation_fails=False
        )

        # Assertions
        assert op_res == op
        mock_op_api_obj.get_operation.assert_called_once_with(op.id)
