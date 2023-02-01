# -*- coding: utf-8 -*-

# (c) 2023, Jan Kodera (jkodera@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import time
import math

try:
    import fusion as purefusion
except ImportError:
    pass


def await_operation(module, fusion, op_id, fail_playbook_if_operation_fails=True):
    """
    Waits for given operation to finish.
    Throws an exception if the operation fails or times out.
    """
    op_api = purefusion.OperationsApi(fusion)
    next_timeout = 250
    while True:
        op = op_api.get_operation(op_id)
        if op.status == "Succeeded":
            return op
        if op.status == "Failed":
            if fail_playbook_if_operation_fails:
                module.fail_json(
                    msg="operation {0} ({1}) failed: {2}".format(
                        op_id, op.request_type, op.error
                    )
                )
            return op
        time.sleep(int(math.ceil(op.retry_in / 1000)))
