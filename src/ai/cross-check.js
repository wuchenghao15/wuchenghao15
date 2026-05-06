/**
 * MTSCOS AI 系统 - AI交叉检查模块
 * 结合本地和云端AI引擎的分析结果
 */

class AICrossCheck {
    constructor(localAI, cloudAI) {
        this.localAI = localAI;
        this.cloudAI = cloudAI;
    }

    // 交叉检查分析结果
    async crossCheckAnalysis(input, context) {
        console.log('开始AI交叉检查...');
        
        // 并行执行本地和云端AI分析
        const [localResult, cloudResult] = await Promise.all([
            this.localAI.analyze(input, context),
            this.cloudAI.analyze(input, context)
        ]);
        
        // 比较结果
        const comparison = this.compareResults(localResult, cloudResult);
        
        // 生成最终结果
        const finalResult = this.generateFinalResult(localResult, cloudResult, comparison);
        
        return {
            localResult,
            cloudResult,
            comparison,
            finalResult
        };
    }

    // 比较结果
    compareResults(localResult, cloudResult) {
        const similarity = this.calculateSimilarity(localResult, cloudResult);
        const hasConflict = this.checkConflicts(localResult, cloudResult);
        
        return {
            similarity,
            hasConflict,
            conflictDetails: hasConflict ? this.getConflictDetails(localResult, cloudResult) : []
        };
    }

    // 计算相似度
    calculateSimilarity(result1, result2) {
        // 简单的相似度计算，实际项目中可以使用更复杂的算法
        if (!result1 || !result2) return 0;
        
        const keys1 = Object.keys(result1);
        const keys2 = Object.keys(result2);
        const commonKeys = keys1.filter(key => keys2.includes(key));
        
        let matchingKeys = 0;
        commonKeys.forEach(key => {
            if (JSON.stringify(result1[key]) === JSON.stringify(result2[key])) {
                matchingKeys++;
            }
        });
        
        return commonKeys.length > 0 ? (matchingKeys / commonKeys.length) * 100 : 0;
    }

    // 检查冲突
    checkConflicts(result1, result2) {
        // 检查关键字段是否存在冲突
        const criticalFields = ['riskLevel', 'severity', 'recommendation'];
        
        for (const field of criticalFields) {
            if (result1[field] !== result2[field]) {
                return true;
            }
        }
        
        return false;
    }

    // 获取冲突详情
    getConflictDetails(result1, result2) {
        const conflicts = [];
        const criticalFields = ['riskLevel', 'severity', 'recommendation'];
        
        for (const field of criticalFields) {
            if (result1[field] !== result2[field]) {
                conflicts.push({
                    field,
                    localValue: result1[field],
                    cloudValue: result2[field]
                });
            }
        }
        
        return conflicts;
    }

    // 生成最终结果
    generateFinalResult(localResult, cloudResult, comparison) {
        if (comparison.similarity > 80) {
            // 结果高度一致，返回任意一个
            return localResult;
        } else if (comparison.hasConflict) {
            // 存在冲突，返回包含冲突信息的结果
            return {
                ...localResult,
                conflicts: comparison.conflictDetails,
                conflictResolved: false,
                crossCheckInfo: comparison
            };
        } else {
            // 结果有差异但无冲突，合并结果
            return {
                ...localResult,
                ...cloudResult,
                merged: true,
                crossCheckInfo: comparison
            };
        }
    }
}

module.exports = AICrossCheck;
