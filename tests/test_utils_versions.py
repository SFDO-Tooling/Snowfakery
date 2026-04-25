import inspect

from packaging.version import Version

from snowfakery.utils import versions


def test_versions_module_does_not_reference_pkg_resources():
    """Regression lint: pkg_resources is removed in setuptools>=81 (default on 3.14)."""
    src = inspect.getsource(versions)
    assert "pkg_resources" not in src, (
        "snowfakery.utils.versions must not use pkg_resources; "
        "use packaging.version.parse instead"
    )


def test_get_installed_version_returns_packaging_version():
    result = versions.get_installed_version("4.2.1")
    assert isinstance(result, Version)
    assert str(result) == "4.2.1"


def test_is_final_release_unchanged():
    assert versions.is_final_release("4.2.1") is True
    assert versions.is_final_release("4.2.1b1") is False
    assert versions.is_final_release("2.0.dev0") is False
