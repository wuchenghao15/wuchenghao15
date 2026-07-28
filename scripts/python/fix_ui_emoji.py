#!/usr/bin/env python3
import os
import re

EMOJI_MAP = {
    '📝': '<i class="fas fa-file-alt"></i>',
    '📊': '<i class="fas fa-chart-bar"></i>',
    '👥': '<i class="fas fa-users"></i>',
    '📚': '<i class="fas fa-book-open"></i>',
    '🤖': '<i class="fas fa-robot"></i>',
    '🔔': '<i class="fas fa-bell"></i>',
    '👨‍🏫': '<i class="fas fa-chalkboard-user"></i>',
    '👩‍🎓': '<i class="fas fa-user-graduate"></i>',
    '👨‍💻': '<i class="fas fa-user-cog"></i>',
    '💡': '<i class="fas fa-lightbulb"></i>',
    '🌟': '<i class="fas fa-star"></i>',
    '🔥': '<i class="fas fa-flame"></i>',
    '⚡': '<i class="fas fa-bolt"></i>',
    '🎯': '<i class="fas fa-target"></i>',
    '🎨': '<i class="fas fa-palette"></i>',
    '🏆': '<i class="fas fa-trophy"></i>',
    '🎁': '<i class="fas fa-gift"></i>',
    '🎈': '<i class="fas fa-balloon"></i>',
    '🎉': '<i class="fas fa-party-horn"></i>',
    '⭐': '<i class="fas fa-star"></i>',
    '💫': '<i class="fas fa-sparkles"></i>',
    '✨': '<i class="fas fa-sparkles"></i>',
    '💎': '<i class="fas fa-gem"></i>',
    '💖': '<i class="fas fa-heart"></i>',
    '💗': '<i class="fas fa-heart"></i>',
    '💓': '<i class="fas fa-heart"></i>',
    '💞': '<i class="fas fa-heart"></i>',
    '💘': '<i class="fas fa-heart"></i>',
    '💝': '<i class="fas fa-heart"></i>',
    '💟': '<i class="fas fa-heart"></i>',
    '💌': '<i class="fas fa-envelope"></i>',
    '💋': '<i class="fas fa-heart"></i>',
    '💍': '<i class="fas fa-ring"></i>',
    '💏': '<i class="fas fa-heart"></i>',
    '💑': '<i class="fas fa-heart"></i>',
    '💒': '<i class="fas fa-church"></i>',
    '💔': '<i class="fas fa-heart-broken"></i>',
    '💕': '<i class="fas fa-heart"></i>',
    '📈': '<i class="fas fa-chart-line"></i>',
    '📉': '<i class="fas fa-chart-line"></i>',
    '📋': '<i class="fas fa-list-check"></i>',
    '📁': '<i class="fas fa-folder"></i>',
    '📂': '<i class="fas fa-folder-open"></i>',
    '📄': '<i class="fas fa-file"></i>',
    '📑': '<i class="fas fa-file-lines"></i>',
    '📒': '<i class="fas fa-book"></i>',
    '📕': '<i class="fas fa-book"></i>',
    '📖': '<i class="fas fa-book-open"></i>',
    '📗': '<i class="fas fa-book"></i>',
    '📘': '<i class="fas fa-book"></i>',
    '📙': '<i class="fas fa-book"></i>',
    '📚': '<i class="fas fa-book-open"></i>',
    '📔': '<i class="fas fa-book"></i>',
    '📓': '<i class="fas fa-book"></i>',
    '📒': '<i class="fas fa-book"></i>',
    '📕': '<i class="fas fa-book"></i>',
    '📗': '<i class="fas fa-book"></i>',
    '📘': '<i class="fas fa-book"></i>',
    '📙': '<i class="fas fa-book"></i>',
    '📚': '<i class="fas fa-book-open"></i>',
    '📖': '<i class="fas fa-book-open"></i>',
    '📕': '<i class="fas fa-book"></i>',
    '📗': '<i class="fas fa-book"></i>',
    '📘': '<i class="fas fa-book"></i>',
    '📙': '<i class="fas fa-book"></i>',
    '📚': '<i class="fas fa-book-open"></i>',
    '📖': '<i class="fas fa-book-open"></i>',
    '🔧': '<i class="fas fa-wrench"></i>',
    '🔨': '<i class="fas fa-hammer"></i>',
    '⚙️': '<i class="fas fa-cog"></i>',
    '🛠️': '<i class="fas fa-tools"></i>',
    '🗂️': '<i class="fas fa-folder-tree"></i>',
    '📁': '<i class="fas fa-folder"></i>',
    '📂': '<i class="fas fa-folder-open"></i>',
    '📄': '<i class="fas fa-file"></i>',
    '📋': '<i class="fas fa-list-check"></i>',
    '📝': '<i class="fas fa-file-alt"></i>',
    '📑': '<i class="fas fa-file-lines"></i>',
    '📊': '<i class="fas fa-chart-bar"></i>',
    '📈': '<i class="fas fa-chart-line"></i>',
    '📉': '<i class="fas fa-chart-line"></i>',
    '📈': '<i class="fas fa-chart-line"></i>',
    '📉': '<i class="fas fa-chart-line"></i>',
    '📊': '<i class="fas fa-chart-bar"></i>',
    '📈': '<i class="fas fa-chart-line"></i>',
    '📉': '<i class="fas fa-chart-line"></i>',
}

def replace_emoji_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for emoji, replacement in EMOJI_MAP.items():
            content = content.replace(emoji, replacement)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error: {filepath} - {e}")
        return False

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    templates_dir = os.path.join(project_root, 'templates')
    print(f"Templates directory: {templates_dir}")
    
    fixed_count = 0
    total_files = 0
    
    for root, dirs, files in os.walk(templates_dir):
        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                total_files += 1
                if replace_emoji_in_file(filepath):
                    fixed_count += 1
    
    print(f"\nTotal files processed: {total_files}")
    print(f"Files with emoji replaced: {fixed_count}")

if __name__ == '__main__':
    main()
