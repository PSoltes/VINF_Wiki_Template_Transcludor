import regex
from xml.etree import ElementTree
import glob
import os
import json
import wikitextparser as wtp
from parser_functions import ParserFunctions
from datetime import datetime
from multiprocessing import Process, Array
import functools
import sys
import getopt

used_templates = dict()
total_pfs = 0
invokes = 0


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

class TemplateTranscludor:

    def __init__(self, result_file='results.txt', templates_source_folder='./templates'):
        with open(f'{templates_source_folder}/lookup_table.json', 'rt') as file:
            self.template_lookup_table = json.load(file)
        with open(f'{templates_source_folder}/redirects_table.json', 'rt') as file:
            self.redirects_table = json.load(file)
        self.pf = ParserFunctions()
        self.template_cache = {}
        self.used_templates = {}
        self.invokes = 0
        self.total_pfs = 0
        self.result_file = open(result_file, 'w')
    
    def __del__(self):
        self.result_file.close()

    def get_template_call_from_text(self, text):
        if text == None:
            return None
        i = 0
        braces = 0
        added = []
        left_pos = None
        while i < len(text):
            if i+2 < len(text) and  text[i] == '{' and text[i+1] == '{' and text[i+2] == '{':
                braces += 3
                i += 3
                added.append(3)
                continue
            if i+2 < len(text) and  text[i] == '}' and text[i+1] == '}' and text[i+2] == '}' and len(added) > 0 and added[-1] == 3:
                braces = max(braces - 3, 0)
                added.pop()
                i += 3
                continue
            if i+1 < len(text) and  text[i] == '{' and text[i+1] == '{':
                braces += 2
                if left_pos is None:
                    left_pos = i
                added.append(2)
                i += 2
                continue
            if i+1 < len(text) and  text[i] == '}' and text[i+1] == '}' and len(added) > 0 and added[-1] == 2:
                braces = max(braces - 2, 0)
                if left_pos is not None and braces == 0:
                    return {
                        'start': left_pos,
                        'end': i + 2,
                        'group': text[left_pos : i + 2]
                    }
                added.pop()
                i += 2
                continue
            i += 1
        return None
    
    def parse_pf_call(self, pf_call):
        pass

    def parse_template_call(self, template_call):
        constants = Constants()
        name_vars = []
        result = {
            'constant_type': False,
            'variables': {}
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
            result['name'] = split_pf_call[0]
            if len(split_pf_call) > 1:
                result['variables'] = [variable.strip()
                                   for variable in self.parse_param_list(split_pf_call[1].strip())]
        else:
            name_vars = self.parse_param_list(stripped_template_call)
            result['name'] = self.pf.ucfirst(*[name_vars[0].strip()])
            i = 1
            for variable in name_vars[1:]:
                split_variable = variable.split('=', 1)
                if len(split_variable) > 1:
                    result['variables'][split_variable[0]] = split_variable[1].strip()
                else:
                    result['variables'][str(i)] = variable.strip()
                i += 1

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
                result.append(paramlist[last_cut:i].strip(' \r\n\t'))
                last_cut = i + 1
            i+=1
        result.append(paramlist[last_cut:].strip(' \r\n\t'))
        return result

            


    def fetch_template_definition(self, template_name):
        real_template_name = template_name
        while real_template_name in self.redirects_table:
            if real_template_name == self.redirects_table[real_template_name]:
                break
            real_template_name = self.redirects_table[real_template_name]
        try:
            template_lookup_table_entry = self.template_lookup_table[real_template_name]
            if not template_name in self.used_templates:
                self.used_templates[template_name] = 1
            return self.find_template_definition_in_file(template_lookup_table_entry)
        except KeyError:
            if not template_name in self.used_templates:
                self.used_templates[template_name] = 0
            return None

    def find_template_definition_in_file(self, lookup_table_entry):
        with open(f'templates/{lookup_table_entry["filename"]}', 'rt') as file:
            template = ''
            for index, line in enumerate(file):
                if index >= lookup_table_entry['start']:
                    if index <= lookup_table_entry['end']:
                        template += line
                    else:
                        break
            template = template.rstrip('\r\n')
            return template

    def get_variable_from_text(self, text):
        return regex.search(
            r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', text)

    def remove_subst_call_from_template(self, template_call):
        #everything here is subst cause content isnt dynamically changed
        return regex.sub(r'(subst:|safesubst:)', '', template_call, flags=regex.IGNORECASE)

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
        substituted_template = ''
        variable = self.get_variable_from_text(template_definition)

        while variable is not None:
            subst_variable = self.subst_variable_with_value(
                variable.group(), variables)
            substituted_template += template_definition[:variable.start(
            )] + str(subst_variable)
            template_definition = template_definition[variable.end():]
            variable = self.get_variable_from_text(template_definition)
        substituted_template += template_definition

        return substituted_template

    def process_pf(self, text, frame, level = 0):
        if level > 25:
            print(f'Warning exceeding 10th level recursion. Level: {level}')
        expanded_text = ''
        text_to_search = text
        template_call = self.get_template_call_from_text(text_to_search)
        while template_call is not None:
            name_vars = self.parse_template_call(template_call['group'])
            expanded_text += text_to_search[:template_call['start']] + str(self.process_pf(template_call['group'][2:-2], {**frame, **name_vars}, level + 1))
            text_to_search = text_to_search[template_call['end']:]
            template_call = self.get_template_call_from_text(text_to_search)
        expanded_text += text_to_search
        if level != 0 and frame['constant_type'] == 'parser_function':
            if frame['name'] in self.pf.functions:
                name_vars = self.parse_template_call('{{' + expanded_text + '}}')
                try:
                    expanded_text = self.pf.functions[frame['name']](*name_vars['variables'])
                except TypeError:
                    print(f'Too many or too few arguments in function call:{text}')
        elif level != 0 and frame['constant_type'] == 'variable':
            expanded_text = self.pf.variable(frame)
        self.total_pfs += 1
        if 'name' in frame and frame['name'] == '#invoke':
            self.invokes += 1
        return expanded_text

    def process_text(self, text, level = 0, frame = {}):
        if level > 15:
            print(f'Level: {level}')
            return regex.sub(r'({{|}})', '', text)
        expanded_text = ''
        text_to_search = text if text is not None else ''
        if not 'name' in frame or not frame['name'] in self.template_cache:
                    template_call = self.get_template_call_from_text(text_to_search)
                    while template_call is not None:
                        template_call['group'] = self.remove_subst_call_from_template(template_call['group'])
                        name_vars = self.parse_template_call(template_call['group'])
                        if not name_vars['constant_type']:
                            template_definition = self.fetch_template_definition(name_vars['name'])
                            if template_definition == None:
                                expanded_text += text_to_search[:template_call['start']] + template_call['group'][2:-2]
                            else:
                                expanded_text += text_to_search[:template_call['start']] + self.process_text(template_definition, level + 1, {**frame, **name_vars})
                        else:
                            template_definition = template_call['group'][2:-2]
                            expanded_text += text_to_search[:template_call['start']] + '{{' + self.process_text(template_definition, level + 1, {**frame, **name_vars}) + '}}'
                        text_to_search = text_to_search[template_call['end']:]
                        template_call = self.get_template_call_from_text(text_to_search)
                    expanded_text += text_to_search
        else:
            expanded_text = self.template_cache[frame['name']]
        if level != 0:
            if not frame['constant_type']:
                if frame['name'] not in self.template_cache:
                    self.template_cache[frame['name']] = expanded_text
                expanded_text = self.place_variables_into_template(expanded_text, frame['variables'])
        else:
            expanded_text = self.process_pf(expanded_text, frame)

        return expanded_text

    def page_process(self, text, frame, result_file, stat_array):
        try:
            processed_page = self.process_text(text, frame=frame)
            result_file.write(processed_page)
            stat_array[0] += len(self.used_templates)
            stat_array[1] += sum(x == 0 for x in self.used_templates.values())
            stat_array[2] += self.total_pfs
            stat_array[3] += self.invokes
            not_used_temps = functools.reduce(lambda a,b : a + b + '\n' if self.used_templates[b] == 0 else a, self.used_templates.keys(), "")
            with open('./not_found_templates.txt', 'a') as not_found_temp_file:
                not_found_temp_file.write(not_used_temps)
        except Exception as e:
            print(e)  
        
    def proces_xml_wiki(self, wiki_xml_path):
        stat_array = Array('i',[0,0,0,0], lock=False)        
        errors = []
        i = 0
        print(datetime.now())
        with open(wiki_xml_path, 'rt', encoding='utf-8') as source_file:
            for event, elem in ElementTree.iterparse(source_file):
                _, _, tag = elem.tag.rpartition('}')
                if tag == 'page':
                    i += 1
                    if i % 500 == 0:
                        print(f'Processed {i} pages')
                        with open('./numeral_usage.txt', 'w', encoding='utf-8') as fileee:
                            fileee.write(str(i)+'\n')
                            fileee.write(f'Total parser functions: {stat_array[2]}\n')
                            fileee.write(f'Total invokes: {stat_array[3]}\n')
                            fileee.write(f'Templates requested: {stat_array[0]}\n')
                            fileee.write(f'Requested templates not found: {stat_array[1]}\n')
                    ns = elem.findtext(
                        '{http://www.mediawiki.org/xml/export-0.10/}ns')
                    if int(ns) < 4 and i != 1922:
                        title = elem.findtext(
                            '{http://www.mediawiki.org/xml/export-0.10/}title')
                        content = elem.findtext(
                            '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
                        try:
                            page_parse_process = Process(target=self.page_process, kwargs={
                                "text": content,
                                "frame": {
                                    'NAMESPACENUMBER': ns,
                                    'PAGENAME': title,
                                    'FULLPAGENAME': title,
                                    'NAMESPACE': 'Pending'  # map namespace number to namespace
                                },
                                "result_file": self.result_file,
                                "stat_array": stat_array,
                            })
                            page_parse_process.start()
                            page_parse_process.join(timeout=600)
                            page_parse_process.terminate()

                        except Exception as e:
                            errors.append(content)
                            print(e)
                    if event == 'end':
                        elem.clear()
        with open('./errors.txt', 'x', encoding='utf-8') as error_log:
            for error in errors:
                error_log.write(error)
        # with open('./template_usage.json', 'w', encoding='utf-8') as temp_usage_file:
        #     json.dump(used_templates.__dict__, temp_usage_file)
        with open('./numeral_usage.txt', 'w', encoding='utf-8') as fileee:
            fileee.write('Full file')
            fileee.write(f'Total parser functions: {stat_array[2]}\n')
            fileee.write(f'Total invokes: {stat_array[3]}\n')
            fileee.write(f'Templates requested: {stat_array[0]}\n')
            fileee.write(f'Requested templates not found: {stat_array[1]}\n')
        print(datetime.now())


# templ_trans = TemplateTranscludor()
# templ_trans.proces_xml_wiki('/home/psoltes/Downloads/enwiki-20201020-pages-articles-multistream1.xml-p1p41242')

if __name__ == '__main__':
    templates_folder = None
    output_file = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ho:t:', ['output=', 'templ='])
    except getopt.GetoptError:
      print ('template_transludor.py -o <outputfile> -t <template_folder> [list of inputs]')
      sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('template_transludor.py -o <outputfile> -t <template_folder> [list of inputs]')
            sys.exit()
        elif opt in ['-o', '--output']:
            output_file = arg
        elif opt in ['-t', '--templ']:
            templates_folder = arg
    
    templ_trans = TemplateTranscludor(output_file, templates_folder)
    for arg in args:
        templ_trans.proces_xml_wiki(arg)
