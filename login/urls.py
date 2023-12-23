from django.urls import path
from . import views


# Add your URL patterns here.
urlpatterns = [
    path('', views.login_view, name='login'),
]
