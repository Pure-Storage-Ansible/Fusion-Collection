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

    def __init__(self, id=None, success=None):
        if success is None:
            self.status = "Pending"
        elif success:
            self.status = "Succeeded"
        else:
            self.status = "Failed"
        self.id = id


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

    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs

    @property
    def changed(self):
        return self.kwargs["changed"]


class AnsibleFailJson(Exception):
    """
    Exception class to be raised by module.fail_json and caught by the test case
    Docs: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html
    """

    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def exit_json(*args, **kwargs):
    """
    Function to patch over exit_json; package return data into an exception
    Docs: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html
    """

    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(args, kwargs)


def fail_json(*args, **kwargs):
    """
    Function to patch over fail_json; package return data into an exception
    Docs: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html
    """

    kwargs["failed"] = True
    raise AnsibleFailJson(args, kwargs)


def side_effects_with_exceptions(side_effects):
    """
    Assumes side_effects is a list. Works similarly to `MagicMock(side_effect=side_effects)`,
    but if item in the list is instance of an exception, it raises it instead of returning it.
    """
    side_effects = side_effects.copy()

    def _pop_side_effect(*args, **kwargs):
        i = side_effects.pop(0)
        if isinstance(i, Exception):
            raise i
        return i

    return _pop_side_effect
