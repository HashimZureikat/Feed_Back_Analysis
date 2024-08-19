from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', include('feedback.urls')),
    path('analyze_feedback/', include('feedback.urls')),
    path('register/', include('feedback.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('feedback/', include('feedback.urls')),
    path('', RedirectView.as_view(url='/feedback/home/', permanent=True)),
    path('', TemplateView.as_view(template_name='index.html')),  # Serve React app
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)