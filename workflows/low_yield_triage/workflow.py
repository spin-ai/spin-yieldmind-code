"""Workflow-as-code：Studio 里「从代码库创建/重建」会执行 build() 生成节点。"""

from skills.workflow import approval, code, condition, output, spec, tool

TEMPLATE = (
    "LOT ${ctx.lot} · 良率 ${steps.n_summary.raw.yield}%\n\n"
    "可疑资源：${steps.n_score.top_resource}（评分 ${steps.n_score.suspect_score}）\n\n"
    "处置建议已进入审批：${steps.n_ap.node}"
)


def build(ctx):
    summary = tool("n_summary", "lot_summary", "批次良率总览", args={"lot_id": "${inputs.lot}"})
    pareto = tool("n_pareto", "lot_pareto", "失效 Pareto", args={"lot_id": "${inputs.lot}"}, depends_on=["n_summary"])
    common = tool("n_common", "commonality", "机台 / 腔体共通性", args={"dim": "tester"}, depends_on=["n_pareto"])
    gate = condition(
        "n_gate",
        "${steps.n_summary.raw.yield} < ${inputs.target}",
        on_true="n_score", on_false="n_ok",
        title="低良率判定", depends_on=["n_common"],
    )
    score = code(
        "n_score", "可疑资源评分",
        function="yield/suspect_score",
        depends_on=["n_gate"],
        inputs={"lift_threshold": 3.0},
    )
    ap = approval("n_ap", "工程师确认", role="PE", sla_min=30, depends_on=["n_score"])
    out = output("n_out", "结论与证据链", template=TEMPLATE, depends_on=["n_ap"])
    ok = output("n_ok", "良率正常", template="LOT ${ctx.lot} 良率未低于目标，无需处置。", depends_on=["n_gate"])
    return spec(
        "低良率归因与处置（代码定义）",
        [summary, pareto, common, gate, score, ap, out, ok],
        description="由 spin-yieldmind-code/workflows/low_yield_triage 自动生成。",
        inputs={
            "lot": {"type": "string", "required": True, "source": "ctx.lot"},
            "target": {"type": "number", "default": 96.5, "required": False},
        },
    )
