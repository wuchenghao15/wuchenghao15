"""
分块测试输入数据
"""

from __future__ import annotations


# 基础测试文本
INPUT_TEXTS = {
    "empty": "",
    "single_char": "字",
    "whitespace": "   \n\t   \r\n   ",
    "unicode_mix": "你好 👋 Hello مرحبا",
    "line_endings": "行1\r\n行2\n行3\r\n行4",
    "multi_newlines": "\n\n\n\n文本\n\n\n\n",
    "html_mixed": "<p>你好</p>\n普通文本\n<div>世界</div>",
    "urls": "访问 https://m-flow.ai 或邮件 test@m-flow.ai",
    "ellipsis": "你好...最近怎样…",
    "structured_list": """让我梳理一下文本分块系统需要测试的关键属性：

分块边界准确性：
- 正确的句子边界检测
- 标点符号处理
- 段落分隔识别
- 特殊字符和空白处理
- 引号和嵌套结构处理

多语言支持：
- 不同语言和文字的处理
- 多语言文档支持
- Unicode正确处理
- 语言特定标点处理

特殊场景：
- 列表和项目符号
- 表格和结构化内容
- 代码块和技术内容
- 引用和参考文献

性能指标：
- 不同文本长度的处理速度
- 大文档的内存使用
- 文档大小增加时的可扩展性

文档格式：
- 纯文本处理
- HTML/XML内容
- PDF文本提取
- Markdown格式

错误处理：
- 格式错误的输入
- 不完整的句子
- 截断的文档
- 无效字符

配置灵活性：
- 可调整的分块大小
- 自定义边界规则
- 可配置的分块重叠

上下文保持：
- 语义连贯性
- 上下文关系保持
- 交叉引用处理""",
    "code_sample": """from typing import (
    Any, List, Optional, Union,
)

class DataProcessor:
    '''数据处理器类'''

    def __init__(self, config: dict) -> None:
        self._config = config
        self._data: List[Any] = []

    def process(self, input_data: Any) -> Optional[dict]:
        '''处理输入数据'''
        if not input_data:
            return None

        result = {
            "status": "processed",
            "items": len(self._data),
            "config": self._config,
        }
        return result

    async def async_process(self, items: List[Any]) -> List[dict]:
        '''异步批量处理'''
        results = []
        for item in items:
            r = await self._process_single(item)
            results.append(r)
        return results""",
    "classical_text": """春江潮水连海平，海上明月共潮生。
滟滟随波千万里，何处春江无月明。
江流宛转绕芳甸，月照花林皆似霰。
空里流霜不觉飞，汀上白沙看不见。
江天一色无纤尘，皎皎空中孤月轮。
江畔何人初见月，江月何年初照人。
人生代代无穷已，江月年年望相似。
不知江月待何人，但见长江送流水。
白云一片去悠悠，青枫浦上不胜愁。
谁家今夜扁舟子，何处相思明月楼。
可怜楼上月裴回，应照离人妆镜台。
玉户帘中卷不去，捣衣砧上拂还来。
此时相望不相闻，愿逐月华流照君。
鸿雁长飞光不度，鱼龙潜跃水成文。
昨夜闲潭梦落花，可怜春半不还家。
江水流春去欲尽，江潭落月复西斜。
斜月沉沉藏海雾，碣石潇湘无限路。
不知乘月几人归，落月摇情满江树。""",
}

# 长词文本测试
INPUT_TEXTS_LONGWORDS = {
    "chinese_prose": """在这座古老而又现代的城市中，隐藏着一条名为杏花巷的小街。
青石板路被岁月打磨得光滑如镜，古墙上的爬山虎为这条充满历史气息的小巷增添了勃勃生机。
清晨时分，巷子里弥漫着早餐铺的香气，那是豆浆和油条的味道。
店门前总是排着长队，有赶时间的上班族，也有悠闲的老人。
巷子深处有一家百年茶馆，古色古香的木桌椅上总是坐满了品茗聊天的街坊。
傍晚时分，夕阳的余晖洒在石板路上，为小巷披上一层金色的外衣。
街角的古树下，常有艺人驻足卖唱，用沧桑的嗓音讲述这座城市的传奇。
游客举着相机，试图捕捉这里独特的市井风情。
这条看似平凡的小巷，承载着无数市民的记忆和岁月的痕迹。""",
}
