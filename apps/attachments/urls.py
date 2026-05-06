from django.urls import path

from . import views

app_name = 'attachments'

urlpatterns = [
    path('<int:pk>/download/', views.attachment_download, name='download'),
    path('<int:pk>/delete/', views.attachment_delete, name='delete'),
]
