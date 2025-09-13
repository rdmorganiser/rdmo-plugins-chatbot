from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from rdmo.core.permissions import HasModelPermission
from rdmo.projects.models import Project
from rdmo.projects.permissions import HasProjectsPermission

from .serializers import ProjectSerializer


class ProjectViewSet(RetrieveModelMixin, GenericViewSet):
    permission_classes = (HasModelPermission | HasProjectsPermission, )
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
