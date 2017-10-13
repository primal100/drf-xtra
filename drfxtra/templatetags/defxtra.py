from django import template
import json

register = template.Library()

@register.filter(name='D')
def D(value, arg):
    return value.get(arg, False)

@register.filter(name="jsonify")
def jsonify(value):
    return json.dumps(value)