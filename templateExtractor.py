import re
from xml.etree import ElementTree
import glob
import os

files = glob.glob('./templates/*')
for f in files:
    os.remove(f)


with open('enwiki-20200920-pages-articles-multistream5.xml-p558392p958045', 'rt', encoding='utf-8') as file:
    for event, elem in ElementTree.iterparse(file):
        _, _, tag = elem.tag.rpartition('}')
        if tag == 'page':
            ns = elem.findtext('{http://www.mediawiki.org/xml/export-0.10/}ns')
            if(ns == '10'):
                _, _, title = elem.findtext(
                    '{http://www.mediawiki.org/xml/export-0.10/}title').rpartition(':')
                title = title.replace('/', '0x2215')
                content = elem.findtext(
                    '{http://www.mediawiki.org/xml/export-0.10/}revision/{http://www.mediawiki.org/xml/export-0.10/}text')
                content = re.sub(r'<noinclude>.*</noinclude>', '', content, flags=re.DOTALL + re.MULTILINE)
                try:
                    f = open(f'templates/{title}.txt', 'x', encoding='utf-8')
                    f.write(content)
                    f.close()
                except:
                    print(title)
            if event == 'end':
                elem.clear()
