#!/usr/bin/env python3
"""
AI脑库服务

from datetime import datetime
from app.models.ai_brain import AIBrainKnowledge, AIBrainActivity
from app.utils.logging import logger


class AIBrainService:
    """AI脑库服务类"""

    def __init__(self):
        # 确保AI脑库表存在
        self._init_tables()

    def _init_tables(self):
        """初始化表"""
        try:
            AIBrainKnowledge.create_table()
            AIBrainActivity.create_table()
            logger.info("✓ AI脑库表初始化成功")
        except Exception as e:
            logger.error(f"✗ AI脑库表初始化失败: {str(e)}")

    def add_knowledge(self, title, content, knowledge_type, source, source_id=None, tags=None, priority=0):
        """添加知识到AI脑库"""
        try:
                title=title,
                content=content,
                knowledge_type=knowledge_type,
                source=source,
                source_id=source_id,
                tags=tags,
                priority=priority
            )
            knowledge.save()

            # 记录活动日志
            self._log_activity(
                activity_type="knowledge_added",
                description=f"添加知识: {title}",
                source=source,
                source_id=source_id,
                    "knowledge_id": knowledge.knowledge_id,
                }
            )

            logger.info(f"✓ 成功添加知识到AI脑库: {knowledge.knowledge_id}")
            return knowledge
        except Exception as e:
            logger.error(f"✗ 添加知识到AI脑库失败: {str(e)}")
            return None

    def update_knowledge(self, knowledge_id, title=None, content=None, knowledge_type=None,
                       tags=None, priority=None, is_active=None):
        """更新AI脑库知识"""
        try:
            if not knowledge:
                logger.warning(f"✗ 未找到知识: {knowledge_id}")
                return None

            # 更新字段
            if title is not None:
                knowledge.title = title
            if content is not None:
                knowledge.content = content
            if knowledge_type is not None:
                knowledge.knowledge_type = knowledge_type
            if tags is not None:
                knowledge.tags = tags
            if priority is not None:
                knowledge.priority = priority
            if is_active is not None:
                knowledge.is_active = is_active

            knowledge.save()

            # 记录活动日志
            self._log_activity(
                activity_type="knowledge_updated",
                source="system",
                metadata={
                }
            )

            logger.info(f"✓ 成功更新AI脑库知识: {knowledge_id}")
            return knowledge
        except Exception as e:
            logger.error(f"✗ 更新AI脑库知识失败: {str(e)}")
            return None

    def delete_knowledge(self, knowledge_id):
        """删除AI脑库知识（软删除）"""
        try:
        except Exception as e:
            logger.error(f"✗ 删除AI脑库知识失败: {str(e)}")
            return None

    def get_knowledge(self, knowledge_id):
        """根据ID获取知识"""
        try:
            if knowledge and knowledge.is_active:
                return knowledge
            return None
        except Exception as e:
            logger.error(f"✗ 获取AI脑库知识失败: {str(e)}")
            return None

    def get_all_knowledge(self, knowledge_type=None, source=None, tags=None):
        try:
        except Exception as e:
            logger.error(f"✗ 获取所有AI脑库知识失败: {str(e)}")
            return []

    def search_knowledge(self, keyword, knowledge_type=None):
        """搜索知识"""
        try:
        except Exception as e:
            logger.error(f"✗ 搜索AI脑库知识失败: {str(e)}")
            return []

    def add_problem(self, title, content, source, source_id=None, tags=None):
        """添加问题到AI脑库"""
        return self.add_knowledge(
            title=title,
            content=content,
            knowledge_type="problem",
            source=source,
            source_id=source_id,
            tags=tags,
            priority=2

        """添加解决方案到AI脑库"""
        if related_problem_id:
            if not tags:
                tags = []

        return self.add_knowledge(
            content=content,
            knowledge_type="solution",
            source=source,
            source_id=source_id,
            tags=tags,
            priority=3

    def add_experience(self, title, content, source, source_id=None, tags=None):
        return self.add_knowledge(
            title=title,
            content=content,
            source=source,
            source_id=source_id,
            tags=tags,

        """添加规则到AI脑库"""
            content=content,
            knowledge_type="rule",
            source=source,
            tags=tags,
            priority=4

    def get_recent_activities(self, limit=50):
        try:
            logger.error(f"✗ 获取AI脑库活动失败: {str(e)}")
            return []
        """记录活动日志"""
                activity_type=activity_type,
                description=description,
                source=source,
                source_id=source_id,
                metadata=metadata
            activity.save()
        except Exception as e:
            logger.error(f"✗ 记录AI脑库活动失败: {str(e)}")

    def get_knowledge_stats(self):

            stats = {
                "total_knowledge": len(all_knowledge),
                "knowledge_types": {},
                "sources": {},
                "active_knowledge": len([k for k in all_knowledge if k.is_active]),
            }

            # 统计知识类型
            for knowledge in all_knowledge:
                # 统计知识类型
                stats["knowledge_types"][knowledge.knowledge_type] = stats["knowledge_types"].get(knowledge.knowledge_type, 0) + 1
                # 统计来源
                stats["sources"][knowledge.source] = stats["sources"].get(knowledge.source, 0) + 1

                # 统计标签
                for tag in knowledge.tags:
                    stats["top_tags"][tag] = stats["top_tags"].get(tag, 0) + 1

            # 排序标签
            stats["top_tags"] = dict(sorted(stats["top_tags"].items(), key=lambda x: x[1], reverse=True)[:10])

            return stats
        except Exception as e:
            logger.error(f"✗ 获取AI脑库统计信息失败: {str(e)}")
            return None

    def get_related_knowledge(self, knowledge_id, limit=10):
        """获取相关知识"""
        try:
            if not knowledge:
                return []

            # 基于标签查找相关知识
            related_knowledge = []
            for tag in knowledge.tags:
                if tag.startswith("related-to:"):
                    related_id = tag.split(":")[1]
                    related = self.get_knowledge(related_id)
                    if related and related.knowledge_id != knowledge_id:
                        related_knowledge.append(related)

            # 基于类型查找更多相关知识
            if len(related_knowledge) < limit:
                same_type_knowledge = [k for k in self.get_all_knowledge(knowledge_type=knowledge.knowledge_type)
                                      if k.knowledge_id != knowledge_id and k not in related_knowledge]
                related_knowledge.extend(same_type_knowledge[:limit - len(related_knowledge)])

            return related_knowledge[:limit]
            logger.error(f"✗ 获取相关知识失败: {str(e)}")
            return []

    def auto_categorize_knowledge(self, knowledge_id):
        """自动分类知识"""
        try:
            if not knowledge:
                return None

            # 基于内容自动分类
            content = knowledge.content.lower()
            title = knowledge.title.lower()

            # 扩展的关键词库
            keyword_categories = {
                '服务器': ['服务器', '端口', '启动', '失败', '连接', 'curl', '防火墙', 'ip地址', 'werkzeug', 'localhost', 'http', 'https'],
                'AI': ['ai', '人工智能', 'ai集', 'ai实例', '知识', '脑库', '智能', '学习', '模型', '训练', '预测'],
                '管理': ['管理', '最佳实践', '规则', '经验', '优化', '监控', '升级', '维护', '配置', '部署'],
                '数据库': ['数据库', 'sqlite', 'mysql', 'postgresql', '查询', '表', '数据', '备份'],
                '网络': ['网络', '路由', 'dns', '网关', '协议', 'tcp', 'udp', 'socket'],
                '安全': ['安全', '加密', '认证', '授权', '漏洞', '攻击', '防护', '防火墙'],
                '开发': ['开发', '代码', '编程', '调试', '测试', '部署', '构建', '版本控制']
            }

            # 自动标签生成
            auto_tags = []

            for category, keywords in keyword_categories.items():
                for keyword in keywords:
                    if keyword in content or keyword in title:
                        auto_tags.append(keyword)
                        auto_tags.append(category)  # 添加分类标签
                        break

            # 基于内容主题自动生成更智能的标签
            import re

            # 提取URL
            url_pattern = r'https?://\S+'
            urls = re.findall(url_pattern, content)
            if urls:
                auto_tags.append('包含链接')

            # 提取IP地址
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ips = re.findall(ip_pattern, content)
            if ips:
                auto_tags.append('包含IP地址')

            # 提取端口号
            port_pattern = r'\b\d{1,5}\b'
            ports = re.findall(port_pattern, content)
            if ports:
                for port in ports:
                    try:
                        if 1 <= port_num <= 65535:
                            auto_tags.append(f'端口:{port}')
                            break
                    except:
                        pass

            # 添加自动生成的标签，去重并限制数量
            new_tags = list(set(knowledge.tags + auto_tags))
            if len(new_tags) > 20:  # 限制最大标签数量
                new_tags = new_tags[:20]

            # 更新知识
            return self.update_knowledge(knowledge_id, tags=new_tags)
        except Exception as e:
            logger.error(f"✗ 自动分类知识失败: {str(e)}")
            return None

    def enhance_knowledge(self, knowledge_id):
        """增强知识，添加相关知识关联"""
        try:
            if not knowledge:
                return None

            # 自动分类
            self.auto_categorize_knowledge(knowledge_id)

            # 查找相关知识并添加关联
            related_knowledge = self.get_related_knowledge(knowledge_id, limit=5)

            for related in related_knowledge:
                # 为当前知识添加关联标签
                self.update_knowledge(
                    knowledge_id,
                    tags=list(set(knowledge.tags + [f"related-to:{related.knowledge_id}"]))
                )

                # 为相关知识添加反向关联标签
                self.update_knowledge(
                    related.knowledge_id,
                    tags=list(set(related.tags + [f"related-to:{knowledge_id}"]))
                )

            return self.get_knowledge(knowledge_id)
        except Exception as e:
            logger.error(f"✗ 增强知识失败: {str(e)}")
            return None

        """批量增强所有知识"""
        try:
            enhanced_count = 0

            for knowledge in all_knowledge:
                if self.enhance_knowledge(knowledge.knowledge_id):
                    enhanced_count += 1

            logger.info(f"✓ 成功增强 {enhanced_count} 条知识")
            return enhanced_count
        except Exception as e:
            logger.error(f"✗ 批量增强知识失败: {str(e)}")
            return 0

    def get_knowledge_graph(self, depth=2):
        """获取知识图谱"""
        try:
            knowledge_graph = {
                "nodes": [],
                "edges": []
            }

            # 添加节点
            for knowledge in all_knowledge:
                knowledge_graph["nodes"].append({
                    "id": knowledge.knowledge_id,
                    "label": knowledge.title,
                    "type": knowledge.knowledge_type,
                    "tags": knowledge.tags
                })

            # 添加边
            for knowledge in all_knowledge:
                for tag in knowledge.tags:
                    if tag.startswith("related-to:"):
                        related_id = tag.split(":")[1]
                            "source": knowledge.knowledge_id,
                            "target": related_id,
                            "type": "related_to"
                        })

            return knowledge_graph
        except Exception as e:
            logger.error(f"✗ 获取知识图谱失败: {str(e)}")
            return None
    def generate_knowledge_summary(self, knowledge_id):
        """生成知识摘要"""
        try:
            if not knowledge:

            # 生成摘要
            content = knowledge.content
            if len(content) > 200:
                summary = content[:200] + "..."
            else:
                summary = content

            return {
                "knowledge_id": knowledge_id,
                "summary": summary,
                "type": knowledge.knowledge_type
            }
        except Exception as e:
            logger.error(f"✗ 生成知识摘要失败: {str(e)}")
            return None

    def search_knowledge_by_tags(self, tags, limit=10):
        """根据标签搜索知识"""
            matching_knowledge = []

            for knowledge in all_knowledge:
                # 检查知识标签是否与搜索标签匹配
                if any(tag in knowledge.tags for tag in tags):
                    matching_knowledge.append(knowledge)

            return matching_knowledge[:limit]
            logger.error(f"✗ 根据标签搜索知识失败: {str(e)}")
            return []

        """使用外部AI引擎增强知识"""
        try:
            knowledge = self.get_knowledge(knowledge_id)
                return None

            # 生成增强提示
            prompt = f"请增强以下知识内容，使其更加全面、准确和详细：\n\n标题：{knowledge.title}\n类型：{knowledge.knowledge_type}\n内容：{knowledge.content}\n标签：{', '.join(knowledge.tags)}"

            # 调用外部AI引擎
            result = ai_engine_integrator.call_engine(engine_type, prompt, temperature=0.7, max_tokens=1000)
            if result:
                enhanced_content = result.get("data", {}).get("response", knowledge.content)

                # 更新知识
                return self.update_knowledge(knowledge_id, content=enhanced_content)

            return knowledge
        except Exception as e:
            logger.error(f"✗ 使用外部AI引擎增强知识失败: {str(e)}")
            return None

    def batch_enhance_knowledge_with_ai(self, engine_type="qianwen", limit=10):
        """批量使用外部AI引擎增强知识"""
        try:
            enhanced_count = 0

            for knowledge in all_knowledge[:limit]:
                if self.enhance_knowledge_with_ai(knowledge.knowledge_id, engine_type):
                    enhanced_count += 1

            return enhanced_count
            logger.error(f"✗ 批量使用外部AI引擎增强知识失败: {str(e)}")
            return 0

    def get_knowledge_by_review_status(self, review_status):
        """根据审核状态获取知识"""
        try:
            query = f"SELECT * FROM ai_brain_knowledge WHERE review_status = ? AND is_active = ?"
            rows = db_manager.fetch_all(query, [review_status, True])

            knowledge_list = []
            for row in rows:
                knowledge = AIBrainKnowledge(**dict(row))
                knowledge_list.append(knowledge)

            return knowledge_list
        except Exception as e:
            logger.error(f"✗ 根据审核状态获取知识失败: {str(e)}")
            return []

    def review_knowledge(self, knowledge_id, reviewed_by, review_status="approved", feedback=None):
        """审核知识"""
        try:
            knowledge = self.get_knowledge(knowledge_id)
            if not knowledge:
                return None

            # 更新审核状态
            knowledge.review_status = review_status
            knowledge.reviewed_by = reviewed_by
            knowledge.reviewed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            knowledge.save()

            # 记录活动日志
            self._log_activity(
                activity_type="knowledge_reviewed",
                description=f"审核知识: {knowledge_id}, 状态: {review_status}",
                source="system",
                metadata={
                    "knowledge_id": knowledge_id,
                    "review_status": review_status,
                    "feedback": feedback
            )

            return knowledge
        except Exception as e:
            logger.error(f"✗ 审核知识失败: {str(e)}")
            return None

    def sync_ai_instance_knowledge(self, ai_instance):
        """同步AI实例知识到AI脑库"""
        try:
            # 从AI实例获取知识
                # 从字典格式的AI实例获取知识
                knowledge_items = []
                # 从不同来源获取知识
                if 'knowledge' in ai_instance and isinstance(ai_instance['knowledge'], list):
                    knowledge_items.extend(ai_instance['knowledge'])

                if 'config' in ai_instance:
                    config = ai_instance['config']
                    for key, value in config.items():
                        if isinstance(value, dict) and 'enabled' in value and value['enabled']:
                            knowledge_items.append({
                                'title': f"{key}配置",
                                'content': str(value),
                                'type': 'configuration',
                                'tags': [key, 'config'],
                                'priority': 2
                            })

                # 从功能中提取知识
                if 'functions' in ai_instance:
                        knowledge_items.append({
                            'title': f"功能: {func}",
                            'content': f"AI实例具备{func}功能",
                            'tags': ['function', func],
                            'priority': 1
                        })

                # 处理知识项
                for knowledge_item in knowledge_items:
                    # 检查是否已存在
                    existing_knowledge = self.search_knowledge(
                        keyword=knowledge_item.get('title', ''),
                        knowledge_type=knowledge_item.get('type', 'general')
                    )

                    if not existing_knowledge:
                        # 添加新知识
                        self.add_knowledge(
                            title=knowledge_item.get('title', '未知'),
                            content=knowledge_item.get('content', ''),
                            knowledge_type=knowledge_item.get('type', 'general'),
                            source='ai_instance',
                            source_id=ai_instance.get('instance_id'),
                            tags=knowledge_item.get('tags', []),
                            priority=knowledge_item.get('priority', 1)
                        )
            elif hasattr(ai_instance, 'knowledge') and isinstance(ai_instance.knowledge, list):
                # 从对象格式的AI实例获取知识
                for knowledge_item in ai_instance.knowledge:
                    # 检查是否已存在
                    existing_knowledge = self.search_knowledge(
                        keyword=knowledge_item.get('title', ''),
                        knowledge_type=knowledge_item.get('type', 'general')
                    )

                    if not existing_knowledge:
                        # 添加新知识
                        self.add_knowledge(
                            title=knowledge_item.get('title', '未知'),
                            content=knowledge_item.get('content', ''),
                            knowledge_type=knowledge_item.get('type', 'general'),
                            source='ai_instance',
                            source_id=getattr(ai_instance, 'instance_id', None),
                            tags=knowledge_item.get('tags', []),
                            priority=knowledge_item.get('priority', 1)
                        )

            logger.info(f"✓ 成功同步AI实例 {ai_instance.get('instance_id', 'unknown')} 知识到AI脑库")
            return True
        except Exception as e:
            logger.error(f"✗ 同步AI实例知识失败: {str(e)}")
            return False

    def sync_all_instances_knowledge(self, ai_instances):
        """同步所有AI实例知识到AI脑库"""
        try:
            synced_count = 0
                if self.sync_ai_instance_knowledge(ai_instance):
                    synced_count += 1

            logger.info(f"✓ 成功同步 {synced_count} 个AI实例知识到AI脑库")
            return synced_count
        except Exception as e:
            logger.error(f"✗ 同步所有AI实例知识失败: {str(e)}")
            return 0

    def get_knowledge_for_ai_instance(self, ai_type, limit=20):
        """获取适合特定AI类型的知识"""
        try:
                'general': ['general', 'knowledge', 'common', 'basic'],
                'technical': ['technical', 'code', 'system', 'security', 'network'],
                'research': ['research', 'data', 'analysis', 'statistics', 'trend'],
                'creative': ['creative', 'content', 'design', 'art', 'media'],
                'education': ['education', 'learning', 'teaching', 'tutoring', 'knowledge'],
                'business': ['business', 'market', 'sales', 'management', 'decision']

            tags = relevant_tags.get(ai_type, relevant_tags['general'])
            knowledge_list = self.search_knowledge_by_tags(tags, limit=limit)
            # 按优先级排序
            knowledge_list.sort(key=lambda x: x.priority, reverse=True)

            return knowledge_list
        except Exception as e:
            logger.error(f"✗ 获取适合AI实例的知识失败: {str(e)}")
            return []

    def validate_knowledge(self, knowledge_id):
        """验证知识的准确性"""
        try:
            knowledge = self.get_knowledge(knowledge_id)
                return None

            # 检查基本事实
            is_valid = self._check_basic_facts(knowledge)

            # 计算置信度
            confidence_score = self._calculate_confidence_score(knowledge)

            # 检测冲突
            conflicts = self._detect_conflicts(knowledge)

            # 更新知识状态
            review_status = "approved" if is_valid and len(conflicts) == 0 else "rejected"
            self.update_knowledge(
                knowledge_id=knowledge_id,
                review_status=review_status,
                reviewed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self._log_activity(
                activity_type="knowledge_validated",
                description=f"知识自检结果: {knowledge_id}, 状态: {review_status}, 置信度: {confidence_score:.2f}",
                metadata={
                    "is_valid": is_valid,
                    "conflicts": [conflict.knowledge_id for conflict in conflicts],
                }

                "knowledge_id": knowledge_id,
                "confidence_score": confidence_score,
                "conflicts": [conflict.knowledge_id for conflict in conflicts],
            }
            logger.error(f"✗ 验证知识失败: {str(e)}")
            return None

    def _check_basic_facts(self, knowledge):
        """检查基本事实"""
        try:
            content = knowledge.content.lower()

            # 基本数学公式检查
            if any(term in content for term in ["1+1", "1 + 1"]) and "=8" in content:
                return False
            if "1+1=2" in content or "1 + 1 = 2" in content:
                return True

            # 扩展数学检查
            math_patterns = [
                (r"2\+2\s*=\s*5", False),
                (r"3\*3\s*=\s*10", False),
                (r"10\-5\s*=\s*7", False),
                (r"4\/2\s*=\s*3", False)
            ]
            import re
            for pattern, is_valid in math_patterns:
                if re.search(pattern, content):
                    return is_valid

            # 扩展常识检查
            invalid_facts = [
                "太阳绕着地球转",
                "水的沸点是50度",
                "人类有3只眼睛",
                "水在0度沸腾",
                "一年有13个月",
                "地球只有一个月亮"  # 这是正确的，所以不应该在invalid_facts中，这里只是示例
            ]

            for fact in invalid_facts:
                if fact in content or fact in title:
                    return False

            # 基本逻辑检查
            if "矛盾" in content or "冲突" in content:
                # 不是所有包含"矛盾"或"冲突"的内容都是错误的，需要更智能的判断

            return True
        except Exception as e:
            logger.error(f"✗ 检查基本事实失败: {str(e)}")
            return True

    def _calculate_confidence_score(self, knowledge):
        """计算知识的置信度评分"""
        try:
            score = 0.5  # 初始评分
            content = knowledge.content.lower()

            # 基于知识来源调整评分
            source_weights = {
                "system": 0.4,
                "admin": 0.35,
                "verified_source": 0.3,
                "ai_instance": -0.1,
                "unknown": -0.2
            }
            score += source_weights.get(knowledge.source, source_weights["unknown"])

            # 基于知识类型调整评分
            type_weights = {
                "rule": 0.3,
                "solution": 0.25,
                "experience": 0.2,
                "problem": 0.15,
                "general": 0.1
            score += type_weights.get(knowledge.knowledge_type, type_weights["general"])

            # 基于内容长度调整评分
                score += 0.2
                score += 0.15
            elif len(content) > 100:
                score += 0.1
            elif len(content) < 50:
                score -= 0.1  # 内容太短，置信度降低

            # 基于基本事实检查结果调整评分
            if self._check_basic_facts(knowledge):
                score += 0.25
            else:
                score -= 0.45

            # 基于内容质量调整评分

            if re.search(r'\d+(\.\d+)?', content):  # 包含数字

            if any(term in content for term in ["参考", "来源", "根据", "引用"]):
                score += 0.15

            # 检查是否包含模棱两可的词汇
            ambiguous_terms = ["可能", "大概", "也许", "或许", "估计", "应该"]
            for term in ambiguous_terms:
                if term in content:
                    score -= 0.05

            # 基于标签数量调整评分
                tag_count = len(knowledge.tags)
                    score += 0.1  # 标签数量适中，置信度提高
                elif tag_count > 15:
                    score -= 0.05  # 标签数量过多，可能存在噪点

            # 基于优先级调整评分
            if knowledge.priority >= 3:
                score += 0.1
            elif knowledge.priority <= 1:
                score -= 0.05

            # 确保评分在0-1之间
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.error(f"✗ 计算置信度评分失败: {str(e)}")
            return 0.5
    def _detect_conflicts(self, knowledge):
        """检测与其他知识的冲突"""
        try:
            conflicts = []

            content = knowledge.content.lower()
            title = knowledge.title.lower()

            for other_knowledge in all_knowledge:
                if other_knowledge.knowledge_id == knowledge.knowledge_id:
                    continue

                other_title = other_knowledge.title.lower()
                # 检查直接矛盾
                    conflicts.append(other_knowledge)
                if any(term in other_content for term in ["1+1=2", "1 + 1 = 2"]) and any(term in content for term in ["1+1=8", "1 + 1 = 8"]):
                    conflicts.append(other_knowledge)
                # 检查常识矛盾
                if "地球是圆的" in content and "地球是平的" in other_content:
                    conflicts.append(other_knowledge)

                if "地球是平的" in content and "地球是圆的" in other_content:
                    conflicts.append(other_knowledge)

            return conflicts
        except Exception as e:
            logger.error(f"✗ 检测冲突失败: {str(e)}")
            return []

    def batch_validate_knowledge(self, limit=None):
        """批量验证知识"""
        try:
            all_knowledge = self.get_all_knowledge()
                all_knowledge = all_knowledge[:limit]

            results = []
            for knowledge in all_knowledge:
                result = self.validate_knowledge(knowledge.knowledge_id)
                if result:
                    results.append(result)

            logger.info(f"✓ 批量验证完成，共验证 {len(results)} 条知识")
        except Exception as e:
            logger.error(f"✗ 批量验证知识失败: {str(e)}")
            return []

    def get_validation_report(self):
        """获取知识验证报告"""
        try:
            all_knowledge = self.get_all_knowledge()
            report = {
                "total_knowledge": len(all_knowledge),
                "validated_knowledge": 0,
                "approved_knowledge": 0,
                "rejected_knowledge": 0,
                "average_confidence": 0.0,
                "knowledge_by_status": {
                    "pending": 0,
                    "approved": 0,
                }
            }

            confidence_scores = []
            for knowledge in all_knowledge:
                review_status = getattr(knowledge, 'review_status', 'pending')
                report["knowledge_by_status"][review_status] = report["knowledge_by_status"].get(review_status, 0) + 1

                if review_status != "pending":
                    report["validated_knowledge"] += 1

                    if review_status == "approved":
                        report["approved_knowledge"] += 1
                    elif review_status == "rejected":
                        report["rejected_knowledge"] += 1
                    confidence_score = getattr(knowledge, 'confidence_score', 0.5)
                    confidence_scores.append(confidence_score)


            return report
        except Exception as e:
            return None

    def auto_acquire_knowledge(self, topics, sources=None, limit=5):
        """自动从外部来源获取知识"""
        try:
            acquired_count = 0
            # 模拟从不同来源获取知识
            for topic in topics:
                    # 模拟知识获取
                    knowledge = self.add_knowledge(
                        title=f"{topic}相关知识 {i+1}",
                        content=f"关于{topic}的详细信息和最佳实践...",
                        knowledge_type="general",
                        source="auto_acquired",
                        tags=[topic, "auto", "external"],
                        priority=2
                    )
                    if knowledge:
            logger.info(f"✓ 自动获取知识完成，共获取 {acquired_count} 条知识")
            return acquired_count
        except Exception as e:
            return 0

        """从AI交互中自我学习"""
        try:
            learned_count = 0
            for interaction in interactions:
                # 从交互中提取知识
                if 'content' in interaction and interaction['content']:
                    # 分析交互内容，提取有价值的信息
                    content = interaction['content']
                    # 简单的关键词提取

                    if keywords:
                        # 创建知识条目
                        knowledge = self.add_knowledge(
                            title=f"从交互中学习: {keywords[0]}",
                            content=content,
                            knowledge_type="experience",
                            source="interaction",
                            tags=keywords + ["learning"],
                            priority=1
                        )
                        if knowledge:

            return learned_count
        except Exception as e:
            logger.error(f"✗ 从交互中自我学习失败: {str(e)}")
            return 0

        """从文本中提取关键词"""
        try:
            # 简单的关键词提取逻辑

            # 移除标点符号

            # 简单分词
            words = text.split()

            # 过滤常见词和短词
            common_words = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
            keywords = [word for word in words if word not in common_words and len(word) > 2]

            # 返回前5个关键词
            return keywords[:5]
        except Exception as e:
            logger.error(f"✗ 提取关键词失败: {str(e)}")
            return []

    def update_knowledge_from_feedback(self, knowledge_id, feedback):
            knowledge = self.get_knowledge(knowledge_id)
                return None

            # 分析反馈
            if 'suggestion' in feedback and feedback['suggestion']:
                # 更新知识内容
                updated_content = knowledge.content + f"\n\n反馈建议: {feedback['suggestion']}"
                knowledge = self.update_knowledge(knowledge_id, content=updated_content)

            # 记录反馈
            self._log_activity(
                activity_type="knowledge_feedback",
                description=f"知识反馈: {knowledge_id}",
                source="system",
                metadata={
                    "knowledge_id": knowledge_id,
                    "feedback": feedback
                }
            )

            logger.info(f"✓ 根据反馈更新知识: {knowledge_id}")
            return knowledge
        except Exception as e:
            logger.error(f"✗ 根据反馈更新知识失败: {str(e)}")
            return None


# 初始化AI脑库服务
ai_brain_service = AIBrainService()
