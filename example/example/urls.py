from django.conf.urls import url, include
from django.contrib import admin
from exampleapp.views import bound, free, widget, free2


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^treewidget/', include('treewidget.urls')),
    url(r'^bound/', bound, name='bound'),
    url(r'^free/', free, name='free'),
    url(r'^free2/', free2, name='free2'),
    url(r'^widget/', widget, name='widget'),
]
