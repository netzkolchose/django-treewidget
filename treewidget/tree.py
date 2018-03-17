# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db.models import QuerySet
from django.utils.encoding import python_2_unicode_compatible
from django.db.models import Q, F
from django.db.models.functions import Substr, Length
from django.db.models import CharField, OuterRef, Subquery

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
    raise UnknownTreeImplementation('cannot map tree implementation')


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
        if isinstance(qs, TreeQuerySet):
            self.qs = qs.qs
        else:
            self.qs = qs
        self.treetype = treetype or get_treetype(self.qs.model)

    def __getitem__(self, item):
        item = self.qs[item]
        if item:
            return TreeNode(item, self.qs.model, self.treetype)
        return item

    def _get_next(self):
        for node in self.qs:
            yield TreeNode(node, self.qs.model, self.treetype)

    def __iter__(self):
        for node in self.qs:
            yield TreeNode(node, self.qs.model, self.treetype)

    def __next__(self):
        return next(self)

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
        return '%s.%s' % (self.qs.model._meta.app_label,
                          self.qs.model._meta.model_name)

    def annotate_parent(self):
        if self.treetype == MPTT:
            parent_field = self.qs.model._mptt_meta.parent_attr
            return TreeQuerySet(self.qs.annotate(_parent_pk=F(parent_field+'__pk')))
        elif self.treetype == TREEBEARD:
            if issubclass(self.qs.model, NS_Node):
                sub = self.qs.model.objects.filter(
                    tree_id=OuterRef('tree_id'),
                    lft__lt=OuterRef('lft'),
                    rgt__gt=OuterRef('rgt')).reverse()[:1]
                qs = self.qs.annotate(_parent_pk=Subquery(sub.values('pk')))
                return TreeQuerySet(qs)
            elif issubclass(self.qs.model, MP_Node):
                sub = self.qs.model.objects.filter(path=OuterRef('parentpath'))
                expr = Substr('path', 1, Length('path') - self.qs.model.steplen,
                              output_field=CharField())
                qs = self.qs.annotate(parentpath=expr).annotate(_parent_pk=Subquery(sub.values('pk')))
                return TreeQuerySet(qs)
            elif issubclass(self.qs.model, AL_Node):
                return TreeQuerySet(
                        self.qs.annotate(_parent_pk=F('parent__pk')))
        raise UnknownTreeImplementation('dont know how to annotate _parent_pk')

    def get_ancestors_parent_annotated(self, include_self=False):
        """
        Creates a queryset containing all parents of the queryset.
        Also annotates the parent pk as `_parent_pk`.
        """
        # django mptt got a ready to go method
        if self.treetype == MPTT:
            parent_field = self.qs.model._mptt_meta.parent_attr
            return TreeQuerySet(
                self.qs.get_ancestors(include_self=include_self)
                    .annotate(_parent_pk=F(parent_field+'__pk')))

        # for treebeard we have to get the parents ourself
        elif self.treetype == TREEBEARD:
            if issubclass(self.qs.model, NS_Node):
                filters = Q()
                for node in self.qs:
                    if include_self:
                        filters |= Q(
                            tree_id=node.tree_id,
                            lft__lte=node.lft,
                            rgt__gte=node.rgt)
                    else:
                        filters |= Q(
                            tree_id=node.tree_id,
                            lft__lt=node.lft,
                            rgt__gt=node.rgt)
                sub = self.qs.model.objects.filter(
                    tree_id=OuterRef('tree_id'),
                    lft__lt=OuterRef('lft'),
                    rgt__gt=OuterRef('rgt')).reverse()[:1]
                qs = self.qs.model.objects.filter(filters)\
                    .annotate(_parent_pk=Subquery(sub.values('pk')))
                return TreeQuerySet(qs)

            elif issubclass(self.qs.model, MP_Node):
                paths = set()
                for node in self.qs:
                    length = len(node.path)
                    if include_self:
                        length += node.steplen
                    paths.update(node.path[0:pos]
                                 for pos in range(node.steplen, length, node.steplen))
                sub = self.qs.model.objects.filter(path=OuterRef('parentpath'))
                expr = Substr('path', 1, Length('path') - self.qs.model.steplen,
                              output_field=CharField())
                qs = self.qs.model.objects.filter(path__in=paths)\
                    .annotate(parentpath=expr)\
                    .annotate(_parent_pk=Subquery(sub.values('pk')))
                return TreeQuerySet(qs)

            elif issubclass(self.qs.model, AL_Node):
                # worst for parent querying
                # we have to walk all levels up to root
                # adds roughly a one query per level
                nodes = self.qs.select_related('parent')
                pks = set()
                parents = set()
                for node in nodes:
                    if include_self:
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
                    self.qs.model.objects.filter(pk__in=pks)
                        .annotate(_parent_pk=F('parent__pk')))

        raise UnknownTreeImplementation('dont know how to annotate _parent_pk')


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
    Helper function to enforce the content of a returned container
    being TreeNode objects. This especially useful if a manager
    or a queryet method returns a container with tree node objects
    instead of a queryset.
    """
    if isinstance(it, QuerySet):
        return it
    return (TreeNode(node) for node in it)
