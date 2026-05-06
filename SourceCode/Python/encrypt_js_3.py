# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:26
#!/usr/bin/env python3
"""
JavaScript 文件加密工具
用于加密 MyScript 目录下的 JavaScript 文件，提供代码保护功能
"""
import os
import base64
import argparse
# JSON import removed - using database
from datetime import datetime

class JSEncryptor:
    """JavaScript文件加密器"""

    def __init__(self, input_dir, output_dir=None, backup=True, verbose=False):
        """

        Args:
            input_dir: 输入目录路径
            output_dir: 输出目录路径，None表示直接替换原文件
            backup: 是否备份原文件
            verbose: 是否显示详细信息
        """
        self.output_dir = output_dir
        self.backup = backup
        self.verbose = verbose
        self.encryption_key = "MTSCOS_SECURITY_KEY_2025"
        self.logs = []

    def log(self, message):
        """记录日志信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        if self.verbose:
            print(log_message)
        self.logs.append(log_message)

    def encrypt_content(self, content):
        """
        1. 使用Base64编码
        2. 添加XOR加密层提高安全性
        3. 生成自解密包装函数
        """
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        # 第二步：XOR加密（简单但有效）
        key_length = len(self.encryption_key)
        xored = ''.join(
            chr(ord(c) ^ ord(self.encryption_key[i % key_length]))
            for i, c in enumerate(encoded)
        )
        # 将XOR后的数据转换为Base64以便安全存储
        xored_encoded = base64.b64encode(xored.encode('utf-8')).decode('utf-8')

        # 第三步：生成自解密的JavaScript代码
        decryption_code = f'''
// MTSCOS - Protected Script
// This file is encrypted for security reasons
(function() {{
    var key = "{self.encryption_key}";
    var encoded = "{xored_encoded}";

    // 解密函数
    function decrypt() {{
        // 解码Base64
        var xored = atob(encoded);

        // XOR解密
        var keyLength = key.length;
        var decoded = '';
        for (var i = 0; i < xored.length; i++) {{
            decoded += String.fromCharCode(
                xored.charCodeAt(i) ^ key.charCodeAt(i % keyLength)
            );
        }}

        // 再次解码Base64获取原始内容
        return atob(decoded);
    }}

    // 执行解密后的代码
    try {{
        var code = decrypt();
        new Function(code)();
        console.error('Error executing protected script:', e);
    }}
}})();
'''

        return decryption_code

        """处理单个JavaScript文件"""
        try:
            # 读取原始文件
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 加密内容
            encrypted_content = self.encrypt_content(original_content)

            # 确定输出路径
            if self.output_dir:
                rel_path = os.path.relpath(file_path, self.input_dir)
                output_path = os.path.join(self.output_dir, rel_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            else:
                output_path = file_path

            # 备份原文件
            if self.backup and not self.output_dir:
                backup_path = f"{file_path}.bak"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                self.log(f"已备份: {file_path} -> {backup_path}")

            # 写入加密后的文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_content)

            self.log(f"已加密: {file_path} -> {output_path}")
            return True

        except Exception as e:
            self.log(f"加密失败: {file_path} - {str(e)}")
            return False

    def process_directory(self):
        """处理目录中的所有JavaScript文件"""
        self.log(f"开始加密目录: {self.input_dir}")

        total_files = 0
        success_files = 0

        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith('.js'):
                    file_path = os.path.join(root, file)
                    total_files += 1
                    if self.process_file(file_path):
                        success_files += 1

        self.log(f"加密完成: 共{total_files}个文件, 成功{success_files}个, 失败{total_files - success_files}个")

        # 保存日志
        self.save_log()

        return success_files

    def save_log(self):
        """保存加密日志"""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(
            log_dir,
            f'js_encrypt_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
        )

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.logs))

        self.log(f"日志已保存至: {log_file}")
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='JavaScript文件加密工具')
    parser.add_argument(
        '--input', '-i',
        default='./MyScript',
        help='输入目录路径，默认为 ./MyScript'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='输出目录路径，默认为直接替换原文件'
    )
        '--no-backup',
        action='store_true',
        help='不备份原文件'
    )
        action='store_true',
        help='显示详细输出'
    )
    args = parser.parse_args()
    # 验证输入目录
    if not os.path.isdir(args.input):
        return

    encryptor = JSEncryptor(
        input_dir=args.input,
        output_dir=args.output,
        backup=not args.no_backup,
    )

    success_count = encryptor.process_directory()

    if success_count > 0:
        print(f"加密成功！共处理 {success_count} 个JavaScript文件。")
        print("加密失败！")

if __name__ == '__main__':
    main()
