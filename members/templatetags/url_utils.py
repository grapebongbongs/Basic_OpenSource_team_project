from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def querystring_without_page(context):
    request = context['request']
    query = request.GET.copy()
    if 'page' in query:
        del query['page']
    return query.urlencode()