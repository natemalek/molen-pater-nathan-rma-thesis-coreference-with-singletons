# you have to run it on a GPU-enabled machine because the models use CudaTensor 
GPU="-gpuid 0"

cd nn
mkdir -p bps
mkdir -p conllouts

th mr_clust_embed.lua $GPU -bpsName dev -loadAndPredict -pwDevFeatPrefix downloaded-features/dev_small -anaDevFeatPrefix downloaded-features/dev_small -savedPWNetFi downloaded-models/trpldev-mce-700-200.model-pw -savedNANetFi downloaded-models/trpldev-mce-700-200.model-na -savedLSTMFi downloaded-models/trpldev-mce-700-200.model-lstm
cd ../modifiedBCS
./WriteCoNLLPreds.sh ../nn/bps bps/dev.bps ../nn/conllouts/ ../../data/conll-2012-flat/dev-all/ ../../data/conll-2012/gender.data
cd ../nn
../../reference-coreference-scorers/v8.01/scorer.pl all ../../data/conll-2012-flat/dev-all/all.v4_auto_conll conllouts/dev.bps.out
