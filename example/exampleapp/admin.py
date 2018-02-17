# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Mptt, Treebeardmp, Treebeardal, Treebeardns, Example
from mptt.admin import DraggableMPTTAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory


class MpttAdmin(DraggableMPTTAdmin):
    list_display = (
        'tree_actions',
        'indented_title',
    )
    list_display_links = (
        'indented_title',
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super(MpttAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields['parent'].queryset = Mptt.objects.exclude(pk=1)
        return form


class TreebeardmpAdmin(TreeAdmin):
    form = movenodeform_factory(Treebeardmp)


class TreebeardalAdmin(TreeAdmin):
    form = movenodeform_factory(Treebeardal)


class TreebeardnsAdmin(TreeAdmin):
    form = movenodeform_factory(Treebeardns)


admin.site.register(Mptt, MpttAdmin)
admin.site.register(Treebeardmp, TreebeardmpAdmin)
admin.site.register(Treebeardal, TreebeardalAdmin)
admin.site.register(Treebeardns, TreebeardnsAdmin)
admin.site.register(Example, admin.ModelAdmin)
