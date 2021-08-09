import utils
import os

_data = None

def DATA(): return _data

def RAW(): return os.path.join(DATA(), 'data_raw') + '/'
def MODELS(): return os.path.join(DATA(), 'models') + '/'
def CLUSTERERS(): return os.path.join(DATA(), 'clusterers') + '/'
def DOCUMENTS(): return os.path.join(DATA(), 'documents') + '/'
def ACTION_SPACES_BASE(): return os.path.join(DATA(), 'action_spaces') + '/'
def GOLD(): return os.path.join(DATA(), 'gold') + '/'
def MISC(): return os.path.join(DATA(), 'misc') + '/'

def CHINESE(): return False
def PRETRAINED_WORD_VECTORS():
    return ('data/polyglot_64d.txt' if CHINESE() else 'data/w2v_50d.txt')

def FEATURES_BASE(): return os.path.join(DATA(), 'features') + '/'
def MENTION_DATA(): return os.path.join(FEATURES_BASE(), 'mention_data') + '/'
def RELEVANT_VECTORS(): return MENTION_DATA()
def PAIR_DATA(): return os.path.join(FEATURES_BASE(), 'mention_pair_data') + '/'
def DOC_DATA(): return os.path.join(FEATURES_BASE(), 'doc_data') + '/'

def ACTION_SPACE_NAME(): return 'action_spaces'
def ACTION_SPACE(): return os.path.join(ACTION_SPACES_BASE(), ACTION_SPACE_NAME()) + '/'

def set_data_dir(dir_):
    global _data
    _data = dir_
    utils.mkdir(MISC())
    utils.mkdir(FEATURES_BASE())
    utils.mkdir(MENTION_DATA())
    utils.mkdir(PAIR_DATA())
    utils.mkdir(DOC_DATA())
    utils.mkdir(MODELS())
    utils.mkdir(CLUSTERERS())
    utils.mkdir(DOCUMENTS())
    utils.mkdir(ACTION_SPACES_BASE())
    utils.mkdir(ACTION_SPACE())
    
set_data_dir('./data/')
