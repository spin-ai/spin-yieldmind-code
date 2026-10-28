"""Input/row parsing helpers shared by workflow code functions."""


def rows(value):
    """把 list[dict] 或 {head, rows} 表格统一成 list[dict]。"""
    if isinstance(value, list):
        return [r for r in value if isinstance(r, dict)]
    if isinstance(value, dict):
        head = value.get("head") or []
        body = value.get("rows") or []
        if head and body:
            out = []
            for r in body:
                if isinstance(r, dict):
                    out.append(r)
                elif isinstance(r, list):
                    out.append({str(head[i]): (r[i] if i < len(r) else None) for i in range(len(head))})
            return out
        inner = value.get("rows")
        if isinstance(inner, list):
            return [r for r in inner if isinstance(r, dict)]
    return []


def number(value, default=None):
    """把 93.1 / '93.1%' / ' 1,234 ' / True 解析成 float；失败返回 default。"""
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def require(inputs, key, default=None):
    """取必填输入；缺失时明确报错（节点会显示真实错误而不是静默跑错）。"""
    if inputs is None or key not in inputs or inputs[key] is None or str(inputs[key]).strip() == "":
        if default is not None:
            return default
        raise ValueError("缺少必填输入：" + key)
    return inputs[key]


def clamp(value, low, high):
    return max(low, min(high, value))


def round_or(value, digits=4, default=0.0):
    v = number(value, None)
    if v is None:
        return default
    return round(v, digits)
