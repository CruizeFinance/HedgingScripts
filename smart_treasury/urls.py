from django.conf.urls import url

from smart_treasury.views import SmartTreasuryViewset

urlpatterns = [
    url("", SmartTreasuryViewset.as_view({"get": "list"}), name="SmartTreasury"),
]
