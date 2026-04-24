from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as account_views

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Accounts 
    path('accounts/', include('apps.accounts.urls')),
    
    # Homepage
    path('', account_views.home, name='home'),
    
    # About Page
    path('about/', account_views.about, name='about'),
    
    # Contact Page
    path('contact/', account_views.contact, name='contact'),

    # How It Works Page
    path('how-it-works/', account_views.how_it_works, name='how_it_works'),

    # Help as User Manual
    path('help/', account_views.help_page, name='help'),

    # Client 
    path('client/', include('apps.client.urls')),

    # Volunteer
    path('volunteer/', include('apps.volunteer.urls')),

    # Matching 
    path('matching/', include('apps.matching.urls')),
   
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)