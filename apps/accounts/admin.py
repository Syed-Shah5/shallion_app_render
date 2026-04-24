from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'role', 'status', 'is_email_verified', 'date_joined')
    list_filter = ('role', 'status', 'is_email_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone')}),
        ('Role & Status', {'fields': ('role', 'status')}),
        ('Verifications', {'fields': (
            'is_email_verified', 'email_verified_at',
            'pvg_number', 'pvg_verified', 'pvg_verified_at',
            'gp_certificate', 'gp_certificate_verified', 'gp_certificate_verified_at'
        )}),
        ('Profile', {'fields': ('profile_completed',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone', 'role', 'password1', 'password2'),
        }),
    )

admin.site.register(User, CustomUserAdmin)