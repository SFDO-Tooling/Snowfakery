from warnings import warn

from pytest import fixture


try:
    from cumulusci.tests.pytest_plugins.pytest_sf_orgconnect import (
        pytest_addoption,
        sf_pytest_cli_orgname,
        org_config,
        sf,
        project_config,
        user_requested_network_access,
        current_org_shape,
        cli_org_config,
    )
    from cumulusci.cli.runtime import CliRuntime
    from cumulusci.core.runtime import BaseCumulusCI

except ImportError as e:
    if "No module named 'cumulusci'" not in str(e):
        raise

    warn("Cannot import CumulusCI. Skipping some tests.")
    pytest_sf_orgconnect = None

    def sf_pytest_cli_orgname(request):
        return "OFFLINE_NO_ORG"


@fixture(scope="session")
def orgname(request):
    return sf_pytest_cli_orgname(request) or "orgname"


@fixture(scope="session")
def runtime(request):
    """Get the CumulusCI runtime for the current working directory."""

    # if there is a real orgname, use a real CliRuntime
    # to get access to it
    if sf_pytest_cli_orgname(request):
        return CliRuntime()
    else:
        return BaseCumulusCI()


__all__ = [
    "pytest_addoption",
    "sf_pytest_cli_orgname",
    "org_config",
    "runtime",
    "sf",
    "project_config",
    "user_requested_network_access",
    "current_org_shape",
    "cli_org_config",
]
