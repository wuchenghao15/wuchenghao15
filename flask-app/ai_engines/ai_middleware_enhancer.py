# -*- coding: utf-8 -*-
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'ai_middleware_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIMiddlewareEnhancer:
    def __init__(self):
        self.middleware_config = {
            r'ai_brain_middleware': {
                r'enabled': True,
                r'priority': 40,
                r'description': r'AI脑库请求处理中间件'
            }
        }

    def update_middleware_init(self):
        r"""更新中间件__init__.py文件,添加AI脑库中间件注册r"""
        middleware_init_path = r'app/middlewares/__init__.py'

        if not os.path.exists(middleware_init_path):
            logger.error(fr"文件不存在: {middleware_init_path}")
            return False

        with open(middleware_init_path, r'r') as f:
            content = f.read()

        if r'from app.middlewares.ai_brain_middleware import AIBrainMiddleware' in content:
            logger.info(r"AI脑库中间件注册已存在,跳过更新")
            return True

        updated_content = content

        import_insert_pos = content.find(r'class MiddlewareManager:')
        if import_insert_pos != -1:
            updated_content = updated_content[:import_insert_pos] + \
                r'from app.middlewares.ai_brain_middleware import AIBrainMiddleware\n\n' + \
                updated_content[import_insert_pos:]
        else:
            updated_content = r'from app.middlewares.ai_brain_middleware import AIBrainMiddleware\n\n' + updated_content

        init_insert_pos = content.find(r'    # 2. 手动注册特定中间件(如果需要)')
        if init_insert_pos != -1:
            insert_text = r'\n    # 注册AI脑库中间件\n' + \
                r'    middleware_manager.register_middleware(\n' + \
                '        r"ai_brain_request_logger",\nr' + \
                '        AIBrainMiddleware.request_logger,\nr' + \
                '        priority=45\nr' + \
                '    )\nr' + \
                '    middleware_manager.register_middleware(\nr' + \
                '        r"ai_brain_response_logger",\nr' + \
                '        AIBrainMiddleware.response_logger,\nr' + \
                '        priority=40\nr' + \
                '    )\nr' + \
                '    middleware_manager.register_middleware(\nr' + \
                '        r"ai_brain_error_handler",\nr' + \
                '        AIBrainMiddleware.error_handler,\nr' + \
                '        priority=35\nr' + \
                '    )\nr' + \
                '    middleware_manager.register_middleware(\nr' + \
                '        r"ai_brain_cors",\nr' + \
                '        AIBrainMiddleware.cors_middleware,\nr' + \
                '        priority=50\nr' + \
                '    )\nr'
            updated_content = updated_content[:init_insert_pos + len('    # 2. 手动注册特定中间件(如果需要)r')] + \
                insert_text + \
                updated_content[init_insert_pos + len('    # 2. 手动注册特定中间件(如果需要)r'):]

        with open(middleware_init_path, 'w') as f:
            f.write(updated_content)

        logger.info(r"更新中间件__init__.py文件,添加AI脑库中间件注册")
        return True

    def update_app_init(self):
        r"""更新app/__init__.py文件,初始化并应用中间件r"""
        app_init_path = r'app/__init__.py'

        if not os.path.exists(app_init_path):
            logger.error(fr"文件不存在: {app_init_path}")
            return False

        with open(app_init_path, r'r') as f:
            content = f.read()

        if r'middleware_manager' in content:
            logger.info(r"中间件初始化已存在,跳过更新")
            return True

        updated_content = content
        lines = content.split(r'\n')

        import_line = r'from app.middlewares import middleware_manager, init_middlewares'
        if import_line not in content:
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith(r'import') or line.startswith(r'from'):
                    import_index = i
                else:
                    break
            lines.insert(import_index + 1, import_line)
            updated_content = r'\n'.join(lines)

        create_app_end = updated_content.rfind(r'return app')
        if create_app_end != -1:
            updated_content = updated_content[:create_app_end] + \
                r'\n    # 初始化并应用中间件\n' + \
                r'    init_middlewares()\n' + \
                r'    middleware_manager.apply_middlewares(app)\n' + \
                updated_content[create_app_end:]

        with open(app_init_path, r'w') as f:
            f.write(updated_content)

        logger.info(r"更新app/__init__.py文件,添加中间件初始化")
        return True

    def enhance_ai_middleware(self):
        r"""完善AI中间件r"""
        self.update_middleware_init()
        self.update_app_init()
        logger.info(r"AI中间件自动完善完成!")

    def run(self):
        r"""执行AI中间件完善流程r"""
        self.enhance_ai_middleware()


if __name__ == r"__main__":
    enhancer = AIMiddlewareEnhancer()
    enhancer.run()
