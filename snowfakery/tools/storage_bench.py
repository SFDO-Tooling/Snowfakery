""" Benchmarking tool for the RowHistory backing database"""

from snowfakery.row_history import RowHistory
from snowfakery.object_rows import RowHistoryCV
from time import time

COUNT = 200_000


def main(count):
    rh: RowHistory = RowHistory()
    RowHistoryCV.set(rh)
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
        assert rh.random_row_reference("table", "current-iteration", False).blah
        assert rh.random_row_reference("Nicknamed", "current-iteration", False).blah
        assert rh.random_row_reference("Nicknamed2", "current-iteration", False).blah
        assert rh.random_row_reference("Sparse", "current-iteration", False).blah
    end = time()
    print("Loaded", end - start)


main(COUNT)
