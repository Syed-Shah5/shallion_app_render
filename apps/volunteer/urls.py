from django.urls import path
from . import views

app_name = 'volunteer'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Profile management
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/view/', views.view_profile, name='view_profile'),
    
    # Preferences
    path('preferences/create/', views.create_preferences, name='create_preferences'),
    path('preferences/edit/', views.edit_preferences, name='edit_preferences'),
    
    # Availability
    path('update-availability/', views.update_availability, name='update_availability'),

    # Matching
    path('matched-clients/', views.matched_clients, name='matched_clients'),
    
    # Account management
    path('delete-account/', views.delete_account, name='delete_account'),
]

