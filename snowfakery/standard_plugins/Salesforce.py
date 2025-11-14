from base64 import b64encode
from logging import getLogger
from pathlib import Path
from random import randrange
from tempfile import TemporaryDirectory

from snowfakery import data_gen_exceptions as exc
from snowfakery.data_gen_exceptions import (
    DataGenError,
    DataGenNameError,
    DataGenValueError,
)
from snowfakery.data_generator_runtime_object_model import (
    FieldFactory,
    ObjectTemplate,
    SimpleValue,
    StructuredValue,
)
from snowfakery.output_streams import SqlDbOutputStream
from snowfakery.parse_recipe_yaml import TableInfo
from snowfakery.plugins import (
    ParserMacroPlugin,
    PluginOption,
    PluginResult,
    SnowfakeryPlugin,
    memorable,
)
from snowfakery.standard_plugins.datasets import (
    DatasetBase,
    DatasetPluginBase,
    sql_dataset,
)
from snowfakery.utils.validation_utils import resolve_value

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

    class Functions:
        @memorable
        def ProfileId(self, name):
            query = f"select Id from Profile where Name='{name}'"
            return self.context.plugin.sf_connection.query_single_record(query)

        Profile = ProfileId

        def ContentFile(self, file: str):
            template_path = Path(self.context.current_filename).parent

            with open(template_path / file, "rb") as data:
                return b64encode(data.read()).decode("ascii")

    class Validators:
        """Validators for Salesforce plugin functions."""

        @staticmethod
        def validate_ProfileId(sv, context):
            """Validate Salesforce.ProfileId(name) and Salesforce.Profile(name)"""

            # Get positional and keyword arguments
            args = getattr(sv, "args", [])
            kwargs = getattr(sv, "kwargs", {})

            # Check if name provided as positional arg
            name_val = None
            if args:
                if len(args) != 1:
                    context.add_error(
                        f"Salesforce.ProfileId: Expected 1 positional argument (name), got {len(args)}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                raw_val = args[0]
                # Check raw type before resolution (to catch invalid types early)
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"Salesforce.ProfileId: 'name' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                name_val = resolve_value(raw_val, context)
            elif "name" in kwargs:
                raw_val = kwargs["name"]
                # Check raw type before resolution (to catch invalid types early)
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"Salesforce.ProfileId: 'name' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                name_val = resolve_value(raw_val, context)
            else:
                context.add_error(
                    "Salesforce.ProfileId: Missing required parameter 'name'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate name is a string after resolution
            if name_val is not None and not isinstance(name_val, str):
                context.add_error(
                    f"Salesforce.ProfileId: 'name' must be a string, got {type(name_val).__name__}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # WARNING: Unknown parameters
            valid_params = {"name", "parent", "_"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"Salesforce.ProfileId: Unknown parameter(s): {', '.join(sorted(unknown))}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return mock: Salesforce Profile ID
            # Profile IDs start with "005" and are 18 characters (15-char + 3-char suffix)
            return "00558000001abcAAA"

        validate_Profile = validate_ProfileId  # Alias

        @staticmethod
        def validate_ContentFile(sv, context):
            """Validate Salesforce.ContentFile(file)"""

            # Get positional and keyword arguments
            args = getattr(sv, "args", [])
            kwargs = getattr(sv, "kwargs", {})

            # Check if file provided as positional arg
            file_val = None
            if args:
                if len(args) != 1:
                    context.add_error(
                        f"Salesforce.ContentFile: Expected 1 positional argument (file), got {len(args)}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                raw_val = args[0]
                # Check raw type before resolution (to catch invalid types early)
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"Salesforce.ContentFile: 'file' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                file_val = resolve_value(raw_val, context)
            elif "file" in kwargs:
                raw_val = kwargs["file"]
                # Check raw type before resolution (to catch invalid types early)
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"Salesforce.ContentFile: 'file' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                file_val = resolve_value(raw_val, context)
            else:
                context.add_error(
                    "Salesforce.ContentFile: Missing required parameter 'file'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate file is a string after resolution
            if file_val is not None:
                if not isinstance(file_val, str):
                    context.add_error(
                        f"Salesforce.ContentFile: 'file' must be a string, got {type(file_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                else:
                    # Validate file exists relative to recipe
                    if context.current_template and context.current_template.filename:
                        template_path = Path(context.current_template.filename).parent
                        file_path = template_path / file_val

                        if not file_path.exists():
                            context.add_error(
                                f"Salesforce.ContentFile: File not found: {file_val}",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )
                        elif not file_path.is_file():
                            context.add_error(
                                f"Salesforce.ContentFile: Path must be a file, not a directory: {file_val}",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )

            # WARNING: Unknown parameters
            valid_params = {"file", "parent", "_"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"Salesforce.ContentFile: Unknown parameter(s): {', '.join(sorted(unknown))}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return intelligent mock: base64-encoded mock file content
            return b64encode(b"Mock file content for validation").decode("ascii")


class SOQLDatasetImpl(DatasetBase):
    iterator = None
    tempdir = None

    def __init__(self, plugin, *args, **kwargs):
        from cumulusci.tasks.bulkdata.step import (
            DataOperationStatus,
            get_query_operation,
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

        tempdir, iterator = create_tempfile_sql_db_iterator(
            iteration_mode, fieldnames, qs.get_results()
        )
        iterator.cleanup.push(tempdir)
        return iterator

    def close(self):
        pass


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
            if mx < 1:
                raise DataGenError(
                    f"No records found matching {query_from}{where_clause}"
                )
            rand_offset = randrange(0, mx)
            query = f"SELECT {fields} FROM {query_from}{where_clause} LIMIT 1 OFFSET {rand_offset}"
            # todo: use CompositeParallelSalesforce to cache 200 at a time
            return self._sf_connection.query_single_record(query)

        @memorable
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

    class Validators:
        """Validators for SalesforceQuery plugin functions."""

        @staticmethod
        def validate_random_record(sv, context):
            """Validate SalesforceQuery.random_record(from, fields, where)"""

            # Get positional and keyword arguments
            args = getattr(sv, "args", [])
            kwargs = getattr(sv, "kwargs", {})

            # Parse 'from' parameter (special handling because it's a Python keyword)
            query_from = None
            from_is_positional = False

            # Check positional args
            if args:
                if len(args) != 1:
                    context.add_error(
                        f"SalesforceQuery.random_record: Expected 1 positional argument (from), got {len(args)}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                from_is_positional = True
                raw_val = args[0]
                # Check raw type before resolution
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"SalesforceQuery.random_record: 'from' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                query_from = resolve_value(raw_val, context)

            # Check keyword args
            if "from" in kwargs:
                if from_is_positional:
                    context.add_warning(
                        "SalesforceQuery.random_record: Cannot specify 'from' both as positional and keyword argument",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                raw_val = kwargs["from"]
                # Check raw type before resolution
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"SalesforceQuery.random_record: 'from' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                query_from = resolve_value(raw_val, context)

            # ERROR: Missing required 'from'
            if query_from is None:
                context.add_error(
                    "SalesforceQuery.random_record: Missing required parameter 'from'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate 'from' is a string after resolution
            if not isinstance(query_from, str):
                context.add_error(
                    f"SalesforceQuery.random_record: 'from' must be a string, got {type(query_from).__name__}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Validate 'fields' parameter
            fields_str = "Id"  # Default
            if "fields" in kwargs:
                raw_val = kwargs["fields"]
                # Check raw type before resolution
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"SalesforceQuery.random_record: 'fields' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                else:
                    fields_val = resolve_value(raw_val, context)
                    if fields_val is not None:
                        if not isinstance(fields_val, str):
                            context.add_error(
                                f"SalesforceQuery.random_record: 'fields' must be a string, got {type(fields_val).__name__}",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )
                        else:
                            fields_str = fields_val

            # Validate 'where' parameter
            if "where" in kwargs:
                raw_val = kwargs["where"]
                # Check raw type before resolution
                if not isinstance(raw_val, (str, SimpleValue, type(None))):
                    context.add_error(
                        f"SalesforceQuery.random_record: 'where' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                else:
                    where_val = resolve_value(raw_val, context)
                    if where_val is not None and not isinstance(where_val, str):
                        context.add_error(
                            f"SalesforceQuery.random_record: 'where' must be a string, got {type(where_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # WARNING: Unknown parameters
            valid_params = {"from", "fields", "where", "parent", "_"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"SalesforceQuery.random_record: Unknown parameter(s): {', '.join(sorted(unknown))}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return mock object with dynamic field attributes
            return SalesforceQuery.Validators._create_mock_record(fields_str)

        @staticmethod
        def validate_find_record(sv, context):
            """Validate SalesforceQuery.find_record(from, fields, where)"""

            # Get positional and keyword arguments
            args = getattr(sv, "args", [])
            kwargs = getattr(sv, "kwargs", {})

            # Parse 'from' parameter (special handling because it's a Python keyword)
            query_from = None
            from_is_positional = False

            # Check positional args
            if args:
                if len(args) != 1:
                    context.add_error(
                        f"SalesforceQuery.find_record: Expected 1 positional argument (from), got {len(args)}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                from_is_positional = True
                raw_val = args[0]
                # Check raw type before resolution
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"SalesforceQuery.find_record: 'from' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                query_from = resolve_value(raw_val, context)

            # Check keyword args
            if "from" in kwargs:
                if from_is_positional:
                    context.add_warning(
                        "SalesforceQuery.find_record: Cannot specify 'from' both as positional and keyword argument",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                raw_val = kwargs["from"]
                # Check raw type before resolution
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"SalesforceQuery.find_record: 'from' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                    return
                query_from = resolve_value(raw_val, context)

            # ERROR: Missing required 'from'
            if query_from is None:
                context.add_error(
                    "SalesforceQuery.find_record: Missing required parameter 'from'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return

            # Validate 'from' is a string after resolution
            if not isinstance(query_from, str):
                context.add_error(
                    f"SalesforceQuery.find_record: 'from' must be a string, got {type(query_from).__name__}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Validate 'fields' parameter
            fields_str = "Id"  # Default
            if "fields" in kwargs:
                raw_val = kwargs["fields"]
                # Check raw type before resolution
                if not isinstance(raw_val, (str, SimpleValue)):
                    context.add_error(
                        f"SalesforceQuery.find_record: 'fields' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                else:
                    fields_val = resolve_value(raw_val, context)
                    if fields_val is not None:
                        if not isinstance(fields_val, str):
                            context.add_error(
                                f"SalesforceQuery.find_record: 'fields' must be a string, got {type(fields_val).__name__}",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )
                        else:
                            fields_str = fields_val

            # Validate 'where' parameter
            if "where" in kwargs:
                raw_val = kwargs["where"]
                # Check raw type before resolution
                if not isinstance(raw_val, (str, SimpleValue, type(None))):
                    context.add_error(
                        f"SalesforceQuery.find_record: 'where' must be a string, got {type(raw_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                else:
                    where_val = resolve_value(raw_val, context)
                    if where_val is not None and not isinstance(where_val, str):
                        context.add_error(
                            f"SalesforceQuery.find_record: 'where' must be a string, got {type(where_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # WARNING: Unknown parameters
            valid_params = {"from", "fields", "where", "parent", "_"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"SalesforceQuery.find_record: Unknown parameter(s): {', '.join(sorted(unknown))}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return mock object with dynamic field attributes
            return SalesforceQuery.Validators._create_mock_record(fields_str)

        @staticmethod
        def _create_mock_record(fields_str):
            """Create a mock Salesforce record with dynamic field attributes."""
            # Parse comma-separated fields
            field_names = [f.strip() for f in fields_str.split(",") if f.strip()]
            if not field_names:
                field_names = ["Id"]

            # Create mock object class
            class MockSalesforceRecord:
                def __init__(self, field_names):
                    for field_name in field_names:
                        setattr(self, field_name, f"<mock_{field_name}>")

                def __repr__(self):
                    fields = ", ".join(
                        [f"{k}=<mock_{k}>" for k in self.__dict__.keys()]
                    )
                    return f"MockSalesforceRecord({fields})"

            return MockSalesforceRecord(field_names)
