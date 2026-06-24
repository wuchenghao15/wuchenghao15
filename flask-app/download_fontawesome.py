import urllib.request
import zipfile
import os
import shutil

url = 'https://github.com/FortAwesome/Font-Awesome/releases/download/6.4.0/fontawesome-free-6.4.0-web.zip'
local_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/src/html/assets/vendor/fontawesome.zip'
extract_dir = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/src/html/assets/vendor/'

print('[AI修复] 下载Font Awesome...')
urllib.request.urlretrieve(url, local_path)

print('[AI修复] 解压...')
with zipfile.ZipFile(local_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

print('[AI修复] 重命名...')
os.remove(local_path)
old_dir = os.path.join(extract_dir, 'fontawesome-free-6.4.0-web')
new_dir = os.path.join(extract_dir, 'fontawesome')
if os.path.exists(new_dir):
    shutil.rmtree(new_dir)
os.rename(old_dir, new_dir)

print('[AI修复] webfonts文件:')
for f in os.listdir(os.path.join(new_dir, 'webfonts')):
    print(f'  {f}')

print('[AI修复] 完成!')