# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Simon Dodsley <simon@purestorage.com>,2021
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    import fusion
except ImportError:
    pass

from os import environ
import platform

TOKEN_EXCHANGE_URL = "https://api.pure1.purestorage.com/oauth2/1.0/token"
VERSION = 1.0
USER_AGENT_BASE = "Ansible"

PARAM_ISSUER_ID = "issuer_id"
PARAM_PRIVATE_KEY_FILE = "private_key_file"
ENV_ISSUER_ID = "FUSION_ISSUER_ID"
ENV_API_HOST = "FUSION_API_HOST"
ENV_PRIVATE_KEY_FILE = "FUSION_PRIVATE_KEY_FILE"
ENV_TOKEN_ENDPOINT = "FUSION_TOKEN_ENDPOINT"

# will be deprecated in 2.0.0
PARAM_APP_ID = "app_id"  # replaced by PARAM_ISSUER_ID
PARAM_KEY_FILE = "key_file"  # replaced by PARAM_PRIVATE_KEY_FILE
ENV_APP_ID = "FUSION_APP_ID"  # replaced by ENV_ISSUER_ID
ENV_HOST = "FUSION_HOST"  # replaced by ENV_API_HOST
DEP_VER = "2.0.0"


def _env_deprecation_warning(module, old_env, new_env, vers):
    if old_env in environ:
        if new_env in environ:
            module.warn(
                f"{old_env} env variable is ignored because {new_env} is specified."
                f" {old_env} env variable is deprecated and will be removed in version {vers}"
                f" Please use {new_env} env variable only."
            )
        else:
            module.warn(
                f"{old_env} env variable is deprecated and will be removed in version {vers}"
                f" Please use {new_env} env variable instead."
            )


def _param_deprecation_warning(module, old_param, new_param, vers):
    if old_param in module.params:
        module.warn(
            f"{old_param} parameter is deprecated and will be removed in version {vers}"
            f" Please use {new_param} parameter instead."
            f" Don't use both parameters simultaneously."
        )


def get_fusion(module):
    """Return System Object or Fail"""
    # deprecation warnings
    _param_deprecation_warning(module, PARAM_APP_ID, PARAM_ISSUER_ID, DEP_VER)
    _param_deprecation_warning(module, PARAM_KEY_FILE, PARAM_PRIVATE_KEY_FILE, DEP_VER)
    _env_deprecation_warning(module, ENV_APP_ID, ENV_ISSUER_ID, DEP_VER)
    _env_deprecation_warning(module, ENV_HOST, ENV_API_HOST, DEP_VER)

    user_agent = "%(base)s %(class)s/%(version)s (%(platform)s)" % {
        "base": USER_AGENT_BASE,
        "class": __name__,
        "version": VERSION,
        "platform": platform.platform(),
    }

    issuer_id = module.params[PARAM_ISSUER_ID]
    key_file = module.params[PARAM_PRIVATE_KEY_FILE]

    config = fusion.Configuration()
    config.host = environ.get(ENV_API_HOST, environ.get(ENV_HOST, config.host))
    config.token_endpoint = environ.get(ENV_TOKEN_ENDPOINT, config.token_endpoint)

    if issuer_id is not None and key_file is not None:
        try:
            config.issuer_id = issuer_id
            config.private_key_file = key_file
            client = fusion.ApiClient(config)
            client.set_default_header("User-Agent", user_agent)
        except Exception:
            module.fail_json(msg="Unknown failure. Please contact Pure Support")
    elif (
        ENV_ISSUER_ID in environ or ENV_APP_ID in environ
    ) and ENV_PRIVATE_KEY_FILE in environ:
        try:
            config.issuer_id = environ.get(ENV_ISSUER_ID, environ.get(ENV_APP_ID))
            config.private_key_file = environ.get(ENV_PRIVATE_KEY_FILE)
            client = fusion.ApiClient(config)
            client.set_default_header("User-Agent", user_agent)
        except Exception:
            module.fail_json(msg="Unknown failure. Please contact Pure Support")
    else:
        module.fail_json(
            msg=f"You must set {ENV_ISSUER_ID} and f{ENV_PRIVATE_KEY_FILE} environment variables "
            f"or the {PARAM_ISSUER_ID} and f{PARAM_PRIVATE_KEY_FILE} module arguments"
        )
    try:
        api_instance = fusion.DefaultApi(client)
        api_instance.get_version()
    except Exception as err:
        module.fail_json(msg="Fusion authentication failed: {0}".format(err))
    return client


def fusion_argument_spec():
    """Return standard base dictionary used for the argument_spec argument in AnsibleModule"""

    return dict(
        issuer_id=dict(
            no_log=True,
            aliases=[PARAM_APP_ID],
            deprecated_aliases=[
                dict(
                    name=PARAM_APP_ID,
                    version=DEP_VER,
                    collection_name="purefusion.fusion",
                )
            ],
        ),
        private_key_file=dict(
            no_log=False,
            aliases=[PARAM_KEY_FILE],
            deprecated_aliases=[
                dict(
                    name=PARAM_KEY_FILE,
                    version=DEP_VER,
                    collection_name="purefusion.fusion",
                )
            ],
        ),
    )
