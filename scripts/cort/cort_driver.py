# adapt from cort/scripts/train-and-predict-all.py
import os
import subprocess

project_dir_abs = os.path.dirname(os.path.abspath(__file__))
##cort_home = os.path.join(project_dir_abs, 'output', 'cort', 'venv', 'bin')
# Nathan edit:
cort_home = os.path.join("/mnt/c/Users/natha/Documents/Thesis/even/", 'output', 'cort', 'venv', 'bin')

def get_author_provided_model(system):
    return 'models/cort/model-%s-train.obj' %system

def get_extractor(data_set, system):
    if system == "closest" or system == "latent":
        return "cort.coreference.approaches.mention_ranking.extract_substructures"
    elif system == "tree":
        return "cort.coreference.approaches.antecedent_trees.extract_substructures"
    elif system == "pair":
        if data_set == "train":
            return "cort.coreference.approaches.mention_pairs" \
                   ".extract_training_substructures"
        else:
            return "cort.coreference.approaches.mention_pairs" \
                   ".extract_testing_substructures"


def get_perceptron(system):
    if system == "pair":
        return "cort.coreference.approaches.mention_pairs.MentionPairsPerceptron"
    elif system == "closest":
        return "cort.coreference.approaches.mention_ranking.RankingPerceptronClosest"
    elif system == "latent":
        return "cort.coreference.approaches.mention_ranking.RankingPerceptron"
    elif system == "tree":
        return "cort.coreference.approaches.antecedent_trees.AntecedentTreePerceptron"


def get_cost_function(system):
    if system == "pair":
        return "cort.coreference.cost_functions.null_cost"
    else:
        return "cort.coreference.cost_functions.cost_based_on_consistency"


def get_clusterer(system):
    if system == "pair":
        return "cort.coreference.clusterer.best_first"
    else:
        return "cort.coreference.clusterer.all_ante"


def train(system, inp_path, out_model_path):
    cmd = [os.path.join(cort_home, 'cort-train'),
        "-in", inp_path,
        "-out", out_model_path,
        "-extractor", get_extractor("train", system),
        "-perceptron", get_perceptron(system),
        "-cost_function", get_cost_function(system),
        "-cost_scaling", "100"]
    print('Command: ' + ' '.join(cmd))
    return subprocess.call(cmd)


def predict(system, model_path, inp_path, out_path):
    return subprocess.call([
        os.path.join(cort_home, "cort-predict-conll"),
        "-in", inp_path,
        "-model", model_path,
        "-out", out_path,
        "-ante", out_path + ".antecedents",
        "-extractor", get_extractor('test', system),
        "-perceptron", get_perceptron(system),
        "-clusterer", get_clusterer(system)])
