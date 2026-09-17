#!/usr/bin/env python3
# m_flow/eval/__main__.py
"""
P7-6: Evaluation CLI Entry Point

Usage:
    python -m m_flow.eval --dataset procedural_eval_v1.jsonl
    python -m m_flow.eval --dataset procedural_eval_v1.jsonl --compare-baseline
    python -m m_flow.eval --dataset procedural_eval_v1.jsonl --save-baseline
"""

import argparse
import asyncio
import os
import sys


def get_datasets_dir() -> str:
    """Get datasets directory"""
    return os.path.join(os.path.dirname(__file__), "datasets")


def get_baselines_dir() -> str:
    """Get baselines directory"""
    return os.path.join(os.path.dirname(__file__), "baselines")


def progress_callback(current: int, total: int, case_id: str):
    """Progress callback"""
    pct = current / total * 100
    print(f"\r[{current}/{total}] ({pct:.0f}%) Running: {case_id[:30]}...", end="", flush=True)


async def main_async(args):
    from m_flow.eval.config import EvalConfig, EvalSetup
    from m_flow.eval.loader import CaseLoader
    from m_flow.eval.runner import EvalRunner
    from m_flow.eval.report import EvalReport

    # Parse dataset path
    if os.path.isabs(args.dataset):
        dataset_path = args.dataset
    else:
        dataset_path = os.path.join(get_datasets_dir(), args.dataset)

    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found: {dataset_path}")
        sys.exit(1)

    print(f"[STATS] Loading dataset: {dataset_path}")

    # Load dataset
    loader = CaseLoader(dataset_path)
    cases = loader.load()

    if loader.errors:
        print("[WARN] Dataset warnings:")
        for err in loader.errors[:5]:
            print(f"   {err}")

    stats = loader.get_stats()
    print(f"   Total cases: {stats['total']}")
    for k, v in stats.items():
        if k != "total":
            print(f"   - {k}: {v}")

    # Load configuration
    if args.config:
        config = EvalConfig.load(args.config)
    else:
        config = EvalConfig.from_env()
        config.name = args.name or "default"

    print(f"\n[CONFIG] Config: {config.name}")

    # Prepare environment
    setup = EvalSetup(config)
    await setup.prepare()

    # Run evaluation
    print("\n[RUN] Running evaluation...")
    runner = EvalRunner(config)

    results = await runner.run_all(
        cases,
        concurrency=args.concurrency,
        progress_callback=progress_callback if not args.quiet else None,
    )

    print()  # Newline

    # Load baseline (if comparison needed)
    baseline = None
    if args.compare_baseline:
        baseline_path = args.compare_baseline
        if not os.path.isabs(baseline_path):
            baseline_path = os.path.join(get_baselines_dir(), baseline_path)

        if os.path.exists(baseline_path):
            print(f"[STATS] Loading baseline: {baseline_path}")
            baseline = EvalReport.load(baseline_path)
        else:
            print(f"[WARN] Baseline not found: {baseline_path}")

    # Generate report
    print("\n[NOTE] Generating report...")
    report = EvalReport.build(
        cases=cases,
        results=results,
        config=config,
        dataset_path=dataset_path,
        baseline=baseline,
    )

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"[STATS] Evaluation Results: {config.name}")
    print(f"{'=' * 60}")

    if report.metrics:
        print("\nOverall Metrics:")
        print(f"   Recall@1: {report.metrics.overall.recall_at_1:.2%}")
        print(f"   Recall@3: {report.metrics.overall.recall_at_3:.2%}")
        print(f"   FP Inject Rate: {report.metrics.overall.fp_inject_rate:.2%}")
        print(f"   Context Completeness: {report.metrics.overall.ctx_completeness:.2%}")
        print(f"   Trigger Accuracy: {report.metrics.overall.trigger_accuracy:.2%}")

        print("\nMetrics by Type:")
        for t, m in report.metrics.by_type.items():
            print(f"   {t}: n={m.n}, Recall@1={m.recall_at_1:.2%}, Recall@3={m.recall_at_3:.2%}")

    # Show baseline comparison
    if report.baseline_name:
        print(f"\nBaseline Comparison ({report.baseline_name}):")
        for k, v in report.baseline_delta.items():
            sign = "+" if v > 0 else ""
            status = "[OK]" if v >= 0 else "[WARN]"
            if k == "fp_inject_rate":
                status = "[OK]" if v <= 0 else "[WARN]"
            print(f"   {status} {k}: {sign}{v:.2%}")

        if report.regressions:
            print("\n[WARN] Regression Detection:")
            for r in report.regressions:
                print(f"   - {r}")

    # Show failure buckets
    if any(v > 0 for v in report.failure_buckets.values()):
        print("\nFailure Buckets:")
        for bucket, count in sorted(report.failure_buckets.items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"   {bucket}: {count}")

    # Show top failure cases
    if report.failures:
        print("\nTop Failure Cases (trace_id can be used for debugging):")
        for f in report.failures[:10]:
            print(f"   [{f.id}] {f.buckets} -> trace: {f.trace_id}")

    # Save report
    output_dir = args.output or "."
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, f"eval_report_{config.name}.json")
    md_path = os.path.join(output_dir, f"eval_report_{config.name}.md")

    report.save_json(json_path)
    report.save_markdown(md_path)

    print("\n📄 Report saved:")
    print(f"   JSON: {json_path}")
    print(f"   Markdown: {md_path}")

    # Save as baseline (if needed)
    if args.save_baseline:
        baseline_path = args.save_baseline
        if not os.path.isabs(baseline_path):
            baseline_path = os.path.join(get_baselines_dir(), baseline_path)

        report.save_json(baseline_path)
        print(f"\n[OK] Saved as baseline: {baseline_path}")

    # CI gate check
    if args.gate:
        if report.regressions:
            print(f"\n[FAIL] CI Gate FAILED: {len(report.regressions)} regressions detected")
            sys.exit(1)
        else:
            print("\n[OK] CI Gate PASSED")
            sys.exit(0)

    print(f"\n{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Mflow Evaluation System (P7)")

    parser.add_argument(
        "--dataset",
        "-d",
        required=True,
        help="Dataset file path (JSONL format)",
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Config file path (JSON format)",
    )
    parser.add_argument(
        "--name",
        "-n",
        default="default",
        help="Evaluation name",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for reports",
    )
    parser.add_argument(
        "--compare-baseline",
        "-b",
        help="Baseline file to compare against",
    )
    parser.add_argument(
        "--save-baseline",
        "-s",
        help="Save current results as baseline",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Concurrency level (1 recommended for stability)",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Enable CI gate mode (exit 1 on regression)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode (no progress output)",
    )

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
