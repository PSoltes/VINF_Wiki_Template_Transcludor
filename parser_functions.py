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

if __name__ == '__main__':
    pf = ParserFunctions()
    print(f'This module contains following wiki parser functions: {pf.functions.keys()}')
    print(pf.pf_tag(*['b', 'Pavol Soltes', 'aria-id="255"', 'name="nasrac"']))
