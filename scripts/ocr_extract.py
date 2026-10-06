# -*- coding: utf-8 -*-
"""王道2027计算机网络PDF -> 分章Markdown（OCR全流程）"""
import re
import time
import pymupdf
from rapidocr_onnxruntime import RapidOCR

PDF = r"F:\下载\英语一阅读\2027计算机网络_高清带书签版.pdf"
OUT_DIR = r"F:\undergraduate\data\raw"

CHAPTERS = [
    (1, "计算机网络体系结构", 13, 41),
    (2, "物理层", 42, 61),
    (3, "数据链路层", 62, 138),
    (4, "网络层", 139, 235),
    (5, "传输层", 236, 278),
    (6, "应用层", 279, 316),
]

WATERMARKS = {"机教育", "王道计", "算机教育", "王道计算机教育", "扫一扫",
              "视频讲解", "永久微信93637888", "王道考研"}

ocr = RapidOCR()
doc = pymupdf.open(PDF)
toc = doc.get_toc()

# 页码 -> 该页开始的编号小节标题（1.1 / 4.2.1 这种）
headmap = {}
for lvl, title, page in toc:
    t = re.sub(r"\s+", " ", title).strip()
    if re.match(r"^\d+(\.\d+)+", t):
        headmap.setdefault(page, []).append((lvl, t))

t_start = time.time()
total_pages = sum(pe - ps + 1 for _, _, ps, pe in CHAPTERS)
done = 0

for num, title, ps, pe in CHAPTERS:
    out = [f"# 第{num}章 {title}", ""]
    for p in range(ps - 1, pe):  # 0基页码
        for _lvl, t in headmap.get(p + 1, []):
            out.append("## " + t)
        pix = doc[p].get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5))
        result, _ = ocr(pix.tobytes("png"))
        lines = [r[1].strip() for r in result] if result else []
        for i, l in enumerate(lines):
            if l in WATERMARKS or "关注公众号" in l or "训练营" in l:
                continue
            if i < 3 and re.fullmatch(r"\d{1,3}", l):
                continue
            if i < 3 and re.fullmatch(r"第\d+章.{0,14}", l):
                continue
            out.append(l)
        out.append("")
        done += 1
        if done % 10 == 0:
            el = time.time() - t_start
            eta = el / done * (total_pages - done)
            print(f"[{done}/{total_pages}] {el/60:.1f}min 已用, 预计还剩 {eta/60:.1f}min", flush=True)
    fname = f"{OUT_DIR}\\0{num}-{title}.md"
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    with open(fname, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"已写出: {fname} ({len(text)}字符)", flush=True)

print(f"全部完成，总耗时 {(time.time()-t_start)/60:.1f} 分钟", flush=True)
