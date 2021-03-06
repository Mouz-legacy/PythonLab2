class JsonSerializer:
    deque = getattr(__import__('collections'), 'deque')
    inspect = __import__('inspect')
    types = __import__('types')
    sort_keys = False
    f_found = {}

    @staticmethod
    def dict_to_class(cls):
        try:
            return type(cls["name"], tuple(cls["bases"]), cls["dict"])
        except IndexError:
            raise StopIteration("Incorrect class")

    @staticmethod
    def dict_to_obj(obj):
        try:
            def __init__(self):
                pass

            cls = obj["class"]
            temp = cls.__init__
            cls.__init__ = __init__
            res = obj["class"]()
            res.__dict__ = obj["vars"]
            res.__init__ = temp
            res.__class__.__init__ = temp
            return res
        except IndexError:
            raise StopIteration("Incorrect object")

    @staticmethod
    def dict_to_code(obj):
        return JsonSerializer.types.CodeType(obj["co_argcount"],
                                             obj["co_kwonlyargcount"],
                                             obj["co_nlocals"],
                                             obj["co_stacksize"],
                                             obj["co_flags"],
                                             bytes(bytearray(JsonSerializer.parse_array(obj["co_code"], 1)[0])),
                                             tuple(obj["co_consts"]),
                                             tuple(obj["co_names"]),
                                             tuple(obj["co_varnames"]),
                                             obj["co_filename"],
                                             obj["co_name"],
                                             obj["co_firstlineno"],
                                             bytes(bytearray(JsonSerializer.parse_array(obj["co_lnotab"], 1)[0])),
                                             tuple(obj["co_freevars"]),
                                             tuple(obj["co_cellvars"]))

    @staticmethod
    def dict_to_module(obj):
        try:
            return __import__(obj)
        except ModuleNotFoundError:
            raise ImportError(str(obj) + ' not found')

    @staticmethod
    def validate_object(obj):
        if not hasattr(obj, '__dict__'):
            return False
        if JsonSerializer.inspect.isroutine(obj):
            return False
        if JsonSerializer.inspect.isclass(obj):
            return False
        else:
            return True

    @staticmethod
    def parse_dict(string, idx):
        args = {}
        comma = False
        colon = False
        phase = False
        temp = None

        try:
            next_char = string[idx]
        except IndexError:
            raise StopIteration(idx)

        while True:
            if next_char == '}':
                break
            elif next_char == ' ' or next_char == '\n':
                idx += 1
            elif next_char == ',':
                if comma is False:
                    raise StopIteration(idx)
                idx += 1
                phase = False
                comma = False
            elif next_char == ':':
                if colon is False:
                    raise StopIteration(idx)
                idx += 1
                phase = True
                colon = False
            elif not comma and not phase:
                if next_char == '"':
                    obj, idx = JsonSerializer.parse_string(string, idx + 1)
                    if obj in args:
                        raise StopIteration(idx)
                    temp = obj
                    phase = False
                    colon = True
                else:
                    raise StopIteration(idx)
            elif not colon and phase:
                if next_char == '"':
                    obj, idx = JsonSerializer.parse_string(string, idx + 1)
                    args[temp] = obj
                elif next_char.isdigit() or (next_char == '-' and string[idx + 1].isdigit()):
                    obj, idx = JsonSerializer.parse_digit(string, idx)
                    args[temp] = obj
                elif next_char == '{':
                    obj, idx = JsonSerializer.parse_dict(string, idx + 1)
                    args[temp] = obj
                elif next_char == '[':
                    obj, idx = JsonSerializer.parse_array(string, idx + 1)
                    args[temp] = obj
                elif next_char == 'n' and string[idx:idx + 4] == 'null':
                    args[temp] = None
                    idx += 4
                elif next_char == 't' and string[idx:idx + 4] == 'true':
                    args[temp] = True
                    idx += 4
                elif next_char == 'f' and string[idx:idx + 5] == 'false':
                    args[temp] = False
                    idx += 5
                elif next_char == 'N' and string[idx:idx + 3] == 'NaN':
                    args[temp] = float('NaN')
                    idx += 3
                elif next_char == 'I' and string[idx:idx + 8] == 'Infinity':
                    args[temp] = float('Infinity')
                    idx += 8
                elif next_char == '-' and string[idx:idx + 9] == '-Infinity':
                    args[temp] = float('-Infinity')
                    idx += 9
                else:
                    raise StopIteration(string[idx])

                comma = True
            else:
                raise StopIteration(idx)

            try:
                next_char = string[idx]
            except IndexError:
                raise StopIteration(idx)

        if not comma and not colon and len(args) != 0:
            raise StopIteration(idx)
        if "##function_type##" in args and len(args.keys()) == 1:
            return JsonSerializer.dict_to_func(args["##function_type##"]), idx + 1
        if "##static_method_type##" in args and len(args.keys()) == 1:
            return staticmethod(args["##static_method_type##"]), idx + 1
        if "##class_method_type##" in args and len(args.keys()) == 1:
            return classmethod(args["##static_method_type##"]), idx + 1
        if "##class_type##" in args and len(args.keys()) == 1:
            return JsonSerializer.dict_to_class(args["##class_type##"]), idx + 1
        if "##instance_type##" in args and len(args.keys()) == 1:
            return JsonSerializer.dict_to_obj(args["##instance_type##"]), idx + 1
        if "##module_type##" in args and len(args.keys()) == 1:
            return JsonSerializer.dict_to_module(args["##module_type##"]), idx + 1
        if "##code_type##" in args and len(args.keys()) == 1:
            return JsonSerializer.dict_to_code(args["##code_type##"]), idx + 1
        else:
            if JsonSerializer.sort_keys:
                return dict(sorted(args.items())), idx + 1
            else:
                return args, idx + 1

    @staticmethod
    def parse_string(string, idx):
        first = idx
        opened = False
        try:
            while string[idx] != '"' or opened:
                if string[idx] == '\\':
                    opened = not opened
                else:
                    opened = False
                idx += 1
        except IndexError:
            raise StopIteration(idx)
        return string[first:idx], idx + 1

    @staticmethod
    def collect_funcs(obj, is_visited):
        for i in obj.__globals__:
            attr = obj.__globals__[i]
            if JsonSerializer.inspect.isfunction(attr) and attr.__name__ not in is_visited:
                is_visited[attr.__name__] = attr
                is_visited = JsonSerializer.collect_funcs(attr, is_visited)
        return is_visited

    @staticmethod
    def set_funcs(obj, is_visited, gls):
        for i in obj.__globals__:
            attr = obj.__globals__[i]
            if JsonSerializer.inspect.isfunction(attr) and attr.__name__ not in is_visited:
                is_visited[attr.__name__] = True
                attr.__globals__.update(gls)
                is_visited = JsonSerializer.set_funcs(attr, is_visited, gls)
        return is_visited

    @staticmethod
    def dict_to_func(obj):
        res = JsonSerializer.types.FunctionType(globals=obj["__globals__"],
                                                code=obj["__code__"],
                                                name=obj['__name__'])
        funcs = JsonSerializer.collect_funcs(res, {})
        funcs.update({res.__name__: res})
        JsonSerializer.set_funcs(res, {res.__name__: True}, funcs)
        res.__globals__.update(funcs)
        res.__globals__['__builtins__'] = __import__('builtins')
        return res

    @staticmethod
    def parse_digit(string, idx):
        first = idx
        try:
            while string[idx] == '.' or string[idx].isdigit() or string[idx] == 'e' or string[idx] == 'E' \
                    or string[idx] == '-' or string[idx] == '+':
                idx += 1
        except IndexError:
            pass

        res = string[first:idx]
        try:
            return int(res), idx
        except ValueError:
            try:
                return float(res), idx
            except ValueError:
                raise StopIteration(idx)

    @staticmethod
    def parse_array(string, idx):
        args = JsonSerializer.deque()
        comma = False

        try:
            next_char = string[idx]
        except IndexError:
            raise StopIteration(idx)

        while True:
            if next_char == ']':
                break
            elif next_char == ' ' or next_char == '\n':
                idx += 1
            elif next_char == ',':
                if comma is False:
                    raise StopIteration(idx)
                idx += 1
                comma = False
            elif not comma:
                if next_char == '"':
                    obj, idx = JsonSerializer.parse_string(string, idx + 1)
                    args.append(obj)
                elif next_char.isdigit() or (next_char == '-' and string[idx + 1].isdigit()):
                    obj, idx = JsonSerializer.parse_digit(string, idx)
                    args.append(obj)
                elif next_char == '{':
                    obj, idx = JsonSerializer.parse_dict(string, idx + 1)
                    args.append(obj)
                elif next_char == '[':
                    obj, idx = JsonSerializer.parse_array(string, idx + 1)
                    args.append(obj)
                elif next_char == 'n' and string[idx:idx + 4] == 'null':
                    args.append(None)
                    idx += 4
                elif next_char == 't' and string[idx:idx + 4] == 'true':
                    args.append(True)
                    idx += 4
                elif next_char == 'f' and string[idx:idx + 5] == 'false':
                    args.append(False)
                    idx += 5
                elif next_char == 'N' and string[idx:idx + 3] == 'NaN':
                    args.append(float('NaN'))
                    idx += 3
                elif next_char == 'I' and string[idx:idx + 8] == 'Infinity':
                    args.append(float('Infinity'))
                    idx += 8
                elif next_char == '-' and string[idx:idx + 9] == '-Infinity':
                    args.append(float('-Infinity'))
                    idx += 9
                else:
                    print(string[idx-100:idx+100])
                    raise StopIteration(idx)

                comma = True
            else:
                print(string[idx-100:idx+100])
                raise StopIteration(idx)

            try:
                next_char = string[idx]
            except IndexError:
                raise StopIteration(idx)
        if not comma and len(args) != 0:
            raise StopIteration(idx)
        return list(args), idx + 1

    @staticmethod
    def loads(string):
        idx = 0
        try:
            while string[idx] == ' ' or string[idx] == '\n':
                idx += 1
        except IndexError:
            pass

        if string[idx] == '"':
            obj, idx = JsonSerializer.parse_string(string, idx + 1)
        elif string[idx].isdigit() or (string[idx] == '-' and string[idx + 1].isdigit()):
            obj, idx = JsonSerializer.parse_digit(string, idx)
        elif string[idx] == '{':
            obj, idx = JsonSerializer.parse_dict(string, idx + 1)
        elif string[idx] == '[':
            obj, idx = JsonSerializer.parse_array(string, idx + 1)
        elif string[idx] == 'n' and string[idx:idx + 4] == 'null':
            obj = None
            idx += 4
        elif string[idx] == 't' and string[idx:idx + 4] == 'true':
            obj = True
            idx += 4
        elif string[idx] == 'f' and string[idx:idx + 5] == 'false':
            obj = False
            idx += 5
        elif string[idx] == 'N' and string[idx:idx + 3] == 'NaN':
            obj = False
            idx += 3
        elif string[idx] == 'I' and string[idx:idx + 8] == 'Infinity':
            obj = float('Infinity')
            idx += 8
        elif string[idx] == '-' and string[idx:idx + 9] == '-Infinity':
            obj = float('-Infinity')
            idx += 9
        else:
            raise StopIteration(idx)

        try:
            while True:
                if string[idx] != ' ' and string[idx] != '\n':
                    raise StopIteration(idx)
                idx += 1
        except IndexError:
            pass

        return obj

    @staticmethod
    def load(fp):
        try:
            with open(fp, 'r') as file:
                data = file.read()
        except FileNotFoundError:
            raise FileNotFoundError("file doesn't exist")
        return JsonSerializer.loads(data)

    @staticmethod
    def dumps_list(obj, step="", new_step=""):
        if not len(obj):
            return "[]"
        new_step = "\n" + new_step
        res = "[" + new_step
        for i in range(len(obj) - 1):
            res += step + JsonSerializer._dumps(obj[i], step, new_step.replace('\n', '') + step) + "," + new_step
        res += step + JsonSerializer._dumps(obj[-1], step, new_step.replace('\n', '') + step) + new_step + "]"
        return res

    @staticmethod
    def dumps_dict(obj, step="", new_step=""):
        if not len(obj):
            return "{}"
        if JsonSerializer.sort_keys:
            obj = dict(sorted(obj.items()))
        new_step = "\n" + new_step
        res = "{" + new_step
        keys = list(obj)
        for i in keys[:-1]:
            res += step + '"' + str(i) + '"' + ": " + JsonSerializer._dumps(obj[i], step,
                                                                            new_step.replace('\n', '') + step) + "," + new_step
        res += step + '"' + str(keys[-1]) + '"' + ": " + JsonSerializer._dumps(obj[keys[-1]], step,
                                                                               new_step.replace('\n',
                                                                                         '') + step) + new_step + "}"
        return res

    @staticmethod
    def class_to_dict(cls):
        dpns = ()
        if len(cls.__bases__) != 0:
            for i in cls.__bases__:
                if i.__name__ != "object":
                    dpns += (JsonSerializer.class_to_dict(i),)
        args = {}
        st_args = dict(cls.__dict__)
        if len(st_args) != 0:
            for i in st_args:
                if JsonSerializer.inspect.isclass(st_args[i]):
                    args[i] = JsonSerializer.class_to_dict(st_args[i])
                elif JsonSerializer.inspect.isfunction(st_args[i]):
                    if st_args[i].__name__ not in JsonSerializer.f_found:
                        args[i] = JsonSerializer.function_to_dict(st_args[i])
                elif isinstance(st_args[i], staticmethod):
                    if st_args[i].__func__.__name__ not in JsonSerializer.f_found:
                        args[i] = JsonSerializer.staticmethod_to_dict(st_args[i])
                elif isinstance(st_args[i], classmethod):
                    if st_args[i].__func__.__name__ not in JsonSerializer.f_found:
                        args[i] = JsonSerializer.class_method_to_dict(st_args[i])
                elif JsonSerializer.inspect.ismodule(st_args[i]):
                    args[i] = JsonSerializer.module_to_dict(st_args[i])
                elif JsonSerializer.validate_object(st_args[i]):
                    args[i] = JsonSerializer.object_to_dict(st_args[i])
                elif isinstance(st_args[i],
                                (set, dict, list, int, float, type(True), type(False), type(None), tuple)):
                    args[i] = st_args[i]
        return {"##class_type##": {"name": cls.__name__, "bases": dpns, "dict": args}}

    @staticmethod
    def object_to_dict(obj):
        return {"##instance_type##": {"class": JsonSerializer.class_to_dict(obj.__class__), "vars": obj.__dict__}}

    @staticmethod
    def module_to_dict(obj):
        return {"##module_type##": obj.__name__}

    @staticmethod
    def staticmethod_to_dict(obj):
        return {"##static_method_type##": JsonSerializer.function_to_dict(obj.__func__)}

    @staticmethod
    def class_method_to_dict(obj):
        return {"##class_method_type##": JsonSerializer.function_to_dict(obj.__func__)}

    @staticmethod
    def function_to_dict(obj):
        gls = JsonSerializer.gather_gls(obj, obj.__code__)

        return {"##function_type##": {"__globals__": gls,
                                      "__name__": obj.__name__,
                                      "__code__":
                                          JsonSerializer.code_to_dict(obj.__code__)
                                      }}

    @staticmethod
    def code_to_dict(obj):
        return {"##code_type##": {"co_argcount": obj.co_argcount,
                                  "co_kwonlyargcount": obj.co_kwonlyargcount,
                                  "co_nlocals": obj.co_nlocals,
                                  "co_stacksize": obj.co_stacksize,
                                  "co_flags": obj.co_flags,
                                  "co_code": obj.co_code,
                                  "co_consts": obj.co_consts,
                                  "co_names": obj.co_names,
                                  "co_varnames": obj.co_varnames,
                                  "co_filename": obj.co_filename,
                                  "co_name": obj.co_name,
                                  "co_firstlineno": obj.co_firstlineno,
                                  "co_lnotab": obj.co_lnotab,
                                  "co_freevars": obj.co_freevars,
                                  "co_cellvars": obj.co_cellvars
                                  }
                }

    @staticmethod
    def gather_gls(obj, obj_code):
        JsonSerializer.f_found[obj.__name__] = True
        gls = {}
        for i in obj_code.co_names:
            try:
                if JsonSerializer.inspect.isclass(obj.__globals__[i]):
                    gls[i] = JsonSerializer.class_to_dict(obj.__globals__[i])
                elif JsonSerializer.inspect.isfunction(obj.__globals__[i]):
                    if obj.__globals__[i].__name__ not in JsonSerializer.f_found:
                        gls[i] = JsonSerializer.function_to_dict(obj.__globals__[i])
                elif isinstance(obj.__globals__[i], staticmethod):
                    if obj.__globals__[i].__func__.__name__ not in JsonSerializer.f_found:
                        gls[i] = JsonSerializer.staticmethod_to_dict(obj.__globals__[i])
                elif isinstance(obj.__globals__[i], classmethod):
                    if obj.__globals__[i].__func__.__name__ not in JsonSerializer.f_found:
                        gls[i] = JsonSerializer.class_method_to_dict(obj.__globals__[i])
                elif JsonSerializer.inspect.ismodule(obj.__globals__[i]):
                    gls[i] = JsonSerializer.module_to_dict(obj.__globals__[i])
                elif JsonSerializer.validate_object(obj.__globals__[i]):
                    gls[i] = JsonSerializer.object_to_dict(obj.__globals__[i])
                elif isinstance(obj.__globals__[i], (set, dict, list, int, float, bool, type(None), tuple, str)):
                    gls[i] = obj.__globals__[i]
            except KeyError:
                pass
        for i in obj_code.co_consts:
            if isinstance(i, JsonSerializer.types.CodeType):
                gls.update(JsonSerializer.gather_gls(obj, i))
        return gls

    @staticmethod
    def _dumps(obj, step='', new_step=''):
        if obj is None:
            return "null"
        elif obj is True:
            return "true"
        elif obj is False:
            return "false"
        elif obj is float("Inf"):
            return "Infinity"
        elif obj is float("-Inf"):
            return "-Infinity"
        elif obj is float("NaN"):
            return "NaN"
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, bytes):
            return "\"" + str(list(bytearray(obj))) + "\""
        elif isinstance(obj, str):
            return "\"" + obj.replace('\\', '\\\\').replace('\"', '\\\"') + "\""
        elif isinstance(obj, (set, tuple)):
            return JsonSerializer.dumps_list(list(obj), step, new_step)
        elif isinstance(obj, list):
            return JsonSerializer.dumps_list(obj, step, new_step)
        elif isinstance(obj, dict):
            return JsonSerializer.dumps_dict(obj, step, new_step)
        elif JsonSerializer.inspect.isfunction(obj):
            res = JsonSerializer.dumps_dict(JsonSerializer.function_to_dict(obj), step, new_step)
            JsonSerializer.f_found = {}
            return res
        elif isinstance(obj, staticmethod):
            res = JsonSerializer.dumps_dict(JsonSerializer.staticmethod_to_dict(obj), step, new_step)
            JsonSerializer.f_found = {}
            return res
        elif isinstance(obj, classmethod):
            res = JsonSerializer.dumps_dict(JsonSerializer.class_method_to_dict(obj), step, new_step)
            JsonSerializer.f_found = {}
            return res
        elif JsonSerializer.inspect.ismodule(obj):
            return JsonSerializer.dumps_dict(JsonSerializer.module_to_dict(obj), step, new_step)
        elif JsonSerializer.inspect.isclass(obj):
            return JsonSerializer.dumps_dict(JsonSerializer.class_to_dict(obj), step, new_step)
        elif JsonSerializer.validate_object(obj):
            return JsonSerializer.dumps_dict(JsonSerializer.object_to_dict(obj), step, new_step)
        elif isinstance(obj, JsonSerializer.types.CodeType):
            return JsonSerializer.dumps_dict(JsonSerializer.code_to_dict(obj), step, new_step)
        else:
            raise TypeError()

    @staticmethod
    def dumps(obj, sort_keys=False, indent=None):
        JsonSerializer.f_found = {}
        JsonSerializer.sort_keys = sort_keys
        if isinstance(indent, int) and indent > 0:
            step = " " * indent
            res = JsonSerializer._dumps(obj, step)
            if indent < 1:
                res = res.replace("\n", "")
        else:
            res = JsonSerializer._dumps(obj).replace("\n", "")
        return res

    @staticmethod
    def dump(obj, fp, sort_keys=False, indent=None):
        try:
            with open(fp, 'w') as file:
                file.write(JsonSerializer.dumps(obj, sort_keys, indent))
        except FileNotFoundError:
            raise FileNotFoundError("file doesn't exist")
