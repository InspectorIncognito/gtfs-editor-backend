"""gtfseditor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_nested import routers
from rest_api import views


router = routers.SimpleRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'users', views.UserViewSet)

project_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
project_router.register(r'calendars', views.CalendarViewSet, basename='project-calendars')
project_router.register(r'levels', views.LevelViewSet, basename='project-levels')
project_router.register(r'calendardates', views.CalendarDateViewSet, basename='project-calendardates')
project_router.register(r'feedinfo', views.FeedInfoViewSet, basename='project-feedinfo')
project_router.register(r'stops', views.StopViewSet, basename='project-stops')
project_router.register(r'pathways', views.PathwayViewSet, basename='project-pathways')
project_router.register(r'shapes', views.ShapeViewSet, basename='project-shapes')
project_router.register(r'shapepoints', views.ShapePointViewSet, basename='project-shapepoints')
project_router.register(r'transfers', views.TransferViewSet, basename='project-transfers')
project_router.register(r'agencies', views.AgencyViewSet, basename='project-agencys')
project_router.register(r'routes', views.RouteViewSet, basename='project-routes')
project_router.register(r'fareattributes', views.FareAttributeViewSet, basename='project-fareattributes')
project_router.register(r'farerules', views.FareRuleViewSet, basename='project-farerules')
project_router.register(r'trips', views.TripViewSet, basename='project-trips')
project_router.register(r'stoptimes', views.StopTimeViewSet, basename='project-stoptimes')

urlpatterns = [
    path(r'admin/', admin.site.urls),
    path(r'django-rq/', include('django_rq.urls')),
    path(r'api/', include(router.urls)),
    path(r'api/', include(project_router.urls)),
    path(r'api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
