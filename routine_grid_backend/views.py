# routine_grid_backend/views.py (create this file)
from django.shortcuts import render
from django.views.generic import TemplateView


class ScalarDocumentationView(TemplateView):
    template_name = "api_docs/scalar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the schema URL - adjust if you have a different base URL
        schema_url = self.request.build_absolute_uri("/api/schema.yaml")
        context["schema_url"] = schema_url
        return context
