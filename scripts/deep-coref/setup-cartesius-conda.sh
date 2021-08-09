module load Miniconda2
conda create --name python2-conda python=2.7
source activate python2-conda
conda install mkl-service theano=0.8 pygpu=0.7.5