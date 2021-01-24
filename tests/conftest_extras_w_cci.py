from unittest.mock import patch

import pytest

from cumulusci.tests.pytest_plugins.pytest_sf_vcr import (
    salesforce_vcr,  # noqa
    salesforce_matcher,  # noqa
)
from cumulusci.tests.util import DummyOrgConfig

DUMMY_ORGNAME = "pytest_sf_orgconnect_dummy_orgconfig"


@pytest.fixture(scope="session")
def fallback_orgconfig():
    def fallback_orgconfig():
        return DummyOrgConfig(
            {
                "instance_url": "https://orgname.salesforce.com",
                "access_token": "pytest_sf_orgconnect_abc123",
                "id": "ORGID/ORGID",
            },
            DUMMY_ORGNAME,
        )

    original_get_org = None

    def get_org(self, name: str):
        if name == DUMMY_ORGNAME:
            return DUMMY_ORGNAME, fallback_orgconfig()
        else:
            return original_get_org(self, name)

    p = patch(
        "cumulusci.cli.runtime.CliRuntime.get_org",
        get_org,
    )
    original_get_org = p.get_original()[0]
    with p:
        yield fallback_orgconfig


__all__ = ["salesforce_vcr", "salesforce_matcher", "fallback_orgconfig"]
