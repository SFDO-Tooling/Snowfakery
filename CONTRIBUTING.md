# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at <https://github.com/SFDO-Tooling/Snowfakery/issues>.

When reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in
  troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whomever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with
"enhancement" and "help wanted" is open to whomever wants to
implement it.

### Write Documentation

Snowfakery could always use more documentation, whether as part of the
official Snowfakery docs, in docstrings, or even on the web in blog
posts, articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at
<https://github.com/SFDO-Tooling/Snowfakery/issues>.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to
  implement.
- Remember that this is a volunteer-driven project, and that
  contributions are welcome :)

## Get Started!

Ready to contribute? Here's how to set up Snowfakery for local
development.

1.  Fork the Snowfakery repo on GitHub.

2.  Clone your fork to your local workspace.

3.  Create and activate fresh virtual environment using virtualenv.
    (Google this if you don't know how). If you name your virtualenv
    "myenv" then it will be ignored by by git due to our .gitignore file.
    Or you could make it outside of the project repo.

4.  Install development requirements:

    ```{.shell}
    $ make dev-install
    ```

5.  Install `pre-commit` hooks for `black` and `flake8`:

    ```{.shell}
    $ pre-commit install --install-hooks
    ```

6.  Add the current directory to your python path. The easy, one-time
    way to do that is with a command like:

    ```sh
    $ export PYTHONPATH=.
    ```

    But if you install a tool like `direnv` then you won't need to remember
    to do that every time you start a terminal or restart your computer.

7.  After making changes, run the tests and make sure they all pass:

    ```{.shell}
    $ pytest
    ```

## Testing with CumulusCI

It's a best practice to test your changes with CumulusCI. Some Snowfakery
features "turn on" if CumulusCI is detected in the Python installation.
Instead of 20+ tests being skipped you may see just a couple.

You can install a local CumulusCI repo into your Snowfakery like this:

```sh
$ pip install -e ../CumulusCI
```

After this, your `pytest` should include many tests that would otherwise
be skipped.

## Testing and Coverage

Your new code should also have meaningful tests. One way to double
check that your tests cover everything is to ensure that your new
code has test code coverage:

    $ pytest --cov

    or

    $ make coverage

Code should have 100% coverage. If some corner case is impractical
to test, first, try to test it anyways. If you still think it is
impractical (e.g. a one in a million error case which is hard to mock
for some reason), you can use a declaration of `# pragma: no cover`
to skip it.

## Submitting your change

Push your changes to GitHub and submit a pull request. The base
branch should be a new feature branch that we create to receive the
changes (contact us to create the branch). This allows us to test the
changes using our build system before merging to main.

## Contributing to the docs

Build the docs like this:

```sh
    $ make docs
    $ open build/html/index.html
```

Set `SF_MKDOCS_BUILD_LOCALES=False` to skip building all locales.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

- You properly installed the `pre-commit` hooks.
- Documentation is updated to reflect all changes.
- New classes, functions, etc have docstrings.
- New code has comments.
- Code style and file structure is similar to the rest of the project.

## Releasing Snowfakery

It's easy for maintainers to release a version of Snowfakery to GitHub
and PyPI! First, create a new branch for your version:

```{.shell}
$ git switch -c feature/snowfakery-<versionnum>
```

Make the necessary changes to prepare the new release:

1.  Update the version in `snowfakery/version.txt`

2.  Update the release notes in `HISTORY.md`

Commit the changes, open a Pull Request on GitHub and request approval
from another committer.

Once your PR has been merged, PyPI release process should be triggered
automatically by Github Actions.

You can finish up the process by updating the release object that was
auto-created in Github:

Just paste in the changelog notes and hit publish.

Tada! You've published a new version of Snowfakery.

## Internal Software Architecture

Take a look at [`docs/arch/ArchIndex.md`](docs/arch/ArchIndex.md) to learn about
Snowfakery's architecture.

## Updating Dependencies

Run `make update-deps` to update requirements files locally.

Then run `make dev-install && pytest` to test.
