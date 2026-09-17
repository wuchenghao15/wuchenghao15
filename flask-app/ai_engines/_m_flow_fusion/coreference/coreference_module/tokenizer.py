"""
Chinese Tokenizer - Fine-grained Classification v2
Fixes jieba segmentation/POS tagging issues
"""

import re
import jieba
import jieba.posseg as pseg
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Token:
    """Token result"""

    word: str
    pos: str
    entity_type: str = "O"
    start: int = -1  # start character position
    end: int = -1  # end character position


@dataclass
class Mention:
    """Entity mention (with position info)"""

    surface: str  # surface text
    type: str  # entity type: PER_NAME, PER_TITLE, LOC_NAME, LOC_PLACE, OBJ, TIME
    start: int  # start character position
    end: int  # end character position
    sentence_id: int = 0  # sentence ID (optional)


class ChineseTokenizer:
    """
    Chinese Tokenizer - Fine-grained Classification

    Entity types:
    - PER_NAME:  person names (e.g. Xiao Ming, Liu Dehua, Zhang San)
    - PER_TITLE: person titles (e.g. mama, doctor, girl)
    - LOC_NAME:  location names (e.g. Beijing, Shanghai, New York)
    - LOC_PLACE: places (e.g. school, hospital, supermarket)
    - OBJ:       objects
    - O:         other
    """

    # === Person title words (not names, but person references) ===
    PERSON_TITLES = {
        # Kinship titles
        "妈妈",
        "爸爸",
        "父亲",
        "母亲",
        "爷爷",
        "奶奶",
        "姥姥",
        "姥爷",
        "外公",
        "外婆",
        "公公",
        "婆婆",
        "岳父",
        "岳母",
        "哥哥",
        "姐姐",
        "弟弟",
        "妹妹",
        "叔叔",
        "阿姨",
        "舅舅",
        "姑姑",
        "伯伯",
        "婶婶",
        "姨妈",
        "姨父",
        "舅妈",
        "姑父",
        "儿子",
        "女儿",
        "孙子",
        "孙女",
        "外孙",
        "外孙女",
        "丈夫",
        "妻子",
        "老公",
        "老婆",
        "爱人",
        "媳妇",
        "女婿",
        # Professional titles
        "医生",
        "护士",
        "老师",
        "教授",
        "学生",
        "警察",
        "司机",
        "厨师",
        "工人",
        "农民",
        "程序员",
        "科学家",
        "设计师",
        "工程师",
        "律师",
        "法官",
        "经理",
        "老板",
        "员工",
        "同事",
        "秘书",
        "助理",
        "主任",
        "院长",
        "师傅",
        "徒弟",
        "教练",
        "运动员",
        "演员",
        "歌手",
        "导演",
        "记者",
        "服务员",
        "售货员",
        "快递员",
        "外卖员",
        "保安",
        "保洁",
        "主播",
        "博主",
        "网红",
        "明星",
        "艺人",
        "歌星",
        "影星",
        "UP主",
        "老铁",
        "兄弟",
        "姐妹",
        "小哥",
        "小姐姐",
        "小哥哥",
        "大神",
        "大佬",
        "帅哥",
        "美女",
        "靓仔",
        "靓女",
        "小伙",
        "姑娘",
        "少女",
        "小姑娘",
        "太太",
        "夫人",
        "女士",
        "先生",
        "小姐",
        "员工",
        "职员",
        "同事",
        "小朋友",
        "大人",
        "成年人",
        "未成年人",
        "青少年",
        "中年人",
        # Administrative titles
        "市长",
        "县长",
        "区长",
        "镇长",
        "村长",
        "书记",
        "委员",
        "代表",
        "局长",
        "处长",
        "科长",
        "股长",
        "组长",
        "队长",
        "班长",
        "总统",
        "主席",
        "总理",
        "部长",
        "厅长",
        "司长",
        "署长",
        "将军",
        "司令",
        "军长",
        "师长",
        "团长",
        "营长",
        "连长",
        "排长",
        "选手",
        "冠军",
        "亚军",
        "季军",
        "球员",
        "球星",
        "教练员",
        # Service staff (note: some words are both nouns and verbs, avoid adding here)
        "客服",
        "前台",
        "导购",
        "柜员",
        "出纳",
        "会计",
        "审计",
        # Person descriptions (can be referred to by he/she)
        "男孩",
        "女孩",
        "小男孩",
        "小女孩",
        "男人",
        "女人",
        "老人",
        "年轻人",
        "孩子",
        "少年",
        "青年",
        "中年",
        "老年",
        "婴儿",
        "幼儿",
        "儿童",
        "小偷",
        "罪犯",
        "嫌疑人",
        "受害者",
        "证人",
        "原告",
        "被告",
        "牙医",
        "兽医",
        "中医",
        "西医",
        "名医",
        "大夫",
        "研究生",
        "博士生",
        "硕士生",
        "本科生",
        "高中生",
        "初中生",
        "小学生",
        # Social titles
        "同学",
        "朋友",
        "同事",
        "邻居",
        "客户",
        "顾客",
        "乘客",
        "病人",
        "患者",
        "伤员",
        "嫌疑人",
        "证人",
        "被告",
        "原告",
        "小偷",
        "骗子",
        "罪犯",
        "技术人员",
        "工作人员",
        "服务人员",
        # General titles (keep those that can refer to specific individuals)
        "先生",
        "女士",
        "小姐",
        "姑娘",
        "小伙",
        "小伙子",
        "大爷",
        "大妈",
        "大叔",
        "大婶",
        "男人",
        "女人",
        "孩子",
        "小孩",
        "老人",
        "年轻人",
        "中年人",
        "少年",
        "青年",
        "老年人",
        "男孩",
        "女孩",
        "男生",
        "女生",
        "男士",
        "女士",
        "老头",
        "老太太",
        # Note: generic terms like 'person', 'people', 'everyone' are not included as they are indefinite references
    }

    # === Place words (not named locations) ===
    PLACE_WORDS = {
        # Commercial places
        "超市",
        "商店",
        "店铺",
        "商场",
        "市场",
        "菜市场",
        "批发市场",
        "餐厅",
        "饭店",
        "酒店",
        "宾馆",
        "旅馆",
        "民宿",
        "酒吧",
        "咖啡厅",
        "药店",
        "书店",
        "花店",
        "水果店",
        "便利店",
        "专卖店",
        "银行",
        "邮局",
        "快递站",
        # Educational places
        "学校",
        "大学",
        "中学",
        "小学",
        "幼儿园",
        "培训班",
        "补习班",
        "教室",
        "实验室",
        "图书馆",
        "阅览室",
        "自习室",
        "办公室",
        "操场",
        "体育馆",
        "游泳池",
        "食堂",
        "宿舍",
        "礼堂",
        # Medical places
        "医院",
        "诊所",
        "卫生院",
        "门诊",
        "急诊",
        "病房",
        "手术室",
        "药房",
        "化验室",
        "检查室",
        # Office/work places
        "公司",
        "工厂",
        "车间",
        "仓库",
        "办公室",
        "会议室",
        "接待室",
        "写字楼",
        "园区",
        "基地",
        # Transportation places
        "机场",
        "车站",
        "火车站",
        "汽车站",
        "地铁站",
        "码头",
        "港口",
        "停车场",
        "加油站",
        "服务区",
        # Public places
        "公园",
        "广场",
        "博物馆",
        "美术馆",
        "展览馆",
        "科技馆",
        "电影院",
        "剧院",
        "音乐厅",
        "体育场",
        "游乐场",
        "派出所",
        "警察局",
        "法院",
        "政府",
        "市政府",
        # Residential places (houses/yards moved to OBJECT_WORDS, can be referred by "it")
        "家",
        "家里",
        "房间",
        "卧室",
        "客厅",
        "厨房",
        "卫生间",
        "阳台",
        "楼上",
        "楼下",
        "门口",
        "地下室",
        "车库",
        "小区",
        "社区",
        "村子",
        "胡同",
        "弄堂",
        "厕所",
        "洗手间",
        "盥洗室",
        "浴室",
        "储藏室",
        "杂物间",
        "阁楼",
        # Natural places
        "山上",
        "山下",
        "河边",
        "湖边",
        "海边",
        "田里",
        "地里",
        "林子",
        # Service places
        "网吧",
        "理发店",
        "美发店",
        "健身房",
        "洗浴中心",
        "足疗店",
        "修理店",
        "洗车店",
        "干洗店",
        "照相馆",
        "婚纱店",
        "诊所",
        "牙科",
        "眼科",
        "美容院",
        "按摩店",
        # Modern places
        "直播间",
        "录音棚",
        "摄影棚",
        "演播室",
        "工作室",
        "健身中心",
        "购物中心",
        "娱乐中心",
        "文化中心",
        "会展中心",
        "美食广场",
        "美食街",
        "步行街",
        "商业街",
        "网咖",
        "电竞馆",
        "桌游吧",
        "KTV",
        "酒吧",
    }

    # === Object words ===
    OBJECT_WORDS = {
        # Animals (can be referred by "it/they")
        "猫",
        "狗",
        "鸟",
        "鱼",
        "兔子",
        "老鼠",
        "蛇",
        "龟",
        "乌龟",
        "狮子",
        "老虎",
        "豹",
        "熊",
        "狼",
        "狐狸",
        "鹿",
        "马",
        "牛",
        "羊",
        "猪",
        "鸡",
        "鸭",
        "鹅",
        "鸽子",
        "麻雀",
        "燕子",
        "乌鸦",
        "喜鹊",
        "孔雀",
        "蝴蝶",
        "蜜蜂",
        "蚂蚁",
        "蟑螂",
        "蚊子",
        "苍蝇",
        "大象",
        "长颈鹿",
        "斑马",
        "河马",
        "犀牛",
        "熊猫",
        "猴子",
        "猩猩",
        "海豚",
        "鲸鱼",
        "鲨鱼",
        "章鱼",
        "螃蟹",
        "虾",
        "贝壳",
        "小猫",
        "小狗",
        "小鸟",
        "小鱼",
        "宠物",
        "动物",
        "鸟儿",
        "狗儿",
        "猫儿",
        "兔儿",  # Animals with "er" suffix
        # Food
        "苹果",
        "香蕉",
        "橘子",
        "葡萄",
        "西瓜",
        "草莓",
        "梨",
        "桃",
        "面包",
        "蛋糕",
        "饼干",
        "糖果",
        "巧克力",
        "冰淇淋",
        "饺子",
        "面条",
        "米饭",
        "馒头",
        "包子",
        "粥",
        "牛奶",
        "咖啡",
        "茶",
        "果汁",
        "可乐",
        "啤酒",
        "酒",
        "水",
        "菜",
        "肉",
        "鱼",
        "蛋",
        "饭",
        "药",
        # Electronics
        "电视",
        "电脑",
        "手机",
        "平板",
        "相机",
        "耳机",
        "音箱",
        "冰箱",
        "洗衣机",
        "空调",
        "微波炉",
        "电饭煲",
        "电话",
        "短信",
        "邮件",
        "视频",
        "音乐",
        "游戏",
        "直播",
        "微信",
        "抖音",
        "微博",
        "淘宝",
        "支付宝",
        "B站",
        "照片",
        "图片",
        "文章",
        "帖子",
        "评论",
        "弹幕",
        "报纸",
        "杂志",
        "小说",
        "故事",
        "新闻",
        "广播",
        "节目",
        "频道",
        # Vehicles
        "火车",
        "飞机",
        "轮船",
        "出租车",
        "公交车",
        "地铁",
        "高铁",
        "动车",
        # Dining
        "火锅",
        "烧烤",
        "奶茶",
        "外卖",
        "快餐",
        "盒饭",
        "便当",
        # Daily necessities
        "钥匙",
        "钱包",
        "眼镜",
        "雨伞",
        "手表",
        "项链",
        "戒指",
        "毛巾",
        "牙刷",
        "肥皂",
        "洗发水",
        # Clothing
        "衣服",
        "裤子",
        "鞋子",
        "帽子",
        "袜子",
        "手套",
        "围巾",
        "外套",
        "相机",
        "镜头",
        # Stationery/documents
        "书",
        "本子",
        "笔",
        "报纸",
        "杂志",
        "文件",
        "报告",
        "论文",
        "作业",
        "信",
        "快递",
        "包裹",
        "礼物",
        "礼品",
        "红包",
        "奖品",
        "奖金",
        # Vehicles
        "车",
        "汽车",
        "自行车",
        "摩托车",
        "公交车",
        "出租车",
        "火车",
        "飞机",
        "船",
        # Furniture
        "桌子",
        "椅子",
        "沙发",
        "床",
        "柜子",
        "书架",
        # Real estate
        "房子",
        "房屋",
        "住宅",
        "别墅",
        "公寓",
        "院子",
        "花园",
        "阳台",
        # Abstract objects/documents/matters (for coreference: it/this/that often refers to these)
        "项目",
        "计划",
        "方案",
        "问题",
        "决定",
        "战略",
        "部分",
        "模块",
        "系统",
        "服务器",
        "任务",
        "流程",
        "步骤",
        "版本",
        "合同",
        "协议",
        "政策",
        "规则",
        "测试",
        "交付",
        "延期",
        "申请",
        "分公司",
        "办事处",
        "程序",
        "软件",
        "应用",
        "代码",
        "算法",
        "数据",
        "接口",
        "网站",
        "平台",
        "东西",
        "物品",
        "货物",
        "商品",
        "物件",
        "店铺",
        "商铺",
        "门店",
        "网店",
        # Event/matter phrases (often referred to by "it")
        "这件事",
        "那件事",
        "这事",
        "那事",
        "此事",
        "这种做法",
        "那种做法",
        "这种情况",
        "那种情况",
        # Abstract nouns (frequent anaphora targets)
        "消息",
        "一致",
        "争议",
        "答复",
        "结论",
        "结果",
        "原因",
        "影响",
        "故障",
        # Organizations/departments/role groups (for "they/them" reference)
        "产品",
        "技术",
        "运营",
        "业务",
        "市场部",
        "销售部",
        "分公司",
        "办事处",
        "总部",
        "用户",
        "管理员",
        "团队",
        "管理层",
        "执行层",
        "投资方",
        "投资人",
        "创始人",
        "顾问",
        "外部顾问",
        "反馈",
        "理解",
        "立场",
        "意见",
        "建议",
        "想法",
        "方向",
    }

    # Abstract object suffixes: treat compound phrases like "acquisition plan/R&D proposal" as OBJ
    ABSTRACT_SUFFIXES = {
        "计划",
        "方案",
        "决定",
        "问题",
        "项目",
        "结论",
        "共识",
        "反馈",
        "理解",
        "立场",
        "意见",
        "建议",
        "想法",
        "方向",
    }

    # === Colloquial kinship prefix ("my dad/my mom/my sis...") ===
    _KINSHIP_TITLES = {
        "爸",
        "妈",
        "爸爸",
        "妈妈",
        "父亲",
        "母亲",
        "爷爷",
        "奶奶",
        "外公",
        "外婆",
        "姥爷",
        "姥姥",
        "哥",
        "姐",
        "哥哥",
        "姐姐",
        "弟",
        "妹",
        "弟弟",
        "妹妹",
        "老公",
        "老婆",
        "丈夫",
        "妻子",
    }

    # === Foreign names (jieba may not recognize) ===
    FOREIGN_NAMES = {
        "汤姆",
        "杰瑞",
        "杰克",
        "玛丽",
        "大卫",
        "迈克",
        "约翰",
        "彼得",
        "艾米",
        "露西",
        "安娜",
        "莉莉",
        "杰森",
        "凯文",
        "安迪",
        "麦克",
        "艾米丽",
        "史密斯",
        "约翰逊",
        "威廉姆",
        "杰克逊",
        "布莱恩",
        "玛格丽特",
        "伊丽莎白",
        "亚历山大",
        "迈克尔",
        "玛利亚",
        "安德烈",
        "维多利亚",
        "尼古拉斯",
        "克里斯",
        "詹姆斯",
        "罗伯特",
        "威廉",
        "理查德",
        "查尔斯",
        "托马斯",
        "乔治",
        "亨利",
        "爱德华",
        "弗兰克",
        "丹尼尔",
        "马修",
        "珍妮",
        "凯特",
        "索菲亚",
        "奥利维亚",
        "艾玛",
        "夏洛特",
    }

    # === Common nicknames (jieba may segment incorrectly) ===
    COMMON_NAMES = {
        # Xiao+name
        "小明",
        "小红",
        "小华",
        "小李",
        "小王",
        "小张",
        "小刘",
        "小陈",
        "小美",
        "小丽",
        "小军",
        "小燕",
        "小芳",
        "小强",
        "小刚",
        "小伟",
        "小杰",
        "小林",
        "小英",
        "小玲",
        "小敏",
        "小琳",
        "小慧",
        "小雪",
        "小静",
        "小艳",
        "小霞",
        "小梅",
        "小娟",
        "小兰",
        "小萍",
        "小云",
        # Lao+surname
        "老王",
        "老李",
        "老张",
        "老刘",
        "老陈",
        "老赵",
        "老周",
        "老吴",
        "老孙",
        "老杨",
        "老黄",
        "老林",
        "老郭",
        "老马",
        "老朱",
        "老胡",
        # A+name
        "阿强",
        "阿明",
        "阿华",
        "阿伟",
        "阿杰",
        "阿军",
        "阿刚",
        "阿林",
        # Common two-character names
        "张伟",
        "王芳",
        "李娜",
        "刘洋",
        "陈静",
        "杨洁",
        "赵敏",
        "黄丽",
        "周杰",
        "吴刚",
        "孙强",
        "马军",
        "朱明",
        "胡伟",
        "郭华",
        "林燕",
    }

    # Tiangan-Dizhi name codes (require special contextual judgment)
    # Note: these are only recognized as names in parallel structures, not standalone
    TIANGAN_DIZHI_NAMES = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}

    # === Time words ===
    TIME_WORDS = {
        # Relative time - day
        "今天",
        "昨天",
        "前天",
        "大前天",
        "明天",
        "后天",
        "大后天",
        "今日",
        "昨日",
        "前日",
        "明日",
        "后日",
        "当天",
        "那天",
        "这天",
        "某天",
        "有一天",
        # Relative time - week
        "这周",
        "上周",
        "上上周",
        "下周",
        "下下周",
        "本周",
        "这个星期",
        "上个星期",
        "下个星期",
        "周一",
        "周二",
        "周三",
        "周四",
        "周五",
        "周六",
        "周日",
        "周末",
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六",
        "星期天",
        "星期日",
        # Relative time - month
        "这个月",
        "上个月",
        "下个月",
        "本月",
        "当月",
        "一月",
        "二月",
        "三月",
        "四月",
        "五月",
        "六月",
        "七月",
        "八月",
        "九月",
        "十月",
        "十一月",
        "十二月",
        # Relative time - year
        "今年",
        "去年",
        "前年",
        "明年",
        "后年",
        "当年",
        "那年",
        "这一年",
        "某年",
        # Time periods
        "早上",
        "上午",
        "中午",
        "下午",
        "傍晚",
        "晚上",
        "深夜",
        "凌晨",
        "半夜",
        "早晨",
        "清晨",
        "黄昏",
        "夜里",
        "夜间",
        "白天",
        "黑夜",
        # Seasons
        "春天",
        "夏天",
        "秋天",
        "冬天",
        "春季",
        "夏季",
        "秋季",
        "冬季",
        # Holidays
        "春节",
        "过年",
        "元旦",
        "元旦节",
        "国庆",
        "国庆节",
        "国庆假期",
        "中秋",
        "中秋节",
        "端午",
        "端午节",
        "清明",
        "清明节",
        "五一",
        "五一节",
        "劳动节",
        "十一",
        "十一假期",
        "元宵节",
        "七夕",
        "七夕节",
        "重阳",
        "重阳节",
        "圣诞",
        "圣诞节",
        "平安夜",
        "除夕",
        "大年三十",
        "大年初一",
        # Fuzzy time
        "以前",
        "之前",
        "从前",
        "过去",
        "曾经",
        "以后",
        "之后",
        "将来",
        "未来",
        "日后",
        "现在",
        "目前",
        "当前",
        "此刻",
        "眼下",
        "如今",
        "刚才",
        "刚刚",
        "方才",
        "适才",
        "最近",
        "近来",
        "近期",
        "近日",
        "这段时间",
        "那段时间",
        # Clock times
        "一点",
        "两点",
        "三点",
        "四点",
        "五点",
        "六点",
        "七点",
        "八点",
        "九点",
        "十点",
        "十一点",
        "十二点",
    }

    # === Famous landmarks (as location names) ===
    FAMOUS_PLACES = {
        "长城",
        "故宫",
        "天安门",
        "颐和园",
        "圆明园",
        "天坛",
        "十三陵",
        "泰山",
        "华山",
        "黄山",
        "峨眉山",
        "武当山",
        "嵩山",
        "衡山",
        "西湖",
        "洱海",
        "青海湖",
        "太湖",
        "洞庭湖",
        "鄱阳湖",
        "九寨沟",
        "张家界",
        "黄龙",
        "桂林",
        "三峡",
        "漓江",
        "兵马俑",
        "布达拉宫",
        "莫高窟",
        "龙门石窟",
        "云冈石窟",
        "外滩",
        "东方明珠",
        "鼓浪屿",
        "黄鹤楼",
        "岳阳楼",
        "滕王阁",
    }

    # === Compound words requiring splitting ===
    COMPOUND_WORDS = {
        # Verb+place (action phrases, place words not treated as independent location entities)
        "回家": [("回家", "O")],  # Don't split, treat as O
        "到家": [("到家", "O")],
        "离家": [("离家", "O")],
        "出门": [("出门", "O")],
        "进门": [("进门", "O")],
        "上楼": [("上楼", "O")],
        "下楼": [("下楼", "O")],
        # Keep "at home" since "home" as adverbial does indicate location
        "在家": [("在", "O"), ("家", "LOC_PLACE")],
        # Have+object
        "有书": [("有", "O"), ("书", "OBJ")],
        "有车": [("有", "O"), ("车", "OBJ")],
        "有钱": [("有", "O"), ("钱", "OBJ")],
        "有房": [("有", "O"), ("房", "LOC_PLACE")],
        # System/project+verb (split to identify objects)
        "系统升级": [("系统", "OBJ"), ("升级", "O")],
        "系统崩溃": [("系统", "OBJ"), ("崩溃", "O")],
        "项目延期": [("项目", "OBJ"), ("延期", "O")],
        "项目完成": [("项目", "OBJ"), ("完成", "O")],
        # Verb+object (jieba may merge them)
        "看电视": [("看", "O"), ("电视", "OBJ")],
        "穿衣服": [("穿", "O"), ("衣服", "OBJ")],
        "喝咖啡": [("喝", "O"), ("咖啡", "OBJ")],
        "喝茶": [("喝", "O"), ("茶", "OBJ")],
        "喝水": [("喝", "O"), ("水", "OBJ")],
        "喝酒": [("喝", "O"), ("酒", "OBJ")],
        "吃饭": [("吃", "O"), ("饭", "OBJ")],
        "吃菜": [("吃", "O"), ("菜", "OBJ")],
        "开车": [("开", "O"), ("车", "OBJ")],
        "骑车": [("骑", "O"), ("车", "OBJ")],
        "洗衣服": [("洗", "O"), ("衣服", "OBJ")],
        "看书": [("看", "O"), ("书", "OBJ")],
        "写字": [("写", "O"), ("字", "O")],
        "打电话": [("打", "O"), ("电话", "OBJ")],
        "发短信": [("发", "O"), ("短信", "OBJ")],
        "发邮件": [("发", "O"), ("邮件", "OBJ")],
        "做作业": [("做", "O"), ("作业", "OBJ")],
        "写作业": [("写", "O"), ("作业", "OBJ")],
        "听音乐": [("听", "O"), ("音乐", "OBJ")],
        "看电影": [("看", "O"), ("电影", "OBJ")],
        "玩游戏": [("玩", "O"), ("游戏", "OBJ")],
        "刷手机": [("刷", "O"), ("手机", "OBJ")],
        "修电脑": [("修", "O"), ("电脑", "OBJ")],
        "洗碗": [("洗", "O"), ("碗", "OBJ")],
        "扫地": [("扫", "O"), ("地", "O")],
        "拖地": [("拖", "O"), ("地", "O")],
        "看直播": [("看", "O"), ("直播", "OBJ")],
        "刷抖音": [("刷", "O"), ("抖音", "OBJ")],
        "玩微信": [("玩", "O"), ("微信", "OBJ")],
        "发微博": [("发", "O"), ("微博", "OBJ")],
        "逛淘宝": [("逛", "O"), ("淘宝", "OBJ")],
        "买手机": [("买", "O"), ("手机", "OBJ")],
        "买衣服": [("买", "O"), ("衣服", "OBJ")],
        "买电脑": [("买", "O"), ("电脑", "OBJ")],
        "接电话": [("接", "O"), ("电话", "OBJ")],
        "挂电话": [("挂", "O"), ("电话", "OBJ")],
        "看报纸": [("看", "O"), ("报纸", "OBJ")],
        "读小说": [("读", "O"), ("小说", "OBJ")],
        "听广播": [("听", "O"), ("广播", "OBJ")],
        "拍照片": [("拍", "O"), ("照片", "OBJ")],
        "录视频": [("录", "O"), ("视频", "OBJ")],
        "写文章": [("写", "O"), ("文章", "OBJ")],
        "看新闻": [("看", "O"), ("新闻", "OBJ")],
        "坐火车": [("坐", "O"), ("火车", "OBJ")],
        "坐飞机": [("坐", "O"), ("飞机", "OBJ")],
        "坐地铁": [("坐", "O"), ("地铁", "OBJ")],
        "坐高铁": [("坐", "O"), ("高铁", "OBJ")],
        "坐公交": [("坐", "O"), ("公交", "OBJ")],
        "吃火锅": [("吃", "O"), ("火锅", "OBJ")],
        "吃烧烤": [("吃", "O"), ("烧烤", "OBJ")],
        # Organization+person title
        "公司员工": [("公司", "LOC_PLACE"), ("员工", "PER_TITLE")],
        "学校老师": [("学校", "LOC_PLACE"), ("老师", "PER_TITLE")],
        "医院医生": [("医院", "LOC_PLACE"), ("医生", "PER_TITLE")],
        "银行员工": [("银行", "LOC_PLACE"), ("员工", "PER_TITLE")],
        "工厂工人": [("工厂", "LOC_PLACE"), ("工人", "PER_TITLE")],
        # Parallel person titles
        "帅哥美女": [("帅哥", "PER_TITLE"), ("美女", "PER_TITLE")],
        "男女老少": [("男", "O"), ("女", "O"), ("老", "O"), ("少", "O")],
        "爷爷奶奶": [("爷爷", "PER_TITLE"), ("奶奶", "PER_TITLE")],
        "外公外婆": [("外公", "PER_TITLE"), ("外婆", "PER_TITLE")],
        "叔叔阿姨": [("叔叔", "PER_TITLE"), ("阿姨", "PER_TITLE")],
        # Classifier+object
        "本书": [("本", "O"), ("书", "OBJ")],
        "部手机": [("部", "O"), ("手机", "OBJ")],
        "台电脑": [("台", "O"), ("电脑", "OBJ")],
        "辆车": [("辆", "O"), ("车", "OBJ")],
        "件衣服": [("件", "O"), ("衣服", "OBJ")],
        "个苹果": [("个", "O"), ("苹果", "OBJ")],
        # Person+person (jieba may merge them)
        "爸爸妈妈": [("爸爸", "PER_TITLE"), ("妈妈", "PER_TITLE")],
        "爷爷奶奶": [("爷爷", "PER_TITLE"), ("奶奶", "PER_TITLE")],
        "哥哥姐姐": [("哥哥", "PER_TITLE"), ("姐姐", "PER_TITLE")],
        "弟弟妹妹": [("弟弟", "PER_TITLE"), ("妹妹", "PER_TITLE")],
        "叔叔阿姨": [("叔叔", "PER_TITLE"), ("阿姨", "PER_TITLE")],
        "舅舅姑姑": [("舅舅", "PER_TITLE"), ("姑姑", "PER_TITLE")],
        "老公老婆": [("老公", "PER_TITLE"), ("老婆", "PER_TITLE")],
        "哥哥弟弟": [("哥哥", "PER_TITLE"), ("弟弟", "PER_TITLE")],
        "姐姐妹妹": [("姐姐", "PER_TITLE"), ("妹妹", "PER_TITLE")],
        "外公外婆": [("外公", "PER_TITLE"), ("外婆", "PER_TITLE")],
        "公公婆婆": [("公公", "PER_TITLE"), ("婆婆", "PER_TITLE")],
        "岳父岳母": [("岳父", "PER_TITLE"), ("岳母", "PER_TITLE")],
    }

    # === Surname + title pattern ===
    SURNAME_TITLES = {
        "阿姨",
        "大爷",
        "大妈",
        "大叔",
        "大婶",
        "叔叔",
        "婶婶",
        "爷爷",
        "奶奶",
        "伯伯",
        "姑姑",
        "舅舅",
        "先生",
        "女士",
        "小姐",
        "太太",
        "夫人",  # Honorifics
        "师傅",
        "老板",
        "经理",
        "总",
        "董",  # Professional titles
        "医生",
        "护士",
        "教授",
        "博士",
        "律师",
        "法官",
        "警官",  # Professional occupations
        "老师",
        "校长",
        "主任",
        "院长",
        "部长",
        "局长",  # Education/administrative
    }

    # Common surnames
    SURNAMES = {
        "张",
        "李",
        "王",
        "刘",
        "陈",
        "杨",
        "黄",
        "赵",
        "周",
        "吴",
        "徐",
        "孙",
        "马",
        "朱",
        "胡",
        "郭",
        "何",
        "高",
        "林",
        "罗",
        "郑",
        "梁",
        "谢",
        "唐",
        "许",
        "邓",
        "冯",
        "韩",
        "曹",
        "曾",
    }

    # Weak rule only for test names like Zhang San / Li Si / Wang Wu
    _NUM_NAME_CHARS = set("一二三四五六七八九十")

    # === Compound surnames ===
    COMPOUND_SURNAMES = {
        "欧阳",
        "司马",
        "诸葛",
        "东方",
        "上官",
        "皇甫",
        "令狐",
        "公孙",
        "慕容",
        "南宫",
        "独孤",
        "轩辕",
        "尉迟",
        "长孙",
        "宇文",
        "端木",
    }

    # === Exclusion words (common words mistagged as locations by jieba) ===
    # Note: merged two definitions to avoid incomplete exclusion sets
    NOT_LOCATION = {
        # Directional word combinations
        "东西",
        "西东",
        "南北",
        "上下",
        "左右",
        "前后",
        "朝西",
        "朝东",
        "朝南",
        "朝北",
        "向西",
        "向东",
        "向南",
        "向北",
        "往西",
        "往东",
        "往南",
        "往北",
        "东边",
        "西边",
        "南边",
        "北边",
        # Others
        "美",
        "里",
        "上海滩",
        # Musical instruments (jieba may mistag as locations)
        "吉他",
        "提琴",
        "钢琴",
    }

    # === Exclusion words (common words mistagged as person names by jieba) ===
    NOT_PERSON = {
        "喝咖啡",
        "看电视",
        "穿衣服",
        "吃饭",
        "开车",
        "岳父",
        "岳母",
        "明星",
        "小可爱",
        "小狗",
        "小猫",
        "猫咪",
        "狗狗",
        "宠物",  # Animals
        "华为",
        "小米",
        "苹果",
        "腾讯",
        "阿里",
        "百度",
        "京东",
        "美团",  # Companies
        "人",
        "人们",
        "大家",
        "众人",
        "旁人",
        "路人",
        "行人",  # Generic references
        "小宝贝",
        "宝贝",
        "亲爱的",
        "帅哥",
        "美女",  # Nicknames (treated as person)
        "滑雪",
        "滑冰",
        "游泳",
        "跑步",
        "健身",  # Sports
        "小提琴",
        "大提琴",
        "钢琴",
        "吉他",
        "笛子",  # Musical instruments
        # Idioms/adjective phrases (jieba often mistags as person names)
        "阳光明媚",
        "风和日丽",
        "春暖花开",
        "万里无云",
        "碧空如洗",
        "鸟语花香",
        "山清水秀",
        "风景如画",
        "美不胜收",
        "如诗如画",
        "心旷神怡",
        "赏心悦目",
        "流连忘返",
        "叹为观止",
        "目不暇接",
        "天气",
        "阳光",
        "月光",
        "星光",
        "灯光",
        "光芒",
        "光线",
    }

    def __init__(self):
        """Initialize: add custom words to jieba"""
        # Add common nicknames
        for name in self.COMMON_NAMES:
            jieba.add_word(name, tag="nr")

        # Add foreign names
        for name in self.FOREIGN_NAMES:
            jieba.add_word(name, tag="nr")

        # Add professional titles (prevent jieba from splitting)
        for title in self.PERSON_TITLES:
            jieba.add_word(title, tag="n")

        # Add surname+title combos
        for surname in self.SURNAMES:
            for title in self.SURNAME_TITLES:
                jieba.add_word(surname + title, tag="nr")

        # Add place words (prevent jieba from splitting)
        for place in self.PLACE_WORDS:
            jieba.add_word(place, tag="n")

        # Add object words (prevent jieba from splitting)
        for obj in self.OBJECT_WORDS:
            jieba.add_word(obj, tag="n")

        # Add colloquial kinship phrases (improve recognition of "my dad/my mom" patterns)
        for kin in self._KINSHIP_TITLES:
            jieba.add_word("我" + kin, tag="n")

    def tokenize(self, text: str) -> List[Token]:
        """Tokenize and annotate entity types (with position info)

        Args:
            text: input text

        Returns:
            List[Token]: tokenization results, each Token contains word, pos, entity_type, start, end
        """
        raw_tokens = [(t.word, t.flag) for t in pseg.cut(text)]
        tokens = []

        # Single-pointer scan to locate span
        cursor = 0

        i = 0
        while i < len(raw_tokens):
            word, flag = raw_tokens[i]

            # Calculate current word span
            start = text.find(word, cursor)
            if start == -1:
                start = cursor  # fallback
            end = start + len(word)

            # 0. Compound surname merge: if current word is compound surname followed by name, merge
            if word in self.COMPOUND_SURNAMES and i + 1 < len(raw_tokens):
                next_word, next_flag = raw_tokens[i + 1]
                if next_flag in ["nr", "nrt", "nrfg"] or len(next_word) <= 2:
                    # Merge compound surname and name
                    merged_word = word + next_word
                    merged_end = start + len(merged_word)
                    tokens.append(
                        Token(word=merged_word, pos="nr", entity_type="PER_NAME", start=start, end=merged_end)
                    )
                    cursor = merged_end
                    i += 2
                    continue

            # 0.5 Single-char surname merge: if single char tagged as name, try merging with following chars
            if word in self.SURNAMES and flag in ["nr", "nrt"] and len(word) == 1 and i + 1 < len(raw_tokens):
                next_word, next_flag = raw_tokens[i + 1]
                if len(next_word) <= 2 and next_flag not in ["v", "p", "c", "d", "r"]:
                    # Merge surname and name
                    merged_word = word + next_word
                    merged_end = start + len(merged_word)
                    tokens.append(
                        Token(word=merged_word, pos="nr", entity_type="PER_NAME", start=start, end=merged_end)
                    )
                    cursor = merged_end
                    i += 2
                    continue

            # 1. Check if splitting is needed
            if word in self.COMPOUND_WORDS:
                sub_cursor = start
                for w, etype in self.COMPOUND_WORDS[word]:
                    sub_start = sub_cursor
                    sub_end = sub_cursor + len(w)
                    tokens.append(Token(word=w, pos="x", entity_type=etype, start=sub_start, end=sub_end))
                    sub_cursor = sub_end
                cursor = end
                i += 1
                continue

            # 1.5 Name+particle adhesion fix: e.g. name stuck with adverbs
            # Let the name enter PER_NAME, avoid missing in parallel structures
            if (
                len(word) == 3
                and word[0] in self.SURNAMES
                and "\u4e00" <= word[1] <= "\u9fff"
                and word[2] in {"都", "也", "还", "就", "才"}
            ):
                name = word[:2]
                tail = word[2:]
                name_end = start + 2
                tokens.append(Token(word=name, pos="nr", entity_type="PER_NAME", start=start, end=name_end))
                tokens.append(Token(word=tail, pos="d", entity_type="O", start=name_end, end=end))
                cursor = end
                i += 1
                continue

            # 1.5.1 Name+verb adhesion fix: e.g. name stuck with verbs
            # Common verb list
            common_verbs = {
                "问",
                "说",
                "想",
                "看",
                "听",
                "做",
                "走",
                "来",
                "去",
                "给",
                "让",
                "叫",
                "请",
                "找",
                "要",
                "会",
                "能",
                "可",
                "知",
                "道",
            }
            if (
                len(word) == 3
                and word[0] in self.SURNAMES
                and word[1] in self._NUM_NAME_CHARS
                and word[2] in common_verbs
            ):
                name = word[:2]
                verb = word[2:]
                name_end = start + 2
                tokens.append(Token(word=name, pos="nr", entity_type="PER_NAME", start=start, end=name_end))
                tokens.append(Token(word=verb, pos="v", entity_type="O", start=name_end, end=end))
                cursor = end
                i += 1
                continue

            # 1.5.2 Merge "title+men": e.g. "teacher"+"men" -> "teachers"
            # Preserves plural marker for plural pronoun resolution
            if i + 1 < len(raw_tokens):
                next_word, next_flag = raw_tokens[i + 1]
                if next_word == "们":
                    entity_type = self._get_entity_type(word, flag)
                    if entity_type in {"PER_TITLE", "PER_NAME"}:
                        merged = word + "们"
                        merged_end = end + 1
                        tokens.append(
                            Token(word=merged, pos=flag, entity_type=entity_type, start=start, end=merged_end)
                        )
                        cursor = merged_end
                        i += 2  # skip current word and "men"
                        continue

            # 1.6 Merge numeric year: 2023 + nian -> 2023nian
            if re.match(r"^\d{4}$", word) and i + 1 < len(raw_tokens):
                next_word, next_flag = raw_tokens[i + 1]
                if next_word == "年":
                    merged = word + "年"
                    merged_end = start + len(merged)
                    tokens.append(Token(word=merged, pos="t", entity_type="TIME", start=start, end=merged_end))
                    cursor = merged_end
                    i += 2
                    continue

            # 1.7 Tiangan-Dizhi as name codes in parallel structures
            # e.g. A, B, C, D in "A, B, C, D all came"
            if word in self.TIANGAN_DIZHI_NAMES:
                # Check if in parallel structure (surrounded by commas)
                if i > 0 and raw_tokens[i - 1][0] in {"、", "，", ","}:
                    tokens.append(Token(word=word, pos="nr", entity_type="PER_NAME", start=start, end=end))
                    cursor = end
                    i += 1
                    continue
                elif i + 1 < len(raw_tokens) and raw_tokens[i + 1][0] in {"、", "，", ","}:
                    tokens.append(Token(word=word, pos="nr", entity_type="PER_NAME", start=start, end=end))
                    cursor = end
                    i += 1
                    continue

            # 1.8 Entity conjunction prefix cleanup: remove leading conjunctions
            # But exclude known valid compound words
            if len(word) >= 2 and word[0] in {"和", "与", "及", "或", "跟", "同"}:
                # Exclude known valid compound words
                valid_compounds = {
                    "同学",
                    "同事",
                    "同志",
                    "同意",
                    "同样",
                    "同时",
                    "同情",
                    "和平",
                    "和谐",
                    "和睦",
                    "和解",
                    "和气",
                    "与其",
                    "与否",
                    "与会",
                    "及时",
                    "及格",
                    "及早",
                    "或者",
                    "或许",
                    "跟随",
                    "跟踪",
                    "跟进",
                    "跟班",
                }
                if word in valid_compounds:
                    # Keep as is, do not split
                    pass
                else:
                    # Check if remainder after removing prefix is valid name
                    rest = word[1:]
                    rest_flag = "nr"  # assume it's a person name
                    rest_entity = self._get_entity_type(rest, rest_flag)
                    # Only split when remainder is a confirmed name
                    if rest in self.COMMON_NAMES or rest in self.FOREIGN_NAMES or len(rest) >= 2:
                        if rest_entity == "PER_NAME":
                            # Split: conjunction + name
                            conj_end = start + 1
                            tokens.append(Token(word=word[0], pos="c", entity_type="O", start=start, end=conj_end))
                            tokens.append(Token(word=rest, pos="nr", entity_type="PER_NAME", start=conj_end, end=end))
                            cursor = end
                            i += 1
                            continue

            # 1.9 Merge consecutive English words into entity (e.g. New York)
            if flag == "eng" and i + 1 < len(raw_tokens):
                next_word, next_flag = raw_tokens[i + 1]
                # Skip spaces
                if next_word.strip() == "" and i + 2 < len(raw_tokens):
                    next_next_word, next_next_flag = raw_tokens[i + 2]
                    if next_next_flag == "eng":
                        # Merge word + space + next_next_word
                        merged = word + " " + next_next_word
                        merged_end = start + len(merged)
                        merged_type = self._get_entity_type(merged, "eng")
                        if merged_type == "O":
                            # Determine by first word
                            if word in {"New", "Los", "San"}:
                                merged_type = "LOC_NAME"
                            elif word[0].isupper():
                                merged_type = "PER_NAME"
                        tokens.append(
                            Token(word=merged, pos="eng", entity_type=merged_type, start=start, end=merged_end)
                        )
                        cursor = merged_end
                        i += 3
                        continue

            # 2. Context fix: if object word is followed by "store", do not classify as object
            entity_type = self._get_entity_type(word, flag)
            if entity_type == "OBJ" and i + 1 < len(raw_tokens):
                next_word = raw_tokens[i + 1][0]
                if next_word in {"店", "公司", "集团", "厂", "厂家"}:
                    entity_type = "O"

            # 2.1 Context fix: title words after "want to be/become" are not identified as persons
            # e.g. "doctor" in "someone wants to be a doctor" is a target, not a person
            if entity_type == "PER_TITLE" and i >= 1:
                prev_word = raw_tokens[i - 1][0]
                if prev_word in {"想当", "当", "做", "成为", "作为", "当上", "做了", "成了", "当了"}:
                    entity_type = "O"
                # Handle split "want to be" cases
                elif prev_word in {"当", "做"} and i >= 2:
                    prev_prev_word = raw_tokens[i - 2][0]
                    if prev_prev_word in {"想", "要", "会", "能", "得"}:
                        entity_type = "O"
                # 2.2 "is a" + title word is predicate, not independent person
                # e.g. "doctor" in "Xiaoming is a doctor" should not be standalone person
                elif prev_word in {"个", "一个", "名", "位", "一名", "一位"} and i >= 2:
                    prev_prev_word = raw_tokens[i - 2][0]
                    if prev_prev_word == "是":
                        entity_type = "O"
                elif prev_word == "是":
                    # Direct "is doctor" case
                    entity_type = "O"

            tokens.append(Token(word=word, pos=flag, entity_type=entity_type, start=start, end=end))
            cursor = end
            i += 1

        return tokens

    def _get_entity_type(self, word: str, pos: str) -> str:
        """Determine entity type (fine-grained classification)"""

        # 0. Colloquial kinship: my-dad/my-mom... -> person title (can be antecedent)
        if len(word) >= 2 and word.startswith("我") and word[1:] in self._KINSHIP_TITLES:
            return "PER_TITLE"

        # 0.1 Reduplicated nicknames (jieba often misses nr tag) -> person name
        if len(word) == 2 and word[0] == word[1] and "\u4e00" <= word[0] <= "\u9fff":
            return "PER_NAME"

        # 0.2 Two-char "surname+given name" weak rule (jieba sometimes tags names as n)
        # Only enabled when first char is common surname and POS looks like noun
        # Further restricted: only match surname+numeric-name, avoid false positives
        if len(word) == 2 and word[0] in self.SURNAMES and word[1] in self._NUM_NAME_CHARS and pos in {"n", "nr", "nz"}:
            return "PER_NAME"

        # 0.3 English word recognition (pos='eng')
        # Determine type based on context and word features
        if pos == "eng":
            # Technical terms -> object
            tech_terms = {
                "API",
                "SDK",
                "IDE",
                "UI",
                "UX",
                "URL",
                "HTTP",
                "HTTPS",
                "HTML",
                "CSS",
                "JSON",
                "XML",
                "CPU",
                "GPU",
                "RAM",
                "ROM",
                "SSD",
                "HDD",
                "USB",
                "HDMI",
                "WiFi",
                "Bluetooth",
                "Python",
                "Java",
                "JavaScript",
                "TypeScript",
                "React",
                "Vue",
                "Angular",
                "iOS",
                "macOS",
                "Linux",
                "Unix",
                "Windows",
                "MySQL",
                "Redis",
                "MongoDB",
                "PostgreSQL",
                "Docker",
                "Kubernetes",
            }
            if word in tech_terms or word.upper() == word:  # all-caps usually are abbreviations/terms
                return "OBJ"

            # Product/brand terms -> object
            product_words = {
                "iPhone",
                "iPad",
                "MacBook",
                "iMac",
                "AirPods",
                "Apple Watch",
                "Windows",
                "Android",
                "Linux",
                "Chrome",
                "Firefox",
                "Safari",
                "Tesla",
                "BMW",
                "Benz",
                "Mercedes",
                "Toyota",
                "Honda",
                "Nike",
                "Adidas",
                "Puma",
                "Gucci",
                "LV",
                "Chanel",
                "Starbucks",
                "KFC",
                "McDonald",
                "Subway",
            }
            if word in product_words:
                return "OBJ"

            # Location terms -> location
            location_words = {
                "New York",
                "Los Angeles",
                "San Francisco",
                "Washington",
                "Chicago",
                "London",
                "Paris",
                "Tokyo",
                "Seoul",
                "Singapore",
                "Beijing",
                "Shanghai",
                "Guangzhou",
                "Shenzhen",
                "Sydney",
                "Melbourne",
                "Toronto",
                "Vancouver",
                "Berlin",
                "Munich",
                "Rome",
                "Milan",
                "Barcelona",
                "Madrid",
            }
            if word in location_words:
                return "LOC_NAME"

            # Company/org terms -> object (can be referred by "it")
            company_words = {
                "Google",
                "Apple",
                "Microsoft",
                "Facebook",
                "Twitter",
                "Amazon",
                "Tesla",
                "Netflix",
                "Uber",
                "Airbnb",
                "SpaceX",
                "IBM",
                "Intel",
                "AMD",
                "Nvidia",
                "Oracle",
                "SAP",
            }
            if word in company_words:
                return "OBJ"  # companies as subjects can be referred by "it"
            # Store-ending names -> location
            store_patterns = ("Store", "Shop", "Mall", "Center", "Centre", "Station")
            if word.endswith(store_patterns):
                return "LOC_PLACE"

            # English person name detection
            if word and word[0].isupper() and len(word) >= 2:
                # Exclude already-processed words
                all_non_person = product_words | location_words | company_words
                if word not in all_non_person:
                    # Assume capitalized English words are person names
                    return "PER_NAME"
            return "O"

        # 0.4 Organization names (pos='nt') -> location
        if pos == "nt":
            return "LOC_PLACE"

        # 0.5 Proper nouns (pos='nz') -> possibly company/brand/org
        if pos == "nz":
            # Well-known tech companies
            tech_companies = {
                "腾讯",
                "阿里",
                "阿里巴巴",
                "百度",
                "字节",
                "字节跳动",
                "京东",
                "美团",
                "华为",
                "小米",
                "网易",
                "新浪",
                "搜狐",
                "滴滴",
                "拼多多",
                "OPPO",
                "vivo",
            }
            if word in tech_companies:
                return "LOC_PLACE"
            # Other proper nouns default to object/brand
            return "OBJ"

        # Exclude misidentifications
        if word in self.NOT_LOCATION and pos in ["ns", "nsf"]:
            return "O"
        if word in self.NOT_PERSON and pos in ["nr", "nrt", "nrfg"]:
            return "O"

        # 1. Surname+title pattern -> person title
        if len(word) >= 2:
            first_char = word[0]
            rest = word[1:]
            if first_char in self.SURNAMES and rest in self.SURNAME_TITLES:
                return "PER_TITLE"

        # 2. Compound surname detection
        if word in self.COMPOUND_SURNAMES:
            return "PER_NAME"  # compound surname appearing alone treated as part of person name

        # 3. Foreign name dictionary
        if word in self.FOREIGN_NAMES:
            return "PER_NAME"

        # 4. Common nickname dictionary
        if word in self.COMMON_NAMES:
            return "PER_NAME"

        # 4. Person title dictionary
        if word in self.PERSON_TITLES:
            return "PER_TITLE"

        # 5. Famous landmarks (as location)
        if word in self.FAMOUS_PLACES:
            return "LOC_NAME"

        # 6. Place word dictionary
        if word in self.PLACE_WORDS:
            return "LOC_PLACE"

        # 6. Object word dictionary
        if word in self.OBJECT_WORDS:
            return "OBJ"

        # 6.1 Abstract object suffix (treat whole compound as OBJ)
        if len(word) >= 3:
            for suf in self.ABSTRACT_SUFFIXES:
                if word.endswith(suf):
                    return "OBJ"

        # 7. Time word dictionary
        if word in self.TIME_WORDS:
            return "TIME"

        # 7.1 Numeric year recognition: 2023nian/2024/1990nian etc.
        if re.match(r"^\d{4}年?$", word):
            return "TIME"

        # 7.2 Chinese month recognition
        if re.match(r"^[一二三四五六七八九十]+月(份)?$", word):
            return "TIME"

        # 7.3 Classifier structure (pos='mq') may be month
        if pos == "mq" and ("月" in word or "年" in word or "日" in word):
            return "TIME"

        # 8. jieba person name POS
        if pos in ["nr", "nrt", "nrfg"]:
            return "PER_NAME"

        # 8. jieba location name POS
        if pos in ["ns", "nsf"]:
            return "LOC_NAME"

        # 9. jieba place POS
        if pos == "s":
            return "LOC_PLACE"

        return "O"

    def analyze(self, text: str) -> Dict:
        """Analyze text, return results grouped by type (backward-compatible interface)"""
        tokens = self.tokenize(text)

        result = {
            "text": text,
            "person_names": [],
            "person_titles": [],
            "location_names": [],
            "location_places": [],
            "objects": [],
            "times": [],
        }

        for t in tokens:
            if t.entity_type == "PER_NAME":
                result["person_names"].append(t.word)
            elif t.entity_type == "PER_TITLE":
                result["person_titles"].append(t.word)
            elif t.entity_type == "LOC_NAME":
                result["location_names"].append(t.word)
            elif t.entity_type == "LOC_PLACE":
                result["location_places"].append(t.word)
            elif t.entity_type == "OBJ":
                result["objects"].append(t.word)
            elif t.entity_type == "TIME":
                result["times"].append(t.word)

        return result

    def analyze_mentions(self, text: str, sentence_id: int = 0) -> List[Mention]:
        """Analyze text, return Mention list in occurrence order (with position info)

        Differences from analyze():
        1. Preserves entity occurrence order in original text (not grouped by type)
        2. Includes precise character position info (start, end)
        3. Supports specifying sentence ID

        Args:
            text: input text
            sentence_id: sentence ID (for multi-sentence scenarios)

        Returns:
            List[Mention]: entity mentions in occurrence order
        """
        tokens = self.tokenize(text)
        mentions = []

        entity_types = {"PER_NAME", "PER_TITLE", "LOC_NAME", "LOC_PLACE", "OBJ", "TIME"}

        for token in tokens:
            if token.entity_type in entity_types:
                mentions.append(
                    Mention(
                        surface=token.word,
                        type=token.entity_type,
                        start=token.start,
                        end=token.end,
                        sentence_id=sentence_id,
                    )
                )

        return mentions


def demo():
    """Demo"""
    tokenizer = ChineseTokenizer()

    tests = [
        "小明在学校读书",
        "刘德华去北京开演唱会",
        "妈妈在超市买苹果",
        "医生在医院看病人",
        "姑娘在公园散步",
        "老师在教室教学生",
        "张三去上海出差",
        "爸爸妈妈带孩子去公园",
        "警察在派出所办案",
        "快递员送快递",
        "大卫去机场",
        "看电视",
        "喝咖啡",
    ]

    print("=" * 70)
    print("Fine-grained Classification v2: Fix jieba segmentation issues")
    print("=" * 70)

    for text in tests:
        result = tokenizer.analyze(text)
        parts = []

        if result["person_names"]:
            parts.append(f"PER_NAME:{result['person_names']}")
        if result["person_titles"]:
            parts.append(f"PER_TITLE:{result['person_titles']}")
        if result["location_names"]:
            parts.append(f"LOC_NAME:{result['location_names']}")
        if result["location_places"]:
            parts.append(f"LOC_PLACE:{result['location_places']}")
        if result["objects"]:
            parts.append(f"OBJ:{result['objects']}")

        print(f"\n{text}")
        print(f"  -> {', '.join(parts) if parts else 'None'}")


if __name__ == "__main__":
    demo()
