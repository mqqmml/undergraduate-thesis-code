# -*- coding: utf-8 -*-
r"""从新题源构建 eval-v2.0 并全自动质检（取代人工填表审核）。

题源（F:\下载\hyperdown-client-windows-amd64\Downloads\计算机网络\ 及同层）：
    - 计算机网络技术题库(密码yscl).pdf              扫描版 OCR，约 1391 个题号（主力）
    - 计算机网络试题库含答案(个人整理打印版).pdf     300+ 道带答案选择题
    - 计算机网络期末试题及答案.pdf                   内嵌答案（填空/选择）+ 文末答案区
    - 计算机网络试题及答案.pdf                      02141 试题 + 文末参考答案
    - 计算机网络笔试题.pdf                          问答对（问 + 答：，含杂题需过滤）
    - 计算机网络基础知识要点.pdf                    知识总结（不作题源）

自动质检（auto-audit，替代 human_audit_sample_30.csv）：
    A1 去重：题干归一化精确去重 + token Jaccard>0.7 近重复
    A2 gold 映射：题干+答案映射 chunk，idf 加权分须达阈值，否则丢弃
    A3 答案支撑：gold chunk 与标准答案的 token 重叠须达标（MCQ 0.15 / QA 0.3）
    A4 过滤：知识库外老技术（windows95/netware/拨号）、缺图题、非网络题丢弃

输出：
    data/eval/questions_v2.0.jsonl
    data/eval/eval_v2.0_manifest.json
    data/eval/audit_report_v2.0.md
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

import jieba

ROOT = Path(__file__).resolve().parent.parent
EXAM_WORK = Path(r"C:\Users\mawulifu\WorkBuddy\2026-10-02-17-52-15\exam_work")

_STOPWORDS = {
    "的", "是", "在", "和", "或", "与", "为", "有", "被", "将", "了", "不", "要",
    "可以", "因此", "所以", "因为", "对于", "如果", "则", "那么", "例如", "本题",
    "选择", "解析", "答案", "选项", "正确", "错误", "其中", "一个", "一种",
    "这个", "这种", "该", "其", "它", "他", "她", "我们", "需要", "进行", "通过",
    "使用", "采用", "根据", "由于", "而且", "并且", "但是", "然而", "首先", "然后",
    "最后", "第一", "第二", "第三", "即", "等", "者", "时", "中",
    "上", "下", "前", "后", "内", "外", "间", "之", "而", "以", "及", "但", "并",
    "因", "所", "从", "向", "到", "对", "把", "让", "给", "比", "很", "最",
    "以下", "下列", "属于", "指", "请问", "上述", "有关", "不是", "称为", "什么",
}

_PUNCT = re.compile(r"[\s，。、；：？！,.;:?!”\"'()（）\[\]【】《》\-—_/\\|*#`~+=<>_]+")


def normalize(text: str) -> str:
    return _PUNCT.sub("", (text or "").lower())


def tokens(text: str) -> List[str]:
    return [t for t in jieba.lcut_for_search(normalize(text)) if t and t.strip()]


def load_chunks(path: Path) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            item["_tokens"] = set(tokens(item["text"]))
            chunks.append(item)
    return chunks


def compute_idf(chunks: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    df: Counter[str] = Counter()
    for c in chunks:
        df.update(c["_tokens"])
    N = len(chunks)
    return {t: math.log((N + 1) / (df[t] + 1) + 1) for t in df}


# ------------------------------------------------------------------
# 通用清洗
# ------------------------------------------------------------------

_PAGE_RE = re.compile(r"^\s*(=+ P\d+ =+|\d+)\s*$")
_NOISE_LINE = re.compile(r"^(云上成理|上成理|8元|公众号.*|官方QQ群.*|难度：.*|类型：.*|知识点：.*|备注：.*)$")
# 内嵌选择题答案：__B__ / （ B） / (B)
_MC_MARK = re.compile(r"[（(]\s*[A-D]\s*[）)]|[_＿]{1,4}\s*[A-D]\s*[_＿]{1,4}")
# 内嵌填空答案：下划线紧邻的 1-8 字短内容（纯标点除外；不吃掉两侧下划线）
_SHORT_ANS = re.compile(r"(?<=[_＿])(?![、，,。；;：:·])[^_＿\s](?:[^_＿]{0,7}?)(?=[_＿＿])")
# 连续下划线（>=2）折叠为 ____
_BLANK_RE = re.compile(r"[_＿]{2,}")
# 残留题号
_LEADNUM_RE = re.compile(r"^\s*\d+(?:\.\d+)?\s*[\.．、]?\s*")
# 试卷大节标题（题面截断用）
_SEC_MARK = re.compile(r"第[一二三四五六七八]部分|[一二三四五六七八]、(填空题|选择题|名词解释|简答题|简答|计算题|应用题|综合题)")
# 网络相关性关键词
_NET_KW = re.compile(
    r"网络|协议|IP|TCP|UDP|以太网|路由|交换|DNS|HTTP|FTP|DHCP|ARP|ICMP|OSI|"
    r"MAC|端口|分组|报文|帧|比特|信道|带宽|局域网|广域网|子网|掩码|拓扑|"
    r"传输|数据链路|物理层|应用层|防火墙|加密|CSMA|令牌|复用|载波"
)


def clean_lines(text: str) -> List[str]:
    out = []
    for ln in text.splitlines():
        ln = re.sub(r"云上成理", "", ln).strip()
        if not ln or _PAGE_RE.match(ln):
            continue
        if "QlO" in ln or _NOISE_LINE.match(ln):
            continue
        out.append(ln)
    return out


def strip_inline_answers(text: str) -> str:
    """去掉题面中内嵌的答案，只留空位。顺序：字母标记 -> 短答案 -> 下划线折叠。"""
    t = _MC_MARK.sub("（ ）", text)
    t = re.sub(r"[_＿][ \t]+", "_", t)  # "_ 答案" -> "_答案"
    t = _SHORT_ANS.sub("____", t)
    t = _BLANK_RE.sub("____", t)
    return t


def strip_lead_num(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = _LEADNUM_RE.sub("", text, count=1)
    return text.strip()


# ------------------------------------------------------------------
# 解析器 A：内嵌答案选择题（题库打印版 / 技术题库yscl）
# ------------------------------------------------------------------

_ANS_INLINE = re.compile(r"[（(]\s*([A-D])\s*[）)]")
_OPT_START = re.compile(r"(?:^|\s)A\s*[\.．、,，]")
_OPT_SPLIT = re.compile(r"(?:^|\s)([A-D])\s*[\.．、,，]")


def parse_mc_inline(text: str, source: str, two_level: bool = False) -> List[Dict[str, Any]]:
    lines = clean_lines(text)
    qnum_re = re.compile(r"^\s*(\d+\.\d+)\s" if two_level else r"^\s*(\d+)\s*[\.．、]\s*\S")
    blocks, cur = [], []
    for ln in lines:
        if qnum_re.match(ln):
            if cur:
                blocks.append(cur)
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        blocks.append(cur)

    entries = []
    for blk in blocks:
        joined = re.sub(r"\s+", " ", " ".join(blk))
        om = _OPT_START.search(joined)
        if not om:
            continue
        stem, opt_part = joined[: om.start()], joined[om.start():]
        am = list(_ANS_INLINE.finditer(stem))
        if not am:
            continue
        ans = am[-1].group(1)
        stem = strip_inline_answers(stem)
        stem = strip_lead_num(stem)

        parts = _OPT_SPLIT.split(opt_part)
        options: Dict[str, str] = {}
        if len(parts) >= 3:
            for i in range(1, len(parts) - 1, 2):
                letter = parts[i]
                if letter not in options:
                    options[letter] = parts[i + 1].strip(" ；;，,。")
        if len(options) < 3 or ans not in options or len(stem) < 8:
            continue
        opt_str = " ".join(f"{k}. {options[k]}" for k in sorted(options))
        entries.append({
            "question": f"{stem} {opt_str}",
            "options": options,
            "answer_letter": ans,
            "answer_text": options[ans],
            "source": source,
        })
    return entries


# ------------------------------------------------------------------
# 解析器 B：文末答案区试卷（02141 / 期末）
# ------------------------------------------------------------------

_LETTER_KEY = re.compile(r"(\d+)\s*[.．]\s*([A-D])(?![A-Za-z0-9])")
# 答案区里的题号边界（数字+分隔符；其后不能紧跟 IP 样式数字串）
_ANS_BOUND = re.compile(r"(?<![\d.])(\d{1,2})\s*[、．.]\s*")
_IP_LIKE = re.compile(r"^\s*\d+[.,]\d+[.,]\d+")


def expand_answer_section(a_part: str) -> Dict[int, str]:
    answers: Dict[int, str] = {}
    for ln in a_part.splitlines():
        # 1) "14-28：B Ａ Ｂ B D" 行式密钥
        m = re.match(r"\s*(\d+)\s*[-–—]\s*(\d+)\s*[：:]\s*(.+)$", ln)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            letters = re.findall(r"[A-DＡ-Ｄ]", m.group(3))
            if hi > lo and hi - lo + 1 == len(letters):
                for i, L in enumerate(letters):
                    answers[lo + i] = L
                continue
        # 2) "1.A 2.B 3.D" 行式密钥
        for pm in _LETTER_KEY.finditer(ln):
            answers[int(pm.group(1))] = pm.group(2)
        if _LETTER_KEY.search(ln):
            # 该行还可能同时挂着文本答案（少见），继续走 3）
            pass
        # 3) 顺序题号 + 文本答案（可能一行多题）
        pieces = _ANS_BOUND.split(ln)
        # pieces: [前导, num, text, num, text, ...]
        if len(pieces) >= 3:
            for i in range(1, len(pieces) - 1, 2):
                num = int(pieces[i])
                rest = pieces[i + 1]
                # 排除 IP/数字串误切（如 "7.128.0.0.0"）
                if _IP_LIKE.match(rest):
                    continue
                if num in answers and re.fullmatch(r"[A-D]", answers[num]):
                    continue  # 已有字母密钥，跳过
                body = rest.strip(" 。；;，,")
                if body and num not in answers:
                    answers[num] = body
        else:
            m2 = re.match(r"\s*(\d{1,2})\s*[、．.]\s*(.+)$", ln)
            if m2 and not _IP_LIKE.match(m2.group(2)):
                num = int(m2.group(1))
                if num not in answers:
                    answers[num] = m2.group(2).strip(" 。；;，,")
    # 4) 跨行编号答案块（正文里换行的情况）
    ablocks = re.split(r"\n(?=\d+\s*[、．.])", a_part)
    for ab in ablocks:
        m = re.match(r"(\d+)\s*[、．.]\s*(.*)", ab, re.DOTALL)
        if not m:
            continue
        num = int(m.group(1))
        body = re.sub(r"\s+", " ", m.group(0)).strip()
        body = re.sub(r"^\d+\s*[、．.]\s*", "", body).strip(" 。；;，,")
        if num not in answers and len(body) >= 2 and not _IP_LIKE.match(body):
            answers[num] = body
    return answers


def parse_paper_with_key(text: str, source: str, key_marker: str) -> List[Dict[str, Any]]:
    text_j = "\n".join(clean_lines(text))
    idx = text_j.find(key_marker)
    if idx == -1:
        return []
    q_part, a_part = text_j[:idx], text_j[idx:]
    answers = expand_answer_section(a_part)

    qblocks = re.split(r"\n(?=\d+\s*[、．.])", q_part)
    entries = []
    for qb in qblocks:
        m = re.match(r"(\d+)\s*[、．.]\s*(.*)", qb, re.DOTALL)
        if not m:
            continue
        num = int(m.group(1))
        ans = answers.get(num, "")
        if not ans:
            continue
        qtext = re.sub(r"\s+", " ", qb).strip()
        qtext = re.sub(r"^\d+\s*[、．.]\s*", "", qtext)
        qtext = strip_inline_answers(qtext)
        om = _OPT_START.search(qtext)
        options: Dict[str, str] = {}
        opt_text = ""
        if om:
            opt_text = qtext[om.start():]
            qtext = qtext[: om.start()]
            parts = _OPT_SPLIT.split(opt_text)
            if len(parts) >= 3:
                for i in range(1, len(parts) - 1, 2):
                    letter = parts[i]
                    if letter not in options:
                        options[letter] = parts[i + 1].strip(" ；;，,。")
        if len(qtext) < 8:
            continue
        if re.fullmatch(r"[A-D]", ans.strip()):
            letter = ans.strip()
            qfull = qtext + (" " + opt_text if opt_text else "")
            qfull = _SEC_MARK.split(qfull)[0].strip()  # 截掉混入的大节标题
            entries.append({
                "question": qfull,
                "options": options,
                "answer_letter": letter,
                "answer_text": options.get(letter, ""),
                "source": source,
            })
        elif len(ans) >= 4:
            qtext = _SEC_MARK.split(qtext)[0].strip()
            entries.append({
                "question": qtext.strip(),
                "options": {},
                "answer_letter": "",
                "answer_text": ans,
                "source": source,
            })
    return entries


# ------------------------------------------------------------------
# 解析器 C：笔试题（N．问 \n 答：...）
# ------------------------------------------------------------------

def parse_bishi(text: str) -> List[Dict[str, Any]]:
    text_j = "\n".join(clean_lines(text))
    blocks = re.split(r"\n(?=\d+\s*[．.、])", text_j)
    entries = []
    for blk in blocks:
        m = re.match(r"(\d+)\s*[．.、]\s*(.*)", blk, re.DOTALL)
        if not m:
            continue
        body = m.group(2)
        am = re.search(r"答[：:]", body)
        if not am:
            continue
        q = re.sub(r"\s+", " ", body[: am.start()]).strip()
        a = re.sub(r"\s+", " ", body[am.end():]).strip()
        if len(q) < 8 or len(a) < 10:
            continue
        if not _NET_KW.search(q + a):
            continue
        entries.append({
            "question": q,
            "options": {},
            "answer_letter": "",
            "answer_text": a,
            "source": "笔试题",
        })
    return entries


# ------------------------------------------------------------------
# 题型分类 / key_points
# ------------------------------------------------------------------

def classify_type(question: str, answer: str) -> str:
    qe = question + " " + answer
    if re.search(r"计算|速率|多少个|多少位|时延|带宽.*要求|子网掩码应|划分几个|至少要.*种|效率为|码元|主机范围|划分子网|IP 地址空间|数据传输率", qe):
        return "计算型"
    if re.search(r"区别|不同|相似之处|相比|比较|对比|与.*相比|相同点|不同点", qe):
        return "对比型"
    if re.search(r"过程|步骤|流程|如何工作|简述|工作原理|三次握手|四次挥手|建立连接|传输过程|的作用|功能是|主要功能", qe):
        return "过程型"
    if re.search(r"分别|各.*对应|哪些.*属于|按照.*排序|发展顺序|依次|哪一组", qe):
        return "多跳型"
    return "事实型"


def extract_key_points(question: str, answer: str) -> List[str]:
    text = answer or question
    first_sent = re.split(r"[。；!！]", text)[0]
    terms = re.findall(r"[A-Za-z][A-Za-z/\-]{1,15}|[\u4e00-\u9fa5]{2,12}", first_sent)
    out, seen = [], set()
    for t in terms:
        t = t.strip()
        if not t or t in _STOPWORDS or re.fullmatch(r"[A-D]", t):
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= 5:
            break
    return out


# ------------------------------------------------------------------
# 自动质检
# ------------------------------------------------------------------

_ERA_BAD = re.compile(
    r"[Ww]indows\s*95|[Ww]indows\s*98|Windows\s*2000|Windows\s*NT|[Ww]indows\s*2000[Ss]erver|"
    r"NetWare|Netware|NOVELL|Novell|"
    r"拨号|ATDP|ATDT|[Mm]odem|MODEM|X\.25 的分组级|windows95|windows98|"
    r"IPX|ipx|Netscape|NetScape|RS-232C|RS—232C|"
    r"活动目录|网上邻居|SQL|游标|域名服务器上的区域|Linux 环境中"
)
_FIG_BAD = re.compile(r"下图|如图|图所示|图 \d|波形|如图所示|拓扑结构如下图|表 \d 是")


def pass_filters(e: Dict[str, Any]) -> bool:
    text = e["question"] + " " + e.get("answer_text", "")
    if _ERA_BAD.search(text):
        return False
    if _FIG_BAD.search(e["question"]):
        return False
    return True


def gold_map(query: str, chunks, idf, top_n: int = 2):
    qtokens = set(tokens(query))
    if not qtokens:
        return [], 0.0
    scored = []
    for c in chunks:
        s = sum(idf.get(t, 0.0) for t in qtokens if t in c["_tokens"])
        scored.append((s, c["chunk_id"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    selected, best = [], scored[0][0] if scored else 0.0
    for i, (s, cid) in enumerate(scored[:top_n]):
        if s <= 0:
            break
        if i > 0 and s < scored[i - 1][0] * 0.3:
            break
        selected.append(cid)
    return selected, best


def answer_support(answer_text: str, chunk_texts: List[str]) -> float:
    atoks = [t for t in tokens(answer_text) if t not in _STOPWORDS]
    if not atoks:
        return 1.0
    ctoks = set(tokens(" ".join(chunk_texts)))
    hit = sum(1 for t in atoks if t in ctoks)
    return hit / len(atoks)


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ------------------------------------------------------------------
# 主流程
# ------------------------------------------------------------------

def main() -> None:
    chunks = load_chunks(ROOT / "data" / "processed" / "chunks.jsonl")
    idf = compute_idf(chunks)
    chunk_by_id = {c["chunk_id"]: c["text"] for c in chunks}
    print(f"[build] 载入 {len(chunks)} 个 chunk")

    raw: List[Dict[str, Any]] = []
    src_specs = [
        ("题库打印版.txt", lambda t: parse_mc_inline(t, "题库打印版", two_level=True)),
        ("技术题库yscl_ocr.txt", lambda t: parse_mc_inline(t, "技术题库yscl", two_level=False)),
        ("期末试题及答案.txt", lambda t: parse_paper_with_key(t, "期末试题及答案", "答案：")),
        ("试题及答案.txt", lambda t: parse_paper_with_key(t, "02141试题", "参考答案")),
        ("笔试题.txt", lambda t: parse_bishi(t)),
    ]
    src_stats = {}
    for fn, parser in src_specs:
        p = EXAM_WORK / fn
        if not p.exists():
            print(f"[build] 跳过缺失题源：{fn}")
            continue
        entries = parser(p.read_text(encoding="utf-8"))
        src_stats[fn] = len(entries)
        raw.extend(entries)
        print(f"[build] {fn}: 解析 {len(entries)} 题")
    print(f"[build] 候选合计 {len(raw)}")

    # A1 去重（此时 MCQ 题面已含选项，跨源同题可被识别）
    seen_norm: set[str] = set()
    seen_toks: List[set[str]] = []
    deduped, dropped_dup = [], 0
    for e in raw:
        n = normalize(e["question"])
        if not n or n in seen_norm:
            dropped_dup += 1
            continue
        qt = set(tokens(e["question"]))
        if any(jaccard(qt, st) > 0.7 for st in seen_toks if st):
            dropped_dup += 1
            continue
        seen_norm.add(n)
        seen_toks.append(qt)
        deduped.append(e)
    print(f"[audit A1] 去重丢弃 {dropped_dup}，剩 {len(deduped)}")

    # A4 过滤
    kept = [e for e in deduped if pass_filters(e)]
    print(f"[audit A4] 时代/缺图过滤丢弃 {len(deduped) - len(kept)}，剩 {len(kept)}")

    # A2+A3 gold 映射与答案支撑
    final = []
    drop_no_gold, drop_support = 0, 0
    for e in kept:
        q = e["question"]
        ans_letter = e.get("answer_letter", "")
        opt = e.get("options", {})
        ans_full = (opt.get(ans_letter, "") + " " if ans_letter and opt.get(ans_letter) else "") + e.get("answer_text", "")
        cids, best = gold_map(q + " " + ans_full[:100], chunks, idf)
        if not cids or best < 6.0:
            drop_no_gold += 1
            continue
        support_th = 0.15 if ans_letter else 0.30
        support = answer_support(ans_full, [chunk_by_id[c] for c in cids])
        if support < support_th:
            drop_support += 1
            continue
        qtype = classify_type(q, ans_full)
        entry = {
            "id": "",
            "type": qtype,
            "question": q,
            "gold_answer": (f"{ans_letter}. {opt[ans_letter]}" if ans_letter and ans_letter in opt else ans_full).strip(),
            "gold_evidence": [],
            "gold_chunks": cids,
            "key_points": extract_key_points(q, ans_full),
            "source": e["source"],
        }
        if opt:
            entry["options"] = opt
        if ans_letter:
            entry["answer_letter"] = ans_letter
        final.append(entry)
    print(f"[audit A2] gold 映射失败丢弃 {drop_no_gold}")
    print(f"[audit A3] 答案支撑不足丢弃 {drop_support}")
    print(f"[audit] 新题入选 {len(final)}")

    # 合并 v1.1
    v11_path = ROOT / "data" / "eval" / "questions_v1.1.jsonl"
    with open(v11_path, "r", encoding="utf-8") as f:
        v1 = [json.loads(line) for line in f if line.strip()]
    for e in v1:
        e.setdefault("source", "v1.0人工")
        e.setdefault("key_points", [])

    all_entries = v1 + final
    tc = Counter(e["type"] for e in all_entries)
    for i, e in enumerate(all_entries, 1):
        e["id"] = f"q{i:03d}"

    out_path = ROOT / "data" / "eval" / "questions_v2.0.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for e in all_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    by_src_final = Counter(e["source"] for e in final)
    manifest = {
        "version": "2.0",
        "created": "2026-10-07",
        "note": "新题源均带标准答案；A1 去重 / A2 gold 映射 / A3 答案支撑 / A4 时代缺图过滤全自动质检，无需人工填表",
        "total": len(all_entries),
        "from_v1": len(v1),
        "new": len(final),
        "type_distribution": dict(tc),
        "source_parse_stats": src_stats,
        "source_final_stats": dict(by_src_final),
        "audit": {
            "dropped_duplicate": dropped_dup,
            "dropped_era_or_figure": len(deduped) - len(kept),
            "dropped_no_gold": drop_no_gold,
            "dropped_low_support": drop_support,
        },
        "sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
        "sources": [
            "F:\\下载\\hyperdown-client-windows-amd64\\Downloads\\计算机网络技术题库(密码yscl).pdf",
            "F:\\下载\\hyperdown-client-windows-amd64\\Downloads\\计算机网络\\计算机网络\\计算机网络试题库含答案(个人整理打印版).pdf",
            "F:\\下载\\hyperdown-client-windows-amd64\\Downloads\\计算机网络\\计算机网络\\计算机网络期末试题及答案.pdf",
            "F:\\下载\\hyperdown-client-windows-amd64\\Downloads\\计算机网络\\计算机网络\\计算机网络试题及答案.pdf",
            "F:\\下载\\hyperdown-client-windows-amd64\\Downloads\\计算机网络\\计算机网络\\计算机网络笔试题.pdf",
        ],
    }
    with open(ROOT / "data" / "eval" / "eval_v2.0_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    rep = [
        "# eval-v2.0 自动质检报告",
        "",
        "- 生成时间：2026-10-07",
        f"- 总题数：**{len(all_entries)}**（v1.1 保留 {len(v1)} + 新增 {len(final)}）",
        f"- 题型分布：{dict(tc)}",
        f"- 去重丢弃 {dropped_dup}；时代/缺图过滤丢弃 {len(deduped) - len(kept)}；"
        f"gold 映射失败丢弃 {drop_no_gold}；答案支撑不足丢弃 {drop_support}",
        "",
        "## 各题源解析量 / 入选量",
        "",
    ]
    for k, v in src_stats.items():
        rep.append(f"- {k}：解析 {v} 题")
    for k, v in by_src_final.items():
        rep.append(f"- 入选 {k}：{v} 题")
    rep += ["", "## 入选样例（每题源前 3 题）", ""]
    for s in sorted(set(e["source"] for e in final)):
        for e in [x for x in final if x["source"] == s][:3]:
            rep.append(f"### [{s}] {e['id']}（{e['type']}）")
            rep.append(f"- 题干：{e['question'][:90]}")
            rep.append(f"- 答案：{e['gold_answer'][:70]}")
            rep.append(f"- gold_chunks：{e['gold_chunks']}")
            rep.append("")
    (ROOT / "data" / "eval" / "audit_report_v2.0.md").write_text("\n".join(rep), encoding="utf-8")

    print(f"[build] questions_v2.0.jsonl 写出：{len(all_entries)} 题")
    print(f"[build] 题型分布：{dict(tc)}")
    print(f"[build] 报告：data/eval/audit_report_v2.0.md")


if __name__ == "__main__":
    main()
