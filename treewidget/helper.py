from json import dumps
from operator import attrgetter
from itertools import imap
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
    return 'unkown'


def get_parent(node, treetype):
    if treetype == 'treebeard':
        return node.get_parent()
    elif treetype == 'mptt':
        return getattr(node, node.__class__._mptt_meta.parent_attr, None)
    return None


def get_level(node, treetype):
    if treetype == 'treebeard':
        return node.get_depth()
    elif treetype == 'mptt':
        return getattr(node, node.__class__._mptt_meta.level_attr, 0)
    return None


def get_order(model):
    treetype = get_treetype(model)
    if treetype == 'treebeard':
        return model.node_order_by
    elif treetype == 'mptt':
        return model._mptt_meta.order_insertion_by
    return []


def get_orderattr(node, model):
    return [getattr(node, attr.lstrip('-')) for attr in get_order(model)]


def get_orderattr_json(node, model):
    return dumps(get_orderattr(node, model))


def get_orderattr_signs(model):
    return dumps([-1 if attr.startswith('-') else 1 for attr in get_order(model)])


def get_appmodel(model):
    return '%s.%s' % (model._meta.app_label, model._meta.model_name)


def get_attribute(it, attr):
    return imap(attrgetter(attr), it)
