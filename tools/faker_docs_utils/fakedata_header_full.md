# Fake data

##### Overview

Fake data comes in a few different flavours. Let's start with the
most common pattern:

```yaml
# examples/salesforce/simple_account.recipe.yml
- object: Account
  fields:
    Name:
      fake: Company
    Description:
      fake: CatchPhrase
    BillingStreet:
      fake: StreetAddress
    BillingCity:
      fake: City
    BillingState:
      fake: State
    BillingPostalCode:
      fake: PostalCode
    BillingCountry:
      fake: CurrentCountry
    Phone:
      fake: PhoneNumber
```

So the first obvious question is where you find these names. The answer
is you can scroll down on this page to see a long list with descriptions.

The description above might generate output like this:

```json
Account(id=1, Name=Nelson-Deleon, Description=Secured bandwidth-monitored moratorium, BillingStreet=2187 Kerry Way, BillingCity=Rangelland, BillingState=Colorado, BillingPostalCode=08388, BillingCountry=United States, Phone=001-738-530-9719)
```

It doesn't matter if you use upper or lower case for fake names.

##### Formulas

Sometimes you might want to combine the fake data with other data
in a single field. You can use formula syntaax for this.

```yaml
# examples/faker_in_formula.recipe.yml
- object: Account
  fields:
    Name: ${{fake.State}} State University
```

Some complex faker definitions can also use parameters. The
documentation says what parameters are allowed. The docs
for [fake: sentence](#fake-sentence) define `nb_words` and
`variable_nb_words`, for example.

```yaml
# examples/parameters.recipe.yml
- object: Example
  fields:
    gibberish_words: ${{fake.Sentence(nb_words=10, variable_nb_words=False)}}
```

##### Block fakers with parameters

If you'd rather not use the formula syntax (${{ blah }}) there is also
a nested syntax for that:

```yaml
# examples/parameters_block.recipe.yml
- object: Example
  fields:
    gibberish_words:
      fake.Sentence:
        nb_words: 10
        variable_nb_words: False
```

##### Localization

Our fake data can be localized to many languages. We have
[detailed docs](https://snowfakery.readthedocs.io/en/feature-fake-data-docs/locales.html)
about how to use fake data in each of the other languages.

Let's say that you want to generate fake data for France instead of the
United States.

You do so by setting the special `snowfakery_locale` "variable" like this.

```yaml
# examples/salesforce/simple_account_french.recipe.yml

- var: snowfakery_locale
  value: fr_FR
- object: Account
  fields:
    Name:
      fake: Company
    Description:
      fake: CatchPhrase
    BillingStreet:
      fake: StreetAddress
    BillingCity:
      fake: City
    BillingState:
      fake: State
    BillingPostalCode:
      fake: PostalCode
    BillingCountry:
      fake: CurrentCountry
    Phone:
      fake: PhoneNumber
```

This will translate the State to the appropriate administrative unit in
France. `CurrentCountry` will be France, not `United States`. The Catch
Phrase will be in French and so forth.

For example:

```json
Account(id=1, Name=Parent Auger S.A.S., Description=Le confort de rouler de manière sûre, BillingStreet=54, rue de Bailly, BillingCity=Charrier, BillingState=Île-de-France, BillingPostalCode=72902, BillingCountry=France, Phone=08 05 11 90 19)
```

We can do many countries. For example, Japanese (ja_JP locale):

```json
Account(id=1, Name=有限会社山下電気, Description=Inverse 24hour pricing structure, BillingStreet=040 佐々木 Street, BillingCity=横浜市金沢区, BillingState=福岡県, BillingPostalCode=181-5538, BillingCountry=Japan, Phone=070-4156-5072)
```

We can even pick the locale randomly:

```yaml
# examples/salesforce/simple_account_random.recipe.yml
- var: snowfakery_locale
  value:
    random_choice:
      - ja_JP # Japanese
      - en_CA # Canadian English
      - fr_FR # French from France
      - fr_CA # Canadian Frencch
      - de_DE # German from Germany
- object: Account
  fields:
    Name:
      fake: Company
    Description:
      fake: CatchPhrase
    BillingStreet:
      fake: StreetAddress
    BillingCity:
      fake: City
    BillingState:
      fake: State
    BillingPostalCode:
      fake: PostalCode
    BillingCountry:
      fake: CurrentCountry
    Phone:
      fake: PhoneNumber
```

##### Fake Dates and Numbers

The main Snowfakery documentation describes how to fake
[dates](index.md#date-between) and [numbers](index.md#random-number).

That's it. Those are all of the concepts you need.

##### Custom Faker Providers

You can also include Faker extension libraries ("Providers") after
you’ve added them to your Python install:

```yaml
 - plugin: faker_microservice.Provider
 - object: OBJ
    fields:
    service_name:
        fake:
            microservice
```

You would install that provider like this:

```s
$ pip install faker_microservice
```

Here are some Python Faker providers:

<https://faker.readthedocs.io/en/master/communityproviders.html>

And you could make your own providers as well. Aaron Crossman
has written [a tutorial](https://spinningcode.org/2021/06/snowfakery-custom-plugins-part-2/)
about that process.

## Index of Fake Datatypes
