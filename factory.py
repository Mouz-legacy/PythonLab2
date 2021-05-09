from json_serializer import JsonSerializer


class Creator:

    @staticmethod
    def factory_method(self):
        if self == "json":
            return JsonSerializer
        else:
            print("Other serializers are not yet supported")
            pass


class TestSerializer:

    def __init__(self, n="Petya", s="Petrov"):
        self.name = n
        self.surname = s


if __name__ == '__main__':
    print("There must be tests")