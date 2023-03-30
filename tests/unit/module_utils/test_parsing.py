# -*- coding: utf-8 -*-

# (c) 2023, Jan Kodera (jkodera@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.purestorage.fusion.plugins.module_utils.parsing import (
    parse_number_with_metric_suffix,
    print_number_with_metric_suffix,
    parse_minutes,
)

import pytest


class MockException(Exception):
    pass


class MockModule:
    def fail_json(self, msg):
        raise MockException()


def test_parsing_valid_number():
    module = MockModule()
    assert parse_number_with_metric_suffix(module, "0") == 0
    assert parse_number_with_metric_suffix(module, "1") == 1
    assert parse_number_with_metric_suffix(module, "1K") == 1024
    assert parse_number_with_metric_suffix(module, "1 K") == 1024
    assert parse_number_with_metric_suffix(module, "124 M") == 124 * 1024 * 1024
    assert parse_number_with_metric_suffix(module, "10 G") == 10 * 1024 * 1024 * 1024
    assert (
        parse_number_with_metric_suffix(module, "20 T")
        == 20 * 1024 * 1024 * 1024 * 1024
    )
    assert (
        parse_number_with_metric_suffix(module, "30 P")
        == 30 * 1024 * 1024 * 1024 * 1024 * 1024
    )
    assert (
        parse_number_with_metric_suffix(module, "30000 P")
        == 30000 * 1024 * 1024 * 1024 * 1024 * 1024
    )
    assert parse_number_with_metric_suffix(module, "0", factor=1000) == 0
    assert parse_number_with_metric_suffix(module, "1", factor=1000) == 1
    assert parse_number_with_metric_suffix(module, "1K", factor=1000) == 1000
    assert (
        parse_number_with_metric_suffix(module, "124M", factor=1000)
        == 124 * 1000 * 1000
    )
    assert parse_number_with_metric_suffix(module, "1.5K", factor=1000) == 1500
    assert parse_number_with_metric_suffix(module, "1.5K", factor=1024) == 1536


def test_parsing_invalid_number():
    module = MockModule()
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "102X")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "102 N")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "102 N", factor=1000)
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "million")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "K")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "K1")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "1K1")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "1 K1")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "M")
    with pytest.raises(MockException):
        assert parse_number_with_metric_suffix(module, "hello world")


def test_printing():
    assert print_number_with_metric_suffix(0) == "0 "
    assert print_number_with_metric_suffix(1) == "1 "
    assert print_number_with_metric_suffix(124) == "124 "
    assert print_number_with_metric_suffix(1024) == "1 K"
    assert print_number_with_metric_suffix(1024, factor=1000) == "1.02 K"
    assert print_number_with_metric_suffix(2048) == "2 K"


def test_parsing_valid_time_period():
    module = MockModule()
    assert parse_minutes(module, "10") == 10
    assert parse_minutes(module, "2h") == 120
    assert parse_minutes(module, "2H") == 120
    assert parse_minutes(module, "14D") == 14 * 24 * 60
    assert parse_minutes(module, "1W") == 7 * 24 * 60
    assert parse_minutes(module, "12Y") == 12 * 365 * 24 * 60
    assert (
        parse_minutes(module, "10Y20W30D40H50M")
        == 10 * 365 * 24 * 60 + 20 * 7 * 24 * 60 + 30 * 24 * 60 + 40 * 60 + 50
    )
    assert (
        parse_minutes(module, "10Y20W30D40H")
        == 10 * 365 * 24 * 60 + 20 * 7 * 24 * 60 + 30 * 24 * 60 + 40 * 60
    )
    assert (
        parse_minutes(module, "10Y20W30D")
        == 10 * 365 * 24 * 60 + 20 * 7 * 24 * 60 + 30 * 24 * 60
    )
    assert parse_minutes(module, "10Y20W") == 10 * 365 * 24 * 60 + 20 * 7 * 24 * 60
    assert (
        parse_minutes(module, "20W30D40H50M")
        == 20 * 7 * 24 * 60 + 30 * 24 * 60 + 40 * 60 + 50
    )
    assert parse_minutes(module, "30D40H50M") == 30 * 24 * 60 + 40 * 60 + 50
    assert parse_minutes(module, "40H50M") == 40 * 60 + 50
    assert parse_minutes(module, "30D50M") == 30 * 24 * 60 + 50
    assert parse_minutes(module, "20W40H") == 20 * 7 * 24 * 60 + 40 * 60


def test_parsing_invalid_time_period():
    module = MockModule()
    with pytest.raises(MockException):
        assert parse_minutes(module, "")
    with pytest.raises(MockException):
        assert parse_minutes(module, "1s")
    with pytest.raises(MockException):
        assert parse_minutes(module, "1S")
    with pytest.raises(MockException):
        assert parse_minutes(module, "1V")
    with pytest.raises(MockException):
        assert parse_minutes(module, "0M")
    with pytest.raises(MockException):
        assert parse_minutes(module, "0H10M")
    with pytest.raises(MockException):
        assert parse_minutes(module, "0H10M")
    with pytest.raises(MockException):
        assert parse_minutes(module, "0D10H10M")
    with pytest.raises(MockException):
        assert parse_minutes(module, "01W10D10H10M")
    with pytest.raises(MockException):
        assert parse_minutes(module, "01Y0H10M")
    with pytest.raises(MockException):
        assert parse_minutes(module, "1V")
