import os

class DatasetPaths(object):
    def __init__(self, base_dir, test_dir_name=None):
        self.base_dir = base_dir
        self.test_dir_name = test_dir_name
        
    @property
    def train_path(self):
        return os.path.join(self.base_dir, 'train') 
        
    @property
    def dev_path(self):
        return os.path.join(self.base_dir, 'dev') 
        
    @property
    def test_path(self):
        return os.path.join(self.base_dir, self.test_dir_name or 'test') 
