class YardErrorBase:
    class _Error:
        code = 0

        def __init__(self, name, warning=True):
            self.name = name
            self.__class__.code -= 1
            self.value = self.__class__.code
            self.warning = warning

        def inform(self, msg=None):
            if self.warning:
                print("Error {}: {}".format(self.name, msg))
            return self.value

        def __str__(self):
            return "{} = {}".format(self.name, self.value)

        def __eq__(self, other):
            if isinstance(other, self.__class__):
                return self.value == other.value
            else:
                return self.value == other

    @classmethod
    def list_errors(cls):
        errors = []
        for item in cls.__dict__.values():
            if isinstance(item, cls._Error):
                errors.append(item)
        errors.sort(key=lambda x: x.value, reverse=True)
        for error in errors:
            print(error)
