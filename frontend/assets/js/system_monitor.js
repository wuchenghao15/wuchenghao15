(function() {
    'use strict';

    const SystemMonitor = {
        servers: {},
        logs: [],
        database: {
            tables: 12,
            usedSpace: '256 MB',
            lastSync: new Date().toLocaleTimeString()
        },
        autoRepair: true,
        autoBackup: true,
        faultWarning: true,
        operationHistory: [],

        init: function() {
            this.initializeServers();
            this.initializeParticles();
            this.initializeEventListeners();
            this.startMonitoring();
            this.log('success', '系统监控AI已成功启动');
            this.log('info', '所有服务器状态正常');
            this.updateStats();
        },

        initializeServers: function() {
            this.servers = {
                router: { name: '路由服务器', ip: '192.168.1.1', port: 8080, status: 'online', health: 100 },
                rule: { name: '规则服务器', ip: '192.168.1.2', port: 8081, status: 'online', health: 100 },
                county: { name: '全县服务器', ip: '192.168.1.3', port: 8082, status: 'online', health: 100 },
                script: { name: '脚本服务器', ip: '192.168.1.4', port: 8083, status: 'online', health: 100 },
                user: { name: '用户服务器', ip: '192.168.1.5', port: 8084, status: 'online', health: 100 },
                firewall: { name: '防火墙', ip: '192.168.1.6', port: 8085, status: 'online', health: 100 },
                redis: { name: 'Redis', ip: '192.168.1.7', port: 6379, status: 'online', health: 100 }
            };
            this.renderServerList();
        },

        initializeParticles: function() {
            if (typeof particlesJS !== 'undefined') {
                particlesJS('particles-js', {
                    particles: {
                        number: { value: 60, density: { enable: true, value_area: 800 } },
                        color: { value: ['#165DFF', '#4080FF', '#73B4FF'] },
                        shape: { type: 'circle' },
                        opacity: { value: 0.5, random: true, anim: { enable: true, speed: 1 } },
                        size: { value: 3, random: true, anim: { enable: true, speed: 2 } },
                        line_linked: { enable: true, distance: 150, color: '#165DFF', opacity: 0.4 },
                        move: { enable: true, speed: 1, out_mode: 'out' }
                    },
                    interactivity: {
                        events: {
                            onhover: { enable: true, mode: 'grab' },
                            onclick: { enable: true, mode: 'push' }
                        },
                        modes: { grab: { distance: 140 }, push: { particles_nb: 4 } }
                    },
                    retina_detect: true
                });
            }
        },

        initializeEventListeners: function() {
            const self = this;

            document.getElementById('autoRepairToggle')?.addEventListener('change', function() {
                self.autoRepair = this.checked;
                self.log(this.checked ? 'success' : 'warning', 
                    '自动修复系统已' + (this.checked ? '启用' : '禁用'));
                self.recordOperation('autoRepair', this.checked ? '启用' : '禁用');
            });

            document.getElementById('autoBackupToggle')?.addEventListener('change', function() {
                self.autoBackup = this.checked;
                self.log(this.checked ? 'success' : 'warning', 
                    '自动备份系统已' + (this.checked ? '启用' : '禁用'));
                self.recordOperation('autoBackup', this.checked ? '启用' : '禁用');
            });

            document.getElementById('faultWarningToggle')?.addEventListener('change', function() {
                self.faultWarning = this.checked;
                self.log(this.checked ? 'success' : 'warning', 
                    '故障预警系统已' + (this.checked ? '启用' : '禁用'));
                self.recordOperation('faultWarning', this.checked ? '启用' : '禁用');
            });

            document.getElementById('repairNowBtn')?.addEventListener('click', function() {
                self.performAutoRepair();
            });

            document.getElementById('backupNowBtn')?.addEventListener('click', function() {
                self.performBackup();
            });

            document.getElementById('clearLogsBtn')?.addEventListener('click', function() {
                self.clearLogs();
            });

            document.getElementById('syncDbBtn')?.addEventListener('click', function() {
                self.syncDatabase();
            });

            document.getElementById('optimizeDbBtn')?.addEventListener('click', function() {
                self.optimizeDatabase();
            });

            document.getElementById('logLevelFilter')?.addEventListener('change', function() {
                self.filterLogs(this.value);
            });
        },

        startMonitoring: function() {
            const self = this;
            setInterval(function() {
                self.checkServerHealth();
            }, 5000);

            setInterval(function() {
                self.performAutoRepairIfNeeded();
            }, 10000);

            if (this.autoBackup) {
                setInterval(function() {
                    self.performBackup();
                }, 60000);
            }
        },

        checkServerHealth: function() {
            let onlineCount = 0;
            let warningCount = 0;
            let offlineCount = 0;

            for (const key in this.servers) {
                const server = this.servers[key];
                const random = Math.random();
                
                if (random > 0.95) {
                    server.status = 'offline';
                    server.health = 0;
                    offlineCount++;
                    if (this.faultWarning) {
                        this.log('error', `${server.name} 已离线，正在尝试重新连接...`);
                    }
                } else if (random > 0.85) {
                    server.status = 'warning';
                    server.health = Math.floor(Math.random() * 40) + 30;
                    warningCount++;
                    if (this.faultWarning) {
                        this.log('warning', `${server.name} 健康度下降: ${server.health}%`);
                    }
                } else {
                    server.status = 'online';
                    server.health = Math.floor(Math.random() * 20) + 80;
                    onlineCount++;
                }
            }

            document.getElementById('onlineCount').textContent = onlineCount;
            document.getElementById('warningCount').textContent = warningCount;
            document.getElementById('offlineCount').textContent = offlineCount;

            this.renderServerList();
            this.updateStats();
        },

        renderServerList: function() {
            const container = document.querySelector('.server-list');
            if (!container) return;

            container.innerHTML = '';

            for (const key in this.servers) {
                const server = this.servers[key];
                const item = document.createElement('div');
                item.className = 'server-item';
                item.dataset.server = key;

                const statusIcon = server.status === 'online' ? 'fa-check-circle' :
                                   server.status === 'warning' ? 'fa-exclamation-triangle' : 'fa-times-circle';
                const statusClass = server.status;

                item.innerHTML = `
                    <div class="server-icon">
                        <i class="fas ${this.getServerIcon(key)}"></i>
                    </div>
                    <div class="server-info">
                        <h4>${server.name}</h4>
                        <p class="server-ip">${server.ip}:${server.port}</p>
                        <div class="health-bar">
                            <div class="health-fill ${statusClass}" style="width: ${server.health}%"></div>
                        </div>
                    </div>
                    <div class="server-status-indicator ${statusClass}">
                        <i class="fas ${statusIcon}"></i>
                    </div>
                `;

                container.appendChild(item);
            }
        },

        getServerIcon: function(key) {
            const icons = {
                router: 'fa-route',
                rule: 'fa-rules',
                county: 'fa-globe',
                script: 'fa-code',
                user: 'fa-user',
                firewall: 'fa-shield-alt',
                redis: 'fa-database'
            };
            return icons[key] || 'fa-server';
        },

        performAutoRepairIfNeeded: function() {
            if (!this.autoRepair) return;

            for (const key in this.servers) {
                const server = this.servers[key];
                
                if (server.status === 'offline') {
                    this.log('info', `正在修复 ${server.name}...`);
                    setTimeout(function() {
                        server.status = 'online';
                        server.health = 75;
                        this.log('success', `${server.name} 修复成功`);
                        this.recordOperation('repair', server.name);
                    }.bind(this), 2000);
                } else if (server.status === 'warning') {
                    this.log('info', `正在优化 ${server.name}...`);
                    setTimeout(function() {
                        server.health = Math.min(100, server.health + 20);
                        if (server.health >= 80) {
                            server.status = 'online';
                        }
                        this.log('success', `${server.name} 优化完成，当前健康度: ${server.health}%`);
                        this.recordOperation('optimize', server.name);
                    }.bind(this), 1500);
                }
            }

            this.renderServerList();
            this.updateStats();
        },

        performAutoRepair: function() {
            this.log('info', '开始全面系统检查...');
            this.recordOperation('fullScan', '开始');

            setTimeout(function() {
                let repaired = 0;
                for (const key in this.servers) {
                    const server = this.servers[key];
                    if (server.status !== 'online' || server.health < 100) {
                        server.status = 'online';
                        server.health = 100;
                        repaired++;
                    }
                }
                
                this.log('success', `系统检查完成，修复了 ${repaired} 个问题`);
                this.recordOperation('fullRepair', `修复了 ${repaired} 个问题`);
                this.renderServerList();
                this.updateStats();
            }.bind(this), 3000);
        },

        performBackup: function() {
            this.log('info', '开始数据库备份...');
            this.recordOperation('backup', '开始');

            setTimeout(function() {
                const backupData = {
                    timestamp: new Date().toISOString(),
                    servers: JSON.parse(JSON.stringify(this.servers)),
                    database: JSON.parse(JSON.stringify(this.database)),
                    logs: this.logs.slice(-100)
                };

                localStorage.setItem('mtscos_backup_' + Date.now(), JSON.stringify(backupData));
                
                this.database.lastSync = new Date().toLocaleTimeString();
                document.getElementById('lastSync').textContent = this.database.lastSync;
                
                this.log('success', '数据库备份完成');
                this.recordOperation('backup', '完成');
            }.bind(this), 2000);
        },

        syncDatabase: function() {
            this.log('info', '开始数据库同步...');
            this.recordOperation('sync', '开始');

            setTimeout(function() {
                this.database.lastSync = new Date().toLocaleTimeString();
                document.getElementById('lastSync').textContent = this.database.lastSync;
                this.log('success', '数据库同步完成');
                this.recordOperation('sync', '完成');
            }.bind(this), 2500);
        },

        optimizeDatabase: function() {
            this.log('info', '开始数据库优化...');
            this.recordOperation('optimize', '开始');

            setTimeout(function() {
                const oldSpace = parseInt(this.database.usedSpace);
                const newSpace = Math.floor(oldSpace * 0.7);
                this.database.usedSpace = newSpace + ' MB';
                document.getElementById('usedSpace').textContent = this.database.usedSpace;
                
                this.log('success', `数据库优化完成，释放了 ${oldSpace - newSpace} MB 空间`);
                this.recordOperation('optimize', '完成');
            }.bind(this), 3000);
        },

        log: function(level, message) {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = { level, message, timestamp };
            this.logs.push(logEntry);

            if (this.logs.length > 500) {
                this.logs.shift();
            }

            this.renderLogs();
        },

        renderLogs: function(filter = 'all') {
            const container = document.getElementById('logContainer');
            if (!container) return;

            const filteredLogs = filter === 'all' ? 
                this.logs : 
                this.logs.filter(log => log.level === filter);

            if (filteredLogs.length === 0) {
                container.innerHTML = '<div class="log-placeholder"><p>暂无日志记录</p></div>';
                return;
            }

            const recentLogs = filteredLogs.slice(-50).reverse();
            
            container.innerHTML = recentLogs.map(log => {
                const iconMap = {
                    info: 'fa-info-circle',
                    warning: 'fa-exclamation-triangle',
                    error: 'fa-times-circle',
                    success: 'fa-check-circle'
                };
                
                return `
                    <div class="log-entry ${log.level}">
                        <i class="fas ${iconMap[log.level] || 'fa-info-circle'}"></i>
                        <span class="log-time">${log.timestamp}</span>
                        <span class="log-message">${log.message}</span>
                    </div>
                `;
            }).join('');
        },

        filterLogs: function(level) {
            this.renderLogs(level);
        },

        clearLogs: function() {
            this.logs = [];
            this.renderLogs();
            this.log('info', '日志已清空');
            this.recordOperation('clearLogs', '清空');
        },

        recordOperation: function(operation, details) {
            const entry = {
                operation,
                details,
                timestamp: new Date().toLocaleTimeString()
            };
            this.operationHistory.unshift(entry);

            if (this.operationHistory.length > 50) {
                this.operationHistory.pop();
            }

            this.renderOperationHistory();
        },

        renderOperationHistory: function() {
            const container = document.getElementById('aiOperationsContainer');
            if (!container) return;

            if (this.operationHistory.length === 0) {
                container.innerHTML = '<div class="operation-placeholder"><p>暂无操作记录</p></div>';
                return;
            }

            container.innerHTML = this.operationHistory.map(op => {
                const iconMap = {
                    repair: 'fa-wrench',
                    optimize: 'fa-magic',
                    backup: 'fa-save',
                    sync: 'fa-sync',
                    fullScan: 'fa-search',
                    fullRepair: 'fa-tools',
                    clearLogs: 'fa-trash',
                    autoRepair: 'fa-robot',
                    autoBackup: 'fa-database',
                    faultWarning: 'fa-bell'
                };

                return `
                    <div class="operation-item">
                        <div class="operation-icon">
                            <i class="fas ${iconMap[op.operation] || 'fa-cog'}"></i>
                        </div>
                        <div class="operation-details">
                            <p class="operation-text">${op.details}</p>
                            <span class="operation-time">${op.timestamp}</span>
                        </div>
                    </div>
                `;
            }).join('');
        },

        updateStats: function() {
            const tableCountEl = document.getElementById('tableCount');
            if (tableCountEl) {
                this.database.tables = Math.floor(Math.random() * 5) + 10;
                tableCountEl.textContent = this.database.tables;
            }

            const usedSpaceEl = document.getElementById('usedSpace');
            if (usedSpaceEl) {
                usedSpaceEl.textContent = this.database.usedSpace;
            }

            const lastSyncEl = document.getElementById('lastSync');
            if (lastSyncEl) {
                lastSyncEl.textContent = this.database.lastSync;
            }

            const onlineCount = document.getElementById('onlineCount');
            const warningCount = document.getElementById('warningCount');
            const offlineCount = document.getElementById('offlineCount');

            if (onlineCount && warningCount && offlineCount) {
                let online = 0, warning = 0, offline = 0;
                for (const key in this.servers) {
                    if (this.servers[key].status === 'online') online++;
                    else if (this.servers[key].status === 'warning') warning++;
                    else offline++;
                }
                onlineCount.textContent = online;
                warningCount.textContent = warning;
                offlineCount.textContent = offline;
            }
        }
    };

    document.addEventListener('DOMContentLoaded', function() {
        SystemMonitor.init();
    });

    window.SystemMonitor = SystemMonitor;
})();