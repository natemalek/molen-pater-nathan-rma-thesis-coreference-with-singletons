from config import scorer
import os
from cort.core.corpora import Corpus
import codecs
import random
import subprocess

def copy_gold_annotations(doc):
    doc.system_mentions = doc.annotated_mentions
    for m in doc.system_mentions:
        m.attributes['set_id'] = m.attributes['annotated_set_id']
    return doc

class Oracle(object):
    name = 'oracle'
    def __call__(self, doc):
        return copy_gold_annotations(doc)

class RandomAntecedent(object):

    name = "random-antecedent"
    rand = random.Random(8429)

    def __call__(self, doc):
        doc.system_mentions = doc.annotated_mentions
        mentions_to_process = list(doc.system_mentions)
        self.rand.shuffle(mentions_to_process)
        available_set_id = 1
        for i, m in enumerate(mentions_to_process):
            antecedent = self.rand.choice(mentions_to_process[:i] + [None])
            if antecedent is None:
                m.attributes['set_id'] = available_set_id
                available_set_id += 1
            else:
                m.attributes['set_id'] = antecedent.attributes['set_id']
        return doc

class RandomAgglomeration(object):
    ''' 
    Implement a process similar to deep-coref
    
    Clark, K., & Manning, C. D. (2016). Improving Coreference Resolution by Learning 
    Entity-Level Distributed Representations. Proceedings of the 54th Annual Meeting 
    of the Association for Computational Linguistics, 643–653. 
    https://doi.org/10.18653/v1/P16-1061
    '''

    name = "random-agglomeration"
    rand = random.Random(22923)

    def __call__(self, doc):
        doc.system_mentions = doc.annotated_mentions
        mentions_to_process = list(enumerate(doc.system_mentions))
        self.rand.shuffle(mentions_to_process)
        # start with singleton
        clusters = [[m] for _, m in mentions_to_process]
        # divide mentions into clusters
        for i, m in mentions_to_process:
            cluster_m, = [c for c in clusters if m in c]
            antecedents = set(doc.system_mentions[:i])
            candidates = [c for c in clusters if antecedents.intersection(c)] + ['Skip']
            chosen_cluster = self.rand.choice(candidates)
            if chosen_cluster != 'Skip':
                intact_clusters = [c for c in clusters if c not in [cluster_m, chosen_cluster]]
                merged_cluster = [cluster_m + chosen_cluster]
                clusters = intact_clusters + merged_cluster
        # convert clusters into set IDs
        for i, cluster in enumerate(clusters):
            for m in cluster:
                assert m.attributes.get('set_id') is None, 'Clustering collision'
                m.attributes['set_id'] = i
        return doc

class OneClusterBaseline(object):
    name = "one-cluster"
    def __call__(self, doc):
        doc.system_mentions = doc.annotated_mentions
        for m in doc.system_mentions:
            m.attributes['set_id'] = 1
        return doc

class HeadMatchBaseline(object):
    name = "head-match"
    def __call__(self, doc):
        doc.system_mentions = doc.annotated_mentions
        head2id = {}
        for m in doc.system_mentions:
            head = m.attributes['head_as_lowercase_string']
            if head not in head2id:
                head2id[head] = len(head2id)+1
            m.attributes['set_id'] = head2id[head]
        return doc

