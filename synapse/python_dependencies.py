# Copyright 2015, 2016 OpenMarket Ltd
# Copyright 2017 Vector Creations Ltd
# Copyright 2018 New Vector Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from distutils.version import LooseVersion

logger = logging.getLogger(__name__)

# this dict maps from python package name to a list of modules we expect it to
# provide.
#
# the key is a "requirement specifier", as used as a parameter to `pip
# install`[1], or an `install_requires` argument to `setuptools.setup` [2].
#
# the value is a sequence of strings; each entry should be the name of the
# python module, optionally followed by a version assertion which can be either
# ">=<ver>" or "==<ver>".
#
# [1] https://pip.pypa.io/en/stable/reference/pip_install/#requirement-specifiers.
# [2] https://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-dependencies
REQUIREMENTS = {
    "jsonschema>=2.5.1": ["jsonschema>=2.5.1"],
    "frozendict>=0.4": ["frozendict"],
    "unpaddedbase64>=1.1.0": ["unpaddedbase64>=1.1.0"],
    "canonicaljson>=1.1.3": ["canonicaljson>=1.1.3"],
    "signedjson>=1.0.0": ["signedjson>=1.0.0"],
    "pynacl>=1.2.1": ["nacl>=1.2.1", "nacl.bindings"],
    "service_identity>=1.0.0": ["service_identity>=1.0.0"],
    "Twisted>=16.0.0": ["twisted>=16.0.0"],

    # We use crypto.get_elliptic_curve which is only supported in >=0.15
    "pyopenssl>=0.15": ["OpenSSL>=0.15"],

    "pyyaml": ["yaml"],
    "pyasn1": ["pyasn1"],
    "daemonize": ["daemonize"],
    "bcrypt": ["bcrypt>=3.1.0"],
    "pillow": ["PIL"],
    "pydenticon": ["pydenticon"],
    "blist": ["blist"],
    "pysaml2>=3.0.0": ["saml2>=3.0.0"],
    "pymacaroons-pynacl": ["pymacaroons"],
    "msgpack-python>=0.3.0": ["msgpack"],
    "phonenumbers>=8.2.0": ["phonenumbers"],
    "six": ["six"],
    "prometheus_client": ["prometheus_client"],
}
CONDITIONAL_REQUIREMENTS = {
    "web_client": {
        "matrix_angular_sdk>=0.6.8": ["syweb>=0.6.8"],
    },
    "preview_url": {
        "netaddr>=0.7.18": ["netaddr"],
    },
    "email.enable_notifs": {
        "Jinja2>=2.8": ["Jinja2>=2.8"],
        "bleach>=1.4.2": ["bleach>=1.4.2"],
    },
    "matrix-synapse-ldap3": {
        "matrix-synapse-ldap3>=0.1": ["ldap_auth_provider"],
    },
    "psutil": {
        "psutil>=2.0.0": ["psutil>=2.0.0"],
    },
    "affinity": {
        "affinity": ["affinity"],
    },
}


def requirements(config=None, include_conditional=False):
    reqs = REQUIREMENTS.copy()
    if include_conditional:
        for _, req in CONDITIONAL_REQUIREMENTS.items():
            reqs.update(req)
    return reqs


def github_link(project, version, egg):
    return "https://github.com/%s/tarball/%s/#egg=%s" % (project, version, egg)


DEPENDENCY_LINKS = {
}


class MissingRequirementError(Exception):
    def __init__(self, message, module_name, dependency):
        super(MissingRequirementError, self).__init__(message)
        self.module_name = module_name
        self.dependency = dependency


def check_requirements(config=None):
    """Checks that all the modules needed by synapse have been correctly
    installed and are at the correct version"""
    for dependency, module_requirements in (
            requirements(config, include_conditional=False).items()):
        for module_requirement in module_requirements:
            if ">=" in module_requirement:
                module_name, required_version = module_requirement.split(">=")
                version_test = ">="
            elif "==" in module_requirement:
                module_name, required_version = module_requirement.split("==")
                version_test = "=="
            else:
                module_name = module_requirement
                version_test = None

            try:
                module = __import__(module_name)
            except ImportError:
                logging.exception(
                    "Can't import %r which is part of %r",
                    module_name, dependency
                )
                raise MissingRequirementError(
                    "Can't import %r which is part of %r"
                    % (module_name, dependency), module_name, dependency
                )
            version = getattr(module, "__version__", None)
            file_path = getattr(module, "__file__", None)
            logger.info(
                "Using %r version %r from %r to satisfy %r",
                module_name, version, file_path, dependency
            )

            if version_test == ">=":
                if version is None:
                    raise MissingRequirementError(
                        "Version of %r isn't set as __version__ of module %r"
                        % (dependency, module_name), module_name, dependency
                    )
                if LooseVersion(version) < LooseVersion(required_version):
                    raise MissingRequirementError(
                        "Version of %r in %r is too old. %r < %r"
                        % (dependency, file_path, version, required_version),
                        module_name, dependency
                    )
            elif version_test == "==":
                if version is None:
                    raise MissingRequirementError(
                        "Version of %r isn't set as __version__ of module %r"
                        % (dependency, module_name), module_name, dependency
                    )
                if LooseVersion(version) != LooseVersion(required_version):
                    raise MissingRequirementError(
                        "Unexpected version of %r in %r. %r != %r"
                        % (dependency, file_path, version, required_version),
                        module_name, dependency
                    )


def list_requirements():
    result = []
    linked = []
    for link in DEPENDENCY_LINKS.values():
        egg = link.split("#egg=")[1]
        linked.append(egg.split('-')[0])
        result.append(link)
    for requirement in requirements(include_conditional=True):
        is_linked = False
        for link in linked:
            if requirement.replace('-', '_').startswith(link):
                is_linked = True
        if not is_linked:
            result.append(requirement)
    return result


if __name__ == "__main__":
    import sys
    sys.stdout.writelines(req + "\n" for req in list_requirements())
