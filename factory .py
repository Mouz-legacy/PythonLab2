from json_serializer import JsonSerializer


class Creator:

    @staticmethod
    def factory_method(self):
        if self == "json":
            return JsonSerializer
        else:
            print("Other serializers are not yet supported")
            pass