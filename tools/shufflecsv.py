from sys import stdin, stdout
from random import shuffle

# Shuffle a CSV on stdin to stdout
#
# It's much more efficient to shuffle a CSV once instead of every
# time you run a Snowfakey recipe. So this script does it.


def main():
    firstline = stdin.readline()
    rows = stdin.readlines()

    stdout.write(firstline)
    shuffle(rows)
    stdout.writelines(rows)


main()
