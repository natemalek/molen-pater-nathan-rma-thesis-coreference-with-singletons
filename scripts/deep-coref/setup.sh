# I tried using virtualenv but it caused errors on my cluster
# the software was written on Python 2
# Theano 0.7 leads to "relu note found" error
# Theano 0.9 leads to "mkl not found" error and "ImportError: cannot import name downsample"
pip install --user theano=0.8

# there's some warnings for missing pygpu but I can't install it
# "ERROR: Could not find a version that satisfies the requirement pygpu (from versions: none)"

cd deep-coref/modified_keras
python setup.py install --user

deactivate