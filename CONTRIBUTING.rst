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
3. Create a fresh virtual environment using virtualenv and install development requirements::

    $ pip install -r requirements_dev.txt

4. Install ``pre-commit`` hooks for ``black`` and ``flake8``::

    $ pre-commit install --install-hooks

5. After making changes, run the tests and make sure they all pass::

    $ pytest

6. Your new code should also have meaningful tests. One way to double check that
   your tests cover everything is to ensure that your new code has test code coverage:

   $ pytest --cov

7. Push your changes to GitHub and submit a pull request. The base branch should 
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
