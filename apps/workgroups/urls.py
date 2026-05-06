from django.urls import path

from . import views

app_name = 'workgroups'

urlpatterns = [
    path('', views.WorkGroupListView.as_view(), name='list'),
    path('create/', views.workgroup_create, name='create'),
    path('<int:pk>/', views.workgroup_detail, name='detail'),
    path('<int:pk>/edit/', views.workgroup_edit, name='edit'),
    path('<int:pk>/add-member/', views.workgroup_add_member, name='add_member'),
    path('<int:pk>/deactivate/', views.workgroup_deactivate, name='deactivate'),
    path('<int:pk>/attach/', views.workgroup_attach, name='attach'),
    path('<int:pk>/attachments/<int:att_pk>/delete/', views.workgroup_delete_attachment, name='delete_attachment'),
]
