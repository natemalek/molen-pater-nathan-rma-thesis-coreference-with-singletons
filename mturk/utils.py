from cort.core.spans import Span
from collections import defaultdict
import re
import os
from glob import glob
from itertools import islice


def map_values(dict_, func):
    ''' 
    Apply function <code>func</code> over the values of the dictionary <code>dict_</code>.
    Return a new dictionary.
    '''
    return {key: func(val) for key, val in dict_.items()}


def extract_results_official_scorer_log_file(path):
    recall_precision_regex = r'Recall:[\(\)\d/ ]+ ([\d\.]+)%\s+Precision:[\(\)\d/ ]+ ([\d\.]+)%'
    line_of_interest_regex = (r'METRIC (muc|bcub|ceafe):|' +
                                r'Identification of Mentions:\s+' + recall_precision_regex + '|' +
                                r'Coreference:(?:.+)\s+F1: ([\d\.]+)%')
    with open(path) as f:
        s = f.read()
    try:
        matchers = list(re.finditer(line_of_interest_regex, s))
        metric1_m, mention_identification_m, result1_m, metric2_m, _, result2_m, _, _, metric3_m, _, result3_m, _ = matchers
        results = [float(m.group(4)) for m in [result1_m, result2_m, result3_m]]
        return {
            'mention_r': mention_identification_m.group(2),
            'mention_p': mention_identification_m.group(3),
            'f1_' + metric1_m.group(1): result1_m.group(4),
            'f1_' + metric2_m.group(1): result2_m.group(4),
            'f1_' + metric3_m.group(1): result3_m.group(4),
            'f1_conll': sum(results) / 3 
        }
    except:
        print('Error in file: %s' %path)
        raise


def remove_write_protection(path):
    if os.path.exists(path):
        os.chmod(path, 0o777)


def symlink_safe(root_dir, link_file, destination):
    link_file = os.path.join(root_dir, link_file)
    destination = os.path.join(root_dir, destination)
    if os.path.islink(link_file):
        os.remove(link_file) # avoid error if the script has been run before
    os.symlink(os.path.abspath(destination), link_file)


def match_with_line_no(text_file_path, line_of_interest_regex):
    with open(text_file_path) as f:
        matchers_with_line_no = ((re.search(line_of_interest_regex, line), line_no) for line_no, line in enumerate(f))
        matchers_with_line_no = [(matcher, line_no) for line_no, matcher in matchers_with_line_no if matcher]
    return matchers_with_line_no


def grouper(list_, n):
    """
    Collect data into fixed-length chunks or blocks
    Adapt from https://docs.python.org/3/library/itertools.html#itertools-recipes
    
    >>> list(grouper('ABCDEF', 3))
    [("A", "B", "C"), ("D", "E")]
    """
    assert len(list_) % n == 0
    args = [iter(list_)] * n
    return zip(*args)


def grouper_variable_length(list_, n):
    """
    Collect data into fixed-length chunks or blocks
    Adapt from https://docs.python.org/3/library/itertools.html#itertools-recipes
    
    >>> list(grouper_variable_length('ABCDE', 3))
    [("A", "B", "C"), ("D", "E")]
    """
    iter_ = iter(list_)
    extract_max_n = lambda: tuple(islice(iter_, n))
    group = extract_max_n()
    while len(group) > 0:
        yield group
        group = extract_max_n()


def spans_over_tokens(doc, toks):
    ''' 
    Return minimal spans (in term of number and size) that don't cross
    sentence boundary to cover given tokens and nothing else. 
    '''
    spans = []
    last_begin = last_end = -2
    sent_span_it = iter(sorted(doc.sentence_spans))
    sent_span = None
    for tok in sorted(toks):
        if tok == last_end+1 and tok <= sent_span.end:
            # enlarge the current span
            last_end = tok
        else:
            # record the current span if any, begin a new one
            if last_begin >= 0:
                spans.append(Span(last_begin, last_end))
            last_begin = last_end = tok
            while sent_span is None or tok > sent_span.end:
                sent_span = next(sent_span_it)
    if last_begin >= 0:
        spans.append(Span(last_begin, last_end))
    return spans


def span_subtract(big_span, small_spans_iterable):
    results = []
    start = big_span.begin
    small_spans_iterable = (Span(s,s) if isinstance(s, int) else s 
                            for s in small_spans_iterable)
    for s in sorted(small_spans_iterable):
        if s.begin > start:
            results.append(Span(start, s.begin-1))
        if s.end >= start:
            start = s.end+1
    if start <= big_span.end:
        results.append(Span(start, big_span.end))
    return results


def _walk_linear_positions(subtree, begin2nodes):
    if not hasattr(subtree, 'span'):
        for c in subtree:
            _walk_linear_positions(c, begin2nodes)
        subtree.span = Span(subtree[0].span.begin, subtree[-1].span.end)
        begin2nodes[subtree.span.begin].append(subtree)


def remove_linear_positions(tree):
    delattr(tree, 'begin2nodes') 
    for s in tree.subtrees(): delattr(s, 'span')


def compute_linear_positions(tree):
    if not hasattr(tree, 'begin2nodes'): 
        tree.begin2nodes = []
        for i in range(len(tree.leaves())):
            pos_node = tree[tree.leaf_treeposition(i)[:-1]]
            assert len(pos_node) == 1 # only the terminal node as child
            pos_node.span = Span(i, i)
            tree.begin2nodes.append([pos_node])
        _walk_linear_positions(tree, tree.begin2nodes)


def subtrees_over_span(root, begin_or_span, end_inclusive=None):
    '''
    Find the minimal number of subtrees to cover a contiguous span
    '''
    if isinstance(begin_or_span, Span) and end_inclusive is None:
        begin, end = begin_or_span.begin, begin_or_span.end
    else:
        begin, end = begin_or_span, end_inclusive
    assert begin <= end
    compute_linear_positions(root)
    subtrees = []
    covered_end = begin-1
    while covered_end != end:
        nodes = root.begin2nodes[covered_end+1]
        i = 0
        while (i+1 < len(nodes) and nodes[i+1].span.end <= end): 
            i += 1
        subtrees.append(nodes[i])
        covered_end = nodes[i].span.end
    return subtrees


def _walk_format_conll(tree, col):
    if isinstance(tree[0], str): # it is a POS node
        assert len(tree) == 1
    else:
        for child in tree:
            _walk_format_conll(child, col)
        col[tree.span.begin] = '(' + tree.label() + col[tree.span.begin]
        col[tree.span.end] = col[tree.span.end] + ')'


def format_conll(tree):
    col = ['*']*len(tree.leaves())
    compute_linear_positions(tree)
    _walk_format_conll(tree, col)
    return col


def add_system_set_ids(doc):
    for m in doc.system_mentions:
        set_id = doc.coref[m.span]
        m.attributes['set_id'] = set_id

        
def get_chains(doc):
    span2mention = dict((m.span, m) for m in doc.annotated_mentions)
    id2chain = defaultdict(list)
    for span in sorted(doc.coref):
        id2chain[doc.coref[span]].append(span2mention[span])
    chains = sorted(id2chain.values())
    return chains


def find_sentence(span, doc):
    for sid, sspan in enumerate(doc.sentence_spans):
        if span.begin >= sspan.begin and span.end <= sspan.end:
            return sid
    return -1


def span_overlap(span1, span2):
    toks1 = set(range(span1.begin, span1.end+1))
    toks2 = set(range(span2.begin, span2.end+1))
    return len(toks1.intersection(toks2)) > 0


def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)

def str_base(number,base):
    '''
    Convert an integer to a string in any base <= 36.

    >>> str_base(224,15)
    'ee'
    '''
    if number < 0:
        return '-' + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digit_to_char(m)
    return digit_to_char(m)

def glob_all(patterns):
    paths = []
    for pattern in patterns:
        my_paths = glob(pattern)
        assert len(my_paths) >= 1, "No match was found for pattern:" + pattern
        paths.extend(my_paths)
    return paths
