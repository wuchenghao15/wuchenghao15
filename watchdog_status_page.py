#!/usr/bin/env python3
"""仙女座状态页守护进程 — Python 写, 彻底脱离 shell 组"""
import os, sys, time, signal, subprocess, logging, socket

PORT = 8889

# 统一运行目录 (不散落 /tmp)
_RUN_DIR = os.path.expanduser("~/.mtscos/run")
os.makedirs(_RUN_DIR, exist_ok=True)
PID_FILE = os.path.join(_RUN_DIR, "andromeda_status_page.pid")
LOG_FILE = os.path.join(_RUN_DIR, "status_watchdog.log")
STATUS_STDOUT = os.path.join(_RUN_DIR, "andromeda_status.out.log")
STATUS_STDERR = os.path.join(_RUN_DIR, "andromeda_status.err.log")

# 状态页模块位置 (自动探测: 同目录 engines/ 或项目根 engines/)
_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_HERE) == "engines":
    # 守护自己在 engines/ 目录里
    APP_DIR = _HERE  # 状态页也在这儿
else:
    # 守护在项目根
    APP_DIR = os.path.join(_HERE, "flask-app")
APP_SCRIPT = os.path.join(APP_DIR, "engines", "andromeda_status_page.py")
CHECK_INTERVAL = 5  # 秒

# 日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger("watchdog")

# 忽略常见信号, 不会被 shell kill 带走
signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

def is_port_listening(port: int) -> bool:
    """检查端口是否被监听"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

def read_pidfile() -> int | None:
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        # 验证进程真的存在
        os.kill(pid, 0)
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        return None

def start_status_page() -> bool:
    """启动状态页 — 用 Popen 彻底脱离父进程"""
    # 清旧
    old_pid = read_pidfile()
    if old_pid:
        try:
            os.kill(old_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    
    # 清端口 (lsof 在 macOS 可用)
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{PORT}"],
            capture_output=True, text=True, timeout=3
        )
        for pid_str in result.stdout.strip().split("\n"):
            if pid_str.strip():
                try:
                    os.kill(int(pid_str), signal.SIGKILL)
                except (ProcessLookupError, ValueError):
                    pass
    except Exception:
        pass
    
    time.sleep(0.5)
    
    # 启动 (DETACHED_PROCESS 等价: 用 fork+setsid 方式)
    try:
        log.info(f"启动状态页: {APP_SCRIPT} (cwd={APP_DIR})")
        proc = subprocess.Popen(
            [sys.executable, "-u", APP_SCRIPT],
            cwd=APP_DIR,
            stdout=open(STATUS_STDOUT, "a"),
            stderr=open(STATUS_STDERR, "a"),
            # 关键: 彻底脱离父进程组
            start_new_session=True,
            close_fds=True,
        )
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        log.info(f"✅ 启动 PID={proc.pid} 端口={PORT}")
        return True
    except Exception as e:
        log.error(f"❌ 启动失败: {e}")
        return False

def main():
    log.info("👁️ 守护启动")
    
    # 先确保状态页在跑
    pid = read_pidfile()
    port_ok = is_port_listening(PORT)
    if not pid or not port_ok:
        log.info("首次启动状态页")
        start_status_page()
        time.sleep(3)
    
    crash_count = 0
    CONSECUTIVE_CRASH_THRESHOLD = 3  # 连续 3 次检测到挂才重启 (5s × 3 = 15s)
    
    while True:
        pid = read_pidfile()
        port_ok = is_port_listening(PORT)
        
        # 健康判定: 端口监听 OR (PID 存在且进程活着) — 任一即为 OK
        healthy = port_ok or pid is not None
        
        if not healthy:
            crash_count += 1
            if crash_count >= CONSECUTIVE_CRASH_THRESHOLD:
                log.warning(f"💥 确认崩溃 (连续 {crash_count} 次 port/PID 均不可用) → 重启")
                # 先彻底清端口再拉
                try:
                    lsof_out = subprocess.run(["lsof", "-ti", f"tcp:{PORT}"], capture_output=True, timeout=3).stdout
                    for _pid in lsof_out.decode().strip().split("\n"):
                        _pid = _pid.strip()
                        if _pid:
                            os.kill(int(_pid), 9)
                except Exception:
                    pass
                time.sleep(1)
                start_status_page()
                crash_count = 0  # 重启后归零, 等后续观察
            else:
                log.info(f"⏳ 状态页可能在启动/重启中 ({crash_count}/{CONSECUTIVE_CRASH_THRESHOLD})")
        else:
            if crash_count > 0:
                log.info(f"✅ 恢复正常 (连续 {crash_count} 次检测到 port/PID 暂不可用, 现已 OK)")
            crash_count = 0
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
