from typing import Optional, Tuple, List, Dict
import heapq
from ..models import Airport, Route

class GraphService:
    """Service class for graph algorithms (traversal, shortest path)."""

    @staticmethod
    def get_nth_node(start_code: str, direction: str, n: int) -> Optional[Tuple[Airport, List[Route]]]:
        start_code = start_code.strip().upper()
        try:
            current = Airport.objects.get(code=start_code)
        except Airport.DoesNotExist:
            return None

        path_routes = []
        # Using select_related when following route objects will be inside loop
        for i in range(n):
            try:
                route = current.outgoing_routes.select_related('to_airport').get(position=direction)
            except Route.DoesNotExist:
                return None
            path_routes.append(route)
            current = route.to_airport
        return current, path_routes

    @staticmethod
    def find_longest_route_overall() -> Optional[Route]:
        return Route.objects.select_related('from_airport', 'to_airport').order_by('-duration').first()

    @staticmethod
    def find_longest_child_for_airport(airport_code: str) -> Optional[Route]:
        try:
            airport = Airport.objects.get(code=airport_code.strip().upper())
        except Airport.DoesNotExist:
            return None
        return airport.outgoing_routes.select_related('to_airport').order_by('-duration').first()

    @staticmethod
    def shortest_path(source_code: str, target_code: str) -> Optional[Dict]:
        source_code = source_code.strip().upper()
        target_code = target_code.strip().upper()
        try:
            source = Airport.objects.get(code=source_code)
            target = Airport.objects.get(code=target_code)
        except Airport.DoesNotExist:
            return None

        # Build adjacency list using in-memory map; optimized DB reads:
        airports = Airport.objects.all().only('code')
        adj = {ap.code: [] for ap in airports}

        # Select routes with related airport codes
        for r in Route.objects.select_related('from_airport', 'to_airport').all():
            a = r.from_airport.code
            b = r.to_airport.code
            w = r.duration
            adj[a].append((b, w, r))   # forward
            adj[b].append((a, w, None)) # treat as undirected; reverse edge not attached to a route instance

        # Dijkstra
        dist = {code: float('inf') for code in adj}
        prev = {code: None for code in adj}
        prev_edge = {code: None for code in adj}
        dist[source.code] = 0
        heap = [(0, source.code)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            if u == target.code:
                break
            for v, w, edge in adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    prev_edge[v] = edge
                    heapq.heappush(heap, (nd, v))

        if dist[target.code] == float('inf'):
            return None

        # Reconstruct path nodes and edges
        path_nodes = []
        edges = []
        cur = target.code
        while cur is not None:
            path_nodes.append(cur)
            edges.append(prev_edge[cur])
            cur = prev[cur]
        path_nodes.reverse()
        edges.reverse()
        return {'distance': dist[target.code], 'path': path_nodes, 'edges': edges[1:]}
