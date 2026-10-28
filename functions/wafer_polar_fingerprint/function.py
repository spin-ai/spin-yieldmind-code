"""极坐标指纹（代码库版本，与 analytics/signature.py 的 polar-fingerprint 同源）。

上游建议接 wafer_map 节点：函数默认读取 steps[map_node].raw.features；
也可以直接通过 inputs.features 传入同一套特征对象。
"""

import math

from skills.contract import number

CLASSES = ["Edge-Ring", "Center", "Donut", "Edge-Loc", "Loc", "Scratch", "Random", "Near-full", "none"]
LABELS = {
    "Edge-Ring": "边缘环带", "Center": "中心斑", "Donut": "中环带",
    "Edge-Loc": "边缘局部", "Loc": "局部簇", "Scratch": "划痕",
    "Random": "随机散布", "Near-full": "近全废", "none": "无明显签名",
}
FEATURES = [
    "fail_rate", "mean_r", "edge_ratio", "center_ratio", "mid_ratio",
    "radial_entropy", "angular_entropy", "sector_peak", "ring_peak",
    "edge_sector_peak", "edge_angular_entropy",
    "aspect", "compact", "cluster_frac", "n_clusters",
]
SCALE = {
    "fail_rate": 0.25, "mean_r": 0.25, "edge_ratio": 0.25,
    "center_ratio": 0.25, "mid_ratio": 0.25,
    "radial_entropy": 0.40, "angular_entropy": 0.40,
    "sector_peak": 0.25, "ring_peak": 0.25,
    "edge_sector_peak": 0.30, "edge_angular_entropy": 0.40,
    "aspect": 2.50, "compact": 0.30, "cluster_frac": 0.25, "n_clusters": 15.0,
}
PROTO = {
    "Edge-Ring": {"fail_rate": 0.20, "mean_r": 0.95, "edge_ratio": 1.00, "center_ratio": 0.00, "mid_ratio": 0.00,
                  "radial_entropy": 0.00, "angular_entropy": 1.00, "sector_peak": 0.13, "ring_peak": 1.00,
                  "edge_sector_peak": 0.13, "edge_angular_entropy": 1.00,
                  "aspect": 1.00, "compact": 0.15, "cluster_frac": 1.00, "n_clusters": 1},
    "Center": {"fail_rate": 0.12, "mean_r": 0.23, "edge_ratio": 0.00, "center_ratio": 1.00, "mid_ratio": 0.00,
               "radial_entropy": 0.46, "angular_entropy": 1.00, "sector_peak": 0.14, "ring_peak": 0.50,
               "edge_sector_peak": 0.00, "edge_angular_entropy": 0.00,
               "aspect": 1.00, "compact": 0.73, "cluster_frac": 1.00, "n_clusters": 1},
    "Donut": {"fail_rate": 0.34, "mean_r": 0.68, "edge_ratio": 0.00, "center_ratio": 0.00, "mid_ratio": 1.00,
              "radial_entropy": 0.50, "angular_entropy": 1.00, "sector_peak": 0.13, "ring_peak": 0.51,
              "edge_sector_peak": 0.22, "edge_angular_entropy": 0.96,
              "aspect": 1.00, "compact": 0.40, "cluster_frac": 1.00, "n_clusters": 1},
    "Edge-Loc": {"fail_rate": 0.12, "mean_r": 0.82, "edge_ratio": 0.75, "center_ratio": 0.01, "mid_ratio": 0.25,
                 "radial_entropy": 0.30, "angular_entropy": 0.35, "sector_peak": 0.55, "ring_peak": 0.70,
                 "edge_sector_peak": 0.70, "edge_angular_entropy": 0.35,
                 "aspect": 1.40, "compact": 0.20, "cluster_frac": 0.85, "n_clusters": 2},
    "Loc": {"fail_rate": 0.07, "mean_r": 0.50, "edge_ratio": 0.25, "center_ratio": 0.25, "mid_ratio": 0.25,
            "radial_entropy": 0.50, "angular_entropy": 0.50, "sector_peak": 0.45, "ring_peak": 0.45,
            "edge_sector_peak": 0.15, "edge_angular_entropy": 0.50,
            "aspect": 1.60, "compact": 0.55, "cluster_frac": 0.95, "n_clusters": 1},
    "Scratch": {"fail_rate": 0.05, "mean_r": 0.55, "edge_ratio": 0.25, "center_ratio": 0.20, "mid_ratio": 0.25,
                "radial_entropy": 0.60, "angular_entropy": 0.20, "sector_peak": 0.55, "ring_peak": 0.45,
                "edge_sector_peak": 0.25, "edge_angular_entropy": 0.20,
                "aspect": 7.00, "compact": 0.03, "cluster_frac": 0.95, "n_clusters": 1},
    "Random": {"fail_rate": 0.30, "mean_r": 0.55, "edge_ratio": 0.30, "center_ratio": 0.20, "mid_ratio": 0.30,
               "radial_entropy": 0.95, "angular_entropy": 0.98, "sector_peak": 0.14, "ring_peak": 0.50,
               "edge_sector_peak": 0.14, "edge_angular_entropy": 0.95,
               "aspect": 1.20, "compact": 0.12, "cluster_frac": 0.20, "n_clusters": 25},
    "Near-full": {"fail_rate": 0.98, "mean_r": 0.67, "edge_ratio": 0.28, "center_ratio": 0.12, "mid_ratio": 0.42,
                  "radial_entropy": 0.91, "angular_entropy": 1.00, "sector_peak": 0.13, "ring_peak": 0.24,
                  "edge_sector_peak": 0.25, "edge_angular_entropy": 0.94,
                  "aspect": 1.00, "compact": 0.77, "cluster_frac": 1.00, "n_clusters": 1},
    "none": {"fail_rate": 0.00, "mean_r": 0.50, "edge_ratio": 0.00, "center_ratio": 0.00, "mid_ratio": 0.00,
             "radial_entropy": 0.50, "angular_entropy": 0.50, "sector_peak": 0.00, "ring_peak": 0.00,
             "edge_sector_peak": 0.00, "edge_angular_entropy": 0.50,
             "aspect": 1.00, "compact": 0.00, "cluster_frac": 0.00, "n_clusters": 0},
}
WEIGHTS = {
    "Edge-Ring": {"edge_ratio": 1.6, "mean_r": 1.2, "angular_entropy": 1.3, "radial_entropy": 1.2, "edge_sector_peak": 0.8, "compact": 0.5, "cluster_frac": 0.5, "n_clusters": 0.5},
    "Center": {"center_ratio": 2.0, "mean_r": 1.0, "edge_ratio": 0.8, "mid_ratio": 0.8, "radial_entropy": 0.8, "compact": 1.2, "cluster_frac": 1.2, "n_clusters": 1.2, "fail_rate": 0.8},
    "Donut": {"mid_ratio": 1.8, "center_ratio": 0.8, "edge_ratio": 0.8, "mean_r": 1.1, "compact": 0.8, "cluster_frac": 0.8, "n_clusters": 0.8},
    "Edge-Loc": {"edge_sector_peak": 2.0, "edge_angular_entropy": 2.0, "angular_entropy": 1.2, "edge_ratio": 1.2, "sector_peak": 1.2},
    "Loc": {"mean_r": 0.3, "edge_ratio": 0.3, "center_ratio": 0.3, "mid_ratio": 0.3, "radial_entropy": 0.5, "angular_entropy": 0.5, "sector_peak": 0.7, "ring_peak": 0.5, "edge_sector_peak": 0.3, "edge_angular_entropy": 0.3, "compact": 1.5, "cluster_frac": 1.8, "n_clusters": 1.5, "fail_rate": 1.2},
    "Scratch": {"aspect": 2.0, "compact": 1.6, "angular_entropy": 1.5, "sector_peak": 1.2, "cluster_frac": 1.0, "mean_r": 0.5, "edge_ratio": 0.5, "center_ratio": 0.5, "mid_ratio": 0.5, "edge_angular_entropy": 1.2},
    "Random": {"radial_entropy": 1.5, "angular_entropy": 1.5, "n_clusters": 1.5, "cluster_frac": 1.5, "compact": 1.2, "fail_rate": 1.2},
    "Near-full": {"fail_rate": 2.5, "edge_ratio": 1.0, "center_ratio": 1.0, "mid_ratio": 1.0, "compact": 0.8, "cluster_frac": 0.8, "radial_entropy": 0.8, "n_clusters": 0.5},
    "none": {"fail_rate": 3.0, "compact": 0.5, "cluster_frac": 0.5, "n_clusters": 0.5, "radial_entropy": 0.3, "angular_entropy": 0.3},
}


def _value(feat, key):
    v = number(feat.get(key), 0.0)
    if key == "aspect":
        return min(8.0, max(0.0, v))
    if key == "n_clusters":
        return min(60.0, max(0.0, v))
    return min(1.0, max(0.0, v))


def _distance(feat, cls):
    proto = PROTO[cls]
    over = WEIGHTS.get(cls, {})
    num = 0.0
    den = 0.0
    for key in FEATURES:
        w = number(over.get(key), 1.0)
        if w <= 0:
            continue
        delta = (_value(feat, key) - proto[key]) / SCALE[key]
        num += w * delta * delta
        den += w
    return math.sqrt(num / den) if den else 0.0


def _drivers(feat, cls):
    proto = PROTO[cls]
    over = WEIGHTS.get(cls, {})
    out = []
    for key in FEATURES:
        w = number(over.get(key), 1.0)
        if w <= 0:
            continue
        out.append({
            "key": key,
            "observed": round(_value(feat, key), 4),
            "prototype": round(proto[key], 4),
            "weight": round(w, 2),
            "delta": round(abs(_value(feat, key) - proto[key]) / SCALE[key], 4),
        })
    out.sort(key=lambda r: r["delta"])
    return out[:4]


def _features_from_steps(steps, node_id):
    if not isinstance(steps, dict):
        return {}
    node = steps.get(node_id)
    if not isinstance(node, dict):
        return {}
    raw = node.get("raw") if isinstance(node.get("raw"), dict) else {}
    feat = raw.get("features")
    return feat if isinstance(feat, dict) else {}


def run(ctx, inputs, steps):
    node_id = str(inputs.get("map_node") or "n_map")
    feat = inputs.get("features")
    if not isinstance(feat, dict):
        feat = _features_from_steps(steps, node_id)
    if not feat:
        raise ValueError("缺少特征：请先运行 wafer_map，或通过 inputs.features 传入 raw.features")
    dists = {c: _distance(feat, c) for c in CLASSES}
    sims = {c: math.exp(-1.65 * dists[c]) for c in CLASSES}
    total = sum(sims.values()) or 1.0
    scores = {c: sims[c] / total for c in CLASSES}
    order = sorted(CLASSES, key=lambda c: -scores[c])
    top = order[0]
    second = order[1] if len(order) > 1 else top
    node = steps.get(node_id) if isinstance(steps, dict) else {}
    chart = node.get("chart") if isinstance(node, dict) and isinstance(node.get("chart"), dict) else {}
    raw = node.get("raw") if isinstance(node, dict) and isinstance(node.get("raw"), dict) else {}
    wafer_id = str(chart.get("wafer_id") or raw.get("wafer_id") or (ctx or {}).get("wafer") or "")
    return {
        "signature": top,
        "label": LABELS[top],
        "score": round(scores[top], 4),
        "runner_up": second,
        "margin": round(scores[top] - scores[second], 4),
        "distance": round(dists[top], 4),
        "fail_rate": round(number(feat.get("fail_rate"), 0.0), 4),
        "drivers": _drivers(feat, top),
        "features": feat,
        "wafer_id": wafer_id,
        "lot": str((ctx or {}).get("lot") or ""),
    }
