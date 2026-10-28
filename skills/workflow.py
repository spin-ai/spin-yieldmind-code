"""Workflow-as-code DSL: build() returns a WorkflowSpec dict.

Usage:
    from skills.workflow import spec, tool, code, output

    def build(ctx):
        return spec("我的工作流", [
            tool("n_summary", "lot_summary", "良率总览", args={"lot_id": "${inputs.lot}"}),
            code("n_score", "评分", function="yield/yield_gap", depends_on=["n_summary"]),
            output("n_out", "结论", depends_on=["n_score"]),
        ])
"""


def spec(name, nodes, description="", inputs=None, policies=None, triggers=None):
    """组装 WorkflowSpec。nodes 用下面的构造函数生成。"""
    return {
        "schema_version": 1,
        "name": name,
        "description": description,
        "origin": "repo",
        "status": "draft",
        "input_schema": inputs or {
            "lot": {"type": "string", "required": True, "source": "ctx.lot"},
        },
        "policies": policies or {
            "max_runtime_s": 600, "concurrency": 1, "audit": True, "data_scope": "inherit",
        },
        "triggers": triggers or [{"type": "manual"}],
        "nodes": nodes,
    }


def _node(id, kind, title, depends_on):
    return {
        "id": id,
        "type": kind,
        "title": title,
        "depends_on": list(depends_on or []),
        "enabled": True,
    }


def tool(id, ref, title="", args=None, depends_on=None):
    """平台工具节点：ref 必须是已注册工具（lot_summary / lot_pareto / ...）。"""
    node = _node(id, "tool", title or ref, depends_on)
    node["ref"] = ref
    node["args"] = args or {}
    node["output"] = {"kinds": ["metrics", "table"], "default": "metrics"}
    return node


def condition(id, expr, on_true="", on_false="", title="条件判定", depends_on=None):
    """条件节点：expr 用 ${steps.xxx} / ${inputs.xxx} 引用；分支只在命中时执行。"""
    node = _node(id, "condition", title, depends_on)
    node["expr"] = expr
    branches = {}
    if on_true:
        branches["true"] = on_true
    if on_false:
        branches["false"] = on_false
    node["branches"] = branches
    return node


def code(id, title="", function="", source="", output_schema=None, depends_on=None,
         inputs=None, timeout_s=5):
    """代码节点。

    · function="yield/xxx"：引用代码库 functions/ 里的函数（推荐）；
    · source="..."：直接内联代码（必须定义 run(ctx, inputs, steps)）。
    """
    node = _node(id, "code", title or "自定义代码", depends_on)
    node["timeout_s"] = timeout_s
    if function:
        node["repo_function"] = function
    if source:
        node["code"] = source
    if output_schema:
        node["output_schema"] = output_schema
    if inputs:
        node["input_bindings"] = inputs
    return node


def approval(id, title="工程师确认", role="PE", sla_min=30, depends_on=None):
    node = _node(id, "approval", title, depends_on)
    node["role"] = role
    node["sla_min"] = sla_min
    return node


def action(id, ref, title="", args=None, depends_on=None, dry_run=True, approval_node=""):
    """副作用动作：必须绑定 approval 节点（发布前校验）。"""
    node = _node(id, "action", title or ref, depends_on)
    node["ref"] = ref
    node["args"] = args or {}
    node["dry_run"] = dry_run
    if approval_node:
        node["approval_node"] = approval_node
    return node


def output(id, title="结论与证据链", template="", depends_on=None):
    node = _node(id, "output", title, depends_on)
    node["template"] = template or "运行完成，已生成证据链。"
    node["format"] = "markdown"
    return node


def chain(nodes):
    """按数组顺序串成线性依赖（适合没有分支的流程）。"""
    out = []
    prev = ""
    for n in nodes:
        node = dict(n)
        deps = list(node.get("depends_on") or [])
        if prev and prev not in deps:
            deps.append(prev)
        node["depends_on"] = deps
        out.append(node)
        prev = node["id"]
    return out
