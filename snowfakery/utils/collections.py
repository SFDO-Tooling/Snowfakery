class OrderedSet(dict):
    """Simplistic ordered set.

    Other methods can be added later or we can swap it out for
    a 3rd party version."""

    def __init__(self, vals=()):
        self.update(zip(vals, vals))

    def add(self, val):
        self[val] = val

    def remove(self, val):
        del self[val]
