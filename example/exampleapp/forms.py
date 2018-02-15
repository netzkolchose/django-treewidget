from django.forms import ModelForm, Form, CharField
from models import City, Region
from treewidget.fields import TreeModelMultipleField, FreeTreeField
from json import dumps


class CityForm(ModelForm):
    class Meta:
        model = City
        fields = ('name', 'regions',)


class FreeForm(Form):
    name = CharField(max_length=63)
    regions = TreeModelMultipleField(Region.objects, settings={'show_buttons': True, 'search': True, 'dnd': True})


some_data = [
   { "id" : "ajson1", "parent" : "#", "text" : "Simple root node", "state": {"bla": 123} },
   { "id" : "ajson2", "parent" : "#", "text" : "Root node 2" },
   { "id" : "ajson3", "parent" : "ajson2", "text" : "Child 1", "state": {"selected": True}},
   { "id" : "ajson4", "parent" : "ajson2", "text" : "Child 2" },
]


class FreeForm2(Form):
    name = CharField(max_length=63)
    regions = FreeTreeField(initial=dumps(some_data))
