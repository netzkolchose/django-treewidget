# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db.models import QuerySet
from django.utils.encoding import python_2_unicode_compatible

try:
    from treebeard.models import Node as TreebeardNode
    from treebeard.al_tree import AL_Node
    from treebeard.ns_tree import NS_Node
    from treebeard.mp_tree import MP_Node
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
        'is_root'   :   lambda node: node.is_root(),
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
        'is_root'   :   lambda node: node.is_root_node(),
    },
}


class UnknownTreeImplementation(Exception):
    pass


def get_treetype(model):
    """
    Return the function mapping of the real model tree implementation.
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
        if isinstance(qs, TreeQuerySet):
            self.qs = qs.qs
            self.qs_it = qs.qs_it
            self.cached = qs.cached
            self.fill_cache = qs.fill_cache
        else:
            self.qs_it = iter(self.qs)
            self.cached = []
            self.fill_cache = True
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
            if self.fill_cache:
                node = TreeNode(node, self.qs.model, self.treetype)
                self.cached.append(node)
            return node
        except StopIteration:
            self.qs_it = iter(self.cached)
            self.fill_cache = False
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

    def get_ancestors(self):
        # django mptt got a ready to go method
        # has best runtime due to prefetch the parent attribute
        if self.treetype == MPTT:
            return TreeQuerySet(
                self.qs.get_ancestors(include_self=True).select_related('parent'))

        # for treebeard we have to get the parents ourself
        # we also patch the result with a parent attribute
        elif self.treetype == TREEBEARD:
            if issubclass(self.qs.model, NS_Node):
                from django.db.models import Q
                pks = [node.pk for node in self.qs]
                filters = Q(pk__in=set(pks))
                for node in self.qs:
                    if node.is_root():
                        continue
                    filters |= Q(tree_id=node.tree_id,
                                 lft__lt=node.lft,
                                 rgt__gt=node.rgt)

                # patch parent attribute
                qs = self.qs.model.objects.filter(filters)
                nodes = [TreeNode(node) for node in qs]
                for n in nodes:
                    if n.is_root:
                        continue
                    for node in qs:
                        if (node.tree_id == n.node.tree_id
                                and node.lft <= n.node.lft
                                and node.rgt >= n.node.rgt and node != n.node):
                            n._parent = TreeNode(node)
                # fake queryset with all nodes and parents in cache
                qs = TreeQuerySet(qs)
                qs.cached = nodes
                qs.qs_it = iter(qs.cached)
                qs.fill_cache = False
                return qs

            elif issubclass(self.qs.model, MP_Node):
                from django.db.models import Q
                pks = [node.pk for node in self.qs]
                filters = Q(pk__in=set(pks))
                for node in self.qs:
                    if node.is_root():
                        continue
                    paths = [
                        node.path[0:pos]
                        for pos in range(0, len(node.path), node.steplen)[1:]
                    ]
                    filters |= Q(path__in=paths)

                # patch parent attribute
                qs = self.qs.model.objects.filter(filters)
                nodes = [TreeNode(node) for node in qs]
                for n in nodes:
                    if n.is_root:
                        continue
                    depth = int(len(n.node.path) / n.node.steplen) - 1
                    parentpath = n.node.path[0:depth * n.node.steplen]
                    for node in qs:
                        if node.path == parentpath:
                            n._parent = TreeNode(node)
                # fake queryset with all nodes and parents in cache
                qs = TreeQuerySet(qs)
                qs.cached = nodes
                qs.qs_it = iter(qs.cached)
                qs.fill_cache = False
                return qs

            elif issubclass(self.qs.model, AL_Node):
                # almost like the generic fallback
                # difference:
                #   we have a parent attribute we can prefetch
                #   to lower db interaction
                nodes = self.qs.select_related('parent')
                pks = set()
                parents = set()
                for node in nodes:
                    pks.add(node.pk)
                    if node.parent:
                        parents.add(node.parent.pk)
                missing = parents - pks

                while missing:
                    pks.update(parents)
                    parents.clear()
                    for node in self.qs.model.objects.filter(
                            pk__in=missing).select_related('parent'):
                        if node.parent:
                            parents.add(node.parent.pk)
                    missing = parents - pks

                return TreeQuerySet(
                    self.qs.model.objects.filter(
                        pk__in=pks).select_related('parent'))

        # fallback to generic implementation with worst runtime
        # walks tree levels until all parents are known
        pks = set()
        parents = set()
        for node in self:
            pks.add(node.node.pk)
            if not node.is_root:
                parents.add(node.parent.node.pk)
        missing = parents - pks

        while missing:
            pks.update(parents)
            parents.clear()
            for node in TreeQuerySet(self.qs.model.objects.filter(pk__in=missing)):
                if node.parent:
                    parents.add(node.parent.node.pk)
            missing = parents - pks

        return TreeQuerySet(self.qs.model.objects.filter(pk__in=pks))


@python_2_unicode_compatible
class TreeNode(object):
    """
    Abstract tree node proxy for common tree attribute access.
    The real tree node can be accessed via the `node` attribute.

    NOTE: Only typical tree node attributes get abstracted,
    if you need a specific value from a node, access it via `node`
    (e.g. `obj.node.some_field`).
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
        try:
            # hack for treebeard to avoid additional db lookups
            return self._parent
        except AttributeError:
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

    @property
    def pk(self):
        return self.node.pk

    @property
    def is_root(self):
        return self._get_real('is_root')


def force_treenode(it):
    """
    Helper function to enforce the content of a returned container type
    being TreeNode objects. This especially useful if a manager or queryet
    method returns a container with tree node objects.
    """
    if isinstance(it, TreeQuerySet):
        return it
    return (TreeNode(node) for node in it)
