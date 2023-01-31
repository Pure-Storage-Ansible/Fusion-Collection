# -*- coding: utf-8 -*-

# (c) 2023, Jan Kodera (jkodera@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

UNIT_SUFFIXES = ["K", "M", "G", "T", "P"]


def parse_number_with_suffix(module, number, factor=1024):
    """Given a human-readable string (e.g. 2G, 30M, 400),
    return the resolved integer.
    Will fail via Ansible if the input is not valid.
    """
    try:
        stripped_num = number.strip()
        if stripped_num[-1].isdigit():
            return int(stripped_num)
        # has unit prefix
        result = float(stripped_num[:-1])
        suffix = stripped_num[-1].upper()
        factor_count = UNIT_SUFFIXES.index(suffix) + 1
        for _i in range(0, factor_count):
            result = result * float(factor)
        return int(result)
    except Exception:
        module.fail_json(
            msg="'{0}' is not a valid number, use '400', '1K', '2M', ...".format(number)
        )
    return 0


def print_number_with_suffix(number, factor=1024):
    """Returns string with the number, suffixed space and
    potentially factor suffix, e.g. 400 -> '400 ', 1000 -> '1 K'
    etc."""
    factor_count = 0
    float_rem = number
    int_rem = number
    while factor_count < len(UNIT_SUFFIXES) and int_rem >= int(factor):
        float_rem = int_rem / float(factor)
        int_rem = int_rem / int(factor)
        factor_count += 1
    if factor_count == 0:
        return "{0} ".format(number)
    return "{0:.5g} {1}".format(round(float_rem, 2), UNIT_SUFFIXES[factor_count - 1])
