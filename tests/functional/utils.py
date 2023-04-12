from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from dataclasses import dataclass

from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes


@dataclass
class OperationMock:
    """
    Mock Operation object. This object should be returned by mocked api.
    """

    id: int


class SuccessfulOperationMock:
    """
    Mock object for successful operation. This object is returned by mocked Operation API if the operation was successful.
    """

    status = "Succeeded"


class FailedOperationMock:
    """
    Mock object for failed operation. This object is returned by mocked Operation API if the operation failed.
    """

    status = "Failed"


def set_module_args(args):
    """
    Prepare arguments so that they will be picked up during module creation.
    Docs: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html
    """

    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    """
    Exception class to be raised by module.exit_json and caught by the test case
    Docs: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html
    """

    pass


class AnsibleFailJson(Exception):
    """
    Exception class to be raised by module.fail_json and caught by the test case
    Docs: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html
    """

    pass


def exit_json(*args, **kwargs):
    """
    Function to patch over exit_json; package return data into an exception
    Docs: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html
    """

    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """
    Function to patch over fail_json; package return data into an exception
    Docs: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html
    """

    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)
