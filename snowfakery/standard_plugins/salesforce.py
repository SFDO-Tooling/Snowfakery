from random import randrange


from snowfakery.plugins import SnowfakeryPlugin, PluginOption
from snowfakery.data_gen_exceptions import (
    DataGenNameError,
    DataGenValueError,
    DataGenError,
)

MAX_SALESFORCE_OFFSET = 2000  # Any way around this?

ns = "snowfakery.standard_plugins.salesforce.Salesforce"


class Salesforce(SnowfakeryPlugin):

    allowed_options = [PluginOption(f"{ns}.orgname", str)]

    class Functions:
        _sf_connection = None

        @property
        def _sf(self):
            if not self._sf_connection:
                self._sf_connection = _get_sf_connection(self._orgname)
            return self._sf_connection

        @property
        def _orgname(self):
            fieldvars = self.context.field_vars()
            try:
                return fieldvars[f"{ns}.orgname"]
            except KeyError:
                raise DataGenNameError(
                    "Orgname is not specified. Use --plugin-option orgname <yourorgname>",
                    None,
                    None,
                )

        def query_random(self, query_from):
            count_q = self._sf.query(f"SELECT count() FROM {query_from}")
            count = count_q["totalSize"]
            rand_offset = randrange(0, min(count, MAX_SALESFORCE_OFFSET))

            # todo: use CompositeParallelSalesforce to cache 200 at a time
            return self._query_record(query_from, rand_offset)

        def _query_record(self, query_from, offset):
            query = f"Select Id FROM {query_from} LIMIT 1 OFFSET {offset}"
            qr = self._sf.query(query)
            records = qr.get("records")
            if not records:
                raise DataGenValueError(
                    f"No records returned by query {query}", None, None
                )
            return records[0]["Id"]

        def query_record(self, query_from):
            return self._query_record(query_from, 0)


def _get_sf_connection(orgname):
    try:
        from cumulusci.cli.runtime import CliRuntime

        from cumulusci.salesforce_api.utils import get_simple_salesforce_connection
    except ImportError as e:
        raise ImportError("cumulusci module cannot be loaded by snowfakery", *e.args)

    try:
        runtime = CliRuntime(load_keychain=True)
    except Exception as e:
        raise DataGenError("CLI Runtime cannot be loaded", *e.args)

    name, org_config = runtime.get_org(orgname)
    sf = get_simple_salesforce_connection(runtime.project_config, org_config)
    return sf
