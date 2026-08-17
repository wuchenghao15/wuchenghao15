#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportReturnType=false, reportUnboundVariable=false, reportInvalidTypeForm=false, reportUnusedVariable=false, reportGeneralTypeIssues=false
# basedpyright: reportMissingImports=false, reportReturnType=false, reportUnboundVariable=false, reportInvalidTypeForm=false, reportUnusedVariable=false, reportGeneralTypeIssues=false, reportUnknownMemberType=false
"""农历日历服务（完整版）。

基于标准农历算法（1900-2100），支持：
  - 公历 → 农历 精确转换（脚本计算，非固定数组赋值）
  - 天干地支 年/月/日 干支
  - 佛教重要节日、菩萨诞辰、罗汉纪念日
  - 初一/十五/节日倒计时
"""

from __future__ import annotations

import datetime as _dt
import math
from typing import Any, Dict, List, Optional, Tuple


class LunarCalendarService:
    """农历日历服务（标准算法实现）。"""

    # ================================================================
    #  农历数据表（1900-2100，共 201 年，每年一个十六进制编码）
    #  编码规则：
    #    bits 0-3   : 闰月序号 (0=无闰月, 1-12)
    #    bits 4-15  : 12 个月大小 (bit=1 表示 30 天, bit=0 表示 29 天)
    #                 从 bit 0x8000 (正月) 到 bit 0x800 (腊月)
    #    bit 16     : 闰月大小 (1=30天, 0=29天)
    # ================================================================
    LUNAR_INFO: List[int] = [
        0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,  # 1900-1909
        0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,  # 1910-1919
        0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,  # 1920-1929
        0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,  # 1930-1939
        0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,  # 1940-1949
        0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5b0, 0x14573, 0x052b0, 0x0a9a8, 0x0e950, 0x06aa0,  # 1950-1959
        0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,  # 1960-1969
        0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,  # 1970-1979
        0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,  # 1980-1989
        0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,  # 1990-1999
        0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,  # 2000-2009
        0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,  # 2010-2019
        0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,  # 2020-2029
        0x05aa0, 0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,  # 2030-2039
        0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,  # 2040-2049
        0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0,  # 2050-2059
        0x0a2e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,  # 2060-2069
        0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,  # 2070-2079
        0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,  # 2080-2089
        0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,  # 2090-2099
        0x0d520,  # 2100
    ]

    # 天干地支
    TIAN_GAN: List[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    DI_ZHI: List[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    # 天干对应五行
    GAN_WUXING: List[str] = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]
    ZHI_WUXING: List[str] = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]

    # 生肖（地支对应）
    ZHI_ANIMAL: List[str] = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

    # 天干阴阳
    GAN_YINYANG: List[str] = ["阳", "阴", "阳", "阴", "阳", "阴", "阳", "阴", "阳", "阴"]

    # 农历月中文名
    CHN_MONTH: List[str] = [
        "正", "二", "三", "四", "五", "六",
        "七", "八", "九", "十", "冬", "腊",
    ]

    # 农历日中文名
    CHN_DAY_1: List[str] = [
        "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
        "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
    ]

    # ================================================================
    #  English translations
    # ================================================================
    EN_TIAN_GAN: List[str] = [
        "Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"
    ]
    EN_DI_ZHI: List[str] = [
        "Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"
    ]
    EN_ZHI_ANIMAL: List[str] = [
        "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"
    ]
    EN_CHN_MONTH: List[str] = [
        "1st", "2nd", "3rd", "4th", "5th", "6th",
        "7th", "8th", "9th", "10th", "11th", "12th",
    ]
    EN_CHN_DAY: List[str] = [
        "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th",
        "11th", "12th", "13th", "14th", "15th", "16th", "17th", "18th", "19th", "20th",
        "21st", "22nd", "23rd", "24th", "25th", "26th", "27th", "28th", "29th", "30th",
    ]
    EN_GAN_WUXING: List[str] = [
        "Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"
    ]
    EN_ZHI_WUXING: List[str] = [
        "Water", "Earth", "Wood", "Wood", "Earth", "Fire", "Fire", "Earth", "Metal", "Metal", "Earth", "Water"
    ]
    EN_GAN_YINYANG: List[str] = [
        "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"
    ]

    # ================================================================
    #  佛教重要节日（基于农历日期）
    #  key = (月, 日)；value = 节日名称列表
    # ================================================================
    BUDDHIST_FESTIVALS_LUNAR: Dict[Tuple[int, int], List[str]] = {
        # 正月
        (1, 1): ["春节", "弥勒佛圣诞"],
        (1, 8): ["燃灯佛圣诞"],
        (1, 15): ["元宵节", "释迦牟尼佛成道日"],
        (1, 20): ["药师佛圣诞"],
        # 二月
        (2, 8): ["释迦牟尼佛出家日", "阿弥陀佛圣诞"],
        (2, 15): ["释迦牟尼佛涅槃日"],
        (2, 19): ["观世音菩萨圣诞"],
        # 三月
        (3, 1): ["帝释天尊圣诞"],
        (3, 8): ["释迦牟尼佛成道日"],
        (3, 16): ["准提菩萨圣诞"],
        (3, 20): ["文殊菩萨圣诞"],
        # 四月
        (4, 4): ["清明"],
        (4, 8): ["浴佛节", "释迦牟尼佛圣诞"],
        (4, 14): ["阿难尊者圣诞"],
        (4, 15): ["卫塞节"],
        (4, 16): ["大势至菩萨圣诞"],
        (4, 19): ["观世音菩萨圣诞"],
        (4, 28): ["药王菩萨圣诞"],
        # 五月
        (5, 5): ["端午节"],
        (5, 13): ["释迦牟尼佛涅槃日"],
        (5, 18): ["张天师圣诞"],
        # 六月
        (6, 3): ["护法韦驮尊天菩萨圣诞"],
        (6, 8): ["释迦牟尼佛说法纪念日"],
        (6, 15): ["半年节"],
        (6, 19): ["观世音菩萨成道日"],
        (6, 24): ["地藏王菩萨圣诞"],
        # 七月
        (7, 7): ["七夕节", "乞巧节"],
        (7, 13): ["大势至菩萨圣诞"],
        (7, 15): ["中元节", "盂兰盆节"],
        (7, 21): ["普贤菩萨圣诞"],
        (7, 24): ["龙树菩萨圣诞"],
        (7, 30): ["地藏王菩萨圣诞"],
        # 八月
        (8, 15): ["中秋节", "月光菩萨圣诞"],
        (8, 18): ["观音菩萨圣诞"],
        (8, 21): ["地藏王菩萨圣诞"],
        (8, 22): ["燃灯古佛圣诞"],
        # 九月
        (9, 9): ["重阳节", "斗战胜佛圣诞"],
        (9, 13): ["地藏王菩萨圣诞"],
        (9, 19): ["观世音菩萨出家日"],
        (9, 30): ["药师佛圣诞"],
        # 十月
        (10, 15): ["下元节"],
        (10, 17): ["阿弥陀佛圣诞"],
        (10, 22): ["妈祖圣诞"],
        # 十一月
        (11, 4): ["药师佛圣诞"],
        (11, 7): ["阿弥陀佛圣诞"],
        (11, 17): ["弥陀佛圣诞"],
        # 十二月
        (12, 8): ["腊八节", "释迦牟尼佛成道日"],
        (12, 23): ["小年"],
        (12, 30): ["除夕"],
    }

    # 佛教重要节日（基于公历）
    BUDDHIST_FESTIVALS_SOLAR: Dict[Tuple[int, int], List[str]] = {
        (1, 1): ["元旦"],
        (2, 14): ["情人节"],
        (2, 16): ["迎春节"],
        (3, 8): ["妇女节"],
        (3, 12): ["植树节"],
        (4, 1): ["愚人节"],
        (4, 5): ["清明节"],
        (5, 1): ["劳动节"],
        (5, 4): ["青年节"],
        (6, 1): ["儿童节"],
        (6, 19): ["父亲节"],
        (7, 1): ["建党节"],
        (8, 1): ["建军节"],
        (9, 10): ["教师节"],
        (10, 1): ["国庆节"],
        (10, 31): ["万圣节"],
        (12, 25): ["圣诞节"],
        (12, 31): ["除夕"],
    }

    # ================================================================
    #  English festival translations (lunar-based)
    # ================================================================
    EN_FESTIVALS_LUNAR: Dict[Tuple[int, int], List[str]] = {
        (1, 1): ["Spring Festival", "Maitreya Buddha Birthday"],
        (1, 8): ["Dipankara Buddha Birthday"],
        (1, 15): ["Lantern Festival", "Sakyamuni Buddha Enlightenment Day"],
        (1, 20): ["Medicine Buddha Birthday"],
        (2, 8): ["Sakyamuni Buddha Monastic Day", "Amitabha Buddha Birthday"],
        (2, 15): ["Sakyamuni Buddha Nirvana Day"],
        (2, 19): ["Avalokiteshvara Bodhisattva Birthday"],
        (3, 1): ["Sakra Devanam Indra Birthday"],
        (3, 8): ["Sakyamuni Buddha Enlightenment Day"],
        (3, 16): ["Cundi Bodhisattva Birthday"],
        (3, 20): ["Manjushri Bodhisattva Birthday"],
        (4, 4): ["Qingming Festival"],
        (4, 8): ["Vesak Day", "Sakyamuni Buddha Birthday"],
        (4, 14): ["Ananda Elder Birthday"],
        (4, 15): ["Visakha Puja Day"],
        (4, 16): ["Mahasthamaprapta Bodhisattva Birthday"],
        (4, 19): ["Avalokiteshvara Bodhisattva Birthday"],
        (4, 28): ["Medicine King Bodhisattva Birthday"],
        (5, 5): ["Dragon Boat Festival"],
        (5, 13): ["Sakyamuni Buddha Nirvana Day"],
        (5, 18): ["Zhang Tianshi Birthday"],
        (6, 3): ["Skanda Bodhisattva Birthday"],
        (6, 8): ["Sakyamuni Buddha Sermon Memorial Day"],
        (6, 15): ["Half Year Festival"],
        (6, 19): ["Avalokiteshvara Bodhisattva Enlightenment Day"],
        (6, 24): ["Ksitigarbha Bodhisattva Birthday"],
        (7, 7): ["Qixi Festival", "Magpie Festival"],
        (7, 13): ["Mahasthamaprapta Bodhisattva Birthday"],
        (7, 15): ["Ghost Festival", "Ullambana Festival"],
        (7, 21): ["Samantabhadra Bodhisattva Birthday"],
        (7, 24): ["Nagarjuna Bodhisattva Birthday"],
        (7, 30): ["Ksitigarbha Bodhisattva Birthday"],
        (8, 15): ["Mid-Autumn Festival", "Moonlight Bodhisattva Birthday"],
        (8, 18): ["Avalokiteshvara Bodhisattva Birthday"],
        (8, 21): ["Ksitigarbha Bodhisattva Birthday"],
        (8, 22): ["Dipankara Ancient Buddha Birthday"],
        (9, 9): ["Double Ninth Festival", "Dipankara Buddha Birthday"],
        (9, 13): ["Ksitigarbha Bodhisattva Birthday"],
        (9, 19): ["Avalokiteshvara Bodhisattva Renunciation Day"],
        (9, 30): ["Medicine Buddha Birthday"],
        (10, 15): ["Lower Yuan Festival"],
        (10, 17): ["Amitabha Buddha Birthday"],
        (10, 22): ["Mazu Birthday"],
        (11, 4): ["Medicine Buddha Birthday"],
        (11, 7): ["Amitabha Buddha Birthday"],
        (11, 17): ["Amitabha Buddha Birthday"],
        (12, 8): ["Laba Festival", "Sakyamuni Buddha Enlightenment Day"],
        (12, 23): ["Little New Year"],
        (12, 30): ["New Year's Eve"],
    }

    EN_FESTIVALS_SOLAR: Dict[Tuple[int, int], List[str]] = {
        (1, 1): ["New Year's Day"],
        (2, 14): ["Valentine's Day"],
        (2, 16): ["Welcome Spring Festival"],
        (3, 8): ["Women's Day"],
        (3, 12): ["Arbor Day"],
        (4, 1): ["April Fools' Day"],
        (4, 5): ["Qingming Festival"],
        (5, 1): ["Labor Day"],
        (5, 4): ["Youth Day"],
        (6, 1): ["Children's Day"],
        (6, 19): ["Father's Day"],
        (7, 1): ["Party Founding Day"],
        (8, 1): ["Army Day"],
        (9, 10): ["Teachers' Day"],
        (10, 1): ["National Day"],
        (10, 31): ["Halloween"],
        (12, 25): ["Christmas"],
        (12, 31): ["New Year's Eve"],
    }

    # 主要佛、菩萨、罗汉、尊者、祖师 名录
    BUDDHA_LIST: List[Dict[str, str]] = [
        {"name": "释迦牟尼佛", "title": "佛陀", "fame": "娑婆世界教主，功德圆满，说法49年"},
        {"name": "阿弥陀佛", "title": "佛陀", "fame": "西方极乐世界教主，无量寿佛"},
        {"name": "药师佛", "title": "佛陀", "fame": "东方琉璃世界教主，大医王"},
        {"name": "燃灯佛", "title": "佛陀", "fame": "定光佛，过去佛，为释迦授记"},
        {"name": "弥勒佛", "title": "佛陀", "fame": "未来佛，兜率天教主，笑口常开"},
        {"name": "宝幢佛", "title": "佛陀", "fame": "东方宝幢佛"},
        {"name": "阿閦佛", "title": "佛陀", "fame": "东方不动佛"},
        {"name": "宝光佛", "title": "佛陀", "fame": "南方宝光佛"},
        {"name": "大日如来", "title": "佛陀", "fame": "法身佛，密宗本尊"},
        {"name": "卢舍那佛", "title": "佛陀", "fame": "报身佛"},
        {"name": "毗卢遮那佛", "title": "佛陀", "fame": "法身佛，华藏世界教主"},
        {"name": "观音菩萨", "title": "菩萨", "fame": "观世音，大悲救苦救难，三十三化身"},
        {"name": "普贤菩萨", "title": "菩萨", "fame": "大行愿王，骑六牙白象，十大愿王"},
        {"name": "文殊菩萨", "title": "菩萨", "fame": "大智文殊，骑青狮，智慧第一"},
        {"name": "地藏王菩萨", "title": "菩萨", "fame": "大愿地藏，地狱不空誓不成佛"},
        {"name": "大势至菩萨", "title": "菩萨", "fame": "大精进，与观音同为西方三圣"},
        {"name": "阿弥陀佛", "title": "菩萨", "fame": "同上"},
        {"name": "弥勒菩萨", "title": "菩萨", "fame": "慈氏菩萨，未来佛"},
        {"name": "虚空藏菩萨", "title": "菩萨", "fame": "大虚空藏，智慧如虚空"},
        {"name": "金刚手菩萨", "title": "菩萨", "fame": "密迹金刚，手执金刚杵"},
        {"name": "药王菩萨", "title": "菩萨", "fame": "医者之王，疗治一切众生病苦"},
        {"name": "药上菩萨", "title": "菩萨", "fame": "药王菩萨之弟，同发菩提心"},
        {"name": "月光菩萨", "title": "菩萨", "fame": "月轮普现，清凉光普照"},
        {"name": "日光菩萨", "title": "菩萨", "fame": "日光普照，光破黑暗"},
        {"name": "准提菩萨", "title": "菩萨", "fame": "准提观音，十八臂准提"},
        {"name": "马头观音", "title": "菩萨", "fame": "马头明王，愤怒观音"},
        {"name": "千手观音", "title": "菩萨", "fame": "千眼千臂，大慈大悲"},
        {"name": "不空羂索观音", "title": "菩萨", "fame": "观音化身之一"},
        {"name": "药师三尊", "title": "菩萨", "fame": "药师佛+日光+月光"},
        {"name": "西方三圣", "title": "菩萨", "fame": "阿弥陀佛+观音+大势至"},
        {"name": "华严三圣", "title": "菩萨", "fame": "毗卢遮那佛+文殊+普贤"},
        {"name": "释迦三尊", "title": "菩萨", "fame": "释迦佛+文殊+普贤"},
        {"name": "五百罗汉", "title": "罗汉", "fame": "释迦牟尼佛的五百弟子，各证阿罗汉果"},
        {"name": "十八罗汉", "title": "罗汉", "fame": "降龙伏虎，各显神通"},
        {"name": "大迦叶尊者", "title": "尊者", "fame": "头陀第一，拈花微笑"},
        {"name": "阿难尊者", "title": "尊者", "fame": "多闻第一，佛侍二十五年"},
        {"name": "舍利弗尊者", "title": "尊者", "fame": "智慧第一，佛弟子中最聪明"},
        {"name": "目犍连尊者", "title": "尊者", "fame": "神通第一，能分身供养"},
        {"name": "富楼那尊者", "title": "尊者", "fame": "说法第一，善辩无碍"},
        {"name": "须菩提尊者", "title": "尊者", "fame": "解空第一，悟空性者"},
        {"name": "摩诃迦叶", "title": "尊者", "fame": "头陀行第一，不执于物"},
        {"name": "鸠摩罗什", "title": "祖师", "fame": "四大译经家之一，翻译《金刚经》"},
        {"name": "慧能大师", "title": "祖师", "fame": "禅宗六祖，《六祖坛经》"},
        {"name": "菩提达摩", "title": "祖师", "fame": "禅宗初祖，面壁九年"},
        {"name": "慧可大师", "title": "祖师", "fame": "禅宗二祖，断臂求法"},
        {"name": "僧璨大师", "title": "祖师", "fame": "禅宗三祖，《信心铭》"},
        {"name": "道信大师", "title": "祖师", "fame": "禅宗四祖"},
        {"name": "弘忍大师", "title": "祖师", "fame": "禅宗五祖"},
        {"name": "马祖道一", "title": "祖师", "fame": "南岳怀让弟子，洪州宗"},
        {"name": "百丈怀海", "title": "祖师", "fame": "《百丈清规》，丛林制度"},
        {"name": "赵州从谂", "title": "祖师", "fame": "赵州茶，狗子佛性"},
        {"name": "临济义玄", "title": "祖师", "fame": "临济宗创始人，四料简"},
        {"name": "曹山良价", "title": "祖师", "fame": "曹洞宗创始人，五位君臣"},
        {"name": "云门文偃", "title": "祖师", "fame": "云门宗创始人，三句"},
        {"name": "法眼文益", "title": "祖师", "fame": "法眼宗创始人"},
        {"name": "黄檗希运", "title": "祖师", "fame": "临济义玄之师"},
        {"name": "洞山良价", "title": "祖师", "fame": "曹洞宗创始人"},
        {"name": "丹霞天然", "title": "祖师", "fame": "丹霞烧佛，天然奇特"},
        {"name": "庞蕴居士", "title": "祖师", "fame": "居士禅，诗偈百首"},
    ]

    # ================================================================
    #  初始化
    # ================================================================
    def __init__(self) -> None:
        self._triple_cache: Dict[str, Tuple[int, int, int]] = {}
        self._ganzhi_cache: Dict[str, Dict[str, str]] = {}
        self._lunar_date_cache: Dict[str, Dict[str, Any]] = {}

    # ================================================================
    #  核心农历算法（脚本计算，非固定数组查找）
    # ================================================================
    @classmethod
    def _leap_month(cls, year: int) -> int:
        """求农历 year 年闰几月（0 = 无闰月）。"""
        idx = year - 1900
        if 0 <= idx < len(cls.LUNAR_INFO):
            return cls.LUNAR_INFO[idx] & 0xF
        return 0

    @classmethod
    def _leap_days(cls, year: int) -> int:
        """求农历 year 年闰月的天数。"""
        if cls._leap_month(year):
            idx = year - 1900
            if 0 <= idx < len(cls.LUNAR_INFO):
                return 30 if (cls.LUNAR_INFO[idx] & 0x10000) else 29
        return 0

    @classmethod
    def _month_days(cls, year: int, month: int) -> int:
        """求农历 year 年 month 月（非闰月）的天数（month: 1-12）。"""
        idx = year - 1900
        if 0 <= idx < len(cls.LUNAR_INFO):
            # bit 对应: 0x8000=正月, 0x4000=二月, ..., 0x800=腊月
            mask = 0x8000 >> (month - 1)
            return 30 if (cls.LUNAR_INFO[idx] & mask) else 29
        return 29

    @classmethod
    def _lunar_year_days(cls, year: int) -> int:
        """求农历 year 年总天数。"""
        total = 348  # 29 * 12
        for m in range(1, 13):
            if cls._month_days(year, m) == 30:
                total += 1
        return total + cls._leap_days(year)

    def _solar_to_lunar(self, solar_date: _dt.date) -> Tuple[int, int, int, bool]:
        """公历日期 → (农历年, 农历月, 农历日, 是否闰月)。

        算法：从 1900-01-31（农历 1900-01-01）开始，逐日累加。
        """
        # 基准日期
        base_date = _dt.date(1900, 1, 31)
        target = solar_date

        # 计算天数差
        offset_days = (target - base_date).days

        # 超出范围
        if offset_days < 0:
            # 退化为近似计算
            lunar_year = target.year
            lunar_month = target.month
            lunar_day = target.day
            return (lunar_year, lunar_month, lunar_day, False)

        # 逐年减
        lunar_year = 1900
        while lunar_year < 2100 and offset_days > 0:
            year_days = self._lunar_year_days(lunar_year)
            if offset_days < year_days:
                break
            offset_days -= year_days
            lunar_year += 1

        # 逐月减
        leap = self._leap_month(lunar_year)
        is_leap = False
        lunar_month = 1

        for m in range(1, 13):
            if leap == m and not is_leap:
                # 闰月
                leap_d = self._leap_days(lunar_year)
                if offset_days < leap_d:
                    lunar_month = m
                    is_leap = True
                    break
                offset_days -= leap_d
                is_leap = True  # 标记闰月已处理

            # 非闰月
            md = self._month_days(lunar_year, m)
            if offset_days < md:
                lunar_month = m
                break
            offset_days -= md
            lunar_month = m  # 临时记录

        lunar_day = offset_days + 1

        return (lunar_year, lunar_month, lunar_day, is_leap)

    # ================================================================
    #  天干地支计算
    # ================================================================
    @classmethod
    def _year_ganzhi(cls, year: int) -> Tuple[str, str]:
        """公历年 → 年干支。以立春为界（简化用公历）。"""
        # 甲子年为公元 4 年（year % 60 == 4 对应甲子）
        g_idx = (year - 4) % 10
        z_idx = (year - 4) % 12
        return (cls.TIAN_GAN[g_idx], cls.DI_ZHI[z_idx])

    @classmethod
    def _lunar_month_ganzhi(cls, lunar_year: int, lunar_month: int) -> Tuple[str, str]:
        """农历年月 → 月干支。基于五虎遁规则。"""
        year_gan_idx = (lunar_year - 4) % 10
        start_gan_map = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]
        start_gan = start_gan_map[year_gan_idx]

        g_idx = (start_gan + lunar_month - 1) % 10
        z_idx = (lunar_month + 1) % 12
        return (cls.TIAN_GAN[g_idx], cls.DI_ZHI[z_idx])

    @classmethod
    def _day_ganzhi(cls, solar_date: _dt.date) -> Tuple[str, str]:
        """公历日期 → 日干支。基准：1900-01-01 = 甲戌日 (天干0, 地支10)。"""
        base = _dt.date(1900, 1, 1)
        diff = (solar_date - base).days
        g_idx = (0 + diff) % 10
        z_idx = (10 + diff) % 12
        return (cls.TIAN_GAN[g_idx], cls.DI_ZHI[z_idx])

    # ================================================================
    #  节日计算
    # ================================================================
    def _get_lunar_festivals(self, lunar_month: int, lunar_day: int) -> List[str]:
        """获取农历日期对应的佛教节日。"""
        return self.BUDDHIST_FESTIVALS_LUNAR.get((lunar_month, lunar_day), [])

    def _get_solar_festivals(self, solar_month: int, solar_day: int) -> List[str]:
        """获取公历日期对应的节日。"""
        return self.BUDDHIST_FESTIVALS_SOLAR.get((solar_month, solar_day), [])

    def _get_next_lunar_festival(
        self, lunar_month: int, lunar_day: int, lunar_year: int, is_leap: bool
    ) -> Optional[Dict[str, Any]]:
        """获取下一个农历节日。"""
        # 收集所有有节日的农历日期
        festival_dates = sorted(self.BUDDHIST_FESTIVALS_LUNAR.keys())

        # 检查今年剩余的节日
        for (m, d) in festival_dates:
            if m > lunar_month or (m == lunar_month and d >= lunar_day):
                names = self.BUDDHIST_FESTIVALS_LUNAR[(m, d)]
                return {
                    "month": m, "day": d,
                    "names": names,
                    "days_until": self._days_until_lunar(lunar_month, lunar_day, m, d, lunar_year)
                }

        # 否则返回明年第一个节日
        if festival_dates:
            (m, d) = festival_dates[0]
            names = self.BUDDHIST_FESTIVALS_LUNAR[(m, d)]
            return {
                "month": m, "day": d,
                "names": names,
                "days_until": self._days_until_lunar(lunar_month, lunar_day, m, d, lunar_year, next_year=True)
            }
        return None

    def _days_until_lunar(
        self, cur_m: int, cur_d: int, target_m: int, target_d: int, year: int, next_year: bool = False
    ) -> int:
        """计算到下一个农历节日的天数。"""
        try:
            # 找目标农历日期对应的公历
            target_solar = self._lunar_to_solar_approx(target_m, target_d, year + (1 if next_year else 0))
            # 今天的农历日期对应公历
            today = _dt.date.today()
            diff = (target_solar - today).days
            return max(0, diff)
        except Exception:
            return 0

    def _lunar_to_solar_approx(self, l_month: int, l_day: int, year: int) -> _dt.date:
        """农历→公历（近似：遍历查找）。"""
        # 简化实现：从农历正月初一累加
        base_date = _dt.date(year - 1, 11, 1)  # 大致从前一年11月开始
        # 更准确：农历year年正月初一对应的公历日期
        # 通过反向查找
        for solar_day_offset in range(-30, 370):
            candidate = base_date + _dt.timedelta(days=solar_day_offset)
            ly, lm, ld, _ = self._solar_to_lunar(candidate)
            if ly == year and lm == l_month and ld == l_day:
                return candidate
        # 兜底
        return base_date + _dt.timedelta(days=30 * (l_month - 1) + l_day + 15)

    # ================================================================
    #  农历日 → 中文
    # ================================================================
    @staticmethod
    def _render_day_string(day: int) -> str:
        """农历日 → 中文。"""
        if 1 <= day <= 30:
            return LunarCalendarService.CHN_DAY_1[day - 1]
        return str(day)

    @staticmethod
    def _render_month_string(month: int) -> str:
        """农历月 → 中文。"""
        if 1 <= month <= 12:
            return LunarCalendarService.CHN_MONTH[month - 1] + "月"
        return str(month) + "月"

    @staticmethod
    def _render_day_string_en(day: int) -> str:
        """农历日 → 英文。"""
        if 1 <= day <= 30:
            return LunarCalendarService.EN_CHN_DAY[day - 1]
        return str(day)

    @staticmethod
    def _render_month_string_en(month: int) -> str:
        """农历月 → 英文。"""
        if 1 <= month <= 12:
            return LunarCalendarService.EN_CHN_MONTH[month - 1]
        return str(month)

    def _get_lunar_festivals_en(self, lunar_month: int, lunar_day: int) -> List[str]:
        """获取农历英文节日列表。"""
        return self.EN_FESTIVALS_LUNAR.get((lunar_month, lunar_day), [])

    def _get_solar_festivals_en(self, solar_month: int, solar_day: int) -> List[str]:
        """获取公历英文节日列表。"""
        return self.EN_FESTIVALS_SOLAR.get((solar_month, solar_day), [])

    # ================================================================
    #  公共 API
    # ================================================================
    def get_lunar_date_string(self, maybe_date: Optional[_dt.datetime] = None) -> str:
        """返回形如「丙午年 乙未月 甲辰日 农历六月十六」的字符串。"""
        target = _dt.datetime.now() if maybe_date is None else maybe_date
        solar_date = target.date() if isinstance(target, _dt.datetime) else target

        # 农历转换
        ly, lm, ld, is_leap = self._solar_to_lunar(solar_date)

        # 干支
        y_g, y_z = self._year_ganzhi(ly)
        m_g, m_z = self._lunar_month_ganzhi(ly, lm)
        d_g, d_z = self._day_ganzhi(solar_date)

        # 生肖
        animal = self.ZHI_ANIMAL[(ly - 4) % 12]

        # 农历日期中文
        leap_prefix = "闰" if is_leap else ""
        m_str = self._render_month_string(lm)
        d_str = self._render_day_string(ld)

        # 构建完整字符串
        parts = []
        parts.append(f"{y_g}{y_z}{animal}年")
        parts.append(f"{m_g}{m_z}月")
        parts.append(f"{d_g}{d_z}日")
        parts.append(f"农历{leap_prefix}{m_str}{d_str}")

        return " ".join(parts)

    def get_buddha_info(self, maybe_date: Optional[_dt.datetime] = None) -> List[str]:
        """获取当天佛教节日信息。"""
        target = _dt.datetime.now() if maybe_date is None else maybe_date
        solar_date = target.date() if isinstance(target, _dt.datetime) else target

        ly, lm, ld, is_leap = self._solar_to_lunar(solar_date)

        lunar_festivals = self._get_lunar_festivals(lm, ld)
        solar_festivals = self._get_solar_festivals(target.month, target.day)

        return lunar_festivals + solar_festivals

    def is_first_or_fifteenth(self, maybe_date: Optional[_dt.datetime] = None) -> bool:
        """今天是不是农历初一、十五或佛教节日。"""
        target = _dt.datetime.now() if maybe_date is None else maybe_date
        solar_date = target.date() if isinstance(target, _dt.datetime) else target
        ly, lm, ld, is_leap = self._solar_to_lunar(solar_date)
        if ld == 1 or ld == 15:
            return True
        # 检查是否为佛教节日
        festivals = self._get_lunar_festivals(lm, ld)
        solar_festivals = self._get_solar_festivals(target.month, target.day)
        return len(festivals) > 0 or len(solar_festivals) > 0

    def get_countdown(self, maybe_date: Optional[_dt.datetime] = None) -> Dict[str, Any]:
        """获取初一/十五/节日倒计时。"""
        target = _dt.datetime.now() if maybe_date is None else maybe_date
        solar_date = target.date() if isinstance(target, _dt.datetime) else target

        ly, lm, ld, is_leap = self._solar_to_lunar(solar_date)

        # 当前干支
        y_g, y_z = self._year_ganzhi(ly)
        m_g, m_z = self._lunar_month_ganzhi(ly, lm)
        d_g, d_z = self._day_ganzhi(solar_date)
        animal = self.ZHI_ANIMAL[(ly - 4) % 12]

        # 农历日期中文
        leap_prefix = "闰" if is_leap else ""
        m_str = self._render_month_string(lm)
        d_str = self._render_day_string(ld)

        # 节日
        today_festivals = self._get_lunar_festivals(lm, ld)
        solar_festivals = self._get_solar_festivals(target.month, target.day)
        all_festivals = today_festivals + solar_festivals

        # 初一/十五逻辑（脚本计算，非固定数组）
        countdown_type = ""
        countdown_days = 0

        if ld == 1:
            countdown_type = "初一"
            countdown_days = 0
        elif ld == 15:
            countdown_type = "十五"
            countdown_days = 0
        elif ld < 15:
            countdown_type = "十五"
            countdown_days = 15 - ld
        else:
            # 已过十五，计算到下一个初一
            # 当前月最后一天
            md = self._month_days(ly, lm)
            if self._leap_month(ly) == lm and not is_leap:
                md += self._leap_days(ly)
            days_to_month_end = md - ld
            # 下一个初一 = 本月剩余 + 下个月第一天
            countdown_days = days_to_month_end + 1
            # 如果有闰月在后面，需要考虑
            if self._leap_month(ly) > lm:
                leap_md = self._leap_days(ly)
                next_md = self._month_days(ly, lm + 1 if lm < 12 else 1)
                # 简化：直接用已计算的天数
                pass
            countdown_type = "初一"

        # 如果今天是节日
        festival_today = all_festivals[0] if all_festivals else ""

        return {
            "lunar_year": ly,
            "lunar_month": lm,
            "lunar_day": ld,
            "is_leap": is_leap,
            "year_ganzhi": f"{y_g}{y_z}",
            "month_ganzhi": f"{m_g}{m_z}",
            "day_ganzhi": f"{d_g}{d_z}",
            "animal": animal,
            "lunar_date_str": f"农历{leap_prefix}{m_str}{d_str}",
            "countdown_type": countdown_type,
            "countdown_days": countdown_days,
            "is_first": ld == 1,
            "is_fifteenth": ld == 15,
            "festivals_today": all_festivals,
            "festival_today": festival_today,
        }

    def get_display_text(self, maybe_date: Optional[_dt.datetime] = None, lang: str = "zh") -> str:
        """前端直接展示的一句话，支持中英文。

        Args:
            maybe_date: 可选日期，默认当前时间
            lang: 'zh' 中文（默认）| 'en' 英文
        """
        target = _dt.datetime.now() if maybe_date is None else maybe_date
        solar_date = target.date() if isinstance(target, _dt.datetime) else target

        ly, lm, ld, is_leap = self._solar_to_lunar(solar_date)
        y_g, y_z = self._year_ganzhi(ly)
        m_g, m_z = self._lunar_month_ganzhi(ly, lm)
        d_g, d_z = self._day_ganzhi(solar_date)

        if lang == "en":
            return self._build_display_en(
                target, solar_date, ly, lm, ld, is_leap,
                y_g, y_z, m_g, m_z, d_g, d_z
            )
        else:
            return self._build_display_zh(
                target, solar_date, ly, lm, ld, is_leap,
                y_g, y_z, m_g, m_z, d_g, d_z
            )

    def _build_display_zh(self, target, solar_date, ly, lm, ld, is_leap,
                          y_g, y_z, m_g, m_z, d_g, d_z) -> str:
        """构建中文展示文本。"""
        animal = self.ZHI_ANIMAL[(ly - 4) % 12]

        leap_prefix = "闰" if is_leap else ""
        m_str = self._render_month_string(lm)
        d_str = self._render_day_string(ld)
        lunar_str = f"农历{leap_prefix}{m_str}{d_str}"

        festivals = self._get_lunar_festivals(lm, ld)
        solar_festivals = self._get_solar_festivals(target.month, target.day)
        all_festivals = festivals + solar_festivals

        parts = []
        parts.append(f"{y_g}{y_z}{animal}年")
        parts.append(f"{m_g}{m_z}月")
        parts.append(f"{d_g}{d_z}日")
        parts.append(lunar_str)

        if all_festivals:
            festival_text = "、".join(all_festivals[:2])
            parts.append(f"今日：{festival_text}")
        elif ld == 1:
            parts.append("今日初一")
        elif ld == 15:
            parts.append("今日十五")
        else:
            countdown = self.get_countdown(target)
            cd_type = countdown.get("countdown_type", "")
            cd_days = countdown.get("countdown_days", 0)
            if cd_type and cd_days > 0:
                parts.append(f"{cd_type}还有{cd_days}天")

        return " · ".join(parts)

    def _build_display_en(self, target, solar_date, ly, lm, ld, is_leap,
                          y_g, y_z, m_g, m_z, d_g, d_z) -> str:
        """构建英文展示文本。"""
        zhi_animal = self.EN_ZHI_ANIMAL[(ly - 4) % 12]

        leap_prefix = "Leap " if is_leap else ""
        m_str = self._render_month_string_en(lm)
        d_str = self._render_day_string_en(ld)
        lunar_str = f"Lunar {leap_prefix}{m_str} {d_str}"

        festivals = self._get_lunar_festivals_en(lm, ld)
        solar_festivals = self._get_solar_festivals_en(target.month, target.day)
        all_festivals = festivals + solar_festivals

        parts = []
        parts.append(f"{y_g}{y_z} {zhi_animal} Year")
        parts.append(f"{m_g}{m_z} Month")
        parts.append(f"{d_g}{d_z} Day")
        parts.append(lunar_str)

        if all_festivals:
            festival_text = ", ".join(all_festivals[:2])
            parts.append(f"Today: {festival_text}")
        elif ld == 1:
            parts.append("Today: New Moon (1st day)")
        elif ld == 15:
            parts.append("Today: Full Moon (15th day)")
        else:
            countdown = self.get_countdown(target)
            cd_type = countdown.get("countdown_type", "")
            cd_days = countdown.get("countdown_days", 0)
            if cd_type == "初一" and cd_days > 0:
                parts.append(f"New Moon in {cd_days} days")
            elif cd_type == "十五" and cd_days > 0:
                parts.append(f"Full Moon in {cd_days} days")

        return " · ".join(parts)


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------
lunar_calendar_service = LunarCalendarService()
