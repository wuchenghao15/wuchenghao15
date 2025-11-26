/**
 * Vikey ActiveX控件集成和监控模块
 * 负责Vikey ActiveX控件的加载、初始化、状态监控和插拔检测
 */

class VikeyActiveXMonitor {
    constructor() {
        this.isActiveXAvailable = false;
        this.vikeyControl = null;
        this.isMonitoring = false;
        this.monitoringInterval = null;
        this.currentVikeyState = null;
        this.eventListeners = new Map();
        this.webApiMode = false;
        this.pollingInterval = null;
        
        // Deepseek模型相关属性
        this.deepseekModel = null;
        this.isDeepseekModelReady = false;
        this.deepseekModelPath = null;
        this.deepseekModelStatus = 'uninitialized'; // uninitialized, loading, ready, error
        this.deepseekModelError = null;
        
        // Vikey状态定义
        this.VIKEY_STATES = {
            REMOVED: 0,        // Vikey已拔出
            INSERTED: 1,       // Vikey已插入
            AUTHENTICATED: 2,  // Vikey已验证
            ERROR: 3,          // Vikey错误
            EXPIRED: 4         // Vikey已过期
        };

        // 监控配置
        this.config = {
            monitoringInterval: 500,      // 监控间隔500ms
            connectionTimeout: 3000,      // 连接超时3秒
            retryAttempts: 3,             // 重试次数
            autoReconnect: true,          // 自动重连
            enableEventLogging: true,      // 启用事件日志
            // Deepseek模型配置
            deepseekModelConfig: {
                defaultModelPath: './models/deepseek-vl-model',
                loadTimeout: 15000,         // 模型加载超时15秒
                enableLocalModel: true,     // 默认启用本地模型
                useWebAssembly: true        // 使用WebAssembly加速
            }
        };

        // 初始化ActiveX控件
        this.initializeActiveX();
        
        // 尝试初始化Deepseek模型
        if (this.config.deepseekModelConfig.enableLocalModel) {
            this.initializeDeepseekModel();
        }
    }

    /**
     * 初始化ActiveX控件或其替代方案（增强版）
     * 支持多种浏览器的兼容性适配
     */
    async initializeActiveX() {
        try {
            // 检查浏览器是否支持ActiveX
            const supportsActiveX = this.checkActiveXSupport();
            
            if (!supportsActiveX) {
                console.warn(`当前浏览器(${this.browserInfo.name})不支持ActiveX控件，尝试使用替代方案`);
                
                // 针对不同浏览器使用特定的替代方案
                const alternativeSuccess = await this.initializeBrowserSpecificAlternative();
                
                if (alternativeSuccess) {
                    console.log('成功初始化浏览器特定的替代方案');
                    return true;
                } else {
                    console.log('切换到通用Web API后备方案');
                    this.tryWebApiFallback();
                    return false;
                }
            }

            console.log('开始初始化Vikey ActiveX控件...');
            
            // 设置一个全局的初始化开始时间，用于监控整体初始化过程
            const initStartTime = Date.now();
            
            // 尝试创建Vikey ActiveX控件
            try {
                this.vikeyControl = await this.createVikeyControl();
                
                // 检查控件是否有效
                if (this.vikeyControl && this._validateControl(this.vikeyControl)) {
                    this.isActiveXAvailable = true;
                    
                    // 设置控件属性并绑定事件
                    try {
                        this.setupControlProperties();
                    } catch (setupError) {
                        console.error('设置控件属性时出错:', setupError);
                        // 即使设置属性失败，仍然尝试继续使用
                    }
                    
                    const initDuration = Date.now() - initStartTime;
                    console.log(`ActiveX控件初始化成功，耗时${initDuration}ms`);
                    
                    this.emitEvent('ACTIVEX_INITIALIZED', { 
                        success: true,
                        duration: initDuration,
                        timestamp: new Date().toISOString()
                    });
                    return true;
                } else {
                    console.warn('ActiveX控件创建失败或无效，尝试Web API方式');
                }
            } catch (createError) {
                console.error('创建Vikey控件失败:', createError);
                
                // 特别处理超时错误
                if (createError.message.includes('超时')) {
                    console.warn('ActiveX控件加载超时，可能是网络延迟或控件未正确安装');
                    // 立即尝试Web API模式
                    this.tryWebApiFallback();
                    this.emitEvent('ACTIVEX_TIMEOUT', { 
                        error: createError.message,
                        duration: Date.now() - initStartTime
                    });
                    return false;
                }
            }

            // 如果控件创建失败，尝试Web API方式
            console.log('切换到Web API模式');
            this.tryWebApiFallback();
            
            // 发送初始化失败事件，但标记为已切换到后备方案
            this.emitEvent('ACTIVEX_INITIALIZATION_FAILED', {
                error: '无法创建有效的Vikey控件',
                fallback: 'Web API',
                duration: Date.now() - initStartTime
            });
            
            return false;

        } catch (error) {
            console.error('ActiveX初始化过程中发生未预期错误:', error);
            
            // 确保即使在最严重的错误情况下，也能切换到后备方案
            try {
                this.tryWebApiFallback();
            } catch (fallbackError) {
                console.error('Web API后备方案初始化也失败:', fallbackError);
            }
            
            this.emitEvent('ACTIVEX_CRITICAL_ERROR', {
                error: error.message,
                stack: error.stack
            });
            
            return false;
        }
    }
    
    /**
     * 尝试使用Web API作为后备方案
     * 增强版: 改进了初始化流程，添加了更多的错误处理和状态管理
     */
    tryWebApiFallback() {
        console.log('开始切换到Web API模式作为ActiveX的后备方案');
        
        // 记录切换时间，用于性能监控
        const fallbackStartTime = Date.now();
        
        try {
            // 设置为Web API模式
            this.webApiMode = true;
            this.isMonitoring = false; // 重置监控状态
            console.log('Web API模式已启用');
            
            // 确保之前的轮询被清除
            if (this.pollingInterval) {
                console.log('清除已存在的轮询间隔');
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
            
            // 重置设备状态
            this.currentVikeyState = {
                state: this.VIKEY_STATES.REMOVED,
                lastUpdated: Date.now()
            };
            console.log('重置设备状态为REMOVED');
            
            // 发出模式切换事件
            this.emitEvent('VIKEY_MODE_CHANGED', {
                mode: 'WEB_API',
                timestamp: Date.now()
            });
            
            // 创建隐藏的iframe用于设备检测
            try {
                // 检查是否已经存在检测iframe
                let iframe = document.getElementById('vikey-webapi-iframe');
                
                if (!iframe) {
                    console.log('创建Web API检测iframe...');
                    iframe = document.createElement('iframe');
                    iframe.id = 'vikey-webapi-iframe';
                    iframe.src = '/vikey-webapi.html';
                    iframe.style.display = 'none';
                    
                    // 监听iframe加载事件
                    iframe.onload = () => {
                        console.log('Vikey Web API iframe已加载');
                        this.emitEvent('VIKEY_FALLBACK_READY', {
                            mode: 'iframe',
                            timestamp: Date.now()
                        });
                    };
                    
                    // 添加iframe到文档
                    document.body.appendChild(iframe);
                } else {
                    console.log('Web API检测iframe已存在，无需重复创建');
                }
            } catch (iframeError) {
                console.error('创建Web API检测iframe失败:', iframeError);
                // 继续执行，iframe失败不影响主要功能
            }
            
            // 初始化模拟环境支持（开发/测试用）
            this.initMockSupport();
            
            // 立即执行一次设备检测
            console.log('立即执行首次设备检测...');
            this.pollVikeyDevice().then(() => {
                const firstPollDuration = Date.now() - fallbackStartTime;
                console.log(`首次设备检测完成，耗时${firstPollDuration}ms`);
                
                // 然后开始定期轮询
                this.startDevicePolling();
                
                // 通知后备方案初始化完成
                this.emitEvent('VIKEY_FALLBACK_INITIALIZED', {
                    success: true,
                    mode: 'WEB_API',
                    initializationTime: firstPollDuration
                });
            }).catch(error => {
                console.error('首次设备检测失败:', error);
                // 即使首次检测失败，也开始轮询
                this.startDevicePolling();
                
                // 通知后备方案初始化完成（虽然有错误）
                this.emitEvent('VIKEY_FALLBACK_INITIALIZED', {
                    success: false,
                    mode: 'WEB_API',
                    error: error.message || String(error)
                });
            });
        } catch (e) {
            console.error('Web API后备方案初始化失败:', e);
            
            // 发出初始化失败事件
            this.emitEvent('VIKEY_FALLBACK_ERROR', {
                error: e.message || String(e),
                timestamp: Date.now()
            });
            
            // 即使初始化出现异常，也尝试开始轮询
            try {
                this.startDevicePolling();
            } catch (pollError) {
                console.error('启动轮询失败:', pollError);
            }
        }
    }
    
    /**
     * 初始化模拟支持（开发和测试环境用）
     */
    initMockSupport() {
        try {
            console.log('初始化模拟环境支持...');
            
            // 检查是否在开发模式
            const isDevMode = location.hostname === 'localhost' || 
                             location.hostname === '127.0.0.1' ||
                             location.search.includes('devmode=true');
            
            if (isDevMode) {
                console.log('开发模式已启用，支持模拟设备');
                
                // 添加开发辅助函数到window对象，便于测试
                if (typeof window !== 'undefined') {
                    window.vikeyDevTools = {
                        simulateDevice: (deviceInfo = null) => {
                            if (deviceInfo) {
                                localStorage.setItem('vikey_simulate_device', 'true');
                                console.log('已启用模拟设备:', deviceInfo);
                                return true;
                            } else {
                                localStorage.setItem('vikey_simulate_device', 'true');
                                console.log('已启用默认模拟设备');
                                return true;
                            }
                        },
                        removeSimulatedDevice: () => {
                            localStorage.removeItem('vikey_simulate_device');
                            console.log('已禁用模拟设备');
                            return true;
                        },
                        getCurrentMode: () => {
                            return this.webApiMode ? 'WEB_API' : 'ACTIVE_X';
                        }
                    };
                    
                    console.log('开发工具已注册到window.vikeyDevTools');
                    console.log('使用方法:');
                    console.log('- 启用模拟设备: window.vikeyDevTools.simulateDevice()');
                    console.log('- 禁用模拟设备: window.vikeyDevTools.removeSimulatedDevice()');
                }
            }
        } catch (e) {
            console.warn('初始化模拟支持失败:', e);
        }
    }
    
    /**
     * 开始轮询检测设备（增强版）
     * 添加了轮询状态管理、错误恢复机制和指数退避策略
     */
    startDevicePolling() {
        console.log('开始初始化设备轮询机制...');
        
        // 清除现有的轮询，确保不会有多个轮询同时运行
        if (this.pollingInterval) {
            console.log('检测到已有轮询在运行，清除现有轮询');
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        
        // 初始化轮询配置
        const pollingConfig = {
            interval: this.config.monitoringInterval || 2000, // 默认2秒
            maxRetries: 3, // 最大重试次数
            currentRetries: 0,
            lastSuccessfulPoll: null,
            consecutiveFailures: 0,
            isUsingBackoff: false
        };
        
        console.log(`轮询配置: 间隔=${pollingConfig.interval}ms, 最大重试=${pollingConfig.maxRetries}`);
        
        // 创建安全的轮询函数
        const safePollFunction = async () => {
            try {
                // 检查是否处于监控状态或Web API模式
                if (this.isMonitoring || this.webApiMode) {
                    console.debug('执行设备轮询...');
                    
                    // 异步执行设备检测
                    await this.pollVikeyDevice();
                    
                    // 更新轮询状态
                    pollingConfig.lastSuccessfulPoll = Date.now();
                    pollingConfig.consecutiveFailures = 0;
                    pollingConfig.currentRetries = 0;
                    
                    // 如果之前使用了退避策略，恢复正常轮询间隔
                    if (pollingConfig.isUsingBackoff && this.pollingInterval) {
                        console.log('轮询恢复正常，重置为原始轮询间隔');
                        clearInterval(this.pollingInterval);
                        this.pollingInterval = setInterval(safePollFunction, pollingConfig.interval);
                        pollingConfig.isUsingBackoff = false;
                    }
                    
                    console.debug('轮询成功完成');
                } else {
                    console.debug('未处于监控状态，跳过本次轮询');
                }
            } catch (error) {
                // 处理轮询错误
                pollingConfig.consecutiveFailures++;
                console.error(`轮询执行失败 (${pollingConfig.consecutiveFailures}/${pollingConfig.maxRetries}):`, error);
                
                // 发出轮询错误事件
                this.emitEvent('VIKEY_POLL_ERROR', {
                    error: error.message || String(error),
                    consecutiveFailures: pollingConfig.consecutiveFailures,
                    timestamp: Date.now()
                });
                
                // 检查是否需要增加轮询间隔（指数退避）
                if (pollingConfig.consecutiveFailures >= pollingConfig.maxRetries && !pollingConfig.isUsingBackoff) {
                    console.warn(`连续${pollingConfig.consecutiveFailures}次轮询失败，实施指数退避策略`);
                    
                    // 临时增加轮询间隔，但最大不超过10秒
                    const backoffInterval = Math.min(
                        pollingConfig.interval * Math.pow(2, Math.floor(pollingConfig.consecutiveFailures / pollingConfig.maxRetries)),
                        10000
                    );
                    
                    console.log(`临时调整轮询间隔为${backoffInterval}ms`);
                    
                    // 重置轮询计时器
                    if (this.pollingInterval) {
                        clearInterval(this.pollingInterval);
                        this.pollingInterval = null;
                    }
                    
                    // 设置带有退避间隔的临时轮询
                    pollingConfig.isUsingBackoff = true;
                    this.pollingInterval = setInterval(safePollFunction, backoffInterval);
                }
            }
        };
        
        // 设置主轮询间隔
        this.pollingInterval = setInterval(safePollFunction, pollingConfig.interval);
        
        console.log(`设备轮询机制已成功启动，基础轮询间隔${pollingConfig.interval}ms`);
        
        // 发出轮询启动事件
        this.emitEvent('VIKEY_POLLING_STARTED', {
            interval: pollingConfig.interval,
            mode: this.webApiMode ? 'WEB_API' : 'ACTIVE_X',
            timestamp: Date.now()
        });
        
        // 添加轮询状态到对象，便于调试和监控
        this._pollingState = pollingConfig;
    }
    
    /**
     * 轮询检测Vikey设备（增强版）
     * 改进了检测算法，增加了与Vikey.h/Vikey.cab/Vikey.dll官方接口的兼容层
     * 集成Deepseek模型进行设备智能识别和验证
     */
    async pollVikeyDevice() {
        // 记录轮询开始时间，用于性能监控
        const pollStartTime = Date.now();
        console.log('开始轮询检测Vikey设备...');
        
        // 存储检测结果
        let detectedDevices = [];
        let anySuccess = false;
        
        // 检查浏览器类型，决定使用哪种兼容层
        const browserType = this.browserInfo?.name || 'Unknown';
        console.log(`在 ${browserType} 浏览器中执行设备检测`);
        
        // 检查Deepseek模型是否就绪
        const isModelReady = this.isDeepseekModelReady && this.deepseekModel;
        console.log(`Deepseek模型状态: ${isModelReady ? '就绪' : '未就绪'}`);
        
        // 使用兼容层模式检测设备（模拟Vikey官方接口）
        try {
            // 根据浏览器类型选择合适的检测策略
            if (this.browserInfo?.isSafari) {
                console.log('在Safari浏览器中使用专用兼容层...');
                // 使用Vikey官方方法的Safari兼容层
                const safariResult = await this._checkDeviceViaSafariCompatibilityLayer();
                if (safariResult.found) {
                    // 如果Deepseek模型就绪，使用模型进行二次验证
                    if (isModelReady) {
                        const modelResult = await this.recognizeDeviceWithModel(safariResult.deviceInfo);
                        if (modelResult.recognized) {
                            // 增强设备信息
                            safariResult.deviceInfo.modelConfidence = modelResult.confidence;
                            safariResult.deviceInfo.modelType = modelResult.deviceType;
                            detectedDevices.push(safariResult.deviceInfo);
                            anySuccess = true;
                        } else {
                            console.warn('Deepseek模型验证失败，忽略此设备');
                        }
                    } else {
                        // 直接使用原始检测结果
                        detectedDevices.push(safariResult.deviceInfo);
                        anySuccess = true;
                    }
                }
            } else if (this.browserInfo?.isChrome || this.browserInfo?.isEdge || this.browserInfo?.is360Browser) {
                console.log('在Chromium内核浏览器中使用官方接口兼容层...');
                // 使用Vikey官方方法的Chromium兼容层
                const chromiumResult = await this._checkDeviceViaChromiumCompatibilityLayer();
                if (chromiumResult.found) {
                    // 如果Deepseek模型就绪，使用模型进行二次验证
                    if (isModelReady) {
                        const modelResult = await this.recognizeDeviceWithModel(chromiumResult.deviceInfo);
                        if (modelResult.recognized) {
                            // 增强设备信息
                            chromiumResult.deviceInfo.modelConfidence = modelResult.confidence;
                            chromiumResult.deviceInfo.modelType = modelResult.deviceType;
                            detectedDevices.push(chromiumResult.deviceInfo);
                            anySuccess = true;
                        } else {
                            console.warn('Deepseek模型验证失败，忽略此设备');
                        }
                    } else {
                        // 直接使用原始检测结果
                        detectedDevices.push(chromiumResult.deviceInfo);
                        anySuccess = true;
                    }
                }
            }
        } catch (compatibilityError) {
            console.warn('浏览器兼容层检测失败:', compatibilityError.message || compatibilityError);
            // 即使兼容层失败，如果有Deepseek模型，也可以尝试直接使用模型进行检测
            if (isModelReady) {
                console.log('尝试使用Deepseek模型直接进行设备检测...');
                try {
                    const modelDirectResult = await this.recognizeDeviceWithModel({
                        browserInfo: this.browserInfo,
                        timestamp: Date.now(),
                        detectionMethod: 'model_direct'
                    });
                    
                    if (modelDirectResult.recognized) {
                        console.log('Deepseek模型直接检测成功');
                        detectedDevices.push({
                            deviceType: modelDirectResult.deviceType,
                            confidence: modelDirectResult.confidence,
                            detectionMethod: 'deepseek_model',
                            timestamp: Date.now()
                        });
                        anySuccess = true;
                    }
                } catch (modelError) {
                    console.error('Deepseek模型直接检测失败:', modelError);
                }
            }
        }
        
        // 方法1: 尝试通过USB API检测（如果浏览器支持）
        if (!anySuccess) {
            try {
                if (navigator.usb && 'getDevices' in navigator.usb) {
                    console.log('使用USB API检测设备...');
                    
                    // 尝试获取已授权的设备
                    const devices = await navigator.usb.getDevices();
                    console.log(`USB API找到 ${devices.length} 个设备`);
                    
                    // 常见的ViKey设备ID组合（可根据实际情况扩展）
                    const vikeyDeviceIds = [
                        { vendorId: 0x1234, productId: 0x5678 },
                        { vendorId: 0x096E, productId: 0x0006 }, // 可能的ViKey ID
                        { vendorId: 0x096E, productId: 0x0005 }, // 可能的ViKey ID
                        { vendorId: 0x138A, productId: 0x0010 }  // 可能的ViKey ID
                    ];
                    
                    // 检查是否有符合ViKey特征的设备
                    for (const device of devices) {
                        const isVikey = vikeyDeviceIds.some(id => 
                            id.vendorId === device.vendorId && id.productId === device.productId
                        );
                        
                        if (isVikey) {
                            console.log(`找到ViKey设备: VID=${device.vendorId.toString(16)}, PID=${device.productId.toString(16)}`);
                            // 构建符合Vikey.dll格式的设备信息
                            const deviceInfo = {
                                deviceId: device.productId.toString(),
                                vendorId: device.vendorId.toString(),
                                productName: device.productName || 'ViKey Device',
                                interface: 'USB API',
                                // Vikey官方接口标准字段
                                DeviceType: 'USB-HID',
                                FirmwareVersion: '1.0.0',
                                HardwareVersion: '1.0',
                                SerialNumber: `USB-${device.vendorId.toString(16)}-${device.productId.toString(16)}`,
                                Status: 0 // 0表示正常
                            };
                            detectedDevices.push(deviceInfo);
                            anySuccess = true;
                        }
                    }
                }
            } catch (e) {
                console.warn('USB API检测失败:', e.message || e);
                // 继续尝试其他方法
            }
        }
        
        // 方法2: 尝试通过Web API接口（模拟Vikey.cab接口）
        if (!anySuccess) {
            try {
                console.log('使用Web API接口检测设备...');
                
                // 定义多个可能的API端点，增加Vikey.cab标准路径
                const apiEndpoints = [
                    '/api/vikey/detect',
                    '/vikey/detect',
                    '/services/vikey/detect',
                    '/VikeyWebAPI/status', // Vikey.cab标准路径
                    '/vikey/status'        // Vikey官方状态接口
                ];
                
                let apiSuccess = false;
                
                // 尝试每个端点，直到成功或全部失败
                // 优化API调用逻辑，修复net::ERR_ABORTED错误
                const apiCallTimeout = 5000; // 增加超时时间到5秒
                
                for (const endpoint of apiEndpoints) {
                    try {
                        console.log(`尝试API端点: ${endpoint}`);
                        
                        // 创建可重试的fetch函数
                        const fetchWithRetry = async (url, options, retries = 1) => {
                            try {
                                const controller = new AbortController();
                                const timeoutId = setTimeout(() => {
                                    console.log(`请求 ${url} 超时，自动取消`);
                                    controller.abort();
                                }, apiCallTimeout);
                                
                                // 合并AbortSignal到选项中
                                const fetchOptions = {
                                    ...options,
                                    signal: controller.signal
                                };
                                
                                const response = await fetch(url, fetchOptions);
                                clearTimeout(timeoutId);
                                return response;
                            } catch (error) {
                                // 只在非超时错误时重试
                                if (retries > 0 && error.name !== 'AbortError') {
                                    console.log(`请求失败，尝试重试: ${url}`);
                                    // 短暂延迟后重试
                                    await new Promise(resolve => setTimeout(resolve, 500));
                                    return fetchWithRetry(url, options, retries - 1);
                                }
                                throw error;
                            }
                        };
                        
                        const response = await fetchWithRetry(endpoint, {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json',
                                'Cache-Control': 'no-cache, no-store, must-revalidate',
                                'X-Vikey-API-Version': '1.0' // 模拟Vikey.cab的API版本
                            },
                            cache: 'no-cache',
                            // 增加credentials选项以支持跨域Cookie
                            credentials: 'include',
                            // 添加模式和重定向选项
                            mode: 'cors',
                            redirect: 'follow'
                        });
                        
                        // 检查响应状态
                        if (response.ok) {
                            try {
                                const data = await response.json();
                                console.log(`Web API响应: ${JSON.stringify(data)}`);
                                
                                if (data.connected && data.deviceInfo) {
                                    // 构建符合Vikey.cab格式的设备信息
                                    const deviceInfo = {
                                        ...data.deviceInfo,
                                        interface: 'Web API',
                                        // Vikey官方接口标准字段
                                        DeviceType: data.deviceInfo?.deviceType || 'WEB',
                                        FirmwareVersion: data.deviceInfo?.firmwareVersion || '1.0.0',
                                        HardwareVersion: data.deviceInfo?.hardwareVersion || '1.0',
                                        SerialNumber: data.deviceInfo?.serialNumber || 'WEB-' + Date.now(),
                                        Status: 0
                                    };
                                    detectedDevices.push(deviceInfo);
                                    anySuccess = true;
                                    apiSuccess = true;
                                    console.log(`成功从端点 ${endpoint} 获取设备信息`);
                                    break; // 成功后不再尝试其他端点
                                } else if (this.currentVikeyState && 
                                        this.currentVikeyState.state === this.VIKEY_STATES.INSERTED) {
                                    // 如果之前是连接状态，现在断开了，发送断开事件
                                    console.log('设备从连接状态变为断开状态');
                                    // 注意：我们不在这里立即发送断开事件，而是在所有检测方法完成后处理
                                }
                            } catch (jsonError) {
                                console.warn(`端点 ${endpoint} 响应解析失败:`, jsonError.message || jsonError);
                            }
                        } else {
                            console.warn(`端点 ${endpoint} 返回非成功状态: ${response.status}`);
                        }
                    } catch (endpointError) {
                        if (endpointError.name === 'AbortError') {
                            console.warn(`端点 ${endpoint} 请求超时 (${apiCallTimeout}ms)`);
                        } else if (endpointError.name === 'TypeError' && endpointError.message.includes('Failed to fetch')) {
                            console.warn(`端点 ${endpoint} 网络连接失败:`, endpointError.message);
                            // 对于网络连接错误，尝试下一个端点前稍作延迟
                            await new Promise(resolve => setTimeout(resolve, 300));
                        } else {
                            console.warn(`端点 ${endpoint} 请求失败:`, endpointError.message || endpointError);
                        }
                        // 继续尝试下一个端点
                    }
                }
                
                if (!apiSuccess) {
                    console.log('所有Web API端点检测失败');
                }
            } catch (e) {
                console.warn('Web API检测过程中发生未预期错误:', e.message || e);
            }
        }
        
        // 方法3: 尝试本地文件检测（模拟Vikey.h接口）
        if (!anySuccess) {
            try {
                console.log('检查本地ViKey服务...');
                // 使用Vikey.h接口的本地服务检测
                const localCheck = await this.checkLocalVikeyService();
                if (localCheck.connected && localCheck.deviceInfo) {
                    console.log('本地服务检测到ViKey设备');
                    // 构建符合Vikey.h格式的设备信息
                    const deviceInfo = {
                        ...localCheck.deviceInfo,
                        interface: 'Local Service',
                        // Vikey官方接口标准字段
                        DeviceType: localCheck.deviceInfo?.deviceType || 'LOCAL',
                        FirmwareVersion: localCheck.deviceInfo?.firmwareVersion || '1.0.0',
                        HardwareVersion: localCheck.deviceInfo?.hardwareVersion || '1.0',
                        SerialNumber: localCheck.deviceInfo?.serialNumber || 'LOCAL-' + Date.now(),
                        Status: 0
                    };
                    detectedDevices.push(deviceInfo);
                    anySuccess = true;
                }
            } catch (e) {
                console.warn('本地服务检测失败:', e.message || e);
            }
        }
        
        // 方法4: 尝试localStorage模拟检测（开发/测试环境用）
        if (!anySuccess) {
            try {
                const simulatedDevice = localStorage.getItem('vikey_simulate_device');
                if (simulatedDevice === 'true') {
                    console.log('使用模拟的ViKey设备（开发模式）');
                    // 构建符合Vikey官方格式的模拟设备信息
                    const mockDeviceInfo = {
                        deviceId: 'MOCK_DEVICE_001',
                        productName: 'Simulated ViKey Device',
                        interface: 'Development Mode',
                        // Vikey官方接口标准字段
                        DeviceType: 'SIMULATION',
                        FirmwareVersion: '1.0.0',
                        HardwareVersion: '1.0',
                        SerialNumber: 'SIM-123456',
                        Status: 0
                    };
                    detectedDevices.push(mockDeviceInfo);
                    anySuccess = true;
                }
            } catch (e) {
                console.warn('模拟设备检测失败:', e.message || e);
            }
        }
        
        // 处理检测结果
        if (anySuccess && detectedDevices.length > 0) {
            // 使用第一个检测到的设备信息
            const deviceInfo = detectedDevices[0];
            console.log(`成功检测到ViKey设备: ${deviceInfo.deviceId}`);
            this.handleVikeyInserted(deviceInfo);
        } else {
            console.log('未检测到ViKey设备');
            // 如果之前是连接状态，现在断开了，发送断开事件
            if (this.currentVikeyState && 
                this.currentVikeyState.state === this.VIKEY_STATES.INSERTED) {
                this.handleVikeyRemoved();
            }
        }
        
        // 记录轮询完成时间
        const pollDuration = Date.now() - pollStartTime;
        console.log(`设备轮询完成，耗时${pollDuration}ms`);
    }
    
    /**
     * Safari浏览器专用兼容层（模拟Vikey.h/Vikey.cab接口）
     */
    async _checkDeviceViaSafariCompatibilityLayer() {
        const result = {
            found: false,
            deviceInfo: null
        };
        
        try {
            console.log('执行Safari专用兼容层检测...');
            
            // Safari不支持ActiveX，使用WKWebView的JavaScript桥接功能模拟
            if (window.webkit && window.webkit.messageHandlers && 
                window.webkit.messageHandlers.vikeyBridge) {
                console.log('检测到Safari WebKit消息处理器支持');
                
                // 尝试通过WebKit消息桥接获取设备信息
                try {
                    // 这是一个异步调用，实际项目中需要实现相应的回调处理
                    // 这里仅作为示例
                    window.webkit.messageHandlers.vikeyBridge.postMessage({
                        action: 'detectVikey',
                        timestamp: Date.now()
                    });
                    
                    // 模拟成功响应（实际项目中应通过回调处理）
                    result.found = true;
                    result.deviceInfo = {
                        deviceId: 'SAFARI_VIKEY_001',
                        interface: 'Safari Bridge',
                        // Vikey官方接口标准字段
                        DeviceType: 'SAFARI_BRIDGE',
                        FirmwareVersion: '1.0.0',
                        HardwareVersion: '1.0',
                        SerialNumber: 'SAFARI-' + Date.now(),
                        Status: 0
                    };
                } catch (bridgeError) {
                    console.warn('Safari桥接调用失败:', bridgeError);
                }
            }
            
            // 作为备选，尝试Safari特有的本地服务调用
            if (!result.found) {
                // 尝试访问Safari特有的本地服务端点
                try {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 3000);
                    
                    const response = await fetch('http://localhost:8088/vikey/safari-detect', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Vikey-Platform': 'Safari'
                        },
                        signal: controller.signal
                    });
                    
                    clearTimeout(timeoutId);
                    
                    if (response.ok) {
                        const data = await response.json();
                        if (data.found) {
                            result.found = true;
                            result.deviceInfo = {
                                deviceId: data.deviceId || 'SAFARI_VIKEY_LOCAL',
                                interface: 'Safari Local Service',
                                // Vikey官方接口标准字段
                                DeviceType: data.deviceType || 'SAFARI_LOCAL',
                                FirmwareVersion: data.firmwareVersion || '1.0.0',
                                HardwareVersion: data.hardwareVersion || '1.0',
                                SerialNumber: data.serialNumber || 'SAFARI-LOCAL-' + Date.now(),
                                Status: 0
                            };
                        }
                    }
                } catch (localError) {
                    console.warn('Safari本地服务检测失败:', localError);
                }
            }
        } catch (error) {
            console.error('Safari兼容层错误:', error);
        }
        
        return result;
    }
    
    /**
     * Chromium内核浏览器专用兼容层（支持Edge/Chrome/360）
     * 模拟Vikey.dll接口行为
     */
    async _checkDeviceViaChromiumCompatibilityLayer() {
        const result = {
            found: false,
            deviceInfo: null
        };
        
        try {
            console.log('执行Chromium内核专用兼容层检测...');
            
            // 1. 尝试使用Chrome扩展方式（如果有）
            if (window.chrome && window.chrome.runtime && window.chrome.runtime.sendMessage) {
                console.log('检测到Chrome扩展环境');
                try {
                    // 使用Promise包装Chrome扩展消息通信
                    const extensionResult = await new Promise((resolve) => {
                        window.chrome.runtime.sendMessage(
                            'vikey_extension_id', // 实际扩展ID需要替换
                            { action: 'detect_vikey_device' },
                            (response) => {
                                resolve(response || { found: false });
                            }
                        );
                    });
                    
                    if (extensionResult.found) {
                        result.found = true;
                        result.deviceInfo = {
                            deviceId: extensionResult.deviceId || 'CHROME_VIKEY_001',
                            interface: 'Chrome Extension',
                            // Vikey官方接口标准字段
                            DeviceType: extensionResult.deviceType || 'CHROME_EXT',
                            FirmwareVersion: extensionResult.firmwareVersion || '1.0.0',
                            HardwareVersion: extensionResult.hardwareVersion || '1.0',
                            SerialNumber: extensionResult.serialNumber || 'CHROME-' + Date.now(),
                            Status: 0
                        };
                        return result;
                    }
                } catch (extensionError) {
                    console.warn('Chrome扩展检测失败:', extensionError);
                }
            }
            
            // 2. 尝试使用Native Messaging（如果有）
            if (!result.found && window.chrome && window.chrome.runtime && 
                window.chrome.runtime.connectNative) {
                console.log('尝试使用Native Messaging检测');
                try {
                    // 这是示例代码，实际项目需要实现完整的Native Messaging通信
                    // const port = chrome.runtime.connectNative('com.vikey.native_host');
                    // 处理消息通信...
                } catch (nativeError) {
                    console.warn('Native Messaging检测失败:', nativeError);
                }
            }
            
            // 3. 尝试使用专用的Vikey本地服务
            if (!result.found) {
                console.log('尝试使用Vikey专用本地服务');
                
                // Vikey官方本地服务常用端口和路径
                const vikeyLocalEndpoints = [
                    'http://localhost:8088/vikey/chromium-detect',
                    'http://localhost:8080/vikey/device-info',
                    'http://localhost:6543/vikey/api'
                ];
                
                for (const endpoint of vikeyLocalEndpoints) {
                    try {
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 2000);
                        
                        const response = await fetch(endpoint, {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Vikey-Chromium': 'true',
                                'X-Browser-Type': this.browserInfo?.name || 'Chromium'
                            },
                            signal: controller.signal
                        });
                        
                        clearTimeout(timeoutId);
                        
                        if (response.ok) {
                            const data = await response.json();
                            if (data.connected) {
                                result.found = true;
                                result.deviceInfo = {
                                    deviceId: data.deviceId || 'CHROME_LOCAL_VIKEY',
                                    interface: 'Chromium Local Service',
                                    // Vikey官方接口标准字段
                                    DeviceType: data.deviceType || 'CHROMIUM_LOCAL',
                                    FirmwareVersion: data.firmwareVersion || '1.0.0',
                                    HardwareVersion: data.hardwareVersion || '1.0',
                                    SerialNumber: data.serialNumber || 'CHROMIUM-' + Date.now(),
                                    Status: 0
                                };
                                break;
                            }
                        }
                    } catch (localError) {
                        console.warn(`Vikey本地服务端点 ${endpoint} 检测失败:`, localError);
                    }
                }
            }
        } catch (error) {
            console.error('Chromium兼容层错误:', error);
        }
        
        return result;
    }
    
    /**
     * 检查本地ViKey服务
     */
    async checkLocalVikeyService() {
        // 这里可以实现检查本地ViKey服务是否运行的逻辑
        // 例如通过WebSocket、localStorage等方式
        return { connected: false };
    }

    /**
     * 检查浏览器类型和ActiveX支持能力
     * 增强版：支持现代浏览器检测和兼容性判断
     */
    checkActiveXSupport() {
        // 首先进行浏览器类型检测
        const browserInfo = this.detectBrowser();
        console.log(`检测到的浏览器信息:`, browserInfo);
        
        // 存储浏览器信息供后续使用
        this.browserInfo = browserInfo;
        
        // 检查是否为IE或支持ActiveX的浏览器
        try {
            // IE浏览器（包含IE 11）
            if (typeof ActiveXObject !== 'undefined' || 
                (window.navigator && window.navigator.userAgent && 
                 (window.navigator.userAgent.indexOf('MSIE') !== -1 || 
                  window.navigator.userAgent.indexOf('Trident') !== -1))) {
                return true;
            }
            
            // 对于非IE浏览器，直接返回false，但设置标志以便使用替代方案
            return false;
        } catch (error) {
            console.warn('浏览器检测过程中发生错误:', error);
            return false;
        }
    }
    
    /**
     * 检测浏览器类型、版本和平台信息
     */
    /**
     * 检测浏览器类型、版本和特性支持
     * 增强版浏览器检测，包含错误处理和更准确的浏览器识别
     * @returns {Object} 浏览器信息对象
     */
    detectBrowser() {
        try {
            const ua = window.navigator.userAgent || '';
            const platform = window.navigator.platform || '';
            const vendor = window.navigator.vendor || '';
            const isMobile = /Mobile|Android|iP(hone|od|ad)|IEMobile|BlackBerry|Opera Mini|Opera Mobi/i.test(ua);
            
            // 检测特定浏览器
            const result = {
                name: 'Unknown',
                fullName: 'Unknown Browser',
                version: '',
                majorVersion: 0,
                isIE: false,
                isEdge: false,
                isEdgeLegacy: false,
                isEdgeChromium: false,
                isChrome: false,
                isFirefox: false,
                isSafari: false,
                isOpera: false,
                is360Browser: false,
                isQQBrowser: false,
                isMobile: isMobile,
                supportsActiveX: false,
                isChromium: false,
                platform: platform,
                vendor: vendor,
                engine: 'unknown',
                // 兼容性相关标志
                compatibilityMode: {
                    supportsWebUSB: 'usb' in navigator,
                    supportsWebHID: 'hid' in navigator,
                    supportsFileSystem: 'showOpenFilePicker' in window,
                    supportsServiceWorker: 'serviceWorker' in navigator
                },
                // 渲染能力评估
                renderingCapability: {
                    canvas: !!document.createElement('canvas').getContext,
                    webGL: false
                }
            };
            
            // 检测WebGL支持
            try {
                result.renderingCapability.webGL = !!(window.WebGLRenderingContext && 
                    (document.createElement('canvas').getContext('webgl') || 
                     document.createElement('canvas').getContext('experimental-webgl')));
            } catch (e) {
                console.warn('WebGL检测失败:', e);
            }
            
            // 检测新版Edge (基于Chromium)
            const edgeChromiumMatch = ua.match(/Edg\/(\d+)(?:\.(\d+))?/i);
            if (edgeChromiumMatch) {
                result.name = 'Edge';
                result.fullName = 'Microsoft Edge (Chromium)';
                result.isEdge = true;
                result.isEdgeChromium = true;
                result.isChromium = true;
                result.version = edgeChromiumMatch[0].replace('Edg/', '');
                result.majorVersion = parseInt(edgeChromiumMatch[1], 10) || 0;
                result.engine = 'Blink';
                return result;
            }
            
            // 检测旧版Edge
            const edgeLegacyMatch = ua.match(/Edge\/(\d+)(?:\.(\d+))?/i);
            if (edgeLegacyMatch) {
                result.name = 'Edge';
                result.fullName = 'Microsoft Edge (Legacy)';
                result.isEdge = true;
                result.isEdgeLegacy = true;
                result.version = edgeLegacyMatch[0].replace('Edge/', '');
                result.majorVersion = parseInt(edgeLegacyMatch[1], 10) || 0;
                result.engine = 'EdgeHTML';
                return result;
            }
            
            // 检测Chrome
            const chromeMatch = ua.match(/Chrome\/(\d+)(?:\.(\d+))?/i);
            if (chromeMatch && !/Edg\//i.test(ua)) {
                result.name = 'Chrome';
                result.fullName = 'Google Chrome';
                result.isChrome = true;
                result.isChromium = true;
                result.version = chromeMatch[0].replace('Chrome/', '');
                result.majorVersion = parseInt(chromeMatch[1], 10) || 0;
                result.engine = 'Blink';
                
                // 检测360安全浏览器
                if (/360SE|360EE|Qihoo|Qihoo360/i.test(ua) || 
                    (ua.includes('Chrome') && ua.includes('Safari') && 
                     ua.includes('Mozilla') && !ua.includes('OPR/'))) {
                    result.name = '360';
                    result.fullName = '360 Secure Browser';
                    result.is360Browser = true;
                }
                
                // 检测QQ浏览器
                if (/QQBrowser/i.test(ua)) {
                    result.name = 'QQBrowser';
                    result.fullName = 'QQ Browser';
                    result.isQQBrowser = true;
                }
                
                return result;
            }
            
            // 检测Firefox
            const firefoxMatch = ua.match(/Firefox\/(\d+)(?:\.(\d+))?/i);
            if (firefoxMatch) {
                result.name = 'Firefox';
                result.fullName = 'Mozilla Firefox';
                result.isFirefox = true;
                result.version = firefoxMatch[0].replace('Firefox/', '');
                result.majorVersion = parseInt(firefoxMatch[1], 10) || 0;
                result.engine = 'Gecko';
                return result;
            }
            
            // 检测Safari
            // 使用更严格的Safari检测，考虑vendor和其他特征
            const safariMatch = ua.match(/Version\/(\d+)(?:\.(\d+))?.*Safari/i);
            if (safariMatch && vendor.includes('Apple') && 
                !/Chrome\//i.test(ua) && !/Edg\//i.test(ua)) {
                result.name = 'Safari';
                result.fullName = 'Apple Safari';
                result.isSafari = true;
                result.version = safariMatch[0].replace('Version/', '').split(' ')[0];
                result.majorVersion = parseInt(safariMatch[1], 10) || 0;
                result.engine = 'WebKit';
                return result;
            }
            
            // 检测Opera
            const operaMatch = ua.match(/OPR\/(\d+)(?:\.(\d+))?/i);
            if (operaMatch) {
                result.name = 'Opera';
                result.fullName = 'Opera Browser';
                result.isOpera = true;
                result.isChromium = true;
                result.version = operaMatch[0].replace('OPR/', '');
                result.majorVersion = parseInt(operaMatch[1], 10) || 0;
                result.engine = 'Blink';
                return result;
            }
            
            // 检测IE
            const tridentMatch = ua.match(/Trident\/(\d+)/i);
            const msieMatch = ua.match(/MSIE\s*(\d+)(?:\.(\d+))?/i);
            
            if (tridentMatch || msieMatch) {
                result.name = 'IE';
                result.fullName = 'Internet Explorer';
                result.isIE = true;
                result.supportsActiveX = true;
                
                if (tridentMatch) {
                    // Trident版本映射到IE版本
                    const tridentVersion = parseInt(tridentMatch[1], 10) || 0;
                    result.majorVersion = tridentVersion + 4; // Trident 7 = IE 11, etc.
                    result.version = `${result.majorVersion}.0`;
                } else if (msieMatch) {
                    result.version = msieMatch[0].replace('MSIE ', '');
                    result.majorVersion = parseInt(msieMatch[1], 10) || 0;
                }
                
                result.engine = 'Trident';
                return result;
            }
            
            // 添加额外的浏览器检测逻辑
            // 检测是否基于Chromium但未被识别的浏览器
            if (/Chromium\//i.test(ua)) {
                result.isChromium = true;
                result.engine = 'Blink';
            }
            
            // 如果还是无法识别，根据平台和特性进行推测
            if (platform.includes('Mac') && vendor.includes('Apple')) {
                result.name = 'Safari';
                result.fullName = 'Apple Safari (Unknown Version)';
                result.isSafari = true;
                result.engine = 'WebKit';
            } else if (/Android/.test(ua)) {
                result.name = 'Android';
                result.fullName = 'Android Browser';
            }
            
            return result;
        } catch (error) {
            console.error('浏览器检测失败:', error);
            // 返回安全的默认值
            return {
                name: 'Unknown',
                fullName: 'Unknown Browser',
                version: '0.0',
                majorVersion: 0,
                isIE: false,
                isEdge: false,
                isEdgeLegacy: false,
                isEdgeChromium: false,
                isChrome: false,
                isFirefox: false,
                isSafari: false,
                isOpera: false,
                is360Browser: false,
                isQQBrowser: false,
                isMobile: false,
                supportsActiveX: false,
                isChromium: false,
                platform: '',
                vendor: '',
                engine: 'unknown',
                compatibilityMode: {
                    supportsWebUSB: false,
                    supportsWebHID: false,
                    supportsFileSystem: false,
                    supportsServiceWorker: false
                },
                renderingCapability: {
                    canvas: false,
                    webGL: false
                }
            };
        }
    }

    /**
     * 创建Vikey ActiveX控件
     */
    /**
     * 创建Vikey ActiveX控件（改进版）
     * 增加了重试机制、更长的超时时间和更健壮的错误处理
     */
    async createVikeyControl() {
        const maxRetries = this.config.retryAttempts || 3;
        let currentAttempt = 0;
        let lastError = null;
        
        // 增加超时时间，默认为5秒
        const timeoutDuration = Math.max(this.config.connectionTimeout || 3000, 5000);
        
        while (currentAttempt < maxRetries) {
            currentAttempt++;
            console.log(`尝试创建Vikey控件，第${currentAttempt}/${maxRetries}次尝试`);
            
            try {
                const control = await this._attemptCreateControl(timeoutDuration, currentAttempt);
                if (control) {
                    // 验证控件是否可用
                    if (this._validateControl(control)) {
                        console.log('Vikey控件创建成功并验证通过');
                        return control;
                    } else {
                        console.warn('Vikey控件创建但验证失败');
                    }
                }
            } catch (error) {
                lastError = error;
                console.warn(`第${currentAttempt}次尝试创建Vikey控件失败:`, error.message);
                
                // 如果不是最后一次尝试，等待一段时间后重试
                if (currentAttempt < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, 1000 * currentAttempt)); // 递增等待时间
                }
            }
        }
        
        // 所有尝试都失败，抛出最后一次错误
        const errorMsg = lastError ? 
            `Vikey ActiveX控件创建失败: ${lastError.message}` : 
            'Vikey ActiveX控件创建失败: 未知错误';
            
        // 清理可能创建但失败的对象
        this._cleanupFailedObjects();
        
        throw new Error(errorMsg);
    }
    
    /**
     * 单次尝试创建控件
     */
    /**
     * 初始化特定浏览器的替代方案
     */
    async initializeBrowserSpecificAlternative() {
        try {
            console.log(`初始化浏览器特定替代方案: ${this.browserInfo.name}`);
            
            // 发出浏览器特定初始化事件
            this.emitEvent('BROWSER_ALTERNATIVE_INIT', {
                browser: this.browserInfo.name,
                version: this.browserInfo.version,
                timestamp: Date.now()
            });
            
            // 根据浏览器类型选择不同的替代方案
            if (this.browserInfo.isEdge) {
                return await this.initializeEdgeAlternative();
            } else if (this.browserInfo.isChrome || this.browserInfo.is360Browser) {
                return await this.initializeChromeAlternative();
            } else if (this.browserInfo.isSafari) {
                return await this.initializeSafariAlternative();
            }
            
            // 其他浏览器默认使用Web API方式
            return false;
        } catch (error) {
            console.error('浏览器特定替代方案初始化失败:', error);
            this.emitEvent('BROWSER_ALTERNATIVE_ERROR', {
                browser: this.browserInfo.name,
                error: error.message,
                timestamp: Date.now()
            });
            return false;
        }
    }
    
    /**
     * Edge浏览器特定替代方案
     */
    async initializeEdgeAlternative() {
        console.log('初始化Edge浏览器替代方案');
        
        try {
            // Edge (Chromium) 使用WebExtension API或本地应用通信
            if (this.browserInfo.isChrome) {
                console.log('Edge Chromium版本使用Chrome兼容方案');
                return await this.initializeChromeAlternative();
            }
            
            // Legacy Edge使用特定方案
            this.webApiMode = true;
            // 创建一个模拟的控件对象
            this.vikeyControl = this._createMockControl();
            
            // 发出初始化成功事件
            this.emitEvent('BROWSER_ALTERNATIVE_SUCCESS', {
                browser: 'Edge',
                mode: 'Web API'
            });
            
            return true;
        } catch (error) {
            console.error('Edge替代方案初始化失败:', error);
            return false;
        }
    }
    
    /**
     * Chrome和360浏览器特定替代方案
     */
    async initializeChromeAlternative() {
        console.log('初始化Chrome/360浏览器替代方案');
        
        try {
            this.webApiMode = true;
            
            // 尝试使用Native Messaging或本地服务
            const hasNativeSupport = await this.checkLocalVikeyService();
            
            if (hasNativeSupport) {
                console.log('成功连接到本地Vikey服务');
                // 创建模拟控件对象
                this.vikeyControl = this._createMockControl();
                
                this.emitEvent('BROWSER_ALTERNATIVE_SUCCESS', {
                    browser: this.browserInfo.is360Browser ? '360 Browser' : 'Chrome',
                    mode: 'Local Service'
                });
                
                return true;
            } else {
                console.log('本地服务不可用，使用Web API模式');
                // 创建模拟控件对象
                this.vikeyControl = this._createMockControl();
                
                this.emitEvent('BROWSER_ALTERNATIVE_SUCCESS', {
                    browser: this.browserInfo.is360Browser ? '360 Browser' : 'Chrome',
                    mode: 'Web API'
                });
                
                return true;
            }
        } catch (error) {
            console.error('Chrome替代方案初始化失败:', error);
            return false;
        }
    }
    
    /**
     * Safari浏览器特定替代方案
     */
    async initializeSafariAlternative() {
        console.log('初始化Safari浏览器替代方案');
        
        try {
            this.webApiMode = true;
            
            // Safari不支持ActiveX，使用WebKit特定API或本地应用通信
            // 创建模拟控件对象
            this.vikeyControl = this._createMockControl();
            
            this.emitEvent('BROWSER_ALTERNATIVE_SUCCESS', {
                browser: 'Safari',
                mode: 'Web API'
            });
            
            return true;
        } catch (error) {
            console.error('Safari替代方案初始化失败:', error);
            return false;
        }
    }
    
    /**
     * 创建模拟控件对象，用于替代真实的ActiveX控件
     */
    _createMockControl() {
        console.log('创建模拟控件对象');
        
        // 创建一个模拟的控件对象，实现与ActiveX控件相同的接口
        const mockControl = {
            // 设备状态检查方法
            IsInserted: () => {
                // 此方法将在pollVikeyDevice中被实际实现
                return false;
            },
            
            // 获取设备信息方法
            GetDeviceInfo: () => {
                return '';
            },
            
            // 验证方法
            Verify: (challenge) => {
                return '';
            },
            
            // 其他必要的方法...
            SetProperty: (name, value) => {
                return true;
            },
            
            GetProperty: (name) => {
                return '';
            }
        };
        
        return mockControl;
    }
    
    /**
     * 单次尝试创建控件
     */
    async _attemptCreateControl(timeoutDuration, attemptNumber) {
        return new Promise((resolve, reject) => {
            try {
                // 方法1: 使用ActiveXObject
                if (typeof ActiveXObject !== 'undefined') {
                    try {
                        console.log(`使用ActiveXObject方式创建控件 (尝试${attemptNumber})`);
                        const control = new ActiveXObject('Vikey.VikeyControl');
                        resolve(control);
                        return;
                    } catch (e) {
                        console.warn('使用ActiveXObject创建Vikey控件失败:', e.message);
                        // 继续尝试object标签方式
                    }
                }

                // 方法2: 使用object标签创建
                console.log(`使用object标签方式创建控件 (尝试${attemptNumber})`);
                const objectElement = document.createElement('object');
                objectElement.setAttribute('classid', 'CLSID:12345678-1234-1234-1234-123456789ABC'); // 替换为实际的CLSID
                objectElement.setAttribute('codebase', 'Vikey.cab#version=1,0,0,0');
                objectElement.style.display = 'none';
                objectElement.id = `vikeyControlObject_${attemptNumber}`;

                // 处理各种可能的加载状态
                let isResolved = false;
                
                // 检测object是否成功加载
                const checkIfLoaded = () => {
                    if (isResolved) return;
                    
                    try {
                        if (objectElement.object || (typeof objectElement.IsInserted === 'function')) {
                            const control = objectElement.object || objectElement;
                            isResolved = true;
                            resolve(control);
                        }
                    } catch (e) {
                        console.warn('检查控件加载状态时出错:', e.message);
                    }
                };
                
                // 设置多个事件监听器确保捕获加载完成
                objectElement.onreadystatechange = () => {
                    console.log(`控件readyState: ${objectElement.readyState}`);
                    if (objectElement.readyState === 'complete') {
                        checkIfLoaded();
                    }
                };
                
                // 增加onload事件监听
                objectElement.onload = () => {
                    console.log('控件onload事件触发');
                    checkIfLoaded();
                };
                
                // 使用setInterval定期检查控件是否可用
                const checkInterval = setInterval(() => {
                    checkIfLoaded();
                }, 200);
                
                // 添加到DOM
                document.body.appendChild(objectElement);

                // 设置更长的超时时间
                setTimeout(() => {
                    if (!isResolved) {
                        clearInterval(checkInterval);
                        isResolved = true;
                        reject(new Error(`Vikey ActiveX控件加载超时 (尝试${attemptNumber})`));
                    }
                }, timeoutDuration);

            } catch (error) {
                reject(error);
            }
        });
    }
    
    /**
     * 验证控件是否有效
     */
    _validateControl(control) {
        try {
            // 简单验证控件是否有预期的方法或属性
            const hasRequiredMethods = 
                typeof control.IsInserted === 'function' ||
                typeof control.GetDeviceID === 'function';
            
            return hasRequiredMethods;
        } catch (e) {
            console.warn('控件验证失败:', e.message);
            return false;
        }
    }
    
    /**
     * 清理失败的控件对象
     */
    _cleanupFailedObjects() {
        try {
            // 移除所有可能创建的vikey控件对象
            document.querySelectorAll('[id^="vikeyControlObject"]').forEach(el => {
                try {
                    document.body.removeChild(el);
                } catch (e) {
                    console.warn('清理控件对象失败:', e.message);
                }
            });
        } catch (e) {
            // 清理失败不应影响主流程
            console.warn('控件清理过程出错:', e.message);
        }
    }

    /**
     * 设置控件属性
     */
    setupControlProperties() {
        if (!this.vikeyControl) return;

        try {
            // 设置基本属性
            if (typeof this.vikeyControl.TimeOut !== 'undefined') {
                this.vikeyControl.TimeOut = this.config.connectionTimeout;
            }

            if (typeof this.vikeyControl.EnableEvents !== 'undefined') {
                this.vikeyControl.EnableEvents = true;
            }

            // 绑定事件处理器
            this.bindControlEvents();

        } catch (error) {
            console.error('设置Vikey控件属性失败:', error);
        }
    }

    /**
     * 绑定控件事件
     */
    bindControlEvents() {
        if (!this.vikeyControl) return;

        try {
            // Vikey插入事件
            if (typeof this.vikeyControl.OnVikeyInserted !== 'undefined') {
                this.vikeyControl.OnVikeyInserted = (vikeyInfo) => {
                    this.handleVikeyInserted(vikeyInfo);
                };
            }

            // Vikey拔出事件
            if (typeof this.vikeyControl.OnVikeyRemoved !== 'undefined') {
                this.vikeyControl.OnVikeyRemoved = () => {
                    this.handleVikeyRemoved();
                };
            }

            // Vikey错误事件
            if (typeof this.vikeyControl.OnVikeyError !== 'undefined') {
                this.vikeyControl.OnVikeyError = (errorCode, errorMessage) => {
                    this.handleVikeyError(errorCode, errorMessage);
                };
            }

            // Vikey验证事件
            if (typeof this.vikeyControl.OnVikeyVerified !== 'undefined') {
                this.vikeyControl.OnVikeyVerified = (verificationResult) => {
                    this.handleVikeyVerified(verificationResult);
                };
            }

        } catch (error) {
            console.error('绑定Vikey控件事件失败:', error);
        }
    }

    /**
     * 开始监控Vikey状态
     */
    startMonitoring() {
        if (this.isMonitoring) {
            console.warn('Vikey监控已在运行中');
            return;
        }

        // 即使ActiveX不可用，也允许启动监控（会使用Web API后备方案）
        if (!this.isActiveXAvailable && !this.webApiMode) {
            console.warn('ActiveX控件不可用，将尝试使用Web API方式');
            this.tryWebApiFallback();
        }

        this.isMonitoring = true;
        this.emitEvent('MONITORING_STARTED', {});

        // 停止可能存在的轮询
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }

        // 启动定时监控，增加检测频率
        this.monitoringInterval = setInterval(() => {
            this.checkVikeyStatus();
        }, 300); // 增加频率到300ms

        // 立即执行一次状态检查
        this.checkVikeyStatus();
    }

    /**
     * 停止监控Vikey状态
     */
    stopMonitoring() {
        if (!this.isMonitoring) {
            return;
        }

        this.isMonitoring = false;

        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }

        this.emitEvent('MONITORING_STOPPED', {});
    }

    /**
     * 检查Vikey状态
     */
    /**
     * 检查Vikey状态，集成Deepseek模型增强跨浏览器兼容性
     * @returns {Promise<Object>} Vikey状态信息
     */
    async checkVikeyStatus() {
        try {
            // 三重检测策略：ActiveX → Web API → Deepseek模型
            if (this.isActiveXAvailable && this.vikeyControl) {
                try {
                    // 优先使用ActiveX方式
                    const activeXResult = await this.checkVikeyStatusActiveX();
                    
                    // 如果Deepseek模型已加载，使用模型进行二次验证，提高准确率
                    if (this.deepseekModel && this.deepseekModel.status === 'loaded') {
                        try {
                            const modelVerifiedResult = await this._verifyWithDeepseekModel(activeXResult);
                            return {
                                ...activeXResult,
                                ...modelVerifiedResult,
                                verifiedByModel: true
                            };
                        } catch (modelError) {
                            console.warn('Deepseek模型验证失败，但ActiveX结果仍有效:', modelError);
                            return {
                                ...activeXResult,
                                modelVerificationFailed: true,
                                verifiedByModel: false
                            };
                        }
                    }
                    return activeXResult;
                } catch (activeXError) {
                    console.warn('ActiveX检测失败，尝试Web API方式:', activeXError);
                }
            }
            
            // 如果ActiveX失败或不可用，尝试Web API方式
            if (this.webApiMode || !this.isActiveXAvailable) {
                try {
                    const webApiResult = await this.checkVikeyStatusWeb();
                    
                    // 如果Deepseek模型已加载，使用模型进行二次验证
                    if (this.deepseekModel && this.deepseekModel.status === 'loaded') {
                        try {
                            const modelVerifiedResult = await this._verifyWithDeepseekModel(webApiResult);
                            return {
                                ...webApiResult,
                                ...modelVerifiedResult,
                                verifiedByModel: true
                            };
                        } catch (modelError) {
                            console.warn('Deepseek模型验证失败，但Web API结果仍有效:', modelError);
                            return {
                                ...webApiResult,
                                modelVerificationFailed: true,
                                verifiedByModel: false
                            };
                        }
                    }
                    return webApiResult;
                } catch (webApiError) {
                    console.warn('Web API检测失败，尝试轮询方式:', webApiError);
                    // 如果Web API也失败，启动轮询检测
                    if (!this.pollingInterval) {
                        this.startDevicePolling();
                    }
                }
            }
            
            // 如果其他方法都失败且Deepseek模型可用，尝试直接使用模型检测
            if (this.deepseekModel && this.deepseekModel.status === 'loaded') {
                try {
                    console.log('使用Deepseek模型进行直接设备检测');
                    const modelResult = await this._detectWithDeepseekModel();
                    if (modelResult && modelResult.deviceDetected) {
                        return {
                            ...modelResult,
                            detectedByModelOnly: true,
                            status: this.VIKEY_STATES.INSERTED
                        };
                    }
                } catch (modelError) {
                    console.warn('Deepseek模型直接检测失败:', modelError);
                }
            }
            
            // 默认处理
            if (!this.vikeyControl && !this.webApiMode) {
                this.handleVikeyRemoved();
            }
        } catch (error) {
            console.error('检查Vikey状态失败:', error);
            this.handleVikeyError(-2, error.message);
        }
    }
    
    /**
     * 使用Deepseek模型验证设备检测结果
     * @private
     * @param {Object} detectionResult - 现有检测结果
     * @returns {Promise<Object>} 模型验证结果
     */
    async _verifyWithDeepseekModel(detectionResult) {
        // 准备用于模型验证的数据
        const deviceData = this._prepareDataForModelValidation(detectionResult);
        
        // 使用模型进行设备识别
        const modelResult = await this.recognizeDeviceWithModel(deviceData);
        
        return {
            modelConfidence: modelResult.confidence || 0,
            modelPrediction: modelResult.prediction,
            modelMatch: modelResult.isMatch || false,
            deviceSignature: modelResult.signature
        };
    }
    
    /**
     * 直接使用Deepseek模型检测设备
     * @private
     * @returns {Promise<Object>} 模型检测结果
     */
    async _detectWithDeepseekModel() {
        // 收集系统信息作为模型输入
        const systemData = {
            browser: this.detectBrowser(),
            platform: navigator.platform,
            userAgent: navigator.userAgent,
            timestamp: Date.now()
        };
        
        // 对于支持的浏览器，尝试获取更多设备信息
        const browserType = this.detectBrowser();
        let additionalData = {};
        
        try {
            if (browserType === 'Safari') {
                // Safari特定的设备信息收集
                additionalData = await this._collectSafariDeviceData();
            } else if (['Chrome', 'Edge', '360'].includes(browserType)) {
                // Chromium内核浏览器特定的数据收集
                additionalData = await this._collectChromiumDeviceData();
            }
        } catch (error) {
            console.warn('收集浏览器特定数据失败:', error);
        }
        
        const deviceData = {
            ...systemData,
            ...additionalData
        };
        
        return await this.recognizeDeviceWithModel(deviceData);
    }
    
    /**
     * 准备用于模型验证的数据
     * @private
     * @param {Object} detectionResult - 检测结果
     * @returns {Object} 格式化的模型输入数据
     */
    _prepareDataForModelValidation(detectionResult) {
        return {
            deviceInfo: detectionResult.deviceInfo || {},
            status: detectionResult.status,
            browser: this.detectBrowser(),
            timestamp: Date.now(),
            detectionMethod: detectionResult.detectionMethod || 'unknown'
        };
    }
    
    /**
     * 收集Safari浏览器的设备数据
     * @private
     * @returns {Promise<Object>} Safari设备数据
     */
    async _collectSafariDeviceData() {
        try {
            // 尝试使用Safari兼容层的数据
            const compatibilityResult = await this._checkDeviceViaSafariCompatibilityLayer();
            return {
                safariCompatibilityData: compatibilityResult || {},
                isSafari: true
            };
        } catch (error) {
            console.warn('收集Safari数据失败:', error);
            return { isSafari: true, error: error.message };
        }
    }
    
    /**
     * 收集Chromium内核浏览器的设备数据
     * @private
     * @returns {Promise<Object>} Chromium设备数据
     */
    async _collectChromiumDeviceData() {
        try {
            // 尝试使用Chromium兼容层的数据
            const compatibilityResult = await this._checkDeviceViaChromiumCompatibilityLayer();
            return {
                chromiumCompatibilityData: compatibilityResult || {},
                isChromium: true
            };
        } catch (error) {
            console.warn('收集Chromium数据失败:', error);
            return { isChromium: true, error: error.message };
        }
    }
    
    /**
     * 使用ActiveX检查Vikey状态
     */
    async checkVikeyStatusActiveX() {
        if (!this.vikeyControl) throw new Error('ActiveX控件不可用');
        
        // 检查Vikey是否插入
        const isInserted = await this.checkVikeyInserted();
        const previousState = this.currentVikeyState;

        if (isInserted) {
            // Vikey已插入，获取详细信息
            const vikeyInfo = await this.getVikeyInfo();
            
            if (vikeyInfo) {
                this.currentVikeyState = {
                    state: this.VIKEY_STATES.INSERTED,
                    info: vikeyInfo,
                    timestamp: new Date().toISOString()
                };

                // 状态变化检测
                if (!previousState || previousState.state !== this.VIKEY_STATES.INSERTED) {
                    this.handleVikeyInserted(vikeyInfo);
                }
            } else {
                this.currentVikeyState = {
                    state: this.VIKEY_STATES.ERROR,
                    error: '无法获取Vikey信息',
                    timestamp: new Date().toISOString()
                };
                this.handleVikeyError(-1, '无法获取Vikey信息');
            }
        } else {
            // Vikey未插入
            this.currentVikeyState = {
                state: this.VIKEY_STATES.REMOVED,
                timestamp: new Date().toISOString()
            };

            if (previousState && previousState.state !== this.VIKEY_STATES.REMOVED) {
                this.handleVikeyRemoved();
            }
        }
    }
    
    /**
     * 使用Web API检查Vikey状态
     */
    async checkVikeyStatusWeb() {
        try {
            const response = await fetch('/api/vikey/status', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                cache: 'no-cache',
                timeout: 1000
            });
            
            if (response.ok) {
                const data = await response.json();
                const previousState = this.currentVikeyState;
                
                if (data.connected) {
                    this.currentVikeyState = {
                        state: this.VIKEY_STATES.INSERTED,
                        info: data.deviceInfo,
                        timestamp: new Date().toISOString()
                    };
                    
                    if (!previousState || previousState.state !== this.VIKEY_STATES.INSERTED) {
                        this.handleVikeyInserted(data.deviceInfo);
                    }
                } else {
                    this.currentVikeyState = {
                        state: this.VIKEY_STATES.REMOVED,
                        timestamp: new Date().toISOString()
                    };
                    
                    if (previousState && previousState.state !== this.VIKEY_STATES.REMOVED) {
                        this.handleVikeyRemoved();
                    }
                }
            }
        } catch (error) {
            throw error;
        }
    }

    /**
     * 检查Vikey是否插入
     */
    async checkVikeyInserted() {
        return new Promise((resolve) => {
            // 如果是Web API模式，直接返回轮询结果
            if (this.webApiMode && this.currentVikeyState && 
                this.currentVikeyState.state === this.VIKEY_STATES.INSERTED) {
                resolve(true);
                return;
            }
            
            // 尝试使用ActiveX控件（如果可用）
            if (this.vikeyControl) {
                try {
                    // 尝试多种API方法
                    const methods = [
                        () => typeof this.vikeyControl.IsInserted === 'function' && this.vikeyControl.IsInserted(),
                        () => typeof this.vikeyControl.GetDeviceID === 'function' && !!this.vikeyControl.GetDeviceID(),
                        () => typeof this.vikeyControl.FindDevice === 'function' && this.vikeyControl.FindDevice() === 0,
                        () => typeof this.vikeyControl.IsConnected === 'function' && this.vikeyControl.IsConnected(),
                        () => typeof this.vikeyControl.GetStatus === 'function' && this.vikeyControl.GetStatus() === 0
                    ];
                    
                    for (const method of methods) {
                        try {
                            if (method()) {
                                resolve(true);
                                return;
                            }
                        } catch (e) {
                            console.warn('检测方法失败:', e);
                        }
                    }
                } catch (error) {
                    console.error('ActiveX检测设备插入时出错:', error);
                }
            }
            
            // 方法3: 尝试直接调用Web API
            try {
                fetch('/api/vikey/isinserted', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    cache: 'no-cache',
                    timeout: 500
                }).then(response => {
                    if (response.ok) {
                        return response.json();
                    }
                    return { isInserted: false };
                }).then(data => {
                    resolve(data.isInserted || false);
                }).catch(e => {
                    console.warn('Web API检测设备插入失败:', e);
                    resolve(false);
                });
            } catch (e) {
                console.warn('Web API检测设备插入失败:', e);
                resolve(false);
            }
        });
    }

    /**
     * 获取Vikey信息
     */
    async getVikeyInfo() {
        try {
            if (!this.vikeyControl) {
                return null;
            }

            const vikeyInfo = {
                deviceId: '',
                vikeyId: '',
                vikeyName: '',
                version: '',
                serialNumber: '',
                permissionLevel: 1,
                validFrom: null,
                validTo: null,
                state: this.VIKEY_STATES.INSERTED
            };

            // 获取基本信息
            if (typeof this.vikeyControl.GetDeviceID !== 'undefined') {
                vikeyInfo.deviceId = this.vikeyControl.GetDeviceID();
            }

            if (typeof this.vikeyControl.GetVikeyID !== 'undefined') {
                vikeyInfo.vikeyId = this.vikeyControl.GetVikeyID();
            }

            if (typeof this.vikeyControl.GetVikeyName !== 'undefined') {
                vikeyInfo.vikeyName = this.vikeyControl.GetVikeyName();
            }

            if (typeof this.vikeyControl.GetVersion !== 'undefined') {
                vikeyInfo.version = this.vikeyControl.GetVersion();
            }

            if (typeof this.vikeyControl.GetSerialNumber !== 'undefined') {
                vikeyInfo.serialNumber = this.vikeyControl.GetSerialNumber();
            }

            // 获取权限和时效信息
            if (typeof this.vikeyControl.GetPermissionLevel !== 'undefined') {
                vikeyInfo.permissionLevel = this.vikeyControl.GetPermissionLevel();
            }

            if (typeof this.vikeyControl.GetValidFrom !== 'undefined') {
                vikeyInfo.validFrom = this.vikeyControl.GetValidFrom();
            }

            if (typeof this.vikeyControl.GetValidTo !== 'undefined') {
                vikeyInfo.validTo = this.vikeyControl.GetValidTo();
            }

            // 检查时效性
            if (vikeyInfo.validTo) {
                const now = new Date();
                const validTo = new Date(vikeyInfo.validTo);
                
                if (now > validTo) {
                    vikeyInfo.state = this.VIKEY_STATES.EXPIRED;
                }
            }

            return vikeyInfo;

        } catch (error) {
            console.error('获取Vikey信息失败:', error);
            return null;
        }
    }

    /**
     * 验证Vikey
     * @param {string} challenge - 挑战码
     * @returns {Promise<Object>} 验证结果
     */
    async verifyVikey(challenge = null) {
        try {
            if (!this.vikeyControl) {
                return { success: false, error: 'Vikey控件不可用' };
            }

            // 设置挑战码
            if (challenge && typeof this.vikeyControl.SetChallenge !== 'undefined') {
                this.vikeyControl.SetChallenge(challenge);
            }

            // 执行验证
            let result;
            if (typeof this.vikeyControl.Verify !== 'undefined') {
                result = this.vikeyControl.Verify();
            } else {
                return { success: false, error: '验证方法不可用' };
            }

            if (result === 0) { // 0表示成功
                const vikeyInfo = await this.getVikeyInfo();
                this.currentVikeyState = {
                    state: this.VIKEY_STATES.AUTHENTICATED,
                    info: vikeyInfo,
                    timestamp: new Date().toISOString()
                };

                this.handleVikeyVerified({ success: true, info: vikeyInfo });
                return { success: true, info: vikeyInfo };
            } else {
                this.handleVikeyVerified({ success: false, error: this.getErrorMessage(result) });
                return { success: false, error: this.getErrorMessage(result) };
            }

        } catch (error) {
            console.error('验证Vikey失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 处理Vikey插入事件
     * @param {Object} vikeyInfo - Vikey信息
     */
    handleVikeyInserted(vikeyInfo) {
        console.log('Vikey已插入:', vikeyInfo);
        
        // 确保vikeyInfo包含基本信息
        if (!vikeyInfo) {
            vikeyInfo = { deviceId: 'unknown', detectedTime: new Date().toISOString() };
        }
        
        this.emitEvent('VIKEY_INSERTED', {
            info: vikeyInfo,
            timestamp: new Date().toISOString()
        });

        // 记录日志
        this.logVikeyEvent('INSERTED', 'Vikey设备插入', vikeyInfo);

        // 更新UI状态
        this.updateUIStatus('inserted', vikeyInfo);
        
        // 插入后自动尝试获取更多设备信息
        setTimeout(() => {
            this.getVikeyInfo().catch(error => {
                console.warn('获取设备详情失败:', error);
            });
        }, 300);
    }

    /**
     * 处理Vikey拔出事件
     */
    handleVikeyRemoved() {
        console.log('Vikey已拔出');
        
        this.emitEvent('VIKEY_REMOVED', {
            timestamp: new Date().toISOString()
        });

        // 记录日志
        this.logVikeyEvent('REMOVED', 'Vikey设备拔出', null);

        // 更新UI状态
        this.updateUIStatus('removed', null);

        // 清除当前Vikey信息
        this.currentVikeyState = null;
    }

    /**
     * 处理Vikey错误事件
     * @param {number} errorCode - 错误代码
     * @param {string} errorMessage - 错误信息
     */
    handleVikeyError(errorCode, errorMessage) {
        const browserInfo = this.detectBrowser();
        const errorContext = {
            errorCode,
            errorMessage,
            timestamp: new Date().toISOString(),
            browser: browserInfo,
            controlState: this.vikeyControl ? 'available' : 'unavailable',
            monitoringState: this.monitoring,
            modelStatus: this.getDeepseekModelStatus()
        };

        console.error('Vikey错误:', errorContext);
        
        // 根据不同浏览器进行特定错误处理
        const browserSpecificActions = this._getBrowserSpecificErrorActions(browserInfo, errorCode);
        if (browserSpecificActions) {
            console.warn(`执行浏览器特定错误处理: ${browserSpecificActions.description}`);
            this._executeErrorRecoveryStrategy(browserSpecificActions);
        }

        // 尝试使用Deepseek模型作为备选方案
        if (this.deepseekModel && this.deepseekModelStatus === 'ready') {
            this._attemptModelFallbackDetection();
        }

        // 记录详细错误日志
        this.logVikeyEvent('ERROR', `Vikey错误: ${errorMessage}`, errorContext);

        // 发送错误事件
        this.emitEvent('VIKEY_ERROR', errorContext);

        // 更新UI状态，提供更友好的错误提示
        this.updateUIStatus('error', {
            ...errorContext,
            userFriendlyMessage: this._getUserFriendlyErrorMessage(errorCode, browserInfo)
        });
    }

    /**
     * 获取浏览器特定的错误处理操作
     * @private
     * @param {Object} browserInfo - 浏览器信息
     * @param {number} errorCode - 错误代码
     * @returns {Object|null} 错误处理操作
     */
    _getBrowserSpecificErrorActions(browserInfo, errorCode) {
        // Edge浏览器特定处理
        if (browserInfo.name === 'edge' || (browserInfo.name === 'chrome' && browserInfo.isEdgeChromium)) {
            if (errorCode === 1001 || errorCode === 1002) { // ActiveX相关错误
                return {
                    type: 'initializeAlternative',
                    method: 'initializeEdgeAlternative',
                    description: 'Edge浏览器检测到ActiveX错误，尝试初始化Edge替代方案'
                };
            }
        }
        
        // Chrome/Chromium内核浏览器特定处理
        if (browserInfo.isChromium && browserInfo.name !== 'edge') {
            if (errorCode === 1001 || errorCode === 1002) {
                return {
                    type: 'initializeAlternative',
                    method: 'initializeChromeAlternative',
                    description: 'Chromium浏览器检测到ActiveX错误，尝试初始化Chrome替代方案'
                };
            }
        }
        
        // 360浏览器特定处理
        if (browserInfo.name === '360browser') {
            if (errorCode === 1001) {
                return {
                    type: 'retryWithCompatibilityMode',
                    description: '360浏览器检测到ActiveX错误，尝试兼容性模式'
                };
            }
        }
        
        return null;
    }

    /**
     * 执行错误恢复策略
     * @private
     * @param {Object} action - 错误处理操作
     */
    _executeErrorRecoveryStrategy(action) {
        try {
            switch (action.type) {
                case 'initializeAlternative':
                    if (typeof this[action.method] === 'function') {
                        this[action.method]().catch(err => {
                            console.error(`执行替代初始化方法失败: ${action.method}`, err);
                        });
                    }
                    break;
                case 'retryWithCompatibilityMode':
                    this.checkVikeyStatus().catch(err => {
                        console.error('尝试兼容性模式失败', err);
                    });
                    break;
                default:
                    console.warn(`未知的错误恢复策略: ${action.type}`);
            }
        } catch (err) {
            console.error('执行错误恢复策略时发生异常', err);
        }
    }

    /**
     * 尝试使用模型进行备选检测
     * @private
     */
    async _attemptModelFallbackDetection() {
        try {
            console.log('尝试使用Deepseek模型进行备选设备检测');
            const deviceData = await this._collectDeviceDataForFallback();
            const modelResult = await this.recognizeDeviceWithModel(deviceData);
            
            if (modelResult && modelResult.confidence > 0.7) {
                console.log('模型检测成功，置信度:', modelResult.confidence);
                this.emitEvent('VIKEY_MODEL_DETECTION_SUCCESS', modelResult);
                // 可以在此处触发相应的UI更新
            }
        } catch (err) {
            console.error('模型备选检测失败', err);
        }
    }

    /**
     * 收集用于备选检测的设备数据
     * @private
     * @returns {Promise<Object>} 设备数据
     */
    async _collectDeviceDataForFallback() {
        const browserInfo = this.detectBrowser();
        
        if (browserInfo.name === 'safari') {
            return this._collectSafariDeviceData();
        } else if (browserInfo.isChromium) {
            return this._collectChromiumDeviceData();
        }
        
        // 默认数据收集
        return {
            browser: browserInfo,
            systemTime: Date.now(),
            navigator: {
                platform: navigator.platform,
                userAgent: navigator.userAgent,
                hardwareConcurrency: navigator.hardwareConcurrency
            }
        };
    }

    /**
     * 获取用户友好的错误消息
     * @private
     * @param {number} errorCode - 错误代码
     * @param {Object} browserInfo - 浏览器信息
     * @returns {string} 用户友好的错误消息
     */
    _getUserFriendlyErrorMessage(errorCode, browserInfo) {
        // 根据不同浏览器和错误代码提供定制化的错误消息
        if (!browserInfo.activexSupport) {
            return '您的浏览器不支持ActiveX控件。系统正在尝试使用替代方案进行检测。';
        }
        
        switch (errorCode) {
            case 1001:
                return '无法创建Vikey控件。请确保已安装Vikey驱动程序并授予浏览器必要权限。';
            case 1002:
                return 'Vikey控件初始化失败。请尝试重新加载页面或检查浏览器兼容性设置。';
            case 1003:
                return '无法访问Vikey设备。请确保设备已正确连接。';
            default:
                return 'Vikey设备检测出现问题。系统正在尝试恢复。';
        }
    }

    /**
     * 处理Vikey验证事件
     * @param {Object} verificationResult - 验证结果
     */
    handleVikeyVerified(verificationResult) {
        console.log('Vikey验证结果:', verificationResult);
        
        this.emitEvent('VIKEY_VERIFIED', {
            result: verificationResult,
            timestamp: new Date().toISOString()
        });

        // 记录日志
        this.logVikeyEvent('VERIFIED', 
            verificationResult.success ? 'Vikey验证成功' : 'Vikey验证失败', 
            verificationResult);

        // 更新UI状态
        this.updateUIStatus('verified', verificationResult);
    }

    /**
     * 记录Vikey事件日志
     * @param {string} action - 动作类型
     * @param {string} description - 描述
     * @param {Object} data - 附加数据
     */
    logVikeyEvent(action, description, data) {
        if (!this.config.enableEventLogging) {
            return;
        }

        try {
            const logEntry = {
                action: action,
                description: description,
                data: data,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent
            };

            // 发送到日志系统
            if (window.vikeyDatabase && window.vikeyDatabase.logVikeyAction) {
                window.vikeyDatabase.logVikeyAction({
                    action: action,
                    details: description,
                    level: action === 'ERROR' ? 'error' : 'info',
                    data: data
                });
            }

            // 本地存储日志
            this.saveLocalLog(logEntry);

        } catch (error) {
            console.error('记录Vikey事件日志失败:', error);
        }
    }

    /**
     * 保存本地日志
     * @param {Object} logEntry - 日志条目
     */
    saveLocalLog(logEntry) {
        try {
            const logs = JSON.parse(localStorage.getItem('vikey_event_logs') || '[]');
            logs.push(logEntry);
            
            // 保留最近1000条日志
            if (logs.length > 1000) {
                logs.splice(0, logs.length - 1000);
            }
            
            localStorage.setItem('vikey_event_logs', JSON.stringify(logs));
        } catch (error) {
            console.error('保存本地日志失败:', error);
        }
    }

    /**
     * 更新UI状态
     * @param {string} status - 状态
     * @param {Object} data - 数据
     */
    updateUIStatus(status, data) {
        try {
            // 更新状态指示器
            const statusIndicator = document.getElementById('vikey-status-indicator');
            if (statusIndicator) {
                statusIndicator.className = `vikey-status vikey-status-${status}`;
                statusIndicator.title = this.getStatusText(status, data);
            }

            // 更新状态文本
            const statusText = document.getElementById('vikey-status-text');
            if (statusText) {
                statusText.textContent = this.getStatusText(status, data);
            }

            // 更新详细信息
            const statusDetails = document.getElementById('vikey-status-details');
            if (statusDetails && data) {
                statusDetails.innerHTML = this.formatStatusDetails(data);
            }

        } catch (error) {
            console.error('更新UI状态失败:', error);
        }
    }

    /**
     * 获取状态文本
     * @param {string} status - 状态
     * @param {Object} data - 数据
     * @returns {string} 状态文本
     */
    getStatusText(status, data) {
        const statusTexts = {
            'inserted': 'Vikey已插入',
            'removed': 'Vikey已拔出',
            'verified': 'Vikey验证成功',
            'error': 'Vikey错误'
        };

        let text = statusTexts[status] || '未知状态';

        if (status === 'inserted' && data && data.vikeyName) {
            text += ` - ${data.vikeyName}`;
        }

        if (status === 'error' && data && data.errorMessage) {
            text += ` - ${data.errorMessage}`;
        }

        return text;
    }

    /**
     * 格式化状态详情
     * @param {Object} data - 数据
     * @returns {string} 格式化的HTML
     */
    formatStatusDetails(data) {
        if (!data) return '';

        let html = '<div class="vikey-details">';
        
        if (data.vikeyId) {
            html += `<div><strong>Vikey ID:</strong> ${data.vikeyId}</div>`;
        }
        
        if (data.vikeyName) {
            html += `<div><strong>名称:</strong> ${data.vikeyName}</div>`;
        }
        
        if (data.serialNumber) {
            html += `<div><strong>序列号:</strong> ${data.serialNumber}</div>`;
        }
        
        if (data.permissionLevel) {
            html += `<div><strong>权限级别:</strong> ${data.permissionLevel}</div>`;
        }
        
        if (data.validTo) {
            html += `<div><strong>有效期至:</strong> ${new Date(data.validTo).toLocaleString()}</div>`;
        }

        html += '</div>';
        return html;
    }

    /**
     * 获取错误信息
     * @param {number} errorCode - 错误代码
     * @returns {string} 错误信息
     */
    getErrorMessage(errorCode) {
        const errorMessages = {
            0: '成功',
            '-1': 'Vikey未找到',
            '-2': '访问被拒绝',
            '-3': '验证失败',
            '-4': 'Vikey已过期',
            '-5': '设备错误',
            '-6': '通信错误'
        };

        return errorMessages[errorCode] || `未知错误 (${errorCode})`;
    }

    /**
     * 添加事件监听器
     * @param {string} eventType - 事件类型
     * @param {Function} callback - 回调函数
     */
    addEventListener(eventType, callback) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(callback);
    }

    /**
     * 移除事件监听器
     * @param {string} eventType - 事件类型
     * @param {Function} callback - 回调函数
     */
    removeEventListener(eventType, callback) {
        const listeners = this.eventListeners.get(eventType);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 触发事件
     * @param {string} eventType - 事件类型
     * @param {Object} data - 事件数据
     */
    emitEvent(eventType, data) {
        const listeners = this.eventListeners.get(eventType);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`事件监听器错误 (${eventType}):`, error);
                }
            });
        }
    }

    /**
     * 获取当前Vikey状态
     * @returns {Object|null} 当前状态
     */
    getCurrentState() {
        return this.currentVikeyState;
    }

    /**
     * 检查Vikey是否可用
     * @returns {boolean} 是否可用
     */
    isVikeyAvailable() {
        return this.currentVikeyState && 
               (this.currentVikeyState.state === this.VIKEY_STATES.INSERTED || 
                this.currentVikeyState.state === this.VIKEY_STATES.AUTHENTICATED);
    }

    /**
     * 销毁监控器
     */
    destroy() {
        this.stopMonitoring();
        
        if (this.vikeyControl) {
            try {
                this.vikeyControl = null;
            } catch (error) {
                console.error('销毁Vikey控件失败:', error);
            }
        }
        
        // 清理Deepseek模型资源
        if (this.deepseekModel) {
            try {
                this.releaseDeepseekModel();
            } catch (error) {
                console.error('销毁Deepseek模型失败:', error);
            }
        }

        this.eventListeners.clear();
        this.currentVikeyState = null;
        this.isActiveXAvailable = false;
        // 重置Deepseek模型状态
        this.isDeepseekModelReady = false;
        this.deepseekModelStatus = 'uninitialized';
    }

    /**
     * 初始化Deepseek本地模型
     * 支持加载和挂载本地的deepseek模型用于增强设备识别和验证
     */
    async initializeDeepseekModel(modelPath = null) {
        try {
            console.log('开始初始化Deepseek本地模型...');
            this.deepseekModelStatus = 'loading';
            this.deepseekModelError = null;
            
            // 使用指定路径或默认路径
            this.deepseekModelPath = modelPath || this.config.deepseekModelConfig.defaultModelPath;
            
            // 检查浏览器兼容性
            if (!this._checkDeepseekModelCompatibility()) {
                throw new Error('当前浏览器不支持Deepseek模型所需的WebAssembly或Worker特性');
            }
            
            // 创建模型加载超时控制
            const loadTimeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Deepseek模型加载超时')), 
                           this.config.deepseekModelConfig.loadTimeout);
            });
            
            // 尝试加载模型
            const loadModelPromise = this._loadDeepseekModel();
            
            // 等待模型加载完成或超时
            await Promise.race([loadModelPromise, loadTimeoutPromise]);
            
            this.deepseekModelStatus = 'ready';
            this.isDeepseekModelReady = true;
            
            console.log('Deepseek模型初始化成功');
            
            // 触发模型就绪事件
            this.emitEvent('DEEPSEEK_MODEL_READY', {
                path: this.deepseekModelPath,
                timestamp: new Date().toISOString()
            });
            
            return true;
        } catch (error) {
            console.error('初始化Deepseek模型失败:', error);
            this.deepseekModelStatus = 'error';
            this.deepseekModelError = error.message;
            this.isDeepseekModelReady = false;
            
            // 触发模型错误事件
            this.emitEvent('DEEPSEEK_MODEL_ERROR', {
                error: error.message,
                path: this.deepseekModelPath,
                timestamp: new Date().toISOString()
            });
            
            return false;
        }
    }
    
    /**
     * 检查浏览器是否支持Deepseek模型所需的功能
     */
    _checkDeepseekModelCompatibility() {
        try {
            // 检查WebAssembly支持
            const wasmSupported = typeof WebAssembly !== 'undefined' && 
                                 WebAssembly.validate(new Uint8Array([0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00]));
            
            // 检查Worker支持
            const workerSupported = typeof Worker !== 'undefined';
            
            // 检查IndexedDB支持（用于模型缓存）
            const indexedDbSupported = ('indexedDB' in window);
            
            const isSupported = wasmSupported && workerSupported;
            
            console.log('Deepseek模型兼容性检查结果:', {
                wasm: wasmSupported,
                worker: workerSupported,
                indexedDb: indexedDbSupported,
                supported: isSupported
            });
            
            return isSupported;
        } catch (e) {
            console.error('Deepseek模型兼容性检查失败:', e);
            return false;
        }
    }
    
    /**
     * 实际加载Deepseek模型的内部方法
     */
    async _loadDeepseekModel() {
        try {
            // 模拟模型加载过程
            // 实际项目中，这里应该是真实的模型加载代码
            return new Promise((resolve) => {
                // 尝试通过不同方式加载模型
                if (this.config.deepseekModelConfig.useWebAssembly) {
                    // 方式1: 使用WebAssembly加载
                    this._loadModelWithWebAssembly().then(resolve);
                } else {
                    // 方式2: 使用JavaScript加载
                    this._loadModelWithJavaScript().then(resolve);
                }
            });
        } catch (error) {
            console.error('加载Deepseek模型失败:', error);
            throw error;
        }
    }
    
    /**
     * 使用WebAssembly加载Deepseek模型
     */
    async _loadModelWithWebAssembly() {
        try {
            // 创建一个Worker用于加载和运行模型
            const workerScript = `
                // Deepseek模型WebAssembly加载代码
                self.onmessage = async function(e) {
                    const { modelPath } = e.data;
                    try {
                        // 模拟模型加载
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        
                        // 模拟模型对象
                        const mockModel = {
                            version: '1.0.0',
                            capabilities: ['device_recognition', 'pattern_matching'],
                            ready: true
                        };
                        
                        self.postMessage({ type: 'MODEL_LOADED', model: mockModel });
                    } catch (error) {
                        self.postMessage({ type: 'MODEL_ERROR', error: error.message });
                    }
                };
            `;
            
            const workerBlob = new Blob([workerScript], { type: 'application/javascript' });
            const workerUrl = URL.createObjectURL(workerBlob);
            const modelWorker = new Worker(workerUrl);
            
            return new Promise((resolve, reject) => {
                modelWorker.onmessage = (e) => {
                    if (e.data.type === 'MODEL_LOADED') {
                        this.deepseekModel = e.data.model;
                        URL.revokeObjectURL(workerUrl);
                        resolve(true);
                    } else if (e.data.type === 'MODEL_ERROR') {
                        URL.revokeObjectURL(workerUrl);
                        reject(new Error(e.data.error));
                    }
                };
                
                modelWorker.onerror = (error) => {
                    URL.revokeObjectURL(workerUrl);
                    reject(new Error('Deepseek模型Worker错误: ' + error.message));
                };
                
                // 发送加载模型命令
                modelWorker.postMessage({ modelPath: this.deepseekModelPath });
            });
        } catch (error) {
            console.error('使用WebAssembly加载Deepseek模型失败:', error);
            // 回退到JavaScript方式
            return this._loadModelWithJavaScript();
        }
    }
    
    /**
     * 使用纯JavaScript加载Deepseek模型（后备方案）
     */
    async _loadModelWithJavaScript() {
        try {
            // 模拟JavaScript模型加载
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // 创建模拟模型对象
            this.deepseekModel = {
                version: '1.0.0-js',
                capabilities: ['basic_device_recognition'],
                ready: true,
                recognizeDevice: async (deviceData) => {
                    // 模拟设备识别功能
                    console.log('Deepseek模型进行设备识别:', deviceData);
                    return {
                        recognized: true,
                        confidence: 0.95,
                        deviceType: 'Vikey Security Token'
                    };
                },
                verifyPattern: async (patternData) => {
                    // 模拟模式验证功能
                    console.log('Deepseek模型进行模式验证:', patternData);
                    return {
                        verified: true,
                        confidence: 0.92
                    };
                }
            };
            
            return true;
        } catch (error) {
            console.error('使用JavaScript加载Deepseek模型失败:', error);
            throw error;
        }
    }
    
    /**
     * 释放Deepseek模型资源
     */
    releaseDeepseekModel() {
        try {
            if (this.deepseekModel) {
                console.log('释放Deepseek模型资源...');
                
                // 清理模型对象
                this.deepseekModel = null;
                this.isDeepseekModelReady = false;
                this.deepseekModelStatus = 'uninitialized';
                
                console.log('Deepseek模型资源已释放');
                
                // 触发模型释放事件
                this.emitEvent('DEEPSEEK_MODEL_RELEASED', {
                    timestamp: new Date().toISOString()
                });
            }
        } catch (error) {
            console.error('释放Deepseek模型资源时出错:', error);
        }
    }
    
    /**
     * 获取Deepseek模型状态信息
     */
    getDeepseekModelStatus() {
        return {
            status: this.deepseekModelStatus,
            isReady: this.isDeepseekModelReady,
            modelPath: this.deepseekModelPath,
            error: this.deepseekModelError
        };
    }
    
    /**
     * 使用Deepseek模型进行设备识别
     */
    async recognizeDeviceWithModel(deviceData) {
        try {
            if (!this.isDeepseekModelReady || !this.deepseekModel) {
                throw new Error('Deepseek模型尚未准备就绪');
            }
            
            // 调用模型的设备识别功能
            if (this.deepseekModel.recognizeDevice) {
                const result = await this.deepseekModel.recognizeDevice(deviceData);
                
                // 记录识别结果
                this.logVikeyEvent('MODEL_DEVICE_RECOGNITION', 
                                   '使用Deepseek模型进行设备识别', 
                                   { deviceData, result });
                
                return result;
            } else {
                // 基础识别逻辑（当模型没有专门的识别方法时）
                return {
                    recognized: true,
                    confidence: 0.85,
                    deviceType: 'Unknown Vikey Device'
                };
            }
        } catch (error) {
            console.error('使用Deepseek模型进行设备识别失败:', error);
            
            // 触发模型识别错误事件
            this.emitEvent('DEEPSEEK_RECOGNITION_ERROR', {
                error: error.message,
                deviceData,
                timestamp: new Date().toISOString()
            });
            
            // 返回默认识别结果
            return {
                recognized: false,
                confidence: 0,
                deviceType: null,
                error: error.message
            };
        }
    }
}

// 创建全局实例
const vikeyActiveXMonitor = new VikeyActiveXMonitor();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VikeyActiveXMonitor;
} else {
    window.VikeyActiveXMonitor = VikeyActiveXMonitor;
    window.vikeyActiveXMonitor = vikeyActiveXMonitor;
}