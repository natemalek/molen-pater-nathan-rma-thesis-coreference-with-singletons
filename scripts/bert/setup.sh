set -x

. scripts/setup-cartesius.sh
mkdir -p output/bert
python3 -m venv output/bert/venv
. output/bert/venv/bin/activate
cd bert-coref/
pip3 install --upgrade pip
pip3 install -r requirements.txt
./setup_all.sh
./setup_training.sh ../data/ontonotes-release-5.0 ../output/bert/data
cp -r ../output/bert/data/cased_L-12_H-768_A-12 ../output/bert/data/spanbert_tiny
