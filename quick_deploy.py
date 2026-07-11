import paramiko
import os

SERVER_IP = "192.168.31.105"
SERVER_USER = "wuchenghao15"
SERVER_PASS = "LoginMe.1988$"
PROJECT_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
REMOTE_DIR = "/home/wuchenghao15/mtscos_project"

def run_cmd(ssh, cmd):
    print(f"执行: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    stdout.channel.set_combine_stderr(True)
    output = stdout.read().decode('utf-8', errors='ignore')
    code = stdout.channel.recv_exit_status()
    print(f"退出码: {code}")
    if output:
        print(f"输出: {output[:200]}")
    return output, code

def main():
    print("=== 步骤1: 建立SSH连接 ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=15)
    print("SSH连接成功")

    print("\n=== 步骤2: 检查Python环境 ===")
    run_cmd(ssh, "which python3 && python3 --version")

    print("\n=== 步骤3: 安装依赖 ===")
    run_cmd(ssh, "export DEBIAN_FRONTEND=noninteractive && sudo apt-get update -y -qq")
    run_cmd(ssh, "sudo apt-get install -y -qq python3 python3-venv python3-pip curl")

    print("\n=== 步骤4: 创建虚拟环境 ===")
    run_cmd(ssh, f"rm -rf {REMOTE_DIR}/venv && python3 -m venv {REMOTE_DIR}/venv")

    print("\n=== 步骤5: 查看远程目录 ===")
    run_cmd(ssh, f"ls -la {REMOTE_DIR}/")

    ssh.close()
    print("\n完成！")

if __name__ == "__main__":
    main()