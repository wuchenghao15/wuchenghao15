#!/usr/bin/env python3
"""
§五 安全密码学引擎
====================
AES-GCM 对称加密 + HMAC-SHA256 签名 + 数据指纹 + 密钥管理
对接 cryptography + PyNaCl
"""
import os, json, hashlib, hmac, base64, time, sqlite3, secrets, threading
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from nacl.public import PrivateKey, PublicKey, Box
from nacl.secret import SecretBox
from nacl.utils import random as nacl_random

_DB_PATH = os.environ.get("APP_DB") or None
if not _DB_PATH:
    for p in [os.path.expanduser("~/mtscos/_runtime/databases/Database/app.db")]:
        if os.path.exists(p): _DB_PATH = p; break

_lock = threading.RLock()

def _db():
    c = sqlite3.connect(_DB_PATH or ":memory:")
    c.execute("PRAGMA journal_mode=WAL")
    return c

# ===== 初始化表 =====
def _init_db():
    c = _db()
    c.executescript("""
CREATE TABLE IF NOT EXISTS mt_crypto_keys (
    key_id         TEXT PRIMARY KEY,
    key_type       TEXT NOT NULL,        -- aes_gcm / hmac / nacl_x25519 / nacl_ed25519
    key_name       TEXT,
    key_b64        TEXT NOT NULL,
    is_active      INTEGER DEFAULT 1,
    purpose        TEXT,                 -- encrypt/sign/hash
    expires_at     TEXT,
    created_at     TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS mt_crypto_log (
    op_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    operation      TEXT NOT NULL,        -- encrypt/decrypt/sign/verify/hash
    key_id         TEXT,
    algorithm      TEXT,
    data_len       INTEGER,
    latency_ms     REAL,
    success        INTEGER DEFAULT 1,
    user_id        TEXT,
    created_at     TEXT DEFAULT (datetime('now','localtime'))
);
    """)
    c.commit()
    c.close()

# ===== AES-GCM 对称加密 =====
def aes_gcm_encrypt(plaintext: bytes, key: bytes = None, aad: bytes = b"") -> dict:
    """
    AES-256-GCM 认证加密
    返回 {"ciphertext_b64", "nonce_b64", "key_b64"}
    """
    t0 = time.time()
    if key is None:
        key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    latency = (time.time() - t0) * 1000
    _log_op("encrypt", "AES-256-GCM", len(plaintext), latency, True)
    return {
        "ciphertext_b64": base64.b64encode(ct).decode(),
        "nonce_b64": base64.b64encode(nonce).decode(),
        "key_b64": base64.b64encode(key).decode(),
        "algorithm": "AES-256-GCM",
        "latency_ms": round(latency, 2),
    }

def aes_gcm_decrypt(ciphertext_b64: str, nonce_b64: str, key_b64: str, aad: bytes = b"") -> bytes:
    """AES-256-GCM 解密"""
    t0 = time.time()
    ct = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(nonce_b64)
    key = base64.b64decode(key_b64)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ct, aad)
    latency = (time.time() - t0) * 1000
    _log_op("decrypt", "AES-256-GCM", len(plaintext), latency, True)
    return plaintext

# ===== HMAC-SHA256 签名 =====
def hmac_sign(data: bytes, key: bytes = None) -> dict:
    """HMAC-SHA256 数据签名"""
    t0 = time.time()
    if key is None:
        key = secrets.token_bytes(32)
    sig = hmac.new(key, data, hashlib.sha256).digest()
    latency = (time.time() - t0) * 1000
    _log_op("sign", "HMAC-SHA256", len(data), latency, True)
    return {
        "signature_b64": base64.b64encode(sig).decode(),
        "key_b64": base64.b64encode(key).decode(),
        "algorithm": "HMAC-SHA256",
        "latency_ms": round(latency, 2),
    }

def hmac_verify(data: bytes, signature_b64: str, key_b64: str) -> bool:
    """HMAC-SHA256 验签"""
    t0 = time.time()
    sig = base64.b64decode(signature_b64)
    key = base64.b64decode(key_b64)
    ok = hmac.compare_digest(hmac.new(key, data, hashlib.sha256).digest(), sig)
    latency = (time.time() - t0) * 1000
    _log_op("verify", "HMAC-SHA256", len(data), latency, ok)
    return ok

# ===== 数据指纹（SHA-256）=====
def data_fingerprint(data: bytes) -> dict:
    """计算 SHA-256 指纹 + 简化的 hash 层级对比"""
    t0 = time.time()
    h256 = hashlib.sha256(data).hexdigest()
    h1 = hashlib.md5(data).hexdigest()
    latency = (time.time() - t0) * 1000
    _log_op("hash", "SHA-256", len(data), latency, True)
    return {
        "sha256": h256,
        "md5": h1,
        "length": len(data),
        "latency_ms": round(latency, 2),
    }

# ===== PyNaCl 公钥加密 =====
def nacl_keypair() -> dict:
    """生成 X25519 密钥对"""
    sk = PrivateKey.generate()
    pk = sk.public_key
    return {
        "private_key_b64": base64.b64encode(bytes(sk)).decode(),
        "public_key_b64": base64.b64encode(bytes(pk)).decode(),
        "algorithm": "X25519-XSalsa20-Poly1305",
    }

def nacl_box_encrypt(plaintext: bytes, private_key_b64: str, peer_public_key_b64: str) -> dict:
    """Box 公钥加密（ authenticated encryption）"""
    t0 = time.time()
    sk = PrivateKey(base64.b64decode(private_key_b64))
    pk = PublicKey(base64.b64decode(peer_public_key_b64))
    box = Box(sk, pk)
    ct = box.encrypt(plaintext)
    latency = (time.time() - t0) * 1000
    _log_op("encrypt", "X25519-Box", len(plaintext), latency, True)
    return {"ciphertext_b64": base64.b64encode(ct).decode(), "algorithm": "X25519-Box", "latency_ms": round(latency, 2)}

def nacl_box_decrypt(ciphertext_b64: str, private_key_b64: str, peer_public_key_b64: str) -> bytes:
    """Box 公钥解密"""
    t0 = time.time()
    sk = PrivateKey(base64.b64decode(private_key_b64))
    pk = PublicKey(base64.b64decode(peer_public_key_b64))
    box = Box(sk, pk)
    plaintext = box.decrypt(base64.b64decode(ciphertext_b64))
    latency = (time.time() - t0) * 1000
    _log_op("decrypt", "X25519-Box", len(plaintext), latency, True)
    return plaintext

# ===== 日志 =====
def _log_op(op, algo, data_len, latency_ms, success):
    try:
        c = _db()
        c.execute("""INSERT INTO mt_crypto_log
            (operation, algorithm, data_len, latency_ms, success)
            VALUES (?,?,?,?,?)""", (op, algo, data_len, latency_ms, 1 if success else 0))
        c.commit()
        c.close()
    except Exception:
        pass

# ===== 性能测试 =====
def bench() -> dict:
    """快速测试所有算法性能"""
    import time
    results = {}
    data = b"MTSCOS AI crypto test payload " * 100  # ~2800 bytes
    
    t0 = time.time()
    r = aes_gcm_encrypt(data)
    aes_gcm_decrypt(r["ciphertext_b64"], r["nonce_b64"], r["key_b64"])
    results["AES-256-GCM"] = f"{(time.time()-t0)*1000:.1f}ms"
    
    t0 = time.time()
    r = hmac_sign(data)
    hmac_verify(data, r["signature_b64"], r["key_b64"])
    results["HMAC-SHA256"] = f"{(time.time()-t0)*1000:.1f}ms"
    
    t0 = time.time()
    data_fingerprint(data)
    results["SHA-256"] = f"{(time.time()-t0)*1000:.1f}ms"
    
    kp = nacl_keypair()
    t0 = time.time()
    r = nacl_box_encrypt(data, kp["private_key_b64"], kp["public_key_b64"])
    nacl_box_decrypt(r["ciphertext_b64"], kp["private_key_b64"], kp["public_key_b64"])
    results["X25519-Box"] = f"{(time.time()-t0)*1000:.1f}ms"
    
    return results

# 自动初始化
_init_db()
print("[CRYPTO] crypto_engine initialized (AES-GCM + HMAC + SHA-256 + X25519-Box)")
