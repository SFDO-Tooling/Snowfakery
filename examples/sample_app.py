from snowfakery import generate_data, SnowfakeryApplication


class MyApplication(SnowfakeryApplication):
    def __init__(self, stopping_tablename, count):
        self.count = count
        self._stopping_tablename = stopping_tablename

    def echo(self, message=None, file=None, nl=True, err=False, color=None, **kwargs):
        """Write something to a virtual stdout or stderr.

        Arguments to this function are derived from click.echo"""
        # this is a simplistic implementation! Model your real one
        # on click.echo
        if err:
            print("ERROR:" + message)
        else:
            print(message)

    @property
    def stopping_tablename(self, **kwargs):
        """Return the name of "stopping table/object":

        The table/object whose presence determines
        whether we are done generating data.

        This is used by Snowfakery to validate that
        the provided recipe will not generate forever
        due to a misspelling the stopping tablename."""
        return self._stopping_tablename

    def check_if_finished(self, id_manager, **kwargs):
        """Check if we're finished generating"""
        print("Checking if finished:", id_manager[self.stopping_tablename])
        return id_manager[self.stopping_tablename] >= self.count


myapp = MyApplication("Employee", 100)
generate_data("examples/company.yml", parent_application=myapp, output_file="out.json")
