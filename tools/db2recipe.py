import sys

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql import select
import networkx as nx

from yaml import dump

from snowfakery.utils.template_utils import look_for_number

references = {}


def person_name(fields):
    first_name = fields.get("FirstName")
    last_name = fields.get("LastName")
    if first_name and last_name:
        return f"{first_name} {last_name} {id(last_name)}"


def upper(s):
    if len(s) > 1:
        return s[0].upper() + s[1:]
    else:
        return s


def undo_snake_case(name):
    parts = name.split("_")
    first, rest = parts[0], parts[1:]
    s = "_".join([first] + list(map(upper, rest)))
    return s


def fixup(obj, oids, record_types, relationships):
    fields = obj["fields"]
    for name, value in fields.items():
        if name == "RecordTypeId":
            del fields["RecordTypeId"]
            fields["RecordType"] = record_types[value]
        elif value in oids:
            fields[name] = {"reference": oids[value]}
            relationships.add_edge(
                oids[value], obj["nickname"],
            )
        elif value == "true":
            fields[name] = True
        elif value == "false":
            fields[name] = False
        else:
            try:
                fields[name] = look_for_number(value)
            except ValueError:
                pass

    return fields


def find_record_types(engine, tables):
    rc = {}
    record_type_tables = [
        table
        for tablename, table in tables.items()
        if tablename.endswith("_rt_mapping")
    ]
    for table in record_type_tables:
        s = select([table])
        result = engine.execute(s)
        record_type_rows = list(result)
        for row in record_type_rows:
            record_type_id = row["record_type_id"]
            developer_name = row["developer_name"]
            rc[record_type_id] = developer_name
    return rc


def main(db_url):
    oids = {}
    objs_by_name = {}
    relationships = nx.DiGraph()

    engine = create_engine(db_url)
    metadata = MetaData(bind=engine)
    base = automap_base(bind=engine, metadata=metadata)
    base.prepare(engine, reflect=True)

    record_types = find_record_types(engine, metadata.tables)

    for tablename, table in metadata.tables.items():
        s = select([table])
        result = engine.execute(s)
        rows = list(result)
        for row in rows:
            fields = {undo_snake_case(n): v for n, v in row.items() if v}
            obj = {"object": tablename}
            oid = fields.pop("sf_id", None) or fields.pop("sf_Id", None)

            nick = fields.get("Name") or fields.get("name") or person_name(fields) or ""
            obj["nickname"] = " ".join([tablename, oid or str(id(obj)), nick]).strip()

            oids[oid] = obj["nickname"]
            obj["fields"] = fields
            objs_by_name[obj["nickname"]] = obj

    for obj in objs_by_name.values():
        fixup(obj, oids, record_types, relationships)

    objs = []
    cycles = nx.simple_cycles(relationships)
    for cycle in cycles:
        for nodenum in range(len(cycle) - 1):
            frm = cycle[nodenum]
            to = cycle[nodenum + 1]
            if relationships.has_edge(frm, to):
                relationships.remove_edge(frm, to)

    order = list(nx.algorithms.dag.topological_sort(relationships))
    for node in order:
        obj = objs_by_name.get(node)
        if obj:
            objs.append(obj)
        else:
            assert node in record_types
            continue

    return objs


objs = main("sqlite:////tmp/data.db")
dump(objs, sys.stdout, sort_keys=False)
