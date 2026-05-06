#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
头像裁剪工具
用于处理用户上传的头像，进行裁剪和优化

import os
from PIL import Image
from PIL import ImageDraw
from app.utils.logging import logger

class AvatarCropper:
    """头像裁剪类"""

    def __init__(self):
        self.max_size = 500  # 最大尺寸（宽/高）
        self.min_size = 100  # 最小尺寸（宽/高）
        self.target_size = (200, 200)  # 目标尺寸

    def crop_avatar(self, input_path, output_path):
        """裁剪头像为圆形"""
        try:
            logger.info(f"开始裁剪头像: {input_path} -> {output_path}")

            # 打开图片
            image = Image.open(input_path)

            # 确保图片是RGB模式
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # 获取图片尺寸
            width, height = image.size
            logger.info(f"原始图片尺寸: {width}x{height}")

            # 调整图片大小（保持比例）
            if width > height:
                new_width = self.max_size
                new_height = int((height / width) * new_width)
            else:
                new_height = self.max_size
                new_width = int((width / height) * new_height)

            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"调整后图片尺寸: {new_width}x{new_height}")

            # 创建圆形遮罩
            mask = Image.new('RGBA', self.target_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, self.target_size[0], self.target_size[1]), fill=(255, 255, 255, 255))

            # 裁剪图片为正方形
            crop_size = min(new_width, new_height)
            left = (new_width - crop_size) // 2
            top = (new_height - crop_size) // 2
            right = (new_width + crop_size) // 2
            bottom = (new_height + crop_size) // 2

            cropped_image = resized_image.crop((left, top, right, bottom))

            # 调整为目标尺寸
            cropped_image = cropped_image.resize(self.target_size, Image.Resampling.LANCZOS)

            # 应用圆形遮罩
            result = Image.new('RGBA', self.target_size, (0, 0, 0, 0))
            result.paste(cropped_image, (0, 0), mask)

            # 保存为PNG格式
            result.save(output_path, format='PNG')
            logger.info(f"头像裁剪完成: {output_path}")

            return True, "头像裁剪成功"
        except Exception as e:
            logger.error(f"头像裁剪失败: {str(e)}")
            return False, str(e)

    def validate_avatar(self, file_path):
        """验证头像文件"""
        try:
            width, height = image.size

                return False, f"头像尺寸太小，至少需要 {self.min_size}x{self.min_size} 像素"

            if width > 5000 or height > 5000:
                return False, f"头像尺寸太大，最大支持 5000x5000 像素"

            return True, "头像验证通过"
        except Exception as e:
            logger.error(f"头像验证失败: {str(e)}")
            return False, str(e)

    def optimize_avatar(self, file_path):
        """优化头像，减小文件大小"""
        try:

            image = Image.open(file_path)

            # 保存为优化后的PNG
            optimized_path = file_path.replace('.png', '_optimized.png')

            # 比较文件大小
            original_size = os.path.getsize(file_path)
            optimized_size = os.path.getsize(optimized_path)
            logger.info(f"头像优化完成，大小从 {original_size/1024:.2f}KB 减少到 {optimized_size/1024:.2f}KB")

            # 替换原文件
            os.remove(file_path)
            os.rename(optimized_path, file_path)

            return True, "头像优化成功"
        except Exception as e:
            logger.error(f"头像优化失败: {str(e)}")
            return False, str(e)
