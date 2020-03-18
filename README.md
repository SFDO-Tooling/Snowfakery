# Snowfakery Documentation

Snowfakery is a tool for generating fake data that has relations between tables. Every row is faked data, but also unique and random, like a snowflake. 

To tell Snowfakery what data you want to generate, you need to write a Factory file in YAML.

Snowfakery can write its output to stdout, or any database accessible to SQLAlchemy. **When it is embedded in CumulusCI it can output to a Salesforce org**. Adding new output formats is fairly straightforward and open source contributions of that form are gratefully accepted.

## Central Concepts

YAML is a relatively simple, human-readable format. You can learn more about it at [yaml.org](http://yaml.org/). But you can also just pick up the basics of it by reading along with the examples below. 

YAML uses indentation to say which parts of the file are related to each other. Let’s get started with a stupidly simple example:

simple_static.yml

```
- object: Person
  fields:
    name: Buster Bluth
    age: 35
```

We run this example through Snowfakery like this:

`python generate_from_yaml.py docs/examples/simple_static.yml`

(this example does not represent the final command line interface nor how to use [Advanced Features](https://quip.com/AXY5A4WGTbNP#PJUACAevPk4))

This simple example will generate a single record that looks like this:

```
Person(id=1, name=Buster Bluth, age=35.0)
```

In other words, it is a person record with 3 fields:

|Field	|id	|name	|age	|
|---	|---	|---	|---	|
|Value	|1	|Buster Bluth	|35	|

Two of the fields include data from the YAML file. The ID is auto-generated. 

**Note:** Snowfakery only works for models which are amenable to having an id column on every record. Your tools can use the column, ignore the column, or exchange it for another kind of ID (as CumulusCI does, with Salesforce) but Snowfakery always generates IDs and refers between tables with IDs. Future versions might include a command line option to turn this behaviour on or off.

Let’s make this example more interesting:

persons_of_interest.yml

```
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

* object: Person : This is a template for objects that will go in the Person table
* count: we want 3 records instead of just 1
* name: fake: name : we want to fake the name instead of hard coding it. The list of things you can “fake” is based on a library called “Faker” which we will discuss later.
* age: random_number: we want a random number between the min and max

Now you should get an output more like this:

```
Person(id=1, name=Allison Garcia, age=94)
Person(id=2, name=Megan Campos, age=67)
Person(id=3, name=Katherine Nelson, age=92)
```

We have created people! Or at least fake personas for people! And every time you run it, you will get a different set of people.

So that’s pretty cool, and it’s fake, but it isn't very deep. Let's go deeper.

pet_stories.yml

```
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
                cost: $10
```

If you’re lost: don't worry! Those are a lot of new concepts at once, and you don't have to understand everything in this example right now. We'll come back to these concepts one by one.

But in case you’re in a hurry: In this case we're creating 3 Person objects. Each one has a name, age, dog and cat. Each dog or cat is an Animal, so we'll get 2 animals per Person or a total of 6. Each animal has a favorite food, so we'll get 6 PetFood objects as well.

[Image: image.png]
Later, we’ll discuss how we could have just 2 PetFood objects which are shared. We’ll also discuss how we could randomly select a Pet species or Food. 

## Outputs

Snowfakery builds on a tool called SQLAlchemy, so it gets a variety of database connectors for free:

https://docs.sqlalchemy.org/en/13/dialects/index.html

When integrated with CumulusCI (see [Advanced Features](https://quip.com/AXY5A4WGTbNP#PJUACAevPk4)) it is possible to output to a Salesforce instance.

Snowfakery can also output JSON, directories of CSV and object diagrams.

CSV output goes to a directory with one CSV file per table and a JSON manifest file in the [csvw](https://www.w3.org/TR/tabular-data-primer/) format.

## Objects

The main, core concept in the language is an “Object Template”. It basically represents instructions on how to create a row (or multiple rows) in a database. The rows which are generated will each have a unique an ID. It’s important to keep in mind the difference between the template, in the YAML file and the multiple rows it might generate in the output.

person_of_interest.yml

```
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

We can see above 3 of the main properties of objects:

* object type, which determines what table the object goes in
* count, which determines how many objects are made. Count can also be randomized or computed using [Function Blocks](https://quip.com/AXY5A4WGTbNP#PJUACA1H4V4) or the [Formula Language](https://quip.com/AXY5A4WGTbNP#PJUACACCtyK)
* fields, which say what data values to put in the table.

You can also have more than one object template for a single table.

persons_of_interest.yml

```
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

Sometimes you want to obey a rule like “For every Person I create, I’d like to create 2 animals” (maybe you really like animals).

You would use the `friends` property to do that.

```
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

```
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

[Image: image.png]
There is no explicit relationship between the animals and the people, so we’ll teach how to do that next.

## Relationships

Relationships are a big part of what makes Snowfakery different than the dozens(!) of tools for data generation out there. For example, we can relate pets and owners (“bidirectionally”) like this:

secret_life_of_pets.yml

```
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

Now person has a field called `pet` which refers to `Animal` objects and those animals have a field called `owner` which refers to a Person object. That’s called a bidirectional relationship. It goes both ways. Not all relationships have to be bi, but sometimes it’s what your schema demands.

Let’s look at the output:

```
Animal(id=1, name=Nicole, owner=Person(1))
Person(id=1, name=Steven Ellis, pet=Animal(1))
Animal(id=2, name=Richard, owner=Person(2))
Person(id=2, name=Chad Delacruz, pet=Animal(2))
Animal(id=3, name=Tammie, owner=Person(3))
Person(id=3, name=Corey Zamora, pet=Animal(3))
```

[Image: image.png]

The relationship from the `Person` to the `Animal` is called `pet`
and it is expressed simply by embedding the template for the Animal object in the field named `pet`. 

The relationship from `Animal` to `Person` is called `owner` and it is expressed using the `reference` function. The function looks up the YAML tree for the relevant Person.  
Sometimes you need to express a relationship between two objects that are not directly related in the hierarchy. You can do this using “nicknames”.

pet_stories_2.yml

```
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
          owner: Person
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

```
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

[Image: image.png]Funky!

The basic rule is that the last object created with the nickname is the one that is referenced. 

## Function Blocks

Fields can refer to functions which randomize, compute or look up data.

### Reference

Look up an object to make a reference to it.

```
      - object: Animal
        fields:
          name:
            fake: first_name
          owner:
            reference: Person
```

The reference function looks for an ancestor object by table name (`Person`, in this example) or a previously created nicknamed object by `nickname`.

### random_choice

Choose an option randomly

```
Payment_Method:
  random_choice:
    - Cash
    - Cheque
    - Credit Card
```

You can either pick with even odds as above, or supply odds as a percentage:

```
StageName:
 random_choice:
    Closed Won: 60%
    In Progress: 20%
    New: 20%
```

Randomly choosing a sub-object in a reference field will probably (to be investigated) generate both objects before selecting one to

### Fake

Generate fake data using functions from the [faker](https://github.com/joke2k/faker) library:

```
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

https://faker.readthedocs.io/en/stable/providers.html

### International Fakes

```
fake_i18n('no_NO').phone_number()
ake_i18n('no_NO').first_name()
```

TODO: better explanation

### Date_between

Pick a random date in some date range

```
- object: OBJ
    fields:
    date:
        date_between:
            start_date: 2000-01-01
            end_date: today
```

That would pick a date between Y2K and the present day.

The options `start_date` and `end_date` can take the following forms:

* `YYYY-MM-DD`
* `+<number>d` : `number` days in the future, e.g. `+10d`
* `-<number>d` : `number` days in the past, e.g. `-10d`
* `+<number>m: number` months in the future, e.g. +`10m`
* `+<number>m`: `number` months in the past, e.g. `-10m`
* `+<number>y: number` years in the future, e.g. +`10y`
* `+<number>y`: `number` years in the past, e.g. `-10y`
* `today` : the date the template is evaluated

Examples: Pick a date between 30 days ago and 108 days in the future:

```
Payment_Date:
  date_between:
    start_date: -30d
    end_date: +180d
```

### random_number

Pick a random number in a range specified by min and max:

```
age:
  random_number:
    min: 12
    max: 95
```

### Counter

Counters let you make unique values. 

Let’s say you want a unique customer number for every Person in a group:

```
- object: Person
  count: 3
  fields:
    customer_id:
      counter: Person 
```

TBD: counters are unfinished in the code

## Macros

Macros allow you to re-use groups of fields instead of repeating them manually.

evolution.yml

```
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

```
Animal(id=1, sound=barks, legs=4.0, family=Caninae, species=dog, home=inside)
Animal(id=2, sound=barks, legs=4.0, family=Caninae, species=wolf, home=outside)
```

You can include more than one group of macros:

evolution_2.yml

```
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

```
Animal(id=1, sound=barks, legs=4.0, family=Caninae, home=inside, eats=petfood, species=dog)
Animal(id=2, sound=barks, legs=4.0, family=Caninae, home=inside, eats=petfood, species=dog)
```

Macros can themselves include other macros.

Macros are especially powerful if you combine them with the `include_file` feature which allows one file to include another. Your organization can make a library of the most common object types you work with and then just override fields to combine them or specialize them.

Macros are included left-to-right so if two share values, the last one will override the previous. And the template itself overwrites the macros. (TODO: add test cases for this)

## Including files

You can include a file by a relative path:

```
- include_file: child.yml
```

This pulls in all of the declarations from that file. That file can itself include other files.

## Simple Formulas

Sometimes you would like to include data from another field into the one you are defining now. You can do that with the formula language.

```
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
    message: Thanks for buying <<num_items>> items @ $<<per_item_price>> each!
```




## Formula Language

You can make your data more dynamic by using formulas. Formulas use the same functions described in [Function Blocks](https://quip.com/AXY5A4WGTbNP#PJUACA1H4V4), but they can be used inline like this:

```
- object: Sale
  count: 2
  fields:
    per_item_price: <<random_number(20, 50)>>
    number_of_items: 3
    total: <<per_item_price * number_of_items>>
    message: Thank you for buying $<<total>> items!
```

There is a lot to say about formulas and one day they will all be documented here. In the meantime, here are some general principles:

* use `<<` to start a formula and `>>` to end it
* use Python expression syntax in the middle
* field values defined above on this object are available.
* Use faker values like this: Name: <<fake.word>> Sponsorship
* parent values are available through the parent’s object name. Like Opportunity.amount

Formulas are based on a similar language called Jinja2, but we use `<<` and `>>` where Jinja2 uses `{{` and `}}` because our characters are more compatible with YAML. Similarly, where Jinja2 uses {`% if %}` we use `<% if %>`.

## Template File Options

Hard-coding the exact number of records to create into a template file is not always the ideal thing.

You can pass options (numbers, strings, booleans) to your generator script from a command line.

The first step is to declare the options in your template file:

```
- option: num_accounts
  default: 10
```

If you do not specify a default, the option is required and the template will not be processed without it.

In your script, you use the value by referring to it in a formula:


```
- object: Account
  count: <<num_accounts>>
```

Of course you can do any math you want in the formula:

```
- object: Account
  count: <<num_accounts / 2>>
    field:
        type: A
- object: Account
  count: <<num_accounts / 2>>
    field:
        type: B
```

And then you pass that option like this:

```
--option numaccounts 10
```

## Plugins and Providers 

Plugins and Providers allow Snowfakery to be extended with Python code. A plugin adds new functions to Snowfakery. A Provider adds new capabilities to the Fakery library which is exposed to Snowfakery users through the fake: keyword.

You include either Plugins or Providers in a Snowfakery file like this:


```
- plugin: package.module.classname
```

To write a new Provider, please refer to the documentation for Faker at https://faker.readthedocs.io/en/master/#providers

To write a new Plugin, make a class that inherits from `SnowfakeryPlugin` and implements either the `custom_functions()` method or a `Functions` nested class. The nested class is simple: each method represents a function to expose in the namespace. In this case the function name would be `DoublingPlugin.double`.

```
class DoublingPlugin(SnowfakeryPlugin):
    class Functions:
        def double(self, value):
            return value * 2
```

Make sure to accept `*args` and `**kwargs` to allow for future extensibility of the method signature, and return an object that implements the namespace that you would like to expose. Once again, the function name would be `DoublingPlugin.double`.

```
class Doubler:
   def double(self, value):
       return value * 2

class DoublingPlugin(SnowfakeryPlugin):
    def custom_functions(self, *args, **kwargs):
        return Doubler()
```

Despite the name, plugins can also include data values rather than functions in either form of plugin.
Plugins essentially use Python's `getattr` to find attributes, properties, methods or functions in
the namespace of the object you return from `custom_functions()`.

## Command Line Interface

```
Run 

python snowfakery/cli.py --help for information about command line options

```

## CSV Output

You create a CSV directory like this:

```
python snowfakery/cli.py template.yml —-dburl csvfile:///tmp/csvout
```

This would generate a directory that looks like:

```
Animal.csv 
Person.csv 
PetFood.csv 
csvw_metadata.json
```

The CSVW format is documented here: https://www.w3.org/TR/tabular-data-primer/

## Advanced Features

### Hidden Fields

As described earlier, fields can refer to each other. For example field `c` could be the sum of fields `a` and `b`. Or perhaps you only want to output PersonLastName if PersonFirstName was set, and PersonFirstName is set randomly.

If you want to create a value which will be used in computations but **not** output in the final database or CSV, you do so by creating a field value prefixed by two underscores.


## Snowfakery and Security

Snowfakery is intended to be used as a replacement for Python code which generates data. You should
not feed it an input file from an untrusted source, just as you would not run an untrusted
Python script in your interpreter. If you intend to generate Snowfakery files from another
system, you should generate or validate any formula expressions rather than taking them directly
from users.


## Snowfakery within CumulusCI

The library will be available within a future version of CumulusCI as the class cumulusci.tasks.bulkdata.data_generation.generate_from_yaml.GenerateFromYaml


Options:

• generator_yaml (required): A generator YAML file to use
• num_records: How many times to instantiate the template.
• mapping: A mapping YAML file to use (optional)
• database_url: A path to put a copy of the sqlite database (for debugging) Default: sqlite:////tmp/test_data_2.db
• vars: Pass values to override options in the format VAR1:foo,VAR2:bar
• generate_mapping_file: A path to put a mapping file inferred from the generator_yaml Default: /tmp/temp_mapping.yml

## Internal Software Architecture

|Filename	|Purpose	|
|---	|---	|
|snowfakery.py	|Click-based CLI.

Uses the Click library to supply a CLI.	|
|generate_from_yaml.py	|A CCI task interface to the system.

Wraps data_generator.generate in a CCI task.	|
|data_generator.py	|The API entry point that the above two use.

This may be the best place to start reading. It abstracts away all of the complexity and outlines the core flow.	|
|parse_factory_yaml.py	|Phase 1: parse YAML into a Runtime DOM

Includes some hacks to the YAML parser for handling line numbers.	|
|data_generator_runtime_dom.py	|Phase 2: Runtime.

Actually generate the data by walking the template list top-to-bottom, generating rows as appopriate. 	|
|data_generator_runtime.py	|
|output_streams.py	|Where the data goes in the output. Used during Phase 2.	|
|data_gen_exceptions.py	|Exceptions that can be thrown	|
|generate_mapping_from_factory.py	|In the CCI context, this utility package allows the generation of mapping.yml files.	|
|template_funcs.py	|Functions that can be invoked using either block syntax or in Jinja templates	|
|	|	|
|tests/	|Unit tests	|




