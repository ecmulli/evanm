import re
import os
from pathlib import Path

import networkx as nx
from pyvis.network import Network

G = nx.DiGraph()

# ---------- Define matches as nodes ----------
# id, label, day, time_order, bracket, lane (row index to separate winners/cons)

nodes = [
    # 3.5 bracket - Saturday
    ("35_Sat_14_M1", "3.5 Sat 2:00 – M1", "Sat", 1, "3.5", "main"),
    ("35_Sat_1830_M2", "3.5 Sat 6:30 – M2", "Sat", 3, "3.5", "main"),
    # 4.0 bracket - Saturday
    ("40_Sat_17_M1", "4.0 Sat 5:00 – M1", "Sat", 2, "4.0", "main"),
    ("40_Sat_20_C5", "4.0 Sat 8:00 – C5", "Sat", 4, "4.0", "cons"),
    # 3.5 bracket - Sunday
    ("35_Sun_0930_SF", "3.5 Sun 9:30 – SF (M3)", "Sun", 6, "3.5", "main"),
    ("35_Sun_0930_C6", "3.5 Sun 9:30 – C6", "Sun", 6, "3.5", "cons"),
    ("35_Sun_1230_C7", "3.5 Sun 12:30 – C7", "Sun", 7, "3.5", "cons"),
    ("35_Sun_17_F", "3.5 Sun 5:00 – Final", "Sun", 9, "3.5", "main"),
    ("35_Sun_17_3P", "3.5 Sun 5:00 – 3rd", "Sun", 9, "3.5", "main"),
    ("35_Sun_17_CF", "3.5 Sun 5:00 – Cons F", "Sun", 9, "3.5", "cons"),
    # 4.0 bracket - Sunday
    ("40_Sun_08_W2", "4.0 Sun 8:00 – W2", "Sun", 5, "4.0", "main"),
    ("40_Sun_11_C6", "4.0 Sun 11:00 – C6", "Sun", 7, "4.0", "cons"),
    ("40_Sun_1230_C7", "4.0 Sun 12:30 – C7", "Sun", 8, "4.0", "cons"),
    ("40_Sun_1530_F", "4.0 Sun 3:30 – Final/3P", "Sun", 8, "4.0", "main"),
]

for nid, label, day, torder, bracket, lane in nodes:
    G.add_node(
        nid,
        label=label,
        day=day,
        torder=torder,
        bracket=bracket,
        lane=lane,
    )

# ---------- Add edges for outcomes (Win/Lose) ----------

# 3.5 bracket
G.add_edge("35_Sat_14_M1", "35_Sat_1830_M2", outcome="W")  # win -> Match 2
G.add_edge("35_Sat_14_M1", "35_Sun_0930_C6", outcome="L")  # lose -> Cons 9:30

G.add_edge("35_Sat_1830_M2", "35_Sun_0930_SF", outcome="W")  # win -> Semi
# lose = done (no edge)

G.add_edge("35_Sun_0930_SF", "35_Sun_17_F", outcome="W")  # win -> Final
G.add_edge("35_Sun_0930_SF", "35_Sun_17_3P", outcome="L")  # lose -> 3rd place

G.add_edge("35_Sun_0930_C6", "35_Sun_1230_C7", outcome="W")  # cons win -> 12:30
# lose = done

G.add_edge("35_Sun_1230_C7", "35_Sun_17_CF", outcome="W")  # cons win -> cons final
# lose = done

# 4.0 bracket
G.add_edge("40_Sat_17_M1", "40_Sun_08_W2", outcome="W")  # win -> Sun 8:00
G.add_edge("40_Sat_17_M1", "40_Sat_20_C5", outcome="L")  # lose -> Sat 8:00 cons

G.add_edge("40_Sat_20_C5", "40_Sun_11_C6", outcome="W")  # cons win -> 11:00
# lose = done

G.add_edge("40_Sun_11_C6", "40_Sun_1230_C7", outcome="W")  # cons win -> 12:30
# lose = done

# winners bracket deciding final vs 3rd
G.add_edge("40_Sun_08_W2", "40_Sun_1530_F", outcome="W/L")  # 3:30 is final OR 3rd

# ---------- Create interactive HTML visualization ----------

# Color scheme
bracket_colors = {
    "3.5": "#3498db",  # Blue for 3.5 bracket
    "4.0": "#9b59b6",  # Purple for 4.0 bracket
}

lane_colors = {
    "main": None,  # Use bracket color for main
    "cons": None,  # Use bracket color for consolation too
}

outcome_colors = {
    "W": "#2ecc71",  # Green for wins
    "L": "#e74c3c",  # Red for losses
    "W/L": "#f39c12",  # Orange for W/L (both outcomes)
}

print("📊 Creating interactive HTML visualization...")
net = Network(
    height="900px",
    width="100%",
    directed=True,
    notebook=False,
    cdn_resources="remote",
)


# Calculate time-based levels for hierarchical layout (left to right timeline)
# Extract actual hour from labels for better spacing
def extract_hour_from_label(label: str, day: str) -> float:
    """Extract hour value from label for timeline positioning."""
    # Parse time from label (e.g., "3.5 Sat 2:00 – M1" -> 14.0)
    time_match = re.search(r"(\d{1,2}):(\d{2})", label)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        # Convert to 24-hour format
        # Saturday: 2:00, 5:00, 6:30, 8:00 are PM (14, 17, 18.5, 20)
        # Sunday: 8:00, 9:30, 11:00 are AM (8, 9.5, 11)
        # Sunday: 12:30, 3:30, 5:00 are PM (12.5, 15.5, 17)
        if day == "Sat":
            # Saturday times are PM (afternoon/evening)
            if hour < 12:
                hour += 12
        else:  # Sunday
            # Sunday: 8:00, 9:30, 11:00 are AM; 12:30+ are PM
            if hour >= 12 or (hour == 12 and minute > 0):
                pass  # Already PM
            elif hour < 8:
                hour += 12  # Very early morning (unlikely but handle)
        return hour + minute / 60.0
    # Fallback to time_order
    return None


# Calculate fixed positions for timeline layout (left to right)
# Normalize times to x positions (0-1000 range for pyvis)
time_positions = {}
time_labels = {}  # Store time labels for axis

# First pass: extract all times and find min/max for normalization
all_times = []
for node_id, data in G.nodes(data=True):
    day = data["day"]
    label = data["label"]
    hour = extract_hour_from_label(label, day)
    if hour is None:
        hour = data["torder"] * 2  # Fallback
    # Convert to continuous timeline: Sat starts at 0, Sun continues
    timeline_pos = hour - 14 if day == "Sat" else (hour - 8) + 10
    all_times.append(timeline_pos)
    time_match = re.search(r"(\d{1,2}):(\d{2})", label)
    if time_match:
        time_labels[node_id] = f"{day} {time_match.group(1)}:{time_match.group(2)}"
    else:
        time_labels[node_id] = f"{day} T{data['torder']}"

min_time = min(all_times)
max_time = max(all_times)
time_range = max_time - min_time if max_time > min_time else 1

# Second pass: calculate normalized x positions
for node_id, data in G.nodes(data=True):
    day = data["day"]
    label = data["label"]
    hour = extract_hour_from_label(label, day)
    if hour is None:
        hour = data["torder"] * 2  # Fallback

    # Convert to continuous timeline
    timeline_pos = hour - 14 if day == "Sat" else (hour - 8) + 10

    # Normalize to 0-1000 range (pyvis coordinate system)
    x_pos = ((timeline_pos - min_time) / time_range) * 1000
    time_positions[node_id] = x_pos

# Base Y positions based on bracket and lane
base_y_positions = {
    ("3.5", "main"): 200,
    ("3.5", "cons"): 100,
    ("4.0", "main"): -100,
    ("4.0", "cons"): -200,
}


# Determine if nodes are on win or loss paths for vertical stacking
# Nodes reached via "W" edges are wins (higher), nodes via "L" edges are losses (lower)
def get_node_path_type(node_id: str) -> str:
    """Determine if node is reached via win or loss path."""
    # Check incoming edges
    for source, target, data in G.in_edges(node_id, data=True):
        if target == node_id:
            outcome = data.get("outcome", "")
            if outcome == "W":
                return "win"
            elif outcome == "L":
                return "loss"
    # Default: if no incoming edges or unclear, check if it's a final/consolation
    node_data = G.nodes[node_id]
    label = node_data.get("label", "")
    if "Final" in label and "Cons" not in label:
        return "win"  # Main final is typically win path
    elif "Cons" in label or "3rd" in label:
        return "loss"  # Consolation/3rd is loss path
    return "win"  # Default to win


# Calculate Y positions with vertical stacking for nodes at same time
# Group by bracket/lane AND time to keep brackets separate
y_positions = {}
# Group nodes by (bracket, lane) and x position (same time)
nodes_by_bracket_time = {}
for node_id in time_positions:
    node_data = G.nodes[node_id]
    bracket = node_data["bracket"]
    lane = node_data["lane"]
    x_pos = time_positions[node_id]
    rounded_x = round(x_pos / 5) * 5  # Group nodes at similar x positions

    key = (bracket, lane, rounded_x)
    if key not in nodes_by_bracket_time:
        nodes_by_bracket_time[key] = []
    nodes_by_bracket_time[key].append(node_id)

# Assign Y positions with vertical stacking within each bracket/lane
for (bracket, lane, rounded_x), node_ids in nodes_by_bracket_time.items():
    base_y = base_y_positions[(bracket, lane)]

    if len(node_ids) > 1:
        # Multiple nodes at same time in same bracket/lane - stack them vertically
        # Sort: wins first (higher), then losses (lower)
        sorted_nodes = sorted(
            node_ids,
            key=lambda nid: (
                0 if get_node_path_type(nid) == "win" else 1,
                nid,  # Secondary sort by ID for consistency
            ),
        )

        # Stack vertically: wins go up, losses go down
        vertical_spacing = 80  # pixels between stacked nodes
        win_count = sum(1 for nid in sorted_nodes if get_node_path_type(nid) == "win")

        for i, node_id in enumerate(sorted_nodes):
            path_type = get_node_path_type(node_id)

            if path_type == "win":
                # Wins stack upward from base
                y_positions[node_id] = base_y + (win_count - 1 - i) * vertical_spacing
            else:
                # Losses stack downward from base
                y_positions[node_id] = base_y - (i - win_count + 1) * vertical_spacing
    else:
        # Single node at this time - use base position
        node_id = node_ids[0]
        y_positions[node_id] = base_y

# Ensure all nodes have y positions (fallback for any missed)
for node_id in G.nodes():
    if node_id not in y_positions:
        node_data = G.nodes[node_id]
        bracket = node_data["bracket"]
        lane = node_data["lane"]
        y_positions[node_id] = base_y_positions[(bracket, lane)]

# Configure physics - minimal physics that respects fixed positions
net.set_options(
    """
    {
      "nodes": {
        "font": {"size": 16, "align": "center"},
        "scaling": {"min": 20, "max": 40},
        "shapeProperties": {
          "useBorderWithImage": false
        }
      },
      "edges": {
        "arrows": {"to": {"enabled": true, "scaleFactor": 1.2}},
        "smooth": {"type": "curvedCW", "roundness": 0.3},
        "width": 3,
        "font": {"size": 14, "align": "middle"}
      },
      "physics": {
        "enabled": false
      }
    }
    """
)

# Add nodes with fixed positions based on timeline
for node_id, data in G.nodes(data=True):
    bracket = data["bracket"]
    lane = data["lane"]
    label = data["label"]
    time_label = time_labels[node_id]

    # Determine node color - use bracket color for both main and cons
    color = bracket_colors[bracket]

    # Get fixed positions
    x_pos = time_positions[node_id]
    y_pos = y_positions[node_id]

    # Create tooltip with match details
    tooltip = f"{label}\nBracket: {bracket}\n{time_label}"

    net.add_node(
        node_id,
        label=label,
        color=color,
        title=tooltip,
        font={"size": 14},
        x=x_pos,  # Fixed x position based on time
        y=y_pos,  # Fixed y position based on bracket/lane
        fixed=True,  # Lock position
    )

# Add edges with colors based on outcome
for source, target, edge_data in G.edges(data=True):
    outcome = edge_data.get("outcome", "")
    color = outcome_colors.get(outcome, "#848484")

    net.add_edge(
        source,
        target,
        label=outcome,
        color=color,
        width=3,
    )

# Determine output path - save to web app's public directory if it exists
script_dir = Path(__file__).parent
repo_root = script_dir.parent.parent.parent
web_public_dir = repo_root / "apps" / "web" / "public"

if web_public_dir.exists():
    html_filename = web_public_dir / "tennis_tournament_bracket.html"
    print(f"✓ Saving to web app public directory: {html_filename}")
else:
    html_filename = script_dir / "tennis_tournament_bracket.html"
    print(f"✓ Saving to script directory: {html_filename}")

# Save HTML
net.save_graph(str(html_filename))

print(f"✓ Interactive visualization saved to: {html_filename}")
print("   Open in your browser to explore the tournament flow!")
print("   Timeline flows left to right chronologically!")

