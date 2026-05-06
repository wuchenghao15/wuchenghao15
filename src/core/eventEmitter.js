/**
 * MTSCOS AI 系统 - 事件驱动架构支持
 * 用于系统组件间的事件通信
 */

class EventEmitter {
    constructor() {
        this.events = {};
        this.maxListeners = 10;
    }
    
    // 设置最大监听器数量
    setMaxListeners(n) {
        this.maxListeners = n;
        return this;
    }
    
    // 获取最大监听器数量
    getMaxListeners() {
        return this.maxListeners;
    }
    
    // 监听事件
    on(eventName, listener) {
        if (!this.events[eventName]) {
            this.events[eventName] = [];
        }
        
        // 检查监听器数量
        if (this.events[eventName].length >= this.maxListeners) {
            console.warn("[EventEmitter] 事件 " + eventName + " 的监听器数量超过最大值 " + this.maxListeners);
        }
        
        this.events[eventName].push(listener);
        return this;
    }
    
    // 监听事件（只触发一次）
    once(eventName, listener) {
        const onceListener = function() {
            this.removeListener(eventName, onceListener);
            listener.apply(this, arguments);
        }.bind(this);
        
        onceListener.listener = listener;
        this.on(eventName, onceListener);
        return this;
    }
    
    // 移除事件监听器
    removeListener(eventName, listener) {
        if (!this.events[eventName]) {
            return this;
        }
        
        this.events[eventName] = this.events[eventName].filter(function(l) {
            return l !== listener && l.listener !== listener;
        });
        
        return this;
    }
    
    // 移除所有事件监听器
    removeAllListeners(eventName) {
        if (eventName) {
            delete this.events[eventName];
        } else {
            this.events = {};
        }
        return this;
    }
    
    // 获取事件监听器数量
    listenerCount(eventName) {
        return this.events[eventName] ? this.events[eventName].length : 0;
    }
    
    // 获取事件监听器列表
    listeners(eventName) {
        return this.events[eventName] ? this.events[eventName].slice() : [];
    }
    
    // 触发事件
    emit(eventName) {
        if (!this.events[eventName]) {
            return false;
        }
        
        const args = Array.prototype.slice.call(arguments, 1);
        for (let i = 0; i < this.events[eventName].length; i++) {
            this.events[eventName][i].apply(this, args);
        }
        
        return true;
    }
    
    // 获取所有事件名称
    eventNames() {
        return Object.keys(this.events);
    }
}

module.exports = EventEmitter;
