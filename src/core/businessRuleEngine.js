/**
 * MTSCOS AI 系统 - 业务规则引擎
 * 用于管理和执行业务规则
 */

class BusinessRuleEngine {
    constructor() {
        this.rules = [];
    }
    
    // 添加规则
    addRule(rule) {
        this.rules.push(rule);
        console.log("[RuleEngine] 添加规则: " + rule.name);
    }
    
    // 执行规则
    async executeRules(data, context = {}) {
        const results = [];
        
        for (const rule of this.rules) {
            try {
                // 检查规则条件
                if (await this.evaluateCondition(rule.condition, data, context)) {
                    // 执行规则动作
                    const result = await this.executeAction(rule.action, data, context);
                    results.push({
                        rule: rule.name,
                        result: result,
                        status: "success"
                    });
                }
            } catch (error) {
                results.push({
                    rule: rule.name,
                    error: error.message,
                    status: "failed"
                });
            }
        }
        
        return results;
    }
    
    // 评估规则条件
    async evaluateCondition(condition, data, context) {
        if (typeof condition === "function") {
            return await condition(data, context);
        } else if (typeof condition === "string") {
            // 简单的条件表达式支持
            try {
                return eval(condition);
            } catch (error) {
                console.error("[RuleEngine] 条件表达式执行失败: " + condition, error);
                return false;
            }
        }
        return false;
    }
    
    // 执行规则动作
    async executeAction(action, data, context) {
        if (typeof action === "function") {
            return await action(data, context);
        } else if (typeof action === "string") {
            // 简单的动作表达式支持
            try {
                return eval(action);
            } catch (error) {
                console.error("[RuleEngine] 动作表达式执行失败: " + action, error);
                return null;
            }
        }
        return null;
    }
    
    // 获取规则列表
    getRules() {
        return this.rules;
    }
    
    // 根据名称查找规则
    findRule(name) {
        return this.rules.find(function(rule) { return rule.name === name; });
    }
    
    // 删除规则
    removeRule(name) {
        const index = this.rules.findIndex(function(rule) { return rule.name === name; });
        if (index > -1) {
            this.rules.splice(index, 1);
            console.log("[RuleEngine] 删除规则: " + name);
            return true;
        }
        return false;
    }
}

module.exports = BusinessRuleEngine;
