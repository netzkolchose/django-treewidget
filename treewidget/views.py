from __future__ import unicode_literals
from django.http import JsonResponse
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from treewidget.helper import (get_treetype, get_parent, get_orderattr,
                               get_prev, get_next, pk, get_move)
from django.utils.encoding import force_text


@login_required
def get_node(request):
    appmodel = request.GET.get('appmodel', None)
    ids = request.GET.getlist('ids')
    sort = request.GET.get('sort')
    if not appmodel or not ids:
        return JsonResponse([], safe=False)
    try:
        app_label, model_name = appmodel.split('.')
        model = apps.get_model(app_label=app_label, model_name=model_name)
        treetype = get_treetype(model)
        result = []
        for elem in model.objects.filter(id__in=ids):

            # get parent nodes
            parents = [{
                'name': escape(force_text(p)),
                'parent': pk(get_parent(p, treetype)),
                'id': p.pk,
                'sort': get_orderattr(p, model) if sort else None
            } for p in elem.get_ancestors()]

            result.append({
                'name': escape(force_text(elem)),
                'parent': pk(get_parent(elem, treetype)),
                'id': elem.pk,
                'sort': get_orderattr(elem, model) if sort else None,
                'parents': parents,
                'prev': pk(get_prev(elem, treetype)),
                'next': pk(get_next(elem, treetype))
            })
    except:
        return JsonResponse([], safe=False)
    return JsonResponse(result, safe=False)


# FIXME: mptt ordering?
@login_required
def move_node(request):
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
        treetype = get_treetype(model)
        node_order = getattr(model, 'node_order_by', None)
        node = model.objects.get(pk=node_id)
        if prev_id:
            target = model.objects.get(pk=prev_id)
            get_move(node, treetype)(target, 'sorted-sibling' if node_order else 'right')
        elif next_id:
            target = model.objects.get(pk=next_id)
            get_move(node, treetype)(target, 'sorted-sibling' if node_order else 'left')
        elif parent_id:
            target = model.objects.get(pk=parent_id)
            get_move(node, treetype)(target, 'sorted-child' if node_order else 'first-child')
        else:
            return JsonResponse(False, safe=False)
        return JsonResponse(True, safe=False)
    except:
        return JsonResponse(False, safe=False)
