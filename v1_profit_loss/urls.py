from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

from v1_profit_loss.views import V1ProfitLoss

urlpatterns = [
    url("", V1ProfitLoss.as_view({"get": "list"}), name="V1ProfitLoss"),
]
