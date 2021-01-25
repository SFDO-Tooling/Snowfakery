from copy import deepcopy
from warnings import warn

from snowfakery.data_generator import ExecutionSummary
from snowfakery.data_gen_exceptions import DataGenNameError, DataGenError
from snowfakery.parse_recipe_yaml import TableInfo
from snowfakery.data_generator_runtime import Dependency


def mapping_from_recipe_templates(summary: ExecutionSummary):
    """Use the outputs of the recipe YAML and convert to Mapping.yml format"""
    record_types = generate_record_type_pseudo_tables(summary)
    dependencies, reference_fields = build_dependencies(summary.intertable_dependencies)
    tables = {**summary.tables, **record_types}
    table_order = sort_dependencies(dependencies, tables)
    mappings = mappings_from_sorted_tables(tables, table_order, reference_fields)
    return mappings


def find_record_type_field(fields, context_name):
    """Verify that the RecordType field has the right capitalization and return it."""

    # theoretically a custom object could have a field named record_type but more likely
    # it would be a mistake, so warn on that too
    record_type_fields = [
        field
        for field in fields
        if field.name.lower().replace("d_t", "dt", 1) == "recordtype"
    ]
    if not record_type_fields:
        return None
    elif len(record_type_fields) > 1:
        raise DataGenError(
            f"Only one RecordType field allowed: {context_name}", None, None
        )
    elif record_type_fields[0].name != "RecordType":
        raise DataGenNameError(
            "Recordtype field needs this capitalization: RecordType", None, None
        )

    return record_type_fields[0]


def generate_record_type_pseudo_tables(summary):
    """Generate fake table objects for purposes of dependency sorting, lookups and mapping generation"""
    record_types = {}
    for template in summary.templates:
        real_table_name = template.tablename
        record_type_field = find_record_type_field(template.fields, real_table_name)
        if not record_type_field:
            continue

        real_table = summary.tables[real_table_name]
        record_type_name = record_type_field.definition.definition

        # generate a pretend table for purposes of dependency sorting,
        # lookups and mapping generation
        record_type_pseudo_table = record_types.setdefault(
            record_type_name, TableInfo(template.tablename)
        )
        record_type_pseudo_table.register(template)
        record_type_pseudo_table.record_type = record_type_name

        # copy over the dependencies from the real table
        for dependency in sorted(summary.intertable_dependencies):
            if dependency.table_name_from == real_table_name:
                summary.intertable_dependencies.add(
                    Dependency(record_type_name, *dependency[1:])
                )

        # the record type field isn't helpful for the TableInfo of the real table anymore
        # need a conditional here to ensure its only deleted once
        if real_table.fields.get("RecordType"):
            del real_table.fields["RecordType"]
            real_table.has_record_types = True

    return record_types


def build_dependencies(intertable_dependencies):
    """Figure out which tables depend on which other ones (through foreign keys)

    intertable_dependencies is a dict with values of Dependency objects.

    Returns two things:
        1. a dictionary allowing easy lookup of dependencies by parent table
        2. a dictionary allowing lookups by (tablename, fieldname) pairs
    """
    dependencies = {}
    reference_fields = {}
    for dep in intertable_dependencies:
        table_deps = dependencies.setdefault(dep.table_name_from, set())
        table_deps.add(dep)
        reference_fields[(dep.table_name_from, dep.field_name)] = dep.table_name_to
    return dependencies, reference_fields


def _table_is_free(table_name, dependencies, sorted_tables):
    """Check if every child of this table is already sorted

    Look at the unit test test_table_is_free_simple to see some
    usage examples.
    """
    tables_this_table_depends_upon = dependencies.get(table_name, {})
    for dependency in sorted(tables_this_table_depends_upon):
        if dependency.table_name_to in sorted_tables:
            tables_this_table_depends_upon.remove(dependency)

    return len(tables_this_table_depends_upon) == 0


def sort_dependencies(dependencies, tables):
    """"Sort the dependencies to output tables in the right order."""
    dependencies = deepcopy(dependencies)
    sorted_tables = []

    while tables:
        remaining = len(tables)
        leaf_tables = {
            table
            for table in tables
            if _table_is_free(table, dependencies, sorted_tables)
        }
        sorted_tables.extend(leaf_tables)
        tables = [table for table in tables if table not in sorted_tables]
        if len(tables) == remaining:
            warn(f"Circular references: {tables}. Load mapping may fail!")
            sorted_tables.append(tables[0])
    return sorted_tables


def mappings_from_sorted_tables(
    tables: dict, table_order: list, reference_fields: dict
):
    """Generate mapping.yml data structures. """
    mappings = {}
    for table_name in table_order:
        table = tables[table_name]
        fields = {
            fieldname: fieldname
            for fieldname, fielddef in table.fields.items()
            if (table_name, fieldname) not in reference_fields.keys()
            and fieldname != "RecordType"
        }
        lookups = {
            fieldname: {
                "table": reference_fields[(table_name, fieldname)],
                "key_field": fieldname,
            }
            for fieldname, fielddef in table.fields.items()
            if (table_name, fieldname) in reference_fields.keys()
        }

        if "RecordType" in table.fields:
            fielddef = table.fields["RecordType"].definition
            if not getattr(fielddef, "definition", None):
                raise DataGenError(
                    "Record type definitions must be simple, not computed", None, None
                )
            record_type = fielddef.definition
            filters = [f"RecordType = '{record_type}'"]
        else:
            record_type = None
            # add a filter to avoid returning rows associated with record types
            filters = (
                ["RecordType is NULL"]
                if getattr(table, "has_record_types", False)
                else []
            )

        mapping = {"sf_object": table.name, "table": table.name, "fields": fields}
        if record_type:
            mapping["record_type"] = record_type
        if filters:
            mapping["filters"] = filters
        if lookups:
            mapping["lookups"] = lookups

        mappings[f"Insert {table_name}"] = mapping

    return mappings
