from django.urls import path
from . import views
urlpatterns = [
    path('api/urls/', views.create_url, name='create_url'),
    path('<str:code>/', views.redirect_to_url, name='redirect_to_url'),
    path('api/urls/<str:code>/stats/', views.url_stats, name='url_stats'),
    path('api/urls', views.list_urls, name='list_urls'),
    path('api/urls/<str:code>/', views.delete_url, name='delete_url'),
]