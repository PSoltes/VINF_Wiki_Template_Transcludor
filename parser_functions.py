import re
from math import floor, ceil, sin, cos, tan, acos, asin, atan, log

class Infix(object):
    #Infix got from Wikiextractor package and http://tomerfiliba.com/blog/Infix-Operators/
    def __init__(self, function):
        self.function = function

    def __ror__(self, other):
        return Infix(lambda x, self=self, other=other: self.function(other, x))

    def __or__(self, other):
        return self.function(other)

    def __rlshift__(self, other):
        return Infix(lambda x, self=self, other=other: self.function(other, x))

    def __rshift__(self, other):
        return self.function(other)

    def __call__(self, value1, value2):
        return self.function(value1, value2)

class ParserFunctions(object):

    def __init__(self):
        self.functions = {
            '#if': self.pf_if,
            '#ifeq': self.pf_ifeq,
            'uc': self.uc,
            'ucfirst': self.ucfirst,
            'lc': self.lc,
            'lcfirst': self.lcfirst,
            '#tag': self.pf_tag,
            '#switch': self.pf_switch,
            '#expr': self.pf_expr,
            '#ifexist': lambda *args: '' #cannot be implemented in this env
        }

    def variable(self, frame):
        try:
            return str(frame[frame['name']])
        except KeyError:   
            return frame['name']
    
    def uc(self, *args):
        return args[0].upper()

    def ucfirst(self, *args):
        string = args[0]
        if len(string) > 0:
            return string[0].upper() + string[1:]
        else:
            return string

    def lc(self, *args):
        return args[0].lower()

    def lcfirst(self, *args):
        string = args[0]
        if len(string) > 0:
            return string[0].lower() + string[1:]
        else:
            return string

    def pf_if(self, *args):
        if args[0] == '':
            return args[2] if len(args) > 2 else ''
        else:
            return args[1] if len(args) > 1 else ''

    def pf_ifeq(self, *args):
        if args[0] == args[1]:
            return args[2] if len(args) > 2 else ''
        else:
            return args[3] if len(args) > 3 else ''
    
    def pf_tag(self, *args):
        attrs = ''
        for variable in args[2:]:
                attrs += f'{variable} '
        return f"<{args[0]} {attrs}>{args[1]}</{args[0]}>"

    def pf_switch(self, *args):
        value_hit = False
        default = None
        for param in args[1:]:
            split_param = param.split('=', 1)
            if split_param[0] == args[0]:
                value_hit = True
            if value_hit and len(split_param) > 1 and split_param[0] != '#default':
                return split_param[1]
            if split_param[0] == '#default' and len(split_param) > 1:
                default = split_param[1]
        if default is None:
            default = args[len(args) - 1] if len(args[len(args) - 1].split('=', 1)) == 1 else ''
        return default

    def pf_expr(self, *args):
        expr = ''
        if len(args) > 1:
            for arg in args:
                expr += arg
        else:
            expr = args[0]

        expr = re.sub(r'=', '==', expr)
        expr = re.sub(r'\bround\b', '|ROUND|', expr)
        expr = re.sub('mod', '%', expr)
        expr = re.sub(r'\bdiv\b', '/', expr)
        expr = re.sub(r'trunc (\S+)', r'floor(\1)', expr)
        expr = re.sub(r'ceil ([1-9]+)', r'ceil(\1)', expr)
        expr = re.sub(r'floor ([1-9]+)', r'ceil(\1)', expr)
        expr = re.sub(r'ln\((.*)\)', r'log(\1)', expr)
        return eval(expr)
       


ROUND = Infix(lambda x,y: round(x,floor(y)))

if __name__ == '__main__':
    pf = ParserFunctions()
    print(f'This module contains following wiki parser functions: {pf.functions.keys()}')
