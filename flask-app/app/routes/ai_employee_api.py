# -*- coding: utf-8 -*-
"""
AI员工API路由
提供代码错误检测和修复的API接口
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
import uuid

# 导入错误修复服务
from app.services.ai_error_fixer import (
    ErrorFixer,
    MathErrorDetector,
    ExceptionErrorDetector,
    LogicErrorDetector,
    fix_code
)

# 导入数据库模型
from app.models.ai_employee import (
    AIEmployee,
    ErrorType,
    Solution,
    FixTask,
    LearningRecord,
    AIEmployeeStatus,
    ErrorCategory,
    ErrorSeverity,
    SolutionStatus
)

# 创建蓝图
ai_employee_bp = Blueprint('ai_employee', __name__, url_prefix='/api/ai-employee')


@ai_employee_bp.route('/')
def index():
    """AI员工管理首页"""
    return render_template('admin/ai_employee.html')


@ai_employee_bp.route('/detect', methods=['POST'])
def detect_errors():
    """
    检测代码错误
    POST /api/ai-employee/detect
    {
        "code": "代码内容",
        "language": "python"
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({
                'success': False,
                'error': '代码不能为空'
            }), 400
        
        # 使用错误检测器
        fixer = ErrorFixer()
        errors = fixer.detect_all_errors(code, language)
        
        # 统计各类错误
        error_stats = {}
        for error in errors:
            error_type = error.get('type', 'unknown')
            severity = error.get('severity', 'info')
            
            if error_type not in error_stats:
                error_stats[error_type] = {
                    'count': 0,
                    'severity': severity,
                    'errors': []
                }
            
            error_stats[error_type]['count'] += 1
            error_stats[error_type]['errors'].append(error)
        
        return jsonify({
            'success': True,
            'data': {
                'errors': errors,
                'total_errors': len(errors),
                'error_stats': error_stats,
                'code_lines': len(code.split('\n'))
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/fix', methods=['POST'])
def fix_errors():
    """
    修复代码错误
    POST /api/ai-employee/fix
    {
        "code": "代码内容",
        "language": "python",
        "auto_fix": true
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        language = data.get('language', 'python')
        auto_fix = data.get('auto_fix', True)
        
        if not code:
            return jsonify({
                'success': False,
                'error': '代码不能为空'
            }), 400
        
        # 使用错误修复器
        result = fix_code(code, language)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/fix-single', methods=['POST'])
def fix_single_error():
    """
    修复单个错误
    POST /api/ai-employee/fix-single
    {
        "code": "代码内容",
        "error": {
            "type": "division_by_zero",
            "line": 5,
            "message": "..."
        }
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        error_info = data.get('error', {})
        
        if not code:
            return jsonify({
                'success': False,
                'error': '代码不能为空'
            }), 400
        
        fixer = ErrorFixer()
        fixed_code, explanation = fixer.fix_error(code, error_info)
        
        return jsonify({
            'success': True,
            'data': {
                'original_code': code,
                'fixed_code': fixed_code,
                'explanation': explanation,
                'is_fixed': fixed_code != code
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/fix-all', methods=['POST'])
def fix_all_problems():
    """
    强力修复所有问题 - 调用AI任务调度器进行全面修复
    POST /api/ai-employee/fix-all
    {
        "code": "代码内容",
        "language": "python"
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({
                'success': False,
                'error': '代码不能为空'
            }), 400
        
        import time
        start_time = time.time()
        
        from app.ai.ai_task_scheduler import get_ai_task_scheduler
        scheduler = get_ai_task_scheduler()
        
        fixer = ErrorFixer()
        errors = fixer.detect_all_errors(code, language)
        
        if not errors:
            return jsonify({
                'success': True,
                'data': {
                    'original_code': code,
                    'fixed_code': code,
                    'errors': [],
                    'fix_reports': [],
                    'total_errors': 0,
                    'fixed_count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'repair_report': {
                        'report_id': str(uuid.uuid4()),
                        'employees_count': 0,
                        'strategy': '无需修复',
                        'diagnosis_time': f"{(time.time() - start_time):.2f}s",
                        'fix_time': "0s",
                        'reported_to_db': True,
                        'employees': []
                    }
                }
            })
        
        problems_data = []
        for error in errors:
            problems_data.append({
                'problem_id': f"code_error_{error.get('type')}_{error.get('line', 0)}",
                'severity': error.get('severity', 'medium'),
                'category': 'code_error',
                'title': error.get('message', '代码错误'),
                'description': f"第 {error.get('line', 0)} 行: {error.get('message', '')}",
                'recommendation': error.get('suggestion', ''),
                'error_data': error
            })
        
        fix_result = scheduler.submit_problems_for_fix(problems_data)
        
        scheduler.start_scheduler()
        time.sleep(5)
        
        tasks = scheduler.get_all_tasks()
        completed_tasks = [t for t in tasks if t['status'] == 'completed']
        successful_fixes = [t for t in completed_tasks if t['success']]
        
        fixed_code = code
        fix_reports = []
        for task in successful_fixes:
            if task.get('fix_result'):
                fixed_code = task['fix_result'].get('fixed_code', fixed_code)
                fix_reports.append({
                    'original_error': task.get('problem_data', {}).get('error_data', {}),
                    'explanation': task.get('fix_result', {}).get('explanation', ''),
                    'fixed': True
                })
        
        final_errors = fixer.detect_all_errors(fixed_code, language)
        
        repair_report = scheduler.generate_repair_report(problems_data)
        repair_report['diagnosis_time'] = f"{(time.time() - start_time):.2f}s"
        repair_report['report_id'] = str(uuid.uuid4())
        repair_report['reported_to_db'] = True
        
        scheduler.report_to_database(problems_data, completed_tasks)
        
        end_time = time.time()
        
        return jsonify({
            'success': True,
            'data': {
                'original_code': code,
                'fixed_code': fixed_code,
                'errors': final_errors,
                'fix_reports': fix_reports,
                'total_errors': len(errors),
                'fixed_count': len(fix_reports),
                'timestamp': datetime.now().isoformat(),
                'repair_report': repair_report,
                'execution_time': f"{(end_time - start_time):.2f}s"
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_employee_bp.route('/test-code', methods=['POST'])
def test_fixed_code():
    """
    测试修复后的代码
    POST /api/ai-employee/test-code
    {
        "code": "修复后的代码"
    }
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({
                'success': False,
                'error': '代码不能为空'
            }), 400
        
        # 尝试执行代码
        result = {
            'executed': False,
            'output': '',
            'error': None,
            'success': True
        }
        
        try:
            # 捕获输出
            import sys
            from io import StringIO
            
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            exec(code, {'__name__': '__test__'})
            
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            result['executed'] = True
            result['output'] = output
            
        except SyntaxError as e:
            result['success'] = False
            result['error'] = {
                'type': 'SyntaxError',
                'message': str(e),
                'line': e.lineno
            }
        except Exception as e:
            result['success'] = False
            result['error'] = {
                'type': type(e).__name__,
                'message': str(e)
            }
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/employees', methods=['GET'])
def get_employees():
    """获取AI员工列表"""
    try:
        from app import db
        
        employees = db.session.query(AIEmployee).all()
        
        return jsonify({
            'success': True,
            'data': [emp.to_dict() for emp in employees]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/employees/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
    """获取单个AI员工信息"""
    try:
        from app import db
        
        employee = db.session.query(AIEmployee).get(emp_id)
        
        if not employee:
            return jsonify({
                'success': False,
                'error': 'AI员工不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': employee.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/error-types', methods=['GET'])
def get_error_types():
    """获取错误类型列表"""
    try:
        from app import db
        
        error_types = db.session.query(ErrorType).filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'data': [et.to_dict() for et in error_types]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/solutions', methods=['GET'])
def get_solutions():
    """获取解决方案列表"""
    try:
        from app import db
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = db.session.query(Solution)
        
        if status:
            query = query.filter_by(status=status)
        
        solutions = query.order_by(Solution.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'solutions': [sol.to_dict() for sol in solutions.items],
                'total': solutions.total,
                'page': solutions.page,
                'pages': solutions.pages,
                'has_next': solutions.has_next,
                'has_prev': solutions.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/solutions', methods=['POST'])
def create_solution():
    """创建解决方案"""
    try:
        from app import db
        
        data = request.get_json()
        
        solution = Solution(
            title=data.get('title'),
            error_type_id=data.get('error_type_id'),
            ai_employee_id=data.get('ai_employee_id'),
            problem_description=data.get('problem_description'),
            problem_code=data.get('problem_code'),
            error_message=data.get('error_message'),
            solution_code=data.get('solution_code'),
            explanation=data.get('explanation'),
            steps=data.get('steps', []),
            status=SolutionStatus.PENDING,
            created_by=data.get('created_by')
        )
        
        db.session.add(solution)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': solution.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/solutions/<int:sol_id>/approve', methods=['POST'])
def approve_solution(sol_id):
    """批准解决方案"""
    try:
        from app import db
        
        solution = db.session.query(Solution).get(sol_id)
        
        if not solution:
            return jsonify({
                'success': False,
                'error': '解决方案不存在'
            }), 404
        
        solution.status = SolutionStatus.APPROVED
        solution.approved_by = request.json.get('approved_by')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': solution.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """获取修复任务列表"""
    try:
        from app import db
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = db.session.query(FixTask)
        
        if status:
            query = query.filter_by(status=status)
        
        tasks = query.order_by(FixTask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': [task.to_dict() for task in tasks.items],
                'total': tasks.total,
                'page': tasks.page,
                'pages': tasks.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/tasks', methods=['POST'])
def create_task():
    """创建修复任务"""
    try:
        from app import db
        
        data = request.get_json()
        
        # 生成任务编号
        task_code = f"FIX-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        task = FixTask(
            task_code=task_code,
            error_type_id=data.get('error_type_id'),
            ai_employee_id=data.get('ai_employee_id'),
            source_file=data.get('source_file'),
            source_code=data.get('source_code'),
            error_line=data.get('error_line'),
            error_message=data.get('error_message'),
            priority=data.get('priority', 0),
            status='pending',
            created_by=data.get('created_by')
        )
        
        db.session.add(task)
        db.session.commit()
        
        # 自动执行修复
        fixer = ErrorFixer()
        errors = fixer.detect_all_errors(task.source_code)
        
        if errors:
            fixed_code, fix_reports = fixer.auto_fix_all(task.source_code)
            task.fixed_code = fixed_code
            task.status = 'completed' if fix_reports else 'failed'
            task.is_successful = len(fix_reports) > 0
            task.end_time = datetime.utcnow()
            
            # 计算执行时间
            if task.start_time:
                task.execution_time = (task.end_time - task.start_time).total_seconds()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/learning/record', methods=['POST'])
def record_learning():
    """记录学习"""
    try:
        from app import db
        
        data = request.get_json()
        
        record = LearningRecord(
            ai_employee_id=data.get('ai_employee_id'),
            solution_id=data.get('solution_id'),
            fix_task_id=data.get('fix_task_id'),
            input_data=data.get('input_data'),
            output_data=data.get('output_data'),
            expected_output=data.get('expected_output'),
            is_correct=data.get('is_correct', False),
            error_type=data.get('error_type'),
            error_details=data.get('error_details'),
            loss_value=data.get('loss_value'),
            accuracy=data.get('accuracy'),
            learning_time=data.get('learning_time'),
            learning_type=data.get('learning_type')
        )
        
        db.session.add(record)
        db.session.commit()
        
        # 更新AI员工的学习统计
        if data.get('ai_employee_id'):
            employee = db.session.query(AIEmployee).get(data['ai_employee_id'])
            if employee:
                employee.knowledge_base_size += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_employee_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        from app import db
        from sqlalchemy import func
        
        # 统计AI员工
        total_employees = db.session.query(func.count(AIEmployee.id)).scalar()
        active_employees = db.session.query(func.count(AIEmployee.id)).filter(
            AIEmployee.status == AIEmployeeStatus.ACTIVE
        ).scalar()
        
        # 统计错误类型
        total_error_types = db.session.query(func.count(ErrorType.id)).filter(
            ErrorType.is_active == True
        ).scalar()
        
        # 统计解决方案
        total_solutions = db.session.query(func.count(Solution.id)).scalar()
        approved_solutions = db.session.query(func.count(Solution.id)).filter(
            Solution.status == SolutionStatus.APPROVED
        ).scalar()
        
        # 统计修复任务
        total_tasks = db.session.query(func.count(FixTask.id)).scalar()
        successful_tasks = db.session.query(func.count(FixTask.id)).filter(
            FixTask.is_successful == True
        ).scalar()
        
        # 计算成功率
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 统计各类错误
        error_counts = db.session.query(
            ErrorType.category,
            func.count(ErrorType.id)
        ).group_by(ErrorType.category).all()
        
        return jsonify({
            'success': True,
            'data': {
                'employees': {
                    'total': total_employees,
                    'active': active_employees
                },
                'error_types': {
                    'total': total_error_types
                },
                'solutions': {
                    'total': total_solutions,
                    'approved': approved_solutions
                },
                'tasks': {
                    'total': total_tasks,
                    'successful': successful_tasks,
                    'success_rate': round(success_rate, 2)
                },
                'error_distribution': [
                    {'category': cat.value, 'count': count}
                    for cat, count in error_counts
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 导出蓝图
__all__ = ['ai_employee_bp']
