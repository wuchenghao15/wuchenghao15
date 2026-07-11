import paramiko
import os

SERVER_IP = "192.168.31.105"
SERVER_USER = "wuchenghao15"
SERVER_PASS = "LoginMe.1988$"
PROJECT_DIR = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
REMOTE_DIR = "/home/wuchenghao15/mtscos_project"

def sftp_upload_dir(sftp, local_dir, remote_dir):
    count = 0
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = os.path.join(remote_dir, item)
        if os.path.isdir(local_path):
            try:
                sftp.mkdir(remote_path)
            except IOError:
                pass
            count += sftp_upload_dir(sftp, local_path, remote_path)
        else:
            try:
                sftp.put(local_path, remote_path)
                count += 1
            except Exception as e:
                print(f"  跳过 {item}: {e}")
    return count

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    
    print("正在传输 flask-app 目录...")
    total = sftp_upload_dir(sftp, os.path.join(PROJECT_DIR, "flask-app"), os.path.join(REMOTE_DIR, "flask-app"))
    print(f"传输完成，共 {total} 个文件")
    
    print("正在传输 VERSION 文件...")
    sftp.put(os.path.join(PROJECT_DIR, "VERSION"), os.path.join(REMOTE_DIR, "VERSION"))
    
    print("正在传输 README.md 文件...")
    sftp.put(os.path.join(PROJECT_DIR, "README.md"), os.path.join(REMOTE_DIR, "README.md"))
    
    sftp.close()
    ssh.close()
    print("所有文件传输完成！")

if __name__ == "__main__":
    main()