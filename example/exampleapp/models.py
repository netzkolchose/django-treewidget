from django.db import models
from mptt.models import MPTTModel
from treebeard.mp_tree import MP_Node
from treebeard.al_tree import AL_Node
from treebeard.ns_tree import NS_Node
from treewidget.fields import TreeForeignKey, TreeManyToManyField


# django-mptt
class Mptt(MPTTModel):
    name = models.CharField(max_length=32)
    parent = TreeForeignKey(
        'self', blank=True, null=True, on_delete=models.CASCADE,
        settings={'filtered': True}, help_text='filtered (exclude pk=1 from parent, see admin.py)')

    def __str__(self):
        return self.name


# django-treebeard
class Treebeardmp(MP_Node):
    name = models.CharField(max_length=32)

    def __str__(self):
        return '%s' % self.name


class Treebeardal(AL_Node):
    name = models.CharField(max_length=32)
    parent = models.ForeignKey('self', related_name='children_set', null=True,
                               db_index=True, on_delete=models.CASCADE)
    sib_order = models.PositiveIntegerField()

    def __str__(self):
        return '%s' % self.name


class Treebeardns(NS_Node):
    name = models.CharField(max_length=32)

    def __str__(self):
        return '%s' % self.name


class Example(models.Model):
    mptt = TreeForeignKey(
        Mptt, on_delete=models.CASCADE,
        help_text="default settings: no buttons, no search, not filtered, no drag'n drop, no sort")
    treebeardmp = TreeForeignKey(
        Treebeardmp, on_delete=models.CASCADE,
        settings={'show_buttons': True, 'filtered': True},
        help_text="settings: show_buttons, filtered (exclude pk=1, see admin.py)")
    treebeardal = TreeForeignKey(
        Treebeardal, on_delete=models.CASCADE,
        settings={'search': True, 'dnd': True, 'sort': True},
        help_text="settings: search, drag'n drop, sort")
    treebeardns = TreeForeignKey(
        Treebeardns, on_delete=models.CASCADE,
        settings={'dnd': True},
        help_text="settings: drag'n drop")
    mptt_many = TreeManyToManyField(
        Mptt, related_name='example_many',
        settings={'show_buttons': True, 'search': True, 'dnd': True},
        help_text="settings: buttons, search, drag'n drop<br>")
    treebeardmp_many = TreeManyToManyField(Treebeardmp, related_name='example_many')
    treebeardal_many = TreeManyToManyField(Treebeardal, related_name='example_many')
    treebeardns_many = TreeManyToManyField(Treebeardns, related_name='example_many')
