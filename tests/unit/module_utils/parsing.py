# -*- coding: utf-8 -*-

# (c) 2023, Jan Kodera (jkodera@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.purestorage.fusion.plugins.module_utils.parsing import (
    parse_number_with_suffix,
    print_number_with_suffix,
)

import pytest


class MockException(Exception):
    pass


class MockModule:
    def fail_json(self, msg):
        raise MockException()


def test_parsing_valid_number():
    module = MockModule()
    assert parse_number_with_suffix(module, "0") == 0
    assert parse_number_with_suffix(module, "1") == 1
    assert parse_number_with_suffix(module, "1K") == 1024
    assert parse_number_with_suffix(module, "1 K") == 1024
    assert parse_number_with_suffix(module, "124 M") == 124 * 1024 * 1024
    assert parse_number_with_suffix(module, "10 G") == 10 * 1024 * 1024 * 1024
    assert parse_number_with_suffix(module, "20 T") == 20 * 1024 * 1024 * 1024 * 1024
    assert (
        parse_number_with_suffix(module, "30 P")
        == 30 * 1024 * 1024 * 1024 * 1024 * 1024
    )
    assert (
        parse_number_with_suffix(module, "30000 P")
        == 30000 * 1024 * 1024 * 1024 * 1024 * 1024
    )
    assert parse_number_with_suffix(module, "0", factor=1000) == 0
    assert parse_number_with_suffix(module, "1", factor=1000) == 1
    assert parse_number_with_suffix(module, "1K", factor=1000) == 1000
    assert parse_number_with_suffix(module, "124M", factor=1000) == 124 * 1000 * 1000
    assert parse_number_with_suffix(module, "1.5K", factor=1000) == 1500
    assert parse_number_with_suffix(module, "1.5K", factor=1024) == 1536


def test_parsing_invalid_number():
    module = MockModule()
    with pytest.raises(MockException):
        assert parse_number_with_suffix(module, "") == 0
    with pytest.raises(MockException):
        assert parse_number_with_suffix(module, "102X")
    with pytest.raises(MockException):
        assert parse_number_with_suffix(module, "102 N")
    with pytest.raises(MockException):
        assert parse_number_with_suffix(module, "102 N", factor=1000)
    with pytest.raises(MockException):
        assert parse_number_with_suffix(module, "million")
    with pytest.raises(MockException):
        assert parse_number_with_suffix(module, "K")
    with pytest.raises(MockException):
        assert parse_number_with_suffix(module, "M")
    with pytest.raises(MockException):
        assert parse_number_with_suffix(module, "hello world")


def test_printing():
    assert print_number_with_suffix(0) == "0 "
    assert print_number_with_suffix(1) == "1 "
    assert print_number_with_suffix(124) == "124 "
    assert print_number_with_suffix(1024) == "1 K"
    assert print_number_with_suffix(1024, factor=1000) == "1.02 K"
    assert print_number_with_suffix(2048) == "2 K"
