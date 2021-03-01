class DataGenError(Exception):
    prefix = (
        "An error occurred. If you would like to see a Python traceback, "
        "use the --debug-internals option."
    )

    def __init__(self, message, filename=None, line_num=None):
        self.message = message
        self.filename = filename
        self.line_num = line_num
        assert isinstance(filename, (str, type(None)))
        assert isinstance(line_num, (int, type(None)))
        super().__init__(self.message)

    def __str__(self):
        if self.line_num:
            location = f"\n near {self.filename}:{self.line_num}"
        elif self.filename:
            location = f"\n in {self.filename}"
        else:
            location = ""
        return f"{self.message}{location}"


class DataGenSyntaxError(DataGenError):
    pass


class DataGenYamlSyntaxError(DataGenSyntaxError):
    prefix = (
        "There is a problem with your YAML file.\n"
        + "Consider installing a YAML Validator Plugin for your editor.\n"
        + "For example, if you use VSCode, "
        + "https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml \n"
        + "Or: https://marketplace.visualstudio.com/items?itemName=docsmsft.docs-yaml \n"
        + "The error is:\n"
    )
    pass


class DataGenNameError(DataGenError):
    pass


class DataGenValueError(DataGenError):
    pass


class DataGenImportError(DataGenError):
    pass


class DataGenTypeError(DataGenError):
    pass


def fix_exception(message, parentobj, e):
    """Add filename and linenumber to an exception if needed"""
    filename, line_num = parentobj.filename, parentobj.line_num
    if isinstance(e, DataGenError):
        if not e.filename:
            e.filename = filename
        if not e.line_num:
            e.line_num = line_num
        return e
    else:
        return DataGenError(message, filename, line_num)
