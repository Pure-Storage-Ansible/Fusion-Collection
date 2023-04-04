# -*- coding: utf-8 -*-

# (c) 2023, Jan Kodera (jkodera@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.purestorage.fusion.plugins.module_utils.prerequisites import (
    _parse_version,
    _parse_version_requirements,
    _version_satisfied,
)

import pytest


def test_version():
    # VALID
    assert _parse_version("1.0") == (1, 0, None)
    assert _parse_version("1.0.0") == (1, 0, 0)
    assert _parse_version("2.3.4") == (2, 3, 4)
    assert _parse_version("2.3.5a") == (2, 3, 5)
    assert _parse_version("2.3.6-release") == (2, 3, 6)
    # INVALID
    assert _parse_version("1") is None
    assert _parse_version("1.a") is None
    assert _parse_version("1.1a") is None
    assert _parse_version("a.1") is None
    assert _parse_version("1.") is None
    assert _parse_version("1..") is None
    assert _parse_version("1.0.1.0") is None
    assert _parse_version("1.0.1.a") is None


def test_requirements():
    # VALID
    assert _parse_version_requirements(">= 1.0") == [(">=", (1, 0, None))]
    assert _parse_version_requirements(">=1.0.1") == [(">=", (1, 0, 1))]
    assert _parse_version_requirements(">= 2.0.2-release") == [(">=", (2, 0, 2))]
    assert _parse_version_requirements(" >=3.0.3b") == [(">=", (3, 0, 3))]
    assert _parse_version_requirements("<= 3.3.3") == [("<=", (3, 3, 3))]
    assert _parse_version_requirements("= 3.0.3") == [("=", (3, 0, 3))]
    assert _parse_version_requirements("== 5.3.1") == [("==", (5, 3, 1))]
    assert _parse_version_requirements("< 4.1.2") == [("<", (4, 1, 2))]
    assert _parse_version_requirements("> 1.3.4") == [(">", (1, 3, 4))]
    assert _parse_version_requirements("> 1.3.4, < 2.0") == [
        (">", (1, 3, 4)),
        ("<", (2, 0, None)),
    ]
    assert _parse_version_requirements(">1.3.4 , <2.0") == [
        (">", (1, 3, 4)),
        ("<", (2, 0, None)),
    ]
    assert _parse_version_requirements("> 1.3.4 ,< 2.0") == [
        (">", (1, 3, 4)),
        ("<", (2, 0, None)),
    ]
    assert _parse_version_requirements(">1.3.4,<2.0") == [
        (">", (1, 3, 4)),
        ("<", (2, 0, None)),
    ]
    assert _parse_version_requirements(">1.3.4,<2.0, != 3.4.1") == [
        (">", (1, 3, 4)),
        ("<", (2, 0, None)),
        ("!=", (3, 4, 1)),
    ]
    # INVALID
    with pytest.raises(ValueError):
        _parse_version_requirements(">>1.3.4")
    with pytest.raises(ValueError):
        _parse_version_requirements("<<1.3.4")
    with pytest.raises(ValueError):
        _parse_version_requirements("=>1.3.4,,3.0")
    with pytest.raises(ValueError):
        _parse_version_requirements("=<1.3.4,")
    with pytest.raises(ValueError):
        _parse_version_requirements("=<1.3.4")


def test_version_satisfied():
    assert _version_satisfied("1.0", ">=1.0, <2.0") is True
    assert _version_satisfied("1.0.1", ">=1.0, <2.0") is True
    assert _version_satisfied("2.0", ">=1.0, <2.0") is False
    assert _version_satisfied("2.0.0", ">=1.0, <2.0") is False
    assert _version_satisfied("2.0.1", ">=1.0, <2.0") is False
    assert _version_satisfied("1.0.0", ">=1.0.0") is True
    assert _version_satisfied("1.0", ">=1.0.0") is True
    assert _version_satisfied("1.0", ">=1.0") is True
    assert _version_satisfied("1.0.1", ">=1.0") is True
    assert _version_satisfied("1.0.1", ">=1.0.0") is True
    assert _version_satisfied("1.0.1", "<=1.0.0") is False
    assert _version_satisfied("1.0.0", "<=1.0.0") is True
    assert _version_satisfied("1.0", "<=1.0.0") is True
    assert _version_satisfied("1.0", "<=1.0.1") is True
    assert _version_satisfied("1.0", "<=1.0") is True
    assert _version_satisfied("1.0", "<1.0") is False
    assert _version_satisfied("1.0.0", "<1.0") is False
    assert _version_satisfied("1.0.0", "<1.1") is True
    assert _version_satisfied("1.0.0", "<1.0.1") is True
    assert _version_satisfied("1.0", ">1.0") is False
    assert _version_satisfied("1.0.1", ">1.0") is False
    assert _version_satisfied("1.0", ">1.0.0") is False
    assert _version_satisfied("1.0.0", ">1.0.0") is False
    assert _version_satisfied("1.0.1", ">1.0.0") is True
    assert _version_satisfied("1.0", "==1.0") is True
    assert _version_satisfied("1.0", "=1.0") is True
    assert _version_satisfied("1.0.0", "==1.0") is True
    assert _version_satisfied("1.0.1", "==1.0") is True
    assert _version_satisfied("1.0", "==1.0.0") is True
    assert _version_satisfied("1.0", "==1.0.1") is False
    assert _version_satisfied("1.0", "!=1.0.1") is True
    assert _version_satisfied("1.0", "!=1.0.0") is False
    assert _version_satisfied("1.0.1", "!=1.0") is False
    assert _version_satisfied("1.0", "!=1.0") is False
