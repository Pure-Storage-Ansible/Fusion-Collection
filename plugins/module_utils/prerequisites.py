# -*- coding: utf-8 -*-

# (c) 2023, Jan Kodera (jkodera@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
import re
import importlib
import importlib.metadata
import json

# This file exists because Ansible currently cannot declare dependencies on Python modules
# when imported. When imported, it fails with Ansible-compatible message if requirements
# listed below are not installed
# see https://github.com/ansible/ansible/issues/62733 for more info about lack of req support

#############################

# 'module_name, package_name, version_requirements' triplets
DEPENDENCIES = [
    ("fusion", "purefusion", ">=1.0.11,<2.0")
]

#############################

# returns tuple (MAJOR, MINOR, PATCH)
def _parse_version(val):
    # regexes for this were really ugly
    try:
        parts = val.split('.')
        if len(parts) < 2 or len(parts) > 3:
            return None
        major = int(parts[0])
        minor = int(parts[1])
        if len(parts) > 2:
            patch = re.match(r"^\d+", parts[2])
            patch = int(patch.group(0))
        else:
            patch = None
        return (major, minor, patch)
    except:
        return None

# returns list of tuples [(COMPARATOR, (MAJOR, MINOR, PATCH)),...]
def _parse_version_requirements(val):
    reqs = []
    try:
        parts = val.split(",")
        for part in parts:
            match = re.match(r"\s*(>=|<=|==|=|<|>|!=)\s*([^\s]+)", part)
            op = match.group(1)
            ver = match.group(2)
            ver_tuple = _parse_version(ver)
            if not ver_tuple:
                raise ValueError("invalid version {}".format(ver))
            reqs.append((op, ver_tuple))
        return reqs
    except Exception as e:
        raise ValueError("invalid version requirement '{}' {}".format(val, e))

def _compare_version(op, ver, req):
    def _cmp(a, b):
        return (a > b) - (a < b) 
    major = _cmp(ver[0], req[0])
    minor = _cmp(ver[1], req[1])
    patch = None
    if req[2] is not None:
        patch = _cmp(ver[2] or 0, req[2])
    result = {
        ">=": major > 0 or (major == 0 and (minor > 0 or patch is None or patch >= 0)),
        "<=": major < 0 or (major == 0 and (minor < 0 or patch is None or patch <= 0)),
        ">": major > 0 or (major == 0 and (minor > 0 or patch is not None and patch > 0)),
        "<": major < 0 or (major == 0 and (minor < 0 or patch is not None and patch < 0)),
        "=": major == 0 and minor == 0 and (patch is None or patch == 0),
        "==": major == 0 and minor == 0 and (patch is None or patch == 0),
        "!=": major != 0 or minor != 0 or (patch is not None and patch != 0),
    }.get(op)
    return result

def _version_satisfied(version, requirements):
    version = _parse_version(version)
    requirements = _parse_version_requirements(requirements)
    for req in requirements:
        if not _compare_version(req[0], version, req[1]):
            return False
    return True

def _simulate_fail_json(msg, **kwargs):
    # this is run while module.fail_json() is not available yet
    # fake it as closely as possible

    kwargs['failed'] = True
    kwargs['msg'] = msg

    print('\n{}'.format(json.dumps(kwargs)))
    sys.exit(1)

# poor helper to work around the fact Ansible is unable to manage python dependencies
def require_import(module, package=None, version_requirements=None):
    try:
        importlib.import_module(module)
    except ImportError:
        _simulate_fail_json("Error: Python package '{}' required and missing".format(module))

    if package and version_requirements:
        version = importlib.metadata.version(package)
        # silently ignore version checks and hope for the best if we can't fetch
        # package version since we don't know how the user installs packages
        if version and not _version_satisfied(version, version_requirements):
            _simulate_fail_json("Error: Python package '{}' version '{}' does not satisfy requirements '{}'".format(module, version, version_requirements))

# this actually validates required dependencies right here so we don't have to do it in modules
# as the dependencies are known and static
for (module, package, requirements) in DEPENDENCIES:
    require_import(module, package, requirements)