wget https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/hdf5-1.10.0-patch1/src/hdf5-1.10.0-patch1.tar.gz
tar -xzvf hdf5-1.10.0-patch1.tar.gz
cd hdf5-1.10.0-patch1/
./configure
make
make install

HDF5_DIR=/home/minhle/scratch/hdf5-1.10.0-patch1/hdf5/ pip install --user h5py