import regex
from xml.etree import ElementTree
import glob
import os
import json

class TemplateTranscludor:

    def __init__(self):
        with open('./templates/lookup_table.txt', 'rt') as file:
            self.template_lookup_table = json.load(file)

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

    def get_redirect_name(self, template_with_redirect):
        name = template_with_redirect.split(' ', 1)[1]
        name = name.strip()
        name = name[2:-2]
        name = name.replace('_', ' ')
        return name


    def find_template_definitions(self, template_name):
        templates = []
        for lookup_table_entry in self.template_lookup_table[template_name]:
            templates.append(self.find_template_definition_in_file(lookup_table_entry))
        for template in templates:
            redirect = regex.search(r'(?=(?:\#redirect|\#REDIRECT)).*', template)
            if redirect is not None:
                new_template_name = self.get_redirect_name(template)
                print(template)
                print(new_template_name)
                templates = self.find_template_definitions(new_template_name)
        return templates
        
    def process_variables(self, string_containing_variables, result, top_level):
        variable = regex.search(r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', string_containing_variables)
        if variable is not None:
            split = variable.group()[3:-3].split('|', maxsplit=1)
            if split[0] in result['variables']:
                return result['variables'][split[0]]
            variable_true_value = self.process_variables(variable.group()[3:-3], result, False)
            if top_level == True:
                return variable_true_value
            string_containing_variables = string_containing_variables[:variable.start()] + variable_true_value + string_containing_variables[variable.end():]
        split_variable_value = string_containing_variables.split('|', maxsplit=1)
        if len(split_variable_value) < 2:
            return result['variables'][split_variable_value[0]]
        else:
            if split_variable_value[0] in result['variables']:
                return result['variables'][split_variable_value[0]]
            else:
                return split_variable_value[1]
                
    def place_variables_into_template(self, result):
        transcluded_template = ''
        template_definitions = self.find_template_definitions(result['template_name'])
        for template_definition in template_definitions:
            if len(result['variables'].keys()) == len(regex.findall(r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', template_definition)):
                variable = regex.search(r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', template_definition)
                while variable is not None:
                    template_definition = template_definition[:variable.start()] + self.process_variables(variable.group(), result, True) + template_definition[variable.end():]
                    variable = regex.search(r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', template_definition)
                transcluded_template = template_definition
                break
        return transcluded_template

    def process_template(self, template_string):
        parenthesless_template = regex.sub(r'(^{{|}}$)', '', template_string)
        name_and_variables = parenthesless_template.split('|')
        result = {}
        result['template_name'] = name_and_variables[0].strip()
        variables = {}
        i = 1
        for variable in name_and_variables[1:]:
            variable_name_value = variable.split('=')
            if len(variable_name_value) < 2:
                variables[str(i)] = variable_name_value[0].strip()
            else:
                variables[variable_name_value[0].strip()] = variable_name_value[1].strip()
            i += 1
        result['variables'] = variables
        return result


temp_trans = TemplateTranscludor()
# with open('enwiki-20200920-pages-articles-multistream5.xml-p558392p958045', 'rt', encoding='utf-8') as file:
#     for event, elem in ElementTree.iterparse(file):
#         _, _, tag = elem.tag.rpartition('}')
#         if tag == 'page':
#             ns = elem.findtext('{http://www.mediawiki.org/xml/export-0.10/}ns')
#             if(ns != '10'):
#                 content = elem.findtext(
#                     '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
#                 test_content = 'asdf {{actinium|2|+|14}}\n asdf'
#                 first_template = regex.search(r'\{\{(?>(?:(?!{{|}})[\S\s])+|(?R))*+\}\}', test_content, flags=regex.VERSION1 + regex.VERBOSE)
#                 result = temp_trans.process_template(first_template.group()) 
#                 print(temp_trans.place_variables_into_template(result))
#                 # while first_template is not None:
#                 #     test_content = test_content[:first_template.start()] + 'processed template ' + regex.sub(r'[{}]', '', first_template.group()) + test_content[first_template.end():]
#                 #     first_template = regex.search(r'\{\{(?>(?:(?!{{|}})[\S\s])+|(?R))*+\}\}', test_content, flags=regex.MULTILINE + regex.VERSION1 + regex.VERBOSE)
#                 # print(test_content)
#             if event == 'end':
#                 elem.clear()
