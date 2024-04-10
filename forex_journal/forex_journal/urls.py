"""
URL configuration for forex_journal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from accounts.views import show_settings
from django.contrib.auth import views as auth_views
from accounts.views import *

urlpatterns = (
    [
        path("journal/", include("journal.urls")),
        path("admin/", admin.site.urls),
        path("accounts/", include("accounts.urls")),
        path("tinymce/", include("tinymce.urls")),
        path("signals/", include("trading_signals.urls")),
        path("settings/", show_settings, name="settings"),
        path("trade_debug/", include("trade_debug.urls")),
        path('checuserstatus/', check_user_status, name='check_user_status'),
        path("", include("public.urls")),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + staticfiles_urlpatterns()
)
# path('edit-record/', views.edit_record, name='edit_record'),
# path('save-student', apiViews.savejournal, name='savejournal')
