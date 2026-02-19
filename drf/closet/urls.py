from django.urls import path
from .views import ClosetListView, ClosetCreateView, ClosetDeleteView

urlpatterns = [
    path("", ClosetListView.as_view(), name="closet-list"),
    path("items/", ClosetCreateView.as_view(), name="closet-create"),
    path(
        "items/<int:closet_id>/",
        ClosetDeleteView.as_view(),
        name="closet-delete",
    ),
]
