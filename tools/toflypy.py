#!/usr/bin/env python

"""
This script convert luna pinyin code to flypy code.
It is a proof of concept stage right now, the code is currently quite ugly.

TODO, refactor
"""

#%%
import re
import csv
import sys

rules = '''\
erase/^xx$/
derive/^([jqxy])u$/$1v/
derive/^([aoe])([ioun])$/$1$1$2/
xform/^([aoe])(ng)?$/$1$1$2/
xform/^sh(.*)/U$1/
xform/^ch(.*)/I$1/
xform/^zh(.*)/V$1/
xform/(.)iu$/$1Q/
xform/(.)ei$/$1W/
xform/(.)uan$/$1R/
xform/(.)[uv]e$/$1T/
xform/(.)un$/$1Y/
xform/(.)uo$/$1O/
xform/(.)ie$/$1P/
xform/(.)i?ong$/$1S/
xform/(.)ing$/$1K/
xform/(.)uai$/$1K/
xform/(.)ai$/$1D/
xform/(.)en$/$1F/
xform/(.)eng$/$1G/
xform/(.)[iu]ang$/$1L/
xform/(.)ang$/$1H/
xform/(.)ian$/$1M/
xform/(.)an$/$1J/
xform/(.)ou$/$1Z/
xform/(.)[iu]a$/$1X/
xform/(.)iao$/$1N/
xform/(.)ao$/$1C/
xform/(.)ui$/$1V/
xform/(.)in$/$1B/
xlit/QWRTYUIOPSDFGHJKLZXCVBNM/qwrtyuiopsdfghjklzxcvbnm/'''

class Trie:
    def __init__(self):
        self.children = {}
        self.orig = {}
        self.after = {}
        self.phrase_priority = None
        self.end_of_word = False

    def add(self, scp, phrase_priority=None):
        node = self
        for symbol, code, priority in scp:
            if symbol not in node.children:
                node.children[symbol] = Trie()
            node = node.children[symbol]
            if code not in node.orig:
                node.orig[code] = priority
        node.phrase_priority = phrase_priority
        node.end_of_word = True


#%%
def transform(symbol: str, code: str):
    results = []
    placeholder_translation = str.maketrans('$', '\\')
    for rule_line in rules.splitlines():
        chunks = rule_line.split('/')
        if chunks[0] == 'erase':
            if re.search(chunks[1], code):
                return []
        elif chunks[0] == 'derive':
            found = re.search(chunks[1], code)
            if found:
                results.extend(transform(symbol, found.expand(chunks[2].translate(placeholder_translation))))
        elif chunks[0] == 'xform':
            found = re.search(chunks[1], code)
            if found:
                code = found.expand(chunks[2].translate(placeholder_translation))
        elif chunks[0] == 'xlit':
            code = code.translate(str.maketrans(chunks[1], chunks[2]))

    results.append(code)
    return results

#%%
def line_with_tab(fs):
    for line in fs:
        if line.find('\t') > 0:
            yield line

def load_base_table(filename: str) -> Trie:
    root = Trie()
    with open(filename, 'r') as f:
        reader = csv.reader(line_with_tab(f), delimiter='\t')
        for line in reader:
            token = line[0]
            code = line[1]
            priority = None if len(line) == 2 else line[2]
            if len(token) == 1:
                root.add([[token, code, priority]])
            else:
                root.add(zip(token, code.split(' '), [None]*len(token)), priority)
    return root

def patch_table_with_rules(orig: Trie):
    st = [orig]
    while st:
        onode = st.pop()
        for sym, child in onode.children.items():
            for code, priority in child.orig.items():
                for after in transform(sym, code):
                    child.after[after] = priority
            st.append(child)

def dump_table(root: Trie, buf, when, out=sys.stdout):
    if root.end_of_word and when(len(buf)):
        if len(buf) == 1:
            line = '\t'.join(buf[0][:2]) if not buf[0][2] else '\t'.join(buf[0])
        else:
            word = ''.join(map(lambda x: x[0], buf))
            code = ' '.join(map(lambda x: x[1], buf))
            line = f'{word}\t{code}' if not root.phrase_priority else f'{word}\t{code}\t{root.phrase_priority}'
        print(line, file=out)

    for symbol, child in root.children.items():
        for code, priority in child.after.items():
            dump_table(child, buf + [(symbol, code, priority)], when, out)

is_a_symbol = lambda lengh: lengh == 1
is_a_phrase = lambda lengh: lengh > 1


#%%
def luna_to_flypy():
    luna_table = load_base_table('./luna_pinyin.dict.yaml')
    patch_table_with_rules(luna_table)

    with open('flypy_self_main.dict.yaml', 'w+') as f:
        dump_table(luna_table, [], is_a_symbol, f)

    with open('flypy_self_phrase.dict.yaml', 'w+') as f:
        dump_table(luna_table, [], is_a_phrase, f)

#%%
luna_to_flypy()