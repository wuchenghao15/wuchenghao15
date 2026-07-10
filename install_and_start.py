import paramiko

SERVER_IP = "192.168.31.105"
SERVER_USER = "wuchenghao15"
SERVER_PASS = "LoginMe.1988$"
REMOTE_DIR = "/home/wuchenghao15/mtscos_project"

def run_cmd(ssh, cmd, timeout=120):
    print(f"执行: {cmd[:60]}..." if len(cmd) > 60 else f"执行: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.set_combine_stderr(True)
    output = stdout.read().decode('utf-8', errors='ignore')
    code = stdout.channel.recv_exit_status()
    print(f"退出码: {code}")
    if output:
        lines = output.strip().split('\n')
        if len(lines) > 5:
            print(f"输出 (前5行): {lines[:5]}")
        else:
            print(f"输出: {output[:300]}")
    return output, code

def main():
    print("=== 步骤1: 建立SSH连接 ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=15)
    print("SSH连接成功")

    print("\n=== 步骤2: 更新pip并安装项目依赖 ===")
    run_cmd(ssh, f"{REMOTE_DIR}/venv/bin/python -m pip install --upgrade pip")
    run_cmd(ssh, f"{REMOTE_DIR}/venv/bin/python -m pip install -r {REMOTE_DIR}/flask-app/requirements.txt")

    print("\n=== 步骤3: 检查项目文件结构 ===")
    run_cmd(ssh, f"ls -la {REMOTE_DIR}/flask-app/")

    print("\n=== 步骤4: 停止旧服务 ===")
    run_cmd(ssh, "pkill -f 'python.*app.py' || true")

    print("\n=== 步骤5: 启动Flask服务 ===")
    cmd = f"cd {REMOTE_DIR}/flask-app && nohup {REMOTE_DIR}/venv/bin/python app.py > {REMOTE_DIR}/flask-app/app.log 2>&1 &"
    run_cmd(ssh, cmd)

    print("\n=== 步骤6: 等待服务启动 ===")
    import time
    time.sleep(8)

    print("\n=== 步骤7: 检查服务状态 ===")
    output, code = run_cmd(ssh, "pgrep -f 'python.*app.py' && echo '服务运行中' || echo '服务未运行'")

    print("\n=== 步骤8: 查看日志 ===")
    run_cmd(ssh, f"cat {REMOTE_DIR}/flask-app/app.log")

    print("\n=== 步骤9: 验证服务 ===")
    output, code = run_cmd(ssh, "curl -s http://localhost:8888/ -o /dev/null -w '%{http_code}' || echo '000'")
    print(f"HTTP状态码: {output.strip()}")

    ssh.close()
    print("\n完成！")

if __name__ == "__main__":
    main()