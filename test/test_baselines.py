from baselines import RandomAntecedent, RandomAgglomeration
from test_utils import read_sample_corpus
from collections import Counter

def print_cluster_stats(docs):
    cluster_sizes = [Counter(m.attributes['set_id'] for m in doc.system_mentions)
                     for doc in docs]
    num_clusters = [len(counter) for counter in cluster_sizes]
    cluster_size_max = [max(counter.values()) for counter in cluster_sizes]
    print('Number of clusters:', num_clusters)
    print('Max cluster sizes:', cluster_size_max)    

def test_random_antecedent():
    corpus = read_sample_corpus()
    system = RandomAntecedent()
    new_docs = [system(doc) for doc in corpus]
    print_cluster_stats(new_docs)

def test_random_agglomeration():
    corpus = read_sample_corpus()
    system = RandomAgglomeration()
    new_docs = [system(doc) for doc in corpus]
    print_cluster_stats(new_docs)

if __name__ == "__main__":
    test_random_antecedent()
    test_random_agglomeration()