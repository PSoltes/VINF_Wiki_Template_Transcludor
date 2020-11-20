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
    
    def uc(self, **args):
        return args['0'].upper()

    def ucfirst(self, **args):
        string = args['0']
        if len(string) > 0:
            return string[0].upper() + string[1:]
        else:
            return string

    def lc(self, **args):
        return args['0'].lower()

    def lcfirst(self, **args):
        string = args['0']
        if len(string) > 0:
            return string[0].lower() + string[1:]
        else:
            return string

    def pf_if(self, **args):
        if args['1'] == '':
            return args['3'] if '3' in args else ''
        else:
            return args['2']

    def pf_ifeq(self, **args):
        if args['1'] == args['2']:
            return args['3']
        else:
            return args['4'] if '4' in args else ''
    
    def pf_tag(self, **args):
        attrs = ''
        for key in args.keys():
            if key != '1' and key != '2':
                attrs += f'{key}={args[key]} '
        return f"<{args['1']} {attrs}>{args['2']}</{args['1']}>"        

if __name__ == '__main__':
    pf = ParserFunctions()
    print(f'This module contains following wiki parser functions: {pf.functions.keys()}' )
