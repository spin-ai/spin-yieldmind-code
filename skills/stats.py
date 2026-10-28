"""Pure-python statistics helpers (no numpy required)."""

import math
import statistics


def mean(values):
    data = [float(v) for v in values if v is not None]
    return statistics.fmean(data) if data else 0.0


def std(values, sample=True):
    data = [float(v) for v in values if v is not None]
    if len(data) < 2:
        return 0.0
    return statistics.stdev(data) if sample else statistics.pstdev(data)


def median(values):
    data = [float(v) for v in values if v is not None]
    return statistics.median(data) if data else 0.0


def percentile(values, p):
    """线性插值百分位，p in [0, 100]。"""
    data = sorted(float(v) for v in values if v is not None)
    if not data:
        return 0.0
    p = max(0.0, min(100.0, float(p)))
    idx = (len(data) - 1) * p / 100.0
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return data[lo]
    return data[lo] + (data[hi] - data[lo]) * (idx - lo)


def zscore(value, values):
    data = [float(v) for v in values if v is not None]
    sd = std(data)
    if not data or sd == 0:
        return 0.0
    return round((float(value) - mean(data)) / sd, 4)


def cpk(mean_value, std_value, lower=None, upper=None):
    """双侧/单侧 Cpk；规格缺失或 σ=0 时返回 None。"""
    m = float(mean_value)
    s = float(std_value)
    if s <= 0:
        return None
    parts = []
    if lower is not None:
        parts.append((m - float(lower)) / (3.0 * s))
    if upper is not None:
        parts.append((float(upper) - m) / (3.0 * s))
    if not parts:
        return None
    return round(min(parts), 4)
