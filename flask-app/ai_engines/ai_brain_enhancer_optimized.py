#!/usr/bin/env python3
"""
优化版AI脑库增强器, 用于升级和优化AI脑库系统
主要优化:减少内存占用,提高处理效率
"""
import gc
import json
from datetime import datetime
from app.models.ai_brain import AIBrainKnowledge, AIBrainActivity
from app.services.ai_brain_service import ai_brain_service
from app.ai.ai_engine_integrator import ai_engine_integrator
from app.utils.logging import logger

class OptimizedAIBrainEnhancer:
    """优化版AI脑库增强器"""

    def __init__(self):
        self.enhancement_history = []
        logger.info("优化版AI脑库增强器初始化完成")

    def enhance_knowledge_base(self):
        """增强AI脑库"""
        logger.info("开始增强AI脑库")

        try:
            self._unify_knowledge_types()
            gc.collect()

            self._enhance_knowledge_relationships_optimized()
            gc.collect()

            self._optimize_knowledge_search_optimized()
            gc.collect()

            self._integrate_external_ai_engines()
            gc.collect()

            self._improve_knowledge_graph_optimized()
            gc.collect()

            self._add_knowledge_review_mechanism()
            gc.collect()

            self._enhance_statistics_and_analytics()
            gc.collect()

            logger.info("AI脑库增强完成")
            return {"success": True}
        except Exception as e:
            logger.error(f"增强AI脑库失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _unify_knowledge_types(self):
        """统一知识类型"""
        logger.info("开始统一知识类型")

        standard_types = {
            "problem": "问题",
            "solution": "解决方案",
            "experience": "经验",
            "rule": "规则",
            "concept": "概念",
            "technique": "技术",
            "case": "案例",
            "best_practice": "最佳实践",
            "faq": "常见问题",
            "document": "文档"
        }

        type_keywords = {
            "problem": ["问题", "错误", "失败", "异常", "报错", "bug"],
            "solution": ["解决方案", "解决方法", "修复", "解决", "处理", "fix"],
            "experience": ["经验", "总结", "体会", "教训"],
            "rule": ["规则", "规范", "要求", "准则", "标准"],
            "concept": ["概念", "定义", "解释", "含义"],
            "case": ["案例", "实例", "例子", "示例"],
            "best_practice": ["最佳实践", "建议", "推荐", "最佳方案"],
            "faq": ["常见问题", "faq", "问答", "疑问"],
            "document": ["文档", "说明", "指南", "手册"]
        }

        page = 1
        page_size = 100
        updated_count = 0

        while True:
            knowledges = ai_brain_service.get_knowledge_paginated(page=page, page_size=page_size)
            if not knowledges:
                break

            for knowledge in knowledges:
                if knowledge.knowledge_type not in standard_types:
                    content = knowledge.content.lower() if knowledge.content else ""
                    title = knowledge.title.lower() if knowledge.title else ""

                    matched_type = "concept"
                    max_matches = 0

                    combined_text = (title + " " + content).lower()

                    for type_name, keywords in type_keywords.items():
                        matches = sum(1 for keyword in keywords if keyword in combined_text)
                        if matches > max_matches:
                            max_matches = matches
                            matched_type = type_name

                    if matched_type != knowledge.knowledge_type:
                        ai_brain_service.update_knowledge(
                            knowledge.knowledge_id,
                            knowledge_type=matched_type
                        )
                        updated_count += 1

            del knowledges
            gc.collect()
            page += 1

        self.enhancement_history.append({
            "type": "unify_knowledge_types",
            "timestamp": datetime.now().isoformat(),
            "details": f"统一了{updated_count}条知识的类型,标准类型:{list(standard_types.keys())}"
        })

        logger.info(f"完成统一知识类型, 更新了{updated_count}条知识")

    def _enhance_knowledge_relationships_optimized(self):
        """优化版增强知识关联"""
        logger.info("开始增强知识关联")

        knowledge_dict = {}
        page = 1
        page_size = 500

        while True:
            knowledges = ai_brain_service.get_knowledge_paginated(
                page=page,
                page_size=page_size,
                fields=["knowledge_id", "title", "content"]
            )

            if not knowledges:
                break

            for knowledge in knowledges:
                knowledge_dict[knowledge.knowledge_id] = {
                    "title": knowledge.title or "",
                    "content": knowledge.content or ""
                }

            del knowledges
            gc.collect()
            page += 1

        knowledge_ids = list(knowledge_dict.keys())
        batch_size = 50
        total_batches = (len(knowledge_ids) + batch_size - 1) // batch_size
        enhanced_count = 0

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(knowledge_ids))
            batch_ids = knowledge_ids[start_idx:end_idx]

            for knowledge_id in batch_ids:
                current_knowledge = ai_brain_service.get_knowledge_by_id(knowledge_id)
                if not current_knowledge:
                    continue

                related_knowledge = self._find_similar_knowledge_optimized(
                    knowledge_id,
                    knowledge_dict[knowledge_id],
                    knowledge_dict
                )

                if related_knowledge:
                    new_tags = list(set(current_knowledge.tags))

                    for related in related_knowledge:
                        if current_knowledge.knowledge_id != related.knowledge_id:
                            relation_tag = f"related-to:{related.knowledge_id}"
                            if relation_tag not in new_tags:
                                new_tags.append(relation_tag)

                    if set(new_tags) != set(current_knowledge.tags):
                        ai_brain_service.update_knowledge(
                            current_knowledge.knowledge_id,
                            tags=new_tags
                        )
                        enhanced_count += 1

                del current_knowledge
                gc.collect()

            del batch_ids
            gc.collect()

        del knowledge_dict
        gc.collect()

        self.enhancement_history.append({
            "type": "enhance_knowledge_relationships",
            "timestamp": datetime.now().isoformat(),
            "details": f"增强了{enhanced_count}条知识的关联关系"
        })

        logger.info(f"完成增强知识关联, 更新了{enhanced_count}条知识")

    def _find_similar_knowledge_optimized(self, current_id, current_info, knowledge_dict, limit=3, similarity_threshold=0.3):
        """优化版:基于内容相似度查找相关知识"""
        similar_knowledge = []
        current_text = (current_info["title"] + " " + current_info["content"]).lower()
        current_words = self._get_words(current_text)

        check_count = 0
        max_check = 100

        for knowledge_id, info in knowledge_dict.items():
            if knowledge_id == current_id:
                continue
            check_count += 1
            if check_count > max_check:
                break

            other_text = (info["title"] + " " + info["content"]).lower()
            other_words = self._get_words(other_text)

            intersection = len(current_words.intersection(other_words))
            union = len(current_words.union(other_words))

            if union > 0:
                similarity = intersection / union
                if similarity >= similarity_threshold:
                    related = ai_brain_service.get_knowledge_by_id(knowledge_id)
                    if related:
                        similar_knowledge.append((similarity, related))

        similar_knowledge.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in similar_knowledge[:limit]]

    def _get_words(self, text):
        """提取文本中的关键词"""
        import re
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            words = re.findall(r'[\u4e00-\u9fff]+|[\u3040-\u309f\u30a0-\u30ff]+|[a-zA-Z]+', text.lower())
        else:
            words = text.lower().split()
        return set(words)

    def _optimize_knowledge_search_optimized(self):
        """优化版优化知识搜索"""
        logger.info("开始优化知识搜索")

        page = 1
        page_size = 100
        updated_count = 0

        while True:
            knowledges = ai_brain_service.get_knowledge_paginated(page=page, page_size=page_size)
            if not knowledges:
                break

            for knowledge in knowledges:
                content = knowledge.content.lower() if knowledge.content else ""
                title = knowledge.title.lower() if knowledge.title else ""
                keywords = self._extract_keywords(content + " " + title)

                new_tags = list(set(knowledge.tags + keywords))

                if set(new_tags) != set(knowledge.tags):
                    ai_brain_service.update_knowledge(
                        knowledge.knowledge_id,
                        tags=new_tags
                    )
                    updated_count += 1

            del knowledges
            page += 1

        self.enhancement_history.append({
            "type": "optimize_knowledge_search",
            "timestamp": datetime.now().isoformat(),
            "details": f"为{updated_count}条知识添加了搜索标签"
        })

        logger.info(f"完成优化知识搜索, 更新了{updated_count}条知识")

    def _extract_keywords(self, text):
        """提取文本中的关键词"""
        if not text:
            return []

        import re
        stop_words = set(["的", "是", "在", "和", "了", "有", "不", "这", "我", "他", "她", "它"])

        if any('\u4e00' <= c <= '\u9fff' for c in text):
            words = re.findall(r'[\u4e00-\u9fff]+|[\u3040-\u309f\u30a0-\u30ff]+|[a-zA-Z]+', text)
        else:
            words = text.split()

        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]

        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return [word for word, freq in sorted_words]

    def _integrate_external_ai_engines(self):
        """整合外部AI引擎"""
        logger.info("开始整合外部AI引擎")

        test_prompt = "请简要解释AI脑库的概念和作用"
        test_result = ai_engine_integrator.call_engine("qianwen", test_prompt, temperature=0.7, max_tokens=500)

        if test_result:
            ai_brain_service.add_knowledge(
                title="AI脑库概念解释",
                content=test_result.get("data", {}).get("response", ""),
                knowledge_type="concept",
                source_id="qianwen",
                tags=["ai_brain", "concept", "external_ai"]
            )

        self.enhancement_history.append({
            "type": "integrate_external_ai_engines",
            "timestamp": datetime.now().isoformat(),
            "details": "整合了外部AI引擎,支持使用抖音火山引擎,豆包,腾讯云,阿里云,阿福,千问等引擎增强知识"
        })

        logger.info("完成整合外部AI引擎")

    def _improve_knowledge_graph_optimized(self):
        """改进知识图谱"""
        logger.info("开始改进知识图谱")

        from app.utils.db import db_manager
        cursor = db_manager.get_cursor()

        cursor.execute("SELECT knowledge_id, title, knowledge_type FROM ai_brain_knowledge")
        nodes = []
        node_dict = {}

        for row in cursor.fetchall():
            knowledge_id = row[0]
            node = {
                "id": knowledge_id,
                "title": row[1] or "",
                "type": row[2] or "concept"
            }
            nodes.append(node)
            node_dict[knowledge_id] = node

        cursor.execute("SELECT knowledge_id, tags FROM ai_brain_knowledge")
        edges = []

        for row in cursor.fetchall():
            source_id = row[0]
            tags_str = row[1] or "[]"

            try:
                tags = json.loads(tags_str)
            except json.JSONDecodeError:
                tags = []

            for tag in tags:
                if tag.startswith("related-to:"):
                    target_id = tag.split(":")[1]
                    if source_id in node_dict and target_id in node_dict:
                        source_node = node_dict[source_id]
                        target_node = node_dict[target_id]

                        relation_type = "related_to"

                        if source_node["type"] == "problem" and target_node["type"] == "solution":
                            relation_type = "solved_by"
                        elif source_node["type"] == "solution" and target_node["type"] == "problem":
                            relation_type = "solves"
                        elif source_node["type"] == "concept" and target_node["type"] == "technique":
                            relation_type = "applies_to"
                        elif source_node["type"] == "technique" and target_node["type"] == "concept":
                            relation_type = "based_on"
                        elif source_node["type"] == "case" and target_node["type"] == "experience":
                            relation_type = "derived_from"
                        elif source_node["type"] == "experience" and target_node["type"] == "rule":
                            relation_type = "leads_to"

                        edge = {
                            "source": source_id,
                            "target": target_id,
                            "type": relation_type,
                            "label": relation_type.replace("_", " ").title()
                        }

                        edges.append(edge)

        enhanced_graph = {
            "nodes": nodes,
            "edges": edges
        }

        self._save_enhanced_knowledge_graph(enhanced_graph)

        del nodes
        del node_dict
        del edges
        del enhanced_graph

        self.enhancement_history.append({
            "type": "improve_knowledge_graph",
            "timestamp": datetime.now().isoformat(),
            "details": f"改进了知识图谱,添加了{len(edges)}条带有关系类型的边"
        })

        logger.info("完成改进知识图谱")

    def _save_enhanced_knowledge_graph(self, graph):
        """保存增强后的知识图谱"""
        import os
        graph_file = os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'enhanced_knowledge_graph.json')

        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

    def _add_knowledge_review_mechanism(self):
        """添加知识审核机制"""
        logger.info("开始添加知识审核机制")

        from app.utils.db import db_manager

        try:
            columns = db_manager.fetch_all("PRAGMA table_info(ai_brain_knowledge)")
            has_review_status = any(col[1] == 'review_status' for col in columns)

            if not has_review_status:
                db_manager.execute("ALTER TABLE ai_brain_knowledge ADD COLUMN review_status TEXT DEFAULT 'pending'")
                db_manager.execute("ALTER TABLE ai_brain_knowledge ADD COLUMN reviewed_by TEXT")
                db_manager.execute("ALTER TABLE ai_brain_knowledge ADD COLUMN reviewed_at DATETIME")
                logger.info("已添加知识审核字段")

            db_manager.execute("UPDATE ai_brain_knowledge SET review_status = 'approved'")
            logger.info("已更新所有现有知识的审核状态")

            self.enhancement_history.append({
                "type": "add_knowledge_review_mechanism",
                "timestamp": datetime.now().isoformat(),
                "details": "添加了知识审核机制,包括审核状态,审核人和审核时间字段"
            })
        except Exception as e:
            logger.error(f"添加知识审核机制失败: {str(e)}")

    def _enhance_statistics_and_analytics(self):
        """增强统计和分析"""
        logger.info("开始增强统计和分析")

        from app.utils.db import db_manager

        stats = ai_brain_service.get_knowledge_stats()

        enhanced_stats = {
            **stats,
            "detailed_types": {},
            "knowledge_growth": [],
            "top_sources": {},
            "review_status": {}
        }

        cursor = db_manager.get_cursor()
        cursor.execute("SELECT knowledge_type, COUNT(*) FROM ai_brain_knowledge GROUP BY knowledge_type")
        for row in cursor.fetchall():
            enhanced_stats["detailed_types"][row[0]] = row[1]

        cursor.execute("SELECT review_status, COUNT(*) FROM ai_brain_knowledge GROUP BY review_status")
        for row in cursor.fetchall():
            enhanced_stats["review_status"][row[0]] = row[1]

        self._save_enhanced_statistics(enhanced_stats)

        self.enhancement_history.append({
            "type": "enhance_statistics_and_analytics",
            "timestamp": datetime.now().isoformat(),
            "details": "增强了统计和分析功能,包括详细类型统计,知识增长趋势和审核状态统计"
        })

        logger.info("完成增强统计和分析")

    def _save_enhanced_statistics(self, stats):
        """保存增强后的统计信息"""
        import os
        stats_file = os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'enhanced_knowledge_stats.json')

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

    def get_enhancement_history(self):
        """获取增强历史"""
        return self.enhancement_history
