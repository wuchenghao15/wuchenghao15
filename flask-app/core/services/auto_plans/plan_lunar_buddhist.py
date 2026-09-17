# -*- coding: utf-8 -*-
"""农历佛教道教事件库 - 完整版
────────────────────────
覆盖:
  - 公历节日 (13)
  - 农历传统节日 (12)
  - 佛教: 汉传 (8) + 藏传 (4) + 南传 (3) + 各宗派祖师 (12)
  - 道教: 三清 (3) + 四御 (4) + 文昌/武圣/妈祖/关圣 (4) + 全真/正一/净明祖师 (6)
  - 儒教: 孔子圣诞 (1)
  - 民俗: 送神日/迎神日/祭灶 (3)
  - 合计 ~76 条

每条 event 含 i18n_key, 模板层用 {{ t(event.i18n_key, default=event.event) }} 渲染.
"""

LUNAR_BUDDHIST_EVENTS = [

    # ═══════════════════════════════════════════
    # 公历节日 (13)
    # ═══════════════════════════════════════════
    {'month': 1,   'day': 1,   'event': '元旦',      'i18n_key': 'event.new_year',           'type': '公历节日'},
    {'month': 2,   'day': 14,  'event': '情人节',    'i18n_key': 'event.valentines',         'type': '公历节日'},
    {'month': 3,   'day': 8,   'event': '妇女节',    'i18n_key': 'event.womens_day',         'type': '公历节日'},
    {'month': 3,   'day': 12,  'event': '植树节',    'i18n_key': 'event. Arbor_day',         'type': '公历节日'},
    {'month': 4,   'day': 5,   'event': '清明节',    'i18n_key': 'event.qingming',           'type': '公历节日/农历节日', 'note': '春分后15日'},
    {'month': 5,   'day': 1,   'event': '劳动节',    'i18n_key': 'event.labor_day',           'type': '公历节日'},
    {'month': 5,   'day': 4,   'event': '青年节',    'i18n_key': 'event.youth_day',           'type': '公历节日'},
    {'month': 6,   'day': 1,   'event': '儿童节',    'i18n_key': 'event.childrens_day',       'type': '公历节日'},
    {'month': 7,   'day': 1,   'event': '建党节',    'i18n_key': 'event.cpc_found',           'type': '公历节日'},
    {'month': 8,   'day': 1,   'event': '建军节',    'i18n_key': 'event.army_day',            'type': '公历节日'},
    {'month': 9,   'day': 10,  'event': '教师节',    'i18n_key': 'event.teachers_day',        'type': '公历节日'},
    {'month': 10,  'day': 1,   'event': '国庆节',    'i18n_key': 'event.national_day',        'type': '公历节日'},
    {'month': 12,  'day': 25,  'event': '圣诞节',    'i18n_key': 'event.christmas',           'type': '公历节日'},

    # ═══════════════════════════════════════════
    # 农历传统节日 (12)
    # ═══════════════════════════════════════════
    {'month': 2,   'day': -1,  'event': '除夕',      'i18n_key': 'lunar.chuxi',              'type': '农历节日', 'note': '腊月最后一天'},
    {'month': 1,   'day': -1,  'event': '春节',      'i18n_key': 'lunar.spring',             'type': '农历节日', 'note': '正月初一'},
    {'month': 1,   'day': 15,  'event': '元宵节',    'i18n_key': 'lunar.yuanxiao',           'type': '农历节日'},
    {'month': 5,   'day': -1,  'event': '端午节',    'i18n_key': 'lunar.duanwu',             'type': '农历节日', 'note': '五月初五'},
    {'month': 7,   'day': 7,   'event': '七夕节',    'i18n_key': 'lunar.qixi',               'type': '农历节日', 'note': '七月初七'},
    {'month': 7,   'day': 15,  'event': '中元节',    'i18n_key': 'lunar.zhongyuan',           'type': '农历节日', 'note': '七月十五'},
    {'month': 8,   'day': 15,  'event': '中秋节',    'i18n_key': 'lunar.zhongqiu',           'type': '农历节日', 'note': '八月十五'},
    {'month': 10,  'day': -1,  'event': '重阳节',    'i18n_key': 'lunar.chongyang',           'type': '农历节日', 'note': '九月初九'},
    {'month': 11,  'day': -1,  'event': '寒衣节',    'i18n_key': 'lunar.hanyi',               'type': '农历节日', 'note': '十月初一'},
    {'month': 12,  'day': -1,  'event': '冬至',      'i18n_key': 'lunar.dongzhi',             'type': '农历/节气', 'note': '农历十一月中'},
    {'month': 12,  'day': -1,  'event': '腊八节',    'i18n_key': 'lunar.laba',                'type': '农历节日', 'note': '腊月初八'},
    {'month': 12,  'day': -1,  'event': '小年',      'i18n_key': 'lunar.xiaonian',            'type': '农历节日', 'note': '腊月廿三'},

    # ═══════════════════════════════════════════
    # 佛教 · 汉传 (8)
    # ═══════════════════════════════════════════
    {'month': 2,   'day': 8,   'event': '释迦牟尼佛出家日', 'i18n_key': 'buddha.siddhartha_renunciation', 'type': '佛教·汉传', 'note': '二月初八'},
    {'month': 2,   'day': 15,  'event': '释迦牟尼佛涅槃日', 'i18n_key': 'buddha.siddhartha_nirvana',       'type': '佛教·汉传', 'note': '二月十五'},
    {'month': 4,   'day': 4,   'event': '文殊菩萨圣诞',     'i18n_key': 'buddha.manjusri_birthday',        'type': '佛教·汉传', 'note': '四月初四'},
    {'month': 4,   'day': -1,  'event': '浴佛节',           'i18n_key': 'buddha.bathing',                   'type': '佛教·汉传', 'note': '四月初八 · 释迦牟尼圣诞'},
    {'month': 6,   'day': 19,  'event': '观世音菩萨成道日', 'i18n_key': 'buddha.guanyin_awakening',         'type': '佛教·汉传', 'note': '六月十九'},
    {'month': 7,   'day': -1,  'event': '盂兰盆节',         'i18n_key': 'buddha.ullambana',                 'type': '佛教·汉传', 'note': '七月十五 · 僧众自恣日'},
    {'month': 8,   'day': 22,  'event': '地藏菩萨圣诞',     'i18n_key': 'buddha.ksitigarbha_birthday',      'type': '佛教·汉传', 'note': '八月廿二'},
    {'month': 12,  'day': -1,  'event': '释迦牟尼佛成道日', 'i18n_key': 'buddha.siddhartha_enlightenment',  'type': '佛教·汉传', 'note': '腊月初八'},

    # ═══════════════════════════════════════════
    # 佛教 · 观音三圣诞 (3)
    # ═══════════════════════════════════════════
    {'month': 2,   'day': 19,  'event': '观音菩萨圣诞',     'i18n_key': 'buddha.guanyin_birthday',          'type': '佛教·汉传', 'note': '二月十九'},
    {'month': 6,   'day': 19,  'event': '观音菩萨成道日',   'i18n_key': 'buddha.guanyin_awakening2',        'type': '佛教·汉传', 'note': '六月十九'},
    {'month': 9,   'day': 19,  'event': '观音菩萨出家日',   'i18n_key': 'buddha.guanyin_renunciation',      'type': '佛教·汉传', 'note': '九月十九'},

    # ═══════════════════════════════════════════
    # 佛教 · 其他菩萨 (5)
    # ═══════════════════════════════════════════
    {'month': 1,   'day': 1,   'event': '弥勒菩萨圣诞',     'i18n_key': 'buddha.maitreya_birthday',         'type': '佛教·汉传', 'note': '正月初一'},
    {'month': 5,   'day': 13,  'event': '伽蓝菩萨圣诞',     'i18n_key': 'buddha.garland_birthday',          'type': '佛教·汉传', 'note': '五月十三'},
    {'month': 7,   'day': 13,  'event': '大势至菩萨圣诞',   'i18n_key': 'buddha.mahasthamaprapta_birthday', 'type': '佛教·汉传', 'note': '七月十三'},
    {'month': 11,  'day': 17,  'event': '阿弥陀佛圣诞',     'i18n_key': 'buddha.amitabha_birthday',         'type': '佛教·汉传', 'note': '十一月十七'},
    {'month': 9,   'day': 30,  'event': '药师佛圣诞',       'i18n_key': 'buddha.bhaisajyaguru_birthday',    'type': '佛教·汉传', 'note': '九月三十'},

    # ═══════════════════════════════════════════
    # 佛教 · 藏传 (4)
    # ═══════════════════════════════════════════
    {'month': 4,   'day': 15,  'event': '萨嘎月/佛诞日',   'i18n_key': 'buddha.saga_dawa',                 'type': '佛教·藏传', 'note': '藏历四月十五'},
    {'month': 6,   'day': 4,   'event': '莲花生大士圣诞', 'i18n_key': 'buddha.padmasambhava_birthday',    'type': '佛教·藏传', 'note': '藏历六月初四'},
    {'month': 9,   'day': 22,  'event': '米拉日巴尊者日', 'i18n_key': 'buddha.milarepa_day',              'type': '佛教·藏传', 'note': '藏历九月廿二'},
    {'month': 1,   'day': 25,  'event': '嘎珠五供会',     'i18n_key': 'buddha.gadeng_ngakchod',           'type': '佛教·藏传', 'note': '藏历正月廿五'},

    # ═══════════════════════════════════════════
    # 佛教 · 南传 (3)
    # ═══════════════════════════════════════════
    {'month': 5,   'day': -1,  'event': '卫塞节',         'i18n_key': 'buddha.vesak',                     'type': '佛教·南传', 'note': '公历五月月圆日'},
    {'month': 7,   'day': -1,  'event': '阿舍罗月/安居始', 'i18n_key': 'buddha.asalha',                    'type': '佛教·南传', 'note': '公历七月月圆日'},
    {'month': 10,  'day': -1,  'event': '阿耨月/安居结', 'i18n_key': 'buddha.katina',                    'type': '佛教·南传', 'note': '公历十月月圆日'},

    # ═══════════════════════════════════════════
    # 佛教 · 各宗派祖师 (12)
    # ═══════════════════════════════════════════
    {'month': 1,   'day': 11,  'event': '禅宗·赵州从谂禅师忌日', 'i18n_key': 'chan.zhaozhou_anni',            'type': '佛教·禅宗'},
    {'month': 3,   'day': 8,   'event': '禅宗·六祖慧能大师圣诞', 'i18n_key': 'chan.huineng_birthday',         'type': '佛教·禅宗', 'note': '二月初九'},
    {'month': 10,  'day': 15,  'event': '禅宗·达摩祖师圣诞',   'i18n_key': 'chan.bodhidharma_birthday',     'type': '佛教·禅宗', 'note': '十月初五'},
    {'month': 8,   'day': 23,  'event': '净土宗·善导大师忌日', 'i18n_key': 'pureland.shandao_anni',          'type': '佛教·净土宗', 'note': '三月十四'},
    {'month': 11,  'day': -1,  'event': '净土宗·莲池大师诞辰', 'i18n_key': 'pureland.lianchi_birthday',      'type': '佛教·净土宗', 'note': '六月初八'},
    {'month': 5,   'day': -1,  'event': '天台宗·智顗大师忌日', 'i18n_key': 'tiantai.zhiyi_anni',              'type': '佛教·天台宗', 'note': '五月廿四'},
    {'month': 8,   'day': -1,  'event': '华严宗·杜顺大师忌日', 'i18n_key': 'huayan.dushun_anni',              'type': '佛教·华严宗', 'note': '十一月廿五'},
    {'month': 9,   'day': -1,  'event': '密宗·善无畏三藏忌日', 'i18n_key': 'esoteric.subhakarasimha_anni',    'type': '佛教·密宗', 'note': '十一月初七'},
    {'month': 6,   'day': -1,  'event': '密宗·不空三藏忌日',   'i18n_key': 'esoteric.amoghavajra_anni',       'type': '佛教·密宗', 'note': '六月十五'},
    {'month': 12,  'day': -1,  'event': '三论宗·吉藏大师忌日', 'i18n_key': 'sanzong.jizang_anni',             'type': '佛教·三论宗', 'note': '六月初十'},
    {'month': 11,  'day': -1,  'event': '律宗·道宣律师忌日',   'i18n_key': 'vinaya.daoxuan_anni',             'type': '佛教·律宗', 'note': '十月初三'},
    {'month': 4,   'day': -1,  'event': '唯识宗·玄奘大师忌日', 'i18n_key': 'yogacara.xuanzang_anni',          'type': '佛教·唯识宗', 'note': '二月初五'},

    # ═══════════════════════════════════════════
    # 道教 · 三清 (3)
    # ═══════════════════════════════════════════
    {'month': 1,   'day': -1,  'event': '元始天尊圣诞',     'i18n_key': 'dao.yuanshi_tianzun',         'type': '道教·三清', 'note': '正月初一'},
    {'month': 8,   'day': -1,  'event': '灵宝天尊圣诞',     'i18n_key': 'dao.lingbao_tianzun',         'type': '道教·三清', 'note': '七月初八'},
    {'month': 11,  'day': -1,  'event': '道德天尊圣诞',     'i18n_key': 'dao.daode_tianzun',           'type': '道教·三清', 'note': '二月十五 · 太上老君'},

    # ═══════════════════════════════════════════
    # 道教 · 四御 (4)
    # ═══════════════════════════════════════════
    {'month': 1,   'day': -1,  'event': '玉皇大帝圣诞',     'i18n_key': 'dao.yuhuang_birthday',        'type': '道教·四御', 'note': '正月初九'},
    {'month': 2,   'day': -1,  'event': '紫微大帝圣诞',     'i18n_key': 'dao.ziwei_birthday',          'type': '道教·四御', 'note': '四月十八'},
    {'month': 2,   'day': -1,  'event': '南极长生大帝圣诞', 'i18n_key': 'dao.nanji_birthday',          'type': '道教·四御', 'note': '五月初一'},
    {'month': 10,  'day': -1,  'event': '后土娘娘圣诞',     'i18n_key': 'dao.houtu_birthday',          'type': '道教·四御', 'note': '十月十八'},

    # ═══════════════════════════════════════════
    # 道教 · 四圣 (4)
    # ═══════════════════════════════════════════
    {'month': 2,   'day': 15,  'event': '正一·张天师圣诞', 'i18n_key': 'dao.zhangdaoling_birthday',   'type': '道教·正一', 'note': '二月十五'},
    {'month': 5,   'day': -1,  'event': '关圣帝君圣诞',     'i18n_key': 'dao.guandi_birthday',         'type': '道教·武圣', 'note': '五月十三'},
    {'month': 2,   'day': -1,  'event': '文昌帝君圣诞',     'i18n_key': 'dao.wenchang_birthday',       'type': '道教·文圣', 'note': '二月初三'},
    {'month': 3,   'day': -1,  'event': '妈祖圣诞',         'i18n_key': 'dao.mazu_birthday',           'type': '道教·民间信仰', 'note': '三月廿三'},

    # ═══════════════════════════════════════════
    # 道教 · 各方诸神 (4)
    # ═══════════════════════════════════════════
    {'month': 3,   'day': -1,  'event': '真武大帝圣诞',     'i18n_key': 'dao.zhenwu_birthday',         'type': '道教', 'note': '三月初三'},
    {'month': 6,   'day': -1,  'event': '南斗星君圣诞',     'i18n_key': 'dao.nandou_birthday',         'type': '道教', 'note': '六月初一'},
    {'month': 7,   'day': -1,  'event': '北斗七星君圣诞',   'i18n_key': 'dao.beidou_birthday',         'type': '道教', 'note': '七月初七'},
    {'month': 9,   'day': -1,  'event': '太乙救苦天尊圣诞', 'i18n_key': 'dao.taiyi_birthday',          'type': '道教', 'note': '九月十一'},

    # ═══════════════════════════════════════════
    # 道教 · 各宗派祖师 (6)
    # ═══════════════════════════════════════════
    {'month': 6,   'day': -1,  'event': '全真·王重阳祖师圣诞', 'i18n_key': 'quanzhen.wangchongyang',     'type': '道教·全真', 'note': '六月初一'},
    {'month': 6,   'day': -1,  'event': '全真·丘处机祖师圣诞', 'i18n_key': 'quanzhen.qiuchuji',         'type': '道教·全真', 'note': '正月十九'},
    {'month': 11,  'day': -1,  'event': '全真·马丹阳祖师圣诞', 'i18n_key': 'quanzhen.madanyang',        'type': '道教·全真', 'note': '五月廿二'},
    {'month': 11,  'day': -1,  'event': '全真·张三丰祖师圣诞', 'i18n_key': 'quanzhen.zhangsanfeng',     'type': '道教·全真', 'note': '四月初九'},
    {'month': 2,   'day': -1,  'event': '净明·许逊祖师圣诞',   'i18n_key': 'jingming.xuxun',             'type': '道教·净明', 'note': '正月廿八'},
    {'month': 2,   'day': -1,  'event': '正一·张继先天师忌日', 'i18n_key': 'zhengyi.zhangjixian',       'type': '道教·正一', 'note': '十二月廿二'},

    # ═══════════════════════════════════════════
    # 儒教 + 民俗 (4)
    # ═══════════════════════════════════════════
    {'month': 8,   'day': -1,  'event': '孔子圣诞',         'i18n_key': 'rujia.confucius_birthday',    'type': '儒教', 'note': '八月廿七'},
    {'month': 12,  'day': -1,  'event': '祭灶日',           'i18n_key': 'folk.zaoshen',                'type': '民俗', 'note': '腊月廿三(北)/廿四(南)'},
    {'month': 12,  'day': -1,  'event': '送神日',           'i18n_key': 'folk.songshen',               'type': '民俗', 'note': '腊月廿四'},
    {'month': 1,   'day': -1,  'event': '迎神日',           'i18n_key': 'folk.yingshen',               'type': '民俗', 'note': '正月初四'},
]


# ============================================================================
#  LunarBuddhistPlan  —  兼容类 (__init__.py import 用)
# ============================================================================
class LunarBuddhistPlan:
    """农历佛教道教事件更新计划 - 自动维护农历和佛教事件。
    简化版: 事件源 = LUNAR_BUDDHIST_EVENTS 常量, 供 context_processor 直接引用.
    """

    name = "lunar_buddhist"
    description = "农历佛教道教事件自动维护 (76+ 条覆盖佛/道/儒/民俗/公历)"
    interval_sec = 3600 * 6  # 6 小时跑一次

    def __init__(self):
        self.events = LUNAR_BUDDHIST_EVENTS

    def run(self):
        """更新事件库 (当前实现: 无需更新, 常量已包含所有事件)."""
        return {
            'success': True,
            'total_events': len(LUNAR_BUDDHIST_EVENTS),
            'note': 'LUNAR_BUDDHIST_EVENTS 为静态常量, 无需运行时更新',
        }

    def get_upcoming(self, days: int = 30) -> list:
        """获取未来 N 天内的事件 (简化: 按 month/day 粗匹配)."""
        import datetime as _dt
        from .lunar_calendar_service import lunar_calendar_service  # type: ignore
        tday = _dt.date.today()
        result = []
        for off in range(days + 1):
            tgt = tday + _dt.timedelta(days=off)
            _, lm, ld, _ = lunar_calendar_service._solar_to_lunar(tgt)
            for ev in LUNAR_BUDDHIST_EVENTS:
                em, ed = ev.get('month', 0), ev.get('day', 0)
                if em == lm and ed > 0 and ed == ld:
                    result.append({
                        'offset': off,
                        'date': tgt.isoformat(),
                        'event': ev.get('event', ''),
                        'type': ev.get('type', ''),
                        'i18n_key': ev.get('i18n_key', ''),
                    })
        return result
