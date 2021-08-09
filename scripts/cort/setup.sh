set -x

mkdir -p output/cort/venv
python3 -m venv output/cort/venv
. output/cort/venv/bin/activate

pip install -U pip
pip install tqdm joblib docopt
# other versions of matplotlib won't work with Cartesius as of May 2019
# matplotlib needs to preceed nltk
pip install matplotlib==3.0.1 nltk
pip install soupsieve==1.2 
pip uninstall -y cort

git clone https://github.com/minhlab/cort.git
cd cort
#git reset --hard
#git checkout ...
python setup.py install

deactivate
