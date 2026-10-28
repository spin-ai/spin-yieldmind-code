# YieldMind 工作流代码库（skills + functions）

这个仓库用于托管「工作流代码节点」：平台会把它同步到后端本地目录，
Studio 里可以从代码库加载函数（代码 + 契约一起带入节点），也可以让用户基于
`skills/` 里的安全辅助库写代码。

## 目录约定

```text
README.md
skills/                     # 平台/团队维护的辅助库（只读依赖）
  __init__.py
  contract.py               # 入参/行数据/数值解析
  stats.py                  # mean / std / percentile / cpk
  tables.py                 # 表格 → 行、分组、Top N
  yield.py                  # 从上游步骤结果里取良率 / 最差片
functions/<folder>/
  manifest.json             # 函数 id、输入、输出 Schema、运行时、超时、依赖的 skills
  function.py               # def run(ctx, inputs, steps) -> dict
workflows/<folder>/
  manifest.json             # 工作流 id、标题、版本、tags
  workflow.py               # def build(ctx) -> WorkflowSpec（节点由代码自动生成）
```

## 函数契约（必须满足）

1. 入口固定：`def run(ctx, inputs, steps)`，返回 **dict**。
2. `ctx`：当前运行上下文（`lot` / `stage` / `product` …），只读。
3. `inputs`：manifest 里声明的输入（默认值会带入工作流节点的输入绑定）。
4. `steps`：上游节点输出，按节点 id 访问，例如 `steps["n_common"]["suspects"]`。
5. 返回值必须覆盖 manifest 的 `output_schema` 全部字段，类型匹配。
6. **禁止**：网络、文件、子进程、动态执行、第三方 pip 安装、直接写生产库。
   副作用请用工作流的 `action + approval` 节点。
7. 代码 ≤ 20,000 字符；超时 1–10 秒；默认无网络。

## 工作流也可以代码定义（workflow-as-code）

`workflows/<name>/workflow.py` 里用 DSL 生成节点，平台执行 `build()` 后转成 WorkflowSpec：

```python
from skills.workflow import approval, code, condition, output, spec, tool

def build(ctx):
    return spec("低良率归因", [
        tool("n_summary", "lot_summary", "良率总览", args={"lot_id": "${inputs.lot}"}),
        condition("n_gate", "${steps.n_summary.raw.yield} < ${inputs.target}",
                  on_true="n_score", on_false="n_ok", depends_on=["n_summary"]),
        code("n_score", "可疑资源评分", function="yield/suspect_score", depends_on=["n_gate"]),
        approval("n_ap", "工程师确认", depends_on=["n_score"]),
        output("n_out", "结论", depends_on=["n_ap"]),
        output("n_ok", "良率正常", depends_on=["n_gate"]),
    ])
```

- `spec / tool / condition / code / approval / action / output / chain` 是 DSL；
- `code(function="yield/xxx")` 直接引用同仓库 `functions/` 的函数，不用复制代码；
- 平台会执行 `build()`（受限沙箱）、校验 WorkflowSpec、替换函数快照；
- 代码节点仍为「待评审」，发布时冻结 `code_hash`；
- 在 `/28` 用「从代码库创建」或「代码重建」导入。

## 可以使用的 skills

```python
from skills.contract import rows, number, require
from skills.stats import mean, std, percentile, cpk
from skills.tables import table_rows, column, group_by, top_by
from skills.yield_utils import node_yield, worst_wafer
from skills.workflow import spec, tool, condition, code, approval, action, output, chain
```

`skills/` 里的代码同样受静态校验（不允许 `os` / `socket` / `open` / `eval` 等），
因此可以安全地作为用户代码的公共依赖。

## 本地校验

```bash
python validate.py
```

GitHub Actions 已配置 `.github/workflows/validate.yml`，每次 push / PR 自动跑。
平台同步时还会再校验一次；校验不通过的函数不会出现在 Studio 的代码库列表里。

## 接入平台

在后端环境变量里配置：

```bash
YIELDMIND_CODE_REPO_URL=https://github.com/<org>/<repo>.git
YIELDMIND_CODE_REPO_BRANCH=main
# 私有仓库才需要（只注入 HTTPS URL，不落盘、不回显）
YIELDMIND_CODE_REPO_TOKEN=ghp_xxx
# 可选：启动时自动同步
YIELDMIND_CODE_REPO_AUTOSYNC=1
```

然后在 `/28` 任意代码节点的检查器里点「从代码库加载」。同步后：
- 节点会带入代码、`input_bindings` 默认值、输出 Schema、运行时/超时；
- 来源记录在节点证据里（repo / commit / path / version）；
- 代码评审仍必须人工通过，`code_hash` 随工作流版本冻结。
