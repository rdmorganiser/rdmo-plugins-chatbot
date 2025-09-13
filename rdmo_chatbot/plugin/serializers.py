from rest_framework import serializers

from rdmo.projects.exports import AnswersExportMixin
from rdmo.projects.models import Project


class ProjectSerializer(serializers.ModelSerializer):

    answers = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "answers"
        ]

    def get_answers(self, obj):
        export_plugin = AnswersExportMixin()
        export_plugin.project = obj
        export_plugin.snapshot = None

        data = export_plugin.get_data()
        return data
