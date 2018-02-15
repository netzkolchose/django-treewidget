## treewidget for Django ##

tested with Django 1.11

### Requirements ###

- django-mptt
- jquery

### Provides ###

- model fields: TreeForeignKey, TreeOneToOneField, TreeManyToManyField
- form fields: TreeField, TreeMultipleField
- widgets: TreeWidget, TreeMultipleWidget
- treebeard and mptt support

### TODO ###

- respect siblings order during insert
- move subtree with node


### Customize ###

- in settings.py:
TREEWIDGET_SETTINGS
    - show_buttons: show expand|collapse|Selected buttons
    - search: show search field for in tree search
    - hidable: hide tree in admin form
TREEWIDGET_TREEOPTIONS
    - settings for `jstree()`

- per argument:
```python
TreeForeignKey(..., settings={...}, treeoptions='...')
```