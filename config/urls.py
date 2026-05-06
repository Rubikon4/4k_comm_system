from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('', include('apps.core.urls')),
    path('workgroups/', include('apps.workgroups.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('chats/', include('apps.chats.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('attachments/', include('apps.attachments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
