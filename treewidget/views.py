from django.http import JsonResponse
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.utils.encoding import force_str
from treewidget.tree import TreeQuerySet, TreeNode

# TODO: check for individual permissions


@login_required
def get_node(request):
    """
    Ajax view for node changes with the admin popup.
    Since django's popup functionality itself does not return
    enough data to keep a tree in sync, we have to request
    changes with additional tree data separately.
    Handles add and tree moves with the popup.
    Returns a list of requested nodes with their parents,
    direct siblings and sort order.
    :param request:
    :return:
    """
    appmodel = request.GET.get('appmodel', None)
    ids = request.GET.getlist('ids')
    sort = request.GET.get('sort')
    if not appmodel or not ids:
        return JsonResponse([], safe=False)
    try:
        app_label, model_name = appmodel.split('.')
        model = apps.get_model(app_label=app_label, model_name=model_name)
        result = []
        for elem in TreeQuerySet(model.objects.filter(id__in=ids)):

            # get parent nodes
            parents = [{
                'name': escape(force_str(p)),
                'parent': p.parent.node.pk if p.parent else None,
                'id': p.node.pk,
                'sort': p.ordering if sort else None
            } for p in elem.ancestors]

            result.append({
                'name': escape(force_str(elem)),
                'parent': elem.parent.node.pk if elem.parent else None,
                'id': elem.node.pk,
                'sort': elem.ordering if sort else None,
                'parents': parents,
                'prev': elem.prev_sibling.node.pk if elem.prev_sibling else None,
                'next': elem.next_sibling.node.pk if elem.next_sibling else None
            })
        return JsonResponse(result, safe=False)
    except:
        return JsonResponse([], safe=False)


@login_required
def move_node(request):
    """
    Ajax view to evaluate and execute direct drag'n drop moves in the tree.
    Returns True if the moves is legal, otherwise False.
    Not used, if drag'n drop is disabled.
    :param request:
    :return:
    """
    appmodel = request.GET.get('appmodel', None)
    node_id = request.GET.get('id', None)
    parent_id = request.GET.get('parent', None)
    prev_id = request.GET.get('prev', None)
    next_id = request.GET.get('next', None)
    if not appmodel or not node_id:
        return JsonResponse(False, safe=False)
    try:
        app_label, model_name = appmodel.split('.')
        model = apps.get_model(app_label=app_label, model_name=model_name)

        # need node ordering for treebeard types
        node_order = getattr(model, 'node_order_by', None)
        node = TreeNode(model.objects.get(pk=node_id))
        if prev_id:
            target = model.objects.get(pk=prev_id)
            node.move(target, 'sorted-sibling' if node_order else 'right')
        elif next_id:
            target = model.objects.get(pk=next_id)
            node.move(target, 'sorted-sibling' if node_order else 'left')
        elif parent_id:
            target = model.objects.get(pk=parent_id)
            node.move(target, 'sorted-child' if node_order else 'first-child')
        else:
            return JsonResponse(False, safe=False)
        return JsonResponse(True, safe=False)
    except:
        return JsonResponse(False, safe=False)
