class Roles(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
