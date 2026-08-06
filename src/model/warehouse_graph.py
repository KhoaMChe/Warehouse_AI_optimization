from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
import re
from typing import Hashable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class WarehouseGraphConfig:
    inbound_gate_count: int = 7
    outbound_gate_count: int = 6
    rack_spacing_m: float = 4.0
    bay_spacing_m: float = 1.2
    gate_apron_m: float = 6.0
    staging_offset_m: float = 8.0
    floor_handling_m: float = 1.5
    include_top_cross_aisle: bool = True


class WarehouseGraph:
    def __init__(self, config: WarehouseGraphConfig | None = None):
        self.config = config or WarehouseGraphConfig()
        self.edges: dict[Hashable, list[tuple[Hashable, float]]] = {}
        self.location_node: dict[Hashable, Hashable] = {}
        self.location_floor_cost: dict[Hashable, float] = {}
        self.gates: dict[str, list[Hashable]] = {"inbound": [], "outbound": []}
        self.staging_node: Hashable | None = None

    def add_edge(self, left: Hashable, right: Hashable, distance_m: float) -> None:
        distance = float(max(distance_m, 0.0))
        self.edges.setdefault(left, []).append((right, distance))
        self.edges.setdefault(right, []).append((left, distance))

    @staticmethod
    def _natural_key(value) -> tuple:
        return tuple(
            int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", str(value))
        )

    @staticmethod
    def _position_order(frame: pd.DataFrame) -> pd.Series:
        sequence = pd.to_numeric(frame.get("vi_tri_seq_id", 0), errors="coerce").fillna(0)
        if "ma_so_vi_tri" in frame:
            fallback = pd.to_numeric(
                frame["ma_so_vi_tri"].astype(str).str.replace(r"\D", "", regex=True),
                errors="coerce",
            ).fillna(0)
            sequence = sequence.where(sequence > 0, fallback)
        # Dense rank converts warehouse-specific identifiers into bay steps.
        return sequence.rank(method="dense").sub(1).fillna(0).astype(int)

    @classmethod
    def from_positions(
        cls,
        positions: pd.DataFrame,
        kho_id=None,
        config: WarehouseGraphConfig | None = None,
    ) -> "WarehouseGraph":
        graph = cls(config)
        cfg = graph.config
        frame = positions.copy()
        if kho_id is not None and "kho_id" in frame:
            frame = frame[frame["kho_id"].eq(kho_id)]
        if "deleted" in frame:
            frame = frame[frame["deleted"].fillna(0).eq(0)]
        frame = frame.dropna(subset=["auto_id", "day_ke_id"])
        if frame.empty:
            return graph

        racks = sorted(frame["day_ke_id"].unique(), key=graph._natural_key)
        max_bay = 0
        rack_bays: dict[Hashable, list[int]] = {}
        prepared = []
        for rack in racks:
            rack_frame = frame[frame["day_ke_id"].eq(rack)].copy()
            rack_frame["_bay"] = graph._position_order(rack_frame)
            max_bay = max(max_bay, int(rack_frame["_bay"].max()))
            rack_bays[rack] = sorted(rack_frame["_bay"].unique().tolist())
            prepared.append(rack_frame)
        frame = pd.concat(prepared, ignore_index=True)

        top_y = max(max_bay * cfg.bay_spacing_m, cfg.bay_spacing_m)
        main_nodes = []
        top_nodes = []
        for rack_index, rack in enumerate(racks):
            x = rack_index * cfg.rack_spacing_m
            bottom = ("aisle", rack, 0)
            top = ("aisle", rack, "top")
            main_nodes.append(bottom)
            top_nodes.append(top)

            bay_values = sorted(set(rack_bays[rack]) | {0})
            previous = bottom
            previous_y = 0.0
            for bay in bay_values:
                y = bay * cfg.bay_spacing_m
                node = ("rack", rack, bay)
                if node != previous:
                    graph.add_edge(previous, node, y - previous_y)
                previous, previous_y = node, y
            graph.add_edge(previous, top, top_y - previous_y)

        for nodes in (main_nodes, top_nodes if cfg.include_top_cross_aisle else []):
            for left, right in zip(nodes, nodes[1:]):
                graph.add_edge(left, right, cfg.rack_spacing_m)

        rack_index_map = {rack: index for index, rack in enumerate(racks)}
        for _, row in frame.iterrows():
            location_id = row["auto_id"]
            graph.location_node[location_id] = ("rack", row["day_ke_id"], int(row["_bay"]))
            floor = max(float(row.get("tang", 1) or 1), 1.0)
            graph.location_floor_cost[location_id] = (floor - 1.0) * cfg.floor_handling_m

        # All 13 gates are placed along the lower main cross-aisle. Gate
        # connectors are explicit edges, so routing still uses the graph.
        def connect_gates(kind: str, count: int, prefix: str) -> None:
            if count <= 0:
                return
            gate_indices = np.linspace(0, len(racks) - 1, count).round().astype(int)
            for number, rack_index in enumerate(gate_indices, start=1):
                node = (prefix, number)
                graph.add_edge(node, main_nodes[int(rack_index)], cfg.gate_apron_m)
                graph.gates[kind].append(node)

        connect_gates("inbound", cfg.inbound_gate_count, "IN")
        connect_gates("outbound", cfg.outbound_gate_count, "OUT")
        graph.staging_node = ("STAGING", 1)
        graph.add_edge(graph.staging_node, main_nodes[-1], cfg.staging_offset_m)
        return graph

    def _multi_source_distances(self, sources: list[Hashable]) -> dict[Hashable, float]:
        distance = {node: math.inf for node in self.edges}
        queue = []
        for source in sources:
            if source in distance:
                distance[source] = 0.0
                heapq.heappush(queue, (0.0, repr(source), source))
        while queue:
            current_distance, _, node = heapq.heappop(queue)
            if current_distance != distance[node]:
                continue
            for neighbor, weight in self.edges.get(node, []):
                candidate = current_distance + weight
                if candidate < distance[neighbor]:
                    distance[neighbor] = candidate
                    heapq.heappush(queue, (candidate, repr(neighbor), neighbor))
        return distance

    def distance_matrix(self) -> pd.DataFrame:
        """Return minimum aisle distance from every operational area."""
        inbound = self._multi_source_distances(self.gates["inbound"])
        outbound = self._multi_source_distances(self.gates["outbound"])
        staging = self._multi_source_distances([self.staging_node] if self.staging_node else [])
        rows = []
        for location_id, node in self.location_node.items():
            lift = self.location_floor_cost.get(location_id, 0.0)
            rows.append({
                "auto_id": location_id,
                "inbound_distance_m": inbound.get(node, math.inf) + lift,
                "outbound_distance_m": outbound.get(node, math.inf) + lift,
                "staging_distance_m": staging.get(node, math.inf) + lift,
            })
        return pd.DataFrame(rows)

    def distances_from_locations(self, location_ids) -> dict[Hashable, float]:
        sources = [self.location_node[value] for value in location_ids if value in self.location_node]
        node_distances = self._multi_source_distances(sources)
        return {
            location_id: node_distances.get(node, math.inf)
            for location_id, node in self.location_node.items()
        }

