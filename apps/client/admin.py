from django.contrib import admin
from .models import ClientProfile, ClientPreferences

class ClientPreferencesInline(admin.StackedInline):
    model = ClientPreferences
    can_delete = False
    verbose_name_plural = 'Preferences'

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'city', 'age', 'profile_completed', 'created_at']
    list_filter = ['profile_completed', 'gender', 'city', 'created_at']
    search_fields = ['forename', 'surname', 'user__email', 'city', 'postcode']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ClientPreferencesInline]
    
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
        ('Additional Information', {
            'fields': ('additional_notes', 'profile_completed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
 
@admin.register(ClientPreferences)
class ClientPreferencesAdmin(admin.ModelAdmin):
    list_display = ['client', 'updated_at']
    list_filter = [ 'has_pets', 'preferred_gender', 'updated_at']
    search_fields = ['client__forename', 'client__surname', 'availability_notes']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Client', {
            'fields': ('client',)
        }),
        ('Volunteer Preferences', {
            'fields': ('preferred_gender', 'preferred_languages')
        }),
        ('Schedule Preferences', {
            'fields': ('preferred_days', 'preferred_times', 'preferred_location', 'availability_notes')
        }),
        ('Task Preferences', {
            'fields': ('preferred_tasks',)
        }),
      
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

