from glob import glob
import shutil
import os

def main():
    model_dir = os.path.abspath('e2e-coref/logs/train-gold-mention-spans')
    for path in glob('e2e-coref/logs/eval-*-auto-2018-09-10-eb865b6-*'):
        shutil.rmtree(path)
        os.symlink(model_dir, path)

if __name__ == '__main__':
    main()