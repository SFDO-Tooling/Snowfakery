from multiprocessing import Process, set_start_method
from threading import Thread
from time import time, sleep
from tempfile import TemporaryDirectory
from pathlib import Path
from collections import defaultdict
import locale

import click
from sqlalchemy import create_engine, inspect

from snowfakery import generate_data

benchmark_1 = Path(__file__).parent / "benchmark_1.yml"
try:
    locale.setlocale(locale.LC_ALL, "")
except locale.Error as e:
    print(str(e))


@click.command()
@click.argument("recipe", type=click.Path(), default=str(benchmark_1))
@click.option("--num-records", type=int, default=100_000)
@click.option("--num-records-tablename", type=str, default="Account")
@click.option("--number-of-processes", type=int, default=0)
@click.option("--number-of-threads", type=int, default=0)
def snowbench(
    num_records,
    num_records_tablename,
    recipe,
    number_of_processes=0,
    number_of_threads=0,
):
    """A benchmarking tool for Snowfakery and Snowfakery recipes.

    Note that Snowfakery itself is not multi-threaded or multi-process,
    but it takes only a few lines of code to wrap it in a parallel
    processing context. For example, it might be a few lines of
    shell script or 10 lines of Python code.

    The sweet spot for "number_of_processes" is usually the number of
    CPU cores you have. Processes are usually faster than threads for
    Snowfakery.

    In some weird circumstances number_of_processes=1 may behave
    differently than the default behaviour, because the single
    execution process is spawned off into a sub-process instead
    of being executed inline.
    """
    with TemporaryDirectory() as tempdir, click.progressbar(
        label="Benchmarking", length=num_records, show_eta=False
    ) as progress_bar:

        start = time()
        Thread(
            daemon=True,
            target=status,
            args=[
                tempdir,
                num_records,
                num_records_tablename,
                progress_bar,
            ],
        ).start()
        if not number_of_processes and not number_of_threads:
            print(
                "--number-of-processes and --number-of-threads not supplied.\n"
                "Using a single inline execution unit."
            )
            output_file = Path(tempdir) / "generated_data.db"
            snowfakery(recipe, num_records, num_records_tablename, output_file)
        else:
            multithreaded_test(
                recipe,
                num_records,
                num_records_tablename,
                tempdir,
                number_of_processes,
                number_of_threads,
            )
        progress_bar.update(num_records)
        report_databases(tempdir, start, num_records_tablename)


def multithreaded_test(
    recipe,
    num_records,
    num_records_tablename,
    tempdir,
    number_of_processes,
    number_of_threads,
):
    num_workers = number_of_processes + number_of_threads

    def make_args(tempdir, prefix, idx):
        output_file = f"{tempdir}/sqlite_{prefix}_{idx}.db"
        return recipe, num_records // num_workers, num_records_tablename, output_file

    processes = [
        Process(target=snowfakery, args=make_args(tempdir, "p", idx))
        for idx in range(number_of_processes)
    ]
    threads = [
        Thread(target=snowfakery, args=make_args(tempdir, "t", idx))
        for idx in range(number_of_threads)
    ]

    workers = threads + processes
    start = time()
    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    duration = time() - start
    return duration


def count_databases(tempdir):
    databases = Path(tempdir).glob("*.db")
    counts = defaultdict(int)
    for database in databases:
        count_database(database, counts)
    return dict(counts)


def status(tempdir, num_records, num_records_tablename, progress_bar):
    start = time()
    sleep(2)
    previous_count = 0
    for i in range(1, 10 ** 20):
        sleep(1)
        if i in (2, 5, 10, 20, 30, 45, 90, 150) or (i % 60 == 0):
            print()
            current_count = report_databases(tempdir, start, num_records_tablename)
            progress_bar.update(current_count - previous_count)
            previous_count = current_count


def report_databases(tempdir, start_time, relevant_table_name):
    print()
    print()
    counts = count_databases(tempdir)
    for name, count in counts.items():
        print(name, f"{count:n}")
    total = sum(counts.values())
    duration = time() - start_time
    print(
        f"{total:n} records /",
        f"{int(duration):n} seconds =~",
        f"{int(total / duration):n}",
        "records per second",
        f"\n= {int((total / duration) * 3600):n}",
        "records per hour",
        f"\n= {int((total / duration) * 3600 *24):n}",
        "records per day",
    )
    return counts[relevant_table_name]


def count_database(filename, counts):
    dburl = f"sqlite:///{filename}?mode=ro"
    engine = create_engine(dburl)
    insp = inspect(engine)
    tables = insp.get_table_names()
    for table in tables:
        counts[table] += count_table(engine, table)
    return counts


def count_table(engine, tablename):
    return engine.execute(f"select count(Id) from '{tablename}'").first()[0]


def snowfakery(recipe, num_records, tablename, outputfile):
    assert Path(recipe).exists(), recipe
    output = f"sqlite:///{outputfile}"
    print(output)
    generate_data(
        recipe,
        target_number=(num_records, tablename),
        dburl=output,
    )


def main():
    snowbench.main(prog_name="snowbench")


if __name__ == "__main__":  # pragma: no cover
    set_start_method("spawn")
    main()
