import os
import shutil
from pathlib import Path
from datetime import datetime

# 定义本地生成文件统一归档的指定根目录
UNIFIED_ARCHIVE_DIR = Path(__file__).parent.parent / "local_generated_packs_archive"
# 程序启动自动初始化归档目录，不存在则递归创建
UNIFIED_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

class AIEngine:
    def __init__(self):
        self.archive_root = UNIFIED_ARCHIVE_DIR
        # 初始化阶段自动执行全量智能包文件整合归档
        self._auto_smart_integrate_package_files()

    def _auto_smart_integrate_package_files(self):
        """自动扫描项目全目录散落的包文件、生成的吧快类文件统一归集到指定归档目录"""
        # 配置需要自动识别归档的包/生成文件后缀规则
        target_archive_suffix = {".wav", ".txt", ".json", ".xml"}  # 修改为只归档 .wav, .txt, .json, .xml 文件
        # 遍历项目根目录全文件
        for scan_root, _, file_names in os.walk(Path(__file__).parent.parent):
            # 跳过归档目录自身避免重复循环处理
            if str(self.archive_root.resolve()) in str(Path(scan_root).resolve()):
                continue
            for fname in file_names:
                f_path = Path(scan_root) / fname
                if f_path.suffix.lower() in target_archive_suffix:
                    self._move_to_unified_archive(f_path)

    def _move_to_unified_archive(self, source_file: Path):
        """将目标文件移动到统一归档目录，按日期分子目录存储，重名自动追加时间戳避免覆盖"""
        if not source_file.exists() or not source_file.is_file():
            return
        date_sub_dir = self.archive_root / datetime.now().strftime("%Y%m%d")
        date_sub_dir.mkdir(parents=True, exist_ok=True)
        target_save_path = date_sub_dir / source_file.name
        # 重名冲突处理逻辑
        if target_save_path.exists():
            stem, suffix = target_save_path.stem, target_save_path.suffix
            time_suffix = datetime.now().strftime("%H%M%S%f")
            target_save_path = date_sub_dir / f"{stem}_{time_suffix}{suffix}"
        shutil.move(str(source_file.resolve()), str(target_save_path.resolve()))

    def local_engine_generate_file(self, output_path: str, *args, **kwargs):
        """引擎本地生成文件原有逻辑执行完成后自动归档"""
        # 保留原有引擎生成文件核心逻辑
        super().local_engine_generate_file(output_path, *args, **kwargs)
        generated_f = Path(output_path)
        if generated_f.exists() and generated_f.is_file():
            self._move_to_unified_archive(generated_f)
