from manipulations import delete_subtree, syn_mask
from random import Random
from cort.core.corpora import Corpus
import shutil
import os
from manipulations2 import MaskContextK

shutil.rmtree('test/tmp', ignore_errors=True)
os.mkdir('test/tmp')


def test_delete_whole_tree():
    whole_tree = ['(TOP*', '(S(PP(PP*', '(ADVP*))', '(ADVP*))', '*', 
                  '(NP(NP*', '*)', '(PP*', '(NP*)))', '(VP*', '(VP*', 
                  '(VP*', '*', '(NP(NP(NP*)', '(PP*', '(NP*)))', '*', '*', 
                  '(NP(NP*)', '(PP*', '(NP*)))))))', '*))']
    syntax_arr = delete_subtree(whole_tree)
    assert syntax_arr[0] == '(TOP*' 
    syntax_str = ' '.join(syntax_arr)
    assert syntax_str.count('(') == 1
    assert syntax_str.count(')') == 1
    
def test_delete_subtree():
    subtree = ['(PP(PP*)']
    syntax_arr = delete_subtree(subtree)
    assert syntax_arr[0] == '(PP*'

    subtree = ['(PP(PP*', '*)']
    syntax_arr = delete_subtree(subtree)
    assert syntax_arr[0] == '(PP*' 
    syntax_str = ' '.join(syntax_arr)
    assert syntax_str.count('(') == 1
    assert syntax_str.count(')') == 0


def test_delete_semantic_role():
    subtree = ['(ARGM-DIS*)']
    syntax_arr = delete_subtree(subtree)
    assert syntax_arr[0] == '*'


def test_delete_ner_tag():
    subtree = ['(GPE)']
    syntax_arr = delete_subtree(subtree)
    assert syntax_arr[0] == '*'
