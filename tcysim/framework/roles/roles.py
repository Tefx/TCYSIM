class Roles(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def setup(self):
        for role in self.values():
            role.setup()

    def finish(self):
        for role in self.values():
            if hasattr(role, "finish"):
                role.finish()
