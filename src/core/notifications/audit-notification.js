/**
 * MTSCOS AI 系统 - 审核通知功能
 * 实时通知审核员处理待审核事项
 */

const emailService = require('../email-service');
const systemNotificationService = require('../system-notification-service');

class AuditNotification {
    constructor() {
        this.channels = ['email', 'system_notification'];
    }
    
    // 发送审核通知
    async sendAuditNotification(auditId, auditInfo, channels = this.channels) {
        const notificationContent = {
            subject: '新的审核请求',
            message: '有新的操作需要审核，请尽快处理。',
            auditId: auditId,
            auditInfo: auditInfo,
            timestamp: new Date().toISOString()
        };
        
        const results = [];
        
        // 发送邮件通知
        if (channels.includes('email')) {
            try {
                await emailService.sendEmail({
                    to: auditInfo.auditors,
                    subject: notificationContent.subject,
                    text: notificationContent.message + '

审核ID: ' + auditId + '
操作: ' + auditInfo.operation + '
用户: ' + (auditInfo.userId || '匿名用户') + '
时间: ' + notificationContent.timestamp
                });
                results.push({ channel: 'email', status: 'success' });
            } catch (error) {
                results.push({ channel: 'email', status: 'failed', error: error.message });
            }
        }
        
        // 发送系统通知
        if (channels.includes('system_notification')) {
            try {
                await systemNotificationService.sendNotification({
                    type: 'audit',
                    title: notificationContent.subject,
                    message: notificationContent.message,
                    data: {
                        auditId: auditId,
                        auditInfo: auditInfo
                    },
                    recipients: auditInfo.auditors
                });
                results.push({ channel: 'system_notification', status: 'success' });
            } catch (error) {
                results.push({ channel: 'system_notification', status: 'failed', error: error.message });
            }
        }
        
        return results;
    }
    
    // 发送审核结果通知
    async sendAuditResultNotification(auditId, auditInfo, result) {
        const notificationContent = {
            subject: '审核结果通知',
            message: '您的操作审核已' + result + '。',
            auditId: auditId,
            auditInfo: auditInfo,
            result: result,
            timestamp: new Date().toISOString()
        };
        
        // 发送给操作发起者
        if (auditInfo.userId) {
            await systemNotificationService.sendNotification({
                type: 'audit_result',
                title: notificationContent.subject,
                message: notificationContent.message + '

审核ID: ' + auditId + '
操作: ' + auditInfo.operation + '
时间: ' + notificationContent.timestamp,
                data: {
                    auditId: auditId,
                    result: result
                },
                recipients: [auditInfo.userId]
            });
        }
    }
    
    // 设置通知渠道
    setNotificationChannels(channels) {
        this.channels = channels;
    }
    
    // 获取通知渠道
    getNotificationChannels() {
        return this.channels;
    }
}

module.exports = new AuditNotification();
