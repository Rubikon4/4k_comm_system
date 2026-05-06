from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('count/', views.notification_count, name='count'),
    path('<int:pk>/mark-read/', views.notification_mark_read, name='mark_read'),
    path('<int:pk>/go/', views.notification_go, name='go'),
]
