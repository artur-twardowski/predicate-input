class PredicateInput:
    
    class Continue: pass

    class Action:
        def __init__(self, description=None, **kwargs):
            self.callbacks = {}
            self.description = description

            for arg_name, arg_value in kwargs.items():
                if arg_name.startswith('callback'):
                    try:
                        n_args = int(arg_name[8:])
                        self.callbacks[n_args] = arg_value
                    except ValueError:
                        raise RuntimeError("\"callback\" argument must be suffixed by the number of arguments the callback expects")
                else:
                    raise RuntimeError("Unknown argument: %s" % arg_name)


        def call(self, args, current_input):
            n_args = len(args)
            if n_args in self.callbacks:
                self.callbacks[n_args](*args)
            else:
                raise RuntimeError("Missing callback for <%s> that takes %d argument%s" % (current_input, n_args, "" if n_args == 1 else "s"))


    class Parameter:
        def __init__(self, items: frozenset):
            self.items = items

    class Iterator:
        def __init__(self, parent):
            self._root = parent.get_syntax_tree()
            self._arguments = []
            self.reset()

        def reset(self):
            self._current_input = ""
            self._syntax_tree_ptr = self._root
            self._arguments.clear()
            self._continuing_param = False

        def push(self, data):
            self._current_input += data

            for next_steps, action in self._syntax_tree_ptr.items():
                hit = False
                if isinstance(next_steps, frozenset):
                    if data in next_steps:
                        hit = True
                        if self._continuing_param:
                            self._arguments[-1] += data
                        else:
                            self._arguments.append(data)
                else:
                    hit = (data == next_steps)

                if hit:
                    if action == PredicateInput.Continue:
                        self._continuing_param = True
                        return True
                    elif isinstance(action, PredicateInput.Action):
                        action.call(self._arguments, self._current_input)
                        self.reset()
                        return True
                    elif isinstance(action, dict):
                        self._continuing_param = False
                        self._syntax_tree_ptr = self._syntax_tree_ptr[next_steps]
                        return True
                    else:
                        raise RuntimeError("Invalid type of action: %s" % str(action))

            self.reset()
            return False


    def __init__(self):
        self._current_input = ""
        self._syntax_tree = {}

    def get_syntax_tree(self):
        return self._syntax_tree

    def register(self, sequence: list, action=None):
        syntax_tree_ptr = self._syntax_tree
        current_predicate = ""
        for ix in range(0, len(sequence)):
            item = sequence[ix]
            last_item = (ix == len(sequence) - 1)
            assert isinstance(item, (str, PredicateInput.Parameter)), \
                "Each element of sequence must be either a string or a Parameter" 

            current_predicate += str(item)
            if isinstance(item, PredicateInput.Parameter):
                item = item.items

            if item in syntax_tree_ptr:
                assert isinstance(syntax_tree_ptr[item], dict), \
                    "Already an action taken at <%s>, cannot be a predicate for another action" % current_predicate

            if last_item:
                syntax_tree_ptr[item] = action
            else:
                if item not in syntax_tree_ptr:
                    syntax_tree_ptr[item] = {}
                syntax_tree_ptr = syntax_tree_ptr[item]

    def begin(self):
        return PredicateInput.Iterator(self)


