"""auto_gen_classify v6.0 - 数据分类分级 + 脱敏"""
import re
from enum import Enum

class Level(Enum):
    PUBLIC = 1; INTERNAL = 2; CONFIDENTIAL = 3; SECRET = 4; TOP_SECRET = 5

PII = {
    "phone": re.compile(r"1[3-9]\\d{9}"),
    "email": re.compile(r"[\\w.+-]+@[\\w.-]+\\.[a-zA-Z]{2,}"),
    "id_card": re.compile(r"\\d{17}[\\dXx]"),
}

def classify(text):
    hits = []; level = Level.PUBLIC
    for name, pat in PII.items():
        m = pat.findall(text)
        if m:
            hits.append({"type": name, "count": len(m)})
            if name == "id_card": level = max(level, Level.CONFIDENTIAL)
            elif name == "phone": level = max(level, Level.INTERNAL)
    return {"level": level.name, "hits": hits}

def mask(text, types=None):
    masked = text
    for name, pat in PII.items():
        if types and name not in types: continue
        if name == "phone": masked = pat.sub(lambda m: m.group()[:3] + "****" + m.group()[-4:], masked)
        elif name == "email": masked = pat.sub(lambda m: m.group()[0] + "***@***", masked)
        elif name == "id_card": masked = pat.sub(lambda m: m.group()[:6] + "***********" + m.group()[-2:], masked)
    return masked

if __name__ == "__main__":
    t = "用户张三 13812345678 zhangsan@gmail.com"
    print(classify(t)); print(mask(t))
