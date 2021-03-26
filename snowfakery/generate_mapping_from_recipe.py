from copy import deepcopy
from warnings import warn

from snowfakery.data_generator import ExecutionSummary
from snowfakery.salesforce import find_record_type_column
from snowfakery.utils.collections import OrderedSet


def mapping_from_recipe_templates(summary: ExecutionSummary):
    """Use the outputs of the recipe YAML and convert to Mapping.yml format"""
    dependencies, reference_fields = build_dependencies(summary.intertable_dependencies)
    tables = summary.tables.copy()
    remove_person_contact_id(dependencies, tables)
    table_order = sort_dependencies(dependencies, tables)
    mappings = mappings_from_sorted_tables(tables, table_order, reference_fields)
    return mappings


def remove_person_contact_id(dependencies, tables):
    if "Account" in dependencies:
        dep_to_person_contact = [
            dep
            for dep in dependencies["Account"]
            if dep.table_name_to.lower() == "personcontact"
        ]
        for dep in dep_to_person_contact:
            dependencies["Account"].remove(dep)

    if tables.get("Account") and tables["Account"].fields.get("PersonContactId"):
        del tables["Account"].fields["PersonContactId"]


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
        table_deps = dependencies.setdefault(dep.table_name_from, OrderedSet())
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
        record_type_col = find_record_type_column(table_name, table.fields.keys())

        fields = {
            fieldname: fieldname
            for fieldname, fielddef in table.fields.items()
            if (table_name, fieldname) not in reference_fields.keys()
            and fieldname != record_type_col
        }
        if record_type_col:
            fields["RecordTypeId"] = record_type_col

        lookups = {
            fieldname: {
                "table": reference_fields[(table_name, fieldname)],
                "key_field": fieldname,
            }
            for fieldname, fielddef in table.fields.items()
            if (table_name, fieldname) in reference_fields.keys()
        }
        if table_name == "PersonContact":
            sf_object = "Contact"
        else:
            sf_object = table.name
        mapping = {"sf_object": sf_object, "table": table.name, "fields": fields}
        if lookups:
            mapping["lookups"] = lookups

        mappings[f"Insert {table_name}"] = mapping

    return mappings
