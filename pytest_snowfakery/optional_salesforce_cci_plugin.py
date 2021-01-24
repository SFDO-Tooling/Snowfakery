from pytest import fixture


try:
    from cumulusci.tests.pytest_plugins.pytest_sf_orgconnect import (
        pytest_addoption,
        sf_pytest_orgname,
        org_config,
        runtime,
    )

except ImportError:
    print("Salesforce features will not be tested")
    pytest_sf_orgconnect = None

    def sf_pytest_orgname(request):
        return "OFFLINE_NO_ORG"


@fixture(scope="session")
def orgname(request):
    return sf_pytest_orgname(request) or "orgname"


__all__ = [
    "pytest_addoption",
    "sf_pytest_orgname",
    "org_config",
    "runtime",
]
