from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    
    # Client authentication
    path('client/login/', views.client_login, name='client_login'),
    path('client/register/', views.client_register, name='client_register'),
    path('client/register/confirmation/', views.client_register_confirmation, name='client_register_confirmation'),
    path('client/logout/', views.client_logout, name='client_logout'),
    
    # Volunteer authentication
    path('volunteer/login/', views.volunteer_login, name='volunteer_login'),
    path('volunteer/register/', views.volunteer_register, name='volunteer_register'),
    path('volunteer/register/confirmation/', views.volunteer_register_confirmation, name='volunteer_register_confirmation'),
    path('volunteer/logout/', views.volunteer_logout, name='volunteer_logout'),

    # Email verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
   
    # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]