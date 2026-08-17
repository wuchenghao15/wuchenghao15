# -*- coding: utf-8 -*-
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_middleware_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIMiddlewareEnhancer:
    def __init__(self):
        self.middleware_config = {
            'ai_brain_middleware': {
                'enabled': True,
                'priority': 40,
                'description': 'AI脑库请求处理中间件'
            }
        }

    def update_middleware_init(self):
        """更新中间件__init__.py文件,添加AI脑库中间件注册"""
        middleware_init_path = 'app/middlewares/__init__.py'

        if not os.path.exists(middleware_init_path):
            logger.error(f"文件不存在: {middleware_init_path}")
            return False

        with open(middleware_init_path, 'r') as f:
            content = f.read()

        if 'from app.middlewares.ai_brain_middleware import AIBrainMiddleware' in content:
            logger.info("AI脑库中间件注册已存在,跳过更新")
            return True

        updated_content = content

        import_insert_pos = content.find('class MiddlewareManager:')
        if import_insert_pos != -1:
            updated_content = updated_content[:import_insert_pos] + \
                'from app.middlewares.ai_brain_middleware import AIBrainMiddleware\n\n' + \
                updated_content[import_insert_pos:]
        else:
            updated_content = 'from app.middlewares.ai_brain_middleware import AIBrainMiddleware\n\n' + updated_content

        init_insert_pos = content.find('    # 2. 手动注册特定中间件(如果需要)')
        if init_insert_pos != -1:
            insert_text = '\n    # 注册AI脑库中间件\n' + \
                '    middleware_manager.register_middleware(\n' + \
                '        "ai_brain_request_logger",\n' + \
                '        AIBrainMiddleware.request_logger,\n' + \
                '        priority=45\n' + \
                '    )\n' + \
                '    middleware_manager.register_middleware(\n' + \
                '        "ai_brain_response_logger",\n' + \
                '        AIBrainMiddleware.response_logger,\n' + \
                '        priority=40\n' + \
                '    )\n' + \
                '    middleware_manager.register_middleware(\n' + \
                '        "ai_brain_error_handler",\n' + \
                '        AIBrainMiddleware.error_handler,\n' + \
                '        priority=35\n' + \
                '    )\n' + \
                '    middleware_manager.register_middleware(\n' + \
                '        "ai_brain_cors",\n' + \
                '        AIBrainMiddleware.cors_middleware,\n' + \
                '        priority=50\n' + \
                '    )\n'
            updated_content = updated_content[:init_insert_pos + len('    # 2. 手动注册特定中间件(如果需要)')] + \
                insert_text + \
                updated_content[init_insert_pos + len('    # 2. 手动注册特定中间件(如果需要)'):]

        with open(middleware_init_path, 'w') as f:
            f.write(updated_content)

        logger.info(f"更新中间件__init__.py文件,添加AI脑库中间件注册")
        return True

    def update_app_init(self):
        """更新app/__init__.py文件,初始化并应用中间件"""
        app_init_path = 'app/__init__.py'

        if not os.path.exists(app_init_path):
            logger.error(f"文件不存在: {app_init_path}")
            return False

        with open(app_init_path, 'r') as f:
            content = f.read()

        if 'middleware_manager' in content:
            logger.info("中间件初始化已存在,跳过更新")
            return True

        updated_content = content
        lines = content.split('\n')

        import_line = 'from app.middlewares import middleware_manager, init_middlewares'
        if import_line not in content:
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import') or line.startswith('from'):
                    import_index = i
                else:
                    break
            lines.insert(import_index + 1, import_line)
            updated_content = '\n'.join(lines)

        create_app_end = updated_content.rfind('return app')
        if create_app_end != -1:
            updated_content = updated_content[:create_app_end] + \
                '\n    # 初始化并应用中间件\n' + \
                '    init_middlewares()\n' + \
                '    middleware_manager.apply_middlewares(app)\n' + \
                updated_content[create_app_end:]

        with open(app_init_path, 'w') as f:
            f.write(updated_content)

        logger.info(f"更新app/__init__.py文件,添加中间件初始化")
        return True

    def enhance_ai_middleware(self):
        """完善AI中间件"""
        self.update_middleware_init()
        self.update_app_init()
        logger.info("AI中间件自动完善完成!")

    def run(self):
        """执行AI中间件完善流程"""
        self.enhance_ai_middleware()


if __name__ == "__main__":
    enhancer = AIMiddlewareEnhancer()
    enhancer.run()
