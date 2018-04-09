from collections import OrderedDict

from inflection import camelize, underscore


def deep_camelize(data, uppercase_first_letter=False):
    if isinstance(data, (list, tuple, set)):
        return type(data)([deep_camelize(item) for item in data])

    if isinstance(data, (dict, OrderedDict)):
        return type(data)([(
            camelize(key, uppercase_first_letter) if not key.isupper() else key,
            deep_camelize(value, uppercase_first_letter)
        ) for key, value in data.items()])

    return data


def deep_underscore(data):
    if isinstance(data, (list, tuple, set)):
        return type(data)([deep_underscore(item) for item in data])

    if isinstance(data, (dict, OrderedDict)):
        return type(data)([(
            underscore(key) if not key.isupper() else key,
            deep_underscore(value)
        ) for key, value in data.items()])

    return data


def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))
