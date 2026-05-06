# -*- coding: utf-8 -*-
import logging
import os

# 设置日志记录
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

    def update_middleware_init(self):
        """更新中间件__init__.py文件，添加AI脑库中间件注册"""
        middleware_init_path = 'app/middlewares/__init__.py'

        if not os.path.exists(middleware_init_path):
            logger.error(f"文件不存在: {middleware_init_path}")
            return False

        # 读取当前内容
        with open(middleware_init_path, 'r') as f:
            content = f.read()

        # 检查是否已添加AI脑库中间件注册
        if 'from app.middlewares.ai_brain_middleware import AIBrainMiddleware' in content:
            logger.info("AI脑库中间件注册已存在，跳过更新")
            return True

        # 更新内容，添加AI脑库中间件注册
        updated_content = content

        # 在文件开头添加导入
        import_insert_pos = content.find('class MiddlewareManager:')
        if import_insert_pos != -1:
            updated_content = updated_content[:import_insert_pos] + \
                'from app.middlewares.ai_brain_middleware import AIBrainMiddleware\n\n' + \
                updated_content[import_insert_pos:]
        else:
            # 如果找不到MiddlewareManager类，在文件开头添加导入
            updated_content = 'from app.middlewares.ai_brain_middleware import AIBrainMiddleware\n\n' + updated_content

        # 在init_middlewares函数中添加手动注册
        init_insert_pos = content.find('    # 2. 手动注册特定中间件（如果需要）')
        if init_insert_pos != -1:
            # 找到注释位置，在后面添加注册代码
            updated_content = updated_content[:init_insert_pos + len('    # 2. 手动注册特定中间件（如果需要）')] + \
                '\n    # 注册AI脑库中间件\n' + \
                '    middleware_manager.register_middleware(\n' + \
                '        "ai_brain_request_logger",\n' + \
                '        AIBrainMiddleware.request_logger,\n' + \
                '        priority=45\n' + \
                '    )\n' + \
                '    middleware_manager.register_middleware(\n' + \
                '        AIBrainMiddleware.response_logger,\n' + \
                '        priority=40\n' + \
                '    )\n' + \
                '    middleware_manager.register_middleware(\n' + \
                '        priority=35\n' + \
                '    )\n' + \
                '    middleware_manager.register_middleware(\n' + \
                '        AIBrainMiddleware.cors_middleware,\n' + \
                '    )\n' + \
                updated_content[init_insert_pos + len('    # 2. 手动注册特定中间件（如果需要）'):]

        # 写入更新后的内容
            f.write(updated_content)

        logger.info(f"更新中间件__init__.py文件，添加AI脑库中间件注册")
        return True
    def update_app_init(self):
        """更新app/__init__.py文件，初始化并应用中间件"""
        app_init_path = 'app/__init__.py'

        if not os.path.exists(app_init_path):
            logger.error(f"文件不存在: {app_init_path}")
            return False
        # 读取当前内容
        with open(app_init_path, 'r') as f:

        # 检查是否已初始化中间件
            logger.info("中间件初始化已存在，跳过更新")
            return True

        # 更新内容，添加中间件初始化和应用
        updated_content = content
        # 添加导入语句
        import_line = 'from app.middlewares import middleware_manager, init_middlewares'
        if import_line not in content:
            # 找到import语句位置，插入中间件导入
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import') or line.startswith('from'):
                    import_index = i
                else:
                    break

            lines.insert(import_index + 1, import_line)
            updated_content = '\n'.join(lines)

        # 在create_app函数中初始化中间件
        if create_app_end != -1:
            # 在return app之前添加中间件初始化和应用
            updated_content = updated_content[:create_app_end] + \
                '\n    # 初始化并应用中间件\n' + \
                '    init_middlewares()\n' + \
                '    middleware_manager.apply_middlewares(app)\n' + \
                updated_content[create_app_end:]

        # 写入更新后的内容
        with open(app_init_path, 'w') as f:
            f.write(updated_content)

        logger.info(f"更新app/__init__.py文件，添加中间件初始化")
        return True

    def enhance_ai_middleware(self):
        """完善AI中间件"""

        # 1. 更新中间件__init__.py，添加AI脑库中间件注册
        self.update_middleware_init()

        # 2. 更新app/__init__.py，初始化并应用中间件

        logger.info("AI中间件自动完善完成！")
    def run(self):
        """执行AI中间件完善流程"""
        self.enhance_ai_middleware()

if __name__ == "__main__":
    enhancer = AIMiddlewareEnhancer()
    enhancer.run()
