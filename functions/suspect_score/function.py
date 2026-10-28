"""Example: score the top suspect resource from an upstream commonality node."""

from skills.contract import number, rows


def _candidates(common):
    """兼容三种上游形态：suspects / raw.items / raw.groups / table（含中文列名）。"""
    direct = rows(common.get("suspects"))
    if direct:
        return direct
    raw = common.get("raw") if isinstance(common.get("raw"), dict) else {}
    items = rows(raw.get("items"))
    if items:
        return items
    groups = rows(raw.get("groups"))
    if groups:
        return groups
    return rows(common.get("table"))


def _resource(row):
    tester = str(row.get("tester") or "")
    chamber = str(row.get("chamber") or "")
    if tester:
        return tester if not chamber else tester + "/" + chamber
    for key in ("resource", "label", "组", "取值", "value"):
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            kind = row.get("type") or row.get("资源类型")
            return (str(kind) + " " + str(value)).strip() if kind else str(value)
    return ""


def run(ctx, inputs, steps):
    common = steps.get("n_common") if isinstance(steps, dict) else {}
    suspects = _candidates(common or {})
    threshold = number(inputs.get("lift_threshold"), 3.0)
    scored = [r for r in suspects if number(r.get("lift"), 0.0) >= threshold]

    top = None
    for r in scored:
        if top is None or number(r.get("lift"), 0.0) > number(top.get("lift"), 0.0):
            top = r
    if top is None:
        return {"suspect_score": 0, "top_resource": "", "sample_size": 0}

    score = round(number(top.get("lift"), 0.0) / 10.0, 2)
    return {"suspect_score": score, "top_resource": _resource(top), "sample_size": len(scored)}
