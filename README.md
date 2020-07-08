## treewidget for Django ##

Provides the model fields TreeForeignKey, TreeOneToOneField, TreeManyToManyField
for tree models with a tree widget for django. Uses `jstree` (thanks to vakata).

Tested with django-mptt 0.11.0 and django-treebeard 4.3.1 with Django 2.2 & 3.0.


### Installation ###

- `pip install django-treewidget`
- place `'treewidget'` in `INSTALLED_APPS`
- for AJAX tree updates add the routes to your urls.py,
e.g. `url(r'^treewidget/', include('treewidget.urls'))`


### Usage ###

Just replace any foreign key, m2m or one2one tree model field with the provided counterpart.
jstree depends on jQuery to work. This module does not provide a jQuery version, use the
admin version or place your own version along with your other assets.


### Customization ###

The fields understand two additional arguments:

- **settings**: Dictionary containing the optional boolean values for 'show_buttons'
(shows "Expand", "Collapse" and "Selected" buttons), 'search' (for in-tree search),
'dnd' (drag and drop support) and 'sort' (apply tree order in frontend). Defaults to `{}`.
- **treeoptions**: Settings directly applied to `jstree`. Must be a JSON string, if given as
argument to a field, otherwise a python dictionary. Defaults to `treewidget.fields.TREEOPTIONS`.
Note that some widget settings will override treeoptions to keep working.

Both settings can be provided project wide in settings.py as `TREEWIDGET_SETTINGS` and
`TREEWIDGET_TREEOPTIONS`.

It is possible to render a deeper nested subtree by overriding the default
formatter. Just set the parent id to '#' in the formatter's `render` method for the entries,
that should appear at top level.

**NOTE**: If you use a prefiltered queryset which data does not form a well-formed tree
containing all parents up to the top level, jstree cannot render it correctly.
With 'filtered' in settings set to `True` those querysets will be rendered by
adding missing nodes as not selectable. Make sure, that this does not leak
sensitive tree data (if so, resort to subtree rendering).

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

![screenshot](https://github.com/jerch/django-treewidget/raw/master/screenshot.png  "screenshot")


To run the provided example project:

```bash
$> cd example
$> pip install Django~=2.2              # or 3.0
$> pip install -r requirements.txt
$> ./manage.py migrate
$> ./manage.py createsuperuser
$> ./manage.py loaddata initial_data
$> ./manage.py runserver
```

and point your browser to `http://localhost:8000/admin/exampleapp/example/add/`.
After login you see the widgets in action with different settings.
Also see `exampleapp.Example` model in admin to get an idea of several tree rendering options.