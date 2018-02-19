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

    def render(self, node):
        """
        Render method of a single node.
        NOTE: `node` is a `tree.TreeNode` object.
        Override the render method if you need other data in jstree.
        :param node:
        :return:
        """
        return {
            'id': self.ID_TEMPLATE % (self.attr_name, node.node.pk),
            'parent': self.ID_TEMPLATE % (self.attr_name, node.parent.node.pk) if node.parent else '#',
            'text': escape(force_text(node)),
            'data': {
                'sort': node.ordering if self.settings.get('sort') else []
            },
            'state': {
                'selected': True if str(node.node.pk) in self.selected else False,
                'disabled': True if node.node.pk in self.disabled else False
            }
        }
