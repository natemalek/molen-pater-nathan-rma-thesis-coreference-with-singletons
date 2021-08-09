# train all models simultaneously on GPUs

set -x
# YES="-a"

. scripts/setup-cartesius.sh

scratch=/scratch-shared/minhle/EvEn

E2E_SAMPLE_MODEL=e2e-coref/logs/train-orig-gold-retrain-2019-06-06
DEEP_COREF_SAMPLE_MODEL=$scratch/output/deep-coref/conll-2012-transformed-exported/orig/models/reward_rescaling/best_weights.hdf5

# ~/drake $YES $E2E_SAMPLE_MODEL
~/drake $YES $DEEP_COREF_SAMPLE_MODEL
