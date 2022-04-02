import sqlite3


class RowHistory:
    def __init__(self):
        self.conn = _make_history_table(":memory:")

    def write_row(self, tablename: str, nickname: str, row: dict):
        self.conn.execute(
            "INSERT INTO snowfakery_history VALUES (?, ?, ?, ?)",
            (
                str(id),
                tablename,
                nickname,
                repr(row),
            ),
        )


def _make_history_table(dbname):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS snowfakery_history;")
    c.execute(
        "CREATE TABLE snowfakery_history (id INTEGER NOT NULL, tablename VARCHAR(255) NOT NULL, nickname VARCHAR(255) , data VARCHAR NOT NULL)"
    )
    conn.commit()
    return conn
