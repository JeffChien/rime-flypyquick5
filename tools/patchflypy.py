#!/usr/bin/env python

"""
This script add quick5 codes as suffix to flypy code table.
TODO, refactor
"""

#%%
from __future__ import absolute_import
from tofly import Trie
from tofly import load_base_table, dump_table
from tofly import is_a_symbol, is_a_phrase

#%%
def patch_table(orig: Trie, patch: Trie):
    onode = orig
    for symbol, ochild in onode.children.items():
        if symbol in patch.children:
            pnode = patch.children[symbol]
            for pcode in pnode.orig:
                for ocode, opriority in ochild.orig.items():
                    ochild.after[f'{ocode}{pcode}'] = opriority
            patch_table(ochild, patch)

#%%
def patch_quick5_to_flypy():
    flypy_symbol_table = load_base_table('../flypy_self_main.dict.yaml')
    flypy_phrase_table = load_base_table('../flypy_self_phrase.dict.yaml')
    quick5_table = load_base_table('./quick5.dict.yaml')
    patch_table(flypy_symbol_table, quick5_table)
    patch_table(flypy_phrase_table, quick5_table)

    with open('./flypy_quick5_main.dict.yaml', 'w+') as f:
        dump_table(flypy_symbol_table, [], is_a_symbol, f)

    with open('./flypy_quick5_phrase.dict.yaml', 'w+') as f:
        dump_table(flypy_phrase_table, [], is_a_phrase, f)

#%%
patch_quick5_to_flypy()
