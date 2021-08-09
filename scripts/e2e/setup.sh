set -x

VENV_DIR=$1
mkdir -p $VENV_DIR
python2.7 -m virtualenv -p python2.7 $VENV_DIR

if [ $? -ne 0 ]; then
	exit 1
fi

source $VENV_DIR/bin/activate

# check if it is really python2.7
python -c 'import sys; assert sys.version.startswith("2.7")'
if [ $? -ne 0 ]; then
	>&2 echo "The python version is different from expected"	
	exit 1
fi

if [ ! -e data/ontonotes-release-5.0 ]; then
    >&2 echo "OntoNotes 5.0 not found, make sure you link/copy it to <project root>/data/ontonotes-release-5.0"
	exit 1
fi

pip install tensorflow-gpu==1.3.0
if [ $? -ne 0 ]; then
	>&2 echo "****************************************************************"	
	>&2 echo "Failed to install tensorflow-gpu, please install it manually"	
	>&2 echo "****************************************************************"	
fi

pip install --trusted-host pypi.python.org -r scripts/e2e/requirements.txt
if [ $? -ne 0 ]; then
	>&2 echo "Failed to install requirements"	
	exit 1
fi

# Get the repository
git clone https://github.com/minhlab/e2e-coref.git
cd e2e-coref && \
	git reset --hard && \
	git checkout da7a6859552bd87c0c4b4c88077281a28c0a2281 && \
	bash -x ./setup_all.sh && \
	bash -x ./setup_pretrained.sh && \
	bash -x ./setup_training.sh

if [ $? -ne 0 ]; then
	>&2 echo "Failed to setup e2e-coref"	
	exit 1
fi

deactivate