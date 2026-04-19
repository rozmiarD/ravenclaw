from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from vuln_qualification import qualify  # type: ignore


def run_benchmark(cases_path: str, out_path: str) -> Dict[str, Any]:
    p = Path(cases_path)
    cases = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    total = 0
    tp = fp = fn = tn = 0
    rows = []

    for c in cases:
        if not isinstance(c, dict):
            continue
        total += 1
        expected = str(c.get("expected") or "none")
        q = qualify(c.get("evidence") or {}).as_dict()
        pred = str(q.get("verdict") or "none")

        positive_exp = expected in {"probable", "confirmed"}
        positive_pred = pred in {"probable", "confirmed"}

        if positive_exp and positive_pred:
            tp += 1
        elif (not positive_exp) and positive_pred:
            fp += 1
        elif positive_exp and (not positive_pred):
            fn += 1
        else:
            tn += 1

        rows.append({"id": c.get("id"), "expected": expected, "predicted": pred, "qualification": q})

    precision = tp / max(1, (tp + fp))
    recall = tp / max(1, (tp + fn))
    fpr = fp / max(1, (fp + tn))
    out = {
        "total": total,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "rows": rows,
    }
    Path(out_path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    cases = root / "reports" / "qualification" / "benchmark_cases.json"
    out = root / "reports" / "qualification" / "benchmark_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    res = run_benchmark(str(cases), str(out))
    print(json.dumps(res, ensure_ascii=False, indent=2))
