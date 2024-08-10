# Use the NVIDIA CUDA base image
FROM nvidia/cuda:11.8.0-devel-ubuntu20.04
ENV TZ=Asia/Taiwan \
    DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y wget bzip2 libgl1 git libgtk2.0-dev vim
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh

RUN /opt/conda/bin/conda init bash

# Set environment variables for CUDA
ENV CPATH=/usr/local/cuda-11.8/targets/x86_64-linux/include:$CPATH
ENV LD_LIBRARY_PATH=/usr/local/cuda-11.8/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
ENV PATH=/usr/local/cuda-11.8/bin:/opt/conda/bin:$PATH
# Set depend on "GPU_CC+PTX", GPU_CC 
ENV TORCH_CUDA_ARCH_LIST="8.9+PTX" 

WORKDIR /gof
VOLUME [ "./gof/data" ]

COPY . .

RUN /opt/conda/bin/conda create -n gof python=3.8 -y

SHELL ["conda", "run", "-n", "gof", "/bin/bash", "-c"]

RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118 && \
    pip install -r requirements.txt 

RUN pip install submodules/diff-gaussian-rasterization && \
    pip install submodules/simple-knn/

RUN /bin/bash -c "cd submodules/tetra-triangulation && \
    conda install -c conda-forge cmake gmp cgal -y && \
    cmake . && \
    make && \
    pip install -e ."

# CMD ["bash", "-c", "source ./pipeline.sh"]
CMD ["conda", "run", "--no-capture-output", "-n", "gof", "/bin/bash", "-c", "source ./pipeline.sh"]

# ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "gof", "/bin/bash", "-c", \
#     "python train.py -s ./data/homee_dataset2/ -m ./data/homee_dataset2/result --iteration 100000&& \
#     python extract_mesh.py -m ./data/homee_dataset2/result --iteration 100000 --texture_mesh"]

# Docker build and run instructions (comments for reference)
# docker build -t homee_docker .
# docker run -it --gpus all --name homee homee_docker bash
# mount dataset
# docker run -it --gpus all -v /home/nycu-reconstruction-1/Code/data/:/gof/data --name homee homee_docker 
# docker exec --user $(id -u):$(id -g) -it homee bash

# docker run -it --gpus all \
# -v /home/nycu-reconstruction-1/Code/data/:/gof/data \
# --name homee \
# --user $(id -u):$(id -g) \
# homee_docker 