# -*- coding: utf-8 -*-
"""生成人工抽样复核表（xlsx）：20 题分层抽样，只需在 3 列里选「是/否」。

设计原则：
- 一屏一题，标准答案与模型回答并排，不要求核对检索细节；
- 自动判定值只作参考，人工三列**留空**，必须自己判读（预填会让空白表变成「全通过」，kappa 失去意义）；
- 下拉框限定「是/否」，避免格式不一致导致 kappa 无法计算。

产物：data/eval/human_audit_sheet.xlsx
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from src.config import PROJECT_ROOT

SRC_CSV = PROJECT_ROOT / "results/e3-bm25-1024-rerank-k5/per_question.csv"
OUT = PROJECT_ROOT / "data/eval/human_audit_sheet.xlsx"
N_PER_TYPE = {"事实型": 7, "对比型": 5, "过程型": 5, "多跳型": 2, "计算型": 1}


def load_rows() -> list[dict]:
    with open(SRC_CSV, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sample(rows: list[dict]) -> list[dict]:
    """按题型分层，取每题 KPC 中位附近的样本（避免全挑最好/最差的极端样本）。"""
    picked: list[dict] = []
    for qtype, k in N_PER_TYPE.items():
        sub = [r for r in rows if r.get("type") == qtype]
        sub.sort(key=lambda r: abs(float(r.get("keypoint_coverage") or 0) - 0.72))
        picked.extend(sub[:k])
    return picked


def main() -> None:
    rows = sample(load_rows())

    wb = Workbook()
    ws = wb.active
    ws.title = "人工复核"
    headers = [
        "序号", "题型", "问题", "标准答案", "模型回答（含引用标记）",
        "自动判定 KPC", "自动判定 Faithfulness",
        "① 回答是否正确（是/否）", "② 有无编造内容（无/有）", "③ 引用是否指向依据（是/否）",
        "备注（可选）",
    ]
    widths = [6, 9, 34, 40, 52, 12, 14, 16, 16, 18, 20]
    for i, (h, w) in enumerate(zip(headers, widths), start=1):
        c = ws.cell(row=1, column=i, value=h)
        c.font = Font(bold=True, size=10)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.fill = PatternFill("solid", fgColor="EDEDED")
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[1].height = 36
    ws.freeze_panes = "A2"

    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for r, item in enumerate(rows, start=2):
        answer = (item.get("answer") or "").strip()
        vals = [
            r - 1,
            item.get("type", ""),
            item.get("question", ""),
            item.get("gold_answer", ""),
            answer[:900],
            round(float(item.get("keypoint_coverage") or 0), 2),
            round(float(item.get("faithfulness") or 0), 2),
            "",
            "",
            "",
            "",
        ]
        for i, v in enumerate(vals, start=1):
            c = ws.cell(row=r, column=i, value=v)
            c.alignment = Alignment(vertical="top", wrap_text=True)
            c.font = Font(size=9)
            c.border = border
            if i in (8, 9, 10):
                c.fill = PatternFill("solid", fgColor="FFF3CC")
        ws.row_dimensions[r].height = 96

    dv1 = DataValidation(type="list", formula1='"是,否"', allow_blank=True)
    dv2 = DataValidation(type="list", formula1='"无,有"', allow_blank=True)
    ws.add_data_validation(dv1)
    ws.add_data_validation(dv2)
    last = len(rows) + 1
    for col, dv in (("H", dv1), ("I", dv2), ("J", dv1)):
        dv.add(f"{col}2:{col}{last}")

    # 填写说明页
    ws2 = wb.create_sheet("填写说明")
    guide = [
        "人工抽样复核表 —— 填写说明",
        "",
        "1. 共 20 题，按题型分层抽样（"
        + " / ".join(f"{t} {n}" for t, n in N_PER_TYPE.items())
        + "）。",
        "2. 只填 3 个黄色列（目前留空，必须逐题判读，不能默认全通过）：",
        "   ① 回答是否正确：模型回答是否覆盖标准答案的核心要点（术语不同但意思对 = 是）。",
        "   ② 有无编造内容：回答里是否出现知识库没有、标准答案也没有的内容（有 = 编造）。",
        "   ③ 引用是否指向依据：回答中的 [片段n] 是否真的支撑前一句结论。",
        "3. 「自动判定 KPC / Faithfulness」两列仅供对照，不要照着它填。",
        "4. 备注列可留空；遇到拿不准的题，写一句「拿不准」即可，不算错。",
        "5. 填完保存，运行：PYTHONPATH=. python scripts/kappa_audit.py",
        "   自动计算人工判定与自动判定的一致性（Cohen's kappa）并生成报告；",
        "   未填的行会被跳过，报告头部会注明实际参与计算的题数。",
        "",
        "预计耗时：20~25 分钟。",
    ]
    for i, line in enumerate(guide, start=1):
        c = ws2.cell(row=i, column=1, value=line)
        c.font = Font(bold=(i == 1), size=11)
    ws2.column_dimensions["A"].width = 96

    wb.save(OUT)
    print(f"[audit] 已生成 {OUT}（{len(rows)} 题）")
    print("[audit] 题型分布:", {t: sum(1 for r in rows if r['type'] == t) for t in N_PER_TYPE})


if __name__ == "__main__":
    main()
