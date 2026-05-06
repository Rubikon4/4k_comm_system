from django.urls import path

from . import views

app_name = 'chats'

urlpatterns = [
    path('', views.chat_list, name='list'),
    path('new/direct/', views.create_direct_chat, name='create_direct'),
    path('new/custom/', views.create_custom_chat, name='create_custom'),
    path('<int:pk>/', views.chat_detail, name='detail'),
    path('<int:pk>/info/', views.chat_info, name='info'),
    path('<int:pk>/messages/', views.messages_polling, name='polling'),
    path('<int:pk>/send/', views.send_message, name='send'),
    path('<int:pk>/toggle-writable/', views.toggle_writable, name='toggle_writable'),
    path('<int:pk>/toggle-can-write/', views.toggle_can_write, name='toggle_can_write'),
    path('<int:pk>/members/add/', views.add_chat_member, name='add_member'),
    path('<int:pk>/members/<int:user_id>/remove/', views.remove_chat_member, name='remove_member'),
]
