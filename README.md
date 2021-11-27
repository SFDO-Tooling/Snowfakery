[![Coverage Status](https://coveralls.io/repos/github/SFDO-Tooling/Snowfakery/badge.svg?branch=master)](https://coveralls.io/github/SFDO-Tooling/Snowfakery?branch=master)

# Snowfakery Documentation

Snowfakery is a tool for generating fake data that has relations between tables. Every row is faked data, but also unique and random, like a snowflake.

To tell Snowfakery what data you want to generate, you need to write a Recipe file in YAML.

Snowfakery can write its output to stdout, or any database accessible to SQLAlchemy. **When it is embedded in CumulusCI it can output to a Salesforce org**. Adding new output formats is fairly straightforward and open source contributions of that form are gratefully accepted.

[Documentation](https://snowfakery.readthedocs.io)

## Contributing

To contribute to snowfakery you will first need to setup a [virtual environment](https://docs.python.org/3/tutorial/venv.html).
Once you have youre virtual environment, you can install dependencies via pip:

`pip install -r requirements_dev.txt`

Or you can install dependencies via pip tools:

```python
make dev-install
```

Now you're all set for contributing to Snowfakery!

### Updating Dependencies

Performing dependency updates is easy. Just run `make update-deps` and commit any changes to `requirements/prod.txt` and `requirements/dev.txt`.
