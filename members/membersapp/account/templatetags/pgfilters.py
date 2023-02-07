from django import template

register = template.Library()


@register.filter(is_safe=True)
def field_class(value, arg):
    if 'class' in value.field.widget.attrs:
        c = arg + ' ' + value.field.widget.attrs['class']
    else:
        c = arg
    return value.as_widget(attrs={"class": c})


@register.filter(is_safe=True)
def ischeckbox(obj):
    return obj.field.widget.__class__.__name__ in ["CheckboxInput", "CheckboxSelectMultiple"] and not getattr(obj.field, 'regular_field', False)


@register.filter(is_safe=True)
def ismultiplecheckboxes(obj):
    return obj.field.widget.__class__.__name__ == "CheckboxSelectMultiple" and not getattr(obj.field, 'regular_field', False)


@register.filter(is_safe=True)
def isrequired_error(obj):
    if obj.errors and obj.errors[0] == "This field is required.":
        return True
    return False


@register.filter(is_safe=True)
def label_class(value, arg):
    return value.label_tag(attrs={'class': arg})


@register.filter(name='dictlookup')
def dictlookup(value, key):
    if hasattr(key, 'value'):
        # Django 3.1 made this a ModelChoiceIteratorValue -- while we support both 2.2 and 3.2,
        # we need to treat them differently.
        return value.get(key.value, None)
    else:
        return value.get(key, None)


@register.filter(name='keylookup')
def keylookup(value, key):
    return value[key]
