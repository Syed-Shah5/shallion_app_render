from django.contrib import admin
from .models import VolunteerProfile, VolunteerPreferences

class VolunteerPreferencesInline(admin.StackedInline):
    model = VolunteerPreferences
    can_delete = False
    verbose_name_plural = 'Preferences'

@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'city', 'age', 'profile_completed', 'created_at']
    list_filter = ['profile_completed', 'gender', 'city', 'created_at']
    search_fields = ['forename', 'surname', 'user__email', 'city', 'postcode']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [VolunteerPreferencesInline]
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('forename', 'surname', 'gender', 'date_of_birth', 'phone', 'profile_photo')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'postcode')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
        }),
        ('Volunteer Information', {
            'fields': ('bio', 'skills_description', 'profile_completed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
@admin.register(VolunteerPreferences)
class VolunteerPreferencesAdmin(admin.ModelAdmin):
    list_display = ['volunteer', 'updated_at']
    list_filter = ['can_work_with_pets', 'has_transportation', 'preferred_gender', 'updated_at']
    search_fields = ['volunteer__forename', 'volunteer__surname', 'availability_notes']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Volunteer', {
            'fields': ('volunteer',)
        }),
        ('Client Preferences', {
            'fields': ('preferred_gender', 'preferred_languages')
        }),
        ('Availability', {
            'fields': ('preferred_days', 'preferred_times', 'availability_notes')
        }),
        ('Task Preferences', {
            'fields': ('preferred_tasks',)
        }),
        ('Additional Preferences', {
            'fields': ('can_work_with_pets', 'has_transportation')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )