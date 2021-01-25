try:
    from cumulusci.tests.pytest_plugins.pytest_sf_orgconnect import (
        pytest_addoption,
        sf_pytest_orgname,
        org_config,
        runtime,
    )

except ImportError:
    print("Salesforce features will not be tested")

    def sf_pytest_orgname(request):
        return "OFFLINE_NO_ORG"

    pytest_addoption = None
    org_config = None
    runtime = None

__all__ = [
    "pytest_addoption",
    "sf_pytest_orgname",
    "org_config",
    "runtime",
]
