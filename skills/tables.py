"""Table helpers for workflow code nodes."""

from skills.contract import number, rows


def table_rows(table):
    return rows(table)


def column(records, key):
    return [r.get(key) for r in rows(records)]


def numbers(records, key):
    return [number(r.get(key), None) for r in rows(records) if number(r.get(key), None) is not None]


def group_by(records, key):
    out = {}
    for r in rows(records):
        k = str(r.get(key) if r.get(key) is not None else "")
        out.setdefault(k, []).append(r)
    return out


def top_by(records, key, n=5, reverse=True):
    data = rows(records)
    data.sort(key=lambda r: number(r.get(key), 0.0), reverse=reverse)
    return data[: max(0, int(n))]


def pick(record, keys, default=None):
    for key in keys:
        if isinstance(record, dict) and record.get(key) is not None:
            return record[key]
    return default
