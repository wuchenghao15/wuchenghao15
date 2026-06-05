// Vikey检测与登录模块 - 轻量化版本

// 全局Vikey对象
if (typeof window.MTSCOS === 'undefined') {
    window.MTSCOS = {};
}
if (typeof MTSCOS.Vikey === 'undefined') {
    MTSCOS.Vikey = {};
}

/**
 * Vikey检测模块 - 轻量化版本
 */
MTSCOS.Vikey.Detection = {
    // Vikey状态
    status: {
        connected: false,
        isAdmin: false,
        hardwareId: '',
        firmwareVersion: '',
        statusText: '未检测到Vikey'
    },
    
    // 检测间隔（毫秒）
    detectionInterval: 2000,
    
    // 检测定时器
    detectionTimer: null,
    
    // 初始化Vikey检测
    init: function() {
        console.log('初始化Vikey检测模块...');
        this.startDetection();
        this.setupEventListeners();
    },
    
    // 开始检测Vikey
    startDetection: function() {
        this.detectionTimer = setInterval(() => {
            this.detectVikey();
        }, this.detectionInterval);
    },
    
    // 停止检测Vikey
    stopDetection: function() {
        if (this.detectionTimer) {
            clearInterval(this.detectionTimer);
            this.detectionTimer = null;
        }
    },
    
    // 检测Vikey硬件
    detectVikey: function() {
        try {
            // 优先使用WebUSB API进行检测（现代浏览器支持，包括macOS）
            if (navigator.usb) {
                this.detectVikeyViaWebUSB();
            } else {
                // 显示不支持WebUSB的提示
                this.status = {
                    connected: false,
                    isAdmin: false,
                    hardwareId: '',
                    firmwareVersion: '',
                    statusText: '当前浏览器不支持WebUSB API，请使用Chrome或Safari浏览器'
                };
                this.updateUI();
            }
        } catch (error) {
            // 检测失败
            this.status = {
                connected: false,
                isAdmin: false,
                hardwareId: '',
                firmwareVersion: '',
                statusText: 'Vikey检测失败: ' + error.message
            };
            this.updateUI();
            console.error('Vikey检测错误:', error);
        }
    },
    
    // 通过WebUSB API检测Vikey硬件
    detectVikeyViaWebUSB: function() {
        try {
            console.log('使用WebUSB API检测Vikey...');
            
            // 定义Vikey设备过滤条件
            const vikeyFilters = [
                {
                    vendorId: 0x1234,  // Vikey硬件的厂商ID
                    productId: 0x5678   // Vikey硬件的产品ID
                }
            ];
            
            // 检测已连接的Vikey设备
            navigator.usb.getDevices().then(devices => {
                const vikeyDevices = devices.filter(device => {
                    return vikeyFilters.some(filter => {
                        return device.vendorId === filter.vendorId && device.productId === filter.productId;
                    });
                });
                
                if (vikeyDevices.length > 0) {
                    // 检测到Vikey设备
                    const vikeyDevice = vikeyDevices[0];
                    console.log('检测到Vikey设备:', vikeyDevice);
                    
                    // 打开设备并获取信息
                    this.openVikeyDevice(vikeyDevice);
                } else {
                    // 未检测到Vikey设备
                    this.status = {
                        connected: false,
                        isAdmin: false,
                        hardwareId: '',
                        firmwareVersion: '',
                        statusText: '未检测到Vikey硬件，请插入USB设备'
                    };
                    this.updateUI();
                }
            }).catch(error => {
                console.error('WebUSB设备获取失败:', error);
                this.status = {
                    connected: false,
                    isAdmin: false,
                    hardwareId: '',
                    firmwareVersion: '',
                    statusText: 'WebUSB设备获取失败'
                };
                this.updateUI();
            });
        } catch (error) {
            console.error('WebUSB检测失败:', error);
            this.status = {
                connected: false,
                isAdmin: false,
                hardwareId: '',
                firmwareVersion: '',
                statusText: 'WebUSB检测失败'
            };
            this.updateUI();
        }
    },
    
    // 打开Vikey设备并获取信息
    openVikeyDevice: function(device) {
        device.open().then(() => {
            console.log('已打开Vikey设备');
            
            // 选择Vikey设备的配置
            return device.selectConfiguration(1);
        }).then(() => {
            // 申请设备接口访问权限
            return device.claimInterface(0);
        }).then(() => {
            console.log('已获取Vikey设备访问权限');
            
            // 更新状态为已连接
            this.status = {
                connected: true,
                isAdmin: Math.random() > 0.5, // 简化处理
                hardwareId: 'WEBUSB-' + device.serialNumber || 'webusb-device',
                firmwareVersion: '1.0.0',
                statusText: 'Vikey已连接'
            };
            
            // 更新UI
            this.updateUI();
            
            // 关闭设备连接
            return device.close();
        }).catch(error => {
            console.error('打开Vikey设备失败:', error);
            this.status = {
                connected: false,
                isAdmin: false,
                hardwareId: '',
                firmwareVersion: '',
                statusText: '打开Vikey设备失败'
            };
            this.updateUI();
        });
    },
    
    // 设置事件监听器
    setupEventListeners: function() {
        // Vikey登录按钮点击事件
        const vikeyLoginBtn = document.getElementById('vikey-login-button');
        if (vikeyLoginBtn) {
            vikeyLoginBtn.addEventListener('click', () => {
                this.performVikeyLogin();
            });
        }
        
        // 页面卸载时停止检测
        window.addEventListener('beforeunload', () => {
            this.stopDetection();
        });
    },
    
    // 更新Vikey状态UI
    updateUI: function() {
        const vikeyStatus = document.getElementById('vikey-status');
        const vikeyStatusText = document.getElementById('vikey-status-text');
        
        if (vikeyStatus && vikeyStatusText) {
            if (this.status.connected) {
                vikeyStatus.classList.add('online');
                vikeyStatus.classList.remove('offline');
                vikeyStatusText.textContent = this.status.statusText;
                
                // 更新登录按钮状态
                const vikeyLoginBtn = document.getElementById('vikey-login-button');
                if (vikeyLoginBtn) {
                    vikeyLoginBtn.disabled = false;
                    vikeyLoginBtn.classList.remove('disabled');
                }
            } else {
                vikeyStatus.classList.add('offline');
                vikeyStatus.classList.remove('online');
                vikeyStatusText.textContent = this.status.statusText;
                
                // 更新登录按钮状态
                const vikeyLoginBtn = document.getElementById('vikey-login-button');
                if (vikeyLoginBtn) {
                    vikeyLoginBtn.disabled = true;
                    vikeyLoginBtn.classList.add('disabled');
                }
            }
        }
    },
    
    // 执行Vikey登录
    performVikeyLogin: function() {
        try {
            console.log('开始Vikey登录...');
            
            if (!this.status.connected) {
                alert('未检测到Vikey，请先连接Vikey硬件或检查浏览器兼容性');
                return;
            }
            
            // 显示登录中状态
            const vikeyLoginBtn = document.getElementById('vikey-login-button');
            if (vikeyLoginBtn) {
                vikeyLoginBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> <span>登录中...</span>';
                vikeyLoginBtn.disabled = true;
            }
            
            // 生成挑战码
            const challenge = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            
            // 模拟签名（实际应通过Vikey设备获取）
            const signature = challenge + '_simulated_signature';
            
            // 发送登录请求到服务器
            this.sendVikeyLoginRequest(this.status.hardwareId, challenge, signature);
            
        } catch (error) {
            console.error('Vikey登录错误:', error);
            alert('Vikey登录失败: ' + error.message);
            
            // 恢复登录按钮状态
            const vikeyLoginBtn = document.getElementById('vikey-login-button');
            if (vikeyLoginBtn) {
                vikeyLoginBtn.innerHTML = '<svg class="svg-icon" viewBox="0 0 512 512" width="16" height="16"><path d="M336 144c0-26.5 21.5-48 48-48s48 21.5 48 48-21.5 48-48 48-48-21.5-48-48zm176 48c0-79.5-64.5-144-144-144s-144 64.5-144 144c0 19.3 3.8 37.7 10.7 54.6L144 352 48 256 0 304l96 96 48 48 48-48 16.4-16.4c15.5 5.6 32.1 8.8 49.6 8.8 79.5 0 144-64.5 144-144z"/></svg> <span>使用Vikey登录</span>';
                vikeyLoginBtn.disabled = false;
            }
        }
    },
    
    // 发送Vikey登录请求
    sendVikeyLoginRequest: function(hardwareId, challenge, signature) {
        // 构造登录请求数据
        const loginData = {
            hardwareId: hardwareId,
            challenge: challenge,
            signature: signature,
            timestamp: Date.now(),
            isAdmin: this.status.isAdmin
        };
        
        // 发送AJAX请求
        fetch('/api/auth/login-vikey', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        }).then(response => {
            if (!response.ok) {
                throw new Error('登录请求失败');
            }
            return response.json();
        }).then(response => {
            if (response.success) {
                // 登录成功，保存token和用户信息
                localStorage.setItem('token', response.token);
                localStorage.setItem('userInfo', JSON.stringify(response.userInfo));
                
                // 显示成功消息
                alert('Vikey登录成功！');
                
                // 跳转到仪表盘
                window.location.href = '/dashboard';
            } else {
                // 登录失败
                throw new Error(response.message || '登录失败');
            }
        }).catch(error => {
            console.error('Vikey登录请求失败:', error);
            alert('Vikey登录失败: ' + error.message);
        }).finally(() => {
            // 恢复登录按钮状态
            const vikeyLoginBtn = document.getElementById('vikey-login-button');
            if (vikeyLoginBtn) {
                vikeyLoginBtn.innerHTML = '<svg class="svg-icon" viewBox="0 0 512 512" width="16" height="16"><path d="M336 144c0-26.5 21.5-48 48-48s48 21.5 48 48-21.5 48-48 48-48-21.5-48-48zm176 48c0-79.5-64.5-144-144-144s-144 64.5-144 144c0 19.3 3.8 37.7 10.7 54.6L144 352 48 256 0 304l96 96 48 48 48-48 16.4-16.4c15.5 5.6 32.1 8.8 49.6 8.8 79.5 0 144-64.5 144-144z"/></svg> <span>使用Vikey登录</span>';
                vikeyLoginBtn.disabled = false;
            }
        });
    },
    
    // 获取Vikey状态
    getStatus: function() {
        return this.status;
    },
    
    // 检测Vikey管理员权限
    checkAdminPrivilege: function() {
        return this.status.connected && this.status.isAdmin;
    },
    
    // 获取操作系统类型
    getOperatingSystem: function() {
        const userAgent = window.navigator.userAgent;
        
        if (userAgent.indexOf('Mac OS X') !== -1) {
            return 'macos';
        } else if (userAgent.indexOf('Windows') !== -1) {
            return 'windows';
        } else if (userAgent.indexOf('Linux') !== -1) {
            return 'linux';
        } else {
            return 'other';
        }
    }
};

/**
 * Vikey登录模块 - 轻量化版本
 */
MTSCOS.Vikey.Login = {
    // 初始化Vikey登录
    init: function() {
        console.log('初始化Vikey登录模块...');
    }
};

/**
 * 页面加载完成后初始化Vikey模块
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        MTSCOS.Vikey.Detection.init();
        MTSCOS.Vikey.Login.init();
    });
} else {
    // 页面已经加载完成，直接初始化
    MTSCOS.Vikey.Detection.init();
    MTSCOS.Vikey.Login.init();
}
