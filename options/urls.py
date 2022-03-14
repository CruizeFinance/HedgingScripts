from django.conf.urls import url

from options.views import OptionsViewset

urlpatterns = [
    url(
        "v1/options",
        OptionsViewset.as_view({"get": "options_data"}),
        name="OptionsData",
    ),
]
