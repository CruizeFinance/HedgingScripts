from django.conf.urls import url

from tokens.views import TokensViewset

urlpatterns = [
    url("v1", TokensViewset.as_view({"get": "list"}), name="TokenHistoricalData"),
]
