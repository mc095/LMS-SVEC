from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
#from .views import UpdateVideoViews

urlpatterns = [
    path('custom-admin/', views.custom_admin_view, name='custom-admin-url'),
    path('custom-admin-add/', views.custom_admin_view_add, name='custom-admin-url'),
    #path('videos/<int:video_id>/update-views/', UpdateVideoViews.as_view(), name='update_video_views'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
