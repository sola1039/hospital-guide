# HTML 解析模块: 从深圳大学总医院页面提取医生数据
import re
from html import unescape

TITLE_RE = re.compile(r"职称：</span>([^<]+)")
DEPT_RE = re.compile(r"所属科室：</span>\s*<a[^>]*>\s*<span>([^<]+)</span>")
POST_RE = re.compile(r"职务：</span>([^<]+)")
NAME_RE = re.compile(r'<div class="doct_con">\s*<h2>([^<]+)</h2>')
TEAM_ENTRY_RE = re.compile(
    r'<a href="/Html/Doctors/Main/Index_(\d+)\.html" class="doc_name">([^<]+)</a>.*?'
    r"职称：</span>\s*<a>([^<]*)</a>.*?特长：</span>\s*([^<]*)",
    re.S,
)
DOCTOR_LINK_RE = re.compile(r"/Html/Doctors/Main/Index_(\d+)\.html")
TEAM_LINK_RE = re.compile(r"/Html/Departments/Main/DoctorTeam_(\d+)\.html")


def clean(text: str) -> str:
    text = unescape(text or "")
    text = text.replace(" ", " ").replace("　", " ")
    text = re.sub(r"[ \t\r\n]+", " ", text)
    return text.strip()


def block_text(html: str) -> str:
    """块内HTML转纯文本, 段落边界保留换行"""
    html = re.sub(r"</p\s*>|<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", "", html)
    text = unescape(text).replace(" ", " ").replace("　", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def parse_team_page(html: str) -> list:
    """解析科室团队页, 返回 [{id, 姓名, 职称, 特长}] 列表"""
    results = []
    for doc_id, name, title, techang in TEAM_ENTRY_RE.findall(html):
        results.append(
            {
                "id": int(doc_id),
                "姓名": clean(name),
                "职称": clean(title),
                "特长": clean(techang),
            }
        )
    return results


def parse_doctor_page(html: str) -> dict:
    """解析医生详情页, 返回 {姓名, 职称, 科室, 职务, 诊疗特长, 详细介绍}"""
    name_m = NAME_RE.search(html)
    dept_m = DEPT_RE.search(html)
    title_m = TITLE_RE.search(html)
    post_m = POST_RE.search(html)
    blocks = re.findall(r'<div class="techang">(.*?)</div>', html, re.S)
    techang = block_text(blocks[0]) if len(blocks) > 0 else ""
    detail = block_text(blocks[1]) if len(blocks) > 1 else ""
    return {
        "姓名": clean(name_m.group(1)) if name_m else "",
        "职称": clean(title_m.group(1)) if title_m else "",
        "科室": clean(dept_m.group(1)) if dept_m else "",
        "职务": clean(post_m.group(1)) if post_m else "",
        "诊疗特长": techang,
        "详细介绍": detail,
    }


def collect_doctor_ids(html: str) -> set:
    return {int(x) for x in DOCTOR_LINK_RE.findall(html)}


def collect_team_ids(html: str) -> set:
    return {int(x) for x in TEAM_LINK_RE.findall(html)}
