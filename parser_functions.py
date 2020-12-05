import re
from math import floor, ceil, sin, cos, tan, acos, asin, atan, log
from dateutil import parser

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
            '#ifexist': lambda *args: '', #cannot be implemented in this env
            '#ifexpr': self.pf_ifexpr,
            '#iferror': self.pf_iferror,
            'formatnum': self.pf_formatnum,
            'padleft': self.pf_padleft,
            'padright': self.pf_padright,
            '#dateformat': self.pf_dateformat,
            '#formatdate': self.pf_dateformat,
            'plural': self.pf_plural,


        }
    #todo return some sillines on wrong arguments
    def variable(self, frame):
        if frame['name'] is None:
            return ''
        try:
            return str(frame[frame['name']])
        except KeyError:   
            return frame['name']
    
    def uc(self, *args):
        if len(args) < 1:
            return ''
        return args[0].upper()

    def ucfirst(self, *args):
        string = args[0]
        if len(string) > 0:
            return string[0].upper() + string[1:]
        else:
            return string

    def lc(self, *args):
        if len(args) < 1:
            return ''
        return args[0].lower()

    def lcfirst(self, *args):
        string = args[0]
        if len(string) > 0:
            return string[0].lower() + string[1:]
        else:
            return string

    def pf_if(self, *args):
        if len(args) < 1:
            return ''
        if args[0] == '':
            return args[2] if len(args) > 2 else ''
        else:
            return args[1] if len(args) > 1 else ''

    def pf_ifeq(self, *args):
        if len(args) < 2:
            return ''
        if args[0] == args[1]:
            return args[2] if len(args) > 2 else ''
        else:
            return args[3] if len(args) > 3 else ''
    
    def pf_tag(self, *args):
        if len(args) < 1:
            return ''
        attrs = ''
        for variable in args[2:]:
                attrs += f'{variable} '
        return f"<{args[0]} {attrs}>{args[1]}</{args[0]}>"

    def pf_switch(self, *args):
        if len(args) < 1:
            return ''
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
        try:
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
            expr = re.sub(r'trunc\((.*)\)', r'floor(\1)', expr)
            expr = re.sub(r'ln\((.*)\)', r'log(\1)', expr)
            expr = re.sub(r'(floor|ceil|sin|cos|tan|asin|acos|atan|abs) ([1-9.]+)', r'\1(\2)', expr)
            result = eval(expr)
            if result == True:
                return 1
            elif result == False:
                return 0
            return result
        except:
            return f'<span class="error">Error thrown evaluating expression: "{args[0]}"</span>'


    def pf_ifexpr(self, expr=False, if_true = '', if_false = '', *args):
        if bool(self.pf_expr(expr)):
            return if_true
        else:
            return if_false
    
    def pf_iferror(self, test_string='class="error"', error = '', correct = None, *args):
        if 'class="error"' in test_string:
            return error
        elif correct is not None:
            return correct
        else:
            return test_string

    def pf_formatnum(self, num, *args):
        result = ''
        if len(args) > 0 and args[0] == 'R':
            return num.replace(',', '')
        else:
            start = num.find('.') if num.find('.') != -1 else len(num)
            while start > 0:
                result = num[start - 3:] + result
                num = num[:start - 3]
                start -= 3
                if start > 0:
                    result = ',' + result
            result = num + result
            return result

    def pf_padleft(self, string_to_pad, pad_number, padder_string = '0', *args):
        try:
            padded_length = int(pad_number)
            if len(string_to_pad) > padded_length:
                return string_to_pad
            no_missing_chars = padded_length - len(string_to_pad)
            padder_string_repetitions = int(no_missing_chars / len(padder_string))
            padder_string_part = no_missing_chars % len(padder_string)
            return padder_string * padder_string_repetitions + padder_string[:padder_string_part] + string_to_pad

        except ValueError:
            return f'<span class="error">Invalid padded length in padleft call: "{pad_number}"</span>'
    

    def pf_padright(self, string_to_pad, pad_number, padder_string = '0', *args):
        try:
            padded_length = int(pad_number)
            if len(string_to_pad) > padded_length:
                return string_to_pad
            no_missing_chars = padded_length - len(string_to_pad)
            padder_string_repetitions = int(no_missing_chars / len(padder_string))
            padder_string_part = no_missing_chars % len(padder_string)
            return string_to_pad + padder_string * padder_string_repetitions + padder_string[:padder_string_part]

        except ValueError:
            return f'<span class="error">Invalid padded length in padright call: "{pad_number}"</span>'

    def pf_dateformat(self, date_string, format='', *args):
        try:
            date = parser.parse(date_string)
            formats = {
                'dmy': lambda date: date.strftime('%d %b %Y'),
                'mdy': lambda date: date.strftime('%B %d, %Y'),
                'ymd': lambda date: date.strftime('%Y %b %d')
            }
            if format in formats:
                return formats[format](date)
            else:
                return date.strftime('%Y-%m-%d')
        except:
            return f'<span class="error">Cannot parse date: "{date_string}"</span>'
    
    def pf_plural(self, num, sg, pl, *args):
        if num == '1':
            return sg
        else:
            return pl


ROUND = Infix(lambda x,y: round(x,floor(y)))

if __name__ == '__main__':
    pf = ParserFunctions()
    print(f'This module contains following wiki parser functions: {pf.functions.keys()}')
