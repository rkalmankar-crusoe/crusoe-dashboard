#!/usr/bin/env python3
"""
Crusoe Cloud Capacity Query Tool

This script helps find available GPU capacity for POCs by querying
the hierarchical datacenter inventory.

IMPORTANT: This script only performs READ operations.
"""

import json
from pathlib import Path
from collections import defaultdict

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
INVENTORY_FILE = DATA_DIR / "datacenter_inventory.json"

def load_inventory():
    """Load the datacenter inventory."""
    with open(INVENTORY_FILE, 'r') as f:
        return json.load(f)

def find_available_capacity(
    gpu_type=None,
    min_gpus=None,
    location=None,
    floor=None,
    ib_fabric=None
):
    """
    Find available GPU capacity based on filters.

    Args:
        gpu_type (str): GPU model to filter by (e.g., "H100-SXM-80GB")
        min_gpus (int): Minimum number of GPUs needed
        location (str): Location to filter by (e.g., "Iceland", "icat-m")
        floor (str): Floor to filter by (e.g., "m03a")
        ib_fabric (str): IB fabric ID to filter by

    Returns:
        list: List of available nodes matching the criteria
    """
    inventory = load_inventory()
    available_nodes = []

    for loc_key, loc_data in inventory["locations"].items():
        # Filter by location
        if location and location.lower() not in [loc_key.lower(), loc_data["name"].lower()]:
            continue

        for floor_key, floor_data in loc_data["floors"].items():
            # Filter by floor
            if floor and floor.lower() != floor_key.lower():
                continue

            for rack_key, rack_data in floor_data["racks"].items():
                for ib_key, ib_data in rack_data["ib_fabrics"].items():
                    # Filter by IB fabric
                    if ib_fabric and ib_fabric != ib_key:
                        continue

                    for node in ib_data["nodes"]:
                        # Only include available nodes
                        if not node["is_available"]:
                            continue

                        # Filter by GPU type
                        if gpu_type and gpu_type.lower() != node["gpu_type"].lower():
                            continue

                        # Filter by minimum GPUs
                        if min_gpus and node["gpu_count"] < min_gpus:
                            continue

                        # Add location context
                        node["_location"] = loc_data["name"]
                        node["_floor"] = floor_key
                        node["_rack"] = rack_key

                        available_nodes.append(node)

    return available_nodes

def summarize_capacity(nodes):
    """Summarize capacity by location, GPU type, and IB fabric."""
    summary = {
        "total_nodes": len(nodes),
        "total_gpus": sum(n["gpu_count"] for n in nodes),
        "by_location": defaultdict(lambda: {"nodes": 0, "gpus": 0}),
        "by_gpu_type": defaultdict(lambda: {"nodes": 0, "gpus": 0}),
        "by_ib_fabric": defaultdict(lambda: {"nodes": 0, "gpus": 0, "location": "", "floor": ""}),
    }

    for node in nodes:
        location = node["_location"]
        gpu_type = node["gpu_type"]
        ib_fabric = node["ib_network_id"]
        gpus = node["gpu_count"]

        summary["by_location"][location]["nodes"] += 1
        summary["by_location"][location]["gpus"] += gpus

        summary["by_gpu_type"][gpu_type]["nodes"] += 1
        summary["by_gpu_type"][gpu_type]["gpus"] += gpus

        summary["by_ib_fabric"][ib_fabric]["nodes"] += 1
        summary["by_ib_fabric"][ib_fabric]["gpus"] += gpus
        summary["by_ib_fabric"][ib_fabric]["location"] = location
        summary["by_ib_fabric"][ib_fabric]["floor"] = node["_floor"]

    return summary

def print_capacity_summary(summary):
    """Print capacity summary in a readable format."""
    print(f"\n{'='*60}")
    print(f"AVAILABLE CAPACITY SUMMARY")
    print(f"{'='*60}")

    print(f"\nTotal: {summary['total_nodes']} nodes, {summary['total_gpus']} GPUs")

    print(f"\nBy Location:")
    for location, data in sorted(summary["by_location"].items()):
        print(f"  {location}: {data['nodes']} nodes, {data['gpus']} GPUs")

    print(f"\nBy GPU Type:")
    for gpu_type, data in sorted(summary["by_gpu_type"].items()):
        print(f"  {gpu_type}: {data['nodes']} nodes, {data['gpus']} GPUs")

    print(f"\nBy IB Fabric (Top 10):")
    fabrics = sorted(
        summary["by_ib_fabric"].items(),
        key=lambda x: x[1]["gpus"],
        reverse=True
    )[:10]

    for fabric_id, data in fabrics:
        fabric_short = fabric_id[:16] + "..." if len(fabric_id) > 16 else fabric_id
        print(f"  {fabric_short}")
        print(f"    Location: {data['location']}, Floor: {data['floor']}")
        print(f"    Nodes: {data['nodes']}, GPUs: {data['gpus']}")

def print_node_list(nodes, limit=20):
    """Print list of available nodes."""
    print(f"\n{'='*60}")
    print(f"AVAILABLE NODES (showing {min(limit, len(nodes))} of {len(nodes)})")
    print(f"{'='*60}\n")

    for i, node in enumerate(nodes[:limit]):
        print(f"{i+1}. {node['name']}")
        print(f"   Location: {node['_location']}, Floor: {node['_floor']}, Rack: {node['_rack']}")
        print(f"   GPU: {node['gpu_type']} x{node['gpu_count']}")
        print(f"   State: {node['state']}, Mode: {node['mode']}")
        print(f"   Available Slices: {node['available_slices']}")
        print()

def main():
    """Main execution with example queries."""
    print("\n" + "="*60)
    print("CRUSOE CLOUD CAPACITY QUERY TOOL")
    print("="*60)

    # Example 1: Find all available H100 nodes
    print("\n[Query 1] All available H100-SXM-80GB nodes:")
    nodes = find_available_capacity(gpu_type="H100-SXM-80GB")
    summary = summarize_capacity(nodes)
    print_capacity_summary(summary)

    # Example 2: Find available H200 nodes in Iceland
    print("\n" + "="*60)
    print("\n[Query 2] Available H200 nodes in Iceland:")
    nodes = find_available_capacity(gpu_type="H200-SXM-141GB", location="Iceland")
    summary = summarize_capacity(nodes)
    print_capacity_summary(summary)
    print_node_list(nodes, limit=10)

    # Example 3: Find any available nodes with at least 8 GPUs
    print("\n" + "="*60)
    print("\n[Query 3] Available nodes with 8+ GPUs (any type):")
    nodes = find_available_capacity(min_gpus=8)
    summary = summarize_capacity(nodes)
    print_capacity_summary(summary)

    # Example 4: Find available L40S nodes (good for inference)
    print("\n" + "="*60)
    print("\n[Query 4] Available L40S-48GB nodes:")
    nodes = find_available_capacity(gpu_type="L40S-48GB")
    summary = summarize_capacity(nodes)
    print_capacity_summary(summary)
    print_node_list(nodes, limit=10)

    # Example 5: Find available GB200 superchips
    print("\n" + "="*60)
    print("\n[Query 5] Available GB200-NVL-186GB nodes:")
    nodes = find_available_capacity(gpu_type="GB200-NVL-186GB")
    summary = summarize_capacity(nodes)
    print_capacity_summary(summary)
    print_node_list(nodes, limit=10)

    print("\n" + "="*60)
    print("Query examples completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
