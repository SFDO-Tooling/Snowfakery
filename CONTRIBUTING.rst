.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/SFDO-Tooling/Snowfakery/issues.

When reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help wanted" is open to whomever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement" and "help wanted" is open to whomever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

Snowfakery could always use more documentation, whether as part of the official Snowfakery docs, in docstrings, or even on the web in blog posts, articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/SFDO-Tooling/Snowfakery/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up Snowfakery for local development.

1. Fork the Snowfakery repo on GitHub.
2. Clone your fork to your local workspace.
3. Create and activate fresh virtual environment using virtualenv.
(Google this if you don't know how). If you name your virtualenv
"myenv" then it will be ignored by by git due to our .gitignore file.
Or you could make it outside of the project repo.
4. Install development requirements::

    $ make dev-install

5. Install ``pre-commit`` hooks for ``black`` and ``flake8``::

    $ pre-commit install --install-hooks

6. After making changes, run the tests and make sure they all pass::

    $ pytest

7. Build the docs like this: 
    $ make docs
    $ open build/html/index.html

Set SF_MKDOCS_BUILD_LOCALES=False to skip building all locales

8. Your new code should also have meaningful tests. One way to double check that
   your tests cover everything is to ensure that your new code has test code coverage:

   $ pytest --cov

   or

   $ pytest --cov --cov-report=html

8. Push your changes to GitHub and submit a pull request. The base branch should 
be a new feature branch that we create to receive the changes (contact us to create 
the branch). This allows us to test the changes using our build system before 
merging to main.

Note that we enable typeguard with pytest so if you add type declarations to your 
code, those declarations will be treated as runtime assertions in your python
tests. MyPy validation is also on our roadmap.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

* Documentation is updated to reflect all changes.
* New classes, functions, etc have docstrings.
* New code has comments.
* Code style and file structure is similar to the rest of the project.
* You have run the `black` code formatter.

Releasing Snowfakery
-------------------

It's easy for maintainers to release a version of Snowfakery to GitHub and PyPI! First, 
create a new branch for your version::

    $ git switch -c feature/snowfakery-<versionnum>

Make the necessary changes to prepare the new release:

    1. Update the version in ``snowfakery/version.txt``
    2. Update the release notes in ``HISTORY.md``

Commit the changes, open a Pull Request on GitHub and request approval from another committer.

Once your PR has been merged, PyPI release process should be triggered automatically
by Github Actions.

You can finish up the process by updating the release object that was auto-created in Github:

Just paste in the changelog notes and hit publish. 

Tada! You've published a new version of Snowfakery.

Internal Software Architecture
------------------------------

===================================  ================================  
Filename	                         Purpose	
-----------------------------------  --------------------------------

cli.py	                             Click-based Command Line. Uses the Click library to supply a CLI.
data_generator.py	                 The API entry point the CLI and CCI use. <p>This may be the best place to start reading. It abstracts away all of the complexity and outlines the core flow.	
parse_recipe_yaml.py	             Phase 1: parse YAML into a Runtime DOM<p>Includes some hacks to the YAML parser for handling line numbers.	
data_generator_runtime.py	         Phase 2: Runtime.<p>Actually generate the data by walking the template list top-to-bottom, generating rows as appopriate. 	
data_generator_runtime_dom.py	     An object model used in Phase 2. Roughly similar to the shape of the YAML file.
output_streams.py	                 Where the data goes in the output. Used during Phase 2.	
data_gen_exceptions.py	             Exceptions that can be thrown	
generate_mapping_from_recipe.py	     In the CCI context, this utility package allows the generation of mapping.yml files.	
template_funcs.py	                 Functions that can be invoked using either block syntax or in Jinja templates	
plugins.py                           Infrastructure for plugins 
standard_plugins/                    Plugins that ship with Snowfakery 
tests/	                             Unit tests	
===================================  ================================  


<img src='docs/images/img6.png' id='PJUACA3lKvf' alt='Architecture Diagram'>
