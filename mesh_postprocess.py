import open3d as o3d
import os
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-m', '--mesh', type=str, required=True)
    parser.add_argument('--iteration', type=str, default=None)
    parser.add_argument('-v', '--view', action='store_true', default=False)
    parser.add_argument('-n', '--normal', action='store_true', default=False)
    parser.add_argument('-s', '--simplfied', action='store_true', default=False)
    args = parser.parse_args()
    
    mesh_path = os.path.join(args.mesh, "mesh", "iteration_" + args.iteration, "mesh.ply")
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    print(f'Mesh has {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles')
    
    if not args.simplfied:
        print("Mesh smoothing")
        mesh = mesh.filter_smooth_laplacian(20)
        print("Mesh simplification")
        mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=int(1e6))
        mesh = mesh.filter_smooth_laplacian(3)
        print(f'Mesh has {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles')
        new_name = "." + mesh_path.split('.')[-2] + 'simplified.obj'
        print(f'Saving simplified mesh to {new_name}')
        o3d.io.write_triangle_mesh(new_name, mesh)
    
    if args.normal:
        mesh.compute_vertex_normals()
        
    if args.view:
        o3d.visualization.draw_geometries([mesh])