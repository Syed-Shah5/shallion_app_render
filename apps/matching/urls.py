from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    path('<int:match_id>/', views.match_detail, name='match_detail'),
    path('<int:match_id>/respond/', views.respond_to_match, name='respond_to_match'),
]
