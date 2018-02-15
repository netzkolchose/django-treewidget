from django.forms.widgets import SelectMultiple, Select, Input
from django.forms import CharField, ModelChoiceField, ModelMultipleChoiceField
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.db import models
from django.template import loader
from django.conf import settings
from json import dumps
from django.urls import reverse, NoReverseMatch
from treewidget.helper import (get_treetype, get_level, get_orderattr_json, get_orderattr_signs,
                               get_appmodel, get_attribute)


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
    _mixin_template_name = 'treewidget.html'
    settings = {}
    treeoptions = ''

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

    def get_treelist(self, selected, _id):
        # choices are tree ordered, current is excluded
        qs = self.choices.queryset
        model = qs.model

        if not selected:
            selected = []
        elif not hasattr(selected, '__iter__'):
            selected = [selected]
        selected = map(str, selected)  # convert to str make easy comparison with str(e.pk)

        # rebuild qs from elements and selected with root nodes
        # to ensure we can actually draw a tree
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
        for e in qs:
            if hasattr(e, 'parent'):
                print e.id, e.parent.pk if e.parent else 0, e.get_depth(), e

        # walk the queryset and build tree
        treetype = get_treetype(model)
        old_level = 1 if treetype == 'treebeard' else 0
        stack = []
        for i, e in enumerate(qs):
            new_level = get_level(e, treetype)
            if new_level > old_level:
                stack.append(u'<ul>' * (new_level - old_level))
            elif new_level < old_level:
                stack.append(u'</li></ul></li>' * (old_level - new_level))
            else:
                if i:
                    stack.append(u'</li>')
            stack.append(
                u'<li id="treewidget_%s_%d" data-jstree="%s"%s>'
                % (_id, e.id,
                   escape(u'{"selected":%s}' % u'true' if str(e.pk) in selected else u'false'),
                   u' data-sort="%s"' % escape(get_orderattr_json(e, model))
                        if self.settings.get('sort', None) else u''
                   )
            )
            stack.append(escape(unicode(e)))
            old_level = new_level
        stack.append(u'</li>')
        stack.append(u'</ul></li>' * old_level)
        return u'<ul style="display:none">%s</ul>' % ''.join(stack)

    def _get_mixin_context(self, name, value, attrs=None):
        try:
            update_url = reverse('treewidget.get_node')
            move_url = reverse('treewidget.move_node')
        except NoReverseMatch:
            update_url = ''
            move_url = ''
        if not self.settings and hasattr(settings, 'TREEWIDGET_SETTINGS'):
            self.settings = settings.JSTREEWIDGET_SETTINGS
        if not self.treeoptions:
            self.treeoptions = dumps(settings.JSTREEWIDGET_TREEOPTIONS
                if hasattr(settings, 'TREEWIDGET_TREEOPTIONS') else TREEOPTIONS)
        start_hidden = self.settings.get('start_hidden', False)
        return {'widget':
            {
                'name': name,
                'value': value,
                'attrs': attrs,
                'settings': escape(self.treeoptions),
                'has_data': bool(value) if start_hidden == 'data' else not start_hidden,
                'content': mark_safe(self.get_treelist(value, attrs.get(u'id') if attrs else None)),
                'search': self.settings.get('search', False),
                'sort': get_orderattr_signs(self.choices.queryset.model) if self.settings.get('sort', None) else '[]',
                'dnd': 'true' if self.settings.get('dnd', False) else 'false',
                'show_buttons': self.settings.get('show_buttons', False),
                'hide': self.settings.get('hidable', False),
                'update_url': update_url,
                'move_url': move_url if self.settings.get('dnd', False) else '',
                'appmodel': get_appmodel(self.choices.queryset.model)
            }
        }


# model widgets
class TreeModelMultipleWidget(TreeModelWidgetMixin, SelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        context = self._get_mixin_context(name, value, attrs)
        context['widget']['multiple'] = True
        context['widget']['super_content'] = super(TreeModelMultipleWidget, self).render(
            name, value, attrs)
        template = loader.get_template(self._mixin_template_name).render(context)
        return mark_safe(template)


class TreeModelWidget(TreeModelWidgetMixin, Select):
    def render(self, name, value, attrs=None, choices=()):
        context = self._get_mixin_context(name, value, attrs)
        context['widget']['multiple'] = False
        context['widget']['super_content'] = super(TreeModelWidget, self).render(
            name, value, attrs)
        template = loader.get_template(self._mixin_template_name).render(context)
        return mark_safe(template)


# model form fields
class TreeModelFieldMixin(object):
    def __init__(self, queryset, *args, **kwargs):
        if hasattr(queryset, 'model') and get_treetype(queryset.model) == 'mptt':
            mptt_opts = queryset.model._mptt_meta
            queryset = queryset.order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr)
        super(TreeModelFieldMixin, self).__init__(queryset, *args, **kwargs)


class TreeModelMultipleField(TreeModelFieldMixin, ModelMultipleChoiceField):
    widget = TreeModelMultipleWidget

    def __init__(self, queryset, *args, **kwargs):
        self.settings = kwargs.pop('settings', {})
        self.treeoptions = kwargs.pop('treeoptions', '')
        super(TreeModelMultipleField, self).__init__(queryset, *args, **kwargs)
        self.widget.settings = self.settings
        self.widget.treeoptions = self.treeoptions


class TreeModelField(TreeModelFieldMixin, ModelChoiceField):
    widget = TreeModelWidget

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


# non model widgets and fields
class FreeTreeWidget(Input):
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

    def render(self, name, value, attrs=None, renderer=None):
        own = mark_safe('<div id="klaus_%s" class="klaus"></div>' % name)
        attrs.setdefault('style', '')
        attrs['style'] += 'display: none'
        return own + super(FreeTreeWidget, self). render(name, value, attrs, renderer)


class FreeTreeField(CharField):
    widget = FreeTreeWidget