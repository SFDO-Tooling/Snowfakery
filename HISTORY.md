# Snowfakery History

In the beginning, programmers created the databases. Now the databases were formless and empty, and they had no data.

And so [Salesforce.org](http://salesforce.org/) said “Let there be data,” and there was Snowfakery. And it was good.

## Snowfakery 2.1

Fix an issue with datasets not being closed in an orderly fashion (PR #492)

Emails and usernames will now be generated to match firstnames and lastnames (PR #420)

The `unique_id` and `unique_alpha_code` variables return a unique number that can be used to distinguish any record from others. For example, we can incorporate a unique ID into an email address or an employee ID. (#438)

Numeric and date counters are now available with the `snowfakery.standard_plugins.Counters` plugin. (#438)

Documented Salesforce.ProfileId function which looks up a Profile
in Salesforce by name and substitutes the ID automatically. (#438)



## Snowfakery 2.0.1

Fix problems installing through pipx.

## Snowfakery 2.0

Recipes can now merge in data from Salesforce orgs as
records, IDs or datasets. (#395 and #401)

Output streams can now be specified as 3rd party libraries. Any Python class name
can be passed to --output-format as long as it adheres to the OutputStream
protocol as shown in examples/YamlOutputStream.py (#351)

Snowfakery is thread-safe/multi-processor-ready and available for parallel usage
in CumulusCI. (CumulusCI Repo)

Snowfakery now supports a --reps option as an easier way to repeat a recipe (#416)

Snowfakery now accepts LeadingCaps syntax for all fakers, as well as
underscore_separated and everythinglowercase. (#403)

Salesforce.ContentVersion and Salesforce.ProfileId convenience functions were added
(#421)

Snowfakery now has voluminous documentation about Fakes in many languages and
locales (#409)

## Snowfakery 1.12

Fix a regression: In some contexts it was impossible to call Faker with either
positional arguments or keyword arguments. It is now possible to call with
keyword arguments again. Positional arguments are still disallowed and older
recipes may need to be updated to use keyword arguments. (#388)

e.g. `${{fake.sentence(nb_words=4)}}` instead of `${{fake.sentence(4)}}`

Snowfakery now informs you that it is not possible to use `just_once` in
a nested context. Previously, the results of doing so were unpredictable.
(#333)

## Snowfakery 1.11

Add a simple benchmarking tool available with the command `snowbench`. #346

Update the namespace used for inline fakes to support the same new names as
block-based fakes. (i.e. ${{fake.FirstName}} is the same as fake: FirstName) #357

Fix a bug which caused problems outputting images. #351

## Snowfakery 1.10

Snowfakery now has some of its own built-in "Fake data types". For example "FirstName"
(instead of first_name) and "Username" (which is like a Salesforce Username).
These new names should be more intuitive for Salesforce users. PR #343

Fake "emails" now use domains based on "example.com" and similar domains specified in
RFC 2606. This ensure that they are never real email addresses. Broader domain
email addressses are still available as described in th documentation. PR #343

Fake names are now case agnostic. FIRSTname, firstNAME, firstname, FIRSTNAME,
etc. are all identical. PR #343

## Snowfakery 1.9

Snowfakery's APIs have expanded. The changes should be backwards-compatible. #315

Add support for embedding external files (text or base64 binary). #322

Add support specifically for Salesforce ContentVersion. #322

## Snowfakery 1.8.1

Fixed packaging issue.

## Snowfakery 1.8

Fix regression when an SObject declares a RecordType on some records
but not others.  #301

Add a new feature for integrating with CumulusCI's Load architecture.
This feature will obsolete most (hopefully all) uses of mapping.yml with Snowfakery.  Documentation for it will be in CumulusCI. #290

## Snowfakery 1.7

Adds support for Salesforce Person Accounts to Snowfakery.
See the documentation for details. (#283)

## Snowfakery 1.6.1

Fix regression: Can set RecordType on objects with names that
are SQL keywords (like Case).  (#277)

## Snowfakery 1.6

Record types can now be specified with `random_choice`. #273

Plugins are now searched for in relative directories called "plugins"
as well as a directory under the user's home directory. See the docs
for more information. #229

Snowfakery can now generate SQL text as an output format. The specific
schema is compatible with CCI's data loader, but can be used in other
contexts. #162

Add a `snowfakery_filename` variable to allow injecting the
recipe filename into recipe output. #249

Add NULL to Snowfakery formulas #239

Allow references to be indirect and include dots in them.
Consequently, dots and other punctuation are now disallowed in
nicknames and discouraged in object/table names. #186

Snowfakery's default branch is now main, so references to
master should be updated.

## Snowfakery 1.5

Adds a "random_reference" feature to allow randomized
connections between objects as described in the documentation.
(PR #184)

Adds a notion of "variables" as described in the documentation. These allow computed values to be easily shared between object templates.
(PR #231)

Adds a "snowfakery_locale" variable which determines what locale drives fake data creation (person nammes, state/province name etc.)
(PR #231)

Does not depend upon pygraphviz library which can be difficult to install. One will still generally want to install
[graphviz](https://graphviz.org/), but not both graphviz AND pygraphviz. (PR #171)

Calls to "fake" are optimized. Recipes that are heavily reliant on faked fields may be 10-15% faster. One tradeoff is that e.g. person names or state names do not follow a real-world statistical distribution. Rare names (in en_US locale) like "Mathias" are now as common as real-world common names like "Matthew". (PR #214)

## Snowfakery 1.4

Adds Salesforce Example Files.

Adds an official API for embedding in Python.

Updates dependencies including Faker, which has Salesforce-contributed optimizations.

Adds min, max, round to the math plugin.

## Snowfakery 1.3

`random_number` can now accept a "step" argument as described in the docs.

Allow a short-form random_choice syntax that matches the docs.

`date` now casts datetimes to dates instead of returning them unchanged.

The --target-number value now allows its two sub-arguments to be specified in either order: Tablename then number or number then tablename.

The command line interface gives better error messages about unknown
file extensions.

The continuation file format changed. Do not upgrade Snowfakery while
running a long-running Snowfakery process. The new configuration file
should be less prone to issues relating to failures to serialize results.

## Snowfakery 1.2

Improvements to plugin API: add `evaluate_raw` and `simplify`

Dependency updates.

## Snowfakery 1.1.2

Minor improvements in error reporting.

Update to Faker 4.1.3

## Snowfakery 1.1.1

Fix a deployment problem relating to version.txt

## Snowfakery 1.1

Support for External Datasets. (PR #102)

Macros within Macros now work correctly. (PR #120)

It is now possible to have forward references to Nicknames. (PR #113)

Closed Issue #42: relating to relative month parsing

Closed Issue #131: Parse errors would result in an invalid rather than empty
JSON file.

Change the architecture to always initialize the database based on the recipe
and never do it from the CumulusCI Mapping file.

## Snowfakery 1.0.1

Update URLs for PyPI. No changes to the Snowfakery code itself.

## Snowfakery 1.0.0

Add child_index feature for calculating the index number of each child object (see documentation for more information).

Internal changes to support upcoming features in CumulusCI.

Documentation for the Math plugin.

Dates can now be parsed from strings with the `date()` function. (see docs)

Added `relativedelta()` function. (see docs)

Official formula syntax is now ${{foo}} instead of `<<foo>>`.
The old syntax will be supported for at least the remainder of 2020.

Docs are checked into Git in Markdown format.

Official terminology changed so that Snowfakery files are now called "recipes".

Stabilize the output order for CCI Mapping files generated by Snowfakery.

New syntax for Internalized fake data. (see docs)

Internally use the plugin architecture to support even the builtin functions.

## Snowfakery 0.8.1

Snowfakery includes support for Salesforce RecordTypes.

Snowfakery can output SQL/JSON NULL using YAML blank fields or the YAML literal 'null'

Fields starting with __ are now properly suppressed as per the documentation.

Various performance and reliability improvements:

* parsed dates are now cached
* Jinja values are always coerced to a string where appropriate
* internal attributes were renamed for clarity
* lookups are only generated in CCI mappings if they are actually needed

## Snowfakery 0.8.0

Snowfakery now specifies its install requirements with minimum versions rather than specific versions,
for improved compatibility with CumulusCI.

## Snowfakery 0.7

Windows compatibility improved, especially in test cases.

Changed the syntax for CSV handling.

Added --output-folder command.

## Snowfakery 0.6.1, 0.6.2, 0.6.3

Bugfixes (not user visible) and code cleanup.

## Snowfakery 0.6

Snowfakery 0.6 is open source!

## Snowfakery 0.5

The first version of Snowfakery was [Salesforce.org](http://salesforce.org/) internal-only.
