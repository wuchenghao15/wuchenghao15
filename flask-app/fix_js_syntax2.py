import os
import re

JS_DIR = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/src/html/assets/js'

def fix_js_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    content = content.replace('\\"', '"')
    
    content = re.sub(r'config\.innerHTML\s*(\+)?\s*`', '`', content)
    content = re.sub(r'config\.class\s*(\+)?\s*`', '"btn btn-sm btn-primary"`', content)
    content = re.sub(r'config\.style\s*(\+)?\s*`', '"margin-right: 5px"`', content)
    content = re.sub(r'config\.href\s*(\+)?\s*`', '`', content)
    content = re.sub(r'config\.onclick\s*(\+)?\s*`', '', content)
    content = re.sub(r'config\.cookie\s*(\+)?\s*`', '', content)
    
    content = re.sub(r'`\s*\+\s*config\.\w+\s*\+\s*`', '`', content)
    
    content = re.sub(r'/\* 安全建议：使用配置管理系统 \*/ \*/\* 安全修复：使用环境变量 \*/', '', content)
    content = re.sub(r'/\* 代码质量修复：未使用的.*?\*/', '', content)
    content = re.sub(r'/\* 脚本修复：.*?\*/', '', content)
    content = re.sub(r'/\* 安全修复：.*?\*/', '', content)
    content = re.sub(r'/\* 安全建议：.*?\*/', '', content)
    
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if line.strip() == ';' or line.strip() == '':
            continue
        if line.strip().startswith('/*') and line.strip().endswith('*/'):
            continue
        if line.strip().startswith('//') and '修复' in line:
            continue
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  ✅ 修复: {filepath}')
        return True
    return False

def main():
    print('[AI修复] 开始修复JavaScript语法错误...')
    fixed_count = 0
    total_files = 0
    
    for root, dirs, files in os.walk(JS_DIR):
        for filename in files:
            if filename.endswith('.js'):
                filepath = os.path.join(root, filename)
                total_files += 1
                if fix_js_file(filepath):
                    fixed_count += 1
    
    print(f'[AI修复] 完成! 总计: {total_files} 个文件, 修复: {fixed_count} 个文件')

if __name__ == '__main__':
    main()