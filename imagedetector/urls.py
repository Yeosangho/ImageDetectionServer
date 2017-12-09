
from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^image/', views.show_image, name='show_image'),
    url(r'^$', views.index, name='index'),
]
