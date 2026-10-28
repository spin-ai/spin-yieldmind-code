"""Example: yield gap vs target + worst wafer, using the shared skills library."""

from skills.contract import number
from skills.yield_utils import node_yield, worst_wafer


def run(ctx, inputs, steps):
    node_id = str(inputs.get("summary_node") or "n_summary")
    target = number(inputs.get("target"), 96.5)
    value = node_yield(steps, node_id)
    if value is None:
        value = 0.0
    gap = round(target - value, 2)
    return {
        "yield_pct": round(value, 4),
        "gap_pp": gap,
        "worst_wafer": worst_wafer(steps, node_id),
        "lot": str((ctx or {}).get("lot") or ""),
    }
