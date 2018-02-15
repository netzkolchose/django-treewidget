# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Region, City, Category, Bla, AL_TestNodeSorted
from mptt.admin import DraggableMPTTAdmin
from treewidget.fields import TreeModelField


class RegionAdmin(DraggableMPTTAdmin):
    list_display = (
        'tree_actions',
        'indented_title',
    )
    list_display_links = (
        'indented_title',
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super(RegionAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['parent'].widget.can_delete_related = True
        return form


admin.site.register(Region, RegionAdmin)
admin.site.register(City, admin.ModelAdmin)

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory


class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)

    def get_form(self, request, obj=None, **kwargs):
        print
        print self.get_queryset(request)
        form = super(CategoryAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['_ref_node_id'] = TreeModelField(self.get_queryset(request))
        return form

class AL_TestNodeSortedAdmin(TreeAdmin):
    form = movenodeform_factory(AL_TestNodeSorted)

    def get_form(self, request, obj=None, **kwargs):
        print
        print self.get_queryset(request)
        form = super(AL_TestNodeSortedAdmin, self).get_form(request, obj, **kwargs)
        #form.base_fields['_ref_node_id'] = TreeModelField(self.get_queryset(request))
        return form


admin.site.register(Category, CategoryAdmin)
admin.site.register(AL_TestNodeSorted, AL_TestNodeSortedAdmin)

class BlaAdmin(admin.ModelAdmin):

    def get_form(self, request, obj=None, **kwargs):
        form = super(BlaAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['category'].widget.can_delete_related = True
        return form

admin.site.register(Bla, BlaAdmin)
