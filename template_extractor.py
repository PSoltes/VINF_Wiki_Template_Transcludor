import re
from xml.etree import ElementTree
import glob
import os
from functools import reduce
import json


class TemplateExtractor:

    def __init__(self, path_to_source, path_to_templates_folder='./templates'):
        self.redirects_lookup_table = {}
        self.lookup_table = {}
        self.currently_parsed_templates = []
        self.path_to_source = path_to_source
        self.path_to_templates_folder = path_to_templates_folder
        self.file_counter = 0

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

    def cleanup_templates_folder(self):
        files = glob.glob(self.path_to_templates_folder + '/*')
        for f in files:
            os.remove(f)

    def normalize_redirect_name(self, template_with_redirect):
        name = template_with_redirect.split(' ', 1)[1]
        name = name.strip(' _')
        name = name[2:-2]
        name = name.split(':', 1)[1]
        name = re.sub(r'[\s_]', ' ', name)
        return name

    def check_for_redirects(self, text):
        redirect = re.search(r'(?=(?:\#redirect|\#REDIRECT)).*', text)
        if redirect is not None:
            return self.normalize_redirect_name(text)
        else:
            return None

    def parse_page(self, title, text):
        _, _, title = title.rpartition(':')
        redirect = self.check_for_redirects(text)
        if redirect is not None:
            if title in self.redirects_lookup_table:
                print('Warning! Rewriting redirect entry')
            self.redirects_lookup_table[title] = redirect
            return
        text = self.remove_comments(text)
        text = self.remove_noinclude(text)
        text = self.get_onlyinclude_text(text)
        text = self.remove_includeonly_tags(text)
        text = text.rstrip('\r\n')
        text += '\n'
        self.currently_parsed_templates.append({
            'title': title,
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
                    self.lookup_table[template['title']] = [lookup_table_entry]
            self.currently_parsed_templates = []
            self.file_counter += 1

    def extract_templates(self):
        with open(self.path_to_source, 'rt', encoding='utf-8') as source_file:
            for event, elem in ElementTree.iterparse(source_file):
                _, _, tag = elem.tag.rpartition('}')
                if tag == 'page':
                    ns = elem.findtext(
                        '{http://www.mediawiki.org/xml/export-0.10/}ns')
                    if ns == 10:
                        title = elem.findtext(
                            '{http://www.mediawiki.org/xml/export-0.10/}title')
                        content = elem.findtext(
                            '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
                        self.parse_page(title, content)
                    if len(self.currently_parsed_templates) == 100:
                        self.write_parsed_templates_into_file()
                if event == 'end':
                    elem.clear()
        with open(f'{self.path_to_templates_folder}/lookup_table.txt', 'x', encoding='utf-8') as f:
            f.write(json.dumps(self.lookup_table))
        with open(f'{self.path_to_templates_folder}/redirects_table.txt', 'x', encoding='utf-8') as f:
            f.write(json.dumps(self.redirects_lookup_table))


if __name__ == '__main__':
    templ_extractor = TemplateExtractor(
        'enwiki-20201001-pages-articles-multistream.xml')
    templ_extractor.extract_templates()
