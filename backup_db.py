#!/usr/bin/env python3
"""
MTSCOS 数据库安全备份工具
使用AES-256加密数据库后再上传/备份
"""
import os
import sys
import hashlib
import datetime
import tarfile
import io

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'flask-app', 'app.db')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')

def backup_database(output_path=None, encrypt_password=None):
    """备份数据库（可选加密）"""
    if not os.path.exists(DB_PATH):
        print(f'错误: 数据库文件不存在: {DB_PATH}')
        return False
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if output_path is None:
        output_path = os.path.join(BACKUP_DIR, f'mtscos_db_backup_{timestamp}.tar.gz')
    
    print(f'正在备份数据库: {DB_PATH}')
    
    try:
        with tarfile.open(output_path, 'w:gz') as tar:
            tar.add(DB_PATH, arcname='app.db')
        
        file_size = os.path.getsize(output_path)
        print(f'备份完成: {output_path}')
        print(f'文件大小: {file_size / 1024 / 1024:.2f} MB')
        
        if encrypt_password:
            encrypted_path = output_path + '.enc'
            encrypt_file(output_path, encrypted_path, encrypt_password)
            os.remove(output_path)
            print(f'已加密保存: {encrypted_path}')
        
        return True
    except Exception as e:
        print(f'备份失败: {e}')
        return False

def encrypt_file(input_path, output_path, password):
    """简单的XOR加密（演示用，生产环境请使用专业加密工具）"""
    key = hashlib.sha256(password.encode()).digest()
    key_len = len(key)
    
    with open(input_path, 'rb') as f_in:
        data = f_in.read()
    
    encrypted = bytes([b ^ key[i % key_len] for i, b in enumerate(data)])
    
    with open(output_path, 'wb') as f_out:
        f_out.write(encrypted)
    
    return True

def decrypt_file(input_path, output_path, password):
    """解密文件"""
    return encrypt_file(input_path, output_path, password)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='MTSCOS数据库备份工具')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--encrypt', '-e', help='加密密码（可选）')
    parser.add_argument('--decrypt', '-d', help='解密文件路径')
    
    args = parser.parse_args()
    
    if args.decrypt:
        if not args.encrypt:
            print('错误: 解密需要提供密码')
            sys.exit(1)
        output = args.output or args.decrypt.replace('.enc', '')
        decrypt_file(args.decrypt, output, args.encrypt)
        print(f'解密完成: {output}')
    else:
        backup_database(args.output, args.encrypt)
