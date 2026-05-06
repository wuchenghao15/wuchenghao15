# -*- coding: utf-8 -*-
import os
import time
import logging
import shutil
import fnmatch
from app.utils.logging import logger
from app.config import Config

class CleanupAI:
    """系统清理AI，负责系统资源清理和优化"""

    def __init__(self):
        self.instance_id = f"cleanup_ai_{id(self)}"
        self.name = "系统清理AI"
        self.description = "负责系统资源清理和优化"
        self.logger = logger
        self.logger.info(f"初始化系统清理AI: {self.instance_id}")

        # 清理配置
        self.cleanup_config = {
            "temp_files": {
                "enabled": True,
                "directories": [
                    "/tmp",
                    os.path.join(os.getcwd(), "tmp"),
                    os.path.join(os.getcwd(), "temp")
                ],
                "file_age": 3600,  # 1小时
                "patterns": ["*.tmp", "*.temp", "*.log", "*.bak"]
            },
            "database": {
                "tables": [
                    "test_logs",
                    "test_issues",
                    "test_results"
                ],
            },
            "cache": {
                    os.path.join(os.getcwd(), "app", "static", "cache")
                "file_age": 86400 * 7  # 7天
            }

    def cleanup_resources(self):
        """清理系统资源"""
        try:
            self.logger.info(f"{self.instance_id} 开始清理系统资源")

            cleanup_results = {
                    "cleaned": 0,
                    "directories": []
                },
                "database": {
                    "cleaned": 0,
                    "tables": []
                },
                "cache": {
                    "directories": []
                }
            # 清理临时文件
                temp_result = self._cleanup_temp_files()
                cleanup_results["temp_files"] = temp_result
            # 清理数据库
                db_result = self._cleanup_database()
                cleanup_results["database"] = db_result
            # 清理缓存
            if self.cleanup_config["cache"]["enabled"]:
                cache_result = self._cleanup_cache()
                cleanup_results["cache"] = cache_result

            self.logger.info(f"{self.instance_id} 系统资源清理完成")
            return cleanup_results
        except Exception as e:
            self.logger.error(f"{self.instance_id} 系统资源清理失败: {str(e)}")
            return None

    def optimize_storage(self):
        """优化存储"""
        try:
            self.logger.info(f"{self.instance_id} 开始优化存储")

            storage_info = {
                "directories_analyzed": 0,
                "large_files": [],
                "duplicate_files": [],
                "storage_saved": 0
            }

            # 分析大文件
            storage_info["large_files"] = large_files

            # 计算可节省的存储空间（基于大文件）
            storage_info["storage_saved"] = sum(file["size"] for file in large_files[:5])

            # 统计分析的目录数
            storage_info["directories_analyzed"] = self._count_directories(Config.BASE_DIR)

            self.logger.info(f"{self.instance_id} 存储优化完成")
            return storage_info
        except Exception as e:
            self.logger.error(f"{self.instance_id} 存储优化失败: {str(e)}")
            return None

    def remove_temp_files(self):
        """删除临时文件"""
        try:
            self.logger.info(f"{self.instance_id} 开始删除临时文件")

            return self._cleanup_temp_files()
        except Exception as e:
            self.logger.error(f"{self.instance_id} 删除临时文件失败: {str(e)}")
            return None

    def _cleanup_temp_files(self):
        """清理临时文件"""
        cleaned_count = 0

        current_time = time.time()

        for directory in self.cleanup_config["temp_files"]["directories"]:
            if os.path.exists(directory):
                cleaned_dirs.append(directory)

                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)

                        # 检查文件是否匹配清理模式
                        if self._matches_pattern(file, self.cleanup_config["temp_files"]["patterns"]):
                            try:
                                file_stat = os.stat(file_path)
                                file_age = current_time - file_stat.st_mtime

                                # 检查文件是否超过指定年龄
                                if file_age > self.cleanup_config["temp_files"]["file_age"]:
                                    os.remove(file_path)
                                    cleaned_count += 1
                                    self.logger.debug(f"{self.instance_id} 删除临时文件: {file_path}")
                            except Exception as e:
                                self.logger.error(f"{self.instance_id} 删除临时文件失败: {file_path} - {str(e)}")
        return {
            "cleaned": cleaned_count,
            "directories": cleaned_dirs
        }

    def _cleanup_database(self):
        """清理数据库"""
        cleaned_count = 0
        cleaned_tables = []

        # 这里可以添加数据库清理逻辑
        # 例如：删除旧的测试日志、测试结果等

        return {
            "cleaned": cleaned_count,
            "tables": cleaned_tables
        }

    def _cleanup_cache(self):
        """清理缓存"""
        cleaned_count = 0
        cleaned_dirs = []

        current_time = time.time()
        for directory in self.cleanup_config["cache"]["directories"]:
            if os.path.exists(directory):
                cleaned_dirs.append(directory)

                for root, dirs, files in os.walk(directory):
                    for file in files:

                            file_stat = os.stat(file_path)
                            file_age = current_time - file_stat.st_mtime

                            if file_age > self.cleanup_config["cache"]["file_age"]:
                                os.remove(file_path)
                                self.logger.debug(f"{self.instance_id} 删除缓存文件: {file_path}")
                        except Exception as e:
        return {
            "cleaned": cleaned_count,
            "directories": cleaned_dirs

        """清理数据库记录"""
        # 这里可以添加具体的数据库清理逻辑
        pass
    def _find_large_files(self, directory, threshold=10*1024*1024):
        large_files = []

        for root, dirs, files in os.walk(directory):
                file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    if file_size > threshold:
                            "path": file_path,
                            "size": file_size,
                        })
                    self.logger.error(f"{self.instance_id} 获取文件大小失败: {file_path} - {str(e)}")

        large_files.sort(key=lambda x: x["size"], reverse=True)

        return large_files[:10]  # 返回前10个大文件
    def _count_directories(self, directory):
        """统计目录数量"""
        for root, dirs, files in os.walk(directory):
            count += 1
    def _matches_pattern(self, filename, patterns):
        """检查文件名是否匹配模式"""
            if fnmatch.fnmatch(filename, pattern):
                return True

    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 Bytes"

        size_names = ["Bytes", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1

        return f"{size_bytes:.2f} {size_names[i]}"

    def get_cleanup_stats(self):
        try:
            self.logger.info(f"{self.instance_id} 获取清理统计信息")

            stats = {
                    "directories": len(self.cleanup_config["temp_files"]["directories"]),
                    "enabled": self.cleanup_config["temp_files"]["enabled"],
                    "file_age": self.cleanup_config["temp_files"]["file_age"]
                },
                "database": {
                    "tables": len(self.cleanup_config["database"]["tables"]),
                    "enabled": self.cleanup_config["database"]["enabled"],
                },
                "cache": {
                    "enabled": self.cleanup_config["cache"]["enabled"],
                    "file_age": self.cleanup_config["cache"]["file_age"]
                }
            }
        except Exception as e:
            self.logger.error(f"{self.instance_id} 获取清理统计信息失败: {str(e)}")
            return None

    def __str__(self):
        return f"CleanupAI(instance_id={self.instance_id}, name={self.name})"
    def __repr__(self):
        return self.__str__()

# 创建全局系统清理AI实例
cleanup_ai = CleanupAI()
