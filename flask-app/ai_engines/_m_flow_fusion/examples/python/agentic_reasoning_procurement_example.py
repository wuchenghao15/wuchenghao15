"""Agentic reasoning: use M-flow as a memory backend for an AI procurement agent."""

import asyncio
import m_flow
from m_flow.shared.logging_utils import setup_logging, ERROR
from m_flow.api.v1.search import RecallMode


SUPPLIER_CATALOG = (
    "TechParts Inc supplies microcontrollers (MCU-X200 at $4.50/unit, MCU-X300 at $7.20/unit) "
    "and sensors (TEMP-S1 at $2.10, PRES-S2 at $3.80). Lead time is 2-4 weeks. "
    "Minimum order quantity is 500 units. Quality rating: A."
)

PURCHASE_HISTORY = (
    "Q1 2024: ordered 2000x MCU-X200 from TechParts — delivered on time, 0.1% defect rate. "
    "Q2 2024: ordered 1500x TEMP-S1 from TechParts — 3 days late, 0.3% defect rate. "
    "Q3 2024: ordered 800x PRES-S2 from SensorWorld — on time, 0.05% defect rate, $3.60/unit."
)

PROCUREMENT_POLICY = (
    "Preferred suppliers must have quality rating A or B. "
    "Single-source orders above $10,000 require dual-quote. "
    "Lead times over 3 weeks trigger safety stock alert."
)


class ProcurementAgent:
    """Simulates an AI agent that queries M-flow for procurement decisions."""

    async def initialize(self):
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)

        await m_flow.add(data=SUPPLIER_CATALOG, dataset_name="supplier_catalog")
        await m_flow.add(data=PURCHASE_HISTORY, dataset_name="purchase_history")
        await m_flow.add(data=PROCUREMENT_POLICY, dataset_name="procurement_policies")
        await m_flow.memorize()
        print("Memory initialized with 3 knowledge domains.\n")

    async def query(self, question: str, categories=None):
        print(f"Agent query: {question}")
        datasets = categories or ["supplier_catalog", "purchase_history", "procurement_policies"]
        results = await m_flow.search(
            query_type=RecallMode.TRIPLET_COMPLETION,
            query_text=question,
            datasets=datasets,
        )
        for r in results:
            print(f"  → {r}")
        return results

    async def evaluate_supplier(self, part_number: str):
        print(f"\n--- Evaluating supplier for {part_number} ---")
        await self.query(f"Which suppliers offer {part_number} and at what price?", ["supplier_catalog"])
        await self.query(f"What is the delivery history for {part_number}?", ["purchase_history"])
        await self.query(f"Are there any policy constraints for ordering {part_number}?", ["procurement_policies"])


async def run():
    agent = ProcurementAgent()
    await agent.initialize()

    # Scenario: need to order microcontrollers
    await agent.evaluate_supplier("MCU-X200")

    # Scenario: cross-domain reasoning
    print("\n--- Cross-domain analysis ---")
    await agent.query("Compare TechParts and SensorWorld on delivery reliability")
    await agent.query("What parts have defect rates above 0.2%?")


if __name__ == "__main__":
    setup_logging(log_level=ERROR)
    asyncio.run(run())
