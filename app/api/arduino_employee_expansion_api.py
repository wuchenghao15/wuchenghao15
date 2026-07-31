"""
Arduino AI 员工扩容系统 v3.0
目标：将Arduino相关AI员工从184名扩展到覆盖46个功能类别的完整团队
同时确保系统总员工数量维持在10810名以上
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger('ArduinoEmployeeExpansion')

DEFAULT_MODULE_PATH = "ai_engines.arduino_ai_employees"

ARDUINO_CATEGORIES = {
    "compiler_engineer": {"name": "编译工程师", "count": 24, "base_level": 8, "class": "ArduinoCompilerEngineerEmployee", "team": "编译与构建团队", "capabilities": ["code_compilation", "syntax_check", "error_analysis"]},
    "linker_specialist": {"name": "链接专家", "count": 20, "base_level": 8, "class": "ArduinoLinkerSpecialistEmployee", "team": "编译与构建团队", "capabilities": ["linking", "symbol_resolution", "dependency_analysis"]},
    "objdump_analyst": {"name": "反汇编分析师", "count": 16, "base_level": 9, "class": "ArduinoObjdumpAnalystEmployee", "team": "编译与构建团队", "capabilities": ["disassembly", "machine_code_analysis", "binary_analysis"]},
    "memory_optimizer": {"name": "内存优化专家", "count": 24, "base_level": 10, "class": "ArduinoMemoryOptimizerEmployee", "team": "编译与构建团队", "capabilities": ["memory_optimization", "ram_usage", "flash_optimization"]},
    "build_system_expert": {"name": "构建系统专家", "count": 16, "base_level": 8, "class": "ArduinoBuildSystemExpertEmployee", "team": "编译与构建团队", "capabilities": ["build_system", "makefile", "cmake"]},
    "library_linker": {"name": "库链接专家", "count": 16, "base_level": 7, "class": "ArduinoLibraryLinkerEmployee", "team": "编译与构建团队", "capabilities": ["library_linking", "static_linking", "dynamic_linking"]},
    "firmware_packager": {"name": "固件打包专家", "count": 20, "base_level": 7, "class": "ArduinoFirmwarePackagerEmployee", "team": "编译与构建团队", "capabilities": ["firmware_packaging", "hex_generation", "bin_generation"]},
    "bootloader_specialist": {"name": "Bootloader专家", "count": 12, "base_level": 9, "class": "ArduinoBootloaderSpecialistEmployee", "team": "编译与构建团队", "capabilities": ["bootloader", "flashing", "firmware_upgrade"]},
    "cross_compile_expert": {"name": "交叉编译专家", "count": 12, "base_level": 9, "class": "ArduinoCrossCompileExpertEmployee", "team": "编译与构建团队", "capabilities": ["cross_compilation", "toolchain", "multi_arch"]},
    "size_optimizer": {"name": "体积优化专家", "count": 20, "base_level": 10, "class": "ArduinoSizeOptimizerEmployee", "team": "编译与构建团队", "capabilities": ["size_optimization", "code_stripping", "dead_code_elimination"]},
    "preprocessor_expert": {"name": "预处理器专家", "count": 16, "base_level": 8, "class": "ArduinoPreprocessorExpertEmployee", "team": "编译与构建团队", "capabilities": ["preprocessing", "macros", "conditional_compilation"]},
    "code_coverage": {"name": "代码覆盖率员工", "count": 16, "base_level": 8, "class": "ArduinoCodeCoverageEmployee", "team": "编译与构建团队", "capabilities": ["code_coverage", "test_coverage", "coverage_report"]},
    "hal_developer": {"name": "HAL开发", "count": 28, "base_level": 8, "class": "ArduinoHALDeveloperEmployee", "team": "硬件与驱动团队", "capabilities": ["hal", "hardware_abstraction", "low_level"]},
    "peripheral_driver": {"name": "外设驱动开发", "count": 28, "base_level": 9, "class": "ArduinoPeripheralDriverEmployee", "team": "硬件与驱动团队", "capabilities": ["peripheral_drivers", "gpio", "uart", "spi", "i2c"]},
    "sensor_calibration": {"name": "传感器校准", "count": 24, "base_level": 8, "class": "ArduinoSensorCalibrationEmployee", "team": "硬件与驱动团队", "capabilities": ["sensor_calibration", "adc_calibration", "offset_adjustment"]},
    "motor_control": {"name": "电机控制", "count": 24, "base_level": 9, "class": "ArduinoMotorControlEmployee", "team": "硬件与驱动团队", "capabilities": ["motor_control", "pwm", "servo", "stepper", "dc_motor"]},
    "display_driver": {"name": "显示驱动", "count": 28, "base_level": 8, "class": "ArduinoDisplayDriverEmployee", "team": "硬件与驱动团队", "capabilities": ["display_drivers", "lcd", "oled", "tft", "epd"]},
    "power_management": {"name": "电源管理", "count": 20, "base_level": 9, "class": "ArduinoPowerManagementEmployee", "team": "硬件与驱动团队", "capabilities": ["power_management", "low_power", "sleep_modes", "battery"]},
    "clock_timer": {"name": "时钟定时器", "count": 20, "base_level": 8, "class": "ArduinoClockTimerEmployee", "team": "硬件与驱动团队", "capabilities": ["timer", "rtc", "clock", "pwm_timer"]},
    "wireless_stack": {"name": "无线协议栈", "count": 24, "base_level": 9, "class": "ArduinoWirelessStackEmployee", "team": "硬件与驱动团队", "capabilities": ["wireless", "wifi", "bluetooth", "ble", "lora"]},
    "storage_driver": {"name": "存储驱动", "count": 24, "base_level": 8, "class": "ArduinoStorageDriverEmployee", "team": "硬件与驱动团队", "capabilities": ["storage", "sd_card", "eeprom", "spiffs", "flash"]},
    "code_generator": {"name": "代码生成AI", "count": 24, "base_level": 7, "class": "ArduinoCodeGeneratorEmployee", "team": "AI辅助开发团队", "capabilities": ["code_generation", "template_generation", "boilerplate"]},
    "code_debugger": {"name": "代码调试AI", "count": 20, "base_level": 8, "class": "ArduinoCodeDebuggerEmployee", "team": "AI辅助开发团队", "capabilities": ["debugging", "error_detection", "bug_fixing"]},
    "code_optimizer": {"name": "代码优化AI", "count": 20, "base_level": 7, "class": "ArduinoCodeOptimizerEmployee", "team": "AI辅助开发团队", "capabilities": ["code_optimization", "performance", "refactoring"]},
    "component_advisor": {"name": "组件推荐AI", "count": 24, "base_level": 6, "class": "ArduinoComponentAdvisorEmployee", "team": "AI辅助开发团队", "capabilities": ["component_recommendation", "bom_generation", "part_selection"]},
    "code_completer": {"name": "代码补全", "count": 24, "base_level": 8, "class": "ArduinoCodeCompleterEmployee", "team": "AI辅助开发团队", "capabilities": ["code_completion", "autocomplete", "intellisense"]},
    "intent_parser": {"name": "意图解析", "count": 24, "base_level": 9, "class": "ArduinoIntentParserEmployee", "team": "AI辅助开发团队", "capabilities": ["intent_recognition", "nlp", "natural_language"]},
    "doc_generator": {"name": "文档生成", "count": 24, "base_level": 7, "class": "ArduinoDocGeneratorEmployee", "team": "AI辅助开发团队", "capabilities": ["documentation", "doc_generation", "comment_generation"]},
    "refactoring_expert": {"name": "重构专家", "count": 20, "base_level": 9, "class": "ArduinoRefactoringExpertEmployee", "team": "AI辅助开发团队", "capabilities": ["refactoring", "code_cleanup", "architecture"]},
    "smart_advisor": {"name": "智能顾问AI", "count": 20, "base_level": 9, "class": "ArduinoSmartAdvisorEmployee", "team": "AI辅助开发团队", "capabilities": ["smart_advice", "project_planning", "architecture_design"]},
    "security_auditor": {"name": "安全审计师", "count": 24, "base_level": 9, "class": "ArduinoSecurityAuditorEmployee", "team": "安全与防护团队", "capabilities": ["security_audit", "vulnerability_scan", "penetration_testing"]},
    "crypto_specialist": {"name": "加密专家", "count": 20, "base_level": 10, "class": "ArduinoCryptoSpecialistEmployee", "team": "安全与防护团队", "capabilities": ["cryptography", "aes", "rsa", "sha", "encryption"]},
    "secure_boot": {"name": "安全启动专家", "count": 14, "base_level": 9, "class": "ArduinoSecureBootEmployee", "team": "安全与防护团队", "capabilities": ["secure_boot", "signature_verification", "firmware_signing"]},
    "firewall_engineer": {"name": "防火墙工程师", "count": 16, "base_level": 8, "class": "ArduinoFirewallEngineerEmployee", "team": "安全与防护团队", "capabilities": ["firewall", "network_security", "packet_filtering"]},
    "hardware_security": {"name": "硬件安全专家", "count": 16, "base_level": 9, "class": "ArduinoHardwareSecurityEmployee", "team": "安全与防护团队", "capabilities": ["hardware_security", "tamper_detection", "side_channel"]},
    "library_maintainer": {"name": "库维护工程师", "count": 20, "base_level": 8, "class": "ArduinoLibraryMaintainerEmployee", "team": "库与生态团队", "capabilities": ["library_maintenance", "dependency_management", "versioning"]},
    "driver_porting": {"name": "驱动移植专家", "count": 24, "base_level": 9, "class": "ArduinoDriverPortingEmployee", "team": "库与生态团队", "capabilities": ["driver_porting", "cross_platform", "compatibility"]},
    "ecosystem_integrator": {"name": "生态集成工程师", "count": 20, "base_level": 8, "class": "ArduinoEcosystemIntegratorEmployee", "team": "库与生态团队", "capabilities": ["ecosystem_integration", "third_party", "plugin_system"]},
    "package_manager": {"name": "包管理器专家", "count": 18, "base_level": 8, "class": "ArduinoPackageManagerEmployee", "team": "库与生态团队", "capabilities": ["package_management", "library_manager", "dependency_resolution"]},
    "uart_isp_protocol": {"name": "UART/ISP协议专家", "count": 20, "base_level": 8, "class": "ArduinoUartIspProtocolEmployee", "team": "通信与协议团队", "capabilities": ["uart", "isp", "serial_protocol", "rs232"]},
    "i2c_spi_expert": {"name": "I2C/SPI协议专家", "count": 24, "base_level": 8, "class": "ArduinoI2cSpiExpertEmployee", "team": "通信与协议团队", "capabilities": ["i2c", "spi", "twibus", "serial_bus"]},
    "can_lin_protocol": {"name": "CAN/LIN总线专家", "count": 20, "base_level": 9, "class": "ArduinoCanLinProtocolEmployee", "team": "通信与协议团队", "capabilities": ["can_bus", "lin_bus", "automotive", "industrial"]},
    "cloud_platform": {"name": "云平台工程师", "count": 28, "base_level": 9, "class": "ArduinoCloudPlatformEmployee", "team": "IoT与云平台团队", "capabilities": ["cloud_integration", "mqtt", "aws_iot", "azure_iot"]},
    "edge_computing": {"name": "边缘计算工程师", "count": 28, "base_level": 9, "class": "ArduinoEdgeComputingEmployee", "team": "IoT与云平台团队", "capabilities": ["edge_computing", "tinyml", "on_device_ai", "ml_inference"]},
    "auto_tester": {"name": "自动化测试工程师", "count": 28, "base_level": 8, "class": "ArduinoAutoTesterEmployee", "team": "测试与质量团队", "capabilities": ["automated_testing", "unit_test", "integration_test", "ci_cd"]},
    "quality_assurance": {"name": "质量保证工程师", "count": 20, "base_level": 8, "class": "ArduinoQualityAssuranceEmployee", "team": "测试与质量团队", "capabilities": ["quality_assurance", "qa", "code_review", "standards"]},
    "curriculum_designer": {"name": "课程设计师", "count": 24, "base_level": 7, "class": "ArduinoCurriculumDesignerEmployee", "team": "教育与培训团队", "capabilities": ["curriculum_design", "learning_path", "tutorial_creation"]},
    "code_evolver": {"name": "代码进化AI", "count": 0, "base_level": 10, "class": "ArduinoCodeEvolverEmployee", "team": "AI辅助开发团队", "capabilities": ["code_evolution", "pattern_learning", "self_improvement"]},
    "iot_automation": {"name": "IoT自动化专家", "count": 0, "base_level": 9, "class": "ArduinoIoTAutomationEmployee", "team": "IoT与云平台团队", "capabilities": ["iot_automation", "device_discovery", "ota_upgrade", "remote_deployment"]},
}

TOTAL_EMPLOYEE_TARGET = 10810
ARDUINO_BASE_LOAD_ORDER = 500


def _generate_employee_id(prefix: str, idx: int) -> str:
    return f"arduino_{prefix}_{idx:04d}"


def _generate_name(category_name: str, idx: int) -> str:
    return f"Arduino{category_name}{idx:03d}号"


class ArduinoEmployeeExpander:
    """Arduino AI员工扩容管理器"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._get_registry_db_path()
        self._created_employees: List[Tuple[str, str, int, str]] = []
        self._ensure_logging()

    def _ensure_logging(self):
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    def _get_registry_db_path(self) -> str:
        return os.path.join(PROJECT_ROOT, 'app.db')

    def _get_current_employee_count(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ai_agent_registry")
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.OperationalError:
            return 0

    def _get_next_load_order(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(MAX(load_order), 0) FROM ai_agent_registry")
                result = cursor.fetchone()
                max_order = result[0] if result else 0
                return max(ARDUINO_BASE_LOAD_ORDER, max_order + 1)
        except sqlite3.OperationalError:
            return ARDUINO_BASE_LOAD_ORDER

    def expand_all_employees(self, register_in_db: bool = True) -> List[Tuple[str, str, int, str]]:
        """
        创建所有46个功能类别的Arduino AI员工
        返回列表：[(employee_id, name, level, category_type), ...]
        """
        logger.info("开始创建Arduino AI员工扩容...")
        self._created_employees = []
        category_index: Dict[str, int] = {}

        for cat_key, cat_info in ARDUINO_CATEGORIES.items():
            count = cat_info["count"]
            if count <= 0:
                continue
            base_level = cat_info["base_level"]
            category_name = cat_info["name"]
            class_name = cat_info["class"]

            category_index[cat_key] = 0

            for idx in range(1, count + 1):
                level = base_level
                if idx > count * 0.9:
                    level = min(base_level + 2, 10)
                elif idx > count * 0.7:
                    level = min(base_level + 1, 10)

                employee_id = _generate_employee_id(cat_key, idx)
                employee_name = _generate_name(category_name, idx)
                category_type = cat_key

                self._created_employees.append((employee_id, employee_name, level, category_type))
                category_index[cat_key] = idx

        logger.info(f"Arduino AI员工创建完成，共 {len(self._created_employees)} 名")

        if register_in_db:
            self.register_in_ai_registry(self._created_employees)

        return self._created_employees

    def register_in_ai_registry(self, employees: List[Tuple[str, str, int, str]]) -> Dict[str, Any]:
        """
        批量注册AI员工到AIAgentLoader的数据库
        表：ai_agent_registry
        """
        if not employees:
            return {"success": False, "error": "员工列表为空"}

        logger.info(f"开始向AI注册表批量注册 {len(employees)} 名Arduino员工...")

        inserted_count = 0
        skipped_count = 0
        error_count = 0
        errors: List[str] = []

        current_load_order = self._get_next_load_order()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS ai_agent_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT UNIQUE,
                        agent_name TEXT NOT NULL,
                        module_path TEXT,
                        class_name TEXT,
                        agent_type TEXT DEFAULT 'employee',
                        is_auto_load INTEGER DEFAULT 1,
                        load_order INTEGER DEFAULT 100,
                        status TEXT DEFAULT 'registered',
                        capabilities TEXT,
                        config TEXT,
                        created_at TEXT,
                        last_loaded_at TEXT,
                        load_count INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()

                for employee_id, employee_name, level, category_type in employees:
                    try:
                        cat_info = ARDUINO_CATEGORIES.get(category_type, {})
                        class_name = cat_info.get("class", "AIEmployee")
                        capabilities = cat_info.get("capabilities", [])
                        team = cat_info.get("team", "Arduino团队")

                        config = {
                            "category": category_type,
                            "team": team,
                            "level": level,
                            "arduino_specialist": True,
                            "expansion_version": "3.0"
                        }

                        cursor = conn.execute('''
                            INSERT OR IGNORE INTO ai_agent_registry
                            (agent_id, agent_name, module_path, class_name, agent_type,
                             is_auto_load, load_order, status, capabilities, config, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'registered', ?, ?, ?)
                        ''', (
                            employee_id,
                            employee_name,
                            DEFAULT_MODULE_PATH,
                            class_name,
                            f"arduino_{category_type}",
                            1,
                            current_load_order,
                            json.dumps(capabilities, ensure_ascii=False),
                            json.dumps(config, ensure_ascii=False),
                            datetime.now().isoformat()
                        ))

                        if cursor.rowcount > 0:
                            inserted_count += 1
                        else:
                            skipped_count += 1

                        current_load_order += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"{employee_id}: {str(e)}")
                        logger.error(f"注册员工 {employee_id} 失败: {e}")

                conn.commit()

        except Exception as e:
            logger.error(f"批量注册数据库失败: {e}")
            return {"success": False, "error": str(e)}

        result = {
            "success": True,
            "total_processed": len(employees),
            "inserted": inserted_count,
            "skipped": skipped_count,
            "errors": error_count,
            "error_details": errors[:10]
        }

        logger.info(f"批量注册完成: 新增{inserted_count}, 跳过{skipped_count}, 错误{error_count}")
        return result

    def get_expansion_summary(self) -> Dict[str, Any]:
        """
        返回扩容摘要：总员工数、按类别细分、等级分布
        """
        employees = self._created_employees if self._created_employees else self._fetch_registered_arduino_employees()

        total = len(employees)

        category_breakdown: Dict[str, Dict[str, Any]] = {}
        for cat_key, cat_info in ARDUINO_CATEGORIES.items():
            category_breakdown[cat_key] = {
                "name": cat_info["name"],
                "team": cat_info["team"],
                "target_count": cat_info["count"],
                "actual_count": 0,
                "base_level": cat_info["base_level"]
            }

        level_distribution: Dict[int, int] = {l: 0 for l in range(1, 11)}
        team_distribution: Dict[str, int] = {}

        for emp_id, emp_name, level, cat_type in employees:
            if cat_type in category_breakdown:
                category_breakdown[cat_type]["actual_count"] += 1

            if level in level_distribution:
                level_distribution[level] += 1

            cat_info = ARDUINO_CATEGORIES.get(cat_type, {})
            team = cat_info.get("team", "未分类")
            team_distribution[team] = team_distribution.get(team, 0) + 1

        arduino_total = sum(v["actual_count"] for v in category_breakdown.values())
        current_registry_total = self._get_current_employee_count()

        return {
            "expansion_version": "3.0",
            "timestamp": datetime.now().isoformat(),
            "total_arduino_employees_created": total,
            "total_arduino_by_category": arduino_total,
            "current_registry_total": current_registry_total,
            "target_total": TOTAL_EMPLOYEE_TARGET,
            "gap_to_target": max(0, TOTAL_EMPLOYEE_TARGET - current_registry_total),
            "category_count": len([c for c in category_breakdown.values() if c["target_count"] > 0]),
            "category_breakdown": category_breakdown,
            "level_distribution": {f"L{l}": c for l, c in level_distribution.items() if c > 0},
            "team_distribution": team_distribution,
            "arduino_percentage_of_total": round((arduino_total / current_registry_total * 100), 2) if current_registry_total > 0 else 0
        }

    def _fetch_registered_arduino_employees(self) -> List[Tuple[str, str, int, str]]:
        """从数据库获取已注册的Arduino员工"""
        result: List[Tuple[str, str, int, str]] = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT agent_id, agent_name, config, agent_type FROM ai_agent_registry WHERE agent_type LIKE 'arduino_%'")
                for row in cursor.fetchall():
                    try:
                        config = json.loads(row["config"] or "{}")
                        level = config.get("level", 5)
                        cat_type = config.get("category", row["agent_type"].replace("arduino_", ""))
                    except (json.JSONDecodeError, TypeError):
                        level = 5
                        cat_type = row["agent_type"].replace("arduino_", "")
                    result.append((row["agent_id"], row["agent_name"], level, cat_type))
        except Exception as e:
            logger.warning(f"获取已注册Arduino员工失败: {e}")
        return result

    def ensure_10810_total(self) -> Dict[str, Any]:
        """
        确保系统总员工数 >= 10810
        若不足，则创建补充的通用Arduino专家员工
        """
        current_count = self._get_current_employee_count()
        gap = TOTAL_EMPLOYEE_TARGET - current_count

        if gap <= 0:
            logger.info(f"系统总员工数已达标: {current_count} >= {TOTAL_EMPLOYEE_TARGET}")
            return {
                "success": True,
                "current_count": current_count,
                "target": TOTAL_EMPLOYEE_TARGET,
                "filler_added": 0,
                "gap": 0,
                "message": "员工总数已达标"
            }

        logger.info(f"员工数缺口: {gap} 名，开始创建补充员工...")

        filler_employees: List[Tuple[str, str, int, str]] = []
        filler_categories = [
            ("generic_specialist", "通用Arduino专家", 7, "ArduinoGenericSpecialistEmployee"),
            ("junior_developer", "初级Arduino开发员", 5, "ArduinoJuniorDeveloperEmployee"),
            ("senior_consultant", "高级Arduino顾问", 9, "ArduinoSeniorConsultantEmployee"),
            ("tech_lead", "技术主管", 10, "ArduinoTechLeadEmployee"),
            ("solution_architect", "解决方案架构师", 10, "ArduinoSolutionArchitectEmployee"),
        ]

        current_load_order = self._get_next_load_order() + 10000
        inserted = 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS ai_agent_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT UNIQUE,
                        agent_name TEXT NOT NULL,
                        module_path TEXT,
                        class_name TEXT,
                        agent_type TEXT DEFAULT 'employee',
                        is_auto_load INTEGER DEFAULT 1,
                        load_order INTEGER DEFAULT 100,
                        status TEXT DEFAULT 'registered',
                        capabilities TEXT,
                        config TEXT,
                        created_at TEXT,
                        last_loaded_at TEXT,
                        load_count INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()

                for i in range(gap):
                    cat_idx = i % len(filler_categories)
                    cat_type, cat_name, base_level, class_name = filler_categories[cat_idx]
                    emp_idx = (i // len(filler_categories)) + 1

                    emp_id = f"arduino_{cat_type}_f{emp_idx:05d}"
                    emp_name = f"Arduino{cat_name}补充{emp_idx:04d}号"

                    level = base_level
                    if i > gap * 0.9:
                        level = min(base_level + 1, 10)

                    filler_employees.append((emp_id, emp_name, level, cat_type))

                    config = {
                        "category": cat_type,
                        "team": "通用扩容团队",
                        "level": level,
                        "arduino_specialist": True,
                        "expansion_version": "3.0",
                        "is_filler": True
                    }

                    try:
                        cursor = conn.execute('''
                            INSERT OR IGNORE INTO ai_agent_registry
                            (agent_id, agent_name, module_path, class_name, agent_type,
                             is_auto_load, load_order, status, capabilities, config, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'registered', ?, ?, ?)
                        ''', (
                            emp_id,
                            emp_name,
                            DEFAULT_MODULE_PATH,
                            class_name,
                            f"arduino_{cat_type}",
                            1,
                            current_load_order,
                            json.dumps(["general_purpose", "arduino_development"], ensure_ascii=False),
                            json.dumps(config, ensure_ascii=False),
                            datetime.now().isoformat()
                        ))
                        if cursor.rowcount > 0:
                            inserted += 1
                        current_load_order += 1

                    except Exception as e:
                        logger.error(f"创建补充员工 {emp_id} 失败: {e}")

                conn.commit()

        except Exception as e:
            logger.error(f"补充员工创建失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "current_count": current_count,
                "target": TOTAL_EMPLOYEE_TARGET,
                "gap": gap
            }

        new_total = self._get_current_employee_count()
        logger.info(f"补充员工创建完成: 新增{inserted}名, 系统总数: {new_total}")

        return {
            "success": True,
            "before_count": current_count,
            "after_count": new_total,
            "target": TOTAL_EMPLOYEE_TARGET,
            "gap_filled": gap,
            "filler_added": inserted,
            "filler_categories_used": len(filler_categories)
        }

    def export_registry_json(self, path: str) -> Dict[str, Any]:
        """
        导出完整注册表为JSON格式供审计
        """
        logger.info(f"导出AI注册表到: {path}")

        registry_data: List[Dict[str, Any]] = []
        total_count = 0
        arduino_count = 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ai_agent_registry ORDER BY load_order ASC")
                for row in cursor.fetchall():
                    item = dict(row)
                    item["capabilities"] = json.loads(item.get("capabilities") or "[]")
                    try:
                        item["config"] = json.loads(item.get("config") or "{}")
                    except (json.JSONDecodeError, TypeError):
                        item["config"] = {}

                    registry_data.append(item)
                    total_count += 1
                    if item["agent_type"] and item["agent_type"].startswith("arduino_"):
                        arduino_count += 1

            export_result = {
                "export_timestamp": datetime.now().isoformat(),
                "expansion_version": "3.0",
                "total_records": total_count,
                "arduino_records": arduino_count,
                "non_arduino_records": total_count - arduino_count,
                "registry": registry_data
            }

            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_result, f, ensure_ascii=False, indent=2)

            logger.info(f"导出完成: 共{total_count}条记录，Arduino员工{arduino_count}名")

            return {
                "success": True,
                "path": path,
                "total_records": total_count,
                "arduino_records": arduino_count,
                "file_size_bytes": os.path.getsize(path)
            }

        except Exception as e:
            logger.error(f"导出注册表失败: {e}")
            return {"success": False, "error": str(e)}


def main():
    """主函数：执行扩容流程，输出摘要，确保总数达到10810"""
    print("=" * 80)
    print("Arduino AI 员工扩容系统 v3.0")
    print("=" * 80)
    print(f"启动时间: {datetime.now().isoformat()}")
    print()

    expander = ArduinoEmployeeExpander()
    print(f"[1/5] 数据库路径: {expander.db_path}")
    print(f"      当前注册表员工数: {expander._get_current_employee_count()}")
    print()

    print("[2/5] 正在创建Arduino AI员工 (覆盖46个功能类别)...")
    employees = expander.expand_all_employees(register_in_db=True)
    print(f"      创建完成: {len(employees)} 名员工")
    print()

    print("[3/5] 生成扩容摘要...")
    summary = expander.get_expansion_summary()
    print(f"      功能类别数: {summary['category_count']}")
    print(f"      Arduino员工总数: {summary['total_arduino_by_category']}")

    print("      团队分布:")
    for team, count in sorted(summary["team_distribution"].items(), key=lambda x: -x[1]):
        print(f"        - {team}: {count}人")

    print("      等级分布:")
    for level, count in sorted(summary["level_distribution"].items()):
        bar = "█" * (count // 2)
        print(f"        {level}: {count:4d} {bar}")
    print()

    print(f"[4/5] 确保系统总员工数 >= {TOTAL_EMPLOYEE_TARGET}...")
    ensure_result = expander.ensure_10810_total()
    if ensure_result["success"]:
        if "filler_added" in ensure_result:
            print(f"      补充员工: +{ensure_result['filler_added']} 名")
        print(f"      员工总数: {ensure_result.get('after_count', ensure_result.get('current_count', 0))}")
        print(f"      目标: {TOTAL_EMPLOYEE_TARGET} ✓")
    else:
        print(f"      错误: {ensure_result.get('error', '未知错误')}")
    print()

    export_path = os.path.join(PROJECT_ROOT, "_output", "arduino_employee_registry_export.json")
    print(f"[5/5] 导出注册表到: {export_path}")
    export_result = expander.export_registry_json(export_path)
    if export_result["success"]:
        print(f"      导出成功: {export_result['total_records']} 条记录")
        print(f"      文件大小: {export_result.get('file_size_bytes', 0) / 1024:.1f} KB")
    else:
        print(f"      导出失败: {export_result.get('error', '未知错误')}")
    print()

    final_count = expander._get_current_employee_count()
    print("=" * 80)
    print("扩容完成")
    print("=" * 80)
    print(f"系统AI员工总数: {final_count}")
    print(f"目标: {TOTAL_EMPLOYEE_TARGET}")
    print(f"状态: {'✓ 达标' if final_count >= TOTAL_EMPLOYEE_TARGET else '✗ 未达标'}")
    print(f"Arduino员工占比: {round((summary['total_arduino_by_category'] / final_count * 100), 2) if final_count > 0 else 0}%")
    print(f"完成时间: {datetime.now().isoformat()}")

    return {
        "success": final_count >= TOTAL_EMPLOYEE_TARGET,
        "total_employees": final_count,
        "target": TOTAL_EMPLOYEE_TARGET,
        "arduino_employees": summary["total_arduino_by_category"]
    }


if __name__ == '__main__':
    main()
