# Using Snowfakery with Salesforce

Snowfakery recipes that generate Salesforce records are just like any
other Snowfakery recipes. You use SObject names for the 'objects'.
There are several examples [in the Snowfakery repository](https://github.com/SFDO-Tooling/Snowfakery/tree/main/examples/salesforce)

## Using Snowfakery within CumulusCI

The process of actually generating the data into a Salesforce
org happens through CumulusCI. The majority of the documentation
on using Snowfakery with CumulusCI is in
[the Generate Data section of the CumulusCI documentation](https://cumulusci.readthedocs.io/en/latest/data.html?highlight=snowfakery#generate-fake-data).

A summarized overview follows.

[CumulusCI](http://www.github.com/SFDO-Tooling/CumulusCI) is a
tool and framework for building portable automation for
Salesforce projects. It is created by the same team that
creates Snowfakery.

The easiest way to learn about CumulusCI (and to learn how to
install it) is with its [Trailhead Trail](https://trailhead.salesforce.com/en/content/learn/trails/build-applications-with-cumulusci).


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

## Incorporating Information from Salesforce

There are various cases where it might be helpful to relate newly created synthetic
data to existing data in a Salesforce org. For example, that data might have
been added in a previous CumulusCI task or some other process.

For example, if you have a Campaign object and would like to associate
Contacts to it through CampaignMembers.

Here is an example where we query a particular Campaign object:

```yaml
# examples/salesforce/CampaignMembers-first.recipe.yml
- plugin: snowfakery.standard_plugins.Salesforce.SalesforceQuery

- object: Contact
  fields:
    FirstName: Bobby
    LastName: McFerrin
  friends:
    - object: CampaignMember
      fields:
        ContactId:
          reference: Contact
        CampaignId:
          SalesforceQuery.find_record:
            from: Campaign
            where: name='Our Campaign'
```

Perhaps you do not care which Campaign you connect to:

```yaml
# examples/salesforce/CampaignMembers-random.recipe.yml
- plugin: snowfakery.standard_plugins.Salesforce.SalesforceQuery

- object: Contact
  count: 10
  fields:
    FirstName:
      fake: FirstName
    LastName:
      fake: LastName
  friends:
    - object: CampaignMember
      fields:
        ContactId:
          reference: Contact
        CampaignId:
          SalesforceQuery.random_record:
            from: Campaign
```

As you can see, `find_record` looks for a particular record, and returns the first
one that Salesforce finds. `random_record` looks for an random record out of the
first 2000 Salesforce finds. The 2000-record scope limit is based on a Salesforce
limitation and future versions of Snowfakery may incorporate a workaround.

NOTE: The features we are discussing in this section are for linking to records
that are in the Salesforce org _before_ the recipe iteration started. These features
are not for linking to records created by the recipe itself.

Sometimes we want to do more than just link to the other record. For example,
perhaps we want to create Users for Contacts and have the Users have the same
name as the Contacts.

```yaml
# examples/salesforce/UsersForContacts.yml
- plugin: snowfakery.standard_plugins.Salesforce.SalesforceQuery
- plugin: snowfakery.standard_plugins.Salesforce

- object: User
  fields:
    __random_contact:
      SalesforceQuery.random_record:
        from: Contact
        fields: Id, FirstName, LastName

    FirstName: ${{__random_contact.FirstName}}
    LastName: ${{__random_contact.LastName}}
    Alias: Grace
    Username:
      fake: Username
    Email: ${{Username}}
    TimeZoneSidKey: America/Bogota
    LocaleSidKey: en_US
    EmailEncodingKey: UTF-8
    LanguageLocaleKey: en_US
    ProfileId:
      SalesforceQuery.find_record:
        from: Profile
        where: Name='Identity User'
    # ContactId: ${{__random_contact.Id}}
```

In this case, the actual connection between the contact and
the User is commented out because `Identity User` users cannot
have Contacts, but you can see how you would connect a
synthetic object to a pre-existing object, while also getting
access to other fields.

If you would like to use Salesforce query as a Dataset, that's
another way that you can ensure that every synthetic record you
create is associated with a distinct record from Salesforce.

```yaml
# examples/soql_dataset.recipe.yml
- plugin: snowfakery.standard_plugins.Salesforce.SOQLDataset
- object: Contact
  count: 10
  fields:
    __users_from_salesforce:
      SOQLDataset.iterate:
        fields: Id, FirstName, LastName
        from: User
    OwnerId: ${{__users_from_salesforce.Id}}
    FirstName: ${{__users_from_salesforce.FirstName}}
    LastName: ${{__users_from_salesforce.LastName}}
    Username: TestUser${{fake.Username}}
```

Or if you'd like them in a random order, you can
use `SOQLDataset.shuffle`:

```yaml
# examples/soql_dataset_shuffled.recipe.yml
- plugin: snowfakery.standard_plugins.Salesforce.SOQLDataset
- object: Contact
  count: 10
  fields:
    __users_from_salesforce:
      SOQLDataset.shuffle:
        fields: Id, FirstName, LastName
        from: User
    # The next line depends on the users having particular
    # permissions.
    OwnerId: ${{__users_from_salesforce.Id}}
    FirstName: ${{__users_from_salesforce.FirstName}}
    LastName: ${{__users_from_salesforce.LastName}}
    Username: TestUser${{fake.Username}}
```

You may also specify a "where" clause to filter out irrelevant records:

```yaml
# examples/soql_dataset_where.recipe.yml
- plugin: snowfakery.standard_plugins.Salesforce.SOQLDataset
- object: Contact
  count: 10
  fields:
    __users_from_salesforce:
      SOQLDataset.shuffle:
        fields: Id, FirstName, LastName
        from: User
        where: FirstName Like 'A%'
    OwnerId: ${{__users_from_salesforce.Id}}
    FirstName: ${{__users_from_salesforce.FirstName}}
    LastName: ${{__users_from_salesforce.LastName}}
```

### Testing Queries

In general, you can test Snowfakery files outside of CumulusCI to see if they work:

```s
$ snowfakery recipe.yml
```

If you have a recipe which depends on data from an org,
specify the CumulusCI org name like this:

```s
$ snowfakery recipe.yml --plugin-options org_name qa
```

When you run the recipe in this way, it will connect to the org to pull data but
not change data in the org at all.

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

## Profiles

The `Salesforce.ProfileId` function looks up a Profile in
Salesforce by name and substitutes the ID.

```yaml
- plugin: snowfakery.standard_plugins.Salesforce
- object: User
  fields:
    Alias: Grace
    Username:
      fake: Username
    LastName: Wong
    Email: ${{Username}}
    TimeZoneSidKey: America/Bogota
    LocaleSidKey: en_US
    EmailEncodingKey: UTF-8
    LanguageLocaleKey: en_US
    ProfileId:
      Salesforce.ProfileId: Identity User
```

## Creating and Referencing Person Accounts

There are several features planned for the Salesforce Plugin, but
the one supported currently is for Person Accounts.

You can use Person Accounts like this:

```yaml
- plugin: snowfakery.standard_plugins.Salesforce
- object: Account
  fields:
    FirstName:
      fake: FirstName
    LastName:
      fake: LastName
    PersonMailingStreet:
      fake: StreetAddress
    PersonMailingCity:
      fake: City
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
