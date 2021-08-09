# Usage: eval-single-python-model.sh <input_dir>

. scripts/deep-coref/init-cartesius-gpu.sh

python -u deep-coref/pairwise_learning.py $1