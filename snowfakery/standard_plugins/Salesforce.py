from random import randrange
from logging import getLogger
from tempfile import TemporaryDirectory
from pathlib import Path

from snowfakery.plugins import ParserMacroPlugin
from snowfakery.data_generator_runtime_object_model import (
    ObjectTemplate,
    FieldFactory,
    SimpleValue,
    StructuredValue,
)
from snowfakery import data_gen_exceptions as exc

from snowfakery.plugins import SnowfakeryPlugin, PluginOption, PluginResult
from snowfakery.data_gen_exceptions import (
    DataGenNameError,
    DataGenValueError,
    DataGenError,
)
from snowfakery.standard_plugins.datasets import (
    DatasetBase,
    DatasetPluginBase,
    sql_dataset,
)
from snowfakery.output_streams import SqlDbOutputStream
from snowfakery.parse_recipe_yaml import TableInfo


MAX_SALESFORCE_OFFSET = 2000  # Any way around this?

# the option name that the user specifies on the CLI or API is just "org_name"
# but using this long name internally prevents us from clashing with the
# user's variable names.
plugin_option_org_name = (
    "snowfakery.standard_plugins.Salesforce.SalesforceQuery.org_name"
)
plugin_option_org_config = (
    "snowfakery.standard_plugins.Salesforce.SalesforceQuery.org_config"
)
plugin_option_project_config = (
    "snowfakery.standard_plugins.Salesforce.SalesforceQuery.project_config"
)


class SalesforceConnection:
    """Helper layer above simple_salesforce and salesforce_bulk"""

    _sf = None

    def __init__(self, get_project_config_and_org_config):
        self.get_project_config_and_org_config = get_project_config_and_org_config
        self.logger = getLogger(__name__)

    @property
    def sf(self):
        """simple_salesforce client"""
        if not self._sf:
            project_config, org_config = self.get_project_config_and_org_config()
            self._sf, self._bulk = self._get_sf_clients(project_config, org_config)
        return self._sf

    @property
    def bulk(self):
        """salesforce_bulk client"""
        self.sf  # initializes self._bulk as a side-effect
        return self._bulk

    def query(self, *args, **kwargs):
        """Query Salesforce through simple_salesforce"""
        return self.sf.query(*args, **kwargs)

    def query_single_record(self, query):
        """Query Salesforce through simple_salesforce and
        validate that query returns 1 and only 1 record"""
        qr = self.sf.query(query)
        records = qr.get("records")
        if not records:
            raise DataGenValueError(f"No records returned by query {query}", None, None)
        elif len(records) > 1:  # pragma: no cover
            raise DataGenValueError(
                f"Multiple records returned by query {query}", None, None
            )
        record = records[0]
        if "attributes" in record:
            del record["attributes"]
        if len(record.keys()) == 1:
            return tuple(record.values())[0]
        else:
            return PluginResult(record)

    def compose_query(self, context_name, **kwargs):
        kwargs = kwargs.copy()
        fields = kwargs.pop("fields", None)
        sobject = kwargs.pop("from", None)
        where = kwargs.pop("where", None)

        if not fields:
            raise DataGenError(f"{context_name} needs a 'fields' list")

        if not sobject:
            raise DataGenError(f"{context_name} needs a 'from'")

        if kwargs:
            raise DataGenError(
                f"Unknown argument in {context_name}: {tuple(kwargs.keys())}"
            )

        query = f"SELECT {fields} FROM {sobject} "
        if where:
            query += f" WHERE {where}"
        return query

    @staticmethod
    def _get_sf_clients(project_config, org_config):
        from cumulusci.salesforce_api.utils import get_simple_salesforce_connection

        sf = get_simple_salesforce_connection(project_config, org_config)
        return sf, _init_bulk(sf, org_config)


def _init_bulk(sf, org_config):
    from salesforce_bulk import SalesforceBulk

    return SalesforceBulk(
        host=org_config.instance_url.replace("https://", "").rstrip("/"),
        sessionId=org_config.access_token,
        API_version=sf.sf_version,
    )


def check_orgconfig(config):
    from cumulusci.core.config import BaseConfig

    if isinstance(config, BaseConfig):
        return config
    raise TypeError(f"Should be a CCI Config, not {type(config)}")


class SalesforceConnectionMixin:
    _sf_connection = None
    _runtime = None
    allowed_options = [
        PluginOption(plugin_option_org_name, str),
        PluginOption(plugin_option_org_config, check_orgconfig),
        PluginOption(plugin_option_project_config, check_orgconfig),
    ]

    @property
    def sf_connection(self):
        assert self.context
        if not self._sf_connection:
            self._sf_connection = SalesforceConnection(
                self.get_project_config_and_org_config
            )
        return self._sf_connection

    def get_project_config_and_org_config(self):
        fieldvars = self.context.field_vars()
        project_config = fieldvars.get(plugin_option_project_config)
        org_config = fieldvars.get(plugin_option_org_config)

        if not project_config or not org_config:
            project_config, org_config = self._get_org_info_from_cli_keychain()

        return project_config, org_config

    def _get_org_info_from_cli_keychain(self):
        org_name = self.get_org_name()  # from command line argument
        runtime = self._get_CliRuntime()  # from CCI CliRuntime
        name, org_config = runtime.get_org(org_name)
        return runtime.project_config, org_config

    def _get_CliRuntime(self):
        if self._runtime:
            return self._runtime  # pragma: no cover

        try:
            from cumulusci.cli.runtime import CliRuntime

            self._runtime = CliRuntime(load_keychain=True)
            return self._runtime
        except Exception as e:  # pragma: no cover
            raise DataGenError("CumulusCI Runtime cannot be loaded", *e.args)

    def get_org_name(self):
        """Look up the org_name in the scope"""
        fieldvars = self.context.field_vars()
        try:
            return fieldvars[plugin_option_org_name]
        except KeyError:
            raise DataGenNameError(
                "Orgname is not specified. Use --plugin-option org_name <yourorgname>",
                None,
                None,
            )


class Salesforce(ParserMacroPlugin, SnowfakeryPlugin, SalesforceConnectionMixin):
    def __init__(self, *args, **kwargs):
        args = args or [None]
        super().__init__(*args, **kwargs)

    def SpecialObject(self, context, args) -> ObjectTemplate:
        """Currently there is only one special object defined: PersonContact"""
        sobj, nickname = self._parse_special_args(args)
        line_info = context.line_num()
        if sobj == "PersonContact":
            return self._render_person_contact(context, sobj, nickname, line_info)
        else:
            raise exc.DataGenError(
                f"Unknown special object '{sobj}'. Did you mean 'PersonContact'?",
                None,
                None,
            )

    def _render_person_contact(self, context, sobj, nickname, line_info):
        """Generate the code to render a person contact as CCI expects.

        Code generation is a better strategy for this than a runtime
        plugin because some analysis of the table structures happens
        at parse time.
        """
        fields = [
            FieldFactory(
                "IsPersonAccount",
                SimpleValue("true", **line_info),
                **line_info,
            ),
            FieldFactory(
                "AccountId",
                StructuredValue("reference", ["Account"], **line_info),
                **line_info,
            ),
        ]
        new_template = ObjectTemplate(
            sobj,
            filename=line_info["filename"],
            line_num=line_info["line_num"],
            nickname=nickname,
            fields=fields,
        )
        context.register_template(new_template)
        return new_template

    def _parse_special_args(self, args):
        """Parse args of SpecialObject"""
        nickname = None
        if isinstance(args, str):
            sobj = args
        elif isinstance(args, dict):
            sobj = args["name"]
            if not isinstance(sobj, str):
                raise exc.DataGenError(
                    f"`name` argument should be a string, not `{sobj}`: ({type(sobj)})"
                )
            nickname = args.get("nickname")
            if nickname and not isinstance(nickname, str):
                raise exc.DataGenError(
                    f"`nickname` argument should be a string, not `{nickname}``: ({type(sobj)})"
                )
        else:
            raise exc.DataGenError(
                f"`name` argument should be a string, not `{args}``: ({type(args)})"
            )

        return sobj, nickname

    # FIXME: This code is not documented or tested
    def ContentFile(self, context, args) -> ObjectTemplate:
        return {
            "Base64.encode": [
                {"File.file_data": {"encoding": "binary", "file": args.get("path")}}
            ]
        }

    def PermissionSetAssignments(self, context, args) -> ObjectTemplate:
        names = args.get("names")
        if not isinstance(names, str):
            raise DataGenValueError(
                f"string `names` not specified for PermissionSetAssignments: {names}"
            )
        names = names.split(",")
        line_info = context.line_num()
        decls = [self._generate_psa(context, line_info, name) for name in names]

        return ObjectTemplate(
            "__wrapper_for_permission_sets",
            filename=line_info["filename"],
            line_num=line_info["line_num"],
            friends=decls,
        )

    def _generate_psa(self, context, line_info, name):
        fields = {"AssigneeId": ("Use")}

        query = f"PermissionSet where Name = '{name}'"

        fields = [
            FieldFactory(
                "PermissionSetId",
                StructuredValue(
                    "SalesforceQuery.find_record", {"from": query}, **line_info
                ),
                **line_info,
            ),
            FieldFactory(
                "AssigneeId",
                StructuredValue("reference", ["User"], **line_info),
                **line_info,
            ),
        ]

        new_template = ObjectTemplate(
            "PermissionSetAssignment",
            filename=line_info["filename"],
            line_num=line_info["line_num"],
            fields=fields,
        )
        context.register_template(new_template)
        return new_template

    class Functions:
        def ProfileId(self, name):
            query = f"select Id from Profile where Name='{name}'"
            return self.context.plugin.sf_connection.query_single_record(query)

        Profile = ProfileId


# TODO: Tests for this class
class SOQLDatasetImpl(DatasetBase):
    def __init__(self, plugin, *args, **kwargs):
        from cumulusci.tasks.bulkdata.step import (
            get_query_operation,
            DataOperationStatus,
        )

        self.get_query_operation = get_query_operation
        self.DataOperationStatus = DataOperationStatus
        self.plugin = plugin
        super().__init__(*args, **kwargs)

    @property
    def sf_connection(self):
        return self.plugin.sf_connection

    def _load_dataset(self, iteration_mode, rootpath, kwargs):
        from cumulusci.tasks.bulkdata.step import DataApi

        query = self.sf_connection.compose_query("SOQLDataset", **kwargs)
        fields = kwargs.get("fields")
        sobject = kwargs.get("from")
        fieldnames = [f.strip() for f in fields.split(",")]
        qs = self.get_query_operation(
            sobject=sobject,
            fields=fieldnames,
            api_options={},
            context=self.sf_connection,
            query=query,
            api=DataApi.SMART,
        )

        try:
            qs.query()
        except Exception as e:
            raise DataGenError(f"Unable to query records for {query}: {e}") from e

        if qs.job_result.status is not self.DataOperationStatus.SUCCESS:
            raise DataGenError(
                f"Unable to query records for {query}: {','.join(qs.job_result.job_errors)}"
            )

        self.tempdir, self.iterator = create_tempfile_sql_db_iterator(
            iteration_mode, fieldnames, qs.get_results()
        )
        return self.iterator

    def close(self):
        self.iterator.close()
        self.tempdir.close()


def create_tempfile_sql_db_iterator(mode, fieldnames, results):
    tempdir, db_url = _create_db(fieldnames, results)
    rc = sql_dataset(db_url, "data", mode)
    return tempdir, rc


def _create_db(fieldnames, results):
    tempdir = TemporaryDirectory()
    tempfile = Path(tempdir.name) / "queryresults.db"
    # TODO: try a real tempdb: "sqlite:///"
    dburl = f"sqlite:///{tempfile}"
    with SqlDbOutputStream.from_url(dburl) as db:
        ti = TableInfo("data")
        ti.fields = {fieldname: None for fieldname in fieldnames}
        db.create_or_validate_tables({"data": ti})
        for row in results:
            row_dict = {fieldname: result for fieldname, result in zip(fieldnames, row)}
            db.write_row("data", row_dict)
        db.flush()
        db.close()
    return tempdir, dburl


class SOQLDataset(SalesforceConnectionMixin, DatasetPluginBase):
    def __init__(self, *args, **kwargs):
        self.dataset_impl = SOQLDatasetImpl(self)
        super().__init__(*args, **kwargs)


class SalesforceQuery(SalesforceConnectionMixin, SnowfakeryPlugin):
    class Functions:
        @property
        def _sf_connection(self):
            return self.context.plugin.sf_connection

        def random_record(self, *args, fields="Id", where=None, **kwargs):
            """Query a random record."""
            context_vars = self.context.context_vars()
            context_vars.setdefault("count_query_cache", {})

            # "from" has to be handled separately because its a Python keyword
            query_from = self._parse_from_from_args(args, kwargs)

            # TODO: Test WHERE
            where_clause = f" WHERE {where}" if where else ""
            count_query = f"SELECT count() FROM {query_from}{where_clause}"
            count_result = self._sf_connection.query(count_query)

            count = count_result["totalSize"]
            mx = min(count, MAX_SALESFORCE_OFFSET)
            context_vars["count_query_cache"][count_query] = mx
            rand_offset = randrange(0, mx)
            query = f"SELECT {fields} FROM {query_from}{where_clause} LIMIT 1 OFFSET {rand_offset}"
            # todo: use CompositeParallelSalesforce to cache 200 at a time
            return self._sf_connection.query_single_record(query)

        def find_record(self, *args, fields="Id", where=None, **kwargs):
            """Find a particular record"""
            query_from = self._parse_from_from_args(args, kwargs)
            where_clause = f" WHERE {where}" if where else ""
            query = f"SELECT {fields} FROM {query_from}{where_clause} LIMIT 1"
            return self._sf_connection.query_single_record(query)

        def _parse_from_from_args(self, args, kwargs):
            query_from = None
            if kwargs:
                query_from = kwargs.pop("from", None)

                if kwargs:
                    raise ValueError(f"Unknown arguments: {tuple(kwargs.keys())}")
            elif args:
                if len(args) != 1 or not isinstance(args[0], str):
                    raise ValueError(f"Only one string argument allowed, not: {args}")
                query_from = args[0]

            if not query_from:
                raise ValueError("Must supply 'from:'")

            return query_from
