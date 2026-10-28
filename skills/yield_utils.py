"""Yield helpers: read yield / worst wafer from upstream tool results."""

from skills.contract import number


def node_output(steps, node_id):
    if not isinstance(steps, dict):
        return {}
    out = steps.get(node_id)
    return out if isinstance(out, dict) else {}


def node_yield(steps, node_id):
    """优先读 raw.yield（数值），其次读 metrics 里的良率百分比。"""
    out = node_output(steps, node_id)
    raw = out.get("raw") if isinstance(out.get("raw"), dict) else {}
    v = number(raw.get("yield"), None)
    if v is not None:
        return round(v, 4)
    for m in out.get("metrics") or []:
        if not isinstance(m, dict):
            continue
        label = str(m.get("label") or "").strip()
        if label in ("良率", "yield", "Yield"):
            return number(m.get("value"), None)
    return None


def worst_wafer(steps, node_id):
    out = node_output(steps, node_id)
    raw = out.get("raw") if isinstance(out.get("raw"), dict) else {}
    wafers = raw.get("wafers") or []
    best = None
    for w in wafers:
        if not isinstance(w, dict):
            continue
        y = number(w.get("yield"), None)
        if y is None:
            continue
        if best is None or y < number(best.get("yield"), 0.0):
            best = w
    if best is None:
        return ""
    return str(best.get("wafer_id") or "")
