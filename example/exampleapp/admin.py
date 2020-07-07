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
        form.base_fields['parent'].queryset = Mptt.objects.exclude(pk=1)  # filtered qs
        return form


class TreebeardmpAdmin(TreeAdmin):
    form = movenodeform_factory(Treebeardmp)


class TreebeardalAdmin(TreeAdmin):
    form = movenodeform_factory(Treebeardal)


class TreebeardnsAdmin(TreeAdmin):
    form = movenodeform_factory(Treebeardns)


class ExampleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('mptt', 'treebeardmp', 'treebeardal', 'treebeardns')
        }),
        ('M2M', {
            'classes': ('collapse',),
            'fields': ('mptt_many', 'treebeardmp_many', 'treebeardal_many', 'treebeardns_many'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super(ExampleAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields['treebeardmp'].queryset = Treebeardmp.objects.exclude(pk=1)  # filtered qs
        return form


admin.site.register(Mptt, MpttAdmin)
admin.site.register(Treebeardmp, TreebeardmpAdmin)
admin.site.register(Treebeardal, TreebeardalAdmin)
admin.site.register(Treebeardns, TreebeardnsAdmin)
admin.site.register(Example, ExampleAdmin)
