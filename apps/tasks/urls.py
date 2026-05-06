from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='list'),
    path('create/', views.task_create, name='create'),
    path('<int:pk>/', views.task_detail, name='detail'),
    path('<int:pk>/status/', views.task_change_status, name='change_status'),
    path('<int:pk>/edit/', views.task_edit, name='edit'),
    path('<int:pk>/assignees/add/', views.task_add_assignee, name='add_assignee'),
    path('<int:pk>/assignees/<int:user_id>/remove/', views.task_remove_assignee, name='remove_assignee'),
]
