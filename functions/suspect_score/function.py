"""Example: score the top suspect resource from an upstream commonality node."""

from skills.contract import number, rows


def run(ctx, inputs, steps):
    common = steps.get("n_common") if isinstance(steps, dict) else {}
    suspects = rows((common or {}).get("suspects"))
    threshold = number(inputs.get("lift_threshold"), 3.0)
    scored = [r for r in suspects if number(r.get("lift"), 0.0) >= threshold]

    top = None
    for r in scored:
        if top is None or number(r.get("lift"), 0.0) > number(top.get("lift"), 0.0):
            top = r
    if top is None:
        return {"suspect_score": 0, "top_resource": "", "sample_size": 0}

    tester = str(top.get("tester") or "")
    chamber = str(top.get("chamber") or "")
    resource = tester if not chamber else tester + "/" + chamber
    score = round(number(top.get("lift"), 0.0) / 10.0, 2)
    return {"suspect_score": score, "top_resource": resource, "sample_size": len(scored)}
