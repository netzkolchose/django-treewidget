from __future__ import unicode_literals
from operator import attrgetter
try:
    from itertools import imap as map
except ImportError:
    pass
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


def get_treetype(model):
    if HAS_TREEBEARD and issubclass(model, TreebeardNode):
        return 'treebeard'
    elif HAS_MPTT and issubclass(model, MPTTModel):
        return 'mptt'
    raise LookupError


def get_parent(node, treetype):
    if treetype == 'treebeard':
        return node.get_parent()
    elif treetype == 'mptt':
        return getattr(node, node.__class__._mptt_meta.parent_attr, None)
    raise LookupError


def get_prev(node, treetype):
    if treetype == 'treebeard':
        return node.get_prev_sibling()
    elif treetype == 'mptt':
        return node.get_previous_sibling()
    raise LookupError


def get_next(node, treetype):
    if treetype == 'treebeard':
        return node.get_next_sibling()
    elif treetype == 'mptt':
        return node.get_next_sibling()
    raise LookupError


def get_level(node, treetype):
    if treetype == 'treebeard':
        return node.get_depth()
    elif treetype == 'mptt':
        return getattr(node, node.__class__._mptt_meta.level_attr, 0)
    raise LookupError


def get_order(model):
    treetype = get_treetype(model)
    if treetype == 'treebeard':
        return model.node_order_by or []
    elif treetype == 'mptt':
        return model._mptt_meta.order_insertion_by or []
    raise LookupError


def get_orderattr(node, model):
    return [getattr(node, attr.lstrip('-')) for attr in get_order(model)]


def get_orderattr_signs(model):
    return [-1 if attr.startswith('-') else 1 for attr in get_order(model)]


def get_appmodel(model):
    return '%s.%s' % (model._meta.app_label, model._meta.model_name)


def get_attribute(it, attr):
    return map(attrgetter(attr), it)


def pk(node):
    return node.pk if node else None


def get_move(node, treetype):
    if treetype == 'treebeard':
        return node.move
    elif treetype == 'mptt':
        return node.move_to
    raise LookupError
