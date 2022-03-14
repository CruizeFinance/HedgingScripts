from django.conf.urls import url

from options.views import OptionsViewset

urlpatterns = [
    url(
        "funding_fee",
        OptionsViewset.as_view({"get": "options_data"}),
        name="OptionsData",
    ),
]
