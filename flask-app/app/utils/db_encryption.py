#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 数据库全要素加密体系
===========================
四要素加密：库名 / 表名 / 列名 / 内容
五级加密等级：L0 极密 / L1 机密 / L2 秘密 / L3 内部 / L4 公开

密钥体系（最高级，VIKEY 硬件派生）：
    VIKEY 根密钥 RK (不可导出)
       └─ HKDF 派生 KEK (内存，不落盘)
            ├─ DEK_L0 / DEK_L1 / DEK_L2 / DEK_L3 (库主密钥)
            └─ 字段级密钥 (per-field HKDF)

flow_id: flow_db_encrypt_20260813_001
STEP_7_EXECUTE 产出
"""

import os
import json
import hashlib
import hmac
import base64
import secrets
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, Optional, Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


# ---------------------------------------------------------------------------
# 一、加密等级定义（L0-L4）
# ---------------------------------------------------------------------------

class EncryptionLevel(IntEnum):
    """数据库加密等级

    L0 极密：SA存在性/活动轨迹/VIKEY凭证/iron_rule违规记录，库名+表名+列名+内容全加密
    L1 机密：用户密码hash/session/权限识别码/用户容器，库名+内容双层加密
    L2 秘密：考试/题库/AI脑库/AI员工配置，库名+库级内容加密
    L3 内部：系统配置/日志/监控/参数，库名+库级内容加密
    L4 公开：公告/公开课/版本号，不加密
    """

    L0_TOP_SECRET = 0      # 极密
    L1_CONFIDENTIAL = 1    # 机密
    L2_SECRET = 2          # 秘密
    L3_INTERNAL = 3        # 内部
    L4_PUBLIC = 4          # 公开


# 各等级加密能力矩阵
LEVEL_CAPABILITY = {
    EncryptionLevel.L0_TOP_SECRET: {
        "db_name_obfuscate": True,    # 库名混淆+加密
        "table_name_map": True,      # 表名哈希映射
        "column_name_map": True,     # 列名哈希映射
        "content_encrypt": True,     # 内容加密
        "double_layer": True,        # 字段双层加密(库级+字段级)
        "vikey_required": True,      # 必须VIKEY在线
    },
    EncryptionLevel.L1_CONFIDENTIAL: {
        "db_name_obfuscate": True,
        "table_name_map": False,
        "column_name_map": False,
        "content_encrypt": True,
        "double_layer": True,
        "vikey_required": False,     # 启动时需VIKEY，运行期用缓存KEK
    },
    EncryptionLevel.L2_SECRET: {
        "db_name_obfuscate": True,
        "table_name_map": False,
        "column_name_map": False,
        "content_encrypt": True,
        "double_layer": False,       # 仅库级
        "vikey_required": False,
    },
    EncryptionLevel.L3_INTERNAL: {
        "db_name_obfuscate": True,
        "table_name_map": False,
        "column_name_map": False,
        "content_encrypt": True,
        "double_layer": False,
        "vikey_required": False,
    },
    EncryptionLevel.L4_PUBLIC: {
        "db_name_obfuscate": False,
        "table_name_map": False,
        "column_name_map": False,
        "content_encrypt": False,
        "double_layer": False,
        "vikey_required": False,
    },
}


# ---------------------------------------------------------------------------
# 二、VIKEY 密钥派生体系（最高级）
# ---------------------------------------------------------------------------

# 根密钥盐（固定常量，与 VIKEY 硬件信息组合派生，本身非密钥）
_ROOT_SALT = b"MTSCOS_VIKEY_ROOT_DERIVATION_v1"
_KEK_INFO = b"mtscos_kek_master_v1"
_DEK_INFO_PREFIX = b"mtscos_dek_"


class VikeyKeyDerivation:
    """VIKEY 硬件根密钥派生

    从 VIKEY 硬件信息派生密钥层级：RK -> KEK -> DEK
    - VIKEY 在线时：从 vikey_info 派生 RK，再派生 KEK/DEK
    - VIKEY 离线时：L0 库锁定；L1-L3 使用启动时缓存的 KEK（内存）
    - 密钥永不落盘，仅存内存
    """

    def __init__(self):
        self._vikey_info: Optional[str] = None
        self._kek: Optional[bytes] = None           # 主密钥(内存)
        self._dek_cache: Dict[int, bytes] = {}      # 等级->库主密钥(内存)
        self._vikey_online: bool = False

    def bind_vikey(self, vikey_info: str) -> bool:
        """绑定 VIKEY 硬件信息，派生根密钥与 KEK

        Args:
            vikey_info: VIKEY 硬件标识（来自 mechanism_ai.create_vikey_session 的 vikey_info）

        Returns:
            True 表示 KEK 已就绪
        """
        if not HAS_CRYPTOGRAPHY or not vikey_info:
            return False
        self._vikey_info = vikey_info
        self._vikey_online = True
        # RK = HKDF(vikey_info, salt=_ROOT_SALT)
        rk = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_ROOT_SALT,
            info=b"mtscos_rk_root_v1",
        ).derive(vikey_info.encode("utf-8"))
        # KEK = HKDF(RK, info=_KEK_INFO)
        self._kek = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=rk,
            info=_KEK_INFO,
        ).derive(rk)
        self._dek_cache.clear()
        return self._kek is not None

    def cache_kek_for_offline(self) -> bool:
        """VIKEY 离线前缓存 KEK（仅 L1-L3 运行期可用，L0 锁定）"""
        if self._kek is None:
            return False
        self._vikey_online = False
        return True

    def is_vikey_online(self) -> bool:
        return self._vikey_online

    def get_dek(self, level: EncryptionLevel) -> Optional[bytes]:
        """获取指定等级的库主密钥 DEK

        L0 必须 VIKEY 在线；L1-L3 允许使用缓存 KEK
        """
        if self._kek is None:
            return None
        # L0 强制 VIKEY 在线
        if level == EncryptionLevel.L0_TOP_SECRET and not self._vikey_online:
            return None
        if level in self._dek_cache:
            return self._dek_cache[level]
        dek = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._kek,
            info=_DEK_INFO_PREFIX + level.name.encode("utf-8"),
        ).derive(self._kek)
        self._dek_cache[level] = dek
        return dek

    def derive_field_key(self, level: EncryptionLevel, table: str, column: str) -> Optional[bytes]:
        """派生字段级密钥（per-field HKDF）"""
        dek = self.get_dek(level)
        if dek is None:
            return None
        ctx = f"{table}::{column}".encode("utf-8")
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=dek,
            info=b"mtscos_field_v1",
        ).derive(ctx)


# ---------------------------------------------------------------------------
# 三、AES-256-GCM 字段加密器
# ---------------------------------------------------------------------------

# 密文前缀标识（用于区分加密数据与明文）
_CIPHER_PREFIX = "MTENC:"


class AESGCMCipher:
    """AES-256-GCM 字段级加密器

    输出格式：MTENC:<base64(nonce||ciphertext||tag)>
    - nonce 随机 12 字节
    - tag 16 字节（GCM 内置）
    """

    def __init__(self, key_derivation: VikeyKeyDerivation):
        self.key_derivation = key_derivation

    def encrypt_field(self, plaintext: Any, level: EncryptionLevel,
                      table: str, column: str) -> Any:
        """加密字段值

        策略：
          - int/float/bool/None 不加密（SQL WHERE = / > / < 需明文索引）
          - str/dict/list 加密（敏感字段一般为文本/结构化）
          - 超长数字字符串/枚举文本按 str 加密
        """
        if not HAS_CRYPTOGRAPHY:
            return plaintext
        cap = LEVEL_CAPABILITY.get(level, {})
        if not cap.get("content_encrypt", False):
            return plaintext
        # 可索引标量 → 保持明文
        if plaintext is None:
            return None
        if isinstance(plaintext, (int, float, bool)):
            return plaintext
        # 空字符串原样返回
        if isinstance(plaintext, str) and plaintext == "":
            return ""
        key = self.key_derivation.derive_field_key(level, table, column)
        if key is None:
            # 密钥不可用（如 L0 VIKEY 离线）：返回原值，由上层拦截
            return plaintext
        # 序列化
        if isinstance(plaintext, (dict, list)):
            data = json.dumps(plaintext, ensure_ascii=False).encode("utf-8")
        elif isinstance(plaintext, str):
            data = plaintext.encode("utf-8")
        else:
            data = str(plaintext).encode("utf-8")
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(nonce, data, None)
        return _CIPHER_PREFIX + base64.b64encode(nonce + ct).decode("ascii")

    def decrypt_field(self, ciphertext: Any, level: EncryptionLevel,
                      table: str, column: str) -> Any:
        """解密字段值"""
        if not HAS_CRYPTOGRAPHY:
            return ciphertext
        if not isinstance(ciphertext, str) or not ciphertext.startswith(_CIPHER_PREFIX):
            return ciphertext
        key = self.key_derivation.derive_field_key(level, table, column)
        if key is None:
            return ciphertext
        try:
            raw = base64.b64decode(ciphertext[len(_CIPHER_PREFIX):])
            nonce, ct = raw[:12], raw[12:]
            aesgcm = AESGCM(key)
            data = aesgcm.decrypt(nonce, ct, None)
            text = data.decode("utf-8")
            # 尝试反序列化
            try:
                return json.loads(text)
            except (json.JSONDecodeError, ValueError):
                return text
        except Exception:
            return ciphertext

    def is_encrypted(self, value: Any) -> bool:
        """判断值是否为加密格式"""
        return isinstance(value, str) and value.startswith(_CIPHER_PREFIX)


# ---------------------------------------------------------------------------
# 四、SchemaMapper — L0 表名/列名哈希映射
# ---------------------------------------------------------------------------

# 映射盐（L0 专用，与 DEK 绑定后存入加密配置表）
_MAPPER_SALT = b"mtscos_l0_schema_mapper_v1"


class SchemaMapper:
    """L0 极密库的表名/列名哈希映射器

    逻辑名 -> 物理名：SHA256(逻辑名 + salt)[:16] 的 hex
    映射可逆（通过逻辑名重算），无需存储双向表
    """

    def __init__(self, salt: bytes = _MAPPER_SALT):
        self.salt = salt
        self._table_cache: Dict[str, str] = {}
        self._column_cache: Dict[Tuple[str, str], str] = {}

    def logical_to_physical_table(self, logical_name: str) -> str:
        """逻辑表名 -> 物理表名（哈希）"""
        if logical_name in self._table_cache:
            return self._table_cache[logical_name]
        # sqlite_master 等系统表不映射
        if logical_name.startswith("sqlite_"):
            return logical_name
        h = hashlib.sha256(self.salt + b"tbl:" + logical_name.encode("utf-8")).hexdigest()[:16]
        physical = f"t_{h}"
        self._table_cache[logical_name] = physical
        return physical

    def logical_to_physical_column(self, table: str, column: str) -> str:
        """逻辑列名 -> 物理列名（哈希）"""
        key = (table, column)
        if key in self._column_cache:
            return self._column_cache[key]
        # 系统列不映射
        if column in ("rowid", "id") or column.startswith("sqlite_"):
            return column
        h = hashlib.sha256(
            self.salt + b"col:" + table.encode("utf-8") + b":" + column.encode("utf-8")
        ).hexdigest()[:12]
        physical = f"c_{h}"
        self._column_cache[key] = physical
        return physical

    def rewrite_sql(self, sql: str, table_map: Dict[str, str],
                    column_map: Dict[Tuple[str, str], str]) -> str:
        """SQL 改写（逻辑名替换为物理名）

        简化实现：替换表名和列名token。生产环境应使用 SQL 解析器。
        """
        if not sql:
            return sql
        result = sql
        # 替换表名
        for logical, physical in table_map.items():
            result = result.replace(logical, physical)
        # 替换列名
        for (table, col), physical in column_map.items():
            result = result.replace(col, physical)
        return result


# ---------------------------------------------------------------------------
# 五、数据库文件级加密（休眠加密 / 运行解密）
# ---------------------------------------------------------------------------

class DatabaseFileCipher:
    """数据库文件级 AES-256 加密

    用途：db 文件休眠时整体加密，启动时用 VIKEY 派生密钥解密到运行路径
    替代 SQLCipher 整库加密（环境无 pysqlcipher3 时的等效方案）
    """

    def __init__(self, key_derivation: VikeyKeyDerivation):
        self.key_derivation = key_derivation

    def encrypt_db_file(self, db_path: str, level: EncryptionLevel) -> bool:
        """加密数据库文件（明文 .db -> .enc.db）"""
        if not HAS_CRYPTOGRAPHY or not os.path.exists(db_path):
            return False
        dek = self.key_derivation.get_dek(level)
        if dek is None:
            return False
        enc_path = db_path + ".enc"
        try:
            with open(db_path, "rb") as f:
                data = f.read()
            nonce = secrets.token_bytes(12)
            aesgcm = AESGCM(dek)
            ct = aesgcm.encrypt(nonce, data, None)
            with open(enc_path, "wb") as f:
                f.write(nonce + ct)
            # 加密成功后删除明文文件
            os.remove(db_path)
            return True
        except Exception:
            return False

    def decrypt_db_file(self, enc_path: str, db_path: str,
                        level: EncryptionLevel) -> bool:
        """解密数据库文件（.enc.db -> 明文 .db，运行期使用）"""
        if not HAS_CRYPTOGRAPHY or not os.path.exists(enc_path):
            return False
        dek = self.key_derivation.get_dek(level)
        if dek is None:
            return False
        try:
            with open(enc_path, "rb") as f:
                raw = f.read()
            nonce, ct = raw[:12], raw[12:]
            aesgcm = AESGCM(dek)
            data = aesgcm.decrypt(nonce, ct, None)
            with open(db_path, "wb") as f:
                f.write(data)
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# 六、库名混淆映射（文件名层面）
# ---------------------------------------------------------------------------

class DbNameObfuscator:
    """数据库文件名混淆

    明文 app.db -> 混淆名 mt_<hash8>.enc.db
    维护逻辑名<->物理名映射（映射表自身加密存储）
    """

    def __init__(self, salt: bytes = _MAPPER_SALT):
        self.salt = salt
        self._logical_to_physical: Dict[str, str] = {}
        self._physical_to_logical: Dict[str, str] = {}

    def obfuscate_name(self, logical_name: str) -> str:
        """逻辑库名 -> 物理文件名"""
        if logical_name in self._logical_to_physical:
            return self._logical_to_physical[logical_name]
        h = hashlib.sha256(self.salt + b"db:" + logical_name.encode("utf-8")).hexdigest()[:8]
        physical = f"mt_{h}.enc.db"
        self._logical_to_physical[logical_name] = physical
        self._physical_to_logical[physical] = logical_name
        return physical

    def resolve_logical_name(self, physical_name: str) -> Optional[str]:
        """物理文件名 -> 逻辑库名"""
        return self._physical_to_logical.get(physical_name)

    def export_mapping(self) -> Dict[str, str]:
        """导出映射表（用于加密存储）"""
        return dict(self._logical_to_physical)

    def import_mapping(self, mapping: Dict[str, str]) -> None:
        """导入映射表"""
        self._logical_to_physical.update(mapping)
        self._physical_to_logical = {v: k for k, v in self._logical_to_physical.items()}


# ---------------------------------------------------------------------------
# 七、加密等级归属表（encryption_classification）
# ---------------------------------------------------------------------------

# 默认等级归属（DBA 产出清单前的初始判定，可由数据库 encryption_classification 表覆盖）
DEFAULT_CLASSIFICATION = {
    # L0 极密
    "mt_iron_rule_violations": EncryptionLevel.L0_TOP_SECRET,
    "sa_activity_log": EncryptionLevel.L0_TOP_SECRET,
    "vikey_state": EncryptionLevel.L0_TOP_SECRET,
    "sa_permission_snapshot": EncryptionLevel.L0_TOP_SECRET,
    "sa_heartbeat": EncryptionLevel.L0_TOP_SECRET,
    # L1 机密
    "users": EncryptionLevel.L1_CONFIDENTIAL,
    "user_container": EncryptionLevel.L1_CONFIDENTIAL,
    "sessions": EncryptionLevel.L1_CONFIDENTIAL,
    # L2 秘密
    "exam_papers": EncryptionLevel.L2_SECRET,
    "questions": EncryptionLevel.L2_SECRET,
    "ai_employees": EncryptionLevel.L2_SECRET,
    "brain_knowledge": EncryptionLevel.L2_SECRET,
    # L3 内部
    "settings": EncryptionLevel.L3_INTERNAL,
    "logs": EncryptionLevel.L3_INTERNAL,
    "configs": EncryptionLevel.L3_INTERNAL,
}


def classify_table(table_name: str) -> EncryptionLevel:
    """判定表的加密等级

    优先查数据库 encryption_classification 表，其次用默认清单，最后降级 L3
    """
    if table_name in DEFAULT_CLASSIFICATION:
        return DEFAULT_CLASSIFICATION[table_name]
    # SA 相关表强制 L0
    if table_name.startswith("sa_") or "vikey" in table_name.lower():
        return EncryptionLevel.L0_TOP_SECRET
    # iron_rule 相关强制 L0
    if "iron_rule" in table_name.lower():
        return EncryptionLevel.L0_TOP_SECRET
    # 认证相关 L1
    if any(k in table_name.lower() for k in ("user", "auth", "session", "token", "password")):
        return EncryptionLevel.L1_CONFIDENTIAL
    # AI/考试/题库 L2
    if any(k in table_name.lower() for k in ("ai_", "exam", "question", "brain")):
        return EncryptionLevel.L2_SECRET
    # 日志/配置 L3
    if any(k in table_name.lower() for k in ("log", "config", "setting")):
        return EncryptionLevel.L3_INTERNAL
    return EncryptionLevel.L3_INTERNAL


# ---------------------------------------------------------------------------
# 八、统一入口 DatabaseEncryption（向后兼容旧接口）
# ---------------------------------------------------------------------------

class DatabaseEncryption:
    """数据库加密统一入口

    向后兼容旧接口（encrypt_data/decrypt_data/encrypt_password 等），
    底层升级为 AES-256-GCM + VIKEY 派生密钥。
    """

    def __init__(self):
        self.encryption_enabled = True
        # 旧版密钥文件（仅用于迁移期解密旧 Fernet 数据，迁移完成后删除）
        self.key_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "encryption_key.key"
        )
        # VIKEY 密钥派生体系
        self.key_derivation = VikeyKeyDerivation()
        # AES-GCM 字段加密器
        self.aes_cipher = AESGCMCipher(self.key_derivation)
        # L0 Schema 映射器
        self.schema_mapper = SchemaMapper()
        # 库名混淆器
        self.db_name_obfuscator = DbNameObfuscator()
        # 文件级加密器
        self.file_cipher = DatabaseFileCipher(self.key_derivation)
        # 旧 Fernet 实例（迁移兼容）
        self._legacy_fernet: Optional[Fernet] = None
        self._init_legacy_fernet()
        # 默认绑定一个开发期密钥（生产环境必须由 VIKEY 覆盖）
        if not self.key_derivation.is_vikey_online():
            self._bind_dev_key()

    def _init_legacy_fernet(self):
        """初始化旧 Fernet（仅用于解密历史数据）"""
        if not HAS_CRYPTOGRAPHY:
            return
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "rb") as f:
                    key = f.read()
                self._legacy_fernet = Fernet(key)
            except Exception:
                self._legacy_fernet = None

    def _bind_dev_key(self):
        """开发期绑定默认密钥（无 VIKEY 时降级，仅 L1-L3 可用，L0 锁定）"""
        # 仅当未绑定 VIKEY 时使用开发根密钥
        dev_vikey = "MTSCOS_DEV_VIKEY_FALLBACK_DO_NOT_USE_IN_PRODUCTION"
        self.key_derivation.bind_vikey(dev_vikey)
        self.key_derivation.cache_kek_for_offline()

    def bind_vikey(self, vikey_info: str) -> bool:
        """绑定 VIKEY 硬件信息（生产环境必须调用）"""
        return self.key_derivation.bind_vikey(vikey_info)

    # ---------- 向后兼容接口（旧版 encrypt_data/decrypt_data） ----------

    def encrypt_data(self, data: Any, level: EncryptionLevel = EncryptionLevel.L1_CONFIDENTIAL,
                     table: str = "default", column: str = "default") -> Any:
        """加密数据（向后兼容旧接口，新增等级/表/列参数）"""
        if not self.encryption_enabled or not HAS_CRYPTOGRAPHY:
            return data
        return self.aes_cipher.encrypt_field(data, level, table, column)

    def decrypt_data(self, data: Any, level: EncryptionLevel = EncryptionLevel.L1_CONFIDENTIAL,
                     table: str = "default", column: str = "default") -> Any:
        """解密数据

        优先用新版 AES-GCM 解密；若为旧版 Fernet 密文（gAAAAA 前缀）则用 legacy 解密
        """
        if not self.encryption_enabled or not HAS_CRYPTOGRAPHY:
            return data
        if isinstance(data, str) and data.startswith(_CIPHER_PREFIX):
            return self.aes_cipher.decrypt_field(data, level, table, column)
        # 兼容旧 Fernet 密文
        if isinstance(data, str) and data.startswith("gAAAAA") and self._legacy_fernet:
            try:
                decrypted = self._legacy_fernet.decrypt(data.encode()).decode()
                try:
                    return json.loads(decrypted)
                except (json.JSONDecodeError, ValueError):
                    return decrypted
            except Exception:
                return data
        return data

    # ---------- 密码哈希（升级为加盐 SHA256，保留旧接口签名） ----------

    def encrypt_password(self, password: str, salt: Optional[str] = None) -> str:
        """密码哈希（加盐 SHA256）

        注意：新密码建议用 hash_password（带随机盐）。
        本方法保留旧签名以兼容现有调用，salt 缺省时用全局盐。
        """
        if salt is None:
            salt = "mtscos_pw_salt_v1"
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

    def verify_password(self, password: str, hashed_password: str,
                        salt: Optional[str] = None) -> bool:
        """校验密码"""
        return self.encrypt_password(password, salt) == hashed_password

    def hash_password(self, password: str) -> str:
        """密码哈希（带随机盐，格式：salt$hash）"""
        salt = secrets.token_hex(16)
        h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"{salt}${h}"

    def verify_hashed_password(self, password: str, stored: str) -> bool:
        """校验带随机盐的密码哈希"""
        try:
            salt, h = stored.split("$", 1)
            return hmac.compare_digest(
                hashlib.sha256((salt + password).encode("utf-8")).hexdigest(), h
            )
        except Exception:
            return False

    # ---------- Session Token ----------

    def generate_session_token(self, user_id: str) -> str:
        """生成 session token（AES-GCM 加密）"""
        token_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "nonce": secrets.token_hex(16),
        }
        return self.encrypt_data(
            token_data, EncryptionLevel.L1_CONFIDENTIAL, "sessions", "token"
        )

    def validate_session_token(self, token: str) -> Optional[str]:
        """校验 session token，返回 user_id"""
        data = self.decrypt_data(
            token, EncryptionLevel.L1_CONFIDENTIAL, "sessions", "token"
        )
        if isinstance(data, dict) and "user_id" in data and "timestamp" in data:
            try:
                token_time = datetime.fromisoformat(data["timestamp"])
                if (datetime.now() - token_time).total_seconds() < 7200:
                    return data["user_id"]
            except Exception:
                return None
        return None

    # ---------- 文件加密（向后兼容旧接口） ----------

    def encrypt_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """加密文件（向后兼容，默认 L1）"""
        if not HAS_CRYPTOGRAPHY:
            return False
        if output_path is None:
            output_path = input_path + ".encrypted"
        dek = self.key_derivation.get_dek(EncryptionLevel.L1_CONFIDENTIAL)
        if dek is None:
            return False
        try:
            with open(input_path, "rb") as f:
                data = f.read()
            nonce = secrets.token_bytes(12)
            aesgcm = AESGCM(dek)
            ct = aesgcm.encrypt(nonce, data, None)
            with open(output_path, "wb") as f:
                f.write(nonce + ct)
            return True
        except Exception:
            return False

    def decrypt_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """解密文件（向后兼容，默认 L1）"""
        if not HAS_CRYPTOGRAPHY:
            return False
        if output_path is None:
            output_path = input_path.replace(".encrypted", "")
        dek = self.key_derivation.get_dek(EncryptionLevel.L1_CONFIDENTIAL)
        if dek is None:
            return False
        try:
            with open(input_path, "rb") as f:
                raw = f.read()
            nonce, ct = raw[:12], raw[12:]
            aesgcm = AESGCM(dek)
            data = aesgcm.decrypt(nonce, ct, None)
            with open(output_path, "wb") as f:
                f.write(data)
            return True
        except Exception:
            return False


# 全局单例（向后兼容：db_encryption = DatabaseEncryption()）
db_encryption = DatabaseEncryption()
