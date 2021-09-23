from unittest.mock import patch

import pytest
from pytest import fixture

from cumulusci.tests.pytest_plugins.pytest_sf_vcr import (
    vcr_config as cci_vcr_config,
    salesforce_vcr,
    simplify_body,
    vcr_state,
)

from cumulusci.tests.util import DummyOrgConfig, DummyKeychain
from cumulusci.core.exceptions import ServiceNotConfigured

DUMMY_ORGNAME = "pytest_sf_orgconnect_dummy_orgconfig"


@pytest.fixture(scope="session")
def fallback_org_config():
    def fallback_org_config():
        return DummyOrgConfig(
            {
                "instance_url": "https://orgname.my.salesforce.com",
                "access_token": "pytest_sf_orgconnect_abc123",
                "id": "ORGID/ORGID",
            },
            DUMMY_ORGNAME,
            keychain=DummyKeychain(),
        )

    original_get_org = original_load_keychain = None

    def get_org(self, name: str):
        if name == DUMMY_ORGNAME:
            return DUMMY_ORGNAME, fallback_org_config()
        else:
            return original_get_org(self, name)

    def _load_keychain(self):
        try:
            return original_load_keychain(self)
        except Exception:
            self.keychain = DummyKeychain()

            def no_services(*args, **kwargs):
                raise ServiceNotConfigured()

            self.keychain.get_service = no_services
            if self.project_config is not None:
                self.project_config.keychain = self.keychain

    p = patch(
        "cumulusci.cli.runtime.CliRuntime.get_org",
        get_org,
    )
    original_get_org = p.get_original()[0]
    p2 = patch(
        "cumulusci.cli.runtime.CliRuntime._load_keychain",
        _load_keychain,
    )
    original_load_keychain = p2.get_original()[0]
    with p, p2:
        yield fallback_org_config


# This should be the same as CCI and can be deleted
# when CCI is updated.
def sf_before_record_response(response):
    response["headers"] = {
        "Content-Type": response["headers"].get("Content-Type", "None"),
        "Others": "Elided",
    }
    if response.get("body"):
        response["body"]["string"] = simplify_body(response["body"]["string"])
    return response


# Snowfakery has a fix that CCI doesn't yet, so inject it.
def sf_vcr_config(request, vcr_config, user_requested_network_access, vcr_state):
    dct = cci_vcr_config(request, user_requested_network_access, vcr_state)
    dct["before_record_response"] = sf_before_record_response
    return dct


vcr_config = fixture(sf_vcr_config, scope="module")

# switch back to this after CCI has the appropriate
# sf_before_record_response
# vcr_config = fixture(cci_vcr_config, scope="module")
vcr = fixture(salesforce_vcr, scope="module")


__all__ = ["vcr_config", "vcr", "fallback_org_config", "vcr_state"]
