import typing as T

from sqlalchemy import create_engine, MetaData, Column, Table, Unicode
from sqlalchemy.sql import select
from sqlalchemy.engine.base import Connection
from snowfakery.data_gen_exceptions import DataGenError


def create_cci_record_type_tables(db_url: str):
    """Create record type tables that CCI expects"""
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(views=True, bind=engine)
    with engine.connect() as connection, connection.begin():  # type: ignore
        for tablename, table in list(metadata.tables.items()):  # type: ignore
            record_type_column = find_record_type_column(
                tablename, table.columns.keys()
            )
            if record_type_column:
                rt_table = _create_record_type_table(tablename, metadata)
                rt_table.create(bind=connection)
                _populate_rt_table(connection, table, record_type_column, rt_table)


def _create_record_type_table(tablename: str, metadata: MetaData) -> Table:
    """Create a table to store mapping between Record Type Ids and Developer Names."""
    rt_map_fields = [
        Column("record_type_id", Unicode(18), primary_key=True),
        Column("developer_name", Unicode(255)),
    ]
    rt_map_table = Table(tablename + "_rt_mapping", metadata, *rt_map_fields)
    return rt_map_table


def _populate_rt_table(
    connection: Connection, table: Table, columnname: str, rt_table: Table
):
    column = getattr(table.columns, columnname)
    query_res = connection.execute(select(column).where(column is not None).distinct())
    record_types = [res[0] for res in query_res if res[0]]  # type: ignore

    if record_types:
        insert_stmt = rt_table.insert()
        rows = [
            dict(zip(rt_table.columns.keys(), (rtname, rtname)))  # type: ignore
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
