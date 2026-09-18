# dev_activity_preflight 模糊匹配修复 (v23.9.1)

**问题**: _DEV_ACTIVITY_PATTERN 用 re.escape() 做精确匹配，无法覆盖中间插字的自然语言
**修复**: 加 25+ 模糊正则模式，动词.{0,15}名词

## 修复前 (失败)
```python
_DEV_ACTIVITY_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in _DEV_ACTIVITY_KEYWORDS),
    re.IGNORECASE
)
# 输入 "新建一个galaxy视频批量生成功能" → hit=None ❌
```

## 修复后 (全绿)
```python
# 精确匹配 + 模糊正则 = 双重保障
_DEV_ACTIVITY_FUZZY_PATTERNS = [
    r"创建.{0,15}(功能|模块|引擎|服务|接口|表|项目|页面|路由|文件|脚本|配置)",
    r"新建.{0,15}(功能|模块|引擎|服务|接口|表|项目|页面|路由|文件|脚本|配置|API)",
    r"修复.{0,15}(bug|Bug|BUG|问题|错误|异常|缺陷)",
    r"优化.{0,15}(代码|性能|配置|逻辑|算法|查询)",
    ...25+ patterns covering 10 categories
]

_DEV_ACTIVITY_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in _DEV_ACTIVITY_KEYWORDS) +
    "|" + "|".join(_DEV_ACTIVITY_FUZZY_PATTERNS),
    re.IGNORECASE | re.UNICODE
)
```

## 测试结果 (全部 PASS)
```
✅ "新建一个galaxy视频批量生成功能" → hit="新建一个galaxy视频批量生成功能"
✅ "修复一下那个bug" → hit="修复一下那个bug"
✅ "新建功能" → hit="新建功能"
✅ "写点代码" → hit="写点代码"
✅ "优化数据库查询性能" → hit="优化数据库查询"
✅ "秦统一六国的故事" → hit=None (非开发活动, 正确放行)
```

## 新增模糊正则覆盖 10 大类
1. 创建类动词 + 名词 (新建/创建/新增)
2. 开发/实现类 (开发/实现/编写/写)
3. 修改/修复类 (修改/修复/解决/调整/优化/重构)
4. 安装/部署/升级类 (安装/部署/升级/迁移)
5. 数据变更类 (SQL关键词 + 数据库.*变更 + 加/增/删/改.*字段)
6. Git 操作类 (git commit/push/pull/add/...)
7. 包管理类 (pip/npm/yarn/conda install)
8. 系统/服务类 (启动/运行/执行.*docker/ollama/python/...)
9. 服务控制类 (停/关/重.*服务/进程/daemon)
10. AI/模型类 (训练/微调/fine-tune.*模型/LLM)

---
**flow_id**: flow_sa_gov_1789689625646 (SA紧急治理通道)
**测试**: 6/6 PASS
**性能**: .{0,15} span 可能稍慢, 但关键词数量从 23 扩展到 48 精确 + 25+ 模糊, 性能影响可忽略
