# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.html import escape
from django.utils.encoding import force_text


class SelectFormatter(object):
    ID_TEMPLATE = 'treewidget_%s_%s'

    def __init__(self, attr_name, selected, disabled, settings):
        self.attr_name = attr_name
        self.selected = selected
        self.disabled = disabled
        self.settings = settings or {}

    def render(self, el):
        return {
            'id': self.ID_TEMPLATE % (self.attr_name, el.node.pk),
            'parent': self.ID_TEMPLATE % (self.attr_name, el.parent.node.pk) if el.parent else '#',
            'text': escape(force_text(el)),
            'data': {
                'sort': el.ordering if self.settings.get('sort') else []
            },
            'state': {
                'selected': True if str(el.node.pk) in self.selected else False,
                'disabled': True if el.node.pk in self.disabled else False
            }
        }
