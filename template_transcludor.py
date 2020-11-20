import regex
from xml.etree import ElementTree
import glob
import os
import json
import wikitextparser as wtp


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Constants(object, metaclass=Singleton):

    def __init__(self):
        self.constants = {
            'parser_functions': [
                'lc',
                'lcfirst',
                'uc',
                'ucfirst',
                'formatnum',
                '#dateformat',
                '#formatdate',
                'padleft',
                'padright',
                'plural',
                '#time',
                'gender',
                '#tag',
                '#expr',
                '#if',
                '#ifeq',
                '#iferror',
                '#ifexpr',
                '#ifexist',
                '#switch',
                '#invoke',
                '#lst',
                '#lsth',
                '#lstx',
            ],
            'variables': [
                'FULLPAGENAME',
                'PAGENAME',
                'NAMESPACE',
                'NAMESPACENUMBER',
            ]
        }

    def is_in_constants(self, text):
        for key in self.constants.keys():
            if text in self.constants[key]:
                return key
        return None


class ParserFunctions(object):

    def __init__(self):
        self.functions = {
            '#if': self.pf_if,
            '#ifeq': self.pf_ifeq,
            'ucfirst': self.ucfirst,
        }

    def variable(self, frame):
        try:
            return str(frame[frame['name']])
        except KeyError:   
            return frame['name']

    def ucfirst(self, string):
        if len(string) > 0:
            return string[0].upper() + string[1:]
        else:
            return string

    def pf_if(self, test_value, if_true, if_false = ''):
        if test_value == '':
            return if_false
        else:
            return if_true

    def pf_ifeq(self, test_value_1, test_value_2, if_true, if_false):
        if test_value_1 == test_value_2:
            return if_true
        else:
            return if_false


class TemplateTranscludor:

    def __init__(self, templates_source_folder='./templates'):
        with open(f'{templates_source_folder}/lookup_table.txt', 'rt') as file:
            self.template_lookup_table = json.load(file)
        with open(f'{templates_source_folder}/redirects_table.txt', 'rt') as file:
            self.redirects_table = json.load(file)
        self.pf = ParserFunctions()

    def get_template_call_from_text(self, text):
        return regex.search(r'\{\{(?>(?:(?!{{|}})[\S\s])+|(?R))*+\}\}', text, flags=regex.VERSION1 + regex.VERBOSE)

    def parse_template_call(self, template_call):
        constants = Constants()
        name_vars = []
        result = {
            'constant_type': False
        }

        stripped_template_call = template_call[2:-2].strip()
        constant_type = constants.is_in_constants(
            stripped_template_call.split(':', 1)[0].strip())

        if constant_type:
            if constant_type == 'parser_functions':
                result['constant_type'] = 'parser_function'
            else:
                result['constant_type'] = 'variable'
            split_pf_call = stripped_template_call.split(':', 1)
            name_vars.append(split_pf_call[0])
            if len(split_pf_call) > 1:
                name_vars.extend(self.parse_param_list(split_pf_call[1].strip()))
        else:
            name_vars = self.parse_param_list(stripped_template_call)

        result['name'] = self.pf.ucfirst(name_vars[0].strip()) if constant_type != 'parser_function' else name_vars[0].strip()
        result['variables'] = {}
        for i, variable in enumerate(name_vars[1:]):
            split_variable = variable.split('=', 1)
            if len(split_variable) > 1:
                result['variables'][split_variable[0]
                                    ] = split_variable[1].strip()
            else:
                result['variables'][str(i + 1)] = variable.strip()


        return result
    
    def parse_param_list(self, paramlist):
        number_of_square = 0
        number_of_curly = 0
        removed_double_curlies = False
        added_double_curlies = False
        last_cut = 0
        result = []
        i = 0
        while i < len(paramlist):
            if i + 1 < len(paramlist) and paramlist[i] == '[' and paramlist[i+1] == '[':
                number_of_square += 2
                i += 2
                continue
            if i + 1 < len(paramlist) and paramlist[i] == '{' and paramlist[i+1] == '{':
                number_of_curly += 2
                i += 2
                added_double_curlies = True
                continue
            elif paramlist[i] == '{' and added_double_curlies:
                number_of_curly += 1
                added_double_curlies = False
            else:
                added_double_curlies = False

            if i + 1 < len(paramlist) and paramlist[i] == ']' and paramlist[i+1] == ']':
                number_of_square -= 2
                i += 2
                continue

            if i + 1 < len(paramlist) and paramlist[i] == '}' and paramlist[i+1] == '}':
                number_of_curly = number_of_curly - 2 if number_of_curly - 2 > 0 else 0
                i += 2
                removed_double_curlies = True
                continue
            elif paramlist[i] == '}' and removed_double_curlies:
                number_of_curly -= 1
                removed_double_curlies = False
            else:
                removed_double_curlies = False
            if number_of_curly == 0 and number_of_square == 0 and paramlist[i] == '|':
                result.append(paramlist[last_cut:i])
                last_cut = i + 1
            i+=1
        result.append(paramlist[last_cut:])
        return result

            


    def fetch_template_definition(self, template_name):
        real_template_name = template_name
        while real_template_name in self.redirects_table:
            real_template_name = self.redirects_table[real_template_name]
        try:
            template_lookup_table_entry = self.template_lookup_table[real_template_name]
            return self.find_template_definition_in_file(template_lookup_table_entry)
        except KeyError:
            return None

    def find_template_definition_in_file(self, lookup_table_entry):
        with open(f'templates/{lookup_table_entry[0]["filename"]}', 'rt') as file:
            template = ''
            for index, line in enumerate(file):
                if index >= lookup_table_entry[0]['start']:
                    if index <= lookup_table_entry[0]['end']:
                        template += line
                    else:
                        break
            template = template.rstrip('\r\n')
            return template

    def get_variable_from_text(self, text):
        return regex.search(
            r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', text)

    def subst_variable_with_value(self, variable_def, variables):
        stripped_variable_def = variable_def[3:-3]
        split_variable_def = stripped_variable_def.strip().split('|', 1)

        while (split_variable_def[0].strip() not in variables or variables[split_variable_def[0].strip()] == '') and len(split_variable_def) > 1:
            if split_variable_def[1].startswith('{{{') and split_variable_def[1].endswith('}}}'):
                split_variable_def = split_variable_def[1][3:-
                                                           3].strip().split('|', 1)
            else:
                split_variable_def[0] = split_variable_def[1]
                break

        return variables[split_variable_def[0].strip()] if split_variable_def[0].strip() in variables else split_variable_def[0].strip()

    def place_variables_into_template(self, template_definition, variables):
        variable = self.get_variable_from_text(template_definition)

        while variable is not None:
            subst_variable = self.subst_variable_with_value(
                variable.group(), variables)
            template_definition = template_definition[:variable.start(
            )] + str(subst_variable) + template_definition[variable.end():]
            variable = self.get_variable_from_text(template_definition)

        return template_definition

    def process_text(self, text, level=0, frame = {}):
        template_call = self.get_template_call_from_text(text)
        while template_call is not None:
            name_vars = self.parse_template_call(template_call.group())
            if not name_vars['constant_type']:
                template_definition = self.fetch_template_definition(
                    name_vars['name'])
            else:
                template_definition = template_call.group()[2:-2]
            template_definition = self.place_variables_into_template(template_definition, name_vars['variables']) if template_definition is not None else ''
            text = text[:template_call.start(
            )] + self.process_text(template_definition, level + 1, {**frame, **name_vars}) + text[template_call.end():]
            template_call = self.get_template_call_from_text(text)
        if level != 0:
            if frame['constant_type'] == 'parser_function':
                if frame['name'] in self.pf.functions:
                    name_vars = self.parse_template_call('{{' + text + '}}')
                    try:
                        text = self.pf.functions[frame['name']](*name_vars['variables'].values())
                    except TypeError:
                        print(f'Too many or too few arguments in function call:{text}')
            elif frame['constant_type'] == 'variable':
                text = self.pf.variable(frame)

        return text
        
    def proces_xml_wiki(self, wiki_xml_path):
        with open(wiki_xml_path, 'rt', encoding='utf-8') as source_file:
            for event, elem in ElementTree.iterparse(source_file):
                _, _, tag = elem.tag.rpartition('}')
                if tag == 'page':
                    ns = elem.findtext(
                        '{http://www.mediawiki.org/xml/export-0.10/}ns')
                    if ns != '10':
                        title = elem.findtext(
                            '{http://www.mediawiki.org/xml/export-0.10/}title')
                        content = elem.findtext(
                            '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
                        print(self.process_text(content, frame={
                            'NAMESPACENUMBER': ns,
                            'PAGENAME': title,
                            'FULLPAGENAME': title,
                            'NAMESPACE': 'Pending' #map namespace number to namespace
                        }))
                    if event == 'end':
                        elem.clear()

    #################################################


templ_trans = TemplateTranscludor()
templ_trans.proces_xml_wiki('./test_file.xml')

# with open('enwiki-20201001-pages-articles-multistream.xml', 'rt', encoding='utf-8') as file:
#     with open('test_file.xml', 'wb') as write_file:
#         i = 0
#         for event, elem in ElementTree.iterparse(file):
#             _, _, tag = elem.tag.rpartition('}')
#             if tag == 'page':
#                 element_string = ElementTree.tostring(elem, encoding='utf-8')
#                 write_file.write(element_string)
#                 if event == 'end':
#                     elem.clear()
#                 i += 1
#             if i > 0:
#                 break
