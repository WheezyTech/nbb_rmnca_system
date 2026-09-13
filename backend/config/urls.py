from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "api/accounts/",
        include("accounts.urls"),
    ),

    path(
        "api/facilities/",
        include("facilities.urls"),
    ),

    path(
        "api/donors/",
        include("donors.urls"),
    ),

    path(
        "api/inventory/",
        include("inventory.urls"),
    ),
    
]