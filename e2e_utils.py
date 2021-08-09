from pyhocon import ConfigFactory
from utils import symlink_safe

class E2eConfig(object):

    def __init__(self, path='e2e-coref/experiments.conf'):
        self.path = path
        self.conf = ConfigFactory.parse_file(self.path)

    def contains(self, key):
        return key in self.conf

    def keys(self):
        return self.conf.keys()

    def __enter__(self):
        self.open_file = open(self.path, 'at')
        return self

    def __exit__(self, *args):
        self.open_file.close()

    def add_eval_conf(self, name, src_conf_name, eval_json_path, eval_conll_path):
        symlink_safe('e2e-coref/logs', name, src_conf_name)
        self.open_file.write('''
{name} = ${{{src_conf_name}}} {{
  embeddings = [${{glove_300d}}, ${{turian_50d}}]
  eval_path = {eval_json_path}
  conll_eval_path = {eval_conll_path}
}}
'''.format(**locals()))

    def add_train_conf(self, name, src_conf_name, train_json_path, eval_json_path, eval_conll_path):
        self.open_file.write('''
{name} = ${{{src_conf_name}}} {{
  train_path = {train_json_path}
  eval_path = {eval_json_path}
  conll_eval_path = {eval_conll_path}
}}
'''.format(**locals()))