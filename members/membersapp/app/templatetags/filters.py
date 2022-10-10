from django import template


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
