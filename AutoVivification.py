class AutoVivification(dict):
    """
    Implementation of perl's autovivification feature and Cache's globals data structure.
    """

    def __missing__(self, key):
        self[key] = value = type(self)()
        return value

    def __setitem__(self, key, value):
        if isinstance(value, type(self)):
            dict.__setitem__(self, key, value)
        else:
            dict.__setitem__(self[key], None, value)

    def get_item(self, *args):
        obj = self
        for arg in args:
            obj = obj[arg]
        return obj[None]

    def set_item(self, keys, value):
        obj = self
        for key in keys[:-1]:
            obj = obj[key]
        obj[keys[-1]] = value

# # # #


if __name__ == "__main__":
    test = AutoVivification()

    test["Hello"] = "World"
    print test.get_item("Hello")

    test["Hello"]["Jimmy"] = "How are you?"
    print test.get_item("Hello", "Jimmy")

    test["Good"]["Bye"] = "abc"
    print test.get_item("Good", "Bye")

    test["Good"]["Bye"] = "xyz"
    print test.get_item("Good", "Bye")
