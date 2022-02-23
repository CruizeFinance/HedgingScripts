from django.conf.urls import url

from tokens.views import TokensViewset

urlpatterns = [
    url(
        "v1/historical_data",
        TokensViewset.as_view({"get": "list"}),
        name="TokenHistoricalData",
    ),
    url(
        "v1/liquidation_threshold",
        TokensViewset.as_view({"get": "liquidation_threshold"}),
    ),
]
