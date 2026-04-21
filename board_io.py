import numpy as np
import json
import io
from board import (
    BoardState, BoardSetup, Loc, Droplet, Box, Pearl, Portal, Gate, StationaryPieceType
)

def serialize_board(state: BoardState) -> str:
    """Serializes a BoardState to a human-readable text format."""
    output = io.StringIO()
    
    # 1. Serialize Grid (Stationary)
    output.write("--- GRID ---\n")
    grid_str = "\n".join(" ".join(str(val) for val in row) for row in state.setup.grid)
    output.write(grid_str + "\n")
    
    # 2. Serialize Portals (Setup Metadata)
    output.write("\n--- PORTALS ---\n")
    portals_data = [{"y": p.loc.y, "x": p.loc.x, "id": p.portal_id} for p in state.setup.portals]
    output.write(json.dumps(portals_data) + "\n")
    
    # 3. Serialize Dynamic Objects
    output.write("\n--- DYNAMIC ---\n")
    dynamic_data = {
        "droplets": [{"y": d.loc.y, "x": d.loc.x} for d in state.droplets],
        "boxes": [{"y": b.loc.y, "x": b.loc.x} for b in state.boxes],
        "pearls": [{"y": p.loc.y, "x": p.loc.x} for p in state.pearls],
        "gates": [{"y": g.loc.y, "x": g.loc.x, "closed": g.is_closed} for g in state.gates],
        "global_direction": state.global_direction.name if state.global_direction else "RIGHT"
    }
    output.write(json.dumps(dynamic_data, indent=2) + "\n")
    
    return output.getvalue()

def parse_board(content: str) -> BoardState:
    """Parses a serialized board string back into a BoardState."""
    sections = content.split("---")
    
    grid = None
    portals = []
    dynamic = {}
    
    for i in range(len(sections)):
        section_name = sections[i].strip()
        if section_name == "GRID":
            grid_lines = sections[i+1].strip().splitlines()
            grid = np.array([[int(val) for val in line.split()] for line in grid_lines], dtype=np.int8)
        elif section_name == "PORTALS":
            portals_raw = json.loads(sections[i+1].strip())
            portals = [Portal(Loc(p["y"], p["x"]), p["id"]) for p in portals_raw]
        elif section_name == "DYNAMIC":
            dynamic = json.loads(sections[i+1].strip())

    setup = BoardSetup(grid, portals)
    
    droplets = [Droplet(Loc(d["y"], d["x"])) for d in dynamic.get("droplets", [])]
    boxes = [Box(Loc(b["y"], b["x"])) for b in dynamic.get("boxes", [])]
    pearls = [Pearl(Loc(p["y"], p["x"])) for p in dynamic.get("pearls", [])]
    gates = [Gate(Loc(g["y"], g["x"]), g["closed"]) for g in dynamic.get("gates", [])]
    
    from board import Direction
    g_dir_name = dynamic.get("global_direction", "RIGHT")
    global_direction = Direction[g_dir_name] if g_dir_name else Direction.RIGHT
    
    return BoardState(setup, droplets, boxes, pearls, gates, global_direction=global_direction)
