#!/usr/bin/env python3
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

modified_files = []
total_line_changes = 0

def should_skip_directory(dirpath):
    parts = dirpath.split(os.sep)
    if '.git' in parts:
        return True
    if '__pycache__' in parts:
        return True
    return False

def find_all_py_files(root):
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        if should_skip_directory(dirpath):
            dirnames[:] = []
            continue
        for fn in filenames:
            if fn.endswith('.py'):
                py_files.append(os.path.join(dirpath, fn))
    return py_files

def is_scripts_python(filepath):
    rel = os.path.relpath(filepath, PROJECT_ROOT)
    return rel.startswith('scripts' + os.sep + 'python' + os.sep) or \
           rel.startswith('scripts/python/')

def is_core_db_path(filepath):
    rel = os.path.relpath(filepath, PROJECT_ROOT)
    return rel.replace(os.sep, '/') == 'core/db_path.py'

def has_db_path_import(content):
    if re.search(r'from\s+core\.db_path\s+import', content):
        return True
    if re.search(r'import\s+core\.db_path', content):
        return True
    if re.search(r'\bget_db_path\b', content) and re.search(r'\bcore\.db_path\b', content):
        return True
    if re.search(r'(^|\s)get_db_path\s*\(', content) and re.search(r'from\s+core', content):
        return True
    return False

def has_mtscos_get_db_path_import(content):
    return '_mtscos_get_db_path' in content

def task1_fix_database_path():
    global total_line_changes
    pattern = re.compile(
        r'^(\s*)DATABASE_PATH\s*=\s*os\.path\.join\(\s*os\.path\.dirname\(\s*os\.path\.abspath\(\s*__file__\s*\)\s*\)\s*,\s*[\'"]app\.db[\'"]\s*\)\s*$',
        re.MULTILINE
    )
    py_files = find_all_py_files(PROJECT_ROOT)
    for fp in sorted(py_files):
        if is_core_db_path(fp):
            continue
        if is_scripts_python(fp):
            continue
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue
        if not pattern.search(content):
            continue
        if has_db_path_import(content) or has_mtscos_get_db_path_import(content):
            continue

        lines = content.split('\n')
        new_lines = []
        import_inserted = False
        file_changed_count = 0
        for i, line in enumerate(lines):
            m = pattern.match(line)
            if m:
                indent = m.group(1)
                if not import_inserted:
                    j = 0
                    insert_idx = 0
                    while j < len(new_lines):
                        ln = new_lines[j]
                        if re.match(r'^\s*#', ln) or ln.strip() == '':
                            j += 1
                            continue
                        if re.match(r'^\s*(from|import)\s+', ln):
                            insert_idx = j + 1
                            j += 1
                            continue
                        break
                    import_line = 'from core.db_path import get_db_path as _mtscos_get_db_path'
                    new_lines.insert(insert_idx, import_line)
                    import_inserted = True
                    file_changed_count += 1
                new_line = indent + "DATABASE_PATH = _mtscos_get_db_path('app.db')"
                new_lines.append(new_line)
                file_changed_count += 1
            else:
                new_lines.append(line)
        if file_changed_count > 0:
            new_content = '\n'.join(new_lines)
            try:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                modified_files.append((fp, file_changed_count))
                total_line_changes += file_changed_count
            except Exception:
                pass

def task2_fix_split_databases():
    fixes_applied = []

    def count_and_apply(fp, transform_fn):
        global total_line_changes
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return 0
        new_content, count = transform_fn(content)
        if count > 0:
            try:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                modified_files.append((fp, count))
                total_line_changes += count
                fixes_applied.append(fp)
                return count
            except Exception:
                return 0
        return 0

    def fix_a_b(content):
        count = 0
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            m = re.match(r'^(\s*)DB_DIR\s*=\s*os\.path\.join\(\s*BASE_DIR\s*,\s*[\'"]split_databases[\'"]\s*\)\s*$', line)
            if m:
                indent = m.group(1)
                new_lines.append(indent + "DB_DIR = os.path.join(BASE_DIR, 'Database')")
                count += 1
            else:
                new_lines.append(line)
        return '\n'.join(new_lines), count

    fp_a = os.path.join(PROJECT_ROOT, 'startup_modules', 'core_init.py')
    fp_b = os.path.join(PROJECT_ROOT, 'startup_modules', 'db_config_loader.py')
    count_and_apply(fp_a, fix_a_b)
    count_and_apply(fp_b, fix_a_b)

    def fix_c_d(content):
        count = 0
        lines = content.split('\n')
        new_lines = []
        import_inserted = False
        for i, line in enumerate(lines):
            m = re.match(
                r'^(\s*)DB_DIR\s*=\s*os\.path\.join\(\s*os\.path\.dirname\(\s*os\.path\.abspath\(\s*__file__\s*\)\s*\)\s*,\s*[\'"]split_databases[\'"]\s*\)\s*$',
                line
            )
            if m:
                indent = m.group(1)
                if not import_inserted and 'from core.db_path import resolve_project_root as _r' not in content:
                    j = 0
                    insert_idx = 0
                    while j < len(new_lines):
                        ln = new_lines[j]
                        if re.match(r'^\s*#', ln) or ln.strip() == '':
                            j += 1
                            continue
                        if re.match(r'^\s*(from|import)\s+', ln):
                            insert_idx = j + 1
                            j += 1
                            continue
                        break
                    import_line = 'from core.db_path import resolve_project_root as _r'
                    new_lines.insert(insert_idx, import_line)
                    import_inserted = True
                    count += 1
                new_lines.append(indent + "DB_DIR = os.path.join(_rr(), 'Database')")
                count += 1
            else:
                new_lines.append(line)
        return '\n'.join(new_lines), count

    fp_c = os.path.join(PROJECT_ROOT, 'core', 'services', 'db_manager.py')
    fp_d = os.path.join(PROJECT_ROOT, 'core', 'services', 'smart_db_router.py')
    count_and_apply(fp_c, fix_c_d)
    count_and_apply(fp_d, fix_c_d)

    def fix_e(content):
        count = 0
        lines = content.split('\n')
        new_lines = []
        import_inserted = False
        for i, line in enumerate(lines):
            if not import_inserted:
                if 'from core.db_path import get_db_path' not in content:
                    m_proj_root = re.match(r'^(\s*)PROJECT_ROOT\s*=\s*os\.path\.dirname', line)
                    if m_proj_root:
                        indent = m_proj_root.group(1)
                        new_lines.append(line)
                        insert_idx = 0
                        tmp_lines = list(new_lines)
                        for k in range(len(tmp_lines)):
                            ln = tmp_lines[k]
                            if re.match(r'^\s*(from|import)\s+', ln):
                                insert_idx = k + 1
                                continue
                            if re.match(r'^\s*#', ln) or ln.strip() == '':
                                continue
                            break
                        if insert_idx == 0:
                            insert_idx = len(new_lines)
                        import_line = 'from core.db_path import get_db_path'
                        new_lines.insert(insert_idx, import_line)
                        import_inserted = True
                        count += 1
                        continue
            m_admin = re.match(
                r'^(\s*)ADMIN_DB\s*=\s*os\.path\.join\(\s*PROJECT_ROOT\s*,\s*[\'"]split_databases[\'"]\s*,\s*[\'"]admin\.db[\'"]\s*\)\s*$',
                line
            )
            if m_admin:
                indent = m_admin.group(1)
                new_lines.append(indent + "ADMIN_DB = get_db_path('admin.db')")
                count += 1
                continue
            m_app = re.match(
                r'^(\s*)APP_DB\s*=\s*os\.path\.join\(\s*PROJECT_ROOT\s*,\s*[\'"]app\.db[\'"]\s*\)\s*$',
                line
            )
            if m_app:
                indent = m_app.group(1)
                new_lines.append(indent + "APP_DB = get_db_path('app.db')")
                count += 1
                continue
            m_sim = re.search(
                r'os\.path\.join\(\s*PROJECT_ROOT\s*,\s*[\'"]split_databases[\'"]\s*,\s*[\'"](_vikey_sim_devices\.json)[\'"]\s*\)',
                line
            )
            if m_sim:
                indent_match = re.match(r'^(\s*)', line)
                indent = indent_match.group(1) if indent_match else ''
                prefix = line[:m_sim.start()]
                suffix = line[m_sim.end():]
                new_line = prefix + "get_db_path('_vikey_sim_devices.json')" + suffix
                new_lines.append(new_line)
                count += 1
                continue
            new_lines.append(line)
        return '\n'.join(new_lines), count

    fp_e = os.path.join(PROJECT_ROOT, 'core', 'services', 'vikey_driver.py')
    count_and_apply(fp_e, fix_e)

    def fix_f(content):
        count = 0
        lines = content.split('\n')
        new_lines = []
        import_inserted = False
        for i, line in enumerate(lines):
            m_ai = re.match(
                r'^(\s*)AI_DB_PATH\s*=\s*os\.path\.join\([^)]*split_databases[^)]*ai\.db[\'"]\s*\)\s*$',
                line
            )
            if m_ai:
                indent = m_ai.group(1)
                if not import_inserted and 'from core.db_path import get_db_path' not in content:
                    j = 0
                    insert_idx = 0
                    while j < len(new_lines):
                        ln = new_lines[j]
                        if re.match(r'^\s*#', ln) or ln.strip() == '':
                            j += 1
                            continue
                        if re.match(r'^\s*(from|import)\s+', ln):
                            insert_idx = j + 1
                            j += 1
                            continue
                        if 'sys.path.insert' in ln:
                            insert_idx = j + 1
                            j += 1
                            continue
                        break
                    import_line = 'from core.db_path import get_db_path'
                    new_lines.insert(insert_idx, import_line)
                    import_inserted = True
                    count += 1
                new_lines.append(indent + "AI_DB_PATH = get_db_path('ai.db')")
                count += 1
            else:
                new_lines.append(line)
        return '\n'.join(new_lines), count

    fp_f = os.path.join(PROJECT_ROOT, 'core', 'services', 'start_all_employees.py')
    count_and_apply(fp_f, fix_f)

    def fix_g(content):
        count = 0
        lines = content.split('\n')
        db_constants = [
            ('AUTH_DB', "'auth.db'"),
            ('APP_DB', "'app.db'"),
            ('SPLIT_SYSTEM_DB', "'system.db'"),
            ('SPLIT_AI_DB', "'ai.db'"),
            ('SPLIT_EXAM_DB', "'exam.db'"),
            ('SPLIT_QUESTION_DB', "'question.db'"),
            ('SPLIT_USER_DB', "'user.db'"),
            ('SPLIT_ADMIN_DB', "'admin.db'"),
            ('SPLIT_LEARNING_DB', "'learning.db'"),
            ('SPLIT_LOG_DB', "'log.db'"),
            ('SPLIT_PROCTOR_DB', "'proctor.db'"),
            ('DATA_MTSCOS_DB', "'mtscos.db'"),
        ]
        new_lines = []
        import_inserted = False
        after_base_sys_path = False
        for i, line in enumerate(lines):
            if not after_base_sys_path:
                if 'BASE_DIR' in line and 'os.path.dirname(os.path.abspath(__file__))' in line:
                    after_base_sys_path = True
                if 'sys.path.insert' in line:
                    after_base_sys_path = True
            matched = False
            for const_name, db_name in db_constants:
                m = re.match(
                    r'^(\s*)' + re.escape(const_name) + r'\s*=\s*os\.path\.join\([^)]+\)\s*$',
                    line
                )
                if m and after_base_sys_path:
                    indent = m.group(1)
                    if not import_inserted and 'from core.db_path import get_db_path' not in content:
                        new_lines.append(line)
                        insert_idx = 0
                        tmp_lines = list(new_lines)
                        for k in range(len(tmp_lines)):
                            ln = tmp_lines[k]
                            if re.match(r'^\s*(from|import)\s+', ln) and 'from flask' not in ln:
                                insert_idx = k + 1
                                continue
                        if insert_idx == 0:
                            insert_idx = len(new_lines) - 1
                        import_line = 'from core.db_path import get_db_path'
                        new_lines.insert(max(insert_idx, 0), import_line)
                        import_inserted = True
                        count += 1
                        matched = True
                        break
                    new_lines.append(indent + const_name + " = get_db_path(" + db_name + ")")
                    count += 1
                    matched = True
                    break
            if not matched:
                new_lines.append(line)
        return '\n'.join(new_lines), count

    fp_g = os.path.join(PROJECT_ROOT, 'server_real_db.py')
    count_and_apply(fp_g, fix_g)

def main():
    print("=" * 70)
    print("  MTSCOS 数据库路径修正脚本")
    print("=" * 70)
    print(f"项目根目录: {PROJECT_ROOT}")
    print()

    print("[任务1] 批量替换 DATABASE_PATH 自引用...")
    before = len(modified_files)
    task1_fix_database_path()
    task1_files = len(modified_files) - before
    print(f"  完成: 处理了 {task1_files} 个文件")
    print()

    print("[任务2] 修正 split_databases 错误路径...")
    before = len(modified_files)
    task2_fix_split_databases()
    task2_files = len(modified_files) - before
    print(f"  完成: 处理了 {task2_files} 个文件")
    print()

    print("=" * 70)
    print("  修改统计")
    print("=" * 70)
    print(f"总修改文件数: {len(modified_files)}")
    print(f"总修改行数:   {total_line_changes}")
    print()
    if modified_files:
        print("修改文件列表:")
        print("-" * 70)
        for fp, cnt in modified_files:
            rel = os.path.relpath(fp, PROJECT_ROOT)
            print(f"  {rel:60s} +{cnt} 行")
    print()
    print("完成。")

if __name__ == '__main__':
    main()
