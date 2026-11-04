# -*- coding: utf-8 -*-
"""把 thesis/drafts/*.md 组装成符合本科毕业论文格式的 docx。

版式：A4、上下 2.54cm、左 3.0cm、右 2.5cm；正文宋体小四、1.5 倍行距、首行缩进 2 字符；
章标题黑体三号居中、节标题黑体四号、三级标题黑体小四；表格三线表、五号字；图居中、图题在下。
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path("F:/undergraduate")
DRAFTS = [ROOT / "thesis/drafts" / n for n in ("ch0-2.md", "ch3.md", "ch4.md", "ch5-6.md")]
OUT = ROOT / "thesis/面向垂直领域的RAG问答系统设计与检索策略优化-初稿.docx"

TITLE = "面向垂直领域的 RAG 问答系统设计与检索策略优化"
INFO = [
    ("学    院", "计算机与网络安全学院"),
    ("专    业", "智能科学与技术"),
    ("班    级", "2023 级 1 班"),
    ("学    号", "202319120316"),
    ("姓    名", "马武立夫"),
    ("指导教师", "曾维"),
]


# ---------------- 基础工具 ----------------
def set_font(run, name="宋体", size=12, bold=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    if color:
        run.font.color.rgb = RGBColor(*color)


def style_setup(doc: Document) -> None:
    st = doc.styles["Normal"]
    st.font.name = "宋体"
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    pf = st.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.first_line_indent = Pt(24)

    specs = {
        "Heading 1": (16, "黑体", WD_ALIGN_PARAGRAPH.CENTER, 18, 12),
        "Heading 2": (14, "黑体", WD_ALIGN_PARAGRAPH.LEFT, 12, 6),
        "Heading 3": (12, "黑体", WD_ALIGN_PARAGRAPH.LEFT, 6, 3),
    }
    for name, (size, font, align, before, after) in specs.items():
        s = doc.styles[name]
        s.font.name = font
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = RGBColor(0, 0, 0)
        s.element.rPr.rFonts.set(qn("w:eastAsia"), font)
        s.paragraph_format.alignment = align
        s.paragraph_format.space_before = Pt(before)
        s.paragraph_format.space_after = Pt(after)
        s.paragraph_format.first_line_indent = Pt(0)
        s.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        # 标题不自动编号
        s.element.get_or_add_pPr()


def add_page_field(par) -> None:
    run = par.add_run()
    fld1 = OxmlElement("w:fldChar"); fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar"); fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1); run._r.append(instr); run._r.append(fld2)
    set_font(run, "宋体", 10.5)


def set_cell_borders(cell, edges: dict[str, tuple[int, str]]) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge, (sz, val) in edges.items():
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), val)
        if val != "nil":
            el.set(qn("w:sz"), str(sz))
            el.set(qn("w:color"), "000000")
        borders.append(el)
    tcPr.append(borders)


def no_table_borders(table) -> None:
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)


def three_line_table(table, n_rows: int) -> None:
    """三线表：外框上下 1.5 磅、表头下 0.75 磅，其余无线。"""
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "12"); el.set(qn("w:color"), "000000")
        borders.append(el)
    for edge in ("left", "right", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    insideH = OxmlElement("w:insideH")
    insideH.set(qn("w:val"), "nil")
    borders.append(insideH)
    tblPr.append(borders)

    # 表头下横线
    for cell in table.rows[0].cells:
        set_cell_borders(cell, {"bottom": (6, "single")})


# ---------------- Markdown 解析 ----------------
def parse(md_text: str):
    """产出 (kind, payload) 序列：h1/h2/h3/p/table/image/caption/refs。"""
    lines = md_text.splitlines()
    i, out = 0, []
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("### "):
            out.append(("h3", line[4:].strip())); i += 1
        elif line.startswith("## "):
            out.append(("h2", line[3:].strip())); i += 1
        elif line.startswith("# "):
            out.append(("h1", line[2:].strip())); i += 1
        elif line.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            out.append(("image", (m.group(1), m.group(2)))); i += 1
        elif re.match(r"^表\d+-\d+", line.strip()):
            out.append(("table_caption", line.strip())); i += 1
        elif line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i].strip())
                i += 1
            rows = []
            for b in block:
                cells = [c.strip() for c in b.strip("|").split("|")]
                if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    continue
                rows.append(cells)
            out.append(("table", rows))
        else:
            out.append(("p", line.strip())); i += 1
    return out


# ---------------- 主体 ----------------
def cover(doc: Document) -> None:
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(60)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run("成都理工大学"), "黑体", 26, bold=True)

    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(6)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run("本科毕业论文（设计）"), "黑体", 22, bold=True)

    for _ in range(2):
        p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)

    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(24)
    set_font(p.add_run(TITLE), "黑体", 20, bold=True)

    t = doc.add_table(rows=len(INFO), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    no_table_borders(t)
    for r, (k, v) in enumerate(INFO):
        for c, text in enumerate((k, "：" + v)):
            cell = t.cell(r, c)
            cell.width = Cm(4.2 if c == 0 else 8.0)
            par = cell.paragraphs[0]
            par.paragraph_format.first_line_indent = Pt(0)
            par.paragraph_format.line_spacing = 1.5
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
            set_font(par.add_run(text), "宋体", 14)
        t.rows[r].height = Cm(1.0)

    for _ in range(2):
        p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run("2026 年 11 月"), "宋体", 14)


def add_toc(doc: Document) -> None:
    h = doc.add_paragraph(); h.paragraph_format.first_line_indent = Pt(0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(h.add_run("目  录"), "黑体", 16, bold=True)
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar"); fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve")
    instr.text = r'TOC \o "1-2" \h \z \u'
    fld_sep = OxmlElement("w:fldChar"); fld_sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t"); txt.text = "（在 Word 中按 F9 更新目录）"
    fld_end = OxmlElement("w:fldChar"); fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin); run._r.append(instr); run._r.append(fld_sep)
    run._r.append(txt); run._r.append(fld_end)
    set_font(run, "宋体", 12)


def add_heading(doc: Document, text: str, level: int) -> None:
    par = doc.add_heading(level=level)
    if level == 1 and text in ("摘要", "Abstract", "参考文献", "致谢"):
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(par.add_run(text), "黑体", {1: 16, 2: 14, 3: 12}[level], bold=True)


def add_para(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(24)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    text = text.replace("`", "")  # 行内代码标记直接去掉
    # 处理 **加粗** 行内标记
    for idx, seg in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not seg:
            continue
        run = p.add_run(seg)
        set_font(run, "宋体", 12, bold=(idx % 2 == 1))


def add_caption(doc: Document, text: str, above: bool = True) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(6 if above else 2)
    p.paragraph_format.space_after = Pt(2 if above else 6)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = above
    set_font(p.add_run(text), "宋体", 10.5, bold=False)


def add_table(doc: Document, rows: list[list[str]]) -> None:
    ncol = max(len(r) for r in rows)
    t = doc.add_table(rows=len(rows), cols=ncol)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    for r, row in enumerate(rows):
        for c in range(ncol):
            cell = t.cell(r, c)
            text = row[c] if c < len(row) else ""
            par = cell.paragraphs[0]
            par.paragraph_format.first_line_indent = Pt(0)
            par.paragraph_format.space_before = Pt(2)
            par.paragraph_format.space_after = Pt(2)
            par.paragraph_format.line_spacing = 1.0
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER if (r == 0 or c > 0) else WD_ALIGN_PARAGRAPH.LEFT
            for idx, seg in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
                if not seg:
                    continue
                run = par.add_run(seg)
                set_font(run, "宋体", 10.5, bold=(r == 0 or idx % 2 == 1))
    three_line_table(t, len(rows))
    # 表后留白
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run("")
    set_font(r, "宋体", 6)


def add_image(doc: Document, alt: str, path: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(14.5))
    add_caption(doc, alt, above=False)


def main() -> None:
    doc = Document()
    style_setup(doc)

    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2.54)
    sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.5)

    cover(doc)

    # 正文另起一节，页码从 1 开始
    new_sec = doc.add_section(WD_SECTION.NEW_PAGE)
    new_sec.top_margin = new_sec.bottom_margin = Cm(2.54)
    new_sec.left_margin, new_sec.right_margin = Cm(3.0), Cm(2.5)

    sectPr = new_sec._sectPr
    pgNum = OxmlElement("w:pgNumType")
    pgNum.set(qn("w:start"), "1")
    sectPr.append(pgNum)

    new_sec.footer.is_linked_to_previous = False
    fp = new_sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_field(fp)

    # 封面不显示页码
    doc.sections[0].footer.is_linked_to_previous = False

    items = []
    for f in DRAFTS:
        items.extend(parse(f.read_text(encoding="utf-8")))

    # 目录插在摘要之后
    toc_done = False
    tbl_no = {}
    for kind, payload in items:
        if kind == "h1":
            if payload == "第1章 绪论" and not toc_done:
                doc.add_page_break()
                add_toc(doc)
                toc_done = True
            add_heading(doc, payload, 1)
        elif kind == "h2":
            add_heading(doc, payload, 2)
        elif kind == "h3":
            add_heading(doc, payload, 3)
        elif kind == "p":
            add_para(doc, payload)
        elif kind == "table_caption":
            add_caption(doc, payload, above=True)
        elif kind == "table":
            add_table(doc, payload)
        elif kind == "image":
            alt, path = payload
            if Path(path).exists():
                add_image(doc, alt, path)
            else:
                add_para(doc, f"［缺图：{path}］")

    # 打开时自动更新域（目录）
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"[thesis] 已生成 {OUT}")


if __name__ == "__main__":
    main()
