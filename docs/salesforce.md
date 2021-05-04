# Using Snowfakery with Salesforce

Snowfakery recipes that generate Salesforce records are just like any
other Snowfakery recipes. You use SObject names for the 'objects'.
There are several examples [in the Snowfakery repository](https://github.com/SFDO-Tooling/Snowfakery/tree/main/examples/salesforce)

## Using Snowfakery within CumulusCI

The process of actually generating the data into a Salesforce
org happens through CumulusCI.

[CumulusCI](http://www.github.com/SFDO-Tooling/CumulusCI) is a
tool and framework for building portable automation for
Salesforce projects. It is created by the same team that
creates Snowfakery.

The easiest way to learn about CumulusCI (and to learn how to
install it) is with its [Trailhead Trail](https://trailhead.salesforce.com/en/content/learn/trails/build-applications-with-cumulusci).

CumulusCI's documentation [describes](https://cumulusci.readthedocs.io/en/latest/data.html?highlight=snowfakery#generate-fake-data)
how to use it with Snowfakery. Here is a short example:

```s
$ cci task run generate_and_load_from_yaml -o generator_yaml examples/salesforce/Contact.recipe.yml -o num_records 300 -o num_records_tablename Contact --org qa
...
```

You can (and more often will) use generate_and_load_from_yaml from
within a flow captured in in a `cumulusci.yml`.

If you have CumulusCI configured and you would like to test this,
you can do so by running some tests that are in the Snowfakery
repo itself.

The Snowfakery repo itself has a `cumulusci.yml` so it is a
CumulusCI project. You can learn how to set up your own
CumulusCI project by [studying it](https://github.com/SFDO-Tooling/Snowfakery/tree/main/cumulusci.yml)

```s

# clone the repo
$ git clone https://github.com/SFDO-Tooling/Snowfakery.git
# change working directory
$ cd Snowfakery
# run a specific test task
$ cci task run generate_opportunities_and_contacts
# run all of the test tasks and flows
$ cci flow run test_everything
...
```

## Record Types

To specify a Record Type for a record, just put the Record Type’s API Name in a field named RecordType.

```yaml
# tests/cci/record_types.yml
- object: Account
  fields:
    name: Bluth Family
    RecordType: HH_Account
- object: Account
  fields:
    name: Bluth Corporation
    RecordType: Organization
- object: Account
  fields:
    name: The Windors
    RecordType: HH_Account
- object: Account
  fields:
    name: The Firm
    RecordType: Organization
```

## Creating and Referencing Person Accounts

There are several features planned for the Salesforce Plugin, but
the first is support for Person Accounts.

You can use Person Accounts like this:

```yaml
- plugin: snowfakery.standard_plugins.Salesforce
- object: Account
  fields:
    FirstName:
      fake: first_name
    LastName:
      fake: last_name
    PersonMailingStreet:
      fake: street_address
    PersonMailingCity:
      fake: city
    PersonContactId:
      Salesforce.SpecialObject: PersonContact
```

This will generate a placeholder object in your recipe which can
be referred to by other templates like so:

```yaml
- object: User
  fields:
    Username:
      fake: email
    ...
    ContactId:
      reference: Account.PersonContactId
```

CumulusCI will fix up the references during data load. If you run into
errors, please verify that the Account object is being loaded before
the others that refer to the PersonContactId. If not, you may need to
write a [CumulusCI '.load.yml'](https://cumulusci.readthedocs.io/en/latest/data.html#controlling-the-loading-process) to ensure that it does.

The `Salesforce.SpecialObject` function cannot currently be used for any other
SObject or in any other context. It must always generate a `PersonContact`
in the `PersonContactId` field.

There is also an alternate syntax which allows nicknaming:

```yaml
...
- object: Account
  fields:
    PersonContactId:
      Salesforce.SpecialObject:
        name: PersonContact
        nickname: PCPC
- object: User
  fields:
    ContactId:
      reference: PCPC
```

## ContentVersions

Files can be used as Salesforce ContentVersions like this:

```yaml
- plugin: snowfakery.standard_plugins.base64.Base64
- plugin: snowfakery.standard_plugins.file.File
- object: Account
  nickname: FileOwner
  fields:
    Name:
      fake: company
- object: ContentVersion
  nickname: FileAttachment
  fields:
    Title: Attachment for ${{Account.Name}}
    PathOnClient: example.pdf
    Description: example.pdf
    VersionData:
      Base64.encode:
        - File.file_data:
            encoding: binary
            file: ${{PathOnClient}}
    FirstPublishLocationId:
      reference: Account
```
