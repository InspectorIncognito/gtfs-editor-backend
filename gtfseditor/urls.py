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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework_nested import routers

from rest_api import views as api_views
from user.views import UserLoginView

router = routers.SimpleRouter()
router.register(r'projects', api_views.ProjectViewSet)


project_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
project_router.register(r'calendars', api_views.CalendarViewSet, basename='project-calendars')
project_router.register(r'levels', api_views.LevelViewSet, basename='project-levels')
project_router.register(r'calendardates', api_views.CalendarDateViewSet, basename='project-calendardates')
project_router.register(r'feedinfo', api_views.FeedInfoViewSet, basename='project-feedinfo')
project_router.register(r'stops', api_views.StopViewSet, basename='project-stops')
project_router.register(r'pathways', api_views.PathwayViewSet, basename='project-pathways')
project_router.register(r'shapes', api_views.ShapeViewSet, basename='project-shapes')
project_router.register(r'shapepoints', api_views.ShapePointViewSet, basename='project-shapepoints')
project_router.register(r'transfers', api_views.TransferViewSet, basename='project-transfers')
project_router.register(r'agencies', api_views.AgencyViewSet, basename='project-agencies')
project_router.register(r'routes', api_views.RouteViewSet, basename='project-routes')
project_router.register(r'fareattributes', api_views.FareAttributeViewSet, basename='project-fareattributes')
project_router.register(r'farerules', api_views.FareRuleViewSet, basename='project-farerules')
project_router.register(r'trips', api_views.TripViewSet, basename='project-trips')
project_router.register(r'stoptimes', api_views.StopTimeViewSet, basename='project-stoptimes')
project_router.register(r'frequencies', api_views.FrequencyViewSet, basename='project-frequencies')

project_router.register(r'services', api_views.ServiceViewSet, basename='project-services')
project_router.register(r'tables', api_views.TablesViewSet, basename='project-tables')

urlpatterns = [
    path('users/login/', UserLoginView.as_view(), name='user-login'),
    path(r'admin/', admin.site.urls),
    path(r'django-rq/', include('django_rq.urls')),
    path(r'api/', include(router.urls)),
    path(r'api/', include(project_router.urls)),
    path(r'api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

if settings.DEBUG:
    # it serves media files in dev server
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
