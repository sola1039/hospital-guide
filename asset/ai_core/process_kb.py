# -*- coding: utf-8 -*-
"""就诊全流程知识库与状态机。

流程推进是确定性的(状态机), 不依赖大模型, 防止 AI 乱编流程。
大模型只负责把步骤翻译成大白话和回答问题。
"""

# 就诊全流程步骤模板: nav_target 是可被 /api/navigate 解析的地点关键词,
# "@dept" 表示去就诊科室, "@exam" 表示按检查项目动态决定; nav_label 是给用户看的地点名
PROCESS_STEPS = [
    {"key": "triage", "title": "预检分诊", "desc": "先说说哪里不舒服, 确定挂哪个科",
     "nav_target": "", "nav_label": "", "tips": ["把症状、持续时间想清楚", "有旧病历和检查报告一起带上"]},
    {"key": "prep", "title": "就诊前准备", "desc": "带齐证件, 确认是否需要空腹",
     "nav_target": "", "nav_label": "", "tips": ["带身份证和医保卡", "抽血、腹部B超、胃镜需要空腹", "前一天早点休息"]},
    {"key": "register", "title": "挂号", "desc": "到分层挂号收费处挂号, 或提前手机预约",
     "nav_target": "分层挂号收费", "nav_label": "挂号收费处", "tips": ["第一次来要先办就诊卡", "不知道挂哪个科可以问导医台"]},
    {"key": "checkin", "title": "到院签到候诊", "desc": "到诊区签到, 坐下等叫号",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["留意叫号屏幕和广播", "别走远, 快到号时回到候诊区"]},
    {"key": "first_visit", "title": "医生首诊", "desc": "向医生说清楚症状, 配合问诊",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["按时间顺序说症状", "医生开的单子要收好"]},
    {"key": "pay", "title": "缴费", "desc": "拿着检查单或处方先去缴费",
     "nav_target": "划价收费", "nav_label": "收费处", "tips": ["缴费后单据留好", "可以用医保卡或手机支付"]},
    {"key": "exam", "title": "检查检验", "desc": "按检查单做抽血、拍片、B超等检查",
     "nav_target": "@exam", "nav_label": "@exam", "tips": ["看清检查单上的楼层和检查前要求", "抽血要空腹, B超有的要憋尿"]},
    {"key": "report", "title": "取报告", "desc": "等检查报告出来, 自助机打印或窗口领取",
     "nav_target": "检验科", "nav_label": "取报告处(检验科)", "tips": ["报告一般1-2小时, 具体看检查项目", "取报告小票要收好"]},
    {"key": "second_visit", "title": "复诊看报告", "desc": "带报告回诊室, 让医生看结果",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["回诊室可能要重新刷号", "把所有报告按顺序放好"]},
    {"key": "final", "title": "终诊结论", "desc": "医生给出诊断结果和治疗方案",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["听不清就请医生写下来", "问清楚要不要复诊"]},
    {"key": "medicine", "title": "取药用药", "desc": "缴费后到药房取药, 按医嘱服药",
     "nav_target": "西药房取药窗口", "nav_label": "西药房取药窗口", "tips": ["取药时核对姓名和药名", "看清楚怎么吃、吃多久"]},
    {"key": "followup", "title": "复诊安排", "desc": "记好复诊时间, 按时回来",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["把复诊时间写在日历上", "病情有变化随时来"]},
]

# 症状关键词 -> 科室 id(与 input/database/seed_data.py 的 departments.id 对应)
SYMPTOM_MAP = [
    (["发烧", "发热", "发冷"], "grb"),
    (["咳嗽", "感冒", "嗓子疼", "咽痛", "有痰", "气短", "哮喘"], "nkmz1"),
    (["头痛", "头晕", "失眠", "手麻", "中风"], "nkmz2"),
    (["肚子疼", "胃疼", "胃胀", "拉肚子", "腹泻", "便秘", "恶心", "呕吐", "反酸"], "nkmz1"),
    (["胸闷", "心慌", "胸痛", "血压", "高血压", "心脏"], "nkmz1"),
    (["血糖", "糖尿病", "甲亢", "甲状腺"], "nkmz2"),
    (["牙疼", "牙齿", "拔牙", "补牙", "洗牙", "口腔"], "kqk"),
    (["眼睛", "视力", "看不清", "眼干", "近视"], "yk"),
    (["耳朵", "耳鸣", "鼻炎", "流鼻涕", "打鼾", "喉咙", "咽喉"], "ebhk"),
    (["皮肤", "痒", "疹子", "湿疹", "过敏", "皮炎", "长痘", "荨麻疹"], "pfk"),
    (["外伤", "伤口", "缝合", "拆线", "扭伤", "骨折"], "wkmz"),
    (["腰疼", "腰痛", "颈椎", "肩膀疼", "腿疼", "疼痛", "康复"], "kftt"),
    (["怀孕", "产检", "孕妇", "建档"], "ckmz"),
    (["妇科", "月经", "白带"], "fkmz"),
    (["孩子", "小孩", "宝宝", "儿童", "小儿"], "erke"),
    (["体检", "健康检查", "入学体检"], "pttc"),
    (["胃镜", "肠镜", "胃肠镜"], "xhnj"),
    (["b超", "彩超", "超声"], "csk"),
    (["抽血", "验血", "化验", "查血"], "jyk"),
    (["拍片", "ct", "核磁", "x光", "放射"], "fs"),
    (["心电图", "心电"], "gnjc"),
    (["中医", "调理", "针灸", "推拿"], "zyk"),
    (["肿瘤", "化疗"], "zlmz"),
    (["碎石", "结石"], "ssj"),
    (["打针", "输液", "吊针"], "zsys"),
]


class JourneyState:
    """就诊流程状态机。步骤推进完全确定, 不经过大模型。"""

    def __init__(self, dept_id: str = "", exams: list = None):
        self.dept_id = dept_id
        self.exams = exams or []
        self.current = 0
        self.done_keys: list = []

    def current_step(self) -> dict:
        step = dict(PROCESS_STEPS[self.current])
        step["index"] = self.current
        step["total"] = len(PROCESS_STEPS)
        return step

    def advance(self) -> dict:
        if self.current < len(PROCESS_STEPS) - 1:
            self.done_keys.append(PROCESS_STEPS[self.current]["key"])
            self.current += 1
        return self.current_step()

    def back(self) -> dict:
        if self.current > 0:
            self.current -= 1
            if self.done_keys and self.done_keys[-1] == PROCESS_STEPS[self.current]["key"]:
                self.done_keys.pop()
        return self.current_step()

    def jump_to(self, key: str) -> dict:
        for i, s in enumerate(PROCESS_STEPS):
            if s["key"] == key:
                self.current = i
                return self.current_step()
        return self.current_step()

    def to_dict(self) -> dict:
        return {"dept_id": self.dept_id, "exams": self.exams,
                "current": self.current, "done_keys": self.done_keys}

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "JourneyState":
        state = cls(d.get("dept_id", ""), d.get("exams", []))
        state.current = int(d.get("current", 0))
        state.done_keys = list(d.get("done_keys", []))
        return state

    @classmethod
    def from_json(cls, text: str) -> "JourneyState":
        import json
        return cls.from_dict(json.loads(text or "{}"))


def match_departments(symptom_text: str) -> list:
    """按症状关键词匹配科室, 返回按命中数排序的科室 id 列表。"""
    text = symptom_text.lower()
    scores: dict = {}
    for keywords, dept_id in SYMPTOM_MAP:
        hits = sum(1 for kw in keywords if kw in text)
        if hits:
            scores[dept_id] = scores.get(dept_id, 0) + hits
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    return [dept_id for dept_id, _ in ranked]
