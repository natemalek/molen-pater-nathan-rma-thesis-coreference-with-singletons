import os
from manipulations import Manipulation, Mention, MentionAndPosition, Syntax, Event
from data import DatasetPaths
from random import Random

def main():
    root_out = os.path.join('output', 'conll-2012-manipulated')
    os.makedirs(root_out, exist_ok=True)
    
    datasets = []
    for seed in [885,  82, 501,  99, 562]:
        name = "mentions_%d" %seed
        MentionDataset = DatasetPaths(os.path.join(root_out, name))
        datasets.append((MentionDataset, Mention(Random(seed), show_names=False)))
    
    for seed in [751, 702, 514, 590, 988]:
        name = 'mentions_instance_%d' %seed
        MentionInstanceDataset = DatasetPaths(os.path.join(root_out, name))
        datasets.append((MentionInstanceDataset, Mention(Random(seed), show_names=True)))
    
    MentionInstancePositionDataset = DatasetPaths( 
            os.path.join(root_out, 'mentions_instance_position'))
    MentionInstancePositionSyntaxDataset = DatasetPaths(
            os.path.join(root_out, 'mentions_instance_position_syntax'))
    PositionEventsDataset = DatasetPaths(
            os.path.join(root_out, 'position_events'))
    datasets.extend([(MentionInstancePositionDataset, MentionAndPosition(None, show_names=True)), 
                     (MentionInstancePositionSyntaxDataset, Syntax()),
                     (PositionEventsDataset, Event())])
    
    for ds, manipulate_func in datasets:
        manipulate_func('data/conll-2012-flat/train', ds.train_path)
        manipulate_func('data/conll-2012-flat/dev', ds.dev_path)
        manipulate_func('data/conll-2012-flat/test-key', ds.test_path)

if __name__ == '__main__':
    main()