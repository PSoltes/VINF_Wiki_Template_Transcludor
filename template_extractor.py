import re
from xml.etree import ElementTree
import glob
import os
from functools import reduce
import json
from datetime import datetime
import sys, getopt


class TemplateExtractor:

    def __init__(self, path_to_source, path_to_templates_folder='./templates', path_to_modules_folder='./modules'):
        self.redirects_lookup_table = {}
        self.lookup_table = {}
        self.currently_parsed_templates = []
        self.path_to_source = path_to_source
        self.path_to_templates_folder = path_to_templates_folder
        self.path_to_modules_folder = path_to_modules_folder
        self.file_counter = 0
        self.error_log_file = open(
            './extractor_errors.txt', 'a+', encoding='utf-8')

    def __del__(self):
        self.error_log_file.close()

    def remove_noinclude(self, text):
        return re.sub(r'<noinclude>(?:(?!<\/noinclude>).)*<\/noinclude>', '', text, flags=re.DOTALL + re.MULTILINE)

    def remove_includeonly_tags(self, text):
        return re.sub(r'<includeonly>|</includeonly>', '', text)

    def remove_comments(self, text):
        return re.sub(r'<!--(?:(?!-->).)*-->', '', text, flags=re.DOTALL + re.MULTILINE)

    def get_onlyinclude_text(self, text):
        onlyinclude_text = ''
        onlyinclude_parts = re.findall(
            r'<onlyinclude>(?:(?!<\/onlyinclude>).)*<\/onlyinclude>', text, flags=re.DOTALL + re.MULTILINE)
        for part in onlyinclude_parts:
            onlyinclude_text += re.sub(r'<onlyinclude>|</onlyinclude>', '', part)
        return onlyinclude_text if onlyinclude_text != '' else text

    def cleanup_folders(self):
        files = glob.glob(self.path_to_templates_folder + '/*')
        for f in files:
            os.remove(f)
        # files = glob.glob(self.path_to_modules_folder + '/*')
        # for f in files:
        #     os.remove(f)

    def normalize_redirect_name(self, template_with_redirect):
        try:
            name = re.sub(r'\#redirect', '#REDIRECT', template_with_redirect, flags=re.IGNORECASE + re.MULTILINE)
            name = name.split('#REDIRECT', 1)[1]
            name = name.split(']]')[0]
            name = name.strip(' _')
            name = name[2:]
            name = name.split(':', 1)
            name = name[1] if len(name) > 1 else name[0]
            name = re.sub(r'[\s_]', ' ', name)
            name = name.strip()
        except IndexError:
            self.error_log_file.write(
                f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}:Error:Normalizing redirect name: {template_with_redirect}')
            self.error_log_file.write('---LogEntryEnd---')
            return None
        return name

    def check_for_redirects(self, text):
        redirect = re.search(r'(?=(?:\#redirect)).*', text, flags=re.IGNORECASE + re.MULTILINE)
        if redirect is not None:
            return self.normalize_redirect_name(text)
        else:
            return None

    def parse_page(self, title, text):
        _, _, title = title.rpartition(':')
        redirect = self.check_for_redirects(text)
        if redirect is not None:
            if title in self.redirects_lookup_table:
                self.error_log_file.write(
                    f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}:Warning:Rewriting redirect entry with title: {title}\n Original text: {text}')
                self.error_log_file.write('---LogEntryEnd---')
            self.redirects_lookup_table[title] = redirect
            return
        text = self.remove_comments(text)
        text = self.remove_noinclude(text)
        text = self.get_onlyinclude_text(text)
        text = self.remove_includeonly_tags(text)
        text = text.rstrip('\r\n')
        text += '\n'
        self.currently_parsed_templates.append({
            'title': title.strip(),
            'content': text
        })
        return

    def write_parsed_templates_into_file(self):
        with open(f'templates/{self.file_counter}.txt', 'x', encoding='utf-8') as file:
            lines_counter = 0
            for template in self.currently_parsed_templates:
                file.write(template['content'])
                lookup_table_entry = {
                    'start': lines_counter,
                    'end': lines_counter + len(template['content'].splitlines()) - 1,
                    'filename': f'{self.file_counter}.txt'
                }
                lines_counter += len(template['content'].splitlines())
                if template['title'] not in self.lookup_table:
                    self.lookup_table[template['title']] = lookup_table_entry
                else:
                    self.error_log_file.write(
                        f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}:Warning:Duplicate template name: {template["title"]}')
                    self.error_log_file.write('---LogEntryEnd---')
            self.currently_parsed_templates = []
            self.file_counter += 1

    def extract_templates(self):
        with open(self.path_to_source, 'rt', encoding='utf-8') as source_file:
            self.cleanup_folders()
            for event, elem in ElementTree.iterparse(source_file):
                _, _, tag = elem.tag.rpartition('}')
                if tag == 'page':
                    ns = elem.findtext(
                        '{http://www.mediawiki.org/xml/export-0.10/}ns')
                    title = elem.findtext(
                        '{http://www.mediawiki.org/xml/export-0.10/}title')
                    if ns == '10':
                        content = elem.findtext(
                            '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
                        self.parse_page(title, content)
                    if len(self.currently_parsed_templates) > 100:
                        self.write_parsed_templates_into_file()
                    # if ns == '828':
                    #     title = elem.findtext(
                    #         '{http://www.mediawiki.org/xml/export-0.10/}title')
                    #     content = elem.findtext(
                    #         '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
                    #     try:
                    #         with open(f'{self.path_to_modules_folder}/{title}.lua', 'x') as module_file:
                    #             module_file.write(content)
                    #     except:
                    #         print(f'Couldnt save module with name: {title}')
                    if event == 'end':
                        elem.clear()
            self.write_parsed_templates_into_file()
        with open(f'{self.path_to_templates_folder}/lookup_table.json', 'x', encoding='utf-8') as f:
            f.write(json.dumps(self.lookup_table))
        with open(f'{self.path_to_templates_folder}/redirects_table.json', 'x', encoding='utf-8') as f:
            f.write(json.dumps(self.redirects_lookup_table))


if __name__ == '__main__':
    templates_folder = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ht:', ['templ='])
    except getopt.GetoptError:
      print ('template_extractor.py -t <template_folder> <input>')
      sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('template_extractor.py -t <template_folder> <input>')
            sys.exit()
        elif opt in ['-t', '--templ']:
            templates_folder = arg
    templ_extractor = TemplateExtractor(args[0], templates_folder)
    templ_extractor.extract_templates()
