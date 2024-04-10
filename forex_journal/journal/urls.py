from django.contrib import admin
from django.urls import path
from . import views
from . views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from .utils import get_pairs

app_name = "journal"
urlpatterns = (
    [
        path("journal/", HomeView.as_view(), name="home"),
        path("add_record/", AddRecordView.as_view(), name="add-record"),
        path("trade/<int:pk>", TradeRecordDetail.as_view(), name="trade-detail"),
        path("trade/<int:pk>/add_photos/", AddPhotos.as_view(), name="add_photos"),
        path("delete_record/<int:pk>", views.delete_record, name="delete-record"),
        path("add_data_before/", AddBeforeDataCreateView.as_view(), name="before-trade-data"),
        path("add_active_trade/", AddActiveRecord.as_view(), name="add-active-trade"),
        path("complete-record/<int:pk>/", CompleteRecord.as_view(), name="complete-record"),
        path("strategy/", StrategyListView.as_view(), name="strategy_list"),
        path("strategy/<int:pk>", StrategyDocs.as_view(), name="strategy_docs"),
        path("edit_recod/<int:pk>", EditRecord.as_view(), name="edit-record"),
        path("edit_active_recod/<int:pk>", EditActiveRecordView.as_view(), name="edit-active-record"),
        path(
            "edit_photo_before/<int:pk>/",
            EditPhotoBeforeView.as_view(),
            name="edit-photo-before",
        ),
        
        path("edit_photo/<int:pk>", EditPhotoView.as_view(), name="edit-photo"),
        path(
            "edit_note_before/<int:pk>/",
            EditNoteBeforeView.as_view(),
            name="edit-note-before",
        ),
        path("edit_note/<int:pk>", EditNoneAfter.as_view(), name="edit-note"),
        path(
            "delete_data_before/<int:pk>",
            views.delete_data_before,
            name="delete_data_before",
        ),
        path("delete_data/<int:pk>", views.delete_data, name="delete_data"),
        path(
            "trade/<int:pk>/add_photos/add_or_restore_before_data/",
            add_or_restore_before_data,
            name="add_or_restore_before_data",
        ),
        path("trade/<int:pk>/photos", PhotosView.as_view(), name="photos"),
        path("assets/", views.assets, name="assets"),
        path("assets/add_new_asset/", views.add_new_asset, name="add_new_asset"),
        path("set_color/<int:record_id>/", views.set_color, name="set_color"),
        path("get_latest_alert/", views.get_latest_alert, name="get_latest_alert"),
        path("get_pairs/", get_pairs, name="get_pairs"),
        path("search_trade/", search_view, name="search_trade"),
        path('search-active/', search_active, name='search_active'),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + staticfiles_urlpatterns()
)
