import regex
from xml.etree import ElementTree
import glob
import os

def process_variables(string_containing_variables, result, top_level):
    variable = regex.search(r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', string_containing_variables)
    if variable is not None:
        split = variable.group()[3:-3].split('|', maxsplit=1)
        if split[0] in result['variables']:
            return result['variables'][split[0]]
        variable_true_value = process_variables(variable.group()[3:-3], result, False)
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

def process_template(template_string):
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

def place_variables_into_template(result):
    transcluded_template = ''
    with open('templates/' + result['template_name'] + '.txt', 'r') as file:
        for line in file:
            variable = regex.search(r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', line)
            while variable is not None:
                line = line[:variable.start()] + process_variables(variable.group(), result, True) + line[variable.end():]
                variable = regex.search(r'\{\{\{(?>(?:(?!{{{|}}})[\S\s])+|(?R))*+\}\}\}', line)
            transcluded_template += line
    return transcluded_template

with open('enwiki-20200920-pages-articles-multistream5.xml-p558392p958045', 'rt', encoding='utf-8') as file:
    for event, elem in ElementTree.iterparse(file):
        _, _, tag = elem.tag.rpartition('}')
        if tag == 'page':
            ns = elem.findtext('{http://www.mediawiki.org/xml/export-0.10/}ns')
            if(ns != '10'):
                content = elem.findtext(
                    '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
                test_content = 'asdf {{actinium|2|+|14}}\n asdf'
                first_template = regex.search(r'\{\{(?>(?:(?!{{|}})[\S\s])+|(?R))*+\}\}', test_content, flags=regex.VERSION1 + regex.VERBOSE)
                result = process_template(first_template.group()) 
                print(place_variables_into_template(result))
                # while first_template is not None:
                #     test_content = test_content[:first_template.start()] + 'processed template ' + regex.sub(r'[{}]', '', first_template.group()) + test_content[first_template.end():]
                #     first_template = regex.search(r'\{\{(?>(?:(?!{{|}})[\S\s])+|(?R))*+\}\}', test_content, flags=regex.MULTILINE + regex.VERSION1 + regex.VERBOSE)
                # print(test_content)
            if event == 'end':
                elem.clear()
