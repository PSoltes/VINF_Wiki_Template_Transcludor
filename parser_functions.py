class ParserFunctions(object):

    def __init__(self):
        self.functions = {
            '#if': self.pf_if,
            '#ifeq': self.pf_ifeq,
            'uc': self.uc,
            'ucfirst': self.ucfirst,
            'lc': self.lc,
            'lcfirst': self.lcfirst
        }

    def variable(self, frame):
        try:
            return str(frame[frame['name']])
        except KeyError:   
            return frame['name']
    
    def uc(self, string):
        return string.upper()

    def ucfirst(self, string):
        if len(string) > 0:
            return string[0].upper() + string[1:]
        else:
            return string

    def lc(self, string):
        return string.lower()

    def lcfirst(self, string):
        if len(string) > 0:
            return string[0].lower() + string[1:]
        else:
            return string

    def pf_if(self, test_value, if_true, if_false = ''):
        if test_value == '':
            return if_false
        else:
            return if_true

    def pf_ifeq(self, test_value_1, test_value_2, if_true, if_false = ''):
        if test_value_1 == test_value_2:
            return if_true
        else:
            return if_false

if __name__ == '__main__':
    pf = ParserFunctions()
    print(f'This module contains following wiki parser functions: {pf.functions.keys()}' )