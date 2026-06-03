#!/usr/bin/env python3
"""
AI脑库解释器
用于管理和操作AI脑库的命令行解释器

"""
import logging
logger = logging.getLogger(__name__)
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_interpreter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ai_interpreter')

class Token:
    """词法标记类"""
    def __init__(self, token_type: str, value: Any):
        self.token_type = token_type
        self.value = value

    def __str__(self) -> str:
        return f"Token({self.token_type}, {self.value})"

class Lexer:
    """词法分析器"""
    def __init__(self, input_str: str):
        self.input = input_str
        self.position = 0
        self.current_char = self.input[self.position] if self.input else None

    def advance(self) -> None:
        """前进到下一个字符"""
        self.position += 1
        if self.position < len(self.input):
            self.current_char = self.input[self.position]
        else:
            self.current_char = None

    def skip_whitespace(self) -> None:
        """跳过空白字符"""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self) -> None:
        """跳过注释"""
        if self.current_char == '#':
            while self.current_char is not None and self.current_char != '\n':
                self.advance()
    def number(self) -> Token:
        """解析数字"""
        result = ''
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            result += self.current_char
            self.advance()
        try:
            if '.' in result:
                return Token('NUMBER', float(result))
            else:
                return Token('NUMBER', int(result))
        except ValueError:
            logger.error(f"无效的数字: {result}")
            return Token('ERROR', result)

    def string(self) -> Token:
        """解析字符串"""
        result = ''
        # 跳过引号
        self.advance()
        while self.current_char is not None and self.current_char != '"':
        # 跳过结束引号
            self.advance()
        return Token('STRING', result)
    def identifier(self) -> Token:
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_' or self.current_char == '-'):
            result += self.current_char
            self.advance()

        keywords = ['update', 'query', 'config', 'status', 'brain', '--source', '--type', '--keyword', '--limit', '--key', '--value', '--dry-run']
        if result in keywords:
            return Token('KEYWORD', result)
        return Token('IDENTIFIER', result)

    def get_next_token(self) -> Token:
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '#':
                self.skip_comment()
                continue

            if self.current_char.isdigit():
                return self.number()

            if self.current_char == '"':
                return self.string()

            if self.current_char.isalpha() or self.current_char == '_' or self.current_char == '-':
                return self.identifier()

            if self.current_char == '--':
                start = self.position
                self.advance()
            # 未知字符
            logger.error(f"未知字符: {self.current_char}")
            self.advance()

class ASTNode:
    """抽象语法树节点基类"""
    def __init__(self, node_type: str):
        self.node_type = node_type

class CommandNode(ASTNode):
    """命令节点"""
    def __init__(self, command: str, arguments: Dict[str, Any]):
        super().__init__('COMMAND')
        self.command = command

    def __str__(self) -> str:
        return f"CommandNode({self.command}, {self.arguments})"

class Parser:
    """语法分析器"""
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type: str) -> None:
        """验证当前标记类型并前进"""
        if self.current_token.token_type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            logger.error(f"语法错误: 期望 {token_type},但得到 {self.current_token.token_type}")

    def parse(self) -> CommandNode:
        """解析命令"""
        # 解析主命令
        if self.current_token.token_type not in ['UPDATE', 'QUERY', 'CONFIG', 'STATUS']:
            logger.error(f"语法错误: 期望命令,但得到 {self.current_token.value}")
            raise SyntaxError(f"语法错误: 期望命令,但得到 {self.current_token.value}")

        command = self.current_token.value.lower()
        self.eat(self.current_token.token_type)

        # 解析命令对象(目前只支持brain)
        if self.current_token.token_type != 'BRAIN':
            logger.error(f"语法错误: 期望 brain,但得到 {self.current_token.value}")
            raise SyntaxError(f"语法错误: 期望 brain,但得到 {self.current_token.value}")
        self.eat('BRAIN')

        arguments = {}
        # 标志选项列表,不需要值
        flag_options = ['--dry-run']

        while self.current_token.token_type != 'EOF':
            if self.current_token.value.lower() in flag_options:
                # 处理标志选项
                option = self.current_token.value.lower()
                self.eat(self.current_token.token_type)
                # 移除--前缀
                option_key = option[2:]
                arguments[option_key] = True
            elif self.current_token.token_type.startswith('--'):
                # 解析需要值的选项
                option = self.current_token.value.lower()
                self.eat(self.current_token.token_type)

                # 解析选项值
                if self.current_token.token_type in ['STRING', 'NUMBER', 'IDENTIFIER']:
                    value = self.current_token.value
                    self.eat(self.current_token.token_type)
                    # 移除--前缀
                    option_key = option[2:]
                    arguments[option_key] = value
                else:
                    logger.error(f"语法错误: 期望选项值,但得到 {self.current_token.token_type}")
            else:
                logger.error(f"语法错误: 期望选项,但得到 {self.current_token.value}")

        return CommandNode(command, arguments)
class CommandHandler:
    """命令处理器"""
    def __init__(self):
        self.command_map: Dict[str, Callable] = {
            'update': self.handle_update,
            'query': self.handle_query,
        }

    def handle_update(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"处理更新命令,参数: {arguments}")

        # 这里将调用ai_brain_updater.py中的功能
        try:
            updater = AIBrainUpdater()
            result = updater.run(dry_run=dry_run)
            return {
                'success': True,
                'message': 'AI脑库更新完成',
                'result': result
            }
        except ImportError as e:
            logger.error(f"导入AI脑库更新器失败: {e}")
            return {
                'success': False,
                'message': f"导入AI脑库更新器失败: {e}"
            }
        except Exception as e:
            logger.error(f"更新AI脑库失败: {e}")
            return {
                'success': False,
            }

    def handle_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理查询命令"""
        logger.info(f"处理查询命令,参数: {arguments}")

        keyword = arguments.get('keyword', '')
        limit = int(arguments.get('limit', 10))

        try:
            from ai_brain_search_enhancer import AIBrainSearchEnhancer

            if keyword:
                # 执行高级搜索
                knowledge_items = AIBrainSearchEnhancer.advanced_search(
                    keyword=keyword,
                    limit=limit
                )
                result = {
                    'keyword': keyword,
                    'count': len(knowledge_items),
                    'items': [item.to_dict() for item in knowledge_items]
                }
                return result
            else:
                # 如果没有关键字,获取热门知识
                result = {
                    'type': 'trending',
                    'limit': limit,
                    'count': len(knowledge_items),
                }
                return {
                    'success': True,
                    'message': '查询完成',
                    'result': result
                }
        except ImportError as e:
            logger.error(f"导入搜索增强器失败: {e}")
            return {
                'success': False,
                'message': f"导入搜索增强器失败: {e}"
            }
        except Exception as e:
            logger.error(f"查询AI脑库失败: {e}")
            return {
                'success': False,
                'message': f"查询AI脑库失败: {e}"
            }

    def handle_config(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理配置命令"""
        logger.info(f"处理配置命令,参数: {arguments}")

        key = arguments.get('key')

        if not key:
            return {
                'success': False,
                'message': '缺少配置键'
            }

        # 这里将实现AI脑库配置功能
        return {
            'success': True,
            'message': '配置完成',
            'result': {
                'key': key,
                'value': value
            }
        }

    def handle_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"处理状态命令,参数: {arguments}")

        try:
            from ai_brain_search_enhancer import AIBrainSearchEnhancer
            stats = AIBrainSearchEnhancer.get_statistics()

            return {
                'success': True,
                'result': {
                    'last_update': '2026-02-25 20:00:00',
                    'knowledge_count': stats.get('total_knowledge', 0),
                    'type_distribution': stats.get('type_distribution', {}),
                    'source_distribution': stats.get('source_distribution', {}),
                    'status': '正常'
                }
            }
        except ImportError as e:
            return {
                'success': False,
                'message': f"导入搜索增强器失败: {e}"
            }
            logger.error(f"获取AI脑库状态失败: {e}")
            return {
            }

    def execute(self, command: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if command in self.command_map:
            return self.command_map[command](arguments)
        else:
            logger.error(f"未知命令: {command}")
            return {
                'success': False,
                'message': f"未知命令: {command}"
            }

class ResultRenderer:
    """结果渲染器"""
    @staticmethod
    def render(result: Dict[str, Any]) -> None:
        """渲染命令执行结果"""
        if result['success']:
            print(f"✅ {result['message']}")
            if 'result' in result:
                ResultRenderer._render_result(result['result'])
        else:
            print(f"❌ {result['message']}")

    @staticmethod
    def _render_result(result: Any) -> None:
        """渲染具体结果"""
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, dict):
                    ResultRenderer._render_result(value)
                elif isinstance(value, list):
                    print(f"  {key} ({len(value)} 项):")
                    for item in value[:5]:
                        print(f"    - {item}")
                    if len(value) > 5:
                        print(f"    ... 还有 {len(value) - 5} 项")
                else:
                    print(f"  {key}: {value}")
        elif isinstance(result, list):
            for item in result[:5]:
                print(f"  - {item}")
            if len(result) > 5:
                print(f"  ... 还有 {len(result) - 5} 项")
        else:
            print(f"  {result}")


class AIBrainInterpreter:
    """AI脑库解释器"""

    def __init__(self):
        self.command_handler = CommandHandler()
        self.result_renderer = ResultRenderer()

    def interpret(self, input_str: str) -> None:
        """解释并执行命令"""
        try:
            lexer = Lexer(input_str)
            parser = Parser(lexer)
            command_node = parser.parse()

            # 执行命令
            result = self.command_handler.execute(command_node.command, command_node.arguments)

            # 渲染结果
            self.result_renderer.render(result)

        except SyntaxError as e:
            print(f"❌ 语法错误: {e}")
        except Exception as e:
            logger.error(f"解释器错误: {e}")

    def run_interactive(self) -> None:
        """运行交互式解释器"""
        print("输入命令或 'help' 获取帮助,'exit' 退出")
        print("支持的命令: update brain, query brain, config brain, status brain")

        while True:
            try:
                input_str = input("ai> ")
                if not input_str.strip():
                    continue
                if input_str.strip().lower() in ['exit', 'quit']:
                    break
                if input_str.strip().lower() == 'help':
                    self._show_help()
                    continue
                self.interpret(input_str)
            except KeyboardInterrupt:
                print("\n退出解释器...")
                break
            except Exception as e:
                logger.error(f"交互式解释器错误: {e}")
                print(f"❌ 交互式解释器错误: {e}")

    def _show_help(self) -> None:
        """显示帮助信息"""
        print("=== AI脑库解释器帮助 ===")
        print("支持的命令:")
        print("  update brain [--dry-run] - 更新AI脑库")
        print("    --dry-run - 模拟运行,不实际更新数据库")
        print("  query brain --keyword <keyword> [--limit <limit>] - 查询AI脑库内容")
        print("    --keyword <keyword> - 查询关键字")
        print("  config brain --key <key> [--value <value>] - 配置AI脑库参数")
        print("    --value <value> - 配置值")
        print("  status brain - 查看AI脑库状态")
        print("  exit/quit - 退出解释器")
        print("  help - 显示帮助信息")
        print()

    """主函数"""
    parser = argparse.ArgumentParser(description='AI脑库解释器')
    parser.add_argument('--command', '-c', type=str, default=None,
                      help='要执行的命令')
    parser.add_argument('--interactive', '-i', action='store_true', help='以交互式模式运行')

    args = parser.parse_args()

    interpreter = AIBrainInterpreter()

    if args.command:
        # 执行单个命令
        interpreter.interpret(args.command)
        # 运行交互式解释器
        interpreter.run_interactive()
    else:
        # 默认以交互式模式运行
        interpreter.run_interactive()
if __name__ == '__main__':
    main()
