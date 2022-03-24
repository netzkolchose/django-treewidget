from django.conf.urls import include
from django.contrib import admin
try:
    from django.conf.urls import url
except ImportError:
    # django 4 and up
    from django.urls import re_path as url



urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^treewidget/', include('treewidget.urls')),
]

from django.conf import settings
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
