from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RouteViewSet,
    AirportViewSet,
    GetNthNodeView,
    ShortestPathView,
    LongestPathView
)

router = DefaultRouter()
router.register('routes', RouteViewSet, basename='routes')
router.register('airports', AirportViewSet, basename='airports')

urlpatterns = [
    path('api/', include(router.urls)),
    
    path('api/graph/nth/', GetNthNodeView.as_view(), name='graph-nth'),
    path('api/graph/shortest/', ShortestPathView.as_view(), name='graph-shortest'),
    path('api/graph/longest/', LongestPathView.as_view(), name='graph-longest'),
]
