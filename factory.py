from json_serializer import JsonSerializer
from pickle_serializer import PickleSerializer


class Creator:

    @staticmethod
    def factory_method(self):
        if self == "json":
            return JsonSerializer
        elif self == "pickle":
            return PickleSerializer
        else:
            print("Other serializers are not yet supported")
            pass
