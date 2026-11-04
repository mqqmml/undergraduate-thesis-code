# -*- coding: utf-8 -*-
"""读取人工复核表，计算人工判定与自动判定的一致性（Cohen's kappa）。

产物：results/audit_kappa.md

判定规则：
- 维度① 回答是否正确：人工「是」=1；自动以 KPC ≥ 0.5 记为「是」（与 metrics 的 kpc_threshold 一致）
- 维度② 有无编造：人工「无」=1（无编造）；自动以 Faithfulness ≥ 0.8 记为「无编造」
- 维度③ 引用是否指向依据：人工「是」=1；自动以 CitationRate > 0 记为「有引用」
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from src.config import PROJECT_ROOT

SHEET = PROJECT_ROOT / "data/eval/human_audit_sheet.xlsx"
OUT = PROJECT_ROOT / "results/audit_kappa.md"
KPC_TH = 0.5
FAITH_TH = 0.8


def kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1 = sum(a) / n
    pb1 = sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


def interpret(k: float) -> str:
    if k >= 0.8:
        return "几乎完全一致"
    if k >= 0.6:
        return "高度一致"
    if k >= 0.4:
        return "中等一致"
    if k >= 0.2:
        return "一般一致"
    return "一致性差"


def main() -> None:
    wb = load_workbook(SHEET, data_only=True)
    ws = wb["人工复核"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    rows = [r for r in rows if r and r[0] is not None]
    total = len(rows)

    recs = []
    for r in rows:
        hc = str(r[7]).strip() if r[7] is not None else ""
        hf = str(r[8]).strip() if r[8] is not None else ""
        hci = str(r[9]).strip() if r[9] is not None else ""
        recs.append(
            {
                "seq": r[0], "type": r[1], "q": r[2],
                "kpc": float(r[5] or 0), "faith": float(r[6] or 0),
                "h_correct": 1 if hc == "是" else 0,
                "h_faith": 1 if hf == "无" else 0,
                "h_cite": 1 if hci == "是" else 0,
                "filled_correct": hc in ("是", "否"),
                "filled_faith": hf in ("无", "有"),
                "note": r[10] if len(r) > 10 else "",
            }
        )

    # 未填的行不参与计算（预填空值曾被误当成「全部达标」）
    sub1 = [r for r in recs if r["filled_correct"]]
    sub2 = [r for r in recs if r["filled_faith"]]
    n1, n2 = len(sub1), len(sub2)

    if n1 == 0 or n2 == 0:
        lines = [
            "# 人工抽样复核报告（待填写）",
            "",
            f"复核表：`data/eval/human_audit_sheet.xlsx`，共 {total} 题，"
            f"已填 ① {n1} 题 / ② {n2} 题。",
            "",
            "> 状态：**尚未人工判读**，因此不给出 kappa。填写第 8~10 列（是/否）后重跑本脚本即可生成结果。",
            "",
            "## 自动判定侧的参考分布（仅用于判断阈值是否过严，不构成一致性结论）",
            "",
            "| 维度 | 自动判定口径 | 自动判为「达标」 | 占比 |",
            "|---|---|---|---|",
            f"| ① 回答是否正确 | KPC ≥ {KPC_TH} | {sum(1 for r in recs if r['kpc'] >= KPC_TH)}/{total} | "
            f"{sum(1 for r in recs if r['kpc'] >= KPC_TH) / total:.3f} |",
            f"| ② 有无编造 | Faithfulness ≥ {FAITH_TH} | {sum(1 for r in recs if r['faith'] >= FAITH_TH)}/{total} | "
            f"{sum(1 for r in recs if r['faith'] >= FAITH_TH) / total:.3f} |",
            "",
        ]
        OUT.write_text("\n".join(lines), encoding="utf-8")
        print(f"[kappa] 复核表尚未填写（① {n1}/{total}、② {n2}/{total}），已写入待填状态到 {OUT}")
        return

    auto_correct = [1 if r["kpc"] >= KPC_TH else 0 for r in sub1]
    auto_faith = [1 if r["faith"] >= FAITH_TH else 0 for r in sub2]
    h_correct = [r["h_correct"] for r in sub1]
    h_faith = [r["h_faith"] for r in sub2]

    k1 = kappa(h_correct, auto_correct)
    k2 = kappa(h_faith, auto_faith)
    agree1 = sum(1 for a, b in zip(h_correct, auto_correct) if a == b) / n1
    agree2 = sum(1 for a, b in zip(h_faith, auto_faith) if a == b) / n2

    lines = [
        "# 人工抽样复核报告",
        "",
        f"样本：{total} 题（分层抽样，来自 BM25-1024 + rerank, top_k=5 最终管线）；"
        f"实际参与计算：① {n1} 题、② {n2} 题（未填行已跳过）",
        "",
        "## 一致性结果",
        "",
        "| 维度 | 自动判定口径 | 人工判为「达标」 | 自动判为「达标」 | 一致率 | Cohen's kappa | 强度 |",
        "|---|---|---|---|---|---|---|",
        f"| ① 回答是否正确 | KPC ≥ {KPC_TH} | {sum(h_correct)}/{n1} | {sum(auto_correct)}/{n1} | {agree1:.3f} | {k1:.3f} | {interpret(k1)} |",
        f"| ② 有无编造 | Faithfulness ≥ {FAITH_TH} | {sum(h_faith)}/{n2} | {sum(auto_faith)}/{n2} | {agree2:.3f} | {k2:.3f} | {interpret(k2)} |",
        "",
        "## 逐题明细",
        "",
        "| # | 题型 | 问题 | KPC | Faith | 人工:正确 | 自动:正确 | 人工:无编造 | 自动:无编造 | 备注 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in recs:
        q = str(r["q"])[:28].replace("|", "\\|")
        a1 = int(r["kpc"] >= KPC_TH)
        a2 = int(r["faith"] >= FAITH_TH)
        hc = r["h_correct"] if r["filled_correct"] else "—"
        hf = r["h_faith"] if r["filled_faith"] else "—"
        lines.append(
            f"| {r['seq']} | {r['type']} | {q} | {r['kpc']:.2f} | {r['faith']:.2f} | "
            f"{hc} | {a1} | {hf} | {a2} | {str(r['note'] or '')[:20]} |"
        )

    lines += [
        "",
        "## 结论写法建议",
        "",
        "- kappa ≥ 0.6 时：可写「自动指标与人工判定高度一致，指标可用于方法间比较」。",
        "- 0.4 ≤ kappa < 0.6 时：写明「自动指标可用于相对比较，绝对水平存在系统性偏移」。",
        "- kappa < 0.4 时：需在局限性中说明，并仅用人工子集做结论。",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[kappa] ① 正确性 kappa={k1:.3f} 一致率={agree1:.3f}")
    print(f"[kappa] ② 无编造 kappa={k2:.3f} 一致率={agree2:.3f}")
    print(f"[kappa] 报告已写入 {OUT}")


if __name__ == "__main__":
    main()
