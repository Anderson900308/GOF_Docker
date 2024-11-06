# Docker for Gaussian Opacity Field
The Repo is the docker enviroment setup for [Gaussian Opacity field](https://github.com/autonomousvision/gaussian-opacity-fields), and modification for [Homee Nerfstudio](https://github.com/homee-ai/nerfstudio).

# Build Docker
Clone the repository and build the Docker environment, need to modified the mount path in docker run command.
```
git clone https://github.com/Anderson900308/GOF_Docker.git
cd gof_docker

# Build Docker environment
docker build -t homee_docker .

# Run the docker image 
docker run -it --gpus all -v /path/to/dataset/:/gof/data --name homee homee_docker 

# To open interatcive shell
docker start homee
docker exec -it homee bash

```
# Nerfstudio Dataset
The dataset is trained in Homee Nerfstudio enviroment, and the format should be as followed
```
Dataset
|---Dataset_nerfstudio
    |---colmap
    |   |---arkit/0
    |   |---colmap/0
    |---images
        |---0001.png
        |---0002.png
        |---...
```
The optimized result shoud be convert to 3DGS.ply format
```
Result
|---splat,ply
```
---
# Mesh Extraction
To run mesh extraction in Nerfstudio format
```
python extract_mesh_nerfstudio.py \
    -s "Path to source folder" \
    --method "Method used in Homee Nerfstudio" \
    --splat_file "Splat file used to extract the mesh" \
    --texture_mesh

# Example 
python extract_mesh_nerfstudio.py \
    -s ./nerfstudio_data/homee_dataset3/homee_dataset3_nerfstudio/ \
    --method arkit \
    --splat_file ./nerfstudio_data/result/h3/splat_modified.ply \
    --texture_mesh
```
# Mesh Postprocess
To run mesh postprocess in Nerfstudio format
```
python mesh_postprocess_nerfstudio.py \
    -s "Path to source folder" \
    --method "Method used in Homee Nerfstudio" \
    --splat_file "Splat file used for extract the mesh" \
    --mesh "Target mesh file to do the postprocess"

# Example 
python mesh_postprocess_nerfstudio.py \
    -s ./nerfstudio_data/homee_dataset3/homee_dataset3_nerfstudio/ \
    --method arkit \
    --splat_file ./nerfstudio_data/result/h3/splat_modified.ply \
    --mesh ./nerfstudio_data/result/h3/splat_modified_mesh_thres_0.95.ply
```
# Normal Dataset
The dataset to train in the Gaussian Opacity Field follows the data format from 3DGS
```
homee_dataset2
|---images
|   |---0001.png
|   |---0002.png
|   |---...
|---sparse
    |---0
        |---cameras.bin
        |---images.bin
        |---points3D.bin
```
The input for mesh extraction follows the result format from 3DGS
```
homee_dataset2_result
|---point_cloud
|   |---iteration_<number of iteration 1>
|   |   |---point_cloud.ply
|   |---iteration_<number of iteration 2>
|   |   |---point_cloud.ply
|   |---...
|---cameras.json
|---cfg_args
|---input.ply
    
```

# Shell Script
The source path, model path and other arguments are defined in the beginning of pipelin.sh

```
#!/bin/bash

SOURCE_PATH="./data/homee_dataset2"
MODEL_PATH="./data/homee_dataset2/result"
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
```
<details>
<summary><span style="font-weight: bold;">Shell Script Arguments for pipline.sh</span></summary>

  #### SOURCE_PATH 
  Path to the source directory containing a COLMAP dataset.
  #### MODEL_PATH
  Path where the trained model should be stored.
  #### ITERATION 
  Number of total iterations to train for.
  #### SKIP_GOF
  Flag to skip training of GOF.
  #### TEXTURE_MESH
  Flag to extract texture mesh from 3DGS.
  #### SKIP_POSTPROCESS
  Flag to skip postprocess of mesh result.

</details>
<br>




