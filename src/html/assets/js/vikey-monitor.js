
    // 初始化安全锁定系统
    if (typeof SecurityLock !== 'undefined') {
        window.securityLock = new SecurityLock();
        console.log('安全锁定系统已初始化');
    }
