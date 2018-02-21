# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.forms.widgets import SelectMultiple, Select
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.utils.safestring import mark_safe
from django.db import models
from django.conf import settings
from json import dumps
from django.urls import reverse, NoReverseMatch
from treewidget.tree import TreeQuerySet, get_treetype, MPTT
from treewidget.formatters import SelectFormatter
from operator import attrgetter


def get_attr_iter(it, attr):
    return map(attrgetter(attr), it)


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


class TreeSelectWidgetMixin(object):
    """
    Mixin class for SelectWidgets to provide the tree functionality.
    """
    settings = {}
    treeoptions = ''
    multiple = False
    choices = None

    class Media:
        js = (
            'treewidget/prepare.js',
            'treewidget/jstree.min.js',
            'treewidget/default.js',
        )
        css = {'screen': (
            'treewidget/themes/default/style.css',
            'treewidget/default.css'
        )}

    # TODO: move heavy db related stuff elsewhere to get more reusable widget code
    def get_drawable_queryset(self, selected):
        """
        Helper method to ensure the data is drawable as a tree. To achieve this,
        the method checks the ancestors of every entry in the original queryset
        and the selected values. A missing value will be added and marked as
        not selectable in the final tree.
        NOTE: This method might add data not contained in the original queryset.
        :param selected:
        :return: (new queryset, selected values, disabled values)
        """
        qs = self.choices.queryset
        model = qs.model

        if not selected:
            selected = []
        elif not hasattr(selected, '__iter__'):
            selected = [selected]
        selected = list(map(str, selected))  # convert to str make easy comparison with str(e.pk)

        # rebuild queryset to ensure we can actually draw a correct tree structure
        # this possibly imports nodes not contained in the original queryset,
        # we mark those later as disabled (not selectable)
        orig_pks = set(get_attr_iter(qs, 'pk'))
        ids = set()
        for el in qs:
            ids.add(el.pk)
            ids.update(get_attr_iter(el.get_ancestors(), 'pk'))

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
                    ids.update(get_attr_iter(el.get_ancestors(), 'pk'))
                except model.DoesNotExist:
                    pass
        # new queryset
        qs = model.objects.filter(pk__in=ids)

        # The added nodes can be enabled by setting choices.queryset
        # to the new queryset, so the select field will see these options too.
        # To write those back to database, the queryset of the POST form
        # field or the clean method needs to be adjusted as well.

        # disabled nodes - difference of new queryset to orig queryset
        disabled = set(get_attr_iter(qs, 'pk')) - orig_pks
        return qs, selected, disabled

    def _get_mixin_context(self, name, qs, selected, disabled, attrs=None):
        """
        Method to build the final tree widget context data.
        The tree data is provided to jstree as json object in the DOM.
        For a single node the datais rendered by `formatters.SelectFormatter`.
        :param name:
        :param qs:
        :param selected:
        :param disabled:
        :param attrs:
        :return:
        """
        # need something like a unique id, use name if none in attrs
        if not attrs or not attrs.get('id'):
            attrs = {'id': name}
        attr_name = attrs.get('id')

        # try to get ajax urls
        try:
            update_url = reverse('treewidget.get_node')
            move_url = reverse('treewidget.move_node')
        except NoReverseMatch:
            update_url = ''
            move_url = ''

        # load settings if not supplied
        if not self.settings and hasattr(settings, 'TREEWIDGET_SETTINGS'):
            self.settings = settings.TREEWIDGET_SETTINGS
        if not self.treeoptions:
            self.treeoptions = dumps(settings.TREEWIDGET_TREEOPTIONS
                if hasattr(settings, 'TREEWIDGET_TREEOPTIONS') else TREEOPTIONS)

        # use TreeQuerySet as abstraction layer for unique access in formatter
        qs = TreeQuerySet(qs)
        formatter = (self.settings.get('formatter') or SelectFormatter)(
            attr_name, selected, disabled, self.settings)

        # additional settings for JS
        additional = {
            'id': attr_name,
            'appmodel': qs.appmodel,
            'disabled': attrs.get('disabled', False),
            'multiple': self.multiple,
            'search': self.settings.get('search', False),
            'show_buttons': self.settings.get('show_buttons', False),
            'sort': qs.ordering_signs if self.settings.get('sort') else [],
            'updateurl': update_url,
            'dnd': self.settings.get('dnd', False),
            'moveurl': move_url if self.settings.get('dnd') else '',
        }

        # data for JS
        json_data = '{"settings": %s, "additional": %s, "treedata": %s}' % (
            self.treeoptions,
            dumps(additional),
            dumps([formatter.render(el) for el in qs])
        )

        # treewidget context
        return {
            'id': attr_name,
            'search': self.settings.get('search', False),
            'show_buttons': self.settings.get('show_buttons', False),
            'json_data': mark_safe(json_data.replace('</script', '<\/script')),
            'disabled': attrs.get('disabled')
        }


class TreeSelectMultiple(SelectMultiple, TreeSelectWidgetMixin):
    template_name = 'treewidget/treewidget.html'
    multiple = True

    def get_context(self, name, value, attrs):
        drawable_qs, selected, disabled = self.get_drawable_queryset(value)
        ctx = super(TreeSelectMultiple, self).get_context(name, value, attrs)
        ctx['widget']['treewidget'] = self._get_mixin_context(
            name, drawable_qs, selected, disabled, attrs)
        ctx['widget']['treewidget']['super_template'] = super(TreeSelectMultiple, self).template_name
        return ctx


class TreeSelect(Select, TreeSelectWidgetMixin):
    template_name = 'treewidget/treewidget.html'
    multiple = False

    def get_context(self, name, value, attrs):
        drawable_qs, selected, disabled = self.get_drawable_queryset(value)
        ctx = super(TreeSelect, self).get_context(name, value, attrs)
        ctx['widget']['treewidget'] = self._get_mixin_context(
            name, drawable_qs, selected, disabled, attrs)
        ctx['widget']['treewidget']['super_template'] = super(TreeSelect, self).template_name
        return ctx


class TreeModelFieldMixin(object):
    def __init__(self, queryset, *args, **kwargs):
        if hasattr(queryset, 'model') and get_treetype(queryset.model) == MPTT:
            mptt_opts = queryset.model._mptt_meta
            queryset = queryset.order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr)
        super(TreeModelFieldMixin, self).__init__(queryset, *args, **kwargs)


class TreeModelMultipleChoiceField(TreeModelFieldMixin, ModelMultipleChoiceField):
    widget = TreeSelectMultiple

    def __init__(self, queryset, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeModelMultipleChoiceField, self).__init__(queryset, *args, **kwargs)
        self.widget.settings = self.settings
        self.widget.treeoptions = self.treeoptions


class TreeModelChoiceField(TreeModelFieldMixin, ModelChoiceField):
    widget = TreeSelect

    def __init__(self, queryset, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeModelChoiceField, self).__init__(queryset, *args, **kwargs)
        self.widget.settings = self.settings
        self.widget.treeoptions = self.treeoptions


class TreeForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeForeignKey, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['form_class'] = TreeModelChoiceField
        kwargs['settings'] = self.settings
        kwargs['treeoptions'] = self.treeoptions
        return super(TreeForeignKey, self).formfield(**kwargs)


class TreeOneToOneField(models.OneToOneField):
    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeOneToOneField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['form_class'] = TreeModelChoiceField
        kwargs['settings'] = self.settings
        kwargs['treeoptions'] = self.treeoptions
        return super(TreeOneToOneField, self).formfield(**kwargs)


class TreeManyToManyField(models.ManyToManyField):
    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeManyToManyField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs['form_class'] = TreeModelMultipleChoiceField
        kwargs['settings'] = self.settings
        kwargs['treeoptions'] = self.treeoptions
        return super(TreeManyToManyField, self).formfield(**kwargs)
