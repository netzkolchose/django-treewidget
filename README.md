## treewidget for Django ##

Provides the model fields TreeForeignKey, TreeOneToOneField, TreeManyToManyField
for tree models with an enhanced widget with the help of `jstree` (thanks to vakata).

Tested with django-mptt and treebeard with Django 1.11 & 2.0.2. Due to a major change of
the widget template handling it will not work with any Django version < 1.11.

### Installation ###

- `pip install django-treewidget`
- place `'treewidget'` in `INSTALLED_APPS`
- for AJAX tree updates add the routes to your urls.py,
e.g. `url(r'^treewidget/', include('treewidget.urls'))`

### Usage ###

Just replace any foreign key, m2m or one2one tree model field with the provided pendants.

### Customization ###

The fields understand two additional arguments:
- **settings**: Dictionary containing the optional boolean keys 'show_buttons'
(shows "Expand", "Collapse" and "Selected" buttons), 'search' (for in-tree search),
'dnd' (drag and drop support) and 'sort' (apply tree order in frontend). Defaults to `{}`.
- **treeoptions**: Settings directly applied to `jstree`. Must be a JSON string, if given as
argument to a field, otherwise a python dictionary. Defaults to `treewidget.fields.TREEOPTIONS`.
Note that some widget settings will override treeoptions to keep working.

Both settings parameter can be set project wide in settings.py as `TREEWIDGET_SETTINGS` and
`TREEWIDGET_TREEOPTIONS`.

### Example ###
```python
from django.db import models
from mptt.models import MPTTModel
from treewidget.fields import TreeForeignKey

class Mptt(MPTTModel):
    name = models.CharField(max_length=32)
    parent = TreeForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
```

Renders like this:

![screenshot](https://github.com/jerch/django-treewidget/raw/master/screenshot.png "screenshot")