import setuptools
from snowfakery import version

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as requirements_file:
    requirements = [req.replace("==", ">=").strip() for req in requirements_file]

with open("requirements_dev.txt") as dev_requirements_file:
    test_requirements = [
        req for req in dev_requirements_file if not req.startswith("-")
    ]

setuptools.setup(
    name="snowfakery",  # Replace with your own username
    version=version.version,
    author="Paul Prescod",
    author_email="pprescod@salesforce.com",
    description=(
        "Snowfakery is a tool for generating fake data that has "
        "relations between tables. Every row is faked data, but also "
        "unique and random, like a snowflake."
    ),
    entry_points={"console_scripts": ["snowfakery=snowfakery.cli:main"]},
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SalesforceFoundation/Snowfakery",
    packages=setuptools.find_packages(),
    package_dir={"snowfakery": "snowfakery"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    tests_require=test_requirements,
)
