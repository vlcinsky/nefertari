from contextlib import contextmanager

from zope.interface import (
    Attribute,
    Interface,
)
from zope.interface import implementer


class IRequestEvent(Interface):
    model = Attribute('Model class affected by the request')
    view = Attribute(
        'View instance which will process the request. Some useful '
        'attributes are: request, _json_params, _query_params. Change '
        '_json_params to edit data used to create/update objects and '
        '_query_params to edit data used to query database.')
    fields = Attribute(
        'Dict of all fields from request.json. Keys are fields names and'
        'values are nefertari.utils.FieldData instances. If request does '
        'not have JSON body, value will be an empty dict.')
    field = Attribute(
        'Changed field name. This field is set/changed in FieldIsChanged '
        'subscriber predicate. Do not use this field to determine what '
        'event was triggered when same event handler was registered with '
        'and without field predicate.')
    instance = Attribute(
        'Object instance affected by request. Used in item requests '
        'only. Should be used to read data only. Changes to the instance '
        'may result in database data inconsistency.')


@implementer(IRequestEvent)
class RequestEvent(object):
    """ Nefertari request event. """
    def __init__(self, model, view,
                 fields=None, field=None, instance=None):
        self.model = model
        self.view = view
        self.fields = fields
        self.field = field
        self.instance = instance


# 'Before' events

class before_index(RequestEvent):
    pass


class before_show(RequestEvent):
    pass


class before_create(RequestEvent):
    pass


class before_update(RequestEvent):
    pass


class before_replace(RequestEvent):
    pass


class before_delete(RequestEvent):
    pass


class before_update_many(RequestEvent):
    pass


class before_delete_many(RequestEvent):
    pass


class before_item_options(RequestEvent):
    pass


class before_collection_options(RequestEvent):
    pass


# 'After' events

class after_index(RequestEvent):
    pass


class after_show(RequestEvent):
    pass


class after_create(RequestEvent):
    pass


class after_update(RequestEvent):
    pass


class after_replace(RequestEvent):
    pass


class after_delete(RequestEvent):
    pass


class after_update_many(RequestEvent):
    pass


class after_delete_many(RequestEvent):
    pass


class after_item_options(RequestEvent):
    pass


class after_collection_options(RequestEvent):
    pass


# Subscriber predicates

class ModelClassIs(object):
    """ Subscriber predicate to check event.model is the right model. """

    def __init__(self, model, config):
        """
        :param model: Model class
        """
        self.model = model

    def text(self):
        return 'Model class is %s' % (self.model,)

    phash = text

    def __call__(self, event):
        """ Check whether one of following is true:

        * event.model is the same class as self.model
        * event.model is subclass of self.model
        """
        return (event.model is self.model or
                issubclass(event.model, self.model))


class FieldIsChanged(object):
    """ Subscriber predicate to check particular field is changed. """

    def __init__(self, field, config):
        self.field = field

    def text(self):
        return 'Field `%s` is changed' % (self.field,)

    phash = text

    def __call__(self, event):
        if self.field in event.fields:
            event.field = event.fields[self.field]
            return True
        return False


@contextmanager
def trigger_events(view_obj):
    """ Trigger before_ and after_ CRUD events.

    :param view_obj: Instance of nefertari.view.BaseView subclass created
        by nefertari.view.ViewMapper.
    """
    from nefertari.utils import FieldData
    _globals = globals()
    request = view_obj.request
    event_kwargs = {
        'view': view_obj,
        'model': view_obj.Model,
        'fields': FieldData.from_dict(
            view_obj._json_params,
            view_obj.Model)
    }
    if hasattr(view_obj.context, 'pk_field'):
        event_kwargs['instance'] = view_obj.context

    before_event = _globals['before_{}'.format(request.action)]
    request.registry.notify(before_event(**event_kwargs))

    yield

    after_event = _globals['after_{}'.format(request.action)]
    request.registry.notify(after_event(**event_kwargs))
