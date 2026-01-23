#!/usr/bin/env python3
"""
Crusoe Cloud Admin Inventory Processor

This script processes the admin node inventory to build hierarchical datacenter structure:
Region → Floor → IB Fabric → Rack → Node → GPU

IMPORTANT: This script only performs READ operations and data processing.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
INPUT_FILE = DATA_DIR / "admin_nodes_inventory.json"
OUTPUT_FILE = DATA_DIR / "datacenter_inventory.json"

# GPU type mapping from slice type to friendly name
GPU_TYPE_MAP = {
    "H100_SXM_80GB": {"name": "H100-SXM-80GB", "gpus_per_node": 8, "vendor": "NVIDIA"},
    "H200_141GB": {"name": "H200-SXM-141GB", "gpus_per_node": 8, "vendor": "NVIDIA"},
    "GB200_186GB": {"name": "GB200-NVL-186GB", "gpus_per_node": 4, "vendor": "NVIDIA"},
    "B200_180GB": {"name": "B200-SXM-180GB", "gpus_per_node": 8, "vendor": "NVIDIA"},
    "L40S_48GB": {"name": "L40S-48GB", "gpus_per_node": 8, "vendor": "NVIDIA"},
    "A100_80GB_SXM": {"name": "A100-SXM-80GB", "gpus_per_node": 8, "vendor": "NVIDIA"},
    "A100_80GB_PCIE": {"name": "A100-PCIe-80GB", "gpus_per_node": 1, "vendor": "NVIDIA"},
    "A100_40GB_PCIE": {"name": "A100-PCIe-40GB", "gpus_per_node": 1, "vendor": "NVIDIA"},
    "MI300X_192GB": {"name": "MI300X-192GB", "gpus_per_node": 8, "vendor": "AMD"},
    "MI355X_288GB": {"name": "MI355X-288GB", "gpus_per_node": 8, "vendor": "AMD"},
    "CPU_ONLY": {"name": "CPU-Only", "gpus_per_node": 0, "vendor": "CPU"},
    "UNKNOWN": {"name": "Unknown", "gpus_per_node": 0, "vendor": "Unknown"},
}

# Location friendly names
LOCATION_NAMES = {
    "icat-m": {"name": "Iceland", "region": "eu-iceland1-a"},
    "nvrm-bsl": {"name": "US West", "region": "us-west1-a"},
    "oh5c-dh": {"name": "US East 2", "region": "us-east2-a"},
    "txdr-iah": {"name": "Dallas", "region": "us-southcentral1-a"},
    "vaeq-cu": {"name": "Virginia", "region": "us-east1-a"},
}

def parse_node_name(node_name):
    """
    Parse node name to extract location, floor, rack, and node number.

    Format: {location}-{floor}-{rack}-{environment}-{type}-{number}
    Examples:
      - icat-m03a-r101-prod-hv-01 → location: icat-m, floor: 03a, rack: r101
      - vaeq-cu12a-r001-prod-hv-01 → location: vaeq-cu, floor: 12a, rack: r001

    Returns:
        dict: Parsed components (location, floor, rack, node_number)
    """
    # Pattern: {location_code}-{floor_code}-{rack}-prod-hv-{number}
    # Location codes are like: icat-m, vaeq-cu, txdr-iah, nvrm-bsl
    # Floor codes are like: m03a, cu12a, iah02a, bsl01a
    # Extract floor identifier (letter+number+letter pattern like m03a, cu12a)

    pattern = r'^([a-z0-9]+)-([a-z0-9]+)-([a-z0-9]+)-(r\d+)-prod-hv-(\d+)$'
    match = re.match(pattern, node_name)

    if match:
        # For 5-part pattern: location1-location2-floor-rack-prod-hv-num
        return {
            "location": f"{match.group(1)}-{match.group(2)}",
            "floor": match.group(3),
            "rack": match.group(4),
            "node_number": match.group(5)
        }

    # Try 4-part pattern: location-floor-rack-prod-hv-num
    pattern2 = r'^([a-z0-9]+)-([a-z0-9]+)-(r\d+)-prod-hv-(\d+)$'
    match2 = re.match(pattern2, node_name)

    if match2:
        return {
            "location": match2.group(1),
            "floor": match2.group(2),
            "rack": match2.group(3),
            "node_number": match2.group(4)
        }

    # Fallback for non-standard names
    parts = node_name.split('-')
    return {
        "location": parts[0] if len(parts) > 0 else "unknown",
        "floor": "unknown",
        "rack": "unknown",
        "node_number": "unknown"
    }

def parse_gpu_type(slice_type):
    """
    Extract GPU type from slice type string.

    Example: SLICE_TYPE_VCPU_88_MEM_480_H100_SXM_80GB_4_IB
    Returns: H100_SXM_80GB
    """
    # Check if this is a CPU-only instance (no GPU in name)
    if not any(gpu in slice_type.upper() for gpu in ['H100', 'H200', 'GB200', 'B200', 'L40S', 'A100', 'A40', 'A6000', 'MI300X', 'MI355X']):
        return "CPU_ONLY"

    # Extract GPU model from slice type using flexible regex patterns
    # Format: SLICE_TYPE_VCPU_X_MEM_Y_<GPU_MODEL>_<SIZE>_<COUNT>_[IB]

    # Try specific patterns
    if 'H200_SXM_141GB' in slice_type:
        return 'H200_141GB'
    elif 'H100_SXM_80GB' in slice_type:
        return 'H100_SXM_80GB'
    elif 'GB200_NVL_186GB' in slice_type or 'GB200_186GB' in slice_type:
        return 'GB200_186GB'
    elif 'B200_SXM_180GB' in slice_type or 'B200_180GB' in slice_type:
        return 'B200_180GB'
    elif 'L40S_PCIE_48GB' in slice_type or 'L40S_48GB' in slice_type:
        return 'L40S_48GB'
    elif 'A100_SXM_80GB' in slice_type:
        return 'A100_80GB_SXM'
    elif 'A100_PCIE_80GB' in slice_type:
        return 'A100_80GB_PCIE'
    elif 'A100_PCIE_40GB' in slice_type:
        return 'A100_40GB_PCIE'
    elif 'MI300X_192GB' in slice_type:
        return 'MI300X_192GB'
    elif 'MI355X_288GB' in slice_type:
        return 'MI355X_288GB'

    return "UNKNOWN"

def calculate_node_gpus(slice_type):
    """Calculate number of GPUs based on slice type."""
    # Extract GPU count from slice type (e.g., _4_IB means 4 GPUs per slice, 2 slices = 8 GPUs)
    gpu_count_match = re.search(r'_(\d+)_IB', slice_type)
    if gpu_count_match:
        gpus_per_slice = int(gpu_count_match.group(1))
        # Most nodes have 2 slices (e.g., H100 nodes have 8 GPUs total, 4 per slice)
        return gpus_per_slice * 2

    # Default to 8 GPUs for standard GPU nodes
    return 8

def process_inventory():
    """
    Process admin node inventory and build hierarchical structure.

    Returns:
        dict: Hierarchical datacenter inventory
    """
    print("\n" + "="*60)
    print("PROCESSING ADMIN NODE INVENTORY (READ-ONLY)")
    print("="*60 + "\n")

    # Load inventory
    print(f"→ Loading inventory from {INPUT_FILE}")
    with open(INPUT_FILE, 'r') as f:
        nodes = json.load(f)

    print(f"  Loaded {len(nodes)} nodes\n")

    # Build hierarchical structure
    hierarchy = defaultdict(lambda: {
        "name": "",
        "region": "",
        "total_nodes": 0,
        "total_gpus": 0,
        "available_nodes": 0,
        "available_gpus": 0,
        "spare_nodes": 0,
        "spare_gpus": 0,
        "hot_spare_nodes": 0,
        "hot_spare_gpus": 0,
        "floors": defaultdict(lambda: {
            "name": "",
            "total_nodes": 0,
            "total_gpus": 0,
            "available_nodes": 0,
            "available_gpus": 0,
            "spare_nodes": 0,
            "spare_gpus": 0,
            "hot_spare_nodes": 0,
            "hot_spare_gpus": 0,
            "racks": defaultdict(lambda: {
                "name": "",
                "total_nodes": 0,
                "total_gpus": 0,
                "available_nodes": 0,
                "available_gpus": 0,
                "spare_nodes": 0,
                "spare_gpus": 0,
                "hot_spare_nodes": 0,
                "hot_spare_gpus": 0,
                "ib_fabrics": defaultdict(lambda: {
                    "id": "",
                    "nodes": []
                })
            })
        })
    })

    # Track global stats
    global_stats = {
        "total_nodes": 0,
        "total_gpus": 0,
        "available_nodes": 0,
        "available_gpus": 0,
        "spare_nodes": 0,
        "spare_gpus": 0,
        "hot_spare_nodes": 0,
        "hot_spare_gpus": 0,
        "gpu_models": defaultdict(lambda: {"total": 0, "available": 0, "spare": 0, "hot_spare": 0}),
        "vendors": defaultdict(lambda: {"total": 0, "available": 0, "spare": 0, "hot_spare": 0}),
    }

    print("→ Processing nodes...")

    for node in nodes:
        # Use location from node data (more reliable than parsing)
        location = node.get("location", "unknown")

        # Parse node name for floor and rack
        parsed = parse_node_name(node["name"])
        floor = parsed["floor"]
        rack = parsed["rack"]

        # Get IB network
        ib_network_id = node.get("ib_network_id", "no-ib")

        # Parse GPU type
        gpu_type_key = parse_gpu_type(node["type"])
        gpu_info = GPU_TYPE_MAP.get(gpu_type_key, {
            "name": "Unknown",
            "gpus_per_node": calculate_node_gpus(node["type"]),
            "vendor": "Unknown"
        })

        # Calculate availability
        is_available = (
            node.get("state") == "Available" and
            node.get("mode") == "AGENT_MODE_NORMAL" and
            int(node.get("avail", 0)) > 0
        )

        # Check if node is spare (unreserved)
        is_reserved = node.get("reserved", "N") == "Y"
        is_spare = is_available and not is_reserved

        # Check if node is hot spare (note field contains "hot spare")
        note = node.get("note", "").lower()
        is_hot_spare = "hot spare" in note or "hot-spare" in note

        # Node details
        node_detail = {
            "id": node["id"],
            "name": node["name"],
            "type": node["type"],
            "gpu_type": gpu_info["name"],
            "gpu_count": gpu_info["gpus_per_node"],
            "vendor": gpu_info["vendor"],
            "state": node.get("state"),
            "mode": node.get("mode"),
            "available_slices": int(node.get("avail", 0)),
            "used_slices": int(node.get("used", 0)) if node.get("used") else 0,
            "is_available": is_available,
            "is_reserved": is_reserved,
            "is_spare": is_spare,
            "is_hot_spare": is_hot_spare,
            "note": node.get("note", ""),
            "ib_network_id": ib_network_id,
            "pod_id": node.get("pod_id", ""),
        }

        # Update hierarchy
        loc_data = hierarchy[location]
        if not loc_data["name"]:
            loc_data["name"] = LOCATION_NAMES.get(location, {}).get("name", location)
            loc_data["region"] = LOCATION_NAMES.get(location, {}).get("region", location)

        floor_data = loc_data["floors"][floor]
        floor_data["name"] = floor

        rack_data = floor_data["racks"][rack]
        rack_data["name"] = rack

        ib_fabric_data = rack_data["ib_fabrics"][ib_network_id]
        ib_fabric_data["id"] = ib_network_id
        ib_fabric_data["nodes"].append(node_detail)

        # Update counts
        gpus = gpu_info["gpus_per_node"]

        # Rack level
        rack_data["total_nodes"] += 1
        rack_data["total_gpus"] += gpus
        if is_available:
            rack_data["available_nodes"] += 1
            rack_data["available_gpus"] += gpus
        if is_spare:
            rack_data["spare_nodes"] += 1
            rack_data["spare_gpus"] += gpus
        if is_hot_spare:
            rack_data["hot_spare_nodes"] += 1
            rack_data["hot_spare_gpus"] += gpus

        # Floor level
        floor_data["total_nodes"] += 1
        floor_data["total_gpus"] += gpus
        if is_available:
            floor_data["available_nodes"] += 1
            floor_data["available_gpus"] += gpus
        if is_spare:
            floor_data["spare_nodes"] += 1
            floor_data["spare_gpus"] += gpus
        if is_hot_spare:
            floor_data["hot_spare_nodes"] += 1
            floor_data["hot_spare_gpus"] += gpus

        # Location level
        loc_data["total_nodes"] += 1
        loc_data["total_gpus"] += gpus
        if is_available:
            loc_data["available_nodes"] += 1
            loc_data["available_gpus"] += gpus
        if is_spare:
            loc_data["spare_nodes"] += 1
            loc_data["spare_gpus"] += gpus
        if is_hot_spare:
            loc_data["hot_spare_nodes"] += 1
            loc_data["hot_spare_gpus"] += gpus

        # Global level
        global_stats["total_nodes"] += 1
        global_stats["total_gpus"] += gpus
        if is_available:
            global_stats["available_nodes"] += 1
            global_stats["available_gpus"] += gpus
        if is_spare:
            global_stats["spare_nodes"] += 1
            global_stats["spare_gpus"] += gpus
        if is_hot_spare:
            global_stats["hot_spare_nodes"] += 1
            global_stats["hot_spare_gpus"] += gpus

        # GPU model stats
        global_stats["gpu_models"][gpu_info["name"]]["total"] += gpus
        if is_available:
            global_stats["gpu_models"][gpu_info["name"]]["available"] += gpus
        if is_spare:
            global_stats["gpu_models"][gpu_info["name"]]["spare"] += gpus
        if is_hot_spare:
            global_stats["gpu_models"][gpu_info["name"]]["hot_spare"] += gpus

        # Vendor stats
        global_stats["vendors"][gpu_info["vendor"]]["total"] += gpus
        if is_available:
            global_stats["vendors"][gpu_info["vendor"]]["available"] += gpus
        if is_spare:
            global_stats["vendors"][gpu_info["vendor"]]["spare"] += gpus
        if is_hot_spare:
            global_stats["vendors"][gpu_info["vendor"]]["hot_spare"] += gpus

    print(f"✓ Processed {global_stats['total_nodes']} nodes with {global_stats['total_gpus']} GPUs")
    print(f"  Available: {global_stats['available_nodes']} nodes, {global_stats['available_gpus']} GPUs")
    print(f"  Spare (Unreserved): {global_stats['spare_nodes']} nodes, {global_stats['spare_gpus']} GPUs")
    print(f"  Hot Spare: {global_stats['hot_spare_nodes']} nodes, {global_stats['hot_spare_gpus']} GPUs\n")

    # Convert defaultdicts to regular dicts for JSON serialization
    def convert_to_dict(obj):
        if isinstance(obj, defaultdict):
            obj = {k: convert_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, dict):
            obj = {k: convert_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            obj = [convert_to_dict(item) for item in obj]
        return obj

    inventory = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "global_stats": convert_to_dict(global_stats),
        "locations": convert_to_dict(hierarchy)
    }

    return inventory

def save_inventory(inventory):
    """Save processed inventory to JSON file."""
    print(f"→ Saving inventory to {OUTPUT_FILE}")

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(inventory, f, indent=2)

    print(f"✓ Inventory saved\n")

def print_summary(inventory):
    """Print summary statistics."""
    print("="*60)
    print("INVENTORY SUMMARY")
    print("="*60)

    stats = inventory["global_stats"]
    print(f"\nGlobal Statistics:")
    print(f"  Total Nodes: {stats['total_nodes']:,}")
    print(f"  Total GPUs: {stats['total_gpus']:,}")
    print(f"  Available Nodes: {stats['available_nodes']:,} ({stats['available_nodes']/stats['total_nodes']*100:.1f}%)")
    print(f"  Available GPUs: {stats['available_gpus']:,} ({stats['available_gpus']/stats['total_gpus']*100:.1f}%)")

    print(f"\nGPU Models:")
    for model, counts in sorted(stats["gpu_models"].items()):
        print(f"  {model}: {counts['total']:,} total, {counts['available']:,} available")

    print(f"\nVendors:")
    for vendor, counts in sorted(stats["vendors"].items()):
        print(f"  {vendor}: {counts['total']:,} total, {counts['available']:,} available")

    print(f"\nLocations:")
    for location_key, location_data in sorted(inventory["locations"].items()):
        print(f"  {location_data['name']}: {location_data['total_nodes']:,} nodes, {location_data['total_gpus']:,} GPUs ({location_data['available_gpus']:,} available)")
        print(f"    Floors: {len(location_data['floors'])}")

def main():
    """Main execution function."""
    try:
        inventory = process_inventory()
        save_inventory(inventory)
        print_summary(inventory)
        print("\n✓ Processing completed successfully\n")

    except Exception as e:
        print(f"✗ Error processing inventory: {e}")
        raise

if __name__ == "__main__":
    main()
