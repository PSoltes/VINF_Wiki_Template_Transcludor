import re
from xml.etree import ElementTree
import glob
import os
from functools import reduce
import json

files = glob.glob('./templates/*')
for f in files:
    os.remove(f)

parsed_templates = []
lookup_table = {}
counter = 0
with open('enwiki-20201001-pages-articles-multistream.xml', 'rt', encoding='utf-8') as file:
    for event, elem in ElementTree.iterparse(file):
        _, _, tag = elem.tag.rpartition('}')
        if tag == 'page':
            ns = elem.findtext('{http://www.mediawiki.org/xml/export-0.10/}ns')
            if(ns == '10'):
                _, _, title = elem.findtext(
                    '{http://www.mediawiki.org/xml/export-0.10/}title').rpartition(':')
                content = elem.findtext(
                    '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
                content = re.sub(r'<noinclude>(?:(?!<\/noinclude>).)*<\/noinclude>', '', content, flags=re.DOTALL + re.MULTILINE)
                content = content.rstrip('\r\n')
                content += '\n'
                parsed_templates.append({
                    'title': title,
                    'content': content
                })
                if len(parsed_templates) == 100:
                    with open(f'templates/{counter}.txt', 'x', encoding='utf-8') as file:
                        lines_counter = 0
                        for template in parsed_templates:
                            file.write(template['content'])
                            lookup_table_entry = {
                                'start': lines_counter,
                                'end': lines_counter + len(template['content'].splitlines()) - 1,
                                'filename': f'{counter}.txt'
                            }
                            lines_counter += len(template['content'].splitlines())
                            if template['title'] in lookup_table:
                                lookup_table[template['title']].append(lookup_table_entry)
                            else:
                                lookup_table[template['title']] = [lookup_table_entry]       
                    parsed_templates = []
                    counter += 1
            if event == 'end':
                elem.clear()
f = open('templates/lookup_table.txt', 'x', encoding='utf-8')
f.write(json.dumps(lookup_table))
f.close()