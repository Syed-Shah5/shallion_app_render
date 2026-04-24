from django.contrib import admin
from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'volunteer', 'status', 'compatibility_score', 'created_at')
    list_filter = ('status',)
    search_fields = ('client__forename', 'volunteer__forename')
    ordering = ('-created_at',)
