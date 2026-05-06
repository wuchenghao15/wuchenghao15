#!/usr/bin/env python3
"""
从GitHub自动扩充日语和英语题库脚本
利用AI自身学习能力和Python技术，从GitHub自动搜索和提取日语和英语题目，并使用AI生成新题目

import os
import sys
# JSON import removed - using database
import requests
import time
import random
import logging
import re
from datetime import datetime
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('expand_question_bank.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('expand_question_bank')

class AIBasedQuestionGenerator:
    """基于AI的题目生成器，利用AI自身学习能力生成高质量题目"""

    def __init__(self):
        """初始化AI题目生成器"""
        logger.info("初始化AI题目生成器...")
        # 模拟AI模型，实际使用时可以替换为真实的AI API调用
        self.model_name = "MTSCOS-AI-Question-Generator"
        self.language_templates = {
            "japanese": {
                "vocabulary": [
                    "请生成一道关于日语词汇'{}'的单选题，包含6个选项，其中1个正确选项，5个容易混淆的干扰项。",
                    "请生成一道测试日语词汇'{}'的单选题，要求选项包含意思相近的词汇。"
                ],
                "grammar": [
                    "请生成一道关于日语语法'{}'的单选题，测试其用法。",
                    "请生成一道测试日语语法结构'{}'的题目，包含6个选项。"
                ],
                    "请生成一段关于'{}'的日语短文，然后根据短文生成一道阅读理解题。",
                    "请生成一段日语阅读材料，并根据材料生成一道选择题。"
                ]
            "english": {
                "vocabulary": [
                    "Please generate a multiple choice question about the English word '{}' with 6 options.",
                ],
                "grammar": [
                    "Generate a grammar question about '{}' structure in English.",
                ],
                "reading": [
                ]
        }

        # 从现有题库学习的词汇和语法点
            "japanese": ["こんにちは", "ありがとう", "すみません", "いただきます", "ごちそうさま", "勉強", "仕事", "学校", "友達", "家族"],
            "english": ["hello", "thank you", "sorry", "please", "goodbye", "study", "work", "school", "friend", "family"]
        }

        self.learned_grammar = {
            "english": ["present simple", "present continuous", "past simple", "past continuous", "future simple", "conditional", "comparative", "superlative", "prepositions", "articles"]
        }

    def learn_from_existing_questions(self, questions: List[Dict[str, Any]], language: str):
        """从现有题目中学习，提取词汇和语法点"""

        for question in questions:
            # 从题目中提取词汇
            question_text = question.get("question_text", "")
            # 简单的词汇提取（实际应用中可以使用NLP工具）
            if language == "japanese":
                # 提取日语词汇
                japanese_words = re.findall(r'[\u3040-\u309F\u30A0-\u30FF]+', question_text)
                for word in japanese_words[:5]:  # 只提取前5个词汇
                    if word not in self.learned_vocabulary["japanese"] and len(word) > 1:
                        self.learned_vocabulary["japanese"].append(word)
            else:
                # 提取英语词汇
                english_words = re.findall(r'\b[a-zA-Z]+\b', question_text)
                for word in english_words[:5]:  # 只提取前5个词汇
                    if word not in self.learned_vocabulary["english"] and len(word) > 2:
                        self.learned_vocabulary["english"].append(word)

        logger.info(f"学习完成！{language}词汇库大小: {len(self.learned_vocabulary[language])}")

    def generate_question(self, language: str, question_type: str, count: int = 1) -> List[Dict[str, Any]]:
        """生成AI题目

        Args:
            language: 语言（japanese或english）
            question_type: 题目类型（vocabulary, grammar, reading等）
            count: 生成的题目数量

        Returns:
            生成的题目列表
        logger.info(f"使用AI生成{count}道{language} {question_type}题目...")

        generated_questions = []

        for _ in range(count):
            try:
                # 选择一个学习过的词汇或语法点
                if question_type == "vocabulary":
                    topic = random.choice(self.learned_vocabulary[language])
                elif question_type == "grammar":
                    topic = random.choice(self.learned_grammar[language])
                else:
                    topic = random.choice(self.learned_vocabulary[language])

                # 选择一个模板
                template = random.choice(self.language_templates[language][question_type])
                prompt = template.format(topic)

                # 模拟AI生成过程（实际应用中可以调用真实的AI API）
                time.sleep(0.1)  # 模拟AI处理时间

                # 生成题目
                generated_question = self._simulate_ai_response(prompt, language, question_type, topic)
                if generated_question:
                    logger.info(f"成功生成题目: {generated_question['question_text'][:30]}...")
                logger.error(f"生成题目失败: {str(e)}")
                continue

        logger.info(f"成功生成{len(generated_questions)}道{language} {question_type}题目")
        return generated_questions

    def _simulate_ai_response(self, prompt: str, language: str, question_type: str, topic: str) -> Dict[str, Any]:
        """模拟AI响应，生成题目

        Args:
            prompt: AI提示词
            language: 语言
            question_type: 题目类型
            topic: 主题

        Returns:
            生成的题目
        # 模拟生成题目，实际应用中可以替换为真实的AI API调用
        question_id = f"ai_gen_{language}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        # 根据语言和类型生成不同的题目
        if language == "japanese":
            if question_type == "vocabulary":
                    "question_id": question_id,
                    "level": random.choice(["N3", "N4", "N5"]),
                    "type": "vocabulary",
                    "question_text": f"'{topic}'の正しい意味はどれですか？",
                    "options": [
                        "选项1", "选项2", "选项3", "选项4", "选项5", "选项6"
                    "correct_answer": "选项1",
                    "explanation": f"'{topic}'の正しい意味は'选项1'です。",
                    "difficulty": random.randint(1, 5),
                    "category": "vocabulary",
                }
            elif question_type == "grammar":
                return {
                    "question_id": question_id,
                    "type": "grammar",
                    "question_text": f"次の文の空白に入る最も適切な言葉はどれですか？\n私は毎日{topic}。",
                    "options": [
                        "勉強しています", "勉強します", "勉強する", "勉強した", "勉強して", "勉強しない"
                    ],
                    "correct_answer": "勉強しています",
                    "explanation": f"'{topic}'は現在進行中の動作を表すので、'ています'形を使用します。",
                    "category": "grammar",
                    "subcategory": "verb conjugation",
                }
            else:
                return {
                    "question_id": question_id,
                    "level": random.choice(["N1", "N2", "N3"]),
                    "type": "reading",
                    "question_text": f"次の文章を読んで、質問に答えてください。\n{topic}についての文章がここに入ります。\n質問：この文章の主旨は何ですか？",
                    "options": [
                    ],
                    "explanation": "文章の主旨は'主旨1'です。",
                    "subcategory": "comprehension",
                }
        else:  # english
            if question_type == "vocabulary":
                    "question_id": question_id,
                    "type": "vocabulary",
                    "question_text": f"What is the meaning of the word '{topic}'?",
                    "options": [
                        "Option 1", "Option 2", "Option 3", "Option 4", "Option 5", "Option 6"
                    ],
                    "correct_answer": "Option 1",
                    "explanation": f"The correct meaning of '{topic}' is 'Option 1'.",
                    "subcategory": "general",
                }
                return {
                    "question_id": question_id,
                    "level": random.choice(["B1", "B2", "C1"]),
                    "type": "grammar",
                    "question_text": f"Choose the correct form of '{topic}' to complete the sentence.\nI {topic} to the park every day.",
                        "go", "goes", "went", "going", "gone", "will go"
                    ],
                    "correct_answer": "go",
                    "difficulty": random.randint(2, 4),
                    "category": "grammar",
                    "subcategory": "verb tense",
            else:
                    "question_id": question_id,
                    "level": random.choice(["B2", "C1", "C2"]),
                    "type": "reading",
                    "options": [
                        "Main idea 1", "Main idea 2", "Main idea 3", "Main idea 4", "Main idea 5", "Main idea 6"
                    ],
                    "correct_answer": "Main idea 1",
                    "difficulty": random.randint(3, 5),
                    "category": "reading",
                }
        """评估题目质量

            question: 要评估的题目

        Returns:
            题目质量分数（0-100）
        # 评估题目文本长度
            score += 20
        if len(question["options"]) >= 4:
            score += 20

        if len(question.get("explanation", "")) > 10:

        # 评估难度合理性
        if 1 <= question.get("difficulty", 1) <= 5:

        if len(question.get("tags", [])) >= 2:
            score += 20

        return min(score, 100)

        """优化题目，提高质量
        Args:
            优化后的题目
        logger.info(f"优化题目: {question['question_text'][:30]}...")

        # 复制题目
        optimized_question = question.copy()

        # 优化选项数量（确保至少6个选项）
        if len(optimized_question["options"]) < 6:
            while len(optimized_question["options"]) < 6:
                last_option = optimized_question["options"][-1]
                new_option = f"{last_option} (变形)"
                optimized_question["options"].append(new_option)

        # 优化标签
        if "tags" not in optimized_question:

        language = "japanese" if any("japanese" in tag.lower() for tag in optimized_question["tags"]) else "english"
            optimized_question["tags"].append(language)

        # 添加类型标签
        if optimized_question["type"] not in optimized_question["tags"]:
            optimized_question["tags"].append(optimized_question["type"])

        if "explanation" not in optimized_question or not optimized_question["explanation"]:
            optimized_question["explanation"] = f"这是一道关于{optimized_question['type']}的题目。"

        logger.info(f"题目优化完成，质量分数: {self.evaluate_question_quality(optimized_question)}")
        return optimized_question
    def categorize_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """自动分类题目

        Args:
            question: 要分类的题目

        Returns:
            分类后的题目
        # 简单的分类算法（实际应用中可以使用更复杂的AI分类）
        categorized_question = question.copy()


        # 根据关键词分类
        if any(word in question_text for word in ["意味", "vocab", "word", "单语", "词汇"]):
            categorized_question["category"] = "vocabulary"
        elif any(word in question_text for word in ["文法", "grammar", "语法", "構造", "structure"]):
            categorized_question["type"] = "grammar"
        elif any(word in question_text for word in ["読む", "reading", "阅读", "passage", "短文"]):
            categorized_question["type"] = "reading"
            categorized_question["category"] = "reading"
            categorized_question["type"] = "vocabulary"
            categorized_question["category"] = "vocabulary"

        return categorized_question

class GitHubQuestionBankExpander:
    """从GitHub自动扩充题库的类"""

    def __init__(self, github_token: str = None):
        """初始化GitHub题库扩充器

            github_token: GitHub访问令牌（可选）
        self.github_token = github_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MTSCOS-AI-Question-Bank-Expander"
        }
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

        # 题目数据结构模板
        self.question_template = {
            "question_id": "",
            "level": "",
            "type": "",
            "question_text": "",
            "options": [],
            "explanation": "",
            "difficulty": 1,
            "category": "",
            "subcategory": "",
            "tags": []
        }

        # 支持的题目类型
            "vocabulary", "grammar", "reading", "listening",
            "writing", "dictation", "translation"
        ]

        # 支持的语言级别
        self.language_levels = {
            "japanese": ["N1", "N2", "N3", "N4", "N5"],
        }
        # 初始化AI题目生成器
        self.ai_generator = AIBasedQuestionGenerator()

    def search_github_repositories(self, query: str, per_page: int = 10, page: int = 1) -> List[Dict[str, Any]]:
        """搜索GitHub仓库

        Args:
            query: 搜索关键词
            page: 页码

        Returns:
            仓库列表
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                "q": query,
                "per_page": per_page,
                "page": page
            }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("items", [])
        except Exception as e:
            logger.error(f"搜索GitHub仓库失败: {str(e)}")
            return []

    def get_repository_content(self, repo_owner: str, repo_name: str, path: str = "") -> Dict[str, Any]:
        """获取仓库内容

            repo_owner: 仓库所有者
            path: 仓库内的路径

        Returns:
            仓库内容
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
            response.raise_for_status()

            return response.json()
            logger.error(f"获取仓库内容失败: {str(e)}")
            return {}

    def download_file_content(self, download_url: str) -> str:
        """下载文件内容

        Args:
            download_url: 文件下载URL

        Returns:
        try:
            response = requests.get(download_url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"下载文件失败: {str(e)}")
            return ""
    def find_question_files(self, repo_owner: str, repo_name: str) -> List[Dict[str, Any]]:
        """在仓库中查找题目文件

        Args:
            repo_owner: 仓库所有者
            repo_name: 仓库名称

        Returns:
        question_files = []

        # 搜索常见的题目文件路径
        common_paths = [
            "", "questions", "data", "题库", "question_bank",
            "japanese", "english", "jlpt", "toefl", "ielts"
        ]

        for path in common_paths:
            content = self.get_repository_content(repo_owner, repo_name, path)

            for item in content:
                if isinstance(item, dict) and item.get("type") == "file":
                    # 检查文件名是否包含题目相关关键词
                    filename = item.get("name", "").lower()
                        # 检查文件扩展名
                        if filename.endswith((".json", ".txt", ".csv", ".yml", ".yaml")):
                            question_files.append(item)

    def extract_questions_from_json(self, content: str, language: str) -> List[Dict[str, Any]]:
        """从JSON文件中提取题目

        Args:
            content: JSON文件内容
            language: 语言（japanese或english）

        Returns:
        questions = []
        try:
            data = eval(content)
            # 检查数据结构
                items = data
            elif isinstance(data, dict) and "questions" in data:
                items = data["questions"]
            else:
                return questions

            for item in items:
                question = self.question_template.copy()

                # 提取题目信息
                question["question_id"] = item.get("id", f"{language}_{int(time.time() * 1000)}")
                question["explanation"] = item.get("explanation", item.get("answer_explanation", ""))
                question["difficulty"] = item.get("difficulty", random.randint(1, 5))

                # 提取选项
                    question["options"] = item["options"]
                elif all(key in item for key in ["optionA", "optionB", "optionC", "optionD"]):
                    question["options"] = [
                        item["optionA"],
                        item["optionB"],
                        item["optionC"],
                        item["optionD"]
                    ]

                # 提取正确答案
                question["correct_answer"] = item.get("answer", item.get("correct", ""))

                # 提取类型
                question_type = item.get("type", "vocabulary").lower()
                # 设置级别
                if language == "japanese":
                    question["level"] = item.get("level", random.choice(self.language_levels["japanese"]))
                    question["level"] = item.get("level", random.choice(self.language_levels["english"]))

                # 设置分类
                question["category"] = item.get("category", question["type"])
                question["subcategory"] = item.get("subcategory", "general")

                # 设置标签
                tags = item.get("tags", [])
                tags.append(question["type"])
                if question["question_text"] and question["correct_answer"]:
                    # 使用AI优化题目
                    optimized_question = self.ai_generator.optimize_question(question)
                    questions.append(optimized_question)
                    logger.info(f"提取到题目: {optimized_question['question_text'][:30]}...")
            logger.error(f"从JSON提取题目失败: {str(e)}")

        return questions

    def extract_questions_from_text(self, content: str, language: str) -> List[Dict[str, Any]]:
        """从文本文件中提取题目
        Args:
            content: 文本文件内容
            language: 语言（japanese或english）

        Returns:
        questions = []
            # 简单的文本格式解析（示例格式）
            lines = content.strip().split('\n')
            current_question = None
            option_index = 0
            options = []
            for line in lines:
                line = line.strip()
                if not line:

                # 检查是否是新题目
                if line.startswith('Q:') or line.startswith('Question:'):
                    # 保存上一个题目
                    if current_question and options:
                        current_question["options"] = options
                        if current_question["question_text"] and current_question["correct_answer"]:
                            # 使用AI优化题目
                            optimized_question = self.ai_generator.optimize_question(current_question)
                            questions.append(optimized_question)

                    # 开始新题目
                    current_question = self.question_template.copy()
                    current_question["question_id"] = f"{language}_{int(time.time() * 1000)}"
                    current_question["question_text"] = line[2:].strip()
                    option_index = 0
                    options = []
                    current_question["language"] = language
                    current_question["level"] = random.choice(self.language_levels[language])
                    current_question["type"] = "vocabulary"
                    current_question["difficulty"] = random.randint(1, 5)
                    current_question["category"] = "vocabulary"
                    current_question["subcategory"] = "general"
                    current_question["tags"] = [language, current_question["level"], "vocabulary"]
                elif line.startswith('A:') or line.startswith('Answer:'):
                    if current_question:
                        current_question["correct_answer"] = line[2:].strip()
                elif line.startswith(tuple([chr(ord('A') + i) + ':' for i in range(10)])):
                    # 选项行（A:, B:, etc.）
                    options.append(line[2:].strip())

            # 保存最后一个题目
                current_question["options"] = options
                if current_question["question_text"] and current_question["correct_answer"]:
                    # 使用AI优化题目
                    optimized_question = self.ai_generator.optimize_question(current_question)
                    questions.append(optimized_question)
        except Exception as e:
            logger.error(f"从文本文件提取题目失败: {str(e)}")

        return questions

    def extract_questions_from_file(self, file_content: str, filename: str, language: str) -> List[Dict[str, Any]]:
        """从文件中提取题目
        Args:
            file_content: 文件内容
            filename: 文件名

        Returns:
            提取的题目列表
        if filename.endswith(".json"):
            return self.extract_questions_from_json(file_content, language)
        elif filename.endswith(".txt"):
        else:
            logger.warning(f"不支持的文件格式: {filename}")
            return []

    def search_and_extract_questions(self, language: str, repo_count: int = 5) -> List[Dict[str, Any]]:
        """搜索并提取题目
        Args:
            language: 语言（japanese或english）
            repo_count: 要搜索的仓库数量

        Returns:
            提取的题目列表
        logger.info(f"开始从GitHub搜索{language}题目，分析{repo_count}个仓库")

        # 构建搜索关键词
        if language == "japanese":
            queries = ["japanese question bank", "jlpt vocabulary", "japanese grammar test", "日语题库"]
        else:
            queries = ["english question bank", "toefl vocabulary", "ielts grammar", "english test questions"]

        all_questions = []
        processed_files = set()

        for query in queries:
            if len(all_questions) >= 50:  # 减少每次提取的题目数量，提高效率
                break

            try:
                repos = self.search_github_repositories(query, per_page=repo_count)
                logger.error(f"搜索仓库失败: {str(e)}")
                continue

            for repo in repos:
                if len(all_questions) >= 50:
                    break

                repo_owner = repo.get("owner", {}).get("login", "")
                repo_name = repo.get("name", "")
                    continue

                logger.info(f"处理仓库: {repo_owner}/{repo_name}")

                try:
                except Exception as e:
                    logger.error(f"查找题目文件失败: {str(e)}")
                    continue

                for file in question_files:
                    if len(all_questions) >= 50:
                        break

                    file_key = f"{repo_owner}/{repo_name}/{file.get('name', '')}"
                        continue
                    # 下载文件内容
                        continue
                    try:
                        content = self.download_file_content(download_url)
                        if content:
                            # 提取题目
                            questions = self.extract_questions_from_file(content, file.get("name", ""), language)
                            logger.info(f"从文件中提取了{len(questions)}道题目")
                    except Exception as e:
                        logger.error(f"处理文件失败: {str(e)}")

            # 避免API速率限制
            time.sleep(0.5)  # 减少等待时间

        logger.info(f"成功从GitHub提取了{len(all_questions)}道{language}题目")

        self.ai_generator.learn_from_existing_questions(all_questions, language)

        return all_questions

    def generate_ai_questions(self, language: str, count: int = 20) -> List[Dict[str, Any]]:

        Args:
            count: 生成的题目数量

        Returns:
            生成的题目列表
        logger.info(f"开始使用AI生成{count}道{language}题目...")


        types = ["vocabulary", "grammar", "reading"]
        count_per_type = count // len(types)

        for question_type in types:
            generated_questions = self.ai_generator.generate_question(language, question_type, count_per_type)
            all_generated_questions.extend(generated_questions)

        # 补充剩余的题目
        remaining_count = count - len(all_generated_questions)
        if remaining_count > 0:
            additional_questions = self.ai_generator.generate_question(language, "vocabulary", remaining_count)

        logger.info(f"成功使用AI生成了{len(all_generated_questions)}道{language}题目")
        return all_generated_questions

        """将题目保存到文件
        Args:
        Returns:
            # 确定文件名
            if language == "japanese":
                filename = "english-questions.json"

                "scripts", filename
            )

            # 检查是否已存在文件
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_questions = json.load(f)
                existing_question_ids = {q["question_id"] for q in existing_questions}
                existing_questions.extend(new_questions)

                # 保存合并后的题目
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_questions, f, ensure_ascii=False, indent=2)
                logger.info(f"已将{len(new_questions)}道新题目添加到{file_path}")
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                logger.info(f"已创建新文件{file_path}，包含{len(questions)}道题目")

        except Exception as e:
            logger.error(f"保存题目失败: {str(e)}")
            return False
    def run(self, include_japanese: bool = True, include_english: bool = True, repo_count: int = 10, ai_generation_count: int = 20) -> Dict[str, Any]:

        Args:
            include_english: 是否包含英语题目
            repo_count: 每个语言要搜索的仓库数量

        logger.info("=== 开始从GitHub扩充题库流程 ===")
        results = {
            "japanese": {"extracted_count": 0, "generated_count": 0, "success": False},
        }

        if include_japanese:
            # 提取日语题目
            japanese_extracted = self.search_and_extract_questions("japanese", repo_count)
            # 使用AI生成日语题目

            # 合并题目
            all_japanese_questions = japanese_extracted + japanese_generated

            # 去重
            unique_questions = {}
                unique_questions[question["question_text"]] = question
            all_japanese_questions = list(unique_questions.values())

            if all_japanese_questions:
                success = self.save_questions_to_file(all_japanese_questions, "japanese")
                results["japanese"] = {
                    "extracted_count": len(japanese_extracted),
                    "generated_count": len(japanese_generated),
                }

        if include_english:
            # 提取英语题目
            english_extracted = self.search_and_extract_questions("english", repo_count)

            english_generated = self.generate_ai_questions("english", ai_generation_count)

            # 合并题目

            # 去重
            unique_questions = {}
            for question in all_english_questions:
                unique_questions[question["question_text"]] = question
            all_english_questions = list(unique_questions.values())

                success = self.save_questions_to_file(all_english_questions, "english")
                results["english"] = {
                    "extracted_count": len(english_extracted),
                    "generated_count": len(english_generated),
                    "total_count": len(all_english_questions),
                }



def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='从GitHub自动扩充日语和英语题库')

    # 语言选择参数
    parser.add_argument('--japanese', action='store_true', default=True,
                      help='是否包含日语题目')
    parser.add_argument('--english', action='store_true', default=True,
                      help='是否包含英语题目')

    # GitHub参数
    parser.add_argument('--github-token', type=str, default=os.environ.get('GITHUB_TOKEN'),
                      help='GitHub访问令牌')
    parser.add_argument('--repo-count', type=int, default=5,
                      help='每个语言要搜索的仓库数量')

    # AI生成参数
    parser.add_argument('--ai-count', type=int, default=20,
                      help='使用AI生成的题目数量')


    # 创建扩充器实例
    expander = GitHubQuestionBankExpander(args.github_token)

    # 运行扩充流程
        include_japanese=args.japanese,
        include_english=args.english,
        repo_count=args.repo_count,
        ai_generation_count=args.ai_count
    )

    # 打印结果
    print("\n=== GitHub题库扩充结果 ===")
    if args.japanese:
        print(f"日语题目: 从GitHub提取{results['japanese']['extracted_count']}道, AI生成{results['japanese']['generated_count']}道, 总计{results['japanese']['total_count']}道, 保存{'成功' if results['japanese']['success'] else '失败'}")
    if args.english:
    print("\n=== 扩充完成 ===")


if __name__ == "__main__":
    main()
