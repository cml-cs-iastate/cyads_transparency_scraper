from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("update_gtr", views.update_transparency, name="update_gtr")
]
