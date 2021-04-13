import typing as T

from sqlalchemy import create_engine, MetaData, Column, Table, Unicode
from sqlalchemy.sql import select

from snowfakery.data_gen_exceptions import DataGenError


def create_cci_record_type_tables(db_url: str):
    """Create record type tables that CCI expects"""
    engine = create_engine(db_url)
    metadata = MetaData(bind=engine)
    metadata.reflect(views=True)
    with engine.connect() as connection:
        for tablename, table in list(metadata.tables.items()):
            record_type_column = find_record_type_column(
                tablename, table.columns.keys()
            )
            if record_type_column:
                rt_table = _create_record_type_table(tablename, metadata)
                rt_table.create()
                _populate_rt_table(connection, table, record_type_column, rt_table)


def _create_record_type_table(tablename: str, metadata: MetaData):
    """Create a table to store mapping between Record Type Ids and Developer Names."""
    rt_map_fields = [
        Column("record_type_id", Unicode(18), primary_key=True),
        Column("developer_name", Unicode(255)),
    ]
    rt_map_table = Table(tablename + "_rt_mapping", metadata, *rt_map_fields)
    return rt_map_table


def _populate_rt_table(connection, table: Table, columnname: str, rt_table: Table):
    column = getattr(table.columns, columnname)
    query_res = connection.execute(
        select([column]).where(column is not None).distinct()
    )
    record_types = [res[0] for res in query_res if res[0]]

    if record_types:
        insert_stmt = rt_table.insert()
        rows = [
            dict(zip(rt_table.columns.keys(), (rtname, rtname)))
            for rtname in record_types
        ]
        connection.execute(insert_stmt, rows)


def find_record_type_column(tablename: str, columnnames: T.Iterable[str]):
    """Find the record type column from a sequence of column names"""
    record_type_columns = [
        t
        for t in columnnames
        if t.lower().replace("_", "") in ("recordtype", "recordtypeid")
    ]
    if len(record_type_columns) > 1:
        raise DataGenError(
            f"Multiple record type columns for {tablename}: {record_type_columns}"
        )

    if len(record_type_columns) == 1:
        return record_type_columns[0]
