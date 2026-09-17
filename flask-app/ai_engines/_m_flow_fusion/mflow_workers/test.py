"""
分布式计算测试模块
验证Modal分布式任务执行
"""

from __future__ import annotations

from modal import App

app = App("m_flow_distributed_test")

_BATCH_SIZE = 10
_TEST_RANGE = 100


@app.function()
def compute_sum(nums: list) -> int:
    """计算数字列表的和"""
    return sum(nums)


@app.local_entrypoint()
def main():
    """测试入口"""
    nums = list(range(_TEST_RANGE))

    # 本地计算
    local_result = compute_sum.local(nums=nums)
    print(f"本地计算结果: {local_result}")

    # 分布式计算
    batches = [nums[i : i + _BATCH_SIZE] for i in range(0, len(nums), _BATCH_SIZE)]
    distributed_result = sum(compute_sum.map(batches))
    print(f"分布式计算结果: {distributed_result}")
