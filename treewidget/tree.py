# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db.models import QuerySet
from django.utils.encoding import python_2_unicode_compatible

try:
    from treebeard.models import Node as TreebeardNode
    HAS_TREEBEARD = True
except ImportError:
    HAS_TREEBEARD = False

try:
    from mptt.models import MPTTModel
    HAS_MPTT = True
except ImportError:
    HAS_MPTT = False


TREEBEARD = {
    'root_level': 1,
    'model': {
        'order'     :   lambda model: model.node_order_by or []
    },
    'node': {
        'parent'    :   lambda node: node.get_parent(),
        'prev'      :   lambda node: node.get_prev_sibling(),
        'next'      :   lambda node: node.get_next_sibling(),
        'ancestors' :   lambda node: force_treenode(node.get_ancestors()),
        'descendants':  lambda node: force_treenode(node.get_descendants()),
        'level'     :   lambda node: node.get_depth(),
        'move'      :   lambda node: lambda target, pos: node.move(target, pos),
    },
}


MPTT = {
    'root_level': 0,
    'model': {
        'order'     :   lambda model: model._mptt_meta.order_insertion_by or []
    },
    'node': {
        'parent'    :   lambda node: getattr(node, node.__class__._mptt_meta.parent_attr, None),
        'prev'      :   lambda node: node.get_previous_sibling(),
        'next'      :   lambda node: node.get_next_sibling(),
        'ancestors' :   lambda node: node.get_ancestors(),
        'descendants':  lambda node: node.get_descendants(),
        'level'     :   lambda node: getattr(node, node.__class__._mptt_meta.level_attr, 0),
        'move'      :   lambda node: lambda target, pos: node.move_to(target, pos),
    },
}


class UnknownTreeImplementation(Exception):
    pass


def get_treetype(model):
    """
    Return the function mapping of the real model tree implementation.

    :raises UnknownTreeImplementation
    :param model:
    :return:
    """
    if HAS_TREEBEARD and issubclass(model, TreebeardNode):
        return TREEBEARD
    elif HAS_MPTT and issubclass(model, MPTTModel):
        return MPTT
    raise UnknownTreeImplementation


class TreeQuerySet(object):
    """
    Abstract model tree queryset proxy. It's main purpose is to decorate queryset methods
    in a way, that objects are returned as TreeNode proxy objects for
    common tree attribute access. The real model tree implementation must be known and
    `get_treetype` must return a method mapping for the real tree attributes
    (see `MPTT` and `TREEBEARD` for example definitions).

    The real queryset can be accessed via the `qs` attribute.
    """
    def __init__(self, qs, treetype=None):
        self.qs = qs
        self.qs_it = iter(self.qs)
        self.treetype = treetype or get_treetype(self.qs.model)

    def __getitem__(self, item):
        item = self.qs[item]
        if item:
            return TreeNode(item, self.qs.model, self.treetype)
        return item

    def __iter__(self):
        return self

    def __next__(self):
        try:
            node = next(self.qs_it)
            return TreeNode(node, self.qs.model, self.treetype)
        except StopIteration:
            self.qs_it = iter(self.qs)
            raise StopIteration

    def next(self):
        return self.__next__()

    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except AttributeError:
            attr = self.qs.__getattribute__(name)
            if callable(attr):
                return self.proxy(attr)
            return attr

    def proxy(self, attr):
        def f(*args, **kwargs):
            res = attr(*args, **kwargs)
            if isinstance(res, self.qs.__class__):
                return TreeQuerySet(res, self.treetype)
            if isinstance(res, self.qs.model):
                return TreeNode(res, self.qs.model, self.treetype)
            return res
        return f

    @property
    def ordering(self):
        return self.treetype['model']['order'](self.qs.model)

    @property
    def ordering_signs(self):
        return [-1 if attr.startswith('-') else 1 for attr in self.ordering]

    @property
    def appmodel(self):
        return '%s.%s' % (self.qs.model._meta.app_label, self.qs.model._meta.model_name)


@python_2_unicode_compatible
class TreeNode(object):
    """
    Abstract tree node proxy for common tree attribute access.
    The real tree node can be accessed via the `node` attribute.

    NOTE: Only typical tree node methods like get abstracted,
    if you need a specific value from a node, access it via `node`
    (e.g. `obj.node.pk` for the pk value).
    """
    def __init__(self, node, model=None, treetype=None):
        self.node = node
        self.model = model or self.node.__class__
        self.treetype = treetype or get_treetype(self.model)

    def _get_real(self, name):
        res = self.treetype['node'][name](self.node)
        if isinstance(res, QuerySet) and res.model == self.model:
            return TreeQuerySet(res, self.treetype)
        if isinstance(res, self.model):
            return TreeNode(res, self.model, self.treetype)
        return res

    def __str__(self):
        return '%s' % self.node

    @property
    def ordering(self):
        return [getattr(self.node, attr.lstrip('-'))
                for attr in self.treetype['model']['order'](self.model)]

    @property
    def parent(self):
        return self._get_real('parent')

    @property
    def prev_sibling(self):
        return self._get_real('prev')

    @property
    def next_sibling(self):
        return self._get_real('next')

    @property
    def ancestors(self):
        return self._get_real('ancestors')

    @property
    def descendants(self):
        return self._get_real('descendants')

    @property
    def level(self):
        return self._get_real('level')

    @property
    def move(self):
        return self._get_real('move')


def force_treenode(it):
    """
    Helper function to enforce the content of a returned container type
    being TreeNode objects. This especially useful if a manager or queryet
    method returns a container with tree node objects.
    :param it:
    :return:
    """
    def g(it):
        for node in it:
            yield TreeNode(node)
    if isinstance(it, TreeQuerySet):
        return it
    return g(it)
