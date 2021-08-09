# to be `source`d into scripts

# important to load all modules before activating conda
# otherwise it will throw the error "Tcl wasn't intalled properly"
module unload python/3.5.2
module unload python
module load Miniconda2
# module load cuda/8.0.61
# module load cudnn/8.0-v6.0
# # enable this if you want to use a GPU
# # use an older version to get rid of this warning: UserWarning: Your cuDNN version is more recent than the one Theano officially supports. If you see any problems, try updating Theano or downgrading cuDNN to version 5.1.
module load cuda/7.0.28
module load cudnn/7.0-v4-prod

source activate python2-conda
export THEANO_FLAGS='device=gpu,floatX=float32'
python -u scripts/test-gpu.py
