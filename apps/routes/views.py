from rest_framework import viewsets, status, views
from rest_framework.response import Response
from .models import Airport, Route
from .serializers import AirportSerializer, RouteSerializer, NthNodeInputSerializer, ShortestPathInputSerializer
from .services.graph import GraphService
from django.db.models import Prefetch
from drf_yasg.utils import swagger_auto_schema


# Create your views here.


class RouteViewSet(viewsets.ModelViewSet):
    """
    /api/routes/  -> list/create
    /api/routes/{pk}/ -> retrieve/update/destroy
    POST payload for create: { from_code, to_code, position, duration }
    """
    queryset = Route.objects.select_related('from_airport', 'to_airport').all()
    serializer_class = RouteSerializer
    
    def list(self, request, *args, **kwargs):
        # Prefetch airports and outgoing for performance if needed
        qs = self.queryset.select_related('from_airport','to_airport')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)



class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer



class GetNthNodeView(views.APIView):

    @swagger_auto_schema(request_body=NthNodeInputSerializer)
    def post(self, request, *args, **kwargs):

        serializer = NthNodeInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"status": False, "errors": serializer.errors,}, status=status.HTTP_400_BAD_REQUEST)
        
        start = serializer.validated_data['start_code']
        direction = serializer.validated_data['direction']
        n = serializer.validated_data['n']

        if not start or direction not in (Route.LEFT, Route.RIGHT) or n <= 0:
            return Response({'detail': 'Invalid input.'}, status=status.HTTP_400_BAD_REQUEST)

        res = GraphService.get_nth_node(start, direction, n)
        if not res:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        airport, path_routes = res
        return Response({
            'airport': AirportSerializer(airport).data,
            'path': [
                {
                    'from': r.from_airport.code,
                    'to': r.to_airport.code,
                    'position': r.position,
                    'duration': r.duration,
                } for r in path_routes
            ]
        })
    

class ShortestPathView(views.APIView):

    @swagger_auto_schema(request_body=ShortestPathInputSerializer)
    def post(self, request, *args, **kwargs):

        serializer = ShortestPathInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"status": False, "errors": serializer.errors,}, status=status.HTTP_400_BAD_REQUEST)

        src = serializer.validated_data['source']
        tgt = serializer.validated_data['target']

        if not src or not tgt:
            return Response({'detail': 'Provide source and target.'}, status=status.HTTP_400_BAD_REQUEST)

        res = GraphService.shortest_path(src, tgt)
        if not res:
            return Response({'detail': 'No path found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'distance': res['distance'],
            'path': res['path'],
        })



class LongestPathView(views.APIView):

    def get(self, request, *args, **kwargs):
        overall = GraphService.find_longest_route_overall()
        overall_data = None

        if overall:
            overall_data = {
                'from': overall.from_airport.code,
                'to': overall.to_airport.code,
                'duration': overall.duration,
            }

        airports = Airport.objects.prefetch_related(
            Prefetch(
                'outgoing_routes',
                queryset=Route.objects.select_related('to_airport').order_by('-duration')
            )
        )

        per_airport = []
        for ap in airports:
            first = ap.outgoing_routes.all().first()
            if first:
                per_airport.append({
                    'airport': ap.code,
                    'child': {
                        'to': first.to_airport.code,
                        'position': first.position,
                        'duration': first.duration,
                    }
                })

        return Response({
            'overall': overall_data,
            'per_airport': per_airport,
        })


