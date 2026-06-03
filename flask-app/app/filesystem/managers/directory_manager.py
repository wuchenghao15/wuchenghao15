# -*- coding: utf-8 -*-
# MTSCOS AI Project 目录管理器
"""
目录管理器,负责目录相关的操作

import os
from typing import Dict, Any, List
from app.utils.logging import logger


class DirectoryManager:
    目录管理器,负责目录相关的操作

        self._storage_manager = storage_manager

    def create_directory(self, path: str) -> bool:
        创建目录

        Args:
            path: 目录路径

        Returns:
            bool: 是否创建成功
        try:
            return self._storage_manager.create_directory(path)
        except Exception as e:
            logger.error(f"创建目录 {path} 失败: {str(e)}")
            return False

    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        删除目录

        Args:
            path: 目录路径
            recursive: 是否递归删除

        Returns:
            bool: 是否删除成功
        try:
            if not self._storage_manager.exists(path):
                return False

            # 检查是否为目录
            if self._storage_manager.get_path_type(path) != 'directory':
                logger.error(f"路径 {path} 不是目录")
                return False

            return self._storage_manager.delete(path, recursive)
        except Exception as e:
            logger.error(f"删除目录 {path} 失败: {str(e)}")
            return False

    def get_directory_info(self, path: str) -> Dict[str, Any]:
        获取目录信息

        Args:
            path: 目录路径

        Returns:
            Dict[str, Any]: 目录信息
        metadata = self._storage_manager.get_metadata(path)

        if metadata['exists'] and metadata['type'] == 'directory':
            # 添加目录特有信息
                'is_file': False,
                'is_directory': True,
                'contents': self._get_directory_contents(path)
            })

        return metadata

    def list_directory(self, path: str) -> List[Dict[str, Any]]:
        列出目录内容

        Args:
            path: 目录路径

        Returns:
            List[Dict[str, Any]]: 目录内容列表
        try:
            # 检查目录是否存在
            if not self._storage_manager.exists(path):
                logger.error(f"目录 {path} 不存在")
                return []

            if self._storage_manager.get_path_type(path) != 'directory':
                logger.error(f"路径 {path} 不是目录")
                return []
            # 获取完整路径
            full_path = self._storage_manager.resolve_path(path)

            contents = []

            # 遍历目录内容
            for item in os.listdir(full_path):
                item_path = os.path.join(path, item)
                item_info = self._storage_manager.get_metadata(item_path)

                # 添加类型信息
                if item_info['type'] == 'file':
                    item_info.update({
                        'is_file': True,
                        'is_directory': False,
                        'extension': os.path.splitext(item)[1],
                    })
                elif item_info['type'] == 'directory':
                    item_info.update({
                        'is_file': False,
                        'is_directory': True,
                        'dirname': item
                    })

                contents.append(item_info)

            return contents
        except Exception as e:
            logger.error(f"列出目录 {path} 内容失败: {str(e)}")
            return []

    def copy_directory(self, src_path: str, dest_path: str, overwrite: bool = False) -> bool:
        复制目录

            src_path: 源目录路径
            dest_path: 目标目录路径

        try:
            if not self._storage_manager.exists(src_path):
                logger.error(f"源目录 {src_path} 不存在")
                return False

            if self._storage_manager.get_path_type(src_path) != 'directory':
                logger.error(f"源路径 {src_path} 不是目录")
                return False

        except Exception as e:
            logger.error(f"复制目录 {src_path} -> {dest_path} 失败: {str(e)}")
            return False

    def move_directory(self, src_path: str, dest_path: str, overwrite: bool = False) -> bool:
        移动目录

        Args:
            src_path: 源目录路径
            dest_path: 目标目录路径
            overwrite: 是否覆盖现有目录

        Returns:
            bool: 是否移动成功
        try:
            # 检查源目录是否存在
            if not self._storage_manager.exists(src_path):
                logger.error(f"源目录 {src_path} 不存在")
                return False

            # 检查源目录是否为目录
            if self._storage_manager.get_path_type(src_path) != 'directory':
                return False

            return self._storage_manager.move(src_path, dest_path, overwrite)
        except Exception as e:
            logger.error(f"移动目录 {src_path} -> {dest_path} 失败: {str(e)}")
            return False

    def rename_directory(self, old_path: str, new_path: str) -> bool:
        重命名目录

        Args:
            old_path: 旧目录路径
            new_path: 新目录路径

        Returns:
    pass
        return self.move_directory(old_path, new_path, overwrite=True)
    def get_directory_size(self, path: str) -> int:
    pass

        Args:
            path: 目录路径

        Returns:
            int: 目录大小(字节)
            if not self._storage_manager.exists(path):
                return 0
            # 检查是否为目录
            if self._storage_manager.get_path_type(path) != 'directory':
                logger.error(f"路径 {path} 不是目录")

            full_path = self._storage_manager.resolve_path(path)

            # 遍历目录中的所有文件和子目录
            for dirpath, dirnames, filenames in os.walk(full_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            logger.error(f"获取目录 {path} 大小失败: {str(e)}")
            return 0

    def find_in_directory(self, path: str, pattern: str, recursive: bool = False) -> List[Dict[str, Any]]:
        在目录中查找文件

        Args:
            path: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归查找

        Returns:
            List[Dict[str, Any]]: 匹配的文件列表
        try:
            # 检查目录是否存在
            if not self._storage_manager.exists(path):
                logger.error(f"目录 {path} 不存在")
                return []

            # 检查是否为目录
            if self._storage_manager.get_path_type(path) != 'directory':
                logger.error(f"路径 {path} 不是目录")
                return []

            import fnmatch
import logging

            # 获取完整路径

            matches = []

            if recursive:
                for dirpath, dirnames, filenames in os.walk(full_path):
                    for filename in filenames:
                        if fnmatch.fnmatch(filename, pattern):
                            relative_path = os.path.relpath(file_path, full_path)
                            file_info = self._storage_manager.get_metadata(relative_path)
                            matches.append(file_info)
            else:
                # 非递归查找
                for filename in os.listdir(full_path):
                    file_path = os.path.join(full_path, filename)
                    if os.path.isfile(file_path) and fnmatch.fnmatch(filename, pattern):
                        relative_path = os.path.join(path, filename)
                        file_info = self._storage_manager.get_metadata(relative_path)
                        matches.append(file_info)

            return matches
            logger.error(f"在目录 {path} 中查找文件失败: {str(e)}")
            return []

    def _get_directory_contents(self, path: str) -> Dict[str, Any]:
        获取目录内容统计信息
        Args:
            path: 目录路径

        Returns:
    pass
        try:
            # 获取完整路径
            full_path = self._storage_manager.resolve_path(path)

            file_count = 0
            dir_count = 0
            total_size = 0

            # 遍历目录内容
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path):
                    file_count += 1
                    total_size += os.path.getsize(item_path)
                elif os.path.isdir(item_path):
                    dir_count += 1

            return {
                'directory_count': dir_count,
                'total_size': total_size
            }
        except Exception as e:
            logger.error(f"获取目录 {path} 内容统计信息失败: {str(e)}")
            return {
                'file_count': 0,
                'directory_count': 0,


        Args:
            recursive: 是否递归清理

        Returns:
            bool: 是否清理成功
        try:
            # 检查目录是否存在
            if not self._storage_manager.exists(path):
                logger.error(f"目录 {path} 不存在")
                return False

            if self._storage_manager.get_path_type(path) != 'directory':
                return False

            # 获取完整路径
            full_path = self._storage_manager.resolve_path(path)

            if recursive:
                # 递归清理子目录
                for dirpath, dirnames, filenames in os.walk(full_path, topdown=False):
                        subdir_path = os.path.join(dirpath, dirname)
                            os.rmdir(subdir_path)
                            logger.info(f"清理空目录: {os.path.relpath(subdir_path, full_path)}")
            else:
                # 仅清理当前目录下的空目录
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    if os.path.isdir(item_path) and not os.listdir(item_path):
                        os.rmdir(item_path)
                        logger.info(f"清理空目录: {os.path.join(path, item)}")
        except Exception as e:
            logger.error(f"清理空目录 {path} 失败: {str(e)}")
            return False

"""