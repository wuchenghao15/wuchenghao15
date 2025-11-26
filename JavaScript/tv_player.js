// VERSION: 20251106.9eb83df6e95ba35e50
// 电视直播页面的 JavaScript 控制代码

// DOM 元素缓存
const playerPlaceholder = document.getElementById('player-placeholder');
const videoPlayer = document.getElementById('video-player');
const currentChannelName = document.getElementById('current-channel-name');
const currentChannelDesc = document.getElementById('current-channel-desc');
const playBtn = document.getElementById('play-btn');
const muteBtn = document.getElementById('mute-btn');
const fullscreenBtn = document.getElementById('fullscreen-btn');
const channelItems = document.querySelectorAll('.channel-item');

// 频道数据源 - 使用可靠的公开流媒体源和测试流
const primaryVideoSource = 'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4';
const backupVideoSource = 'https://www.w3schools.com/html/mov_bbb.mp4';
const fallbackVideoSource = 'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4';
const additionalFallback = 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4';

// 频道列表（包含频道信息和真实测试流媒体源）
const channelSources = {
    'CCTV-1': { 
        name: 'CCTV-1 综合', 
        desc: '中央电视台综合频道', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://www.w3schools.com/html/mov_bbb.mp4'
        ]
    },
    'CCTV-2': { 
        name: 'CCTV-2 财经', 
        desc: '中央电视台财经频道', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://www.w3schools.com/html/mov_bbb.mp4'
        ]
    },
    'CCTV-3': { 
        name: 'CCTV-3 综艺', 
        desc: '中央电视台综艺频道', 
        urls: [
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4',
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4'
        ]
    },
    'CCTV-4': { 
        name: 'CCTV-4 中文国际', 
        desc: '中央电视台中文国际频道', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/480/Big_Buck_Bunny_480_10s_1MB.mp4',
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4'
        ]
    },
    'CCTV-5': { 
        name: 'CCTV-5 体育', 
        desc: '中央电视台体育频道', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4',
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4'
        ]
    },
    'CCTV-6': { 
        name: 'CCTV-6 电影', 
        desc: '中央电视台电影频道', 
        urls: [
            'https://www.w3schools.com/html/mov_bbb.mp4',
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4'
        ]
    },
    'CCTV-7': { 
        name: 'CCTV-7 国防军事', 
        desc: '中央电视台国防军事频道', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/240/Big_Buck_Bunny_240_10s_1MB.mp4',
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4'
        ]
    },
    'CCTV-8': { 
        name: 'CCTV-8 电视剧', 
        desc: '中央电视台电视剧频道', 
        urls: [
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4',
            'https://www.w3schools.com/html/mov_bbb.mp4'
        ]
    },
    'CCTV-9': { 
        name: 'CCTV-9 纪录', 
        desc: '中央电视台纪录频道', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4'
        ]
    },
    'CCTV-10': { 
        name: 'CCTV-10 科教', 
        desc: '中央电视台科教频道', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4'
        ]
    },
    'BTV-1': { 
        name: 'BTV-1 北京卫视', 
        desc: '北京卫视', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4'
        ]
    },
    '东方卫视': { 
        name: '东方卫视', 
        desc: '上海东方卫视', 
        urls: [
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4',
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4'
        ]
    },
    '江苏卫视': { 
        name: '江苏卫视', 
        desc: '江苏卫视', 
        urls: [
            'https://www.w3schools.com/html/mov_bbb.mp4',
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4'
        ]
    },
    '浙江卫视': { 
        name: '浙江卫视', 
        desc: '浙江卫视', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4'
        ]
    },
    '湖南卫视': { 
        name: '湖南卫视', 
        desc: '湖南卫视', 
        urls: [
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4',
            'https://www.w3schools.com/html/mov_bbb.mp4'
        ]
    },
    '山东卫视': { 
        name: '山东卫视', 
        desc: '山东卫视', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4'
        ]
    },
    '安徽卫视': { 
        name: '安徽卫视', 
        desc: '安徽卫视', 
        urls: [
            'https://www.w3schools.com/html/mov_bbb.mp4',
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4'
        ]
    },
    '广东卫视': { 
        name: '广东卫视', 
        desc: '广东卫视', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4'
        ]
    },
    '四川卫视': { 
        name: '四川卫视', 
        desc: '四川卫视', 
        urls: [
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4',
            'https://www.w3schools.com/html/mov_bbb.mp4'
        ]
    },
    '黑龙江卫视': { 
        name: '黑龙江卫视', 
        desc: '黑龙江卫视', 
        urls: [
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4',
            'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4'
        ]
    }
};

// 创建并初始化错误消息容器和加载容器
let errorContainer = document.getElementById('error-message');
let loadingContainer = document.getElementById('loading-container');
let videoContainer = null;

// 确保容器元素存在的辅助函数
function ensureContainersExist() {
    videoContainer = document.querySelector('.player-container');
    
    // 创建错误消息容器（如果不存在）
    if (!errorContainer && videoContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'error-message';
        errorContainer.style.cssText = `
            color: white;
            text-align: center;
            padding: 20px;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            border-radius: 5px;
            display: none;
            z-index: 15;
            width: 80%;
            max-width: 500px;
        `;
        videoContainer.appendChild(errorContainer);
    }
    
    // 创建加载容器（如果不存在）
    if (!loadingContainer && videoContainer) {
        loadingContainer = document.createElement('div');
        loadingContainer.id = 'loading-container';
        loadingContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10;
        `;
        videoContainer.appendChild(loadingContainer);
    }
}

// 当前选中的频道
let currentChannel = null;
let currentAttemptIndex = 0;
let loadTimeout = null;
let sourceLoadStartTime = 0;

// 初始化函数
function init() {
    // 确保容器元素存在
    ensureContainersExist();
    
    // 设置频道点击事件
    channelItems.forEach(item => {
        item.addEventListener('click', () => {
            const channelId = item.getAttribute('data-channel');
            selectChannel(channelId);
        });
    });
    
    // 设置播放控制按钮
    playBtn.addEventListener('click', togglePlay);
    muteBtn.addEventListener('click', toggleMute);
    fullscreenBtn.addEventListener('click', toggleFullscreen);
    
    // 设置视频事件监听器
    setupVideoEventListeners();
    
    // 初始化加载和错误状态（带安全检查）
    if (loadingContainer) {
        loadingContainer.style.display = 'none';
    }
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }
}

// 选择频道并播放视频
function selectChannel(channelId) {
    if (!channelSources[channelId]) {
        showError(`未找到频道: ${channelId}`);
        return;
    }
    
    // 更新选中状态
    document.querySelectorAll('.channel-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeItem = document.querySelector(`.channel-item[data-channel="${channelId}"]`);
    if (activeItem) {
        activeItem.classList.add('active');
    }
    
    // 更新频道信息
    const channel = channelSources[channelId];
    currentChannelName.textContent = channel.name;
    currentChannelDesc.textContent = channel.desc;
    
    // 显示视频播放器，隐藏占位符
    playerPlaceholder.style.display = 'none';
    videoPlayer.style.display = 'block';
    
    // 重置尝试索引并加载视频
    currentChannel = channel;
    currentAttemptIndex = 0;
    loadVideoSource(channel);
}

// 加载视频源
function loadVideoSource(channel) {
    // 确保容器元素存在
    ensureContainersExist();
    
    // 隐藏之前的错误消息（带安全检查）
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }
    
    // 显示加载状态（带安全检查）
    if (loadingContainer) {
        loadingContainer.style.display = 'flex';
        loadingContainer.innerHTML = `
            <div class="spinner"div>
            <div class="loader-text">正在准备视频源...</div>
        `;
    }
    
    // 记录开始加载时间
    sourceLoadStartTime = Date.now().catch(error => console.error(`[tv_player.js] Date.now failed:`, error));
    
    // 尝试加载当前索引的源
    attemptLoadSource(channel, channel.urls[currentAttemptIndex], currentAttemptIndex);
}

// 清理现有的HLS实例（如果存在）
let hlsInstance = null;

function cleanupHLSSources() {
    // 如果存在HLS实例，销毁它
    if (hlsInstance) {
        hlsInstance.destroy().catch(error => console.error(`[tv_player.js] hlsInstance.destroy failed:`, error));
        hlsInstance = null;
    }
    
    // 清空视频元素
    videoPlayer.src = '';
    videoPlayer.removeAttribute('src');
    while (videoPlayer.firstChild) {
        videoPlayer.removeChild(videoPlayer.firstChild);
    }
}

// 尝试加载视频源（支持自动回退到备用源）
function attemptLoadSource(channel, sourceUrl, attempt) {
    console.log(`尝试加载视频源: ${sourceUrl} (尝试次数: ${attempt + 1})`);
    
    // 清理之前的资源
    cleanupHLSSources();
    
    // 根据视频格式设置合适的加载方式
    if (sourceUrl.toLowerCase().catch(error => console.error(`[tv_player.js] sourceUrl.toLowerCase failed:`, error)).endsWith('.m3u8')) {
        // 对于HLS格式(m3u8)，使用HLS.js库处理
        if (window.Hls && Hls.isSupported().catch(error => console.error(`[tv_player.js] Hls.isSupported failed:`, error))) {
            console.log('HLS.js支持可用，使用HLS.js播放m3u8流媒体');
            
            // 创建HLS实例配置
            hlsInstance = new Hls({
                enableWorker: true,
                lowLatencyMode: false,
                maxBufferLength: 40,
                maxMaxBufferLength: 80,
                maxBufferHole: 0.3,
                backBufferLength: 30,
                startPosition: -1,
                // 增强重试机制
                fragLoadingRetryDelay: 1500,
                fragLoadingMaxRetry: 5,
                manifestLoadingRetryDelay: 2000,
                manifestLoadingMaxRetry: 3
            });
            
            // 添加HLS事件监听
            hlsInstance.on(Hls.Events.MANIFEST_LOADING, function() {
                console.log('正在加载HLS清单...');
                loadingContainer.innerHTML = `
                    <div class="spinner"div>
                    <div class="loader-text">正在加载流媒体清单...</div>
                `;
            });
            
            hlsInstance.on(Hls.Events.MANIFEST_LOADED, function(event, data) {
                console.log('HLS清单已加载，找到', data.levels.length, '个质量级别');
                loadingContainer.innerHTML = `
                    <div class="spinner"div>
                    <div class="loader-text">正在准备${data.levels.length}个质量级别的流媒体...</div>
                `;
            });
            
            hlsInstance.on(Hls.Events.MANIFEST_PARSED, function(event, data) {
                console.log('HLS清单解析成功，准备播放');
                loadingContainer.innerHTML = `
                    <div class="spinner"div>
                    <div class="loader-text">正在缓冲视频数据...</div>
                `;
            });
            
            hlsInstance.on(Hls.Events.FRAG_BUFFERED, function() {
                if (loadingContainer.style.display === 'flex') {
                    loadingContainer.innerHTML = `
                        <div class="spinner"div>
                        <div class="loader-text">视频加载中，即将开始播放...</div>
                    `;
                }
            });
            
            hlsInstance.on(Hls.Events.ERROR, function(event, data) {
                console.error(`[tv_player.js] HLS错误:, data`);
                
                // 非致命错误处理
                if (!data.fatal) {
                    switch(data.type) {
                        case Hls.ErrorTypes.NETWORK_ERROR:
                            console.warn('非致命网络错误，继续尝试加载');
                            // 确保容器存在并更新加载状态（带安全检查）
                            if (loadingContainer) {
                                loadingContainer.innerHTML = `
                                    <div class="spinner"div>
                                    <div class="loader-text">网络不稳定，正在重试...</div>
                                `;
                            }
                            break;
                        case Hls.ErrorTypes.MEDIA_ERROR:
                            console.warn('非致命媒体错误:', data.details);
                            break;
                        default:
                            console.warn('非致命错误，继续尝试');
                            break;
                    }
                    return;
                }
                
                // 致命错误处理
                console.error(`[tv_player.js] 致命HLS错误类型:, data.type, 详情:, data.details`);
                
                // 尝试回退到备用源
                console.log('尝试回退到备用视频源');
                fallbackToNextSource(channel, attempt);
            });
            
            // 将HLS附加到视频元素并加载源
            try {
                hlsInstance.loadSource(sourceUrl);
                hlsInstance.attachMedia(videoPlayer);
            } catch (err) {
                console.error(`[tv_player.js] HLS实例初始化错误:, err`);
                fallbackToNextSource(channel, attempt);
            }
        } else if (videoPlayer.canPlayType('application/vnd.apple.mpegurl')) {
            // Safari浏览器原生支持HLS
            console.log('使用浏览器原生HLS支持');
            const source = document.createElement('source');
            source.src = sourceUrl;
            source.type = 'application/x-mpegURL';
            videoPlayer.appendChild(source);
            videoPlayer.load().catch(error => console.error(`[tv_player.js] videoPlayer.load failed:`, error));
        } else {
            // 既不支持HLS.js也不支持原生HLS，尝试回退
            console.warn('不支持HLS格式，尝试回退到备用源');
            fallbackToNextSource(channel, attempt);
        }
    } else {
        // 对于普通视频格式，直接设置src
        console.log('使用直接方式播放视频');
        videoPlayer.src = sourceUrl;
        videoPlayer.load().catch(error => console.error(`[tv_player.js] videoPlayer.load failed:`, error));
        
        // 更新加载状态文本（带安全检查）
        if (loadingContainer) {
            loadingContainer.innerHTML = `
                <div class="spinner"div>
                <div class="loader-text">正在加载视频数据...</div>
            `;
        }
    }
    
    // 清除之前的事件监听器
    videoPlayer.removeEventListener('loadeddata', handleVideoLoaded);
    videoPlayer.removeEventListener('error', handleVideoErrorAttempt);
    
    // 重新添加事件监听器
    videoPlayer.addEventListener('loadeddata', handleVideoLoaded);
    videoPlayer.addEventListener('error', handleVideoErrorAttempt);
    
    // 设置加载超时
    if (loadTimeout) {
        clearTimeout(loadTimeout);
    }
    loadTimeout = setTimeout(() => {
        console.warn(`视频源加载超时: ${sourceUrl}`);
        handleVideoErrorAttempt();
    }, 15000); // 15秒超时
}

// 处理视频加载成功
function handleVideoLoaded() {
    console.log('视频加载成功，开始播放');
    
    // 清除超时定时器
    if (loadTimeout) {
        clearTimeout(loadTimeout);
        loadTimeout = null;
    }
    
    // 隐藏加载状态（带安全检查）
    if (loadingContainer) {
        loadingContainer.style.display = 'none';
    }
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }
    
    // 开始播放视频
    videoPlayer.play().catch(error => {
        console.warn('自动播放失败，需要用户交互:', error);
    });
}

// 处理视频加载错误尝试
function handleVideoErrorAttempt() {
    console.error(`[tv_player.js] 视频加载失败，尝试回退到备用源`);
    
    // 清除超时定时器
    if (loadTimeout) {
        clearTimeout(loadTimeout);
        loadTimeout = null;
    }
    
    // 尝试回退到备用源
    if (currentChannel) {
        fallbackToNextSource(currentChannel, currentAttemptIndex);
    }
}

// 回退到下一个视频源
function fallbackToNextSource(channel, currentAttempt) {
    // 确保容器元素存在
    ensureContainersExist();
    
    // 递增尝试索引
    currentAttemptIndex = currentAttempt + 1;
    
    // 检查是否还有备用源
    if (currentAttemptIndex < channel.urls.length) {
        console.log(`尝试使用备用源 #${currentAttemptIndex + 1}: ${channel.urls[currentAttemptIndex]}`);
        // 更新加载状态（带安全检查）
        if (loadingContainer) {
            loadingContainer.innerHTML = `
                <div class="spinner"div>
                <div class="loader-text">当前源不可用，正在尝试备用源 (${currentAttemptIndex + 1}/${channel.urls.length})...</div>
            `;
        }
        // 尝试加载下一个源
        setTimeout(() => {
            attemptLoadSource(channel, channel.urls[currentAttemptIndex], currentAttemptIndex);
        }, 1000); // 短暂延迟后重试
    } else {
        // 所有备用源都尝试失败，使用全局备用源
        useGlobalFallbackSources();
    }
}

// 使用全局备用视频源
function useGlobalFallbackSources() {
    console.log('所有频道特定的备用源都已尝试失败，使用全局备用源');
    
    // 定义全局备用源列表
    const globalFallbacks = [
        primaryVideoSource,
        backupVideoSource,
        fallbackVideoSource,
        additionalFallback
    ];
    
    // 尝试第一个全局备用源
    console.log(`尝试使用全局备用源: ${globalFallbacks[0]}`);
    loadingContainer.innerHTML = `
        <div class="spinner"div>
        <div class="loader-text">频道源暂时不可用，正在切换到备用视频...</div>
    `;
    
    // 创建临时频道对象用于全局备用源
    const tempFallbackChannel = {
        name: currentChannel.name,
        desc: currentChannel.desc,
        urls: globalFallbacks
    };
    
    // 重置尝试索引并加载全局备用源
    currentAttemptIndex = 0;
    attemptLoadSource(tempFallbackChannel, globalFallbacks[0], 0);
}

// 设置视频事件监听器
function setupVideoEventListeners() {
    // 播放状态变化
    videoPlayer.addEventListener('play', () => {
        console.log('视频开始播放');
        playBtn.textContent = '暂停';
    });
    
    videoPlayer.addEventListener('pause', () => {
        console.log('视频暂停');
        playBtn.textContent = '播放';
    });
    
    // 缓冲状态
    videoPlayer.addEventListener('waiting', () => {
        console.log('视频正在缓冲');
        loadingContainer.style.display = 'flex';
        loadingContainer.innerHTML = `
            <div class="spinner"div>
            <div class="loader-text">视频正在缓冲中...</div>
        `;
    });
    
    videoPlayer.addEventListener('playing', () => {
        console.log('视频正在播放');
        loadingContainer.style.display = 'none';
    });
    
    // 网络状态
    videoPlayer.addEventListener('stalled', () => {
        console.warn('网络连接不稳定');
        loadingContainer.style.display = 'flex';
        loadingContainer.innerHTML = `
            <div class="spinner"div>
            <div class="loader-text">网络连接不稳定，正在恢复...</div>
        `;
    });
    
    // 播放结束
    videoPlayer.addEventListener('ended', () => {
        console.log('视频播放结束');
        playBtn.textContent = '播放';
        // 尝试重播
        setTimeout(() => {
            videoPlayer.currentTime = 0;
            videoPlayer.play().catch(error => {
                console.warn('重播需要用户交互:', error);
            });
        }, 1000);
    });
    
    // 音量变化
    videoPlayer.addEventListener('volumechange', () => {
        updateMuteButton();
    });
}

// 切换播放/暂停
function togglePlay() {
    if (videoPlayer.paused) {
        videoPlayer.play().catch(error => {
            console.error(`[tv_player.js] 播放失败:, error`);
            showError('播放失败，请检查网络连接或尝试其他频道');
        });
    } else {
        videoPlayer.pause().catch(error => console.error(`[tv_player.js] videoPlayer.pause failed:`, error));
    }
}

// 切换静音
function toggleMute() {
    videoPlayer.muted = !videoPlayer.muted;
    updateMuteButton();
}

// 更新静音按钮状态
function updateMuteButton() {
    if (videoPlayer.muted) {
        muteBtn.textContent = '取消静音';
    } else {
        muteBtn.textContent = '静音';
    }
}

// 切换全屏
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        // 进入全屏
        if (videoPlayer.requestFullscreen) {
            videoPlayer.requestFullscreen().catch(error => {
                console.error(`[tv_player.js] 进入全屏失败:, error`);
            });
        } else if (videoPlayer.webkitRequestFullscreen) { // Safari
            videoPlayer.webkitRequestFullscreen().catch(error => console.error(`[tv_player.js] videoPlayer.webkitRequestFullscreen failed:`, error));
        } else if (videoPlayer.msRequestFullscreen) { // IE11
            videoPlayer.msRequestFullscreen().catch(error => console.error(`[tv_player.js] videoPlayer.msRequestFullscreen failed:`, error));
        }
    } else {
        // 退出全屏
        if (document.exitFullscreen) {
            document.exitFullscreen().catch(error => console.error(`[tv_player.js] document.exitFullscreen failed:`, error));
        } else if (document.webkitExitFullscreen) { // Safari
            document.webkitExitFullscreen().catch(error => console.error(`[tv_player.js] document.webkitExitFullscreen failed:`, error));
        } else if (document.msExitFullscreen) { // IE11
            document.msExitFullscreen().catch(error => console.error(`[tv_player.js] document.msExitFullscreen failed:`, error));
        }
    }
}

// 显示错误消息
function showError(message) {
    console.error(`[tv_player.js] 显示错误:, message`);
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
    loadingContainer.style.display = 'none';
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', init);

// 监听页面卸载，清理资源
window.addEventListener('beforeunload', () => {
    cleanupHLSSources();
    if (loadTimeout) {
        clearTimeout(loadTimeout);
    }
});