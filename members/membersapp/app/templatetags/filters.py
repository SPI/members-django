from django import template

from membersapp.app.models import VoteOption


register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def times(number):
    return range(number)


@register.filter
def displayValue(votesystem, value):
    return votesystem.election.displayValue(value)


@register.filter
def results(votesystem):
    return votesystem.results()


@register.filter
def option_description_by_ref(beats):
    return VoteOption.object.get(ref=beats).description
