import paramiko
import os
import time
import socket

SERVER_IP = "192.168.31.105"
SERVER_USER = "wuchenghao15"
SERVER_PASS = "LoginMe.1988$"
PROJECT_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
REMOTE_DIR = "/home/wuchenghao15/mtscos_project"
FLASK_PORT = "8888"

def print_step(num, total, title):
    print(f"\n{'='*50}")
    print(f" [{num}/{total}] {title}")
    print(f"{'='*50}")

def run_ssh_command(ssh, command, sudo=False):
    if sudo:
        command = f"echo '{SERVER_PASS}' | sudo -S {command}"
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout.channel.set_combine_stderr(True)
    output = stdout.read().decode('utf-8', errors='ignore')
    return output, stdout.channel.recv_exit_status()

def sftp_upload_dir(sftp, local_dir, remote_dir):
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = os.path.join(remote_dir, item)
        if os.path.isdir(local_path):
            try:
                sftp.mkdir(remote_path)
            except IOError:
                pass
            sftp_upload_dir(sftp, local_path, remote_path)
        else:
            try:
                sftp.put(local_path, remote_path)
            except Exception as e:
                print(f"  跳过文件 {item}: {str(e)}")

def main():
    print("MTSCOS AI 项目部署脚本")
    print(f"目标服务器: {SERVER_IP}")
    
    print_step(1, 6, "检查远程服务器连接")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((SERVER_IP, 22))
        sock.close()
        if result == 0:
            print("✓ 服务器可访问")
        else:
            print("✗ 服务器不可访问，请检查网络连接")
            return
    except Exception as e:
        print(f"✗ 连接检查失败: {e}")
        return

    print_step(2, 6, "建立SSH连接")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=15)
        print("✓ SSH连接成功")
    except Exception as e:
        print(f"✗ SSH连接失败: {e}")
        return

    print_step(3, 6, "创建远程项目目录")
    output, code = run_ssh_command(ssh, f"mkdir -p {REMOTE_DIR} && mkdir -p {REMOTE_DIR}/flask-app")
    if code == 0:
        print("✓ 目录创建完成")
    else:
        print(f"✗ 目录创建失败: {output}")
        ssh.close()
        return

    print_step(4, 6, "传输项目文件到远程服务器")
    sftp = ssh.open_sftp()
    try:
        print("  正在传输 flask-app 目录...")
        sftp_upload_dir(sftp, os.path.join(PROJECT_DIR, "flask-app"), os.path.join(REMOTE_DIR, "flask-app"))
        print("  正在传输 VERSION 文件...")
        sftp.put(os.path.join(PROJECT_DIR, "VERSION"), os.path.join(REMOTE_DIR, "VERSION"))
        print("  正在传输 README.md 文件...")
        sftp.put(os.path.join(PROJECT_DIR, "README.md"), os.path.join(REMOTE_DIR, "README.md"))
        print("✓ 文件传输完成")
    except Exception as e:
        print(f"✗ 文件传输失败: {e}")
        sftp.close()
        ssh.close()
        return
    sftp.close()

    print_step(5, 6, "配置远程服务器环境")
    commands = [
        "export DEBIAN_FRONTEND=noninteractive",
        "sudo apt-get update -y -qq",
        "sudo apt-get install -y -qq python3 python3-venv python3-pip",
        f"rm -rf {REMOTE_DIR}/venv && python3 -m venv {REMOTE_DIR}/venv",
        f"{REMOTE_DIR}/venv/bin/python -m pip install --upgrade pip -q",
        f"{REMOTE_DIR}/venv/bin/python -m pip install -r {REMOTE_DIR}/flask-app/requirements.txt -q"
    ]
    
    for cmd in commands:
        print(f"  执行: {cmd[:50]}..." if len(cmd) > 50 else f"  执行: {cmd}")
        output, code = run_ssh_command(ssh, cmd)
        if code != 0:
            print(f"  ✗ 命令执行失败: {output.strip()[:100]}")
            ssh.close()
            return
    print("✓ 环境配置完成")

    print_step(6, 6, "启动Flask服务")
    commands = [
        "pkill -f 'python.*app.py' || true",
        "sleep 2",
        f"cd {REMOTE_DIR}/flask-app && nohup {REMOTE_DIR}/venv/bin/python app.py > {REMOTE_DIR}/flask-app/app.log 2>&1 &",
        "sleep 5",
        "pgrep -f 'python.*app.py' && echo 'SUCCESS' || echo 'FAILED'"
    ]
    
    for cmd in commands:
        output, code = run_ssh_command(ssh, cmd)
        if "FAILED" in output:
            print("✗ Flask服务启动失败")
            log_output, _ = run_ssh_command(ssh, f"cat {REMOTE_DIR}/flask-app/app.log")
            print(f"  日志内容: {log_output}")
            ssh.close()
            return
    
    print("✓ Flask服务已启动")

    print_step(7, 7, "验证服务是否正常运行")
    output, code = run_ssh_command(ssh, f"curl -s http://localhost:{FLASK_PORT}/ -o /dev/null -w '%{{http_code}}' || echo '000'")
    http_code = output.strip()
    
    ssh.close()
    
    if http_code == "200":
        print("✓ 服务验证成功！HTTP状态码: 200")
        print("\n" + "="*50)
        print("  部署完成！")
        print("="*50)
        print(f"项目路径: {REMOTE_DIR}")
        print(f"服务地址: http://{SERVER_IP}:{FLASK_PORT}")
        print(f"虚拟环境: {REMOTE_DIR}/venv")
        print(f"日志文件: {REMOTE_DIR}/flask-app/app.log")
        print("\n管理命令:")
        print(f"  查看日志: tail -f {REMOTE_DIR}/flask-app/app.log")
        print("  停止服务: pkill -f 'python.*app.py'")
        print(f"  重启服务: cd {REMOTE_DIR}/flask-app && nohup {REMOTE_DIR}/venv/bin/python app.py > app.log 2>&1 &")
    else:
        print(f"✗ 服务验证失败！HTTP状态码: {http_code}")
        print("请检查服务日志")

if __name__ == "__main__":
    main()