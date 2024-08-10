# Docker for Gaussian Opacity Field

# Dataset
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
The source path, model path and other arguments are defined in the begining of pipelin.sh
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


# Build Docker
Clone the repository and build the Docker environment, need to modified the mount path in docker run command.
```
git clone 
cd gof_docker

# Build Docker environment
docker build -t homee_docker .

# Run the docker image 
docker run -it --gpus all -v /path/to/dataset/:/gof/data --name homee homee_docker 

# To open interatcive shell
docker start homee
docker exec -it homee bash

```

