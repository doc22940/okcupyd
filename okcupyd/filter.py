import inspect

from . import util


class Filters(object):

    def __init__(self, builder_to_keys=None, builder_to_decider=None):
        self.builder_to_keys = builder_to_keys or {}
        self.builder_to_decider = builder_to_decider or {}

    @staticmethod
    def any_decider(function, incoming, accepted_keys):
        return bool(set(incoming).intersection(accepted_keys))

    @staticmethod
    def all_decider(function, incoming, accepted_keys):
        return set(accepted_keys).issubset(set(incoming))

    @staticmethod
    def all_not_none_decider(function, incoming, accepted_keys):
        return all(incoming.get(key) is not None for key in accepted_keys)

    @staticmethod
    def any_not_none_decider(function, incoming, accepted_keys):
        return any(incoming.get(key) is not None for key in accepted_keys)

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__,
                                 repr(self.builder_to_keys.keys()))

    def filters(self, **kwargs):
        builders = [builder
                    for builder, decider in self.builder_to_decider.items()
                    if decider(builder, kwargs, self.builder_to_keys[builder])]
        return [builder(*[kwargs.get(key)
                          for key in self.builder_to_keys[builder]])
                for builder in builders]

    def build(self, **kwargs):
        return {
            'filter{0}'.format(filter_number): filter_string
            for filter_number, filter_string
            in enumerate(self.filters(**kwargs), 1)
        }

    @util.curry
    def register_filter_builder(cls, function, keys=(), decider=None):
        decider = decider or cls.all_not_none_decider
        function_arguments = inspect.getargspec(function).args
        if keys:
            assert len(keys) == len(function_arguments)
        else:
            keys = function_arguments
        cls.builder_to_keys[function] = keys
        cls.builder_to_decider[function] = decider

        return function
