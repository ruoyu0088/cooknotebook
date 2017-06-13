from sympy.printing import StrPrinter

def _piecewise_func(*args):
    for expr, cond in args:
        if cond:
            return expr


class PythonPrinter(StrPrinter):
    def _print_Equality(self, expr):
        return "{} == {}".format(self._print(expr.lhs), self._print(expr.rhs))

    def _print_Piecewise(self, expr):
        return "_piecewise_func({})".format(", ".join(self._print(arg) for arg in expr.args))


def cse2func(funcname, precodes, seq, printer_class=PythonPrinter):
    from IPython import get_ipython
    import textwrap
    printer = printer_class()
    codes = ["def %s:" % funcname]
    if isinstance(precodes, str):
        precodes = [precodes]
    for line in precodes:
        codes.append("    %s" % line)
    for variable, value in seq[0]:
        codes.append("    %s = %s" % (variable, printer._print(value)))
    returns = "    return (%s)" % ", ".join([printer._print(value) for value in seq[1]])
    codes.append("\n".join(textwrap.wrap(returns, 80)))
    code = "\n".join(codes)
    get_ipython().run_code(code)
    cse2func._history[funcname] = code
    return code

cse2func._history = {}