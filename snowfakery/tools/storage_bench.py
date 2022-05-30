""" Benchmarking tool for the RowHistory backing database"""

from snowfakery.row_history import RowHistory
from time import time

COUNT = 200_000


def main(count):
    rh: RowHistory = RowHistory()
    start = time()
    for i in range(0, COUNT, 4):
        rh.save_row(
            "table",
            None,
            {
                "id": i,
                "blah": "blah",
            },
        )

        rh.save_row(
            "table",
            "Nicknamed",
            {
                "id": i + 1,
                "blah": "blah",
            },
        )

        rh.save_row(
            "table",
            "Nicknamed2",
            {
                "id": i + 2,
                "blah": "blah",
            },
        )

        if i % 1000 == 0:
            nickname = "Sparse"
        else:
            nickname = "Unused"

        rh.save_row(
            "table",
            nickname,
            {
                "id": i + 3,
                "blah": "blah",
            },
        )

    end = time()
    print("Saved", end - start)
    start = time()
    for i in range(0, COUNT):
        rh.load_row("table", i)
        rh.load_nicknamed_row("table", "Nicknamed", i)
        rh.load_nicknamed_row("table", "Nicknamed2", i)
        rh.load_nicknamed_row("table", "Sparse", i)
    end = time()
    print(end - start)


main(COUNT)
