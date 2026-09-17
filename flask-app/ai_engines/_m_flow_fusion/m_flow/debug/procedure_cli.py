#!/usr/bin/env python3
# m_flow/debug/procedure_cli.py
"""
P6-4: Procedure CLI

Reads Procedure and its structure from the graph database and displays it.

Usage:
    python -m m_flow.debug.procedure_cli --procedure_id <id>
    python -m m_flow.debug.procedure_cli --list  # List all procedures
"""

import argparse
import asyncio
import json


async def get_graph_provider():
    """Get graph engine."""
    from m_flow.adapters.graph import get_graph_provider as _get_ge

    return await _get_ge()


async def list_procedures():
    """List all Procedures."""
    ge = await get_graph_provider()

    q = """
    MATCH (p:Node)
    WHERE p.type = 'Procedure'
    RETURN p.id AS id, p.name AS name, p.properties AS properties
    ORDER BY p.name
    """
    rows = await ge.query(q)

    if not rows:
        print("No procedures found.")
        return

    print(f"\n[LIST] Procedures ({len(rows)}):")
    print("-" * 80)

    for row in rows:
        props = row.get("properties", {}) or {}
        if isinstance(props, str):
            try:
                props = json.loads(props)
            except (json.JSONDecodeError, TypeError):
                props = {}

        status = props.get("status", "active")
        version = props.get("version", 1)
        signature = props.get("signature") or props.get("procedure_key", "")

        status_emoji = "[OK]" if status == "active" else "[WARN]"
        print(f"   {status_emoji} {row.get('name', '')[:40]:<40} v{version} {signature[:20]}")
        print(f"      id: {row.get('id')}")


async def view_procedure(procedure_id: str):
    """View detailed structure of a single Procedure."""
    ge = await get_graph_provider()

    # Read procedure
    q_proc = f"""
    MATCH (p:Node)
    WHERE p.id = '{procedure_id}'
    RETURN p.id AS id, p.name AS name, p.type AS type, p.properties AS properties
    """
    rows = await ge.query(q_proc)

    if not rows:
        print(f"Procedure not found: {procedure_id}")
        return

    p = rows[0]
    props = p.get("properties", {}) or {}
    if isinstance(props, str):
        try:
            props = json.loads(props)
        except (json.JSONDecodeError, TypeError):
            props = {}

    print(f"\n[LIST] Procedure: {p.get('name', '')}")
    print("=" * 80)
    print(f"   id: {p.get('id')}")
    print(f"   type: {p.get('type')}")
    print(f"   procedure_key: {props.get('signature') or props.get('procedure_key', '')}")
    print(f"   version: {props.get('version', 1)}")
    print(f"   status: {props.get('status', 'active')}")
    print(f"   confidence: {props.get('confidence', 'high')}")
    print()
    print("Summary:")
    print("-" * 40)
    print(props.get("summary", "")[:1200])
    print()

    # Read key points (new: direct Procedure→Point)
    q_key_points = f"""
    MATCH (p:Node)-[r:EDGE]->(pt:Node)
    WHERE p.id = '{procedure_id}' AND pt.type = 'ProcedureStepPoint'
    RETURN pt.id AS id, pt.name AS name, pt.properties AS properties, r.edge_text AS edge_text
    """
    key_pts = await ge.query(q_key_points)

    if key_pts:
        print(f"\n[KEY_POINT] Key Points ({len(key_pts)}):")
        print("-" * 40)
        for i, row in enumerate(key_pts[:50], 1):
            pprops = row.get("properties", {}) or {}
            if isinstance(pprops, str):
                try:
                    pprops = json.loads(pprops)
                except (json.JSONDecodeError, TypeError):
                    pprops = {}
            idx = pprops.get("point_index") or pprops.get("step_number") or "?"
            et = (row.get("edge_text") or "")[:60]
            print(f"   {i:>2}. [{idx}] {row.get('name', '')[:50]}  edge: {et}")

    # Read context points (new: direct Procedure→Point)
    q_ctx_points = f"""
    MATCH (p:Node)-[r:EDGE]->(pt:Node)
    WHERE p.id = '{procedure_id}' AND pt.type = 'ProcedureContextPoint'
    RETURN pt.id AS id, pt.name AS name, pt.properties AS properties, r.edge_text AS edge_text
    """
    ctx_pts = await ge.query(q_ctx_points)

    if ctx_pts:
        print(f"\n[CTX_POINT] Context Points ({len(ctx_pts)}):")
        print("-" * 40)
        for i, row in enumerate(ctx_pts[:50], 1):
            pprops = row.get("properties", {}) or {}
            if isinstance(pprops, str):
                try:
                    pprops = json.loads(pprops)
                except (json.JSONDecodeError, TypeError):
                    pprops = {}
            ct = pprops.get("point_type") or pprops.get("cue_type") or "?"
            et = (row.get("edge_text") or "")[:60]
            print(f"   {i:>2}. [{ct}] {row.get('name', '')[:50]}  edge: {et}")

    # Legacy fallback: Check for Pack-based structure
    if not key_pts and not ctx_pts:
        q_packs = f"""
        MATCH (p:Node)-[r:EDGE]->(k:Node)
        WHERE p.id = '{procedure_id}'
          AND (k.type = 'ProcedureStepsPack' OR k.type = 'ProcedureContextPack')
        RETURN k.id AS id, k.type AS type, k.properties AS properties
        """
        packs = await ge.query(q_packs)
        if packs:
            print("\n[LEGACY] Pack-based structure detected (old data):")
            for row in packs:
                kprops = row.get("properties", {}) or {}
                if isinstance(kprops, str):
                    try:
                        kprops = json.loads(kprops)
                    except (json.JSONDecodeError, TypeError):
                        kprops = {}
                print(f"   {row.get('type')}: {(kprops.get('anchor_text') or '')[:200]}")

    print("\n" + "=" * 80)


def main():
    ap = argparse.ArgumentParser(description="Mflow Procedure CLI")
    ap.add_argument("--procedure_id", help="Procedure ID to view")
    ap.add_argument("--list", action="store_true", help="List all procedures")
    args = ap.parse_args()

    if args.list:
        asyncio.run(list_procedures())
        return

    if args.procedure_id:
        asyncio.run(view_procedure(args.procedure_id))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
