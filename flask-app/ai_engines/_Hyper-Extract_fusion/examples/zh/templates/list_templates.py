"""
List Templates - 列出所有可用的预设模板

Usage:
    python examples/templates/list_templates.py
"""

import yaml
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent


def list_templates():
    mapping_file = Path(__file__).parent / "templates_mapping.yaml"

    with open(mapping_file, "r", encoding="utf-8") as f:
        mappings = yaml.safe_load(f)

    print("\n" + "=" * 80)
    print("📋 Hyper-Extract Preset Templates")
    print("=" * 80)

    for domain, templates in mappings.items():
        if domain in ["test_data_root", "template_root"]:
            continue

        print(f"\n【{domain.upper()} 领域】 ({len(templates)} templates)")
        print("-" * 60)

        for name, info in templates.items():
            template_type = info.get("type", "unknown")
            description = info.get("description", "N/A")
            template_path = info.get("template", "")
            input_path = info.get("input", "")

            print(f"  • {name}")
            print(f"    Type: {template_type}")
            print(f"    Description: {description}")
            print(f"    Template: {template_path}.yaml")
            print(f"    Test Data: tests/test_data/zh/{input_path}")

    print("\n" + "=" * 80)
    print("\n使用方式:")
    print("  python examples/templates/run_template.py -d <domain> -t <template_name>")
    print("\n示例:")
    print("  python examples/templates/run_template.py -d finance -t earnings_summary")
    print("  python examples/templates/run_template.py -d general -t graph")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    list_templates()
