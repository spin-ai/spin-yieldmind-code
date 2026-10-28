"""Workflow-as-code：用代码库函数做极坐标指纹识别。"""

from skills.workflow import code, output, spec, tool

TEMPLATE = (
    "LOT ${ctx.lot} · Wafer ${steps.n_fp.wafer_id}\n\n"
    "指纹结论：**${steps.n_fp.label}**（${steps.n_fp.signature}）\n\n"
    "概率 ${steps.n_fp.score} · 领先 ${steps.n_fp.margin} · 距离 ${steps.n_fp.distance}\n\n"
    "建议：按极坐标指纹对应的工艺 / 搬运 / 探针动作复核。"
)


def build(ctx):
    summary = tool("n_summary", "lot_summary", "良率总览", args={"lot_id": "${inputs.lot}"})
    map_node = tool("n_map", "wafer_map", "晶圆图", args={"lot_id": "${inputs.lot}"}, depends_on=["n_summary"])
    fp = code(
        "n_fp", "极坐标指纹识别",
        function="yield/wafer_polar_fingerprint",
        inputs={"map_node": "n_map"},
        depends_on=["n_map"],
    )
    out = output("n_out", "指纹结论", template=TEMPLATE, depends_on=["n_fp"])
    return spec(
        "极坐标指纹识别（代码定义）",
        [summary, map_node, fp, out],
        description="由 code_repo/workflows/wafer_polar_fingerprint 自动生成。",
        inputs={
            "lot": {"type": "string", "required": True, "source": "ctx.lot"},
        },
    )
