#!/usr/bin/env python3
"""批量修复剩余28个文件的语法错误
针对常见错误模式进行修复：
1. 文档字符串后直接跟代码
2. logger/print调用后直接跟代码
3. 赋值语句后直接跟代码
4. 注释后闭合括号
5. 多行字符串未闭合
"""
import os
import ast
import re
from typing import Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def fix_docstring_merge(lines: list, idx: int) -> Optional[list]:
    """修复文档字符串后直接跟代码
    例如: \"\"\"扫描整个系统\"\"\"logger.info(...)
    例如: \"\"\"self.db_path = db_path (文档字符串没闭合)
    """
    line = lines[idx]
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    # 情况1: """text"""code - 文档字符串闭合后直接跟代码
    # 匹配: """..."""后面紧跟非空字符
    m = re.match(r'^(\s*"""[^"]*""")(\S.*)$', line)
    if m:
        docstring = m.group(1)
        rest = m.group(2)
        new_lines = lines.copy()
        new_lines[idx] = docstring
        # 文档字符串后的代码使用相同缩进，不是 indent+4
        new_lines.insert(idx + 1, ' ' * indent + rest)
        return new_lines
    
    # 也处理单引号的情况
    m = re.match(r"^(\s*'''[^']*''')(\S.*)$", line)
    if m:
        docstring = m.group(1)
        rest = m.group(2)
        new_lines = lines.copy()
        new_lines[idx] = docstring
        new_lines.insert(idx + 1, ' ' * indent + rest)
        return new_lines
    
    # 情况2: """code - 文档字符串的结束引号后直接跟代码
    # 例如: """self.db_path = db_path
    # 例如: """import os
    # 这里 """ 是文档字符串的结束，后面跟了代码
    if stripped.startswith('"""') and not stripped.startswith('""""""'):
        # 检查是否是 """text"""code 的情况（已经由情况1处理）
        # 或者是 """code 的情况（结束引号后跟代码）
        rest_after_docstring = stripped[3:]
        # 如果 rest_after_docstring 不以 """ 开头，说明这是结束引号后跟代码
        if rest_after_docstring and not rest_after_docstring.startswith('"""'):
            # 这是 """code 的情况
            new_lines = lines.copy()
            new_lines[idx] = ' ' * indent + '"""'
            new_lines.insert(idx + 1, ' ' * indent + rest_after_docstring)
            return new_lines
    
    # 同样处理 '''code 的情况
    if stripped.startswith("'''") and not stripped.startswith("''''''"):
        rest_after_docstring = stripped[3:]
        if rest_after_docstring and not rest_after_docstring.startswith("'''"):
            new_lines = lines.copy()
            new_lines[idx] = ' ' * indent + "'''"
            new_lines.insert(idx + 1, ' ' * indent + rest_after_docstring)
            return new_lines
    
    return None


def fix_call_merge(lines: list, idx: int) -> Optional[list]:
    """修复函数调用后直接跟代码
    例如: logger.info("...")return True
    例如: print(f"...")return True
    例如: logger.error(f"...")return {...}
    """
    line = lines[idx]
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    # 找到右括号后面紧跟的非空字符
    # 需要跟踪括号深度和字符串状态
    pos = 0
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    in_string = False
    string_char = None
    triple_quote = False
    
    while pos < len(stripped):
        c = stripped[pos]
        
        if c == '\\':
            pos += 2
            continue
        
        # 处理三引号
        if pos + 2 < len(stripped) and stripped[pos:pos+3] in ('"""', "'''"):
            tq = stripped[pos:pos+3]
            if triple_quote and string_char == tq[0]:
                triple_quote = False
                in_string = False
                string_char = None
                pos += 3
                continue
            elif not in_string:
                triple_quote = True
                in_string = True
                string_char = tq[0]
                pos += 3
                continue
        
        if c in ('"', "'") and not triple_quote:
            if not in_string:
                in_string = True
                string_char = c
            elif string_char == c:
                in_string = False
                string_char = None
            pos += 1
            continue
        
        if in_string:
            pos += 1
            continue
        
        if c == '(':
            paren_depth += 1
        elif c == ')':
            paren_depth -= 1
            if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                # 找到了函数调用的右括号
                # 检查后面是否有代码
                after = stripped[pos + 1:].strip()
                if after and not after.startswith('#') and not after.startswith('.') and not after.startswith(','):
                    # 检查后面不是操作符
                    if after[0] not in ('+', '-', '*', '/', '%', '=', '!', '<', '>', '&', '|', '^', '~', ':'):
                        # 拆分
                        before = stripped[:pos + 1]
                        new_lines = lines.copy()
                        new_lines[idx] = ' ' * indent + before
                        new_lines.insert(idx + 1, ' ' * indent + after)
                        return new_lines
                    # 如果是冒号，也拆分（如 if x:result = ...）
                    if after[0] == ':':
                        before = stripped[:pos + 1]
                        new_lines = lines.copy()
                        new_lines[idx] = ' ' * indent + before
                        new_lines.insert(idx + 1, ' ' * (indent + 4) + after)
                        return new_lines
        elif c == '[':
            bracket_depth += 1
        elif c == ']':
            bracket_depth -= 1
        elif c == '{':
            brace_depth += 1
        elif c == '}':
            brace_depth -= 1
            if brace_depth == 0 and paren_depth == 0 and bracket_depth == 0:
                # 字典/集合的右括号
                after = stripped[pos + 1:].strip()
                if after and not after.startswith('#') and not after.startswith('.') and not after.startswith(','):
                    if after[0] not in ('+', '-', '*', '/', '%', '=', '!', '<', '>', '&', '|', '^', '~', ':'):
                        before = stripped[:pos + 1]
                        new_lines = lines.copy()
                        new_lines[idx] = ' ' * indent + before
                        new_lines.insert(idx + 1, ' ' * indent + after)
                        return new_lines
        
        pos += 1
    
    return None


def fix_comment_bracket(lines: list, idx: int) -> Optional[list]:
    """修复注释后面的闭合括号
    例如: "capabilities": []      # 能力库}
    """
    line = lines[idx]
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    # 找到注释位置
    comment_pos = -1
    in_string = False
    string_char = None
    
    for i, c in enumerate(stripped):
        if c == '\\':
            continue
        if c in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = c
            elif string_char == c:
                in_string = False
            continue
        if in_string:
            continue
        if c == '#':
            comment_pos = i
            break
    
    if comment_pos == -1:
        return None
    
    after_comment = stripped[comment_pos + 1:]
    close_brackets = [c for c in after_comment if c in ')}]']
    
    if close_brackets:
        new_line = stripped[:comment_pos].rstrip() + ''.join(close_brackets) + '  ' + stripped[comment_pos:]
        new_lines = lines.copy()
        new_lines[idx] = ' ' * indent + new_line
        return new_lines
    
    return None


def fix_unclosed_docstring(lines: list, idx: int) -> Optional[list]:
    """修复未闭合的文档字符串
    例如: \"\"\"self.db_path = db_path (应该闭合文档字符串)
    """
    line = lines[idx]
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    # 检查是否以 """ 开头但没有闭合
    if stripped.startswith('"""') and not stripped.endswith('"""'):
        # 统计三引号数量
        count = stripped.count('"""')
        if count == 1:
            # 只有一个三引号，需要闭合
            # 文档字符串内容是从 """ 后面到行尾
            content = stripped[3:]
            new_lines = lines.copy()
            new_lines[idx] = ' ' * indent + '"""' + content + '"""'
            return new_lines
        elif count == 2:
            # 有两个三引号，但可能内容中有代码
            # 例如: """text"""code
            pass
    
    return None


def fix_fstring_merge(lines: list, idx: int) -> Optional[list]:
    """修复f字符串赋值后直接跟代码
    例如: rec_id = f"rec_{int(time.time() * 1000)}_{rid[:8]}"cursor.execute(...)
    """
    line = lines[idx]
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    # 找到f字符串的闭合引号
    # f字符串可以是 f"..." 或 f'...'
    pos = 0
    in_fstring = False
    fstring_char = None
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    
    while pos < len(stripped):
        c = stripped[pos]
        
        if c == '\\':
            pos += 2
            continue
        
        # 检查f字符串开始
        if not in_fstring and pos + 1 < len(stripped):
            if stripped[pos:pos+2] in ('f"', "f'"):
                in_fstring = True
                fstring_char = stripped[pos + 1]
                pos += 2
                continue
            if stripped[pos:pos+2] in ('F"', "F'"):
                in_fstring = True
                fstring_char = stripped[pos + 1]
                pos += 2
                continue
        
        if in_fstring:
            if c == '{':
                brace_depth += 1
            elif c == '}':
                brace_depth -= 1
            elif c == fstring_char and brace_depth == 0:
                # f字符串闭合
                in_fstring = False
                # 检查后面是否有代码
                after = stripped[pos + 1:].strip()
                if after and not after.startswith('#') and not after.startswith('.') and not after.startswith(',') and not after.startswith(')'):
                    if after[0] not in ('+', '-', '*', '/', '%', '=', '!', '<', '>', '&', '|', '^', '~', ':'):
                        before = stripped[:pos + 1]
                        new_lines = lines.copy()
                        new_lines[idx] = ' ' * indent + before
                        new_lines.insert(idx + 1, ' ' * indent + after)
                        return new_lines
            pos += 1
            continue
        
        if c == '(':
            paren_depth += 1
        elif c == ')':
            paren_depth -= 1
        elif c == '[':
            bracket_depth += 1
        elif c == ']':
            bracket_depth -= 1
        
        pos += 1
    
    return None


def fix_multiline_string(lines: list, idx: int) -> Optional[list]:
    """修复多行字符串未闭合的问题
    例如: "Keynote Speaker: The intersection of quantum computing... (未闭合)
    """
    line = lines[idx]
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    # 检查是否是未闭合的字符串
    # 如果行以 " 开头但没有闭合的 "
    if (stripped.startswith('"') and not stripped.endswith('"')) or \
       (stripped.startswith("'") and not stripped.endswith("'")):
        # 可能是多行字符串，用三引号包裹
        # 先检查后面的行是否有闭合引号
        string_char = stripped[0]
        
        # 查看后续几行
        end_idx = idx
        for j in range(idx + 1, min(len(lines), idx + 20)):
            if string_char in lines[j]:
                end_idx = j
                break
        
        if end_idx > idx:
            # 用三引号包裹
            new_lines = lines.copy()
            # 修改开始行
            content_start = stripped[1:]  # 去掉开头的引号
            new_lines[idx] = ' ' * indent + '"""' + content_start
            # 修改结束行
            end_line = lines[end_idx]
            end_stripped = end_line.strip()
            # 找到最后一个引号的位置
            last_quote = end_stripped.rfind(string_char)
            if last_quote >= 0:
                new_end = end_stripped[:last_quote] + '"""' + end_stripped[last_quote + 1:]
                new_lines[end_idx] = ' ' * (len(end_line) - len(end_line.lstrip())) + new_end
                return new_lines
    
    return None


def fix_file(file_path: str) -> Tuple[bool, str]:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            return True, '已经正确'
        except SyntaxError:
            pass
        
        lines = content.split('\n')
        max_iterations = 200
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                ast.parse('\n'.join(lines))
                # 修复成功，保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                return True, f'修复成功 (迭代{iteration}次)'
            except SyntaxError as e:
                line_idx = e.lineno - 1
                if line_idx >= len(lines):
                    return False, f'错误行号超出范围: {e.lineno}'
                
                error_msg = e.msg
                
                # 尝试各种修复策略
                fixed = None
                
                # 策略1: 文档字符串后直接跟代码
                fixed = fix_docstring_merge(lines, line_idx)
                if fixed is None:
                    # 策略1.5: 未闭合的文档字符串
                    fixed = fix_unclosed_docstring(lines, line_idx)
                
                # 策略2: 注释后闭合括号 (检查当前行和前一行)
                if fixed is None and '#' in lines[line_idx].strip():
                    fixed = fix_comment_bracket(lines, line_idx)
                if fixed is None and line_idx > 0 and '#' in lines[line_idx - 1].strip():
                    fixed = fix_comment_bracket(lines, line_idx - 1)
                
                # 策略3: 函数调用后直接跟代码
                if fixed is None:
                    fixed = fix_call_merge(lines, line_idx)
                
                # 策略3.5: 检查前一行是否是函数调用合并
                if fixed is None and line_idx > 0:
                    prev_line = lines[line_idx - 1]
                    prev_stripped = prev_line.strip()
                    # 如果前一行看起来像合并的语句
                    if ('logger.' in prev_stripped or 'print(' in prev_stripped or 
                        'cursor.' in prev_stripped or 'conn.' in prev_stripped):
                        fixed = fix_call_merge(lines, line_idx - 1)
                
                # 策略4: f字符串赋值后直接跟代码
                if fixed is None:
                    fixed = fix_fstring_merge(lines, line_idx)
                
                # 策略4.5: 检查前一行是否是f字符串合并
                if fixed is None and line_idx > 0:
                    prev_line = lines[line_idx - 1]
                    if 'f"' in prev_line or "f'" in prev_line:
                        fixed = fix_fstring_merge(lines, line_idx - 1)
                
                # 策略5: 多行字符串未闭合
                if fixed is None and ('EOL' in error_msg or 'EOF' in error_msg):
                    fixed = fix_multiline_string(lines, line_idx)
                
                # 策略6: 冒号语句后直接跟代码 (if/elif/else/for/while/with/def/class/try/except/finally)
                if fixed is None and 'invalid syntax' in error_msg:
                    line = lines[line_idx]
                    stripped = line.strip()
                    indent = len(line) - len(line.lstrip())
                    
                    # 检查是否是冒号语句
                    keywords = ['if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 
                               'def ', 'class ', 'try:', 'except ', 'finally:']
                    for kw in keywords:
                        if stripped.startswith(kw):
                            # 找到冒号位置（在括号外）
                            pos = 0
                            paren_depth = 0
                            bracket_depth = 0
                            brace_depth = 0
                            in_string = False
                            string_char = None
                            
                            while pos < len(stripped):
                                c = stripped[pos]
                                if c == '\\':
                                    pos += 2
                                    continue
                                if c in ('"', "'"):
                                    if not in_string:
                                        in_string = True
                                        string_char = c
                                    elif string_char == c:
                                        in_string = False
                                    pos += 1
                                    continue
                                if in_string:
                                    pos += 1
                                    continue
                                if c == '(':
                                    paren_depth += 1
                                elif c == ')':
                                    paren_depth -= 1
                                elif c == '[':
                                    bracket_depth += 1
                                elif c == ']':
                                    bracket_depth -= 1
                                elif c == '{':
                                    brace_depth += 1
                                elif c == '}':
                                    brace_depth -= 1
                                elif c == ':' and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                                    after = stripped[pos + 1:].strip()
                                    if after and not after.startswith('#'):
                                        before = stripped[:pos + 1]
                                        fixed = lines.copy()
                                        fixed[line_idx] = ' ' * indent + before
                                        fixed.insert(line_idx + 1, ' ' * (indent + 4) + after)
                                    break
                                pos += 1
                            if fixed is not None:
                                break
                
                # 策略7: unexpected indent - 前一行是单行冒号语句
                if fixed is None and 'unexpected indent' in error_msg and line_idx > 0:
                    prev_line = lines[line_idx - 1]
                    prev_stripped = prev_line.strip()
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    
                    # 检查前一行是否是 if/elif/else/for/while/with 后跟冒号和代码
                    keywords = ['if ', 'elif ', 'else:', 'for ', 'while ', 'with ']
                    for kw in keywords:
                        if prev_stripped.startswith(kw):
                            # 找到冒号
                            colon_pos = -1
                            paren_depth = 0
                            in_string = False
                            string_char = None
                            for i, c in enumerate(prev_stripped):
                                if c == '\\':
                                    continue
                                if c in ('"', "'"):
                                    if not in_string:
                                        in_string = True
                                        string_char = c
                                    elif string_char == c:
                                        in_string = False
                                    continue
                                if in_string:
                                    continue
                                if c == '(':
                                    paren_depth += 1
                                elif c == ')':
                                    paren_depth -= 1
                                elif c == ':' and paren_depth == 0:
                                    colon_pos = i
                                    break
                            
                            if colon_pos >= 0:
                                before = prev_stripped[:colon_pos + 1]
                                after = prev_stripped[colon_pos + 1:].strip()
                                if after:
                                    fixed = lines.copy()
                                    fixed[line_idx - 1] = ' ' * prev_indent + before
                                    fixed.insert(line_idx, ' ' * (prev_indent + 4) + after)
                                    break
                
                if fixed is None:
                    return False, f'无法修复行{e.lineno}: {error_msg}'
                
                lines = fixed
        
        return False, f'达到最大迭代次数'
    
    except Exception as e:
        return False, str(e)


def main():
    # 28个核心文件
    files = [
        'ai_engines/ai_agent_auto_config.py', 'ai_engines/ai_brain_library.py',
        'ai_engines/ai_brain_search_enhancer.py', 'ai_engines/ai_engine_v3.py',
        'ai_engines/ai_log_analyzer.py', 'ai_engines/ai_management.py',
        'ai_engines/ai_performance_monitor.py', 'ai_engines/ai_question_maintenance.py',
        'ai_engines/ai_rule_enhancer.py', 'ai_engines/ai_self_learning_empowered.py',
        'ai_engines/ai_service.py', 'ai_engines/ai_system_monitor.py',
        'ai_engines/arduino_ai_employees.py', 'ai_engines/code_analyzer.py',
        'ai_engines/feature_library_manager.py', 'ai_engines/frontend_backend_sync_ai.py',
        'ai_engines/frontend_fixer_ai.py', 'ai_engines/gamification_engine.py',
        'ai_engines/home_school_communication_engine.py', 'ai_engines/knowledge_base_engine.py',
        'ai_engines/learning_visualization_engine.py', 'ai_engines/math_questions_perfect_ai.py',
        'ai_engines/multi_code_repair_ai.py', 'ai_engines/resource_recommendation_engine.py',
        'ai_engines/rule_base_maintenance_employee.py', 'ai_engines/smart_schedule_engine.py',
        'ai_engines/standalone_ai_brain_map.py', 'ai_engines/system_auto_processor.py',
    ]
    
    print("=" * 60)
    print("批量修复28个核心文件")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    
    for fp in files:
        full_path = os.path.join(PROJECT_ROOT, fp)
        basename = os.path.basename(fp)
        
        success, reason = fix_file(full_path)
        
        if success:
            success_count += 1
            print(f"✅ {basename}: {reason}")
        else:
            failed_count += 1
            print(f"❌ {basename}: {reason}")
    
    print()
    print("=" * 60)
    print(f"修复完成!")
    print(f"  ✅ 成功: {success_count}")
    print(f"  ❌ 失败: {failed_count}")
    print(f"  总计: {len(files)}")
    print(f"  成功率: {success_count / len(files) * 100:.1f}%")
    print("=" * 60)


if __name__ == '__main__':
    main()
