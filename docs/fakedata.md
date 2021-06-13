# Fake Data: en_US

The basic concepts of fake data are described in
the [main docs](index.md#fake-data).

Current Locale: en_US (United States)


Our fake data can be localized to many languages. We have
[detailed docs](https://snowfakery.readthedocs.io/en/feature-fake-data-docs/locales.html) 
about the other languages.

[TOC]

## Commonly Used

### Salesforce Fakers

#### fake: Email

Email address using one of the "example" domains

Aliases:  email

Source: [snowfakery](https://github.com/SFDO-Tooling/Snowfakery/tree/main/snowfakery/fakedata/fake_data_generator.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Email}}
        block_example:
          fake: Email

Outputs:

    Example(id=1, inline_example=dakotagaines@example.org, block_example=thurst@example.net)

### Address Fakers

#### fake: AdministrativeUnit

Aliases:  administrative_unit, administrativeunit

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.AdministrativeUnit}}
        block_example:
          fake: AdministrativeUnit

Outputs:

    Example(id=1, inline_example=North Carolina, block_example=New York)

#### fake: BuildingNumber

Example: '791'

Aliases:  building_number, buildingnumber

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.BuildingNumber}}
        block_example:
          fake: BuildingNumber

Outputs:

    Example(id=1, inline_example=15781, block_example=6593)

#### fake: City

Example: 'Sashabury'

Aliases:  city

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.City}}
        block_example:
          fake: City

Outputs:

    Example(id=1, inline_example=New Raymondside, block_example=West Edgar)

#### fake: Country

Aliases:  country

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Country}}
        block_example:
          fake: Country

Outputs:

    Example(id=1, inline_example=Armenia, block_example=Eritrea)

#### fake: CountryCode

Aliases:  country_code, countrycode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CountryCode}}
        block_example:
          fake: CountryCode

Outputs:

    Example(id=1, inline_example=SE, block_example=RU)

#### fake: CurrentCountry

Aliases:  current_country, currentcountry

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CurrentCountry}}
        block_example:
          fake: CurrentCountry

Outputs:

    Example(id=1, inline_example=United States, block_example=United States)

#### fake: CurrentCountryCode

Aliases:  current_country_code, currentcountrycode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CurrentCountryCode}}
        block_example:
          fake: CurrentCountryCode

Outputs:

    Example(id=1, inline_example=US, block_example=US)

#### fake: Postalcode

Aliases:  postalcode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Postalcode}}
        block_example:
          fake: Postalcode

Outputs:

    Example(id=1, inline_example=67514, block_example=64192)

#### fake: State

Aliases:  state

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.State}}
        block_example:
          fake: State

Outputs:

    Example(id=1, inline_example=North Carolina, block_example=New York)

#### fake: StreetAddress

Example: '791 Crist Parks'

Aliases:  street_address, streetaddress

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.StreetAddress}}
        block_example:
          fake: StreetAddress

Outputs:

    Example(id=1, inline_example=93328 Ortiz Common, block_example=714 Knox Crossing Suite 839)

### Company Fakers

#### fake: CatchPhrase

Example: 'Robust full-range hub'

Aliases:  catch_phrase, catchphrase

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/company/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CatchPhrase}}
        block_example:
          fake: CatchPhrase

Outputs:

    Example(id=1, inline_example=Devolved executive challenge, block_example=Versatile bandwidth-monitored process improvement)

#### fake: Company

Example: 'Acme Ltd'

Aliases:  company

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/company/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Company}}
        block_example:
          fake: Company

Outputs:

    Example(id=1, inline_example=Krause-Wilcox, block_example=Bautista, Callahan and Davila)

### Date_Time Fakers

#### fake: Time

Get a time string (24h format by default)
:param pattern format
Example: '15:02:34'

Aliases:  time

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Time}}
        block_example:
          fake: Time

Outputs:

    Example(id=1, inline_example=19:09:38, block_example=16:37:16)

#### fake: Year

Aliases:  year

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Year}}
        block_example:
          fake: Year

Outputs:

    Example(id=1, inline_example=2003, block_example=1997)

### Lorem Fakers

#### fake: Paragraph

Generate a paragraph.

The ``nb_sentences`` argument controls how many sentences the paragraph
will contain, and setting ``variable_nb_sentences`` to ``False`` will
generate the exact amount, while setting it to ``True`` (default) will
generate a random amount (+/-40%, minimum of 1) using
|randomize_nb_elements|.

Under the hood, |sentences| is used to generate the sentences, so the
argument ``ext_word_list`` works in the same way here as it would in
that method.




ext_word_list=['abc', 'def', 'ghi', 'jkl']

Aliases:  paragraph

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/lorem/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Paragraph(nb_sentences=5)}}
        block_example:
          fake.Paragraph:
            nb_sentences: 5

Outputs:

    Example(id=1, inline_example=Others kind company likely. Tonight themselves true power home price. Night actually score from. Name care several., block_example=Particular pull opportunity throughout take car. Hold increase practice ability court. Civil development large report purpose themselves. I reduce industry. Close ask reduce. Month maintain no sense this manager fine.)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Paragraph(nb_sentences=5, variable_nb_sentences=False)}}
        block_example:
          fake.Paragraph:
            nb_sentences: 5
            variable_nb_sentences: false

Outputs:

    Example(id=1, inline_example=Anyone state wind indeed nature white without. Would I question first. Add senior woman put partner. Budget power them evidence without. Little type physical against., block_example=Son break either president stage population boy. Everything affect American race. Fire happen nothing support suffer which parent. Republican total policy head Mrs debate onto. Catch even front.)

#### fake: Sentence

Generate a sentence.

The ``nb_words`` argument controls how many words the sentence will
contain, and setting ``variable_nb_words`` to ``False`` will generate
the exact amount, while setting it to ``True`` (default) will generate
a random amount (+/-40%, minimum of 1) using |randomize_nb_elements|.

Under the hood, |words| is used to generate the words, so the argument
``ext_word_list`` works in the same way here as it would in that method.




ext_word_list=['abc', 'def', 'ghi', 'jkl']

Aliases:  sentence

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/lorem/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Sentence(nb_words=10)}}
        block_example:
          fake.Sentence:
            nb_words: 10

Outputs:

    Example(id=1, inline_example=Feeling fact by four two data son., block_example=Onto knowledge other his offer face country cost party prevent live bed serious.)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Sentence(nb_words=10, variable_nb_words=False)}}
        block_example:
          fake.Sentence:
            nb_words: 10
            variable_nb_words: false

Outputs:

    Example(id=1, inline_example=Theory type successful together type music hospital relate every speech., block_example=Support time operation wear often late produce you true soldier.)

#### fake: Text

Generate a text string.

The ``max_nb_chars`` argument controls the approximate number of
characters the text string will have, and depending on its value, this
method may use either |words|, |sentences|, or |paragraphs| for text
generation. The ``ext_word_list`` argument works in exactly the same way
it would in any of those methods.

Aliases:  text

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/lorem/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Text(max_nb_chars=20)}}
        block_example:
          fake.Text:
            max_nb_chars: 20

Outputs:

    Example(id=1, inline_example=Book pick method., block_example=Organization into.)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Text(max_nb_chars=80)}}
        block_example:
          fake.Text:
            max_nb_chars: 80

Outputs:

    Example(id=1, inline_example=There many true follow marriage material. Myself use act relationship section., block_example=Family relationship like son might trip at candidate.)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Text(max_nb_chars=160)}}
        block_example:
          fake.Text:
            max_nb_chars: 160

Outputs:

    Example(id=1, inline_example=Measure too maybe off question source. Wrong section town deal movement out stay lot. Parent do ten after those scientist., block_example=Individual man tell response purpose character would.
    Partner hit another. Sing after our car food record power. Himself simply make thing particular.)

#### fake: Word

Generate a word.

This method uses |words| under the hood with the ``nb`` argument set to
``1`` to generate the result.

Aliases:  word

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/lorem/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Word}}
        block_example:
          fake: Word

Outputs:

    Example(id=1, inline_example=interview, block_example=why)

### Person Fakers

#### fake: FirstName

Aliases:  first_name, firstname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FirstName}}
        block_example:
          fake: FirstName

Outputs:

    Example(id=1, inline_example=Danielle, block_example=Vernon)

#### fake: FirstNameFemale

Aliases:  first_name_female, firstnamefemale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FirstNameFemale}}
        block_example:
          fake: FirstNameFemale

Outputs:

    Example(id=1, inline_example=Krista, block_example=Jasmine)

#### fake: FirstNameMale

Aliases:  first_name_male, firstnamemale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FirstNameMale}}
        block_example:
          fake: FirstNameMale

Outputs:

    Example(id=1, inline_example=Logan, block_example=Jared)

#### fake: FirstNameNonbinary

Aliases:  first_name_nonbinary, firstnamenonbinary

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FirstNameNonbinary}}
        block_example:
          fake: FirstNameNonbinary

Outputs:

    Example(id=1, inline_example=Danielle, block_example=Vernon)

#### fake: LastName

Aliases:  last_name, lastname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LastName}}
        block_example:
          fake: LastName

Outputs:

    Example(id=1, inline_example=Goodwin, block_example=Hendrix)

#### fake: Name

Example: 'John Doe'

Aliases:  name

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Name}}
        block_example:
          fake: Name

Outputs:

    Example(id=1, inline_example=Morgan Escobar, block_example=Jay Coleman II)

#### fake: NameFemale

Aliases:  name_female, namefemale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.NameFemale}}
        block_example:
          fake: NameFemale

Outputs:

    Example(id=1, inline_example=Morgan Escobar DDS, block_example=Briana Moon MD)

#### fake: NameMale

Aliases:  name_male, namemale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.NameMale}}
        block_example:
          fake: NameMale

Outputs:

    Example(id=1, inline_example=Ruben Escobar III, block_example=Chris Moon II)

### Phone_Number Fakers

#### fake: PhoneNumber

Aliases:  phone_number, phonenumber

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/phone_number/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PhoneNumber}}
        block_example:
          fake: PhoneNumber

Outputs:

    Example(id=1, inline_example=484-185-8398, block_example=001-471-965-9342)

## Rarely Used

### Salesforce Fakers

#### fake: UserName

Salesforce-style username in the form of an email address

Aliases:  user_name, username

Source: [snowfakery](https://github.com/SFDO-Tooling/Snowfakery/tree/main/snowfakery/fakedata/fake_data_generator.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UserName}}
        block_example:
          fake: UserName

Outputs:

    Example(id=1, inline_example=Kevin_Dodson_fb3675b8-9cde-43e6-8870-e15c2fcd81b5@email-47.sullivan.com, block_example=James_Terrell_e5eeac76-148b-4758-97ab-792809e469e6@email-86.morrow.com)

#### fake: Alias

Salesforce-style 8-character alias

Aliases:  alias

Source: [snowfakery](https://github.com/SFDO-Tooling/Snowfakery/tree/main/snowfakery/fakedata/fake_data_generator.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Alias}}
        block_example:
          fake: Alias

Outputs:

    Example(id=1, inline_example=Martin, block_example=Priscill)

#### fake: RealisticMaybeRealEmail

Like fake: email except that the email domain may be real and therefore
the email address itself may be real. Use with caution, you might
accidentally email strangers!!!

Aliases:  realistic_maybe_real_email, realisticmayberealemail

Source: [snowfakery](https://github.com/SFDO-Tooling/Snowfakery/tree/main/snowfakery/fakedata/fake_data_generator.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RealisticMaybeRealEmail}}
        block_example:
          fake: RealisticMaybeRealEmail

Outputs:

    Example(id=1, inline_example=holly75@gmail.com, block_example=langpenny@hotmail.com)

### Address Fakers

#### fake: Address

Example: '791 Crist Parks, Sashabury, IL 86039-9874'

Aliases:  address

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Address}}
        block_example:
          fake: Address

Outputs:

    Example(id=1, inline_example=848 Martin Springs Suite 947
    Claystad, MD 80819, block_example=533 Sean Crescent Apt. 525
    Gouldton, WY 19684)

#### fake: CityPrefix

Aliases:  city_prefix, cityprefix

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CityPrefix}}
        block_example:
          fake: CityPrefix

Outputs:

    Example(id=1, inline_example=West, block_example=New)

#### fake: CitySuffix

Example: 'town'

Aliases:  city_suffix, citysuffix

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CitySuffix}}
        block_example:
          fake: CitySuffix

Outputs:

    Example(id=1, inline_example=fort, block_example=furt)

#### fake: MilitaryApo

Example: 'PSC 5394 Box 3492

Aliases:  military_apo, militaryapo

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MilitaryApo}}
        block_example:
          fake: MilitaryApo

Outputs:

    Example(id=1, inline_example=PSC 8016, Box 0975, block_example=PSC 3513, Box 9332)

#### fake: MilitaryDpo

Example: 'Unit 3333 Box 9342'

Aliases:  military_dpo, militarydpo

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MilitaryDpo}}
        block_example:
          fake: MilitaryDpo

Outputs:

    Example(id=1, inline_example=Unit 8016 Box 0975, block_example=Unit 3513 Box 9332)

#### fake: MilitaryShip

Example: 'USS'

Aliases:  military_ship, militaryship

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MilitaryShip}}
        block_example:
          fake: MilitaryShip

Outputs:

    Example(id=1, inline_example=USCGC, block_example=USNV)

#### fake: MilitaryState

Example: 'APO'

Aliases:  military_state, militarystate

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MilitaryState}}
        block_example:
          fake: MilitaryState

Outputs:

    Example(id=1, inline_example=AA, block_example=AA)

#### fake: PostalcodeInState

Aliases:  postalcode_in_state, postalcodeinstate

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PostalcodeInState}}
        block_example:
          fake: PostalcodeInState

Outputs:

    Example(id=1, inline_example=97914, block_example=62068)

#### fake: PostalcodePlus4

Aliases:  postalcode_plus4, postalcodeplus4

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PostalcodePlus4}}
        block_example:
          fake: PostalcodePlus4

Outputs:

    Example(id=1, inline_example=76966-3579, block_example=66651-2282)

#### fake: Postcode

Aliases:  postcode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Postcode}}
        block_example:
          fake: Postcode

Outputs:

    Example(id=1, inline_example=67514, block_example=64192)

#### fake: PostcodeInState

:returns: A random postcode within the provided state abbreviation

:param state_abbr: A state abbreviation

Aliases:  postcode_in_state, postcodeinstate

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PostcodeInState}}
        block_example:
          fake: PostcodeInState

Outputs:

    Example(id=1, inline_example=97914, block_example=62068)

#### fake: SecondaryAddress

Aliases:  secondary_address, secondaryaddress

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SecondaryAddress}}
        block_example:
          fake: SecondaryAddress

Outputs:

    Example(id=1, inline_example=Suite 115, block_example=Suite 815)

#### fake: StateAbbr

:returns: A random state or territory abbreviation.

:param include_territories: If True, territories will be included.
If False, only states will be returned.

Aliases:  state_abbr, stateabbr

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.StateAbbr}}
        block_example:
          fake: StateAbbr

Outputs:

    Example(id=1, inline_example=ME, block_example=MI)

#### fake: StreetName

Example: 'Crist Parks'

Aliases:  street_name, streetname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.StreetName}}
        block_example:
          fake: StreetName

Outputs:

    Example(id=1, inline_example=Dwayne River, block_example=Krause Place)

#### fake: StreetSuffix

Example: 'Avenue'

Aliases:  street_suffix, streetsuffix

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.StreetSuffix}}
        block_example:
          fake: StreetSuffix

Outputs:

    Example(id=1, inline_example=Green, block_example=Pass)

#### fake: Zipcode

Aliases:  zipcode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Zipcode}}
        block_example:
          fake: Zipcode

Outputs:

    Example(id=1, inline_example=67514, block_example=64192)

#### fake: ZipcodeInState

Aliases:  zipcode_in_state, zipcodeinstate

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.ZipcodeInState}}
        block_example:
          fake: ZipcodeInState

Outputs:

    Example(id=1, inline_example=97914, block_example=62068)

#### fake: ZipcodePlus4

Aliases:  zipcode_plus4, zipcodeplus4

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/address/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.ZipcodePlus4}}
        block_example:
          fake: ZipcodePlus4

Outputs:

    Example(id=1, inline_example=76966-3579, block_example=66651-2282)

### Automotive Fakers

#### fake: LicensePlate

Generate a license plate.

Aliases:  license_plate, licenseplate

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/automotive/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LicensePlate}}
        block_example:
          fake: LicensePlate

Outputs:

    Example(id=1, inline_example=938 NK7, block_example=40-Q801)

### Bank Fakers

#### fake: BankCountry

Generate the bank provider's ISO 3166-1 alpha-2 country code.

Aliases:  bank_country, bankcountry

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/bank/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.BankCountry}}
        block_example:
          fake: BankCountry

Outputs:

    Example(id=1, inline_example=GB, block_example=GB)

#### fake: Bban

Generate a Basic Bank Account Number (BBAN).

Aliases:  bban

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/bank/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Bban}}
        block_example:
          fake: Bban

Outputs:

    Example(id=1, inline_example=FBTV47112201868483, block_example=GVSN94775159179533)

#### fake: Iban

Generate an International Bank Account Number (IBAN).

Aliases:  iban

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/bank/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Iban}}
        block_example:
          fake: Iban

Outputs:

    Example(id=1, inline_example=GB68FBTV47112201868483, block_example=GB71GVSN94775159179533)

#### fake: Swift

Generate a SWIFT code.

SWIFT codes, reading from left to right, are composed of a 4 alphabet
character bank code, a 2 alphabet character country code, a 2
alphanumeric location code, and an optional 3 alphanumeric branch code.
This means SWIFT codes can only have 8 or 11 characters, so the value of
``length`` can only be ``None`` or the integers ``8`` or ``11``. If the
value is ``None``, then a value of ``8`` or ``11`` will randomly be
assigned.

Because all 8-digit SWIFT codes already refer to the primary branch or
office, the ``primary`` argument only has an effect if the value of
``length`` is ``11``. If ``primary`` is ``True`` and ``length`` is
``11``, the 11-digit SWIFT codes generated will always end in ``'XXX'``
to denote that they belong to primary branches/offices.

For extra authenticity, localized providers may opt to include SWIFT
bank codes, location codes, and branch codes used in their respective
locales. If ``use_dataset`` is ``True``, this method will generate SWIFT
codes based on those locale-specific codes if included. If those codes
were not included, then it will behave as if ``use_dataset`` were
``False``, and in that mode, all those codes will just be randomly
generated as per the specification.

Aliases:  swift

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/bank/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift}}
        block_example:
          fake: Swift

Outputs:

    Example(id=1, inline_example=VKPRGBGW, block_example=KTUGGB9427Q)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift(length=8)}}
        block_example:
          fake.Swift:
            length: 8

Outputs:

    Example(id=1, inline_example=BZRAGBFZ, block_example=WZVUGBA5)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift(length=8, use_dataset=True)}}
        block_example:
          fake.Swift:
            length: 8
            use_dataset: true

Outputs:

    Example(id=1, inline_example=KHXKGBEM, block_example=SHHZGBJ8)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift(length=11)}}
        block_example:
          fake.Swift:
            length: 11

Outputs:

    Example(id=1, inline_example=OCCKGB65GT9, block_example=JWDRGBV8N9S)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift(length=11, primary=True)}}
        block_example:
          fake.Swift:
            length: 11
            primary: true

Outputs:

    Example(id=1, inline_example=OCTZGBYUXXX, block_example=SHJFGBMLXXX)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift(length=11, use_dataset=True)}}
        block_example:
          fake.Swift:
            length: 11
            use_dataset: true

Outputs:

    Example(id=1, inline_example=BTVIGB4EFIJ, block_example=BCWRGBZ7R7P)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift(length=11, primary=True, use_dataset=True)}}
        block_example:
          fake.Swift:
            length: 11
            primary: true
            use_dataset: true

Outputs:

    Example(id=1, inline_example=GVSNGBR2XXX, block_example=PVUWGBWFXXX)

#### fake: Swift11

Generate an 11-digit SWIFT code.

This method uses |swift| under the hood with the ``length`` argument set
to ``11``. If ``primary`` is set to ``True``, the SWIFT code will always
end with ``'XXX'``. All 11-digit SWIFT codes use this convention to
refer to the primary branch/office.

Aliases:  swift11

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/bank/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift11}}
        block_example:
          fake: Swift11

Outputs:

    Example(id=1, inline_example=TPKHGBUEMOP, block_example=ZEZRGB2FFU6)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift11(use_dataset=True)}}
        block_example:
          fake.Swift11:
            use_dataset: true

Outputs:

    Example(id=1, inline_example=PDJRGBSH9V8, block_example=GZTRGBS2FYU)

#### fake: Swift8

Generate an 8-digit SWIFT code.

This method uses |swift| under the hood with the ``length`` argument set
to ``8`` and with the ``primary`` argument omitted. All 8-digit SWIFT
codes already refer to the primary branch/office.

Aliases:  swift8

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/bank/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift8}}
        block_example:
          fake: Swift8

Outputs:

    Example(id=1, inline_example=XCVKGB49, block_example=DLNKGBN9)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Swift8(use_dataset=True)}}
        block_example:
          fake.Swift8:
            use_dataset: true

Outputs:

    Example(id=1, inline_example=POQIGBD9, block_example=ACXMGBA5)

### Barcode Fakers

#### fake: Ean

Generate an EAN barcode of the specified ``length``.

The value of ``length`` can only be ``8`` or ``13`` (default) which will
create an EAN-8 or an EAN-13 barcode respectively.

If a value for ``prefixes`` is specified, the result will begin with one
of the sequences in ``prefixes``.

Aliases:  ean

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/barcode/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ean(length=13)}}
        block_example:
          fake.Ean:
            length: 13

Outputs:

    Example(id=1, inline_example=1858398947198, block_example=6593423209470)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ean(length=8)}}
        block_example:
          fake.Ean:
            length: 8

Outputs:

    Example(id=1, inline_example=11220183, block_example=68483395)

#### fake: Ean13

Generate an EAN-13 barcode.

If ``leading_zero`` is ``True``, the leftmost digit of the barcode will
be set to ``0``. If ``False``, the leftmost digit cannot be ``0``. If
``None`` (default), the leftmost digit can be any digit.

If a value for ``prefixes`` is specified, the result will begin with one
of the sequences in ``prefixes`` and will ignore ``leading_zero``.

This method uses the standard barcode provider's |ean13| under the
hood with the ``prefixes`` argument set to the correct value to attain
the behavior described above.

.. note::
EAN-13 barcode that starts with a zero can be converted to UPC-A
by dropping the leading zero. This may cause problems with readers
that treat all of these code as UPC-A codes and drop the first digit
when reading it.

You can set the argument ``prefixes`` ( or ``leading_zero`` for
convenience) explicitly to avoid or to force the generated barcode to
start with a zero. You can also generate actual UPC-A barcode with
|EnUsBarcodeProvider.upc_a|.

Aliases:  ean13

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/barcode/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ean13}}
        block_example:
          fake: Ean13

Outputs:

    Example(id=1, inline_example=1858398947198, block_example=6593423209470)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ean13(leading_zero=False)}}
        block_example:
          fake.Ean13:
            leading_zero: false

Outputs:

    Example(id=1, inline_example=2220186848335, block_example=5751591795336)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ean13(leading_zero=True)}}
        block_example:
          fake.Ean13:
            leading_zero: true

Outputs:

    Example(id=1, inline_example=135256012306, block_example=0139916151091)

#### fake: Ean8

Generate an EAN-8 barcode.

This method uses |ean| under the hood with the ``length`` argument
explicitly set to ``8``.

If a value for ``prefixes`` is specified, the result will begin with one
of the sequences in ``prefixes``.

Aliases:  ean8

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/barcode/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ean8}}
        block_example:
          fake: Ean8

Outputs:

    Example(id=1, inline_example=80160977, block_example=53513939)

#### fake: LocalizedEan

Generate a localized EAN barcode of the specified ``length``.

The value of ``length`` can only be ``8`` or ``13`` (default) which will
create an EAN-8 or an EAN-13 barcode respectively.

This method uses the standard barcode provider's |ean| under the hood
with the ``prefixes`` argument explicitly set to ``local_prefixes`` of
a localized barcode provider implementation.

Aliases:  localized_ean, localizedean

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/barcode/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LocalizedEan}}
        block_example:
          fake: LocalizedEan

Outputs:

    Example(id=1, inline_example=301609753510, block_example=0432871158717)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LocalizedEan(length=13)}}
        block_example:
          fake.LocalizedEan:
            length: 13

Outputs:

    Example(id=1, inline_example=118583989473, block_example=0759342320948)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LocalizedEan(length=8)}}
        block_example:
          fake.LocalizedEan:
            length: 8

Outputs:

    Example(id=1, inline_example=10220184, block_example=13483395)

#### fake: LocalizedEan13

Generate a localized EAN-13 barcode.

This method uses |localized_ean| under the hood with the ``length``
argument explicitly set to ``13``.

Aliases:  localized_ean13, localizedean13

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/barcode/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LocalizedEan13}}
        block_example:
          fake: LocalizedEan13

Outputs:

    Example(id=1, inline_example=948418583985, block_example=0019659342324)

#### fake: LocalizedEan8

Generate a localized EAN-8 barcode.

This method uses |localized_ean| under the hood with the ``length``
argument explicitly set to ``8``.

Aliases:  localized_ean8, localizedean8

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/barcode/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LocalizedEan8}}
        block_example:
          fake: LocalizedEan8

Outputs:

    Example(id=1, inline_example=7016097, block_example=03513934)

#### fake: UpcA

Generate a 12-digit UPC-A barcode.

The value of ``upc_ae_mode`` controls how barcodes will be generated. If
``False`` (default), barcodes are not guaranteed to have a UPC-E
equivalent. In this mode, the method uses |EnUsBarcodeProvider.ean13|
under the hood, and the values of ``base`` and ``number_system_digit``
will be ignored.

If ``upc_ae_mode`` is ``True``, the resulting barcodes are guaranteed to
have a UPC-E equivalent, and the values of ``base`` and
``number_system_digit`` will be used to control what is generated.

Under this mode, ``base`` is expected to have a 6-digit string value. If
any other value is supplied, a random 6-digit string will be used
instead. As for ``number_system_digit``, the expected value is a ``0``
or a ``1``. If any other value is provided, this method will randomly
choose from the two.

.. important::
When ``upc_ae_mode`` is enabled, you might encounter instances where
different values of ``base`` (e.g. ``'120003'`` and ``'120004'``)
produce the same UPC-A barcode. This is normal, and the reason lies
within the whole conversion process. To learn more about this and
what ``base`` and ``number_system_digit`` actually represent, please
refer to |EnUsBarcodeProvider.upc_e|.

Aliases:  upc_a, upca

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/barcode/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcA}}
        block_example:
          fake: UpcA

Outputs:

    Example(id=1, inline_example=604876475933, block_example=219489241150)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcA(upc_ae_mode=True, number_system_digit=0)}}
        block_example:
          fake.UpcA:
            upc_ae_mode: true
            number_system_digit: 0

Outputs:

    Example(id=1, inline_example=81565000094, block_example=038770000081)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcA(upc_ae_mode=True, number_system_digit=1)}}
        block_example:
          fake.UpcA:
            upc_ae_mode: true
            number_system_digit: 1

Outputs:

    Example(id=1, inline_example=108000000164, block_example=197100005353)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcA(upc_ae_mode=True, base='123456', number_system_digit=0)}}
        block_example:
          fake.UpcA:
            upc_ae_mode: true
            base: '123456'
            number_system_digit: 0

Outputs:

    Example(id=1, inline_example=12345000065, block_example=039332000082)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcA(upc_ae_mode=True, base='120003', number_system_digit=0)}}
        block_example:
          fake.UpcA:
            upc_ae_mode: true
            base: '120003'
            number_system_digit: 0

Outputs:

    Example(id=1, inline_example=12000000003, block_example=071158000075)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcA(upc_ae_mode=True, base='120004', number_system_digit=0)}}
        block_example:
          fake.UpcA:
            upc_ae_mode: true
            base: '120004'
            number_system_digit: 0

Outputs:

    Example(id=1, inline_example=12000000003, block_example=014841000082)

#### fake: UpcE

Generate an 8-digit UPC-E barcode.

UPC-E barcodes can be expressed in 6, 7, or 8-digit formats, but this
method uses the 8 digit format, since it is trivial to convert to the
other two formats. The first digit (starting from the left) is
controlled by ``number_system_digit``, and it can only be a ``0`` or a
``1``. The last digit is the check digit that is inherited from the
UPC-E barcode's UPC-A equivalent. The middle six digits are collectively
referred to as the ``base`` (for a lack of a better term).

On that note, this method uses ``base`` and ``number_system_digit`` to
first generate a UPC-A barcode for the check digit, and what happens
next depends on the value of ``safe_mode``. The argument ``safe_mode``
exists, because there are some UPC-E values that share the same UPC-A
equivalent. For example, any UPC-E barcode of the form ``abc0000d``,
``abc0003d``, and ``abc0004d`` share the same UPC-A value
``abc00000000d``, but that UPC-A value will only convert to ``abc0000d``
because of (a) how UPC-E is just a zero-suppressed version of UPC-A and
(b) the rules around the conversion.

If ``safe_mode`` is ``True`` (default), this method performs another set
of conversions to guarantee that the UPC-E barcodes generated can be
converted to UPC-A, and that UPC-A barcode can be converted back to the
original UPC-E barcode. Using the example above, even if the bases
``120003`` or ``120004`` are used, the resulting UPC-E barcode will
always use the base ``120000``.

If ``safe_mode`` is ``False``, then the ``number_system_digit``,
``base``, and the computed check digit will just be concatenated
together to produce the UPC-E barcode, and attempting to convert the
barcode to UPC-A and back again to UPC-E will exhibit the behavior
described above.

Aliases:  upc_e, upce

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/barcode/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcE}}
        block_example:
          fake: UpcE

Outputs:

    Example(id=1, inline_example=16604872, block_example=04759386)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcE(base='123456')}}
        block_example:
          fake.UpcE:
            base: '123456'

Outputs:

    Example(id=1, inline_example=11234562, block_example=02194899)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcE(base='123456', number_system_digit=0)}}
        block_example:
          fake.UpcE:
            base: '123456'
            number_system_digit: 0

Outputs:

    Example(id=1, inline_example=1234565, block_example=04115786)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcE(base='123456', number_system_digit=1)}}
        block_example:
          fake.UpcE:
            base: '123456'
            number_system_digit: 1

Outputs:

    Example(id=1, inline_example=11234562, block_example=11565933)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcE(base='120000', number_system_digit=0)}}
        block_example:
          fake.UpcE:
            base: '120000'
            number_system_digit: 0

Outputs:

    Example(id=1, inline_example=1200003, block_example=08778400)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcE(base='120003', number_system_digit=0)}}
        block_example:
          fake.UpcE:
            base: '120003'
            number_system_digit: 0

Outputs:

    Example(id=1, inline_example=1200003, block_example=08016946)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UpcE(base='120004', number_system_digit=0)}}
        block_example:
          fake.UpcE:
            base: '120004'
            number_system_digit: 0

Outputs:

    Example(id=1, inline_example=1200003, block_example=07535137)

### Color Fakers

#### fake: Color

Generate a color in a human-friendly way.

Under the hood, this method first creates a color represented in the HSV
color model and then converts it to the desired ``color_format``. The
argument ``hue`` controls the H value according to the following
rules:

- If the value is a number from ``0`` to ``360``, it will serve as the H
value of the generated color.
- If the value is a tuple/list of 2 numbers from 0 to 360, the color's H
value will be randomly selected from that range.
- If the value is a valid string, the color's H value will be randomly
selected from the H range corresponding to the supplied string. Valid
values are ``'monochrome'``, ``'red'``, ``'orange'``, ``'yellow'``,
``'green'``, ``'blue'``, ``'purple'``, and ``'pink'``.

The argument ``luminosity`` influences both S and V values and is
partially affected by ``hue`` as well. The finer details of this
relationship are somewhat involved, so please refer to the source code
instead if you wish to dig deeper. To keep the interface simple, this
argument either can be omitted or can accept the following string
values:``'bright'``, ``'dark'``, ``'light'``, or ``'random'``.

The argument ``color_format`` controls in which color model the color is
represented. Valid values are ``'hsv'``, ``'hsl'``, ``'rgb'``, or
``'hex'`` (default).

Aliases:  color

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/color/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Color(hue='red')}}
        block_example:
          fake.Color:
            hue: red

Outputs:

    Example(id=1, inline_example=#e5909b, block_example=#ff977a)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Color(luminosity='light')}}
        block_example:
          fake.Color:
            luminosity: light

Outputs:

    Example(id=1, inline_example=#f7afed, block_example=#f2de7d)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Color(hue='orange', luminosity='bright')}}
        block_example:
          fake.Color:
            hue: orange
            luminosity: bright

Outputs:

    Example(id=1, inline_example=#cc9d04, block_example=#ba7112)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Color(hue=135, luminosity='dark', color_format='hsv')}}
        block_example:
          fake.Color:
            hue: 135
            luminosity: dark
            color_format: hsv

Outputs:

    Example(id=1, inline_example=hsv(135, 96, 54), block_example=hsv(135, 98, 57))

#### fake: ColorName

Generate a color name.

Aliases:  color_name, colorname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/color/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.ColorName}}
        block_example:
          fake: ColorName

Outputs:

    Example(id=1, inline_example=SlateBlue, block_example=PaleGreen)

#### fake: HexColor

Generate a color formatted as a hex triplet.

Aliases:  hex_color, hexcolor

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/color/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.HexColor}}
        block_example:
          fake: HexColor

Outputs:

    Example(id=1, inline_example=#0a5d30, block_example=#42485f)

#### fake: RgbColor

Generate a color formatted as a comma-separated RGB value.

Aliases:  rgb_color, rgbcolor

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/color/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RgbColor}}
        block_example:
          fake: RgbColor

Outputs:

    Example(id=1, inline_example=75,158,50, block_example=37,169,241)

#### fake: RgbCssColor

Generate a color formatted as a CSS rgb() function.

Aliases:  rgb_css_color, rgbcsscolor

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/color/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RgbCssColor}}
        block_example:
          fake: RgbCssColor

Outputs:

    Example(id=1, inline_example=rgb(75,158,50), block_example=rgb(37,169,241))

#### fake: SafeColorName

Generate a web-safe color name.

Aliases:  safe_color_name, safecolorname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/color/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SafeColorName}}
        block_example:
          fake: SafeColorName

Outputs:

    Example(id=1, inline_example=black, block_example=olive)

#### fake: SafeHexColor

Generate a web-safe color formatted as a hex triplet.

Aliases:  safe_hex_color, safehexcolor

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/color/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SafeHexColor}}
        block_example:
          fake: SafeHexColor

Outputs:

    Example(id=1, inline_example=#449933, block_example=#22aaff)

### Company Fakers

#### fake: Bs

Example: 'integrate extensible convergence'

Aliases:  bs

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/company/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Bs}}
        block_example:
          fake: Bs

Outputs:

    Example(id=1, inline_example=enable front-end channels, block_example=engineer mission-critical e-business)

#### fake: CompanySuffix

Example: 'Ltd'

Aliases:  company_suffix, companysuffix

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/company/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CompanySuffix}}
        block_example:
          fake: CompanySuffix

Outputs:

    Example(id=1, inline_example=Group, block_example=Group)

### Credit_Card Fakers

#### fake: CreditCardExpire

Generate a credit card expiry date.

This method uses |date_time_between| under the hood to generate the
expiry date, so the ``start`` and ``end`` arguments work in the same way
here as it would in that method. For the actual formatting of the expiry
date, |strftime| is used and ``date_format`` is simply passed
to that method.

Aliases:  credit_card_expire, creditcardexpire

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/credit_card/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CreditCardExpire}}
        block_example:
          fake: CreditCardExpire

Outputs:

    Example(id=1, inline_example=09/29, block_example=05/28)

#### fake: CreditCardFull

Generate a set of credit card details.

Aliases:  credit_card_full, creditcardfull

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/credit_card/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CreditCardFull}}
        block_example:
          fake: CreditCardFull

Outputs:

    Example(id=1, inline_example=Diners Club / Carte Blanche
    Vanessa Koch
    30515917953300 01/26
    CVC: 135
    , block_example=VISA 16 digit
    Ana Miranda
    4123098910139912 02/28
    CVC: 151
    )

#### fake: CreditCardNumber

Generate a valid credit card number.

Aliases:  credit_card_number, creditcardnumber

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/credit_card/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CreditCardNumber}}
        block_example:
          fake: CreditCardNumber

Outputs:

    Example(id=1, inline_example=180071965934238, block_example=4947112201868487)

#### fake: CreditCardProvider

Generate a credit card provider name.

Aliases:  credit_card_provider, creditcardprovider

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/credit_card/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CreditCardProvider}}
        block_example:
          fake: CreditCardProvider

Outputs:

    Example(id=1, inline_example=Diners Club / Carte Blanche, block_example=Discover)

#### fake: CreditCardSecurityCode

Generate a credit card security code.

Aliases:  credit_card_security_code, creditcardsecuritycode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/credit_card/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CreditCardSecurityCode}}
        block_example:
          fake: CreditCardSecurityCode

Outputs:

    Example(id=1, inline_example=924, block_example=157)

### Currency Fakers

#### fake: Cryptocurrency

Aliases:  cryptocurrency

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/currency/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Cryptocurrency}}
        block_example:
          fake: Cryptocurrency

Outputs:

    Example(id=1, inline_example=('USDT', 'Tether'), block_example=('ZEC', 'Zcash'))

#### fake: CryptocurrencyCode

Aliases:  cryptocurrency_code, cryptocurrencycode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/currency/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CryptocurrencyCode}}
        block_example:
          fake: CryptocurrencyCode

Outputs:

    Example(id=1, inline_example=USDT, block_example=ZEC)

#### fake: CryptocurrencyName

Aliases:  cryptocurrency_name, cryptocurrencyname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/currency/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CryptocurrencyName}}
        block_example:
          fake: CryptocurrencyName

Outputs:

    Example(id=1, inline_example=Tether, block_example=Zcash)

#### fake: Currency

Aliases:  currency

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/currency/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Currency}}
        block_example:
          fake: Currency

Outputs:

    Example(id=1, inline_example=('SDG', 'Sudanese pound'), block_example=('NGN', 'Nigerian naira'))

#### fake: CurrencyCode

Aliases:  currency_code, currencycode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/currency/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CurrencyCode}}
        block_example:
          fake: CurrencyCode

Outputs:

    Example(id=1, inline_example=SDG, block_example=NGN)

#### fake: CurrencyName

Aliases:  currency_name, currencyname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/currency/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CurrencyName}}
        block_example:
          fake: CurrencyName

Outputs:

    Example(id=1, inline_example=Sudanese pound, block_example=Nigerian naira)

#### fake: CurrencySymbol

Example:: $

Aliases:  currency_symbol, currencysymbol

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/currency/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CurrencySymbol}}
        block_example:
          fake: CurrencySymbol

Outputs:

    Example(id=1, inline_example=$, block_example=₦)

#### fake: Pricetag

Aliases:  pricetag

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/currency/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pricetag}}
        block_example:
          fake: Pricetag

Outputs:

    Example(id=1, inline_example=$1,784.08, block_example=$6.09)

### Date_Time Fakers

#### fake: AmPm

Aliases:  am_pm, ampm

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.AmPm}}
        block_example:
          fake: AmPm

Outputs:

    Example(id=1, inline_example=PM, block_example=PM)

#### fake: Century

Example: 'XVII'

Aliases:  century

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Century}}
        block_example:
          fake: Century

Outputs:

    Example(id=1, inline_example=XVI, block_example=XIII)

#### fake: Date

Get a date string between January 1, 1970 and now
:param pattern format
Example: '2008-11-27'

Aliases:  date

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Date}}
        block_example:
          fake: Date

Outputs:

    Example(id=1, inline_example=2003-01-25, block_example=1997-07-22)

#### fake: DateBetween

Get a Date object based on a random date between two given dates.
Accepts date strings that can be recognized by strtotime().

:param start_date Defaults to 30 years ago
:param end_date Defaults to "today"
Example: Date('1999-02-02')
:return Date

Aliases:  date_between, datebetween

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateBetween}}
        block_example:
          fake: DateBetween

Outputs:

    Example(id=1, inline_example=2000-04-03, block_example=2008-11-03)

#### fake: DateBetweenDates

Takes two Date objects and returns a random date between the two given dates.
Accepts Date or Datetime objects

:param date_start: Date
:param date_end: Date
:return Date

Aliases:  date_between_dates, datebetweendates

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateBetweenDates}}
        block_example:
          fake: DateBetweenDates

Outputs:

    Example(id=1, inline_example=2021-06-13, block_example=2021-06-13)

#### fake: DateObject

Get a date object between January 1, 1970 and now
Example: datetime.date(2016, 9, 20)

Aliases:  date_object, dateobject

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateObject}}
        block_example:
          fake: DateObject

Outputs:

    Example(id=1, inline_example=2003-01-25, block_example=1997-07-22)

#### fake: DateOfBirth

Generate a random date of birth represented as a Date object,
constrained by optional miminimum_age and maximum_age
parameters.

:param tzinfo Defaults to None.
:param minimum_age Defaults to 0.
:param maximum_age Defaults to 115.

Example: Date('1979-02-02')
:return Date

Aliases:  date_of_birth, dateofbirth

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateOfBirth}}
        block_example:
          fake: DateOfBirth

Outputs:

    Example(id=1, inline_example=1940-09-07, block_example=1975-01-12)

#### fake: DateThisCentury

Gets a Date object for the current century.

:param before_today: include days in current century before today
:param after_today: include days in current century after today
Example: Date('2012-04-04')
:return Date

Aliases:  date_this_century, datethiscentury

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateThisCentury}}
        block_example:
          fake: DateThisCentury

Outputs:

    Example(id=1, inline_example=2016-07-13, block_example=2013-10-11)

#### fake: DateThisDecade

Gets a Date object for the decade year.

:param before_today: include days in current decade before today
:param after_today: include days in current decade after today
Example: Date('2012-04-04')
:return Date

Aliases:  date_this_decade, datethisdecade

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateThisDecade}}
        block_example:
          fake: DateThisDecade

Outputs:

    Example(id=1, inline_example=2021-01-12, block_example=2020-11-10)

#### fake: DateThisMonth

Gets a Date object for the current month.

:param before_today: include days in current month before today
:param after_today: include days in current month after today
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('2012-04-04 11:02:02')
:return DateTime

Aliases:  date_this_month, datethismonth

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateThisMonth}}
        block_example:
          fake: DateThisMonth

Outputs:

    Example(id=1, inline_example=2021-06-01, block_example=2021-06-04)

#### fake: DateThisYear

Gets a Date object for the current year.

:param before_today: include days in current year before today
:param after_today: include days in current year after today
Example: Date('2012-04-04')
:return Date

Aliases:  date_this_year, datethisyear

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateThisYear}}
        block_example:
          fake: DateThisYear

Outputs:

    Example(id=1, inline_example=2021-04-10, block_example=2021-04-05)

#### fake: DateTime

Get a datetime object for a date between January 1, 1970 and now
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('2005-08-16 20:39:21')
:return datetime

Aliases:  date_time, datetime

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateTime}}
        block_example:
          fake: DateTime

Outputs:

    Example(id=1, inline_example=2003-01-25 19:09:38, block_example=1997-07-22 16:37:16)

#### fake: DateTimeAd

Get a datetime object for a date between January 1, 001 and now
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('1265-03-22 21:15:52')
:return datetime

Aliases:  date_time_ad, datetimead

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateTimeAd}}
        block_example:
          fake: DateTimeAd

Outputs:

    Example(id=1, inline_example=1877-01-02 08:15:53, block_example=0746-05-19 02:40:04)

#### fake: DateTimeBetween

Get a DateTime object based on a random date between two given dates.
Accepts date strings that can be recognized by strtotime().

:param start_date Defaults to 30 years ago
:param end_date Defaults to "now"
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('1999-02-02 11:42:52')
:return DateTime

Aliases:  date_time_between, datetimebetween

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateTimeBetween}}
        block_example:
          fake: DateTimeBetween

Outputs:

    Example(id=1, inline_example=2000-04-05 02:13:35, block_example=2008-11-05 06:55:21)

#### fake: DateTimeBetweenDates

Takes two DateTime objects and returns a random datetime between the two
given datetimes.
Accepts DateTime objects.

:param datetime_start: DateTime
:param datetime_end: DateTime
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('1999-02-02 11:42:52')
:return DateTime

Aliases:  date_time_between_dates, datetimebetweendates

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateTimeBetweenDates}}
        block_example:
          fake: DateTimeBetweenDates

Outputs:

    Example(id=1, inline_example=2021-06-13 14:05:53, block_example=2021-06-13 14:05:53)

#### fake: DateTimeThisCentury

Gets a DateTime object for the current century.

:param before_now: include days in current century before today
:param after_now: include days in current century after today
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('2012-04-04 11:02:02')
:return DateTime

Aliases:  date_time_this_century, datetimethiscentury

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateTimeThisCentury}}
        block_example:
          fake: DateTimeThisCentury

Outputs:

    Example(id=1, inline_example=2016-07-13 21:34:49, block_example=2013-10-11 08:18:38)

#### fake: DateTimeThisDecade

Gets a DateTime object for the decade year.

:param before_now: include days in current decade before today
:param after_now: include days in current decade after today
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('2012-04-04 11:02:02')
:return DateTime

Aliases:  date_time_this_decade, datetimethisdecade

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateTimeThisDecade}}
        block_example:
          fake: DateTimeThisDecade

Outputs:

    Example(id=1, inline_example=2021-01-12 10:20:55, block_example=2020-11-10 12:31:09)

#### fake: DateTimeThisMonth

Gets a DateTime object for the current month.

:param before_now: include days in current month before today
:param after_now: include days in current month after today
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('2012-04-04 11:02:02')
:return DateTime

Aliases:  date_time_this_month, datetimethismonth

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateTimeThisMonth}}
        block_example:
          fake: DateTimeThisMonth

Outputs:

    Example(id=1, inline_example=2021-06-12 19:04:24, block_example=2021-06-10 19:53:28)

#### fake: DateTimeThisYear

Gets a DateTime object for the current year.

:param before_now: include days in current year before today
:param after_now: include days in current year after today
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('2012-04-04 11:02:02')
:return DateTime

Aliases:  date_time_this_year, datetimethisyear

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DateTimeThisYear}}
        block_example:
          fake: DateTimeThisYear

Outputs:

    Example(id=1, inline_example=2021-04-10 06:42:46, block_example=2021-04-05 08:35:13)

#### fake: DayOfMonth

Aliases:  day_of_month, dayofmonth

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DayOfMonth}}
        block_example:
          fake: DayOfMonth

Outputs:

    Example(id=1, inline_example=25, block_example=22)

#### fake: DayOfWeek

Aliases:  day_of_week, dayofweek

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DayOfWeek}}
        block_example:
          fake: DayOfWeek

Outputs:

    Example(id=1, inline_example=Saturday, block_example=Tuesday)

#### fake: FutureDate

Get a Date object based on a random date between 1 day from now and a
given date.
Accepts date strings that can be recognized by strtotime().

:param end_date Defaults to "+30d"
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('1999-02-02 11:42:52')
:return DateTime

Aliases:  future_date, futuredate

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FutureDate}}
        block_example:
          fake: FutureDate

Outputs:

    Example(id=1, inline_example=2021-07-07, block_example=2021-07-03)

#### fake: FutureDatetime

Get a DateTime object based on a random date between 1 second form now
and a given date.
Accepts date strings that can be recognized by strtotime().

:param end_date Defaults to "+30d"
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('1999-02-02 11:42:52')
:return DateTime

Aliases:  future_datetime, futuredatetime

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FutureDatetime}}
        block_example:
          fake: FutureDatetime

Outputs:

    Example(id=1, inline_example=2021-07-07 04:14:42, block_example=2021-07-03 05:52:50)

#### fake: Iso8601

:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: '2003-10-21T16:05:52+0000'

Aliases:  iso8601

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Iso8601}}
        block_example:
          fake: Iso8601

Outputs:

    Example(id=1, inline_example=2003-01-25T19:09:38, block_example=1997-07-22T16:37:16)

#### fake: Month

Aliases:  month

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Month}}
        block_example:
          fake: Month

Outputs:

    Example(id=1, inline_example=1, block_example=07)

#### fake: MonthName

Aliases:  month_name, monthname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MonthName}}
        block_example:
          fake: MonthName

Outputs:

    Example(id=1, inline_example=January, block_example=July)

#### fake: PastDate

Get a Date object based on a random date between a given date and 1 day
ago.
Accepts date strings that can be recognized by strtotime().

:param start_date Defaults to "-30d"
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('1999-02-02 11:42:52')
:return DateTime

Aliases:  past_date, pastdate

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PastDate}}
        block_example:
          fake: PastDate

Outputs:

    Example(id=1, inline_example=2021-06-06, block_example=2021-06-02)

#### fake: PastDatetime

Get a DateTime object based on a random date between a given date and 1
second ago.
Accepts date strings that can be recognized by strtotime().

:param start_date Defaults to "-30d"
:param tzinfo: timezone, instance of datetime.tzinfo subclass
Example: DateTime('1999-02-02 11:42:52')
:return DateTime

Aliases:  past_datetime, pastdatetime

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PastDatetime}}
        block_example:
          fake: PastDatetime

Outputs:

    Example(id=1, inline_example=2021-06-07 04:14:41, block_example=2021-06-03 05:52:49)

#### fake: Pytimezone

Generate a random timezone (see `faker.timezone` for any args)
and return as a python object usable as a `tzinfo` to `datetime`
or other fakers.

Example: faker.pytimezone()
:return dateutil.tz.tz.tzfile

Aliases:  pytimezone

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pytimezone}}
        block_example:
          fake: Pytimezone

Outputs:

    Example(id=1, inline_example=tzfile('/usr/share/zoneinfo/Pacific/Funafuti'), block_example=tzfile('/usr/share/zoneinfo/Africa/Khartoum'))

#### fake: TimeDelta

Get a timedelta object

Aliases:  time_delta, timedelta

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.TimeDelta}}
        block_example:
          fake: TimeDelta

Outputs:

    Example(id=1, inline_example=0:00:00, block_example=0:00:00)

#### fake: TimeObject

Get a time object
Example: datetime.time(15, 56, 56, 772876)

Aliases:  time_object, timeobject

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.TimeObject}}
        block_example:
          fake: TimeObject

Outputs:

    Example(id=1, inline_example=19:09:38, block_example=16:37:16)

#### fake: TimeSeries

Returns a generator yielding tuples of ``(<datetime>, <value>)``.

The data points will start at ``start_date``, and be at every time interval specified by
``precision``.
``distrib`` is a callable that accepts ``<datetime>`` and returns ``<value>``

Aliases:  time_series, timeseries

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.TimeSeries}}
        block_example:
          fake: TimeSeries

Outputs:

    Example(id=1, inline_example=<generator object Provider.time_series at 0x106cc16d0>, block_example=<generator object Provider.time_series at 0x106cc16d0>)

#### fake: Timezone

Aliases:  timezone

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Timezone}}
        block_example:
          fake: Timezone

Outputs:

    Example(id=1, inline_example=Pacific/Funafuti, block_example=Africa/Khartoum)

#### fake: UnixTime

Get a timestamp between January 1, 1970 and now, unless passed
explicit start_datetime or end_datetime values.
Example: 1061306726

Aliases:  unix_time, unixtime

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/date_time/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UnixTime}}
        block_example:
          fake: UnixTime

Outputs:

    Example(id=1, inline_example=1043521778, block_example=869589436)

### Decorators.Py Fakers

#### fake: AsciiCompanyEmail

Aliases:  ascii_company_email, asciicompanyemail

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.AsciiCompanyEmail}}
        block_example:
          fake: AsciiCompanyEmail

Outputs:

    Example(id=1, inline_example=buckcourtney@tapia.com, block_example=vcrane@moon.com)

#### fake: AsciiEmail

Aliases:  ascii_email, asciiemail

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.AsciiEmail}}
        block_example:
          fake: AsciiEmail

Outputs:

    Example(id=1, inline_example=yodonnell@wiggins.info, block_example=alishawhitehead@gmail.com)

#### fake: AsciiFreeEmail

Aliases:  ascii_free_email, asciifreeemail

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.AsciiFreeEmail}}
        block_example:
          fake: AsciiFreeEmail

Outputs:

    Example(id=1, inline_example=edgar15@yahoo.com, block_example=lovefrances@yahoo.com)

#### fake: AsciiSafeEmail

Aliases:  ascii_safe_email, asciisafeemail

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.AsciiSafeEmail}}
        block_example:
          fake: AsciiSafeEmail

Outputs:

    Example(id=1, inline_example=edgar15@example.com, block_example=lovefrances@example.com)

#### fake: CompanyEmail

Aliases:  company_email, companyemail

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CompanyEmail}}
        block_example:
          fake: CompanyEmail

Outputs:

    Example(id=1, inline_example=buckcourtney@tapia.com, block_example=vcrane@moon.com)

#### fake: DomainName

Produce an Internet domain name with the specified number of
subdomain levels.

>>> domain_name()
nichols-phillips.com
>>> domain_name(2)
williamson-hopkins.jackson.com

Aliases:  domain_name, domainname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DomainName}}
        block_example:
          fake: DomainName

Outputs:

    Example(id=1, inline_example=vega.com, block_example=lyons.com)

#### fake: DomainWord

Aliases:  domain_word, domainword

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.DomainWord}}
        block_example:
          fake: DomainWord

Outputs:

    Example(id=1, inline_example=krause-wilcox, block_example=bautista)

#### fake: FreeEmail

Aliases:  free_email, freeemail

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FreeEmail}}
        block_example:
          fake: FreeEmail

Outputs:

    Example(id=1, inline_example=edgar15@yahoo.com, block_example=lovefrances@yahoo.com)

#### fake: FreeEmailDomain

Aliases:  free_email_domain, freeemaildomain

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FreeEmailDomain}}
        block_example:
          fake: FreeEmailDomain

Outputs:

    Example(id=1, inline_example=yahoo.com, block_example=yahoo.com)

#### fake: Hostname

Produce a hostname with specified number of subdomain levels.

>>> hostname()
db-01.nichols-phillips.com
>>> hostname(0)
laptop-56
>>> hostname(2)
web-12.williamson-hopkins.jackson.com

Aliases:  hostname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Hostname}}
        block_example:
          fake: Hostname

Outputs:

    Example(id=1, inline_example=lt-77.fowler.net, block_example=db-16.tapia.com)

#### fake: SafeDomainName

Aliases:  safe_domain_name, safedomainname

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SafeDomainName}}
        block_example:
          fake: SafeDomainName

Outputs:

    Example(id=1, inline_example=example.com, block_example=example.com)

#### fake: SafeEmail

Aliases:  safe_email, safeemail

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SafeEmail}}
        block_example:
          fake: SafeEmail

Outputs:

    Example(id=1, inline_example=edgar15@example.com, block_example=lovefrances@example.com)

#### fake: Slug

Django algorithm

Aliases:  slug

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/utils/decorators.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Slug}}
        block_example:
          fake: Slug

Outputs:

    Example(id=1, inline_example=discover-mother, block_example=father-challenge)

### File Fakers

#### fake: FileExtension

Generate a file extension under the specified ``category``.

If ``category`` is ``None``, a random category will be used. The list of
valid categories include: ``'audio'``, ``'image'``, ``'office'``,
``'text'``, and ``'video'``.

Aliases:  file_extension, fileextension

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/file/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FileExtension}}
        block_example:
          fake: FileExtension

Outputs:

    Example(id=1, inline_example=js, block_example=ods)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FileExtension(category='image')}}
        block_example:
          fake.FileExtension:
            category: image

Outputs:

    Example(id=1, inline_example=jpeg, block_example=png)

#### fake: FileName

Generate a random file name with extension.

If ``extension`` is ``None``, a random extension will be created under
the hood using |file_extension| with the specified ``category``. If a
value for ``extension`` is provided, the value will be used instead,
and ``category`` will be ignored. The actual name part itself is
generated using |word|.

:sample size=10:

Aliases:  file_name, filename

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/file/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FileName}}
        block_example:
          fake: FileName

Outputs:

    Example(id=1, inline_example=much.mp3, block_example=why.js)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FileName(category='audio')}}
        block_example:
          fake.FileName:
            category: audio

Outputs:

    Example(id=1, inline_example=me.mp3, block_example=past.mp3)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FileName(extension='abcdef')}}
        block_example:
          fake.FileName:
            extension: abcdef

Outputs:

    Example(id=1, inline_example=wait.abcdef, block_example=whatever.abcdef)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FileName(category='audio', extension='abcdef')}}
        block_example:
          fake.FileName:
            category: audio
            extension: abcdef

Outputs:

    Example(id=1, inline_example=discover.abcdef, block_example=mother.abcdef)

#### fake: FilePath

Generate an absolute pathname to a file.

This method uses |file_name| under the hood to generate the file name
itself, and ``depth`` controls the depth of the directory path, and
|word| is used under the hood to generate the different directory names.

:sample size=10:

Aliases:  file_path, filepath

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/file/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FilePath}}
        block_example:
          fake: FilePath

Outputs:

    Example(id=1, inline_example=/bit/force.avi, block_example=/marriage/give.wav)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FilePath(depth=3)}}
        block_example:
          fake.FilePath:
            depth: 3

Outputs:

    Example(id=1, inline_example=/popular/four/leader/health.mp4, block_example=/near/tree/level/me.png)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FilePath(depth=5, category='video')}}
        block_example:
          fake.FilePath:
            depth: 5
            category: video

Outputs:

    Example(id=1, inline_example=/address/whole/official/why/support/assume.mov, block_example=/still/thank/see/inside/though/serve.mp4)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.FilePath(depth=5, category='video', extension='abcdef')}}
        block_example:
          fake.FilePath:
            depth: 5
            category: video
            extension: abcdef

Outputs:

    Example(id=1, inline_example=/their/minute/population/ability/process/relate.abcdef, block_example=/score/gas/show/either/goal/trip.abcdef)

#### fake: MimeType

Generate a mime type under the specified ``category``.

If ``category`` is ``None``, a random category will be used. The list of
valid categories include ``'application'``, ``'audio'``, ``'image'``,
``'message'``, ``'model'``, ``'multipart'``, ``'text'``, and
``'video'``.

Aliases:  mime_type, mimetype

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/file/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MimeType}}
        block_example:
          fake: MimeType

Outputs:

    Example(id=1, inline_example=video/x-ms-wmv, block_example=model/vrml)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MimeType(category='application')}}
        block_example:
          fake.MimeType:
            category: application

Outputs:

    Example(id=1, inline_example=application/rss+xml, block_example=application/gzip)

#### fake: UnixDevice

Generate a Unix device file name.

If ``prefix`` is ``None``, a random prefix will be used. The list of
valid prefixes include: ``'sd'``, ``'vd'``, and ``'xvd'``.

Aliases:  unix_device, unixdevice

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/file/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UnixDevice}}
        block_example:
          fake: UnixDevice

Outputs:

    Example(id=1, inline_example=/dev/xvdp, block_example=/dev/vdz)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UnixDevice(prefix='mmcblk')}}
        block_example:
          fake.UnixDevice:
            prefix: mmcblk

Outputs:

    Example(id=1, inline_example=/dev/mmcblkj, block_example=/dev/mmcblkp)

#### fake: UnixPartition

Generate a Unix partition name.

This method uses |unix_device| under the hood to create a device file
name with the specified ``prefix``.

Aliases:  unix_partition, unixpartition

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/file/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UnixPartition}}
        block_example:
          fake: UnixPartition

Outputs:

    Example(id=1, inline_example=/dev/xvdg8, block_example=/dev/sdj2)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UnixPartition(prefix='mmcblk')}}
        block_example:
          fake.UnixPartition:
            prefix: mmcblk

Outputs:

    Example(id=1, inline_example=/dev/mmcblky1, block_example=/dev/mmcblkt4)

### Geo Fakers

#### fake: Coordinate

Optionally center the coord and pick a point within radius.

Aliases:  coordinate

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/geo/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Coordinate}}
        block_example:
          fake: Coordinate

Outputs:

    Example(id=1, inline_example=80.880444, block_example=37.397359)

#### fake: Latitude

Aliases:  latitude

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/geo/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Latitude}}
        block_example:
          fake: Latitude

Outputs:

    Example(id=1, inline_example=40.440222, block_example=18.6986795)

#### fake: Latlng

Aliases:  latlng

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/geo/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Latlng}}
        block_example:
          fake: Latlng

Outputs:

    Example(id=1, inline_example=(Decimal('66.6004235'), Decimal('-62.724453')), block_example=(Decimal('45.475847'), Decimal('-105.227997')))

#### fake: LocalLatlng

Returns a location known to exist on land in a country specified by `country_code`.
Defaults to 'en_US'. See the `land_coords` list for available locations/countries.

Aliases:  local_latlng, locallatlng

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/geo/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LocalLatlng}}
        block_example:
          fake: LocalLatlng

Outputs:

    Example(id=1, inline_example=('33.03699', '-117.29198', 'Encinitas', 'US', 'America/Los_Angeles'), block_example=('41.0051', '-73.78458', 'Scarsdale', 'US', 'America/New_York'))

#### fake: LocationOnLand

Returns a random tuple specifying a coordinate set guaranteed to exist on land.
Format is `(latitude, longitude, place name, two-letter country code, timezone)`
Pass `coords_only` to return coordinates without metadata.

Aliases:  location_on_land, locationonland

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/geo/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LocationOnLand}}
        block_example:
          fake: LocationOnLand

Outputs:

    Example(id=1, inline_example=('43.4125', '23.225', 'Montana', 'BG', 'Europe/Sofia'), block_example=('65.84811', '24.14662', 'Tornio', 'FI', 'Europe/Helsinki'))

#### fake: Longitude

Aliases:  longitude

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/geo/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Longitude}}
        block_example:
          fake: Longitude

Outputs:

    Example(id=1, inline_example=80.880444, block_example=37.397359)

### Internet Fakers

#### fake: Dga

Generates a domain name by given date
https://en.wikipedia.org/wiki/Domain_generation_algorithm

:type year: int
:type month: int
:type day: int
:type tld: str
:type length: int
:rtype: str

Aliases:  dga

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Dga}}
        block_example:
          fake: Dga

Outputs:

    Example(id=1, inline_example=rirpbubretascqucvnrhbyydewtmalpjievdbixsxknwnwelialvretierm.com, block_example=fctbfriciqlcbvrqhfsxrotu.com)

#### fake: HttpMethod

Returns random HTTP method
https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods

:rtype: str

Aliases:  http_method, httpmethod

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.HttpMethod}}
        block_example:
          fake: HttpMethod

Outputs:

    Example(id=1, inline_example=TRACE, block_example=OPTIONS)

#### fake: ImageUrl

Returns URL to placeholder image
Example: http://placehold.it/640x480

Aliases:  image_url, imageurl

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.ImageUrl}}
        block_example:
          fake: ImageUrl

Outputs:

    Example(id=1, inline_example=https://www.lorempixel.com/300/635, block_example=https://placeimg.com/151/676/any)

#### fake: Ipv4

Returns a random IPv4 address or network with a valid CIDR.

:param network: Network address
:param address_class: IPv4 address class (a, b, or c)
:param private: Public or private
:returns: IPv4

Aliases:  ipv4

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ipv4}}
        block_example:
          fake: Ipv4

Outputs:

    Example(id=1, inline_example=12.130.104.103, block_example=70.17.181.9)

#### fake: Ipv4NetworkClass

Returns a IPv4 network class 'a', 'b' or 'c'.

:returns: IPv4 network class

Aliases:  ipv4_network_class, ipv4networkclass

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ipv4NetworkClass}}
        block_example:
          fake: Ipv4NetworkClass

Outputs:

    Example(id=1, inline_example=b, block_example=b)

#### fake: Ipv4Private

Returns a private IPv4.

:param network: Network address
:param address_class: IPv4 address class (a, b, or c)
:returns: Private IPv4

Aliases:  ipv4_private, ipv4private

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ipv4Private}}
        block_example:
          fake: Ipv4Private

Outputs:

    Example(id=1, inline_example=10.128.66.93, block_example=192.168.75.62)

#### fake: Ipv4Public

Returns a public IPv4 excluding private blocks.

:param network: Network address
:param address_class: IPv4 address class (a, b, or c)
:returns: Public IPv4

Aliases:  ipv4_public, ipv4public

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ipv4Public}}
        block_example:
          fake: Ipv4Public

Outputs:

    Example(id=1, inline_example=48.8.75.189, block_example=198.165.159.67)

#### fake: Ipv6

Produce a random IPv6 address or network with a valid CIDR

Aliases:  ipv6

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ipv6}}
        block_example:
          fake: Ipv6

Outputs:

    Example(id=1, inline_example=23a7:711a:8133:2876:37eb:dcda:e87a:1613, block_example=1846:d424:c17c:6279:23c6:6130:4826:8673)

#### fake: MacAddress

Aliases:  mac_address, macaddress

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MacAddress}}
        block_example:
          fake: MacAddress

Outputs:

    Example(id=1, inline_example=07:2f:cc:00:fc:aa, block_example=7c:a6:20:61:71:7a)

#### fake: PortNumber

Returns a network port number
https://tools.ietf.org/html/rfc6335

:param is_system: System or well-known ports
:param is_user: User or registered ports
:param is_dynamic: Dynamic / private / ephemeral ports
:rtype: int

Aliases:  port_number, portnumber

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PortNumber}}
        block_example:
          fake: PortNumber

Outputs:

    Example(id=1, inline_example=53075, block_example=39755)

#### fake: Tld

Aliases:  tld

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Tld}}
        block_example:
          fake: Tld

Outputs:

    Example(id=1, inline_example=info, block_example=biz)

#### fake: Uri

Aliases:  uri

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Uri}}
        block_example:
          fake: Uri

Outputs:

    Example(id=1, inline_example=http://www.harding.info/home/, block_example=https://lowe.com/)

#### fake: UriExtension

Aliases:  uri_extension, uriextension

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UriExtension}}
        block_example:
          fake: UriExtension

Outputs:

    Example(id=1, inline_example=.jsp, block_example=.php)

#### fake: UriPage

Aliases:  uri_page, uripage

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UriPage}}
        block_example:
          fake: UriPage

Outputs:

    Example(id=1, inline_example=post, block_example=login)

#### fake: UriPath

Aliases:  uri_path, uripath

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UriPath}}
        block_example:
          fake: UriPath

Outputs:

    Example(id=1, inline_example=main, block_example=posts/explore/categories)

#### fake: Url

:param schemes: a list of strings to use as schemes, one will chosen randomly.
If None, it will generate http and https urls.
Passing an empty list will result in schemeless url generation like "://domain.com".

:returns: a random url string.

Aliases:  url

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/internet/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Url}}
        block_example:
          fake: Url

Outputs:

    Example(id=1, inline_example=https://fowler.net/, block_example=http://www.huber.com/)

### Isbn Fakers

#### fake: Isbn10

Aliases:  isbn10

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/isbn/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Isbn10}}
        block_example:
          fake: Isbn10

Outputs:

    Example(id=1, inline_example=1-115-87148-X, block_example=0-85839-894-X)

#### fake: Isbn13

Aliases:  isbn13

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/isbn/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Isbn13}}
        block_example:
          fake: Isbn13

Outputs:

    Example(id=1, inline_example=978-1-115-87148-8, block_example=978-0-85839-894-8)

### Job Fakers

#### fake: Job

Aliases:  job

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/job/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Job}}
        block_example:
          fake: Job

Outputs:

    Example(id=1, inline_example=Radiographer, diagnostic, block_example=Ophthalmologist)

### Lorem Fakers

#### fake: Paragraphs

Generate a list of paragraphs.

This method uses |paragraph| under the hood to generate paragraphs, and
the ``nb`` argument controls exactly how many sentences the list will
contain. The ``ext_word_list`` argument works in exactly the same way
as well.

Aliases:  paragraphs

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/lorem/__init__.py)

#### fake: Sentences

Generate a list of sentences.

This method uses |sentence| under the hood to generate sentences, and
the ``nb`` argument controls exactly how many sentences the list will
contain. The ``ext_word_list`` argument works in exactly the same way
as well.

Aliases:  sentences

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/lorem/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Sentences}}
        block_example:
          fake: Sentences

Outputs:

    Example(id=1, inline_example=['Bring TV program actually race.', 'Themselves true power home price check real.', 'Score from animal exactly drive well good.'], block_example=['Pull opportunity throughout take car.', 'Hold increase practice ability court.', 'Civil development large report purpose themselves.'])

#### fake: Texts

Generate a list of text strings.

The ``nb_texts`` argument controls how many text strings the list will
contain, and this method uses |text| under the hood for text generation,
so the two remaining arguments, ``max_nb_chars`` and ``ext_word_list``
will work in exactly the same way as well.



ext_word_list=['abc', 'def', 'ghi', 'jkl']

Aliases:  texts

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/lorem/__init__.py)

#### fake: Words

Generate a tuple of words.

The ``nb`` argument controls the number of words in the resulting list,
and if ``ext_word_list`` is provided, words from that list will be used
instead of those from the locale provider's built-in word list.

If ``unique`` is ``True``, this method will return a list containing
unique words. Under the hood, |random_sample| will be used for sampling
without replacement. If ``unique`` is ``False``, |random_choices| is
used instead, and the list returned may contain duplicates.

.. warning::
Depending on the length of a locale provider's built-in word list or
on the length of ``ext_word_list`` if provided, a large ``nb`` can
exhaust said lists if ``unique`` is ``True``, raising an exception.

Aliases:  words

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/lorem/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Words}}
        block_example:
          fake: Words

Outputs:

    Example(id=1, inline_example=['together', 'range', 'line'], block_example=['beyond', 'its', 'particularly'])

### Misc Fakers

#### fake: Binary

Generate a random binary blob of ``length`` bytes.

Aliases:  binary

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

#### fake: Boolean

Generate a random boolean value based on ``chance_of_getting_true``.

:sample size=10: chance_of_getting_true=25
:sample size=10: chance_of_getting_true=50
:sample size=10: chance_of_getting_true=75

Aliases:  boolean

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Boolean(chance_of_getting_true=25)}}
        block_example:
          fake.Boolean:
            chance_of_getting_true: 25

Outputs:

    Example(id=1, inline_example=False, block_example=0)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Boolean(chance_of_getting_true=50)}}
        block_example:
          fake.Boolean:
            chance_of_getting_true: 50

Outputs:

    Example(id=1, inline_example=True, block_example=0)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Boolean(chance_of_getting_true=75)}}
        block_example:
          fake.Boolean:
            chance_of_getting_true: 75

Outputs:

    Example(id=1, inline_example=True, block_example=1)

#### fake: Csv

Generate random comma-separated values.

For more information on the different arguments of this method, please refer to
:meth:`dsv() <faker.providers.misc.Provider.dsv>` which is used under the hood.


data_columns=('{{name}}', '{{address}}', '{{safe_color_name}}'),
num_rows=10, include_row_ids=True

Aliases:  csv

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

#### fake: Dsv

Generate random delimiter-separated values.

This method's behavior share some similarities with ``csv.writer``. The ``dialect`` and
``**fmtparams`` arguments are the same arguments expected by ``csv.writer`` to control its
behavior, and instead of expecting a file-like object to where output will be written, the
output is controlled by additional keyword arguments and is returned as a string.

The ``dialect`` argument defaults to ``'faker-csv'`` which is the name of a ``csv.excel``
subclass with full quoting enabled.

The ``header`` argument expects a list or a tuple of strings that will serve as the header row
if supplied. The ``data_columns`` argument expects a list or a tuple of string tokens, and these
string tokens will be passed to  :meth:`pystr_format() <faker.providers.python.Provider.pystr_format>`
for data generation. Argument Groups are used to pass arguments to the provider methods.
Both ``header`` and ``data_columns`` must be of the same length.

Example:
fake.set_arguments('top_half', {'min_value': 50, 'max_value': 100})
fake.dsv(data_columns=('{{ name }}', '{{ pyint:top_half }}'))

The ``num_rows`` argument controls how many rows of data to generate, and the ``include_row_ids``
argument may be set to ``True`` to include a sequential row ID column.

Aliases:  dsv

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

#### fake: FixedWidth

Generate random fixed width values.

Using a list of tuple records that is passed as ``data_columns``, that
defines the structure that will be generated. Arguments within the
record are provider specific, and should be a dictionary that will be
passed to the provider method.

Data Column List format
[('field width', 'definition', {'arguments'})]

The definition can be 'provider', 'provider:argument_group', tokenized
'string {{ provider:argument_group }}' that is passed to the python
provider method pystr_format() for generation, or a fixed '@word'.
Using Lists, Tuples, and Dicts as a definition for structure.

Argument Groups can be used to pass arguments to the provider methods,
but will override the arguments supplied in the tuple record.

Example:
fake.set_arguments('top_half', {'min_value': 50, 'max_value': 100})
fake.fixed_width(data_columns=[(20, 'name'), (3, 'pyint:top_half')])

:param data_columns: specification for the data structure
:type data_columns: list
:param num_rows: number of rows the generator will yield
:type num_rows: int
:param align: positioning of the value. (left, middle, right)
:type align: str
:return: Serialized Fixed Width data
:rtype: str

'max_value': 100})], align='right', num_rows=2

Aliases:  fixed_width, fixedwidth

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

#### fake: Json

Generate random JSON structure values.

Using a dictionary or list of records that is passed as ``data_columns``,
define the structure that is used to build JSON structures.  For complex
data structures it is recommended to use the dictionary format.

Data Column Dictionary format:
{'key name': 'definition'}

The definition can be 'provider', 'provider:argument_group', tokenized
'string {{ provider:argument_group }}' that is passed to the python
provider method pystr_format() for generation, or a fixed '@word'.
Using Lists, Tuples, and Dicts as a definition for structure.

Example:
fake.set_arguments('top_half', {'min_value': 50, 'max_value': 100})
fake.json(data_columns={'Name': 'name', 'Score': 'pyint:top_half'})

Data Column List format:
[('key name', 'definition', {'arguments'})]

With the list format the definition can be a list of records, to create
a list within the structure data.  For literal entries within the list,
set the 'field_name' to None.

:param data_columns: specification for the data structure
:type data_columns: dict
:param num_rows: number of rows the returned
:type num_rows: int
:param indent: number of spaces to indent the fields
:type indent: int
:return: Serialized JSON data
:rtype: str

'Details': {'Name': 'name', 'Address': 'address'}}, num_rows=2

num_rows=1

{'min_value': 50, 'max_value': 100})], num_rows=1

Aliases:  json

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

#### fake: Md5

Generate a random MD5 hash.

If ``raw_output`` is ``False`` (default), a hexadecimal string representation of the MD5 hash
will be returned. If ``True``, a ``bytes`` object representation will be returned instead.

Aliases:  md5

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Md5(raw_output=False)}}
        block_example:
          fake.Md5:
            raw_output: false

Outputs:

    Example(id=1, inline_example=0ced544422ae9d74b425752334506cb5, block_example=e2e862d8792e2235570eb2eb93f0b720)

#### fake: NullBoolean

Generate ``None``, ``True``, or ``False``, each with equal probability.

:sample size=15:

Aliases:  null_boolean, nullboolean

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.NullBoolean}}
        block_example:
          fake: NullBoolean

Outputs:

    Example(id=1, inline_example=False, block_example=False)

#### fake: Password

Generate a random password of the specified ``length``.

The arguments ``special_chars``, ``digits``, ``upper_case``, and ``lower_case`` control
what category of characters will appear in the generated password. If set to ``True``
(default), at least one character from the corresponding category is guaranteed to appear.
Special characters are characters from ``!@#$%^&*()_+``, digits are characters from
``0123456789``, and uppercase and lowercase characters are characters from the ASCII set of
letters.

Aliases:  password

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Password(length=12)}}
        block_example:
          fake.Password:
            length: 12

Outputs:

    Example(id=1, inline_example=z(1Bef!mR*(X, block_example=@tlUcamZ*+6$)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Password(length=40, special_chars=False, upper_case=False)}}
        block_example:
          fake.Password:
            length: 40
            special_chars: false
            upper_case: false

Outputs:

    Example(id=1, inline_example=xw1qpnplndj7l05cspcm15zaejah816i2ebe3whu, block_example=pfaqwxddz723q20eighlofdz9rfc2vpwgo4e71y7)

#### fake: Psv

Generate random pipe-separated values.

For more information on the different arguments of this method, please refer to
:meth:`dsv() <faker.providers.misc.Provider.dsv>` which is used under the hood.


data_columns=('{{name}}', '{{address}}', '{{safe_color_name}}'),
num_rows=10, include_row_ids=True

Aliases:  psv

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

#### fake: Sha1

Generate a random SHA1 hash.

If ``raw_output`` is ``False`` (default), a hexadecimal string representation of the SHA1 hash
will be returned. If ``True``, a ``bytes`` object representation will be returned instead.

Aliases:  sha1

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Sha1(raw_output=False)}}
        block_example:
          fake.Sha1:
            raw_output: false

Outputs:

    Example(id=1, inline_example=c6b69eb0fa28e2085eee479bb87f7bdfcee2e3b4, block_example=f57a6cb25f89722d7389101a0ef9f9547930c529)

#### fake: Sha256

Generate a random SHA256 hash.

If ``raw_output`` is ``False`` (default), a hexadecimal string representation of the SHA56 hash
will be returned. If ``True``, a ``bytes`` object representation will be returned instead.

Aliases:  sha256

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Sha256(raw_output=False)}}
        block_example:
          fake.Sha256:
            raw_output: false

Outputs:

    Example(id=1, inline_example=faa5be1206846743dec0c4d3e5afc2d48a023011fdb6eabcc842f2b47eca8a00, block_example=8e36506d1af0f8133ec6c833feb77689049fec2a0f7a49b8218fd49f41fde9d9)

#### fake: Tar

Generate a bytes object containing a random valid tar file.

The number and sizes of files contained inside the resulting archive can be controlled
using the following arguments:

- ``uncompressed_size`` - the total size of files before compression, 16 KiB by default
- ``num_files`` - the number of files archived in resulting zip file, 1 by default
- ``min_file_size`` - the minimum size of each file before compression, 4 KiB by default

No compression is used by default, but setting ``compression`` to one of the values listed
below will use the corresponding compression type.

- ``'bzip2'`` or ``'bz2'`` for BZIP2
- ``'lzma'`` or ``'xz'`` for LZMA
- ``'gzip'`` or ``'gz'`` for GZIP

Aliases:  tar

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

#### fake: Tsv

Generate random tab-separated values.

For more information on the different arguments of this method, please refer to
:meth:`dsv() <faker.providers.misc.Provider.dsv>` which is used under the hood.


data_columns=('{{name}}', '{{address}}', '{{safe_color_name}}'),
num_rows=10, include_row_ids=True

Aliases:  tsv

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

#### fake: Uuid4

Generate a random UUID4 object and cast it to another type if specified using a callable ``cast_to``.

By default, ``cast_to`` is set to ``str``.

May be called with ``cast_to=None`` to return a full-fledged ``UUID``.

Aliases:  uuid4

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Uuid4}}
        block_example:
          fake: Uuid4

Outputs:

    Example(id=1, inline_example=23a7711a-8133-4876-b7eb-dcd9e87a1613, block_example=1846d424-c17c-4279-a3c6-612f48268673)

#### fake: Zip

Generate a bytes object containing a random valid zip archive file.

The number and sizes of files contained inside the resulting archive can be controlled
using the following arguments:

- ``uncompressed_size`` - the total size of files before compression, 16 KiB by default
- ``num_files`` - the number of files archived in resulting zip file, 1 by default
- ``min_file_size`` - the minimum size of each file before compression, 4 KiB by default

No compression is used by default, but setting ``compression`` to one of the values listed
below will use the corresponding compression type.

- ``'bzip2'`` or ``'bz2'`` for BZIP2
- ``'lzma'`` or ``'xz'`` for LZMA
- ``'deflate'``, ``'gzip'``, or ``'gz'`` for GZIP

Aliases:  zip

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/misc/__init__.py)

### Person Fakers

#### fake: LanguageName

Generate a random i18n language name (e.g. English).

Aliases:  language_name, languagename

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LanguageName}}
        block_example:
          fake: LanguageName

Outputs:

    Example(id=1, inline_example=Ossetian, block_example=Macedonian)

#### fake: LastNameFemale

Aliases:  last_name_female, lastnamefemale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LastNameFemale}}
        block_example:
          fake: LastNameFemale

Outputs:

    Example(id=1, inline_example=Goodwin, block_example=Hendrix)

#### fake: LastNameMale

Aliases:  last_name_male, lastnamemale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LastNameMale}}
        block_example:
          fake: LastNameMale

Outputs:

    Example(id=1, inline_example=Goodwin, block_example=Hendrix)

#### fake: LastNameNonbinary

Aliases:  last_name_nonbinary, lastnamenonbinary

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LastNameNonbinary}}
        block_example:
          fake: LastNameNonbinary

Outputs:

    Example(id=1, inline_example=Goodwin, block_example=Hendrix)

#### fake: NameNonbinary

Aliases:  name_nonbinary, namenonbinary

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.NameNonbinary}}
        block_example:
          fake: NameNonbinary

Outputs:

    Example(id=1, inline_example=Lydia Escobar III, block_example=Edgar Moon II)

#### fake: Prefix

Aliases:  prefix

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Prefix}}
        block_example:
          fake: Prefix

Outputs:

    Example(id=1, inline_example=Mr., block_example=Ms.)

#### fake: PrefixFemale

Aliases:  prefix_female, prefixfemale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PrefixFemale}}
        block_example:
          fake: PrefixFemale

Outputs:

    Example(id=1, inline_example=Dr., block_example=Miss)

#### fake: PrefixMale

Aliases:  prefix_male, prefixmale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PrefixMale}}
        block_example:
          fake: PrefixMale

Outputs:

    Example(id=1, inline_example=Dr., block_example=Dr.)

#### fake: PrefixNonbinary

Aliases:  prefix_nonbinary, prefixnonbinary

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PrefixNonbinary}}
        block_example:
          fake: PrefixNonbinary

Outputs:

    Example(id=1, inline_example=Dr., block_example=Misc.)

#### fake: Suffix

Aliases:  suffix

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Suffix}}
        block_example:
          fake: Suffix

Outputs:

    Example(id=1, inline_example=DVM, block_example=V)

#### fake: SuffixFemale

Aliases:  suffix_female, suffixfemale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SuffixFemale}}
        block_example:
          fake: SuffixFemale

Outputs:

    Example(id=1, inline_example=DVM, block_example=PhD)

#### fake: SuffixMale

Aliases:  suffix_male, suffixmale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SuffixMale}}
        block_example:
          fake: SuffixMale

Outputs:

    Example(id=1, inline_example=DDS, block_example=V)

#### fake: SuffixNonbinary

Aliases:  suffix_nonbinary, suffixnonbinary

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/person/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SuffixNonbinary}}
        block_example:
          fake: SuffixNonbinary

Outputs:

    Example(id=1, inline_example=DDS, block_example=V)

### Phone_Number Fakers

#### fake: CountryCallingCode

Aliases:  country_calling_code, countrycallingcode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/phone_number/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.CountryCallingCode}}
        block_example:
          fake: CountryCallingCode

Outputs:

    Example(id=1, inline_example=+386, block_example=+1 670)

#### fake: Msisdn

https://en.wikipedia.org/wiki/MSISDN

Aliases:  msisdn

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/phone_number/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Msisdn}}
        block_example:
          fake: Msisdn

Outputs:

    Example(id=1, inline_example=9894719659342, block_example=2094711220186)

### Profile Fakers

#### fake: Profile

Generates a complete profile.
If "fields" is not empty, only the fields in the list will be returned

Aliases:  profile

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/profile/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Profile}}
        block_example:
          fake: Profile

Outputs:

    Example(id=1, inline_example={'job': 'Chartered loss adjuster', 'company': 'Landry Inc', 'ssn': '203-96-3622', 'residence': '16884 Mcgrath Overpass Apt. 615\nWest Paula, GA 57022', 'current_location': (Decimal('-38.4751525'), Decimal('12.479165')), 'blood_group': 'A-', 'website': ['http://johnston.biz/'], 'username': 'erikduncan', 'name': 'Mr. Eugene Pitts', 'sex': 'M', 'address': 'Unit 6582 Box 1972\nDPO AP 53704', 'mail': 'hnovak@yahoo.com', 'birthdate': datetime.date(1997, 11, 26)}, block_example={'job': 'IT trainer', 'company': 'Lamb-Walter', 'ssn': '687-26-8894', 'residence': 'PSC 0555, Box 0824\nAPO AP 20935', 'current_location': (Decimal('11.7384085'), Decimal('132.967921')), 'blood_group': 'AB+', 'website': ['http://www.church.com/', 'http://www.leonard.info/', 'https://www.church.info/', 'https://shepherd.com/'], 'username': 'yrubio', 'name': 'Ms. Jade Poole DVM', 'sex': 'F', 'address': 'Unit 9930 Box 0248\nDPO AP 33853', 'mail': 'curtis74@yahoo.com', 'birthdate': datetime.date(2010, 8, 1)})

#### fake: SimpleProfile

Generates a basic profile with personal informations

Aliases:  simple_profile, simpleprofile

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/profile/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.SimpleProfile}}
        block_example:
          fake: SimpleProfile

Outputs:

    Example(id=1, inline_example={'username': 'gkane', 'name': 'Tammie Harris', 'sex': 'F', 'address': 'USS George\nFPO AE 85294', 'mail': 'becky62@gmail.com', 'birthdate': datetime.date(1973, 12, 28)}, block_example={'username': 'qberry', 'name': 'Trevor Patterson', 'sex': 'M', 'address': 'USCGC Sosa\nFPO AP 22707', 'mail': 'colinhurley@hotmail.com', 'birthdate': datetime.date(1926, 12, 24)})

### Providers Fakers

#### fake: Bothify

Generate a string with each placeholder in ``text`` replaced according
to the following rules:

- Number signs ('#') are replaced with a random digit (0 to 9).
- Question marks ('?') are replaced with a random character from ``letters``.

By default, ``letters`` contains all ASCII letters, uppercase and lowercase.

Under the hood, this method uses :meth:`numerify() <faker.providers.BaseProvider.numerify>` and
and :meth:`lexify() <faker.providers.BaseProvider.lexify>` to generate random values for number
signs and question marks respectively.

Aliases:  bothify

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Bothify(letters='ABCDE')}}
        block_example:
          fake.Bothify:
            letters: ABCDE

Outputs:

    Example(id=1, inline_example=58 DA, block_example=48 CA)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: '${{fake.Bothify(text=''Product Number: ????-########'')}}'
        block_example:
          fake.Bothify:
            text: 'Product Number: ????-########'

Outputs:

    Example(id=1, inline_example=Product Number: CfMZ-85839894, block_example=Product Number: cNQq-65934232)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: '${{fake.Bothify(text=''Product Number: ????-########'', letters=''ABCDE'')}}'
        block_example:
          fake.Bothify:
            text: 'Product Number: ????-########'
            letters: ABCDE

Outputs:

    Example(id=1, inline_example=Product Number: DECE-71122018, block_example=Product Number: CACE-33969477)

#### fake: Hexify

Generate a string with each circumflex ('^') in ``text``
replaced with a random hexadecimal character.

By default, ``upper`` is set to False. If set to ``True``, output
will be formatted using uppercase hexadecimal characters.

Aliases:  hexify

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: '${{fake.Hexify(text=''MAC Address: ^^:^^:^^:^^:^^:^^'')}}'
        block_example:
          fake.Hexify:
            text: 'MAC Address: ^^:^^:^^:^^:^^:^^'

Outputs:

    Example(id=1, inline_example=MAC Address: 95:65:18:f2:24:41, block_example=MAC Address: 2c:87:6d:8e:fb:2a)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: '${{fake.Hexify(text=''MAC Address: ^^:^^:^^:^^:^^:^^'', upper=True)}}'
        block_example:
          fake.Hexify:
            text: 'MAC Address: ^^:^^:^^:^^:^^:^^'
            upper: true

Outputs:

    Example(id=1, inline_example=MAC Address: 3F:A6:70:83:7B:5A, block_example=MAC Address: D1:34:71:20:36:3C)

#### fake: LanguageCode

Generate a random i18n language code (e.g. en).

Aliases:  language_code, languagecode

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LanguageCode}}
        block_example:
          fake: LanguageCode

Outputs:

    Example(id=1, inline_example=pap, block_example=mn)

#### fake: Lexify

Generate a string with each question mark ('?') in ``text``
replaced with a random character from ``letters``.

By default, ``letters`` contains all ASCII letters, uppercase and lowercase.

Aliases:  lexify

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: '${{fake.Lexify(text=''Random Identifier: ??????????'')}}'
        block_example:
          fake.Lexify:
            text: 'Random Identifier: ??????????'

Outputs:

    Example(id=1, inline_example=Random Identifier: TemKopZjZI, block_example=Random Identifier: CffuGFgtJs)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: '${{fake.Lexify(text=''Random Identifier: ??????????'', letters=''ABCDE'')}}'
        block_example:
          fake.Lexify:
            text: 'Random Identifier: ??????????'
            letters: ABCDE

Outputs:

    Example(id=1, inline_example=Random Identifier: AECEBEEECD, block_example=Random Identifier: AEDCEBCBBB)

#### fake: Locale

Generate a random underscored i18n locale code (e.g. en_US).

Aliases:  locale

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Locale}}
        block_example:
          fake: Locale

Outputs:

    Example(id=1, inline_example=sw_KE, block_example=raj_IN)

#### fake: Numerify

Generate a string with each placeholder in ``text`` replaced according
to the following rules:

- Number signs ('#') are replaced with a random digit (0 to 9).
- Percent signs ('%') are replaced with a random non-zero digit (1 to 9).
- Exclamation marks ('!') are replaced with a random digit or an empty string.
- At symbols ('@') are replaced with a random non-zero digit or an empty string.

Under the hood, this method uses :meth:`random_digit() <faker.providers.BaseProvider.random_digit>`,
:meth:`random_digit_not_null() <faker.providers.BaseProvider.random_digit_not_null>`,
:meth:`random_digit_or_empty() <faker.providers.BaseProvider.random_digit_or_empty>`,
and :meth:`random_digit_not_null_or_empty() <faker.providers.BaseProvider.random_digit_not_null_or_empty>`
to generate the random values.

Aliases:  numerify

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Numerify(text='Intel Core i%-%%##K vs AMD Ryzen % %%##X')}}
        block_example:
          fake.Numerify:
            text: Intel Core i%-%%##K vs AMD Ryzen % %%##X

Outputs:

    Example(id=1, inline_example=Intel Core i6-3575K vs AMD Ryzen 7 7294X, block_example=Intel Core i3-4409K vs AMD Ryzen 8 7735X)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Numerify(text='!!! !!@ !@! !@@ @!! @!@ @@! @@@')}}
        block_example:
          fake.Numerify:
            text: '!!! !!@ !@! !@@ @!! @!@ @@! @@@'

Outputs:

    Example(id=1, inline_example=90 1 248 8  751 7 , block_example=4  61  7 926 81 6)

#### fake: RandomChoices

Generate a list of objects randomly sampled from ``elements`` with replacement.

For information on the ``elements`` and ``length`` arguments, please refer to
:meth:`random_elements() <faker.providers.BaseProvider.random_elements>` which
is used under the hood with the ``unique`` argument explicitly set to ``False``.



("a", 0.45),
("b", 0.35),
("c", 0.15),
("d", 0.05),
])

("a", 0.45),
("b", 0.35),
("c", 0.15),
("d", 0.05),
]), length=20

Aliases:  random_choices, randomchoices

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

#### fake: RandomDigit

Generate a random digit (0 to 9).

Aliases:  random_digit, randomdigit

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomDigit}}
        block_example:
          fake: RandomDigit

Outputs:

    Example(id=1, inline_example=7, block_example=6)

#### fake: RandomDigitNotNull

Generate a random non-zero digit (1 to 9).

Aliases:  random_digit_not_null, randomdigitnotnull

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomDigitNotNull}}
        block_example:
          fake: RandomDigitNotNull

Outputs:

    Example(id=1, inline_example=8, block_example=7)

#### fake: RandomDigitNotNullOrEmpty

Generate a random non-zero digit (1 to 9) or an empty string.

This method will return an empty string 50% of the time,
and each digit has a 1/18 chance of being generated.

:sample size=10:

Aliases:  random_digit_not_null_or_empty, randomdigitnotnullorempty

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomDigitNotNullOrEmpty}}
        block_example:
          fake: RandomDigitNotNullOrEmpty

Outputs:

    Example(id=1, inline_example=, block_example=2)

#### fake: RandomDigitOrEmpty

Generate a random digit (0 to 9) or an empty string.

This method will return an empty string 50% of the time,
and each digit has a 1/20 chance of being generated.

:sample size=10:

Aliases:  random_digit_or_empty, randomdigitorempty

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomDigitOrEmpty}}
        block_example:
          fake: RandomDigitOrEmpty

Outputs:

    Example(id=1, inline_example=8, block_example=)

#### fake: RandomElement

Generate a randomly sampled object from ``elements``.

For information on the ``elements`` argument, please refer to
:meth:`random_elements() <faker.providers.BaseProvider.random_elements>` which
is used under the hood with the ``unique`` argument set to ``False`` and the
``length`` argument set to ``1``.

:sample size=10: elements=OrderedDict([
("a", 0.45),
("b", 0.35),
("c", 0.15),
("d", 0.05),
])

Aliases:  random_element, randomelement

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

#### fake: RandomElements

Generate a list of randomly sampled objects from ``elements``.

Set ``unique`` to ``False`` for random sampling with replacement, and set ``unique`` to
``True`` for random sampling without replacement.

If ``length`` is set to ``None`` or is omitted, ``length`` will be set to a random
integer from 1 to the size of ``elements``.

The value of ``length`` cannot be greater than the number of objects
in ``elements`` if ``unique`` is set to ``True``.

The value of ``elements`` can be any sequence type (``list``, ``tuple``, ``set``,
``string``, etc) or an ``OrderedDict`` type. If it is the latter, the keys will be
used as the objects for sampling, and the values will be used as weighted probabilities
if ``unique`` is set to ``False``. For example:

.. code-block:: python

 # Random sampling with replacement
fake.random_elements(
elements=OrderedDict([
("variable_1", 0.5),        # Generates "variable_1" 50% of the time
("variable_2", 0.2),        # Generates "variable_2" 20% of the time
("variable_3", 0.2),        # Generates "variable_3" 20% of the time
("variable_4": 0.1),        # Generates "variable_4" 10% of the time
]), unique=False
)

 # Random sampling without replacement (defaults to uniform distribution)
fake.random_elements(
elements=OrderedDict([
("variable_1", 0.5),
("variable_2", 0.2),
("variable_3", 0.2),
("variable_4": 0.1),
]), unique=True
)





("a", 0.45),
("b", 0.35),
("c", 0.15),
("d", 0.05),
]), length=20, unique=False

("a", 0.45),
("b", 0.35),
("c", 0.15),
("d", 0.05),
]), unique=True

Aliases:  random_elements, randomelements

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

#### fake: RandomInt

Generate a random integer between two integers ``min`` and ``max`` inclusive
while observing the provided ``step`` value.

This method is functionally equivalent to randomly sampling an integer
from the sequence ``range(min, max + 1, step)``.

:sample size=10: min=0, max=15
:sample size=10: min=0, max=15, step=3

Aliases:  random_int, randomint

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomInt}}
        block_example:
          fake: RandomInt

Outputs:

    Example(id=1, inline_example=9558, block_example=3578)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomInt(min=0, max=15)}}
        block_example:
          fake.RandomInt:
            min: 0
            max: 15

Outputs:

    Example(id=1, inline_example=4, block_example=9)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomInt(min=0, max=15, step=3)}}
        block_example:
          fake.RandomInt:
            min: 0
            max: 15
            step: 3

Outputs:

    Example(id=1, inline_example=3, block_example=0)

#### fake: RandomLetter

Generate a random ASCII letter (a-z and A-Z).

Aliases:  random_letter, randomletter

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomLetter}}
        block_example:
          fake: RandomLetter

Outputs:

    Example(id=1, inline_example=G, block_example=F)

#### fake: RandomLetters

Generate a list of random ASCII letters (a-z and A-Z) of the specified ``length``.

Aliases:  random_letters, randomletters

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomLetters}}
        block_example:
          fake: RandomLetters

Outputs:

    Example(id=1, inline_example=['P', 'x', 'e', 'q', 'A', 'W', 'f', 'C', 'K', 'C', 'Q', 'C', 'Y', 'F', 'E', 'x'], block_example=['F', 'u', 'D', 'p', 'j', 'j', 'F', 'I', 'y', 'e', 'N', 'T', 'W', 'R', 'U', 'W'])

#### fake: RandomLowercaseLetter

Generate a random lowercase ASCII letter (a-z).

Aliases:  random_lowercase_letter, randomlowercaseletter

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomLowercaseLetter}}
        block_example:
          fake: RandomLowercaseLetter

Outputs:

    Example(id=1, inline_example=q, block_example=p)

#### fake: RandomNumber

Generate a random integer according to the following rules:

- If ``digits`` is ``None`` (default), its value will be set to a random
integer from 1 to 9.
- If ``fix_len`` is ``False`` (default), all integers that do not exceed
the number of ``digits`` can be generated.
- If ``fix_len`` is ``True``, only integers with the exact number of
``digits`` can be generated.

Aliases:  random_number, randomnumber

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomNumber(fix_len=False)}}
        block_example:
          fake.RandomNumber:
            fix_len: false

Outputs:

    Example(id=1, inline_example=67013, block_example=54349339)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomNumber(fix_len=True)}}
        block_example:
          fake.RandomNumber:
            fix_len: true

Outputs:

    Example(id=1, inline_example=72468, block_example=711720)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomNumber(digits=3)}}
        block_example:
          fake.RandomNumber:
            digits: 3

Outputs:

    Example(id=1, inline_example=913, block_example=929)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomNumber(digits=3, fix_len=False)}}
        block_example:
          fake.RandomNumber:
            digits: 3
            fix_len: false

Outputs:

    Example(id=1, inline_example=223, block_example=516)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomNumber(digits=3, fix_len=True)}}
        block_example:
          fake.RandomNumber:
            digits: 3
            fix_len: true

Outputs:

    Example(id=1, inline_example=242, block_example=388)

#### fake: RandomSample

Generate a list of objects randomly sampled from ``elements`` without replacement.

For information on the ``elements`` and ``length`` arguments, please refer to
:meth:`random_elements() <faker.providers.BaseProvider.random_elements>` which
is used under the hood with the ``unique`` argument explicitly set to ``True``.

Aliases:  random_sample, randomsample

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

#### fake: RandomUppercaseLetter

Generate a random uppercase ASCII letter (A-Z).

Aliases:  random_uppercase_letter, randomuppercaseletter

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomUppercaseLetter}}
        block_example:
          fake: RandomUppercaseLetter

Outputs:

    Example(id=1, inline_example=Q, block_example=P)

#### fake: RandomizeNbElements

Generate a random integer near ``number`` according to the following rules:

- If ``le`` is ``False`` (default), allow generation up to 140% of ``number``.
If ``True``, upper bound generation is capped at 100%.
- If ``ge`` is ``False`` (default), allow generation down to 60% of ``number``.
If ``True``, lower bound generation is capped at 100%.
- If a numerical value for ``min`` is provided, generated values less than ``min``
will be clamped at ``min``.
- If a numerical value for ``max`` is provided, generated values greater than
``max`` will be clamped at ``max``.
- If both ``le`` and ``ge`` are ``True``, the value of ``number`` will automatically
be returned, regardless of the values supplied for ``min`` and ``max``.

Aliases:  randomize_nb_elements, randomizenbelements

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomizeNbElements(number=100)}}
        block_example:
          fake.RandomizeNbElements:
            number: 100

Outputs:

    Example(id=1, inline_example=109, block_example=113)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomizeNbElements(number=100, ge=True)}}
        block_example:
          fake.RandomizeNbElements:
            number: 100
            ge: true

Outputs:

    Example(id=1, inline_example=102, block_example=116)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomizeNbElements(number=100, ge=True, min=120)}}
        block_example:
          fake.RandomizeNbElements:
            number: 100
            ge: true
            min: 120

Outputs:

    Example(id=1, inline_example=132, block_example=131)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomizeNbElements(number=100, le=True)}}
        block_example:
          fake.RandomizeNbElements:
            number: 100
            le: true

Outputs:

    Example(id=1, inline_example=85, block_example=79)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomizeNbElements(number=100, le=True, max=80)}}
        block_example:
          fake.RandomizeNbElements:
            number: 100
            le: true
            max: 80

Outputs:

    Example(id=1, inline_example=80, block_example=80)

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.RandomizeNbElements(number=79, le=True, ge=True, min=80)}}
        block_example:
          fake.RandomizeNbElements:
            number: 79
            le: true
            ge: true
            min: 80

Outputs:

    Example(id=1, inline_example=79, block_example=79)

### Python Fakers

#### fake: Pybool

Aliases:  pybool

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pybool}}
        block_example:
          fake: Pybool

Outputs:

    Example(id=1, inline_example=True, block_example=True)

#### fake: Pydecimal

Aliases:  pydecimal

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pydecimal}}
        block_example:
          fake: Pydecimal

Outputs:

    Example(id=1, inline_example=333018422.10356, block_example=935868384284.7)

#### fake: Pydict

Returns a dictionary.

:nb_elements: number of elements for dictionary
:variable_nb_elements: is use variable number of elements for dictionary
:value_types: type of dictionary values

Aliases:  pydict

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pydict}}
        block_example:
          fake: Pydict

Outputs:

    Example(id=1, inline_example={'however': 7230, 'issue': 'tXejffFiKWjvjXrBsGeN', 'across': -9.1092906014666, 'key': 'pNGCiKyJNmNoZgTcnBEu', 'should': 'MsTIkednBgSUNdSogBkf', 'wear': 'todd75@hotmail.com'}, block_example={'certainly': 'elarson@yahoo.com', 'close': datetime.datetime(1991, 8, 28, 21, 39, 37), 'candidate': Decimal('40561592774.2339'), 'same': Decimal('0.66363066127717'), 'camera': 165, 'I': datetime.datetime(1974, 7, 10, 19, 2, 25), 'institution': 'xdavis@gibson.com', 'perhaps': -19796477880609.9, 'management': 7110.96468809015, 'chair': 6293, 'opportunity': 'rHJhWhqkjsZwzLPwkKVb', 'relate': 'bridgetrivera@rich.com', 'firm': 'http://sherman-hartman.com/about.asp', 'health': 'qbrock@hotmail.com'})

#### fake: Pyfloat

Aliases:  pyfloat

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pyfloat}}
        block_example:
          fake: Pyfloat

Outputs:

    Example(id=1, inline_example=333018422.10356, block_example=935868384284.7)

#### fake: Pyint

Aliases:  pyint

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pyint}}
        block_example:
          fake: Pyint

Outputs:

    Example(id=1, inline_example=7961, block_example=6634)

#### fake: Pyiterable

Aliases:  pyiterable

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pyiterable}}
        block_example:
          fake: Pyiterable

Outputs:

    Example(id=1, inline_example=['tyronecervantes@schultz.info', -57431325491810.6, 1020, 'HgoRcbvzSLJhZvFucyhb', 'https://www.houston.com/category/', Decimal('78.8219282425171')], block_example={'jfrXgYsypWXHjZfEiUXP', Decimal('46809.968437303'), 'vLqkpyXPoDJPxuNwmxWh', 'mjtISFuKgpvWEpsmGHBt', 8328, 'zUXIDleQUOKvpfwDVWvf', 'cherylmcmahon@yahoo.com', 2036, Decimal('39529332399.3'), 'NGCiKyJNmNoZgTcnBEuf', Decimal('-33400472.39132'), 'brycewalls@strickland-blair.com', 'caldwellcaitlyn@lewis.com', 'MbxJbVYLedsbsaYQdUkk'})

#### fake: Pylist

Aliases:  pylist

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pylist}}
        block_example:
          fake: Pylist

Outputs:

    Example(id=1, inline_example=[1376, 'vfOMbxJbVYLedsbsaYQd', 'kkJWgatbFSjfrXgYsypW', datetime.datetime(2013, 4, 10, 18, 29, 48), 3015, 'http://quinn.com/', 'qmNpvcgbedvCMhvHextX', 'taYUwtXejffFiKWjvjXr', datetime.datetime(1979, 9, 14, 12, 49, 15), 7576, 'nfrost@johnson-benton.info', 'http://www.chavez-galvan.com/tags/tag/posts/home/', 'mariahhebert@yahoo.com'], block_example=['wongwhitney@smith.biz', datetime.datetime(2009, 7, 31, 3, 33, 54), 7284, 'MsTIkednBgSUNdSogBkf', 'todd75@hotmail.com', 'geraldorr@doyle.org', Decimal('-362.522405940924'), 3571, Decimal('-66131725.1010359')])

#### fake: Pyset

Aliases:  pyset

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pyset}}
        block_example:
          fake: Pyset

Outputs:

    Example(id=1, inline_example={1376, 'nfrost@johnson-benton.info', 'taYUwtXejffFiKWjvjXr', 3015, 'mariahhebert@yahoo.com', datetime.datetime(1979, 9, 14, 12, 49, 15), datetime.datetime(2013, 4, 10, 18, 29, 48), 'kkJWgatbFSjfrXgYsypW', 'vfOMbxJbVYLedsbsaYQd', 'qmNpvcgbedvCMhvHextX', 'http://www.chavez-galvan.com/tags/tag/posts/home/', 7576, 'http://quinn.com/'}, block_example={'geraldorr@doyle.org', Decimal('-362.522405940924'), 'wongwhitney@smith.biz', 'todd75@hotmail.com', 3571, 7284, Decimal('-66131725.1010359'), datetime.datetime(2009, 7, 31, 3, 33, 54), 'MsTIkednBgSUNdSogBkf'})

#### fake: Pystr

Generates a random string of upper and lowercase letters.
:type min_chars: int
:type max_chars: int
:return: String. Random of random length between min and max characters.

Aliases:  pystr

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pystr}}
        block_example:
          fake: Pystr

Outputs:

    Example(id=1, inline_example=GRmMglPrQfhKcDVBJbHF, block_example=DutYbbXjgkPWbwfnlHsj)

#### fake: PystrFormat

Aliases:  pystr_format, pystrformat

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.PystrFormat}}
        block_example:
          fake: PystrFormat

Outputs:

    Example(id=1, inline_example=C9-3877113u, block_example=U0-8018541q)

#### fake: Pystruct

Aliases:  pystruct

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pystruct}}
        block_example:
          fake: Pystruct

Outputs:

    Example(id=1, inline_example=(['AlnRDYPnKrQpTzKvYjZJ', 'ANuZspJKtvkFnBczSvFj', 'GaNPwqXmgqcYwhAuFFQU', 'AwPyLGMUlJalMplCUClp', 'HoHCECnIeqpwakSPaFAf', 'rfzpPsEjOgoRESSZZKyZ', 2775, Decimal('-624.560558663604'), 'ABtOefKYYukvkNLyvsML', 'efFduoNGEJBMQJHIrnoI'], {'more': 'PnYFlpEauZmcjxERRLrI', 'mean': -3380.60709450259, 'raise': 'IPUlkGTQQinWLLRJpTrX', 'woman': 'raymondjacobs@marks.com', 'per': 'qsingleton@hotmail.com', 'direction': 'dwiley@palmer-hays.info', 'medical': 'jimmy52@gmail.com', 'seem': 9318, 'opportunity': Decimal('7816622550.5122'), 'win': Decimal('-3055399609094.3')}, {'likely': {0: 'otXBHKVvOxrMFqEfVbdK', 1: ['WvWAepzTdCCTtyIlHxmm', 'http://singh.biz/homepage/', 'ExvmtRxZXngKbkpmxXzq'], 2: {0: 'pfksTjPmkHNctpoGaWXg', 1: datetime.datetime(1970, 1, 20, 18, 9, 53), 2: [datetime.datetime(2019, 3, 20, 4, 21, 19), 'EGoIizbIEqCmLUsPRhoy']}}, 'successful': {1: 'FUdbrbputMNKRmTxTqxZ', 2: ['QfOxRhpBHrJWrdsahIog', 'irASNEYAkztuzQCKWgLP', 'https://www.spears.com/register.asp'], 3: {1: 'djMgmkbszXrreHUJzGqs', 2: 1542, 3: ['JhDPmefptRyNmKYvScec', 'http://cantu.org/author/']}}, 'can': {2: 'melinda30@gmail.com', 3: [-2971150070.28733, 'HVGSTXNXIMWXYaEXHjir', datetime.datetime(1997, 10, 15, 7, 21, 19)], 4: {2: 'teHuAcZpKPitsiINHMev', 3: Decimal('-3903478892.99996'), 4: ['LXezkrcAngrgTKMZWpFz', 7.17977529165436]}}, 'identify': {3: 'dWgdfLgtXFbfFFDPiDnp', 4: ['http://graham-schmidt.com/main/main/tags/post.htm', 'nxUWoJCUpxEvvkMQHDTS', 'AdLsLrfTUwpuFoEGaiqF'], 5: {3: datetime.datetime(2001, 10, 23, 21, 7, 8), 4: 3321, 5: [994, 8248]}}, 'wrong': {4: 6262, 5: [9966, 3444, 131], 6: {4: 'fAHHfrlrKtqerPRHHTvu', 5: 'http://brennan-dudley.com/', 6: [-48.262033391978, 5463]}}, 'change': {5: 'tVTRrnfOuyedRDijsnha', 6: [7279, -88913121756.539, 'IapbxSUIRyeyLlgZxHZK'], 7: {5: 8851, 6: -60544431.5256728, 7: ['http://www.ferrell.com/terms.php', Decimal('-82.3137650741875')]}}, 'present': {6: 'txXhOTfqojIVkyCoOuft', 7: [datetime.datetime(1995, 12, 29, 0, 20, 55), 58853.2993449084, 32008793.30265], 8: {6: 'bwpcQfqQMwNnvQqPwKjx', 7: 'fjnOoffkdJBcFzUiJkFX', 8: ['VaTLcWeksUwSmKWCVxkR', datetime.datetime(2012, 1, 18, 15, 54, 31)]}}, 'lay': {7: 'natashaherring@watts.com', 8: ['https://hodges.biz/tags/categories/main/', Decimal('87.9261994045045'), 'qOVqzLNoDTdRKRUMIeDb'], 9: {7: 4196, 8: 'AXagmwKEFSdOlOWTBSAT', 9: [Decimal('-1073655449.14833'), 54071212.3645809]}}, 'benefit': {8: -263600384742.957, 9: ['KvGhYNQkRqrITJpQhXKD', 'tWlgjJBZhbcgRSJtyOBg', Decimal('-7.7640121431953')], 10: {8: Decimal('709.678338409695'), 9: 7476, 10: [993, 'kIMaXOkrryujudzakkqA']}}, 'front': {9: 'uaDZZmMjQFQJRhojglex', 10: [145, 'kKcaSVbnsEGYoutRkVIz', 'coUYiMyXVmWbhNoVvYFn'], 11: {9: 1787, 10: 'https://odom.net/main.htm', 11: ['AqBknmSuStqIvQHKYRrx', 'UCCelgqaAasfmInaQCTn']}}}), block_example=(['OXXtemWVJOLAoRkQGPSm', Decimal('28758635.2898326'), 2342, 4044, 'https://graves.org/tag/post/', 1771, 'QuuFCvjVCVBgORMsHOzL', 'NWrGYdSxVtcAWCmJCCml', 'anBHZZLtTIJqQsrEdbwv', 'https://www.hamilton.com/'], {'blue': 'WOFXuxIRpgblNdeqrKwf', 'modern': 'gmueller@gmail.com', 'teacher': 8893, 'account': 3187, 'finally': Decimal('-18247154934.426'), 'same': 6671, 'throw': 6331, 'public': 29116.8304143767, 'single': 'https://ritter-mccoy.com/register.html', 'discussion': 'WMxPLafnTuVegvMMkqgP'}, {'order': {0: 'http://ryan.com/login.jsp', 1: ['https://www.mccall-vasquez.org/posts/categories/search.jsp', 'ksMvjXWSzZdIbrDzwWTU', 'kItUrFRrgsosYSERAWnU'], 2: {0: 'http://www.jenkins-parks.com/', 1: -7529800541539.8, 2: ['CCjKyDWZFAYbiKqzGuEq', 'nKEYyQEsFUlHvhBFButr']}}, 'student': {1: 'YRGgRAEClCyUWZBpeboc', 2: [73334959.7930117, Decimal('-6339158106.71388'), 309050839.29914], 3: {1: 'lHHZBjvmeNaqyhUsNZpt', 2: 'usparks@hotmail.com', 3: ['http://melton-medina.org/category/', 5464]}}, 'executive': {2: Decimal('-49.438926121434'), 3: [datetime.datetime(1999, 11, 21, 5, 44, 5), 'pIaVGadFmrTOATEoYddU', datetime.datetime(1992, 9, 22, 15, 17, 11)], 4: {2: 'PMXrGVmaCwuuJBwJszrB', 3: 1657, 4: [datetime.datetime(2012, 6, 28, 13, 51, 49), 'jWQvXcFsPZpGHqpfXzKO']}}, 'kind': {3: 'http://www.haley-maldonado.com/categories/privacy.php', 4: ['http://bradley-meza.net/search/tags/search/faq/', 'https://www.archer-carpenter.com/posts/tag/list/privacy.php', datetime.datetime(1985, 7, 10, 19, 37, 21)], 5: {3: datetime.datetime(2020, 12, 3, 3, 58, 20), 4: 'YNTymfhoOgZcDDAiySnt', 5: [-86165295881087.6, datetime.datetime(1974, 5, 25, 6, 34, 53)]}}, 'quality': {4: 'http://www.sanders-floyd.com/main/category/login/', 5: [Decimal('5158295364.1217'), 'claysydney@yahoo.com', 1619], 6: {4: 'wallcathy@hinton.org', 5: 9137.47670418247, 6: [datetime.datetime(1984, 4, 3, 2, 1, 37), 'IMBQiNbnexoTcNTGkaeR']}}, 'allow': {5: 'HqGjPKBFwAArotfaNTrp', 6: ['UcjfsRbrWDqTNcTVzGvr', 'heidigutierrez@zimmerman.com', 'xUFsPmEXaEOCmTFvwTJZ'], 7: {5: 'drakesummer@martin.com', 6: Decimal('444.876804221886'), 7: ['jesusrandall@gonzalez.com', 'BauHMCILyGKBobSKTzkk']}}, 'strategy': {6: 'https://hess-hess.com/tag/main/', 7: ['qTwogmFkYTzXcIycKGJl', 'ChDHNOhInFURxoJlKkRc', 'TElVPSMBKzClsvCwVOOo'], 8: {6: -40890567296284.0, 7: 'sgRsEOKCiaERZhVVpyLl', 8: ['BPFYrPDkgzkucwtyQHrb', 'xYMJXbhlNScBWUZIslCE']}}, 'wide': {7: 'gWciUUeILqBHxDmntujX', 8: [-29858635883003.3, 'yeuUzLxzoJkVRnAXSfvt', 'OHnnxvKvUfhNTBCEQRqu'], 9: {7: datetime.datetime(2018, 7, 19, 3, 56, 29), 8: -0.1825490280262, 9: ['tdRlEWsCvfWThwaXErak', 'http://pope.info/search/homepage.jsp']}}, 'your': {8: 2326.8009205109, 9: ['SfBMDlzvgsZchSSfSSzj', Decimal('4.96204389699817'), 'http://foley.com/author/'], 10: {8: 8555, 9: 'barrross@yahoo.com', 10: ['EZJsaXKRmRpJDwnNKDkX', 'hxCMgjRxjMSiaLwRcDSz']}}, 'test': {9: Decimal('652198.966221436'), 10: ['KJQeIvLHqDNVUjvWFemp', 4734, 812], 11: {9: 'rmanning@mcmahon.com', 10: 'fbcYXXDheRDYkmOdIlIP', 11: [Decimal('-47753760363090.5'), 'yharmon@owen.com']}}}))

#### fake: Pytuple

Aliases:  pytuple

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/python/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Pytuple}}
        block_example:
          fake: Pytuple

Outputs:

    Example(id=1, inline_example=(1376, 'vfOMbxJbVYLedsbsaYQd', 'kkJWgatbFSjfrXgYsypW', datetime.datetime(2013, 4, 10, 18, 29, 48), 3015, 'http://quinn.com/', 'qmNpvcgbedvCMhvHextX', 'taYUwtXejffFiKWjvjXr', datetime.datetime(1979, 9, 14, 12, 49, 15), 7576, 'nfrost@johnson-benton.info', 'http://www.chavez-galvan.com/tags/tag/posts/home/', 'mariahhebert@yahoo.com'), block_example=('wongwhitney@smith.biz', datetime.datetime(2009, 7, 31, 3, 33, 54), 7284, 'MsTIkednBgSUNdSogBkf', 'todd75@hotmail.com', 'geraldorr@doyle.org', Decimal('-362.522405940924'), 3571, Decimal('-66131725.1010359')))

### Ssn Fakers

#### fake: Ein

Generate a random United States Employer Identification Number (EIN).

An United States An Employer Identification Number (EIN) is
also known as a Federal Tax Identification Number, and is
used to identify a business entity. EINs follow a format of a
two-digit prefix followed by a hyphen and a seven-digit sequence:
 ##-######

https://www.irs.gov/businesses/small-businesses-self-employed/employer-id-numbers

Aliases:  ein

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/ssn/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ein}}
        block_example:
          fake: Ein

Outputs:

    Example(id=1, inline_example=88-3664860, block_example=76-2336625)

#### fake: InvalidSsn

Generate a random invalid United States Social Security Identification Number (SSN).

Invalid SSNs have the following characteristics:
Cannot begin with the number 9
Cannot begin with 666 in positions 1 - 3
Cannot begin with 000 in positions 1 - 3
Cannot contain 00 in positions 4 - 5
Cannot contain 0000 in positions 6 - 9

https://www.ssa.gov/kc/SSAFactSheet--IssuingSSNs.pdf

Additionally, return an invalid SSN that is NOT a valid ITIN by excluding certain ITIN related "group" values

Aliases:  invalid_ssn, invalidssn

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/ssn/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.InvalidSsn}}
        block_example:
          fake: InvalidSsn

Outputs:

    Example(id=1, inline_example=516-00-4617, block_example=143-12-0000)

#### fake: Itin

Generate a random United States Individual Taxpayer Identification Number (ITIN).

An United States Individual Taxpayer Identification Number
(ITIN) is a tax processing number issued by the Internal
Revenue Service. It is a nine-digit number that always begins
with the number 9 and has a range of 70-88 in the fourth and
fifth digit. Effective April 12, 2011, the range was extended
to include 900-70-0000 through 999-88-9999, 900-90-0000
through 999-92-9999 and 900-94-0000 through 999-99-9999.
https://www.irs.gov/individuals/international-taxpayers/general-itin-information

Aliases:  itin

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/ssn/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Itin}}
        block_example:
          fake: Itin

Outputs:

    Example(id=1, inline_example=917-90-1553, block_example=932-94-8725)

#### fake: Ssn

Generate a random United States Taxpayer Identification Number of the specified type.

If no type is specified, a US SSN is returned.

Aliases:  ssn

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/ssn/en_US/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Ssn}}
        block_example:
          fake: Ssn

Outputs:

    Example(id=1, inline_example=289-18-1554, block_example=634-33-8726)

### User_Agent Fakers

#### fake: AndroidPlatformToken

Generate an Android platform token used in user agent strings.

Aliases:  android_platform_token, androidplatformtoken

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.AndroidPlatformToken}}
        block_example:
          fake: AndroidPlatformToken

Outputs:

    Example(id=1, inline_example=Android 1.5, block_example=Android 2.3.5)

#### fake: Chrome

Generate a Chrome web browser user agent string.

Aliases:  chrome

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Chrome}}
        block_example:
          fake: Chrome

Outputs:

    Example(id=1, inline_example=Mozilla/5.0 (X11; Linux i686) AppleWebKit/531.2 (KHTML, like Gecko) Chrome/63.0.818.0 Safari/531.2, block_example=Mozilla/5.0 (Linux; Android 4.4) AppleWebKit/535.0 (KHTML, like Gecko) Chrome/32.0.844.0 Safari/535.0)

#### fake: Firefox

Generate a Mozilla Firefox web browser user agent string.

Aliases:  firefox

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Firefox}}
        block_example:
          fake: Firefox

Outputs:

    Example(id=1, inline_example=Mozilla/5.0 (X11; Linux x86_64; rv:1.9.7.20) Gecko/2016-10-28 01:20:46 Firefox/12.0, block_example=Mozilla/5.0 (Macintosh; PPC Mac OS X 10 12_8; rv:1.9.5.20) Gecko/2010-01-10 11:18:29 Firefox/3.8)

#### fake: InternetExplorer

Generate an IE web browser user agent string.

Aliases:  internet_explorer, internetexplorer

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.InternetExplorer}}
        block_example:
          fake: InternetExplorer

Outputs:

    Example(id=1, inline_example=Mozilla/5.0 (compatible; MSIE 7.0; Windows 98; Trident/5.0), block_example=Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/5.0))

#### fake: IosPlatformToken

Generate an iOS platform token used in user agent strings.

Aliases:  ios_platform_token, iosplatformtoken

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.IosPlatformToken}}
        block_example:
          fake: IosPlatformToken

Outputs:

    Example(id=1, inline_example=iPhone; CPU iPhone OS 10_3_4 like Mac OS X, block_example=iPhone; CPU iPhone OS 7_1_2 like Mac OS X)

#### fake: LinuxPlatformToken

Generate a Linux platform token used in user agent strings.

Aliases:  linux_platform_token, linuxplatformtoken

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LinuxPlatformToken}}
        block_example:
          fake: LinuxPlatformToken

Outputs:

    Example(id=1, inline_example=X11; Linux x86_64, block_example=X11; Linux x86_64)

#### fake: LinuxProcessor

Generate a Linux processor token used in user agent strings.

Aliases:  linux_processor, linuxprocessor

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.LinuxProcessor}}
        block_example:
          fake: LinuxProcessor

Outputs:

    Example(id=1, inline_example=x86_64, block_example=x86_64)

#### fake: MacPlatformToken

Generate a MacOS platform token used in user agent strings.

Aliases:  mac_platform_token, macplatformtoken

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MacPlatformToken}}
        block_example:
          fake: MacPlatformToken

Outputs:

    Example(id=1, inline_example=Macintosh; U; Intel Mac OS X 10 7_4, block_example=Macintosh; Intel Mac OS X 10 6_5)

#### fake: MacProcessor

Generate a MacOS processor token used in user agent strings.

Aliases:  mac_processor, macprocessor

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.MacProcessor}}
        block_example:
          fake: MacProcessor

Outputs:

    Example(id=1, inline_example=U; PPC, block_example=U; Intel)

#### fake: Opera

Generate an Opera web browser user agent string.

Aliases:  opera

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Opera}}
        block_example:
          fake: Opera

Outputs:

    Example(id=1, inline_example=Opera/9.95.(X11; Linux x86_64; bhb-IN) Presto/2.9.162 Version/12.00, block_example=Opera/8.51.(X11; Linux i686; the-NP) Presto/2.9.186 Version/11.00)

#### fake: Safari

Generate a Safari web browser user agent string.

Aliases:  safari

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.Safari}}
        block_example:
          fake: Safari

Outputs:

    Example(id=1, inline_example=Mozilla/5.0 (Windows; U; Windows NT 6.1) AppleWebKit/535.16.7 (KHTML, like Gecko) Version/5.1 Safari/535.16.7, block_example=Mozilla/5.0 (iPod; U; CPU iPhone OS 3_0 like Mac OS X; fa-IR) AppleWebKit/531.47.3 (KHTML, like Gecko) Version/3.0.5 Mobile/8B112 Safari/6531.47.3)

#### fake: UserAgent

Generate a random web browser user agent string.

Aliases:  user_agent, useragent

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.UserAgent}}
        block_example:
          fake: UserAgent

Outputs:

    Example(id=1, inline_example=Mozilla/5.0 (Windows NT 5.0; the-NP; rv:1.9.1.20) Gecko/2016-08-28 10:17:44 Firefox/3.8, block_example=Mozilla/5.0 (Macintosh; Intel Mac OS X 10 5_8; rv:1.9.5.20) Gecko/2020-03-30 18:10:19 Firefox/3.8)

#### fake: WindowsPlatformToken

Generate a Windows platform token used in user agent strings.

Aliases:  windows_platform_token, windowsplatformtoken

Source: [faker](https://github.com/joke2k/faker/tree/master/faker/providers/user_agent/__init__.py)

##### Samples

Recipe:

    - var: snowfakery_locale
      value: en_US
    - object: Example
      fields:
        inline_example: ${{fake.WindowsPlatformToken}}
        block_example:
          fake: WindowsPlatformToken

Outputs:

    Example(id=1, inline_example=Windows NT 5.2, block_example=Windows NT 5.1)

