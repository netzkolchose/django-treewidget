# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.html import escape
from django.utils.encoding import force_text


class SelectFormatter(object):
    """
    Node formatter in conjunction with `fields.TreeSelect`
    and `fields.TreeSelectMultiple` fields.
    The formatter gets initialized with the attribute name of
    the current field, the selected values (pk values normally),
    disabled pks and the field settings.

    NOTE: Always build the HTML ids with the template string
    `ID_TEMPLATE`, otherwise javascript will not recognize the
    ids correctly (Hardcoded to `'treewidget_<attr_name>_<pk value>'`)
    """
    ID_TEMPLATE = 'treewidget_%s_%s'

    def __init__(self, attr_name, selected, disabled, settings):
        self.attr_name = attr_name
        self.selected = selected
        self.disabled = disabled
        self.settings = settings or {}

    def render(self, queryset):
        """
        Render method of tree data for `jstree`.
        NOTE: `queryset` is a `tree.TreeQueryset` object.
        To avoid expensive database lookups, the parent pk
        is accessible as `node.node._parent_pk`.
        """
        for node in queryset:
            id = self.ID_TEMPLATE % (self.attr_name, node.pk)
            parent = '#'
            #try:
            if node.node._parent_pk:
                parent = self.ID_TEMPLATE % (self.attr_name, node.node._parent_pk)
            #except AttributeError:
            #    parent_obj = node.parent
            #    if parent_obj:
            #        parent = self.ID_TEMPLATE % (self.attr_name, parent_obj.node.pk)
            yield {
                'id': id,
                'parent': parent,
                'text': escape(force_text(node)),
                'data': {
                    'sort': node.ordering if self.settings.get('sort') else []
                },
                'state': {
                    'selected': True if str(node.pk) in self.selected else False,
                    'disabled': True if node.pk in self.disabled else False
                }
            }
