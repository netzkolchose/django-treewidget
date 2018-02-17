from __future__ import unicode_literals
from django.forms.widgets import SelectMultiple, Select
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.db import models
from django.conf import settings
from json import dumps
from django.utils.encoding import force_text
from django.urls import reverse, NoReverseMatch
from treewidget.helper import (get_treetype, get_orderattr, get_orderattr_signs,
                               get_appmodel, get_attribute, get_parent)


TREEOPTIONS = {
    'plugins': ['wholerow'],
    'core': {
        'themes': {'icons': False, 'dots': False},
        'check_callback': True,
        'multiple': True,
        'animation': False
    },
    'search': {'show_only_matches': True}
}


class TreeModelWidgetMixin(object):
    settings = {}
    treeoptions = ''
    multiple = False
    choices = None

    class Media:
        js = (
            'treewidget/prepare.js',
            'treewidget/jstree.min.js',
            'treewidget/default.js'
        )
        css = {'screen': (
            'treewidget/themes/default/style.css',
            'treewidget/default.css'
        )}

    # TODO: move heavy db related stuff elsewhere to get more reusable widget code
    def get_drawable_queryset(self, selected):
        qs = self.choices.queryset
        model = qs.model

        if not selected:
            selected = []
        elif not hasattr(selected, '__iter__'):
            selected = [selected]
        selected = list(map(str, selected))  # convert to str make easy comparison with str(e.pk)

        # rebuild qs to ensure we can actually draw a correct tree structure
        # this imports possibly imports nodes not contained in the original queryset,
        # we mark those later as disabled (not selectable)
        orig_pks = set(get_attribute(qs, 'pk'))
        ids = set()
        for el in qs:
            ids.add(el.pk)
            ids.update(get_attribute(el.get_ancestors(), 'pk'))

        # get parents too, if only a sub is selected
        if selected:
            if not qs.exists():
                _ids = zip(*qs.values_list('pk'))
                if _ids:
                    ids.update(_ids[0])
            for el in selected:
                try:
                    el = model.objects.get(pk=el)
                    ids.add(el.pk)
                    ids.update(get_attribute(el.get_ancestors(), 'pk'))
                except model.DoesNotExist:
                    pass
        # new queryset
        qs = model.objects.filter(pk__in=ids)

        # The added nodes can be enabled by setting choices.queryset
        # to the new queryset, so the select field will see these options too.
        # To write those back to database, the queryset of the POST form
        # field or the clean method needs to be adjusted as well.

        # disabled nodes - difference of orig to new queryset
        disabled = set(get_attribute(qs, 'pk')) - orig_pks
        return qs, selected, disabled

    # TODO: cleanup this mess and make it public API
    def node_formatter(self, _id, el, qs, treetype, selected, disabled):
        pk = 'treewidget_%s_%s' % (_id, el.pk)
        parent = get_parent(el, treetype)
        parent_pk = 'treewidget_%s_%s' % (_id, parent.pk) if parent else '#'
        return {
            'id': pk,
            'parent': parent_pk,
            'text': escape(force_text(el)),
            'data': {
                'sort': get_orderattr(el, qs.model) if self.settings.get('sort') else []
            },
            'state': {
                'selected': True if str(el.pk) in selected else False,
                'disabled': True if el.pk in disabled else False
            }
        }

    def _get_mixin_context(self, name, selected, qs, disabled, attrs=None):
        # need something like a unique id, use name if none in attrs
        if not attrs:
            attrs = {'id': name}

        # try to get ajax urls
        try:
            update_url = reverse('treewidget.get_node')
            move_url = reverse('treewidget.move_node')
        except NoReverseMatch:
            update_url = ''
            move_url = ''

        # load settings if not supplied
        if not self.settings and hasattr(settings, 'TREEWIDGET_SETTINGS'):
            self.settings = settings.JSTREEWIDGET_SETTINGS
        if not self.treeoptions:
            self.treeoptions = dumps(settings.JSTREEWIDGET_TREEOPTIONS
                if hasattr(settings, 'TREEWIDGET_TREEOPTIONS') else TREEOPTIONS)

        # additional settings for JS
        additional = {
            'id': attrs.get('id'),
            'appmodel': get_appmodel(self.choices.queryset.model),
            'disabled': attrs.get('disabled', False),
            'multiple': self.multiple,
            'search': self.settings.get('search', False),
            'show_buttons': self.settings.get('show_buttons', False),
            'sort': get_orderattr_signs(self.choices.queryset.model)
                        if self.settings.get('sort') else [],
            'updateurl': update_url,
            'dnd': self.settings.get('dnd', False),
            'moveurl': move_url if self.settings.get('dnd') else '',
        }

        _id = attrs.get('id')
        treetype = get_treetype(qs.model)

        # data for JS
        json_data = '{"settings": %s, "additional": %s, "treedata": %s}' % (
            self.treeoptions,
            dumps(additional),
            dumps([self.node_formatter(_id, el, qs, treetype, selected, disabled) for el in qs])
        )

        # treewidget context
        return {
            'id': attrs.get('id'),
            'search': self.settings.get('search', False),
            'show_buttons': self.settings.get('show_buttons', False),
            'json_data': mark_safe(json_data.replace('</script', '<\/script')),
            'disabled': attrs.get('disabled')
        }


# model widgets
class TreeSelectMultiple(SelectMultiple, TreeModelWidgetMixin):
    template_name = 'treewidget.html'
    multiple = True

    def get_context(self, name, value, attrs):
        drawable_qs, selected, disabled = self.get_drawable_queryset(value)
        ctx = super(TreeSelectMultiple, self).get_context(name, value, attrs)
        ctx['widget']['treewidget'] = self._get_mixin_context(
            name, selected, drawable_qs, disabled, attrs)
        ctx['widget']['treewidget']['super_template'] = super(TreeSelectMultiple, self).template_name
        return ctx


class TreeSelect(Select, TreeModelWidgetMixin):
    template_name = 'treewidget.html'
    multiple = False

    def get_context(self, name, value, attrs):
        drawable_qs, selected, disabled = self.get_drawable_queryset(value)
        ctx = super(TreeSelect, self).get_context(name, value, attrs)
        ctx['widget']['treewidget'] = self._get_mixin_context(
            name, selected, drawable_qs, disabled, attrs)
        ctx['widget']['treewidget']['super_template'] = super(TreeSelect, self).template_name
        return ctx


# model form fields
class TreeModelFieldMixin(object):
    def __init__(self, queryset, *args, **kwargs):
        if hasattr(queryset, 'model') and get_treetype(queryset.model) == 'mptt':
            mptt_opts = queryset.model._mptt_meta
            queryset = queryset.order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr)
        super(TreeModelFieldMixin, self).__init__(queryset, *args, **kwargs)


class TreeModelMultipleField(TreeModelFieldMixin, ModelMultipleChoiceField):
    widget = TreeSelectMultiple

    def __init__(self, queryset, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeModelMultipleField, self).__init__(queryset, *args, **kwargs)
        self.widget.settings = self.settings
        self.widget.treeoptions = self.treeoptions


class TreeModelField(TreeModelFieldMixin, ModelChoiceField):
    widget = TreeSelect

    def __init__(self, queryset, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeModelField, self).__init__(queryset, *args, **kwargs)
        self.widget.settings = self.settings
        self.widget.treeoptions = self.treeoptions


# model fields
class TreeForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeForeignKey, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['form_class'] = TreeModelField
        kwargs['settings'] = self.settings
        kwargs['treeoptions'] = self.treeoptions
        return super(TreeForeignKey, self).formfield(**kwargs)


class TreeOneToOneField(models.OneToOneField):
    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeOneToOneField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['form_class'] = TreeModelField
        kwargs['settings'] = self.settings
        kwargs['treeoptions'] = self.treeoptions
        return super(TreeOneToOneField, self).formfield(**kwargs)


class TreeManyToManyField(models.ManyToManyField):
    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeManyToManyField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['form_class'] = TreeModelMultipleField
        kwargs['settings'] = self.settings
        kwargs['treeoptions'] = self.treeoptions
        return super(TreeManyToManyField, self).formfield(**kwargs)
