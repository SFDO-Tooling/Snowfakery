import re
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements/prod.txt") as requirements_file:
    requirements = []
    for req in requirements_file.read().splitlines():
        # skip comments and hash lines
        if re.match(r"\s*#", req) or re.match(r"\s*--hash", req):
            continue
        else:
            req = req.split(" ")[0]
            requirements.append(req)

with open("requirements/dev.txt") as dev_requirements_file:
    dev_requirements = []
    for req in dev_requirements_file.read().splitlines():
        # skip comments and hash lines
        if re.match(r"\s*#", req) or re.match(r"\s*--hash", req):
            continue
        else:
            req = req.split(" ")[0]
            dev_requirements.append(req)

# get the version into a global variable named "version"
with open("snowfakery/version.txt") as f:
    version = f.read().strip()

packages = [
    p
    for p in setuptools.find_namespace_packages()
    if p.startswith("snowfakery") and not p.startswith("snowfakery.docs")
]

setuptools.setup(
    name="snowfakery",
    version=version,
    author="Paul Prescod",
    author_email="pprescod@salesforce.com",
    description=(
        "Snowfakery is a tool for generating fake data that has "
        "relations between tables. Every row is faked data, but also "
        "unique and random, like a snowflake."
    ),
    entry_points={
        "console_scripts": [
            "snowfakery=snowfakery.cli:main",
            "snowbench=snowfakery.tools.snowbench:main",
        ]
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SFDO-Tooling/Snowfakery",
    packages=packages,
    package_dir={"snowfakery": "snowfakery"},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    tests_require=dev_requirements,
    data_files=[("requirements", ["requirements/prod.txt", "requirements/dev.txt"])],
)
