from sqlalchemy import create_engine, Table
from sqlalchemy.engine import Engine

from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    MetaData,
    insert,
    Index,
    JSON,
    PickleType,
    UniqueConstraint,
)

from snowfakery.plugins import ObjectRow


class RowHistory:
    def __init__(self):
        self.db = create_engine("sqlite://")
        self.table = _make_history_table(self.db)
        self.connection = self.db.connect()
        self.insert = insert(self.table)

    def write_row(self, tablename: str, nickname: str, row: dict):
        stmt = self.insert.values(
            id=row["id"], table=tablename, nickname=nickname, data=str(row)
        )
        # TODO: experiment with commit-less operatrion and its performance implications
        # with self.connection.begin():
        self.connection.execute(stmt)


def _make_history_table(db: Engine) -> Table:
    metadata = MetaData(bind=db)
    history_table = Table(
        "snowfakery_history",
        metadata,
        Column("id", Integer, nullable=False),
        Column("table", String(30), nullable=False),
        Column("nickname", String),
        Column(
            "data", String, nullable=True
        ),  # TODO: experiment with type string, JSON
        # Index("identifier", "id", "table", unique=True),
        # UniqueConstraint(
        #     "id",
        #     "table",
        # ),
    )
    metadata.create_all()
    return history_table
