
@echo off
rem MTSCOS AI 服务器防火墙配置脚本
rem 功能: 开放上传项目到172.16.0.196所需要的所有端口

echo 开始配置Windows防火墙...

rem 开放HTTP端口
netsh advfirewall firewall add rule name="MTSCOS HTTP" dir=in action=allow protocol=TCP localport=80
echo ✅ 开放HTTP端口(80)

rem 开放HTTPS端口
netsh advfirewall firewall add rule name="MTSCOS HTTPS" dir=in action=allow protocol=TCP localport=443
echo ✅ 开放HTTPS端口(443)

rem 开放SSH端口
netsh advfirewall firewall add rule name="MTSCOS SSH" dir=in action=allow protocol=TCP localport=22
echo ✅ 开放SSH端口(22)

rem 开放MTSCOS AI服务端口
netsh advfirewall firewall add rule name="MTSCOS AI Service" dir=in action=allow protocol=TCP localport=8081
echo ✅ 开放MTSCOS AI服务端口(8081)

rem 开放FTP端口
netsh advfirewall firewall add rule name="MTSCOS FTP" dir=in action=allow protocol=TCP localport=21
echo ✅ 开放FTP端口(21)

rem 开放SMB文件共享端口
netsh advfirewall firewall add rule name="MTSCOS SMB" dir=in action=allow protocol=TCP localport=445
echo ✅ 开放SMB端口(445)

rem 开放远程桌面端口
netsh advfirewall firewall add rule name="MTSCOS RDP" dir=in action=allow protocol=TCP localport=3389
echo ✅ 开放远程桌面端口(3389)

rem 显示当前防火墙规则
echo.
echo 当前MTSCOS相关防火墙规则:
netsh advfirewall firewall show rule name=all | findstr "MTSCOS"

echo.
echo 配置完成
echo 配置完成端口配置脚本执行完成!

echo 防火墙配置完成!
pause
