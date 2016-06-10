from pyramid.config import Configurator

# we must make sure custom models are known at database initialization!
from plld_app import models

from clld.web.icon import MapMarker
from clld.interfaces import (IValueSet, IValue, IDomainElement, IMapMarker, ILanguage)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('clld.web.app')

    config.registry.registerUtility(ApicsMapMarker(), IMapMarker)

    return config.make_wsgi_app()

class ApicsMapMarker(MapMarker):
    def __call__(self, ctx, req):
        icon = None
        if IValueSet.providedBy(ctx):
            if req.matched_route.name == 'valueset' and not ctx.parameter.multivalued:
                return ''
            icon = ctx.jsondata['icon']

        if IValue.providedBy(ctx):
            icon = ctx.domainelement.jsondata['icon']

        if IDomainElement.providedBy(ctx):
            icon = ctx.jsondata['icon']

        if ILanguage.providedBy(ctx):
            icon = ctx.jsondata['icon']

        if icon:
            return req.static_url('plld_app:static/icons/%s' % icon)

        return super(ApicsMapMarker, self).__call__(ctx, req)
