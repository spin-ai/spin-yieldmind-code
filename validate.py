"""Repository self-check: run `python validate.py` before pushing.

Mirrors the platform contract closely enough for CI:
· function entry is `run(ctx, inputs, steps)` and returns an object;
· no network / file / process / dynamic-exec imports or calls;
· manifest has id/title/output_schema and only references skills/ modules.
"""

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BANNED_IMPORTS = {
    "os", "sys", "socket", "subprocess", "requests", "httpx", "urllib", "pathlib",
    "shutil", "tempfile", "pickle", "ctypes", "multiprocessing", "threading",
    "importlib", "builtins", "glob", "io",
}
BANNED_NAMES = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint",
                "globals", "locals", "vars", "getattr", "setattr", "delattr", "type",
                "object", "super", "memoryview"}
ALLOWED_OUTPUT = {"number", "integer", "string", "boolean", "array", "object", "any"}
ID_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def check_code(path, need_run):
    code = path.read_text("utf-8")
    if len(code) > 20000:
        raise ValueError("代码超过 20,000 字符")
    tree = ast.parse(code, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.Await)):
            raise ValueError(f"{type(node).__name__} 不允许")
        if isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split(".")[0]
                if root in BANNED_IMPORTS:
                    raise ValueError(f"禁止导入 {a.name}")
        if isinstance(node, ast.ImportFrom):
            if node.level:
                raise ValueError("不允许相对导入")
            root = (node.module or "").split(".")[0]
            if root in BANNED_IMPORTS:
                raise ValueError(f"禁止导入 {node.module}")
        if isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in BANNED_NAMES:
                raise ValueError(f"禁止使用 {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError(f"禁止访问属性 {node.attr}")
    if need_run:
        has_run = any(isinstance(n, ast.FunctionDef) and n.name == "run" for n in tree.body)
        if not has_run:
            raise ValueError("必须定义 run(ctx, inputs, steps)")


def main():
    errors = []
    skills = set()
    for p in sorted((ROOT / "skills").rglob("*.py")):
        try:
            check_code(p, need_run=False)
            rel = p.relative_to(ROOT).with_suffix("")
            parts = list(rel.parts)
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            skills.add(".".join(parts))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{p}: {exc}")

    ids = set()
    for folder in sorted((ROOT / "functions").iterdir()):
        if not folder.is_dir():
            continue
        mpath = folder / "manifest.json"
        if not mpath.is_file():
            errors.append(f"{folder}: 缺少 manifest.json")
            continue
        try:
            m = json.loads(mpath.read_text("utf-8"))
            if not ID_RE.fullmatch(str(m.get("id") or "")):
                raise ValueError("id 必须形如 group/name")
            if not m.get("title"):
                raise ValueError("缺少 title")
            if m.get("network"):
                raise ValueError("network 必须为 false")
            schema = m.get("output_schema") or {}
            if not schema:
                raise ValueError("output_schema 不能为空")
            for key, spec in schema.items():
                t = (spec.get("type") if isinstance(spec, dict) else spec) or "any"
                if str(t).lower() not in ALLOWED_OUTPUT:
                    raise ValueError(f"output_schema.{key} 类型不支持：{t}")
            for s in m.get("skills") or []:
                if s not in skills:
                    raise ValueError(f"skills 不存在：{s}")
            entry = folder / str(m.get("entry") or "function.py")
            if not entry.is_file():
                raise ValueError(f"找不到入口 {entry.name}")
            check_code(entry, need_run=True)
            if m["id"] in ids:
                raise ValueError("id 重复")
            ids.add(m["id"])
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{folder}: {exc}")

    if errors:
        print("校验失败：")
        for e in errors:
            print(" -", e)
        return 1
    print(f"OK：{len(ids)} 个函数，{len(skills)} 个 skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
