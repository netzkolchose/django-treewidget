# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from mptt.models import MPTTModel
from treebeard.mp_tree import MP_Node
from treebeard.al_tree import AL_Node
from treebeard.ns_tree import NS_Node
from treewidget.fields import TreeForeignKey, TreeManyToManyField
from django.utils.encoding import python_2_unicode_compatible


# django-mptt
@python_2_unicode_compatible
class Mptt(MPTTModel):
    name = models.CharField(max_length=32)
    parent = TreeForeignKey(
        'self', blank=True, null=True, on_delete=models.CASCADE, settings={'filtered': True})

    def __str__(self):
        return self.name


# django-treebeard
@python_2_unicode_compatible
class Treebeardmp(MP_Node):
    name = models.CharField(max_length=32)

    def __str__(self):
        return '%s' % self.name


@python_2_unicode_compatible
class Treebeardal(AL_Node):
    name = models.CharField(max_length=32)
    parent = models.ForeignKey('self', related_name='children_set', null=True,
                               db_index=True, on_delete=models.CASCADE)
    sib_order = models.PositiveIntegerField()

    def __str__(self):
        return '%s' % self.name


@python_2_unicode_compatible
class Treebeardns(NS_Node):
    name = models.CharField(max_length=32)

    def __str__(self):
        return '%s' % self.name


class Example(models.Model):
    mptt = TreeForeignKey(Mptt, on_delete=models.CASCADE)
    treebeardmp = TreeForeignKey(Treebeardmp, on_delete=models.CASCADE,
                                 settings={'show_buttons': True, 'filtered': True})
    treebeardal = TreeForeignKey(Treebeardal, on_delete=models.CASCADE,
                                 settings={'search': True, 'dnd': True, 'sort': True})
    treebeardns = TreeForeignKey(Treebeardns, on_delete=models.CASCADE,
                                 settings={'dnd': True})
    mptt_many = TreeManyToManyField(Mptt, related_name='example_many',
                                    settings={'show_buttons': True, 'search': True, 'dnd': True})
    treebeardmp_many = TreeManyToManyField(Treebeardmp, related_name='example_many')
    treebeardal_many = TreeManyToManyField(Treebeardal, related_name='example_many')
    treebeardns_many = TreeManyToManyField(Treebeardns, related_name='example_many')
