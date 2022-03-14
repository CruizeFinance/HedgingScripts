from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import GenericViewSet


class OptionsViewset(GenericViewSet):
    def get(self):
        pass
