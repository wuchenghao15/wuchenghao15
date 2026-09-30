"""auto_gen_zero_trust v6.0 - 设备指纹模块"""
import hashlib
from flask import request

class DeviceFingerprint:
    def __init__(self): self.size = 16
    def collect(self):
        parts = [
            request.remote_addr or "unknown",
            request.headers.get("User-Agent", "unknown"),
            request.headers.get("Accept-Language", "unknown"),
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]

if __name__ == "__main__":
    print("auto_gen_zero_trust v6.0 ready")
