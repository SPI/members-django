from django import template

from membersapp.app.models import VoteOption


register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def times(number):
    return range(number)


# Ugly workaround to the fact that you cannot call function or address tables
# in Django templates (unlike Flask)
@register.simple_tag
def displayValue(votesystem, value, index):
    return votesystem.election.displayValue(value[index])


@register.simple_tag
def displayValueDoubleIndex(votesystem, value, index, index2):
    return votesystem.election.displayValue(value[index][index2])


@register.filter
def results(votesystem):
    return votesystem.results()


@register.filter
def option_description_by_ref(beats):
    return VoteOption.object.get(ref=beats).description
