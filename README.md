# Snowfakery Documentation

Snowfakery is a tool for generating fake data that has relations between tables. Every row is faked data, but also unique and random, like a snowflake. 

To tell Snowfakery what data you want to generate, you need to write a Factory file in YAML.

Snowfakery can write its output to stdout, or any database accessible to SQLAlchemy. **When it is embedded in CumulusCI it can output to a Salesforce org**. Adding new output formats is fairly straightforward and open source contributions of that form are gratefully accepted.

For the time being, Snowfakery's documentation is in a collaboration tool called Quip, to simplify reviewing in context with
pictures, tables, links etc. It will move to Sphinx and readthedocs at some point.

For now: https://salesforce.quip.com/AXY5A4WGTbNP
