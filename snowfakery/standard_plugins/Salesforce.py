from snowfakery.plugins import ParserMacroPlugin
from snowfakery.data_generator_runtime_object_model import (
    ObjectTemplate,
    FieldFactory,
    SimpleValue,
    StructuredValue,
)
from snowfakery import data_gen_exceptions as exc
from random import randrange
from logging import getLogger
from tempfile import TemporaryDirectory
from pathlib import Path

from salesforce_bulk import SalesforceBulk

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

ns = "snowfakery.standard_plugins.Salesforce.SOQLQuery"


class Salesforce(ParserMacroPlugin):
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
                    f"`name` argument should be a string {sobj}: {type(sobj)}"
                )
            nickname = args.get("nickname")
            if nickname and not isinstance(nickname, str):
                raise exc.DataGenError(
                    f"`nickname` argument should be a string {nickname}: {type(sobj)}"
                )

        return sobj, nickname

    def ContentFile(self, context, args) -> ObjectTemplate:
        return {
            "Base64.encode": [
                {"File.file_data": {"encoding": "binary", "file": args.get("path")}}
            ]
        }


class SOQLDatasetImpl(DatasetBase):
    def __init__(self, plugin, *args, **kwargs):
        from cumulusci.tasks.bulkdata.step import (
            get_query_operation,
            DataOperationStatus,
        )

        self.get_query_operation = get_query_operation
        self.DataOperationStatus = DataOperationStatus
        self.plugin = plugin
        self.logger = getLogger(__name__)
        super().__init__(*args, **kwargs)

    @property
    def sf(self):
        return self.plugin.sf

    @property
    def bulk(self):
        return self.plugin.bulk

    def _compose_query(self, kwargs):
        fields = kwargs.get("fields")
        sobject = kwargs.get("sobject")
        where = kwargs.get("where")

        if not fields:
            raise DataGenError("SOQL Dataset needs a fields", None, None)

        if not sobject:
            raise DataGenError("SOQL Dataset needs an sobject", None, None)

        query = f"SELECT {fields} FROM {sobject} "
        if where:
            query += f" WHERE {where}"
        return query

    def _load_dataset(self, iteration_mode, rootpath, kwargs):
        fields = kwargs.get("fields")
        query = self._compose_query(kwargs)
        fieldnames = [f.strip() for f in fields.split(",")]
        qs = self.get_query_operation(
            sobject=None,
            fields=fieldnames,
            api_options={},
            context=self,
            query=query,
            api=None,
        )

        qs.query()
        if qs.job_result.status is not self.DataOperationStatus.SUCCESS:
            raise DataGenError(
                f"Unable to query records for {query}: {','.join(qs.job_result.job_errors)}"
            )
        self.tempdir, self.iterator = create_iterator(
            iteration_mode, fieldnames, qs.get_results()
        )
        return self.iterator

    def close(self):
        self.iterator.close()
        self.tempdir.close()


def create_iterator(mode, fieldnames, results):
    tempdir, db_url = _create_db(fieldnames, results)
    rc = sql_dataset(db_url, "data", mode)
    return tempdir, rc


def _create_db(fieldnames, results):
    results = list(results)
    tempdir = TemporaryDirectory()
    tempfile = Path(tempdir.name) / "queryresults.db"
    # TODO: try a real tempdb: "sqlite:///"
    dburl = f"sqlite:///{tempfile}"
    with SqlDbOutputStream.from_url(dburl) as db:
        ti = TableInfo("data")
        ti.fields = {
            fieldname: None for fieldname in fieldnames if fieldname.lower() != "id"
        }
        db.create_or_validate_tables({"data": ti})
        for row in results:
            row_dict = {fieldname: result for fieldname, result in zip(fieldnames, row)}
            print(row_dict)
            db.write_row("data", row_dict)
        print(list(db.engine.execute("select * from data")))
        db.flush()
        db.close()
    return tempdir, dburl


class SalesforceConnectionMixin:
    _sf_connection = None
    allowed_options = [PluginOption(f"{ns}.orgname", str)]

    @property
    def sf(self):
        if not self._sf_connection:
            self._sf_connection, self._bulk = _get_sf_connection(self._orgname)
        return self._sf_connection

    def bulk(self):
        if not self._bulk:
            self._sf_connection, self._bulk = _get_sf_connection(self._orgname)
        return self._bulk

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


class SOQLDataset(SalesforceConnectionMixin, DatasetPluginBase):
    def __init__(self, *args, **kwargs):
        self.dataset_impl = SOQLDatasetImpl(self)
        super().__init__(*args, **kwargs)


class SOQLQuery(SalesforceConnectionMixin, SnowfakeryPlugin):
    class Functions:
        def query_random(self, query_from, fields="Id"):
            count_q = self.context.plugin.sf.query(f"SELECT count() FROM {query_from}")
            count = count_q["totalSize"]
            mx = min(count, MAX_SALESFORCE_OFFSET)
            rand_offset = randrange(0, mx)
            query = f"SELECT {fields} FROM {query_from} LIMIT 1 OFFSET {rand_offset}"

            # todo: use CompositeParallelSalesforce to cache 200 at a time
            return self._query_record(query)

        def query_record(self, query_from, fields="Id"):
            query = f"SELECT {fields} FROM {query_from} LIMIT 2"
            return self._query_record(query)

        def reference_record(self, query_from):
            query = f"SELECT Id FROM {query_from} LIMIT 2"
            results = self._query_record(query)
            return results["Id"]

        def _query_record(self, query):
            qr = self.context.plugin.sf.query(query)
            records = qr.get("records")
            if not records:
                raise DataGenValueError(
                    f"No records returned by query {query}", None, None
                )
            elif len(records) > 1:
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
    return sf, _init_bulk(sf, org_config)


def _init_bulk(sf, org_config):
    return SalesforceBulk(
        host=org_config.instance_url.replace("https://", "").rstrip("/"),
        sessionId=org_config.access_token,
        API_version=sf.sf_version,
    )
