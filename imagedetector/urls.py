
from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^image/', views.show_image, name='show_image'),
    url(r'^ready/', views.ready_model, name='ready_model'),
    url(r'^$', views.index, name='index'),
]
