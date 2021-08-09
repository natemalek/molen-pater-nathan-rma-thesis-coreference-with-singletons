import json
import pandas as pd
import traceback
from cort.core import corpora
from cort.analysis import error_extractors
from cort.analysis import spanning_tree_algorithms
import sys
import re
import os

def _mention_key(mention_str):
    start_pos, = re.findall(r'mention_(\d+)_\d+', mention_str)
    return int(start_pos)

def chains_str_from_events(events_str):
    if not events_str or not isinstance(events_str, str):
        return None
    events = [s.split(':', 1)[1] for s in events_str.split(';')]
    chains = {}
    for event in events:
        if (event in ['display_instructions', 'close_instructions', 
                    'start_grouping', 'save_grouping', 'cancel_grouping',
                    'submit'] or 
            event.startswith('select_chain') or event.startswith('confidence') or
            event.startswith('clicked_on_singleton')):
            pass # nothing to do
        elif event.startswith('add_singleton'):
            mention, = re.findall(r'mention_\d+_\d+', event)
            if mention in chains:
                return None # some delete-group events might be missing
            else:
                chains[mention] = [mention]
        elif event.startswith('add_mention_to_chain'):
            (added_mention, chain_mention), = re.findall(r'\((mention_\d+_\d+),\s*(mention_\d+_\d+)(?:=mention_\d+_\d+)*\)', event)
            if added_mention in chains and len(chains[added_mention]) >= 2:
                return None # some delete-group events might be missing
            if chain_mention not in chains:
                return None # some adding events might be missing
            chain = chains[chain_mention]
            chain.append(added_mention)
            chains[added_mention] = chain
        elif event.startswith('add_chain_to_chain'):
            (removed_chain_mention, remaining_chain_mention), = re.findall(r'\((mention_\d+_\d+)(?:=mention_\d+_\d+)*,\s*(mention_\d+_\d+)(?:=mention_\d+_\d+)*\)', event)
            if removed_chain_mention not in chains:
                return None # some adding events might be missing
            if remaining_chain_mention not in chains:
                return None # some adding events might be missing
            removed_chain = chains[removed_chain_mention]
            remaining_chain = chains[remaining_chain_mention]
            for m in list(removed_chain): # avoid endless loop by making a copy
                remaining_chain.append(m)
                chains[m] = remaining_chain
        elif event.startswith('remove_mention'):
            (removed_mention, chain_mention), = re.findall(r'\((mention_\d+_\d+),\s*(mention_\d+_\d+)(?:=mention_\d+_\d+)*\)', event)
            if removed_mention not in chains[chain_mention]:
                return None # something is wrong
            if removed_mention in chains:
                del chains[removed_mention]
        elif event.startswith('delete_group'):
            chain_mention, = re.findall(r'\((mention_\d+_\d+)(?:=mention_\d+_\d+)*\)', event)
            del chains[chain_mention]
        else:
            assert False, 'Unknown event: ' + event
    return ','.join('='.join(chain) for chain in chains.values())


def unpack_json(json_str):
    try:
        json_obj = json.loads(json_str)
        # because sometimes a name appears twice, we have to be careful
        names = set(item['name'] for item in json_obj)
        join_vals = lambda name: ''.join((item.get('value') or '') 
                                         for item in json_obj if item['name'] == name)
        data = {name: join_vals(name) for name in names}
        return pd.Series(data)
    except:
        print("Failed to parse the string: '%s...'" % json_str[:100], file=sys.stderr)
        traceback.print_exc()
        return pd.Series({'chains': ''})

def extract_errors(gold_path, ann_path):
    gold = corpora.Corpus.from_file("gold", open(gold_path))
    ann = corpora.Corpus.from_file("ann", open(ann_path))
    ante_path = ann_path + '.ante'
    assert os.path.exists(ante_path), 'Antecedent file not found at expected location: %s' %ante_path
    with open(ante_path) as f:
        ann.read_antecedents(f)

    extractor = error_extractors.ErrorExtractor(
        gold,
        spanning_tree_algorithms.recall_accessibility,
        spanning_tree_algorithms.precision_system_output
    )
    extractor.add_system(ann)
    return extractor.get_errors()


def visualize(gold_path, ann_path):
    errors = extract_errors(gold_path, ann_path)
    errors.visualize("ann")