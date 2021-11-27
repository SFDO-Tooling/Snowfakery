import re
import pkg_resources
import requests
import typing as T


from json import JSONDecodeError

# This code is adapted from cumulusci/cli/utils.py
FINAL_VERSION_RE = re.compile(r"^[\d\.]+$")


def is_final_release(version: str) -> bool:
    """Returns bool whether version string should be considered a final release.

    Snowfakery versions are considered final if they contain only digits and periods.
    e.g. 1.0.1 is final but 2.0b1 and 2.0.dev0 are not.
    """
    return bool(FINAL_VERSION_RE.match(version))


def get_latest_final_version():
    """return the latest version of snowfakery in pypi, be defensive"""
    # use the pypi json api https://wiki.python.org/moin/PyPIJSON
    res = safe_json_from_response(
        requests.get("https://pypi.org/pypi/snowfakery/json", timeout=5)
    )
    versions = []
    for versionstring in res["releases"].keys():
        if not is_final_release(versionstring):
            continue
        versions.append(pkg_resources.parse_version(versionstring))
    versions.sort(reverse=True)
    return versions[0]


class IsLatestVersion(T.NamedTuple):
    is_latest_version: T.Optional[bool]
    message: str


def check_latest_version(version: str) -> IsLatestVersion:
    """checks for the latest version of snowfakery from pypi.

    Returns bool, message.

    The bool is True if we have the latest version, False if not.
    None if error was detected."""
    try:
        latest_version = get_latest_final_version()
    except Exception as e:

        return IsLatestVersion(
            None, f"Error checking snowfakery version: {type(e)}: {e}"
        )

    obsolete = latest_version > get_installed_version(version)
    if obsolete:
        return IsLatestVersion(
            False, f"An update to Snowfakery is available: {latest_version}"
        )
    else:
        return IsLatestVersion(True, "You have the latest version of Snowfakery")


def get_installed_version(version):
    """returns the version name (e.g. 2.0.0b58) that is installed"""
    return pkg_resources.parse_version(version)


# from cumulusci/utils/http/requests_utils.py
def safe_json_from_response(response):
    "Check JSON response is HTTP200 and actually JSON."
    response.raise_for_status()

    try:
        return response.json()
    except JSONDecodeError:
        raise ValueError(f"Cannot decode as JSON:  {response.text}")
