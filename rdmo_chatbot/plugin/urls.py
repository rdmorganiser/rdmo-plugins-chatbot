from django.urls import include, path

from rest_framework import routers

from .viewsets import ProjectViewSet

app_name = 'v1-chatbot'

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('chatbot/', include(router.urls)),
]
