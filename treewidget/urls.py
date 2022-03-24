try:
    from django.conf.urls import url
except ImportError:
    # django 4 and up
    from django.urls import re_path as url
from treewidget.views import get_node, move_node

urlpatterns = [
    url(r'get_node/$', get_node, name='treewidget.get_node'),
    url(r'move_node/$', move_node, name='treewidget.move_node'),
]
