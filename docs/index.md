# Snowfakery Documentation

Snowfakery is a tool for generating fake data that has relations between tables. Every row is faked data, but also unique and random, like a snowflake.

To tell Snowfakery what data you want to generate, you need to write a Recipe file in YAML.

Snowfakery can write its output to stdout, or any database accessible to SQLAlchemy. **When it is embedded in CumulusCI it can output to a Salesforce org**. Adding new output formats is a fairly straightforward process.

## Installation

Please start by installing Python. Whether or not you are installing CumulusCI, you can install Python by using the instructions from the [CumulusCI site](https://cumulusci.readthedocs.io/en/latest/install.html).

But while you’re at it, why not install CumulusCI too?

Next, you can go to a terminal and install Snowfakery:

```bash
$ pip3 install pipx
...
$ pipx install snowfakery
...
```

If you want to use Snowfakery within CumulusCI, you can find instructions for that in [Using Snowfakery within CumulusCI](#using-snowfakery-within-cumulusci).

After installation, you should be able to invoke Snowfakery like this:

```bash
$ snowfakery somefile.yml
...
```

## Central Concepts

Snowfakery recipes are specified in a YAML format. YAML is a relatively simple, human-readable format. You can learn more about it at [yaml.org](http://yaml.org/). But you can also just pick up the basics of it by reading along with the examples below.

YAML uses indentation to say which parts of the file are related to each other. Let’s get started with a stupidly simple example recipe:

simple_static.yml

```yaml
- object: Person
  fields:
    name: Buster Bluth
    age: 35
```

We run this example through Snowfakery like this:

```bash
$ snowfakery docs/examples/simple_static.yml
...
```

(this example does not represent the final command line interface nor how to use [Advanced Features](#advanced-features)))

This simple example will generate a single record that looks like this:

```json
Person(id=1, name=Buster Bluth, age=35)
```

In other words, it is a person record with 3 fields:

|Field    |id   |name         |age|
|---      |---  |---          |---|
|Value    |1    |Buster Bluth |35 |

Two of the fields include data from the YAML file. The ID is auto-generated.

**Note:** Snowfakery only works for models which are amenable to having an id column on every record. Your tools can use the column, ignore the column, or exchange it for another kind of ID (as CumulusCI does, with Salesforce) but Snowfakery always generates IDs and refers between tables with IDs. Future versions might include a command line option to turn this behaviour on or off.

Let’s make this example more interesting:

persons_of_interest.yml

```yaml
- object: Person
  count: 3
  fields:
      name:
        fake: name
      age:
        random_number:
          min: 12
          max: 95
```

What did we say here?

- object: Person : This is a template for rows that will go in the Person table representing real-world “Person” objects
- count: we want 3 records instead of just 1
- name: fake: name : we want to fake the name instead of hard coding it. The list of things you can “fake” is based on a library called “Faker” which we will discuss later.
- age: random_number: we want a random number between the min and max

Now you should get an output more like this:

```json
Person(id=1, name=Allison Garcia, age=94)
Person(id=2, name=Megan Campos, age=67)
Person(id=3, name=Katherine Nelson, age=92)
```

We have created people! Or at least fake personas for people! And every time you run it, you will get a different set of “people”.

So that’s pretty cool, but it doesn’t use much of Snowfakery’s power. Let's go deeper.

pet_stories.yml

```yaml
- object: Person
  count: 3
  fields:
    name:
      fake: name
    age:
      random_number:
        min: 12
        max: 95
    dog:
      - object: Animal
        fields:
          name:
            fake: first_name
          species: canine
          food:
            - object: PetFood
              fields:
                name: Pets Choice
                cost: $10

        cat:
          - object: Animal
            fields:
              name:
                fake: first_name
              species: feline
              food:
                - object: PetFood
                  fields:
                    name: Pets Choice
                    cost: $1
```

If you’re lost: don't worry! Those are a lot of new concepts at once, and you don't have to understand everything in this example right now. We'll come back to these concepts one by one.

But in case you’re in a hurry: In this case we're creating 3 Person objects. Each one has a name, age, dog and cat. Each dog or cat is an Animal, so we'll get 2 animals per Person or a total of 6. Each animal has a favorite food, so we'll get 6 PetFood objects as well.

<img src='images/img1.png' id='PJUACATPCzI' alt='Relationship diagram' width='800' height='190'>Later, we’ll discuss how we could have just 2 PetFood objects which are shared. We’ll also discuss how we could randomly select a Pet species or Food.

## Outputs

Snowfakery builds on a tool called SQLAlchemy, so it gets a variety of database connectors for free:

<https://docs.sqlalchemy.org/en/13/dialects/index.html>

When integrated with CumulusCI (see [Advanced Features](#advanced-features)) it is possible to output to a Salesforce instance.

Snowfakery can also output JSON, directories of CSV and object diagrams.

CSV output goes to a directory with one CSV file per table and a JSON manifest file in the [csvw](https://www.w3.org/TR/tabular-data-primer/) format.

## Objects

The main, core concept in the language is an “*Object Template*”. It basically represents instructions on how to create a *Row* (or multiple rows) in a database. Rows in turn represent real-world entities like People,  Places or Things and that’s why we use the keyword “Object”.

 Each *Row* has a type, which represents — for example — the name of the table it goes in if it is headed for a relational database, or which CSV file it goes in it if it is destined to be output as CSV. You declare the type after the keyword `object`.

Just as in an Object Relational system, you can think of “Objects” or “Rows” as synonyms (and also synoym with what some systems such as Salesforce call “Records”). Rows are how we represent objects in tables or files.

The rows which are generated will each have a unique an ID.

person_of_interest.yml

```yaml
- object: Person
  count: 10
  fields:
    name:
      fake: name
    age:
      random_number:
        min: 12
        max: 95
```

We can see above 3 of the main properties of Object Templates:

- object type declaration which determines what table or file the row goes in
- count, which determines how many rows are made. Count can also be randomized or computed using [Function Blocks](#function-blocks) or the [Formula Language](#formula-language)
- fields, which say what data values to put in the row.

You can also have more than one object template for any particular Row Type (i.e. relational table, CSV file, Salesforce Object, ...).

persons_of_interest.yml

```yaml
- object: Person
  count: 3
  fields:
    name:
      fake: name
    age:
      random_number:
        min: 12
        max: 95
- object: Person
  count: 3
  fields:
    name:
      fake: name
    age:
      random_number:
        min: 0
        max: 12
```

In this case, there will be 6 Persons in the Person table (or file), 3 with age between 0 and 12 and 3 with age between 12 and 95.

Sometimes you want to obey a rule like “For every Person I create, I’d like to create 2 animals” (maybe you really like animals).

You would use the `friends` property to do that.

```yaml
- object: Person
  count: 3
  fields:
    name:
      fake: name
    age:
      random_number:
        min: 12
        max: 95
  friends: # I get by with a little help from ...
    - object: Animal
      count: 2
      fields:
        name:
          fake: first_name
```

This will output two animals per person:

```yaml
Person(id=1, name=Sierra Ortega, age=91)
Animal(id=1, name=Sarah)
Animal(id=2, name=Brian)
Person(id=2, name=Robert Haley, age=42)
Animal(id=3, name=Michele)
Animal(id=4, name=Jonathan)
Person(id=3, name=Jason White, age=35)
Animal(id=5, name=John)
Animal(id=6, name=Kimberly)
```

<img src='images/img2.png' id='PJUACAveFpc' alt='Relationship diagram' width='800' height='34'>

There is no explicit relationship between the animals and the people in this case, but sometimes you do want such an implicit “relationship” between the number of one object created and the number of the other.

## Relationships

Relationships are a big part of what makes Snowfakery different than the dozens(!) of tools for data generation out there. For example, we can relate pets to their owners like this:

```yaml
- object: Person
  count: 3
  fields:
    name:
      fake: name
    pet:
      - object: Animal
        fields:
          name:
            fake: first_name
          species: Petaurus Breviceps
```

Now each of the 3 people has a Sugar glider for a pet. Which is a good thing, as long as they know how to take care of them.

Let’s look at what that generates:

```json
Person(id=1, name=Rachel Thompson, pet=Animal(1))
Animal(id=2, name=Charles, species=Petaurus Breviceps)
Person(id=2, name=Alexander Zhang, pet=Animal(2))
Animal(id=3, name=Thomas, species=Petaurus Breviceps)
Person(id=3, name=Lisa King, pet=Animal(3))
```

<img src='images/img3.png' id='PJUACAooXkI' alt='Relationship Diagram'>

In addition, we can relate pets and owners “bidirectionally”, like this:

secret_life_of_pets.yml

```yaml
- object: Person
  count: 3
  fields:
    name:
      fake: name
    pet:
      - object: Animal
        fields:
          name:
            fake: first_name
          owner:
            reference: Person
```

Now person has a field called `pet` which refers to `Animal` rows and those animals have a field called `owner` which refers to a Person row. That’s called a bidirectional relationship. It goes both ways. Not all relationships have to be bi, but sometimes it’s what your schema demands.

Let’s look at the output:

```json
Animal(id=1, name=Nicole, owner=Person(1))
Person(id=1, name=Steven Ellis, pet=Animal(1))
Animal(id=2, name=Richard, owner=Person(2))
Person(id=2, name=Chad Delacruz, pet=Animal(2))
Animal(id=3, name=Tammie, owner=Person(3))
Person(id=3, name=Corey Zamora, pet=Animal(3))
```

<img src='images/img4.png' id='PJUACAKTd0o' alt='Relationship Diagram'>

The relationship from the `Person` to the `Animal` is called `pet` and it is expressed simply by embedding the template for Animal in the field named `pet`. 

The relationship from `Animal` to `Person` is called `owner` and it is expressed using the `reference` function. The function looks up the YAML tree for the relevant Person row.

Sometimes you need to express a relationship between two rows that are not directly related in the hierarchy. You can do this using “nicknames”.

pet_stories_2.yml

```yaml
- object: PetFood
  nickname: petschoice
  fields:
    name: Pets Choice
    cost: $10

- object: PetFood
  nickname: vetschoice
  fields:
    name: Vets Choice
    cost: $12

- object: Person
  count: 3
  fields:
    name:
      fake: name
    dog:
      - object: Animal
        nickname: dog
        fields:
          owner: 
            reference: Person
          name:
            fake: first_name
          species: canine
          food:
            reference: petschoice

    cat:
      - object: Animal
        fields:
          owner: Person
          name:
            fake: first_name
          species: feline
          nemesis: dog
          food:
            reference: vetschoice
```

```json
PetFood(id=1, name=Pets Choice, cost=$10)
PetFood(id=2, name=Vets Choice, cost=$12)
Animal(id=1, owner=Person, name=Dustin, species=canine, food=PetFood(1))
Animal(id=2, owner=Person, name=Edwin, species=feline, nemesis=dog, food=PetFood(2))
Person(id=1, name=Antonio Martin, dog=Animal(1), cat=Animal(2))
Animal(id=3, owner=Person, name=Kristy, species=canine, food=PetFood(1))
Animal(id=4, owner=Person, name=Bryan, species=feline, nemesis=dog, food=PetFood(2))
Person(id=2, name=Hunter Wright, dog=Animal(3), cat=Animal(4))
Animal(id=5, owner=Person, name=Gregory, species=canine, food=PetFood(1))
Animal(id=6, owner=Person, name=Veronica, species=feline, nemesis=dog, food=PetFood(2))
Person(id=3, name=Rebecca Williams, dog=Animal(5), cat=Animal(6))
```

<img src='images/img5.png' id='PJUACAJFf27' alt='Relationship Diagram' width='800' height='233'>

Funky!

The basic rule is that the last row (object) created with the nickname is the one that is referenced.

## Function Blocks

Fields can refer to functions which randomize, compute or look up data. We can do that by nesting the function name under the field name or by using formulas. ([Simple Formulas](#simple-formulas))

### Reference

This function allows you to look up a previously created row (object) and make a reference to it.

```yaml
- object: Animal
  fields:
    name:
      fake: first_name
    owner:
      reference: Person
```

The reference function looks for an ancestor object by table name (`Person`, in this example) or a previously created nicknamed object by `nickname`.

### `random_choice`

Function to choose an option randomly from a list:

```yaml
Payment_Method:
  random_choice:
    - Cash
    - Cheque
    - Credit Card
```

You can either pick with even odds as above, or supply odds as a percentage:

```yaml
StageName:
 random_choice:
    Closed Won: 60%
    In Progress: 20%
    New: 20%
```

You can do more sophisticated randomness with features that will be discussed in the section [Random Weights That Are Not Percentages](#random-weights-that-are-not-percentages).

### `fake`

Generate fake data using functions from the [faker](https://github.com/joke2k/faker) library:

```yaml
- object: Account
  fields:
    Name:
      fake: company
    Description:
      fake: catch_phrase
    BillingStreet:
      fake: street_address
    BillingCity:
      fake: city
    BillingState:
      fake: state
```

You can fake all sorts of stuff. Names, addresses, Latin text, English sentences, URLs, etc. The complete list is here:

<https://faker.readthedocs.io/en/stable/providers.html>

You can also include Faker extension libraries after you’ve added them to your Python install:

```yaml
 - plugin: faker_microservice.Provider
 - object: OBJ
    fields:
    service_name:
        fake:
            microservice
```

You would install that provider like this:

```bash
$ pip install faker_microservice
```

Here are some Python Faker providers:

<https://faker.readthedocs.io/en/master/communityproviders.html>

And you could make your own providers as well.

Fake can be called as an inline function in an expression:

```yaml
FullName: ${{fake.first_name}} Johnson
```

You can also call these functions with arguments as described in Faker's [documentation](https://faker.readthedocs.io/en/master/providers.html)

```yaml
country: ${{fake.country_code(representation='alpha-2')}}
```

### International Fakes (syntax still under development)

You can specify internationally appropriate fakes for many different kind of names (e.g. person, company) like this:

```yaml
- object: Viking
  fields:
    Name:
      i18n_fake:
        locale: no_NO
        fake: first_name
```

This will generate a “typical” Norwegian first name.

You can infer which Faker providers are internationalizable by looking through the Faker [repository](https://github.com/joke2k/faker/tree/master/faker/providers) and seeing which directories have localizations. For example there are only three localizations of [credit card](https://github.com/joke2k/faker/tree/master/faker/providers) (who knew that credit cards were different in Iran and Russia) and dozens of localizations for [person name](https://github.com/joke2k/faker/tree/master/faker/providers/person).

You can also call this as an inline function:

```yaml
lars_or_alf_or_something: ${{i18n_fake(locale="no_NO", fake='first_name')}}
```

### `date_between`

Pick a random date in some date range

```yaml
- object: OBJ
    fields:
    date:
        date_between:
            start_date: 2000-01-01
            end_date: today
```

That would pick a date between Y2K and the present day.

The options `start_date` and `end_date` can take the following forms:

- `YYYY-MM-DD`
- `+<number>d` : `number` days in the future, e.g. `+10d`
- `-<number>d` : `number` days in the past, e.g. `-10d`
- `+<number>m: number` months in the future, e.g. +`10m`
- `+<number>m`: `number` months in the past, e.g. `-10m`
- `+<number>y: number` years in the future, e.g. +`10y`
- `+<number>y`: `number` years in the past, e.g. `-10y`
- `today` : the date the template is evaluated

Examples: Pick a date between 30 days ago and 108 days in the future:

```yaml
Payment_Date:
  date_between:
    start_date: -30d
    end_date: +180d
```

`date_between` can also be used as a function in formulas:

```yaml
wedding_date: Our big day is ${{date_between(start_date="2022-01-31", end_date="2022-12-31")}}
```

### `random_number`

Pick a random number in a range specified by min and max:

```yaml
age:
  random_number:
    min: 12
    max: 95
```

`random_number` can also be used as a function in formulas:

```yaml
some_number: A number ${{random_number(min=5, max=10)}}
```

### `if`

`If` allows you to make field values conditional on other field values.

```yaml
- object: Person
  fields:
    gender:
      random_choice:
        - choice:
            probability: 40%
            pick: Male
        - choice:
            probability: 40%
            pick: Female
        - choice:
            probability: 20%
            pick: Other
    name:
      if:
        - choice:
            when: ${{gender=='Male'}}
            pick:
              fake: first_name_male

        - choice:
            when: ${{gender=='Female'}}
            pick:
              fake: first_name_female

        - choice:
            pick:
              fake: first_name
```

The `when` clause can be a Python formula and it will be interpreted as a boolean similar to how Python would do it. The first `when` clause that matches is selected. The last `choice` clause should have no `when` clause, and it is a fallback which is selected if the others do not match.

## Formula functions and variables

The functions below are designed to be used inside of formulas:

The `child_index` variable returns a counter of how many objects from this template were generated
during the execution of the nearest parent template. It resets each time the parent template is
executed again.

```yaml
child_index: Child number ${{child_index}}
```

The `id` variable returns a unique identifier for the current Object/Row to allow you to construct unique identifiers.

```yaml
fields:
  name: ${{fake.last_name}} Household ${{id}}
```

The `today` variable returns a date
representing the current date. This date
will not chanage during the execution of
a single recipe.

The `fake` variable gives access to faker as described elsewhere in this documentation.

The `context.id` variable is a unique identifyer representing the current Object Template (as opposed to Object/Row).

The `context.filename` variable represents the file containing the template. This is useful
for relative paths.

The `date` function can either coerce a string into a date object for calculations OR generate
a new date object from year/month/day parts:

```yaml
    the_date: ${{date("2018-10-30")}}
    another_date: ${{date(year=2018, month=11, day=30)}}
```

The `relativedelta` [function](https://dateutil.readthedocs.io/en/stable/relativedelta.html) 
from `dateutil` is available for use in calculations like this:

```yaml
${{ date(Date_Established__c) + relativedelta(months=child_index) }}
```

## Macros

Macros allow you to re-use groups of fields instead of repeating them manually.

`evolution.yml`

```yaml
 - macro: canine
   fields:
      sound: barks
      legs: 4
      family: Caninae

 - object: Animal
   include: canine
   fields:
      species: dog
      home: inside

 - object: Animal
   include: canine
   fields:
      species: wolf
      home: outside
```

Which generates:

```yaml
Animal(id=1, sound=barks, legs=4.0, family=Caninae, species=dog, home=inside)
Animal(id=2, sound=barks, legs=4.0, family=Caninae, species=wolf, home=outside)
```

You can include more than one group of macros:

evolution_2.yml

```yaml
  - macro: canine
    fields:
      sound: barks
      legs: 4
      family: Caninae

  - macro: domestic
    fields:
      home: inside
      eats: petfood

  - object: Animal
    count: 2
    include: canine, domestic
    fields:
      name: dog
```

Which generates:

```yaml
Animal(id=1, sound=barks, legs=4.0, family=Caninae, home=inside, eats=petfood, species=dog)
Animal(id=2, sound=barks, legs=4.0, family=Caninae, home=inside, eats=petfood, species=dog)
```

Macros can themselves include other macros.

Macros are especially powerful if you combine them with the `include_file` feature which allows one file to include another. Your organization can make a library of the most common object types you work with and then just override fields to combine them or specialize them.

Fields or friends declared  in the macros listed later override those listed earlier. Fields or friends declared in the Object Template override those declared in macros.

## Including files

You can include a file by a relative path:

```yaml
- include_file: child.yml
```

This pulls in all of the declarations from that file. That file can itself include other files.

## Simple Formulas

Sometimes you would like to include data from another field into the one you are defining now. You can do that with the formula language.

```yaml
- object: Sale
  fields:
    num_items:
        random_number:
            min: 10
            max: 20
    per_item_price:
        random_number:
            min: 10
            max: 20
    message: Thanks for buying ${{num_items}} items @ $${{per_item_price}} each!
```

## Formula Language

You can make your data more dynamic by using formulas. Formulas use the same functions described in [Function Blocks](#function-blocks), but they can be used inline like this:

```yaml
- object: Sale
  count: 2
  fields:
    per_item_price: ${{random_number(20, 50)}}
    number_of_items: 3
    total: ${{per_item_price * number_of_items}}
    message: Thank you for buying $${{total}} items!
```

There is a lot to say about formulas and one day they will all be documented here. In the meantime, here are some general principles:

- use `${{` to start a formula and `}}` to end it
- use Python expression syntax in the middle
- field values defined earlier on this object are available as names
- Use faker values like this: Name: ${{fake.first_name}} Johnson
- parent (or ancestor) values are available through the parent’s object name. Like Opportunity.amount

Formulas are based on a similar language called Jinja2, but we use `${{` and `}}` where Jinja2 uses `{{` and `}}` because our version is more compatible with YAML.

The relevant section of the Jinja document is called  [Expressions](https://jinja.palletsprojects.com/en/2.11.x/templates/#expressions). It includes information about [Literals](https://jinja.palletsprojects.com/en/2.11.x/templates/#literals), [Math](https://jinja.palletsprojects.com/en/2.11.x/templates/#math), [Comparisons](https://jinja.palletsprojects.com/en/2.11.x/templates/#comparisons),  [Logic](https://jinja.palletsprojects.com/en/2.11.x/templates/#logic), [Other Operators](https://jinja.palletsprojects.com/en/2.11.x/templates/#other-operators), [If Expressions](https://jinja.palletsprojects.com/en/2.11.x/templates/#if-expression), [Python Methods](https://jinja.palletsprojects.com/en/2.11.x/templates/#python-methods) and [Builtin Filters](https://jinja.palletsprojects.com/en/2.11.x/templates/#list-of-builtin-filters).

In theory you could use Jinja keywords like `${% if` (as opposed to `{% if`) but it isn’t clear under what circumstances that would be necessary.

## Template File Options

Hard-coding the exact number of records to create into a template file is not always the ideal thing.

You can pass options (numbers, strings, booleans) to your generator script from a command line.

The first step is to declare the options in your template file:

```yaml
- option: num_accounts
  default: 10
```

If you do not specify a default, the option is required and the template will not be processed without it.

In your script, you use the value by referring to it in a formula:

```yaml
- object: Account
  count: ${{num_accounts}}
```

Of course you can do any math you want in the formula:

```yaml
- object: Account
  count: ${{num_accounts / 2}}
    field:
        type: A
- object: Account
  count: ${{num_accounts / 2}}
    field:
        type: B
```

And then you pass that option like this:

```yaml
    --option numaccounts 10
```

## Command Line Interface

```yaml
$ snowfakery --help

  Usage: snowfakery [OPTIONS] YAML_FILE

      Generates records from a YAML file

      Records can go to:
          * stdout (default)
          * JSON file (--output_format=json --output-file=foo.json)
          * diagram file (--output_format=png --output-file=foo.png)
          * a database identified by --dburl (e.g. --dburl sqlite:////tmp/foo.db)
          * or to a directory as a set of CSV files (--output-format=csv --output-folder=csvfiles)

      Diagram output depends on the installation of pygraphviz ("pip install
      pygraphviz")

Options:
  --dburl TEXT                    URL for database to save data to. Use
                                  sqlite:///foo.db if you don't have one set
                                  up.

  --output-format [JSON|json|PNG|png|SVG|svg|svgz|jpeg|jpg|ps|dot|txt|csv]
  --output-folder PATH
  -o, --output-file PATH
  --option EVAL_ARG...            Options to send to the recipe YAML.
  --target-number TEXT...         Target options for the recipe YAML.
  --debug-internals / --no-debug-internals
  --cci-mapping-file PATH
  --generate-cci-mapping-file PATH
  --generate-continuation-file FILENAME
                                  A file that captures information about how
                                  to continue a multi-batch data generation
                                  process

  --continuation-file FILENAME    Continue generating a dataset where
                                  'continuation-file' left off

  --version                       Show the version and exit.
  --help                          Show this message and exit.
  
```

## CSV Output

You create a CSV directory like this:

```basy
$ snowfakery template.yml --output-format csv --output-folder csvfiles
...
```

This would generate a directory that looks like:

```bash
Animal.csv
Person.csv
PetFood.csv
csvw_metadata.json
```

If you do not specify an `output-folder`, the files will be created in the current folder.

The [CSVW](https://www.w3.org/TR/tabular-data-primer/) JSON file is a sort of manifest
for all of the CSV files.

## Advanced Features

### Hidden Fields and objects

As described earlier, fields can refer to each other. For example field `c` could be the sum of fields `a` and `b`. Or perhaps you only want to output PersonLastName if PersonFirstName was set, and PersonFirstName is set randomly.

If you want to create a value which will be used in computations but **not** output in the final database or CSV, you do so by creating a field value prefixed by two underscores.

You can even do this with Object Templates to generate “objects” which are never saved as rows to your database, Salesforce org or output file.

### Random Weights That are not percentages

Consider the following field definition:

```yaml
StageName:
 random_choice:
    Closed Won: 5
    In Progress: 3
    New: 4
```

Observant readers will note that the values do not add up to 100. That’s fine. Closed Won will be selected 5/12 of the time, In Progress will be picked 3/12 and New will be picked 4/12 of the time. They are just weights, not necessarily percentage weights.

## Plugins and Providers

Plugins and Providers allow Snowfakery to be extended with Python code. A plugin adds new functions to Snowfakery. A Provider adds new capabilities to the Fakery library which is exposed to Snowfakery users through the fake: keyword.

You include either Plugins or Providers in a Snowfakery file like this:

```yaml
- plugin: package.module.classname
```

To write a new Provider, please refer to the documentation for Faker at https://faker.readthedocs.io/en/master/#providers

### Built-in Plugins

#### Advanced Math

Snowfakery has a "Math" plugin which gives you access to all features from Python's
[math](https://docs.python.org/3/library/math.html) module. For example:

```yaml
  - plugin: snowfakery.standard_plugins.Math
  - object: OBJ
    fields:
      twelve:
          Math.sqrt: 144
```

Or:

```yaml
  - plugin: snowfakery.standard_plugins.Math
  - object: OBJ
    fields:
      twelve: ${Math.sqrt}
```

### Custom Plugins

To write a new Plugin, make a class that inherits from `SnowfakeryPlugin` and implements either the `custom_functions()` method or a `Functions` nested class. The nested class is simple: each method represents a function to expose in the namespace. In this case the function name would be `DoublingPlugin.double`.

```python
class DoublingPlugin(SnowfakeryPlugin):
    class Functions:
        def double(self, value):
            return value * 2
```

Alternately, you can implement the custom_functions method to return an
object with the attributes that implement your namespace:

```python
class Doubler:
  def double(self, value):
      return value * 2
```

```python
class DoublingPlugin(SnowfakeryPlugin):
    def custom_functions(self, *args, **kwargs):
        return Doubler()
```

Make sure to accept `*args` and `**kwargs` to allow for future extensibility of the method signature.

Despite the name, plugins can also include data values rather than functions in either form of plugin. Plugins essentially use Python's `getattr` to find attributes, properties, methods or functions in the namespace of the object you return from `custom_functions()`.

Plugin functions can store persistent information in a Python dictionary called self.context.context_vars(). It will always be supplied to your plugin. For example, here is a simple plugin that counts:

```python
class PluginThatCounts(SnowfakeryPlugin):
    class Functions:
        def count(self):
            context_vars = self.context.context_vars()
            context_vars.setdefault("count", 0)
            context_vars["count"] += 1
            return context_vars["count"]
```

Plugins also have access to a dictionary called `self.context.field_vars()` whic
represents the values that would be available to a formula running in the same context.

Plugins can return normal Python primitive types, datetime.date, `ObjectRow` or `PluginResult` objects. `ObjectRow` objects represent new output records/objects. `PluginResult` objects
expose a namespace that other code can access through dot-notation. PluginResults can be
initialized with either a dict or an object that exposes the namespace through Python 
getattr().

In the rare event that a plugin has a function which need its arguments to be passed to it unevaluated, for later (perhaps conditional) evaluation, you can use the `@snowfakery.lazy decorator`. Then you can evaluate the arguments with `self.context.evaluate()`. 

For example:

```python
class DoubleVisionPlugin(SnowfakeryPlugin):
    class Functions:
        @lazy
        def do_it_twice(self, value):
            "Evaluates its argument 0 times or twice"
            rc = f"{self.context.evaluate(value)} : {self.context.evaluate(value)}"

          return rc
```

Every second time this is called, it will evaluate its argument twice, and stick the two results into a string. For example, if it were called with a call to `random_number`, you would get two different random numbers rather than the same number twice. If it were called with the counter from above, you would get two different counter values in the string.

```yaml
  - plugin: tests.test_custom_plugins_and_providers.DoubleVisionPlugin
  - plugin: tests.test_custom_plugins_and_providers.PluginThatNeedsState
  - object: OBJ
    fields:
      some_value:
          - DoubleVisionPlugin.do_it_twice:
              - abc
      some_value_2:
          - DoubleVisionPlugin.do_it_twice:
              - ${{PluginThatNeedsState.count()}}
```

This would output an `OBJ` row with values:

```json
  {'id': 1, 'some_value': 'abc : abc', 'some_value_2': '1 : 2'})
```

## Using Snowfakery within CumulusC

You can verify that a Snowfakery-compatible version of CumulusCI is installed like this:

```bash
$ cci task info generate_and_load_from_yaml
...
```

or

```bash
$ cci task run generate_and_load_from_yaml
...
```

If its properly configured, you can use the built-in documentation to invoke Snowfakery options through their CumulusCI names. But for example, you would often run it like this:

```bash
$ cci task run generate_and_load_from_yaml -o generator_yaml datasets/some_snowfakery_yaml -o num_records 1000 -o num_records_tablename Account —org dev
...
```

Options (tbd):

• generator_yaml (required): A generator YAML file to use
• num_records: How many times to instantiate the template.
• mapping: A mapping YAML file to use (optional)
• database_url: A path to put a copy of the sqlite database (for debugging) Default: sqlite:////tmp/test_data_2.db
• vars: Pass values to override options in the format VAR1:foo,VAR2:bar or as a Yaml dict (in
• generate_mapping_file: A path to put a mapping file inferred from the generator_yaml Default: /tmp/temp_mapping.yml

To specify a record type for a record, just put the Record Type’s API Name in a field named RecordType.

## Snowfakery Glossary

- Object: When we think about our Rows in the context of each other, we often use the word “Object”. That’s because rows often *represent* real-world entities like houses (or at least their, addresses), organizations and people (in this case its acceptable to objectify people). See also: “Rows”
- Object Template: These represent instructions on how to create a row, or multiple rows in a database. Each row represents a real-world Object.
- Rows: Rows (often also called “records”) in a database are a unit of related information. For example in Salesforce (which includes a database) a “Contact” has a first name, last name, phone number, etc. Each Contact is a row. “Contact” is the type of each of those rows. Rows represent real-world Objects. See “Objects” above for more information.
- Recipe: A Snowfakery YAML file instructing Snowfakery on what to generate.
- YAML: YAML is a relatively simple, human-readable format. You can learn more about it at [yaml.org](http://yaml.org/). But you can also just pick up the basics of it by reading along.

## Internal Software Architecture

|Filename	                        |Purpose	|
|---	                            |---	|
|cli.py	                  |Click-based Command Line. Uses the Click library to supply a CLI.	|
|data_generator.py	              |The API entry point the CLI and CCI use. <p>This may be the best place to start reading. It abstracts away all of the complexity and outlines the core flow.	|
|parse_recipe_yaml.py	            |Phase 1: parse YAML into a Runtime DOM<p>Includes some hacks to the YAML parser for handling line numbers.	|
|data_generator_runtime.py	      |Phase 2: Runtime.<p>Actually generate the data by walking the template list top-to-bottom, generating rows as appopriate. 	
|data_generator_runtime_dom.py	  |An object model used in Phase 2. Roughly similar to the shape of the YAML file.|
|output_streams.py	              |Where the data goes in the output. Used during Phase 2.	|
|data_gen_exceptions.py	          |Exceptions that can be thrown	|
|generate_mapping_from_recipe.py	|In the CCI context, this utility package allows the generation of mapping.yml files.	|
|template_funcs.py	              |Functions that can be invoked using either block syntax or in Jinja templates	|
|plugins.py                       |Infrastructure for plugins |
|standard_plugins/                |Plugins that ship with Snowfakery |
|tests/	                          |Unit tests	|

<img src='images/img6.png' id='PJUACA3lKvf' alt='Architecture Diagram'>

## Appendix: The Age Old Puzzle

```yaml
    # As I was going to St. Ives,
    # I met a man with seven wives,
    # Each wife had seven sacks,
    # Each sack had seven cats,
    # Each cat had seven kits:
    # Kits, cats, sacks, and wives,
    # How many were there going to St. Ives?
    #
    # https://en.wikipedia.org/wiki/As_I_was_going_to_St_Ives
    - object: narrator
    - object: man
      fields:
        wives:
          - object: woman
            count: 7
            fields:
              luggage:
                - object: sack
                  count: 7
                  fields:
                    contents:
                      - object: cat
                        count: 7
                        fields:
                          offspring:
                          - object: kit
                            count: 7
    - object: stats
      fields:
        num_narrators: ${{ man.id }}
        num_men: ${{ man.id }}
        num_women: ${{ woman.id }}
        num_sack: ${{ sack.id }}
        num_cat: ${{ cat.id }}
        num_kittens: ${{ kit.id }}
        everyone: ${{  num_men + num_narrators + num_women + num_sack + num_cat + num_kittens }}
        going_to_st_ives: ${{ num_narrators }}
```

What does it output as its last row?

This (incomplete) picture probably won’t help....

<img src='images/img7.png' id='PJUACAyJrGL' alt='Silly diagram'>
