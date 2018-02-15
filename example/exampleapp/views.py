# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from forms import CityForm, FreeForm, FreeForm2
from models import City
from treewidget.fields import FreeTreeWidget
from json import dumps


def bound(request):
    city = City.objects.get(name='Berlin')
    cityform = CityForm(instance=city)
    return render(request, 'index.html', {'form': cityform})


def free(request):
    freeform = FreeForm()
    return render(request, 'index.html', {'form': freeform})


def free2(request):
    freeform = FreeForm2()
    return render(request, 'index.html', {'form': freeform})

def widget(request):
    w = FreeTreeWidget()
    data = dumps([
       { "id" : "ajson1", "parent" : "#", "text" : "Simple root node", "data": {'bla': 123}},
       { "id" : "ajson2", "parent" : "#", "text" : "Root node 2" },
       { "id" : "ajson3", "parent" : "ajson2", "text" : "Child 1" },
       { "id" : "ajson4", "parent" : "ajson2", "text" : "Child 2" },
    ])
    return render(request, 'index.html', {
        'widget_content': w.render('test', data, {}),
        'assets': w.media})
