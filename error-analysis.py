'''
Created on Jan 12, 2017

@author: Minh Ngoc Le
'''

import cort
from cort.core import corpora
from cort.analysis import error_extractors
from cort.analysis import spanning_tree_algorithms
import sys
from cort.analysis.data_structures import StructuredCoreferenceAnalysis

def get_all_mention_spans(doc):
    return set(m.span for m in doc.annotated_mentions)

def remove_mention_boundary_errors(errors, ref_corpus, sys_corpus):
    ref_doc2spans = dict((doc.identifier, get_all_mention_spans(doc)) 
                         for doc in ref_corpus.documents)
    sys_doc2spans = dict((doc.identifier, get_all_mention_spans(doc)) 
                         for doc in sys_corpus.documents)
    precision_errors = errors["system"]["precision_errors"].filter(lambda e:
            e[0].span in ref_doc2spans[e[0].document.identifier] and
            e[1].span in ref_doc2spans[e[1].document.identifier])
    recall_errors = errors["system"]["recall_errors"].filter(lambda e:
            e[0].span in sys_doc2spans[e[0].document.identifier] and
            e[1].span in sys_doc2spans[e[1].document.identifier])
    mapping = {'system': {'recall_errors': recall_errors,
                          'precision_errors': precision_errors,
                          'decisions': errors['system']['decisions']}}
    return StructuredCoreferenceAnalysis(mapping, errors.corpora, errors.reference) 
            

if __name__ == '__main__':
    reference = corpora.Corpus.from_file("reference", open(sys.argv[1]))
    sys_predict = corpora.Corpus.from_file("system", open(sys.argv[2]))
    sys_predict.read_antecedents(open(sys.argv[3]))

    extractor = error_extractors.ErrorExtractor(
        reference,
        spanning_tree_algorithms.recall_accessibility,
        spanning_tree_algorithms.precision_system_output
    )
    extractor.add_system(sys_predict)

    errors = extractor.get_errors()
    coref_errors = remove_mention_boundary_errors(errors, reference, sys_predict)
    coref_errors.visualize("system")

#     they_errors = errors.filter(
#         lambda error: ' '.join(error[0].attributes['tokens']).lower() 
#                             in ('they', 'them', 'their'))
#     he_errors = errors.filter(
#         lambda error: ' '.join(error[0].attributes['tokens']).lower() 
#                             in ('he', 'him', 'his'))
#     she_errors = errors.filter(
#         lambda error: ' '.join(error[0].attributes['tokens']).lower() 
#                             in ('she', 'her', 'her'))
#     it_errors = errors.filter(
#         lambda error: ' '.join(error[0].attributes['tokens']).lower() 
#                             in ('it', 'its'))
#     pron_anaphor_errors = errors.filter(
#         lambda error: error[0].attributes['type'] == "PRO") 
# 
#     they_errors.visualize("system")