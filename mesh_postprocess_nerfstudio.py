import open3d as o3d
import os
from argparse import ArgumentParser
from arguments import ModelParams, PipelineParams
import sys
import torch
from gaussian_renderer import integrate
from gaussian_renderer import GaussianModel
from nerfstudio_utils import Scene
import numpy as np
import open3d as o3d
from tqdm import tqdm

@torch.no_grad()
def evaluate_alpha(points, views, gaussians, pipeline, background, kernel_size, return_color=True):
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

@torch.no_grad()
def mesh_postprocess(dataset, pipeline, mesh_path):
    if dataset.splat_file != "":
        splat_file = dataset.splat_file
        dataset.model_path = os.path.dirname(splat_file)
    else:
        splat_file = os.path.join(dataset.model_path, "splat.ply") 
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    gaussians = GaussianModel(dataset.sh_degree)
    scene = Scene(dataset, shuffle=False)
    gaussians.load_ply(splat_file)
    bg_color = [1,1,1] if dataset.white_background else [0, 0, 0]
    background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")
    kernel_size = dataset.kernel_size     
    cams = scene.getTrainCameras()
    
    triangles_num = len(mesh.triangles)
    print(f'Before: {len(mesh.vertices)} vertices and {triangles_num} triangles')
    print("Mesh smoothing")
    for i in tqdm(range(20)):
        mesh = mesh.filter_smooth_laplacian(1)
    if triangles_num > 1e7:
        print("Mesh too large, skip simplfication")
    else:
        print("Mesh simplfication")
        target = int(triangles_num / 2)
        mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=int(target))
        mesh = mesh.filter_smooth_laplacian(3)
    
    print(f'After: {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles')
    
    vertices = np.asarray(mesh.vertices)
    vertices = torch.from_numpy(vertices).float().cuda()
    
    print("Re-evaulating color")
    _, color = evaluate_alpha(vertices, cams, gaussians, pipeline, background, kernel_size, return_color=True)
    
    color = color.cpu().numpy()
    mesh.vertex_colors = o3d.utility.Vector3dVector(color)
        
    mesh_name = os.path.basename(mesh_path)
    mesh_name = mesh_name.replace(".ply", "_postprocess.ply")
    export_name = os.path.join(dataset.model_path, mesh_name)
    o3d.io.write_triangle_mesh(export_name, mesh)

if __name__ == '__main__':
    parser = ArgumentParser(description="Testing script parameters")
    model = ModelParams(parser)
    pipeline = PipelineParams(parser)
    parser.add_argument('--mesh', type=str)
    args = parser.parse_args(sys.argv[1:])
    
    mesh_postprocess(model.extract(args), pipeline.extract(args), args.mesh)