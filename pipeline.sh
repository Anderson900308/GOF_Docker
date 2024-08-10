#!/bin/bash

SOURCE_PATH="./data/homee_dataset2_3"
MODEL_PATH="./data/homee_dataset2_3/result"
ITERATION="50000"
SKIP_GOF=false
TEXTURE_MESH=true
SKIP_POSTPROCESS=true

if [ "$SKIP_GOF" = "true" ]; then
    echo "Skipping GOF"
else
    echo "Training GOF"
    python train.py -s $SOURCE_PATH -m $MODEL_PATH --iteration $ITERATION
fi

if [ "$TEXTURE_MESH" = "true" ]; then
    echo "Extract textured mesh"
    python extract_mesh.py -s $SOURCE_PATH -m $MODEL_PATH --iteration $ITERATION --texture_mesh
else
    echo "Extract normal mesh"
    python extract_mesh.py -s $SOURCE_PATH -m $MODEL_PATH --iteration $ITERATION 
fi

if [ "$SKIP_POSTPROCESS" = "true" ]; then
    echo "Skipping postprocess"
else
    echo "Postprocess"
    python mesh_postprocess.py -m $MODEL_PATH --iteration $ITERATION
fi








