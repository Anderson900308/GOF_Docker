import torch
from nerfstudio_utils import Scene
import os
from os import makedirs
from gaussian_renderer import integrate
import random
from tqdm import tqdm
from argparse import ArgumentParser
from arguments import ModelParams, PipelineParams
from gaussian_renderer import GaussianModel
import numpy as np
import trimesh
from tetranerf.utils.extension import cpp
from utils.tetmesh import marching_tetrahedra
import sys

@torch.no_grad()
def evaluate_alpha(points, views, gaussians, pipeline, background, kernel_size, return_color=False):
    final_alpha = torch.ones((points.shape[0]), dtype=torch.float32, device="cuda")
    final_color = torch.ones((points.shape[0], 3), dtype=torch.float32, device="cuda")
    
    with torch.no_grad():
        for _, view in enumerate(tqdm(views, desc="Rendering progress")):
            ret = integrate(points, view, gaussians, pipeline, background, kernel_size=kernel_size)
            alpha_integrated = ret["alpha_integrated"]
            if return_color:
                color_integrated = ret["color_integrated"]
                final_color = torch.where((alpha_integrated < final_alpha).reshape(-1, 1), color_integrated, final_color)
            final_alpha = torch.min(final_alpha, alpha_integrated)
        alpha = 1 - final_alpha
        
    if return_color:
        final_color = torch.clamp(final_color, 0, 1)
        return alpha, final_color
    return alpha

# marching_tetrahedra_with_binary_search(dataset.output_path, cams, gaussians, pipeline, background, kernel_size, texture_mesh)
@torch.no_grad()
def marching_tetrahedra_with_binary_search(model_path, views, gaussians, pipeline, background, kernel_size, texture_mesh : bool, splat_file_name="splat.ply", sdf_thres = 0.5):
    print()
    render_path = model_path
    makedirs(render_path, exist_ok=True)
    points, points_scale = gaussians.get_tetra_points()
    print("create cells and save")
    cells = cpp.triangulate(points)
    torch.save(cells, os.path.join(render_path, "cells.pt"))
    
    # evaluate alpha
    alpha = evaluate_alpha(points, views, gaussians, pipeline, background, kernel_size)

    vertices = points.cuda()[None]
    tets = cells.cuda().long()
    def alpha_to_sdf(alpha):
        sdf = alpha - sdf_thres
        sdf = sdf[None]
        return sdf
    
    sdf = alpha_to_sdf(alpha)
    
    torch.cuda.empty_cache()
    verts_list, scale_list, faces_list, _ = marching_tetrahedra(vertices, tets, sdf, points_scale[None])
    torch.cuda.empty_cache()
    
    end_points, end_sdf = verts_list[0]
    end_scales = scale_list[0]
    
    faces=faces_list[0].cpu().numpy()
    points = (end_points[:, 0, :] + end_points[:, 1, :]) / 2.
        
    left_points = end_points[:, 0, :]
    right_points = end_points[:, 1, :]
    left_sdf = end_sdf[:, 0, :]
    right_sdf = end_sdf[:, 1, :]
    left_scale = end_scales[:, 0, 0]
    right_scale = end_scales[:, 1, 0]
    distance = torch.norm(left_points - right_points, dim=-1)
    scale = left_scale + right_scale
    
    n_binary_steps = 8
    for step in range(n_binary_steps):
        print("binary search in step {}".format(step))
        mid_points = (left_points + right_points) / 2
        alpha = evaluate_alpha(mid_points, views, gaussians, pipeline, background, kernel_size)
        mid_sdf = alpha_to_sdf(alpha).squeeze().unsqueeze(-1)
        
        ind_low = ((mid_sdf < 0) & (left_sdf < 0)) | ((mid_sdf > 0) & (left_sdf > 0))

        left_sdf[ind_low] = mid_sdf[ind_low]
        right_sdf[~ind_low] = mid_sdf[~ind_low]
        left_points[ind_low.flatten()] = mid_points[ind_low.flatten()]
        right_points[~ind_low.flatten()] = mid_points[~ind_low.flatten()]
    
        points = (left_points + right_points) / 2
        if step not in [7]:
            continue
        
        if texture_mesh:
            _, color = evaluate_alpha(points, views, gaussians, pipeline, background, kernel_size, return_color=True)
            vertex_colors=(color.cpu().numpy() * 255).astype(np.uint8)
        else:
            vertex_colors=None
        mesh = trimesh.Trimesh(vertices=points.cpu().numpy(), faces=faces, vertex_colors=vertex_colors, process=False)
        
        splat_file_name = splat_file_name.split(".")[0]
        export_name = splat_file_name + f"_mesh_thres_{sdf_thres}.ply"
        mesh.export(os.path.join(render_path, export_name))

def extract_mesh(dataset : ModelParams, pipeline : PipelineParams, texture_mesh : bool):
    with torch.no_grad():
        if dataset.splat_file != "":
            splat_file = dataset.splat_file
            dataset.model_path = os.path.dirname(splat_file) # type: ignore
        else:
            splat_file = os.path.join(dataset.model_path, "splat.ply") # type: ignore
        splat_file_name = os.path.basename(splat_file)
        gaussians = GaussianModel(dataset.sh_degree)
        scene = Scene(dataset, shuffle=False)
        gaussians.load_ply(splat_file)
        
        bg_color = [1,1,1] if dataset.white_background else [0, 0, 0] # type: ignore
        background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")
        kernel_size = dataset.kernel_size # type: ignore
        
        cams = scene.getTrainCameras()
        thres_list = [0.3, 0.5, 0.7, 0.9, 0.95]
        for thres in thres_list:
            print("Extracting mesh with threshold {}".format(thres))
            marching_tetrahedra_with_binary_search(dataset.model_path, cams, gaussians, pipeline, background, kernel_size, texture_mesh, splat_file_name, thres) # type: ignore
            

if __name__ == "__main__":
    parser = ArgumentParser(description="Testing script parameters")
    model = ModelParams(parser)
    pipeline = PipelineParams(parser)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--texture_mesh", action="store_true")
    args = parser.parse_args(sys.argv[1:])
    
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.set_device(torch.device("cuda:0"))
    
    extract_mesh(model.extract(args), pipeline.extract(args), args.texture_mesh) # type: ignore