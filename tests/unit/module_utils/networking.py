# -*- coding: utf-8 -*-

# (c) 2023, Jan Kodera (jkodera@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.purestorage.fusion.plugins.module_utils.networking import (
    is_valid_address,
    is_valid_network,
    is_address_in_network,
)


def test_valid_address():
    assert is_valid_address("0.0.0.0")
    assert is_valid_address("1.1.1.1")
    assert is_valid_address("192.168.1.2")
    assert is_valid_address("255.255.255.255")


def test_invalid_address():
    assert not is_valid_address("256.1.1.1")
    assert not is_valid_address("1.256.1.1")
    assert not is_valid_address("1.1.256.1")
    assert not is_valid_address("1.1.1.256")
    assert not is_valid_address("1.1.1.256")
    assert not is_valid_address("010.010.010.010")
    assert not is_valid_address("1.1.1")
    assert not is_valid_address("hostname")
    assert not is_valid_address("0x1.0x2.0x3.0x4")


def test_valid_network():
    assert is_valid_network("0.0.0.0/8")
    assert is_valid_network("1.1.1.1/12")
    assert is_valid_network("192.168.1.2/24")
    assert is_valid_network("255.255.255.255/32")


def test_invalid_network():
    assert not is_valid_network("1.1.1.1")
    assert not is_valid_network("1.1.1.1/")
    assert not is_valid_network("1.1.1.1/1")
    assert not is_valid_network("1.1.1.1/7")
    assert not is_valid_network("1.1.1.1/33")


def test_address_is_in_network():
    assert is_address_in_network("1.1.1.1", "1.1.0.0/16")
    assert is_address_in_network("1.1.1.1", "1.1.1.1/32")


def test_address_is_not_in_network():
    assert not is_address_in_network("1.1.1.1", "1.2.0.0/16")
    assert not is_address_in_network("1.1.1.1", "1.1.1.2/32")
