"""Property lookup over the generated range tables (bisect, O(log n))."""
import bisect

from ._data import GCB, WB, SB, INCB, EMOJI


def _build(table):
    """Flatten {name: ranges} into sorted parallel arrays for bisect."""
    starts, ends, names = [], [], []
    for name, ranges in table.items():
        for lo, hi in ranges:
            starts.append(lo)
            ends.append(hi)
            names.append(name)
    order = sorted(range(len(starts)), key=lambda i: starts[i])
    return (
        tuple(starts[i] for i in order),
        tuple(ends[i] for i in order),
        tuple(names[i] for i in order),
    )


def _make_lookup(table, default):
    starts, ends, names = _build(table)

    def lookup(cp):
        i = bisect.bisect_right(starts, cp) - 1
        if i >= 0 and cp <= ends[i]:
            return names[i]
        return default

    return lookup


def _make_flag(table, name):
    ranges = table[name]
    starts = tuple(lo for lo, _ in ranges)
    ends = tuple(hi for _, hi in ranges)

    def flag(cp):
        i = bisect.bisect_right(starts, cp) - 1
        return i >= 0 and cp <= ends[i]

    return flag


gcb = _make_lookup(GCB, "Other")
wb = _make_lookup(WB, "Other")
sb = _make_lookup(SB, "Other")
incb = _make_lookup(INCB, "None")
is_extended_pictographic = _make_flag(EMOJI, "Extended_Pictographic")
