# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from treewidget.fields import TreeForeignKey, TreeManyToManyField #, TreebeardForeignKey

# mptt examples
from mptt.models import MPTTModel


class Region(MPTTModel):
    class Meta:
        verbose_name = 'region'
        verbose_name_plural = 'regions'
    name = models.CharField(max_length=63)
    parent = TreeForeignKey('self', blank=True, null=True,
                            settings={'show_buttons': True, 'search': True, 'sort': True, 'dnd': True})

    #class MPTTMeta:
    #    order_insertion_by=['-name']

    def __unicode__(self):
        return self.name


class City(models.Model):
    class Meta:
        verbose_name = 'city'
        verbose_name_plural = 'cities'
    name = models.CharField(max_length=63)
    regions = TreeManyToManyField(Region, related_name='cities',
                                  settings={'show_buttons': True, 'search': True})

    def __unicode__(self):
        return self.name


City.regions.through.__unicode__ = lambda obj: '%s - %s' % (obj.region.name, obj.city.name)


# treebeard examples
from treebeard.mp_tree import MP_Node
from treebeard.al_tree import AL_Node
from treebeard.forms import MoveNodeForm


class Category(MP_Node):
    name = models.CharField(max_length=30)

    node_order_by = ['name']

    def __unicode__(self):
        return '%s' % self.name


class AL_TestNodeSorted(AL_Node):
    parent = models.ForeignKey('self',
                               related_name='children_set',
                               null=True,
                               db_index=True)
    node_order_by = ['val1', 'val2', 'desc']
    val1 = models.IntegerField()
    val2 = models.IntegerField()
    desc = models.CharField(max_length=255)

    def __unicode__(self):
        return '%s' % self.desc


class Bla(models.Model):
    name = models.CharField(max_length=30)
    category = TreeForeignKey(Category, settings={'hidable': True, 'sort': True, 'dnd': True, 'search': True})
    #al = models.ForeignKey(AL_TestNodeSorted, blank=True, null=True)
    al = TreeForeignKey(AL_TestNodeSorted, settings={'hidable': True, 'sort': True, 'dnd': True, 'search': True})
