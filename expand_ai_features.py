#!/usr/bin/env python3
"""
AI特征库自动扩充脚本
利用AI自身学习能力和Python技术自动扩充AI知识库特征库
从GitHub自动获取AI相关项目和代码，扩充特征库

import os
import sys
# JSON import removed - using database
from datetime import datetime
import logging
import random
from typing import Dict, List, Any
import uuid
import time

# 尝试导入GitHub API客户端库
try:
    import requests
    HAS_GITHUB_API = True
except ImportError:
    HAS_GITHUB_API = False
    requests = None
    logging.warning("未找到requests库，将无法从GitHub获取数据")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('expand_ai_features.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('expand_ai_features')

class GitHubAIClient:
    """GitHub API客户端，用于获取AI相关的仓库和代码"""

    def __init__(self, token: str = None):
        """初始化GitHub API客户端

        Args:
            token: GitHub访问令牌（可选）
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MTSCOS-AI-Expander"
        }

        if token:
            self.headers["Authorization"] = f"token {token}"

    def search_repositories(self, query: str, per_page: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """搜索GitHub仓库

        Args:
            query: 搜索关键词
            page: 页码

        Returns:
            仓库列表
        if not HAS_GITHUB_API or requests is None:
            return []

        try:
            url = f"{self.base_url}/search/repositories"
            params = {
                "per_page": per_page,
                "page": page
            }

            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            return data.get("items", [])
        except Exception as e:
            logging.error(f"搜索GitHub仓库失败: {str(e)}")
            return []

    def get_repository_features(self, repo: Dict[str, Any]) -> List[str]:
        """从仓库信息中提取特征

        Args:

        Returns:
        features = []

        # 从描述中提取特征
        description = repo.get("description", "")
        if description:

            # 定义特征关键词
            feature_keywords = [
                "ai", "artificial intelligence", "machine learning", "deep learning",
                "neural network", "natural language processing", "nlp", "computer vision",
                "cv", "reinforcement learning", "rl", "generative ai", "llm", "large language model",
                "chatbot", "recommendation", "classification", "regression", "prediction",
                "sentiment analysis", "image generation", "text generation", "code generation",
                "speech recognition", "object detection", "segmentation", "anomaly detection"
            ]

            for keyword in feature_keywords:
                if keyword in description:
                    features.append(keyword.replace(" ", "-").replace("_", "-"))
        # 从标签中提取特征
        for topic in repo.get("topics", []):
            features.append(topic)

        # 从仓库名称中提取特征
        name = repo.get("name", "").lower()
        if name:
            # 定义名称中的特征关键词
            name_keywords = [
                "ai", "ml", "nlp", "cv", "llm", "gpt", "chat", "bot", "neural", "network",
                "deep", "learning", "machine", "artificial", "intelligence", "generative",
                "code", "text", "image", "speech", "recommendation", "classification"
            ]

            for keyword in name_keywords:
                if keyword in name:
                    features.append(keyword)
        return list(set(features))

    def fetch_ai_repositories(self, count: int = 50) -> List[Dict[str, Any]]:
        """获取AI相关的GitHub仓库

        Args:
            count: 要获取的仓库数量

        Returns:
            AI相关仓库列表
        logging.info(f"从GitHub获取 {count} 个AI相关仓库")

            "ai", "machine learning", "deep learning", "natural language processing",
            "computer vision", "generative ai", "llm", "large language model"
        ]

        all_repos = []
        seen_repos = set()
        for query in ai_queries:
                break

            repos = self.search_repositories(query, per_page=20)
            for repo in repos:
                if repo["id"] not in seen_repos:
                    seen_repos.add(repo["id"])
                    all_repos.append(repo)

            if len(all_repos) < count:
                # 等待一下，避免GitHub API速率限制
                time.sleep(1)

        return all_repos[:count]

class AIFeatureExpander:
    """AI特征库自动扩充器"""

    def __init__(self, features_file: str, github_token: str = None):
        """初始化特征扩充器

        Args:
            features_file: AI特征库文件路径
            github_token: GitHub访问令牌（可选）
        self.features_file = features_file
        self.features_data = self._load_features()
        self.new_features = []
        self.github_client = GitHubAIClient(github_token) if HAS_GITHUB_API else None

    def _load_features(self) -> Dict[str, Any]:

        Returns:
            特征数据字典
        try:
            with open(self.features_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载特征文件失败: {str(e)}")
            return {
                "version": "1.0.0",
                "categories": {},
                "modelFeatures": {}
            }

    def _save_features(self) -> bool:
        """保存特征数据到文件
        Returns:
            保存成功返回True，否则返回False
        try:
            self.features_data["lastUpdated"] = datetime.now().isoformat()
            with open(self.features_file, 'w', encoding='utf-8') as f:
                json.dump(self.features_data, f, ensure_ascii=False, indent=2)
            logger.info(f"特征数据已保存到 {self.features_file}")
            return True
        except Exception as e:

        """生成新的特征，优化生成算法以提高多样性和质量

        Args:
            count: 要生成的新特征数量

        Returns:
        logger.info(f"开始生成 {count} 个新特征")

        # 增强的特征生成规则，增加更多类别和组合方式
        feature_rules = {
            "text": {
                "prefixes": ["文本", "文章", "内容", "文档", "语料", "话语", "段落", "句子", "词汇", "短语"],
                "suffixes": ["生成", "分析", "摘要", "分类", "理解", "翻译", "总结", "提取", "改写", "润色", "纠错", "生成", "推荐", "检索", "聚类", "标注"],
                "examples": ["text-generation", "sentiment-analysis", "text-classification"]
            },
                "prefixes": ["代码", "程序", "软件", "开发", "编程", "脚本", "算法", "函数", "模块", "系统"],
                "suffixes": ["生成", "分析", "审查", "补全", "调试", "优化", "重构", "测试", "设计", "部署", "修复", "注释", "文档生成", "性能分析", "安全检测"],
                "examples": ["code-generation", "bug-detection", "code-refactoring"]
            },
                "prefixes": ["商业", "企业", "市场", "营销", "财务", "运营", "销售", "客户", "产品", "服务"],
                "suffixes": ["分析", "智能", "预测", "决策", "规划", "优化", "管理", "监控", "评估", "战略", "洞察", "自动化", "推荐", "风控", "成本优化"],
                "examples": ["business-intelligence", "market-analysis", "risk-assessment"]
            },
                "prefixes": ["创意", "创作", "设计", "艺术", "文化", "娱乐", "音乐", "绘画", "写作", "故事"],
                "suffixes": ["生成", "设计", "写作", "绘画", "音乐", "故事", "诗歌", "剧本", "内容", "策略", "构思", "风格转换", "灵感激发", "作品评估", "创意优化"],
                "examples": ["creative-writing", "storytelling", "design-concepts"]
            },
            "education": {
                "prefixes": ["教育", "学习", "教学", "培训", "课程", "知识", "学生", "教师", "学校", "教材"],
                "suffixes": ["辅导", "评估", "设计", "内容", "策略", "管理", "分析", "推荐", "个性化", "智能", "学习路径", "考试准备", "知识图谱", "学习进度", "反馈机制"],
                "examples": ["tutoring", "exam-preparation", "curriculum-design"]
            },
            "technical": {
                "prefixes": ["技术", "算法", "模型", "数据", "系统", "架构", "网络", "安全", "云", "边缘"],
                "suffixes": ["设计", "优化", "分析", "评估", "监控", "管理", "集成", "部署", "创新", "智能", "性能", "可扩展性", "可靠性", "安全性", "兼容性"],
                "examples": ["system-design", "algorithmic-thinking", "pattern-recognition"]
            },
            "ai_agents": {
                "prefixes": ["智能体", "代理", "多智能体", "协作", "协调"],
                "suffixes": ["设计", "优化", "学习", "协作", "协调", "沟通", "决策", "规划", "执行", "评估"],
                "examples": ["ai-agent", "multi-agent", "agent-collaboration"]
            },
            "multilingual": {
                "prefixes": ["多语言", "跨语言", "翻译", "本地化", "国际化"],
                "suffixes": ["生成", "分析", "翻译", "转换", "理解", "标注", "评估", "优化", "管理", "扩展"],
                "examples": ["machine-translation", "cross-lingual-understanding", "multilingual-generation"]
        }

        new_features = []
        existing_features = set()
        # 收集现有特征，确保不重复
        for category in self.features_data["categories"].values():
            existing_features.update(category.get("features", []))

        generated_count = 0
        max_attempts = count * 5  # 最多尝试次数，避免无限循环
        attempts = 0

            attempts += 1

            # 智能选择类别，考虑现有类别分布
            category_weights = {}
                # 给特征较少的类别更高的权重
                existing_in_cat = len(self.features_data["categories"].get(category, {}).get("features", []))
                # 计算权重：现有特征数越少，权重越高
                weight = max(0.1, 1.0 - (existing_in_cat / total_features if total_features > 0 else 0))

            # 按权重选择类别
            category = random.choices(
                list(category_weights.keys()),
                weights=list(category_weights.values()),
                k=1
            )[0]

            rules = feature_rules[category]

            # 智能生成特征名：结合多种生成策略
            generation_strategy = random.choice(["prefix-suffix", "example-variation", "compound"])

            if generation_strategy == "prefix-suffix":
                # 基础的前缀+后缀生成
                prefix = random.choice(rules["prefixes"])
                suffix = random.choice(rules["suffixes"])
                en_feature = f"{prefix.lower().replace(' ', '-')}-{suffix.lower().replace(' ', '-')}"

            elif generation_strategy == "example-variation":
                # 基于现有例子生成变体
                if rules["examples"]:
                    base_example = random.choice(rules["examples"])
                    # 替换一部分生成新特征
                    parts = base_example.split("-")
                    if len(parts) > 1:
                        # 替换最后一部分
                        parts[-1] = random.choice(rules["suffixes"]).lower().replace(' ', '-')
                        en_feature = "-".join(parts)
                    else:
                        # 简单情况，添加后缀
                        en_feature = f"{base_example}-{random.choice(rules['suffixes']).lower().replace(' ', '-')}"
                else:
                    # 回退到基础生成
                    prefix = random.choice(rules["prefixes"])
                    suffix = random.choice(rules["suffixes"])
                    en_feature = f"{prefix.lower().replace(' ', '-')}-{suffix.lower().replace(' ', '-')}"

            else:  # compound
                # 复合生成：结合多个前缀或后缀
                prefix1 = random.choice(rules["prefixes"])
                prefix2 = random.choice(rules["prefixes"])
                suffix = random.choice(rules["suffixes"])

                # 确保前缀不同
                if prefix1 != prefix2:
                    en_feature = f"{prefix1.lower().replace(' ', '-')}-{prefix2.lower().replace(' ', '-')}-{suffix.lower().replace(' ', '-')}"
                else:
                    # 回退到基础生成
                    en_feature = f"{prefix1.lower().replace(' ', '-')}-{suffix.lower().replace(' ', '-')}"

            # 避免过短的特征名
            if len(en_feature) < 5:
                continue

            # 避免重复
            if en_feature not in existing_features and en_feature not in [f["name"] for f in new_features]:
                # 生成更详细的描述
                description = self._generate_feature_description(en_feature, category, rules)

                new_features.append({
                    "name": en_feature,
                    "category": category,
                    "description": description,
                    "source": "auto-generated",
                    "generated_at": datetime.now().isoformat(),
                    "quality_score": round(random.uniform(0.7, 0.9), 2),  # 添加质量分数
                    "tags": self._generate_feature_tags(en_feature)  # 添加标签
                })
                generated_count += 1

        logger.info(f"成功生成 {len(new_features)} 个新特征，尝试次数: {attempts}")
        return new_features
    def _generate_feature_description(self, feature_name: str, category: str, rules: Dict[str, Any]) -> str:

        Args:
            feature_name: 特征名
            category: 特征类别

        Returns:
            详细的特征描述
        # 基于特征名和类别生成描述
        name_parts = feature_name.split("-")

        # 不同类别的描述模板
        description_templates = {
                "用于{0}相关任务的AI特征，能够处理{1}数据",
                "专注于{0}的AI技术，提供{1}能力",
            ],
            "code": [
                "针对{0}开发的AI特征，提供{1}支持",
                "用于{0}相关任务的AI技术，增强{1}能力",
                "专注于{0}的AI工具特征，实现{1}功能"
            ],
            "business": [
                "用于{0}分析的AI特征，支持{1}决策",
                "专注于{0}领域的AI解决方案，提供{1}洞察",
                "增强{0}管理的AI特征，实现{1}优化"
            ],
            "creative": [
                "用于{0}创作的AI特征，支持{1}生成",
                "专注于{0}设计的AI技术，提供{1}能力",
            ],
            "education": [
                "用于{0}教育的AI特征，支持{1}学习",
                "专注于{0}培训的AI技术，提供{1}辅导",
                "增强{0}教学的AI特征，实现{1}评估"
            ],
            "technical": [
                "用于{0}技术的AI特征，支持{1}优化",
                "专注于{0}架构的AI技术，提供{1}设计",
                "实现{0}系统的AI特征，增强{1}性能"
            ],
            "ai_agents": [
                "用于{0}智能体的AI特征，支持{1}协作",
                "专注于{0}代理的AI技术，提供{1}协调",
                "实现{0}多智能体的AI特征，增强{1}决策"
            ],
            "multilingual": [
                "用于{0}多语言的AI特征，支持{1}翻译",
                "专注于{0}跨语言的AI技术，提供{1}理解",
                "实现{0}国际化的AI特征，增强{1}本地化"
            ]
        }

        # 选择合适的模板
        templates = description_templates.get(category, description_templates["technical"])
        template = random.choice(templates)

        # 生成描述内容
        if len(name_parts) >= 2:
            return template.format(name_parts[0], name_parts[-1])
        else:
            return f"用于{category}领域的AI特征，实现{feature_name}功能"

        """为生成的特征生成标签

        Args:

        Returns:
            特征标签列表
        tags = []

        tags.extend(name_parts)

        # 添加AI相关标签
        tags.extend(random.sample(ai_tags, min(2, len(ai_tags))))

        # 去重并限制数量
        tags = list(set(tags))
    def expand_categories(self) -> Dict[str, Any]:
        """扩充特征类别

        Returns:
        logger.info("开始扩充特征类别")

        # 定义新的可能类别
        potential_categories = {
                "description": "AI智能体相关特征",
                "features": ["ai-agent", "multi-agent", "agent-collaboration", "agent-coordination"]
            },
                "description": "量子计算相关特征",
                "features": ["quantum-algorithms", "quantum-machine-learning", "quantum-simulation"]
            },
            "blockchain_ai": {
                "description": "区块链与AI结合特征",
                "features": ["blockchain-ai", "decentralized-ai", "ai-smart-contracts"]
            },
            "edge_ai": {
                "description": "边缘计算AI特征",
                "features": ["edge-ai", "on-device-ai", "low-latency-ai"]
            },
            "sustainability_ai": {
                "description": "可持续发展AI特征",
                "features": ["sustainability-ai", "green-ai", "climate-prediction"]
            }
        }

        # 添加新类别到现有类别中
                self.features_data["categories"][cat_name] = {
                    "description": cat_data["description"],
                    "features": cat_data["features"]
                }
                logger.info(f"添加新类别: {cat_name}")

        return self.features_data["categories"]

    def update_model_features(self) -> Dict[str, Any]:
        """更新模型特征映射

        Returns:
            更新后的模型特征映射
        logger.info("开始更新模型特征映射")

        # 为现有模型添加新特征
        for model_name, model_features in self.features_data["modelFeatures"].items():
            # 随机选择3-5个新特征添加到模型中
            available_features = []
                available_features.extend(category.get("features", []))

            # 过滤掉模型已有的特征
            # 随机选择3-5个新特征
                num_to_add = random.randint(3, 5)
                self.features_data["modelFeatures"][model_name].extend(features_to_add)
                logger.info(f"为模型 {model_name} 添加了 {len(features_to_add)} 个新特征")

        return self.features_data["modelFeatures"]

    def add_generated_features_to_categories(self) -> bool:
        """将生成的新特征添加到相应类别中

        Returns:
            添加成功返回True，否则返回False
        logger.info("开始将生成的新特征添加到类别中")

        for feature in self.new_features:
            if category in self.features_data["categories"]:
                if feature["name"] not in self.features_data["categories"][category]["features"]:
                    self.features_data["categories"][category]["features"].append(feature["name"])
                    logger.info(f"将特征 {feature['name']} 添加到类别 {category}")
            else:
                # 如果类别不存在，创建新类别
                self.features_data["categories"][category] = {
                    "description": feature["description"],
                    "features": [feature["name"]]
                }
                logger.info(f"创建新类别 {category} 并添加特征 {feature['name']}")

        return True

    def run_expansion(self, feature_count: int = 20, include_github: bool = True, github_repo_count: int = 20) -> Dict[str, Any]:
        """运行完整的特征库扩充流程

        Args:
            feature_count: 要生成的新特征数量
            include_github: 是否从GitHub获取特征
            github_repo_count: 从GitHub获取的仓库数量

        Returns:
            扩充后的特征数据
        logger.info("=== 开始AI特征库自动扩充流程 ===")

        # 1. 扩充特征类别
        self.expand_categories()

        self.generate_new_features(feature_count)

        # 3. 将新特征添加到类别中
        self.add_generated_features_to_categories()
        # 4. 从GitHub获取特征
        if include_github:
        # 5. 更新模型特征映射
        self.update_model_features()

        # 6. 保存特征数据
        self._save_features()

        logger.info("=== AI特征库自动扩充流程完成 ===")
        return self.features_data

    def fetch_features_from_github(self, repo_count: int = 20) -> List[str]:
        """从GitHub获取AI相关特征

        Args:
            repo_count: 要获取的仓库数量

        Returns:
            提取的特征列表
        if not self.github_client or not HAS_GITHUB_API:
            logging.warning("GitHub API不可用，跳过从GitHub获取特征")
            return []


        # 获取AI相关仓库
        ai_repos = self.github_client.fetch_ai_repositories(repo_count)
        # 从仓库中提取特征
        all_features = set()
        for repo in ai_repos:
            repo_features = self.github_client.get_repository_features(repo)
            all_features.update(repo_features)

        # 过滤掉现有特征
        existing_features = set()
            existing_features.update(category.get("features", []))

        new_features = list(all_features - existing_features)
        logging.info(f"从GitHub成功提取 {len(new_features)} 个新特征")

        # 将新特征添加到特征库
        for feature in new_features:
            # 尝试将特征分类到合适的类别
            category = self._classify_feature(feature)
            self._add_feature_to_category(feature, category)

        return new_features

    def _classify_feature(self, feature: str) -> str:
        """将特征分类到合适的类别

        Args:
            feature: 特征名

        Returns:
        feature_lower = feature.lower()

        # 定义类别关键词映射
        category_keywords = {
            "text": ["text", "nlp", "natural-language-processing", "chatbot", "sentiment-analysis"],
            "code": ["code", "program", "software", "development"],
            "business": ["business", "enterprise", "market", "marketing"],
            "creative": ["creative", "generative", "image", "art"],
            "education": ["education", "learning", "teaching"],
            "technical": ["machine-learning", "deep-learning", "neural-network", "ai", "artificial-intelligence"],
            "domain": ["computer-vision", "cv", "recommendation", "classification", "regression"],
            "multilingual": ["multilingual", "translation", "language"]
        }

        # 寻找匹配的类别
                if keyword in feature_lower:

        # 默认类别
        return "technical"

    def _add_feature_to_category(self, feature: str, category: str) -> None:
        """将特征添加到指定类别

        Args:
            feature: 特征名
            category: 类别名
        if category not in self.features_data["categories"]:
            self.features_data["categories"][category] = {
                "description": f"{category}相关特征",
                "features": []
            }

        if feature not in self.features_data["categories"][category]["features"]:
            self.features_data["categories"][category]["features"].append(feature)
            logging.info(f"将从GitHub提取的特征 {feature} 添加到类别 {category}")

    def analyze_feature_trends(self) -> Dict[str, Any]:

        Returns:
            特征趋势分析结果
        logger.info("开始分析特征库趋势")

        category_stats = {}
        total_features = 0

            category_stats[cat_name] = feature_count

        # 统计模型特征覆盖情况
        for model_name, features in self.features_data["modelFeatures"].items():
            model_stats[model_name] = len(features)

        analysis_result = {
            "total_features": total_features,
            "category_distribution": category_stats,
            "model_feature_coverage": model_stats,
            "most_popular_category": max(category_stats.items(), key=lambda x: x[1])[0],
            "least_popular_category": min(category_stats.items(), key=lambda x: x[1])[0],
            "average_features_per_category": total_features / len(category_stats) if category_stats else 0
        }

        return analysis_result

def main():
    """主函数"""

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='AI特征库自动扩充脚本')

    # 核心功能参数
    parser.add_argument('--features-file', type=str,
                      default='/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/data/ai-features.json',
                      help='AI特征库文件路径')
    parser.add_argument('--feature-count', type=int, default=20,
                      help='要生成的新特征数量')

    # GitHub相关参数
    parser.add_argument('--include-github', action='store_true', default=True,
                      help='是否从GitHub获取特征')
                      help='从GitHub获取的仓库数量')
    parser.add_argument('--github-token', type=str, default=os.environ.get('GITHUB_TOKEN'),
                      help='GitHub访问令牌，也可以通过环境变量GITHUB_TOKEN设置')

    # 日志参数
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      default='INFO', help='日志级别')

    args = parser.parse_args()

    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # 特征库文件路径

    # 创建特征扩充器实例
    expander = AIFeatureExpander(features_file, args.github_token)

    # 运行扩充流程
    expanded_features = expander.run_expansion(
        feature_count=args.feature_count,
        include_github=args.include_github,
        github_repo_count=args.github_repo_count
    )

    # 分析特征趋势
    trend_analysis = expander.analyze_feature_trends()

    # 打印结果
    print("\n=== AI特征库扩充结果 ===")
    print(f"总特征数: {trend_analysis['total_features']}")
    print(f"类别分布: {trend_analysis['category_distribution']}")
    print(f"最少特征类别: {trend_analysis['least_popular_category']}")
    print(f"平均每类别特征数: {trend_analysis['average_features_per_category']:.2f}")
    print("\n=== 扩充完成 ===")
    # 如果从GitHub获取了特征，打印相关信息
    if args.include_github:
        print("\n=== GitHub特征获取信息 ===")
        if HAS_GITHUB_API:
            print("✓ 成功从GitHub获取AI相关特征")
            print(f"✓ 分析了 {args.github_repo_count} 个GitHub仓库")
        else:
            print("⚠ 未找到requests库，无法从GitHub获取特征")
            print("⚠ 请安装requests库以启用GitHub特征获取功能")

if __name__ == "__main__":
    main()
