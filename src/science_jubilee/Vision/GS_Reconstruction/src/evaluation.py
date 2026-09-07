import open3d as o3d
import numpy as np
import argparse
import sys

def load_and_prepare_point_clouds(source_path, target_path, num_points=100000):
    def load_model(path):
        mesh = o3d.io.read_triangle_mesh(path)
        if len(mesh.triangles) > 0:
            return mesh.sample_points_uniformly(number_of_points=num_points)
        else:
            pcd = o3d.io.read_point_cloud(path)
            pts = np.asarray(pcd.points)
            if len(pts) > num_points:
                indices = np.random.choice(len(pts), num_points, replace=False)
                pcd = pcd.select_by_index(indices)
            return pcd
            
    source_pcd = load_model(source_path)
    target_pcd = load_model(target_path)
    
    # Calcul des normales requis pour l'ICP Point-à-Plan
    source_pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamKNN(knn=30))
    target_pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamKNN(knn=30))
    
    return source_pcd, target_pcd

def get_object_size(pcd):
    """Mesure la taille de l'objet (diagonale) en ignorant les 2% de points extrêmes."""
    points = np.asarray(pcd.points)
    p_min = np.percentile(points, 2, axis=0)
    p_max = np.percentile(points, 98, axis=0)
    return np.linalg.norm(p_max - p_min)

def translation_initialization(source, target):
    """Superpose uniquement les centres de masse, sans toucher à la rotation ni à l'échelle."""
    center_S = np.mean(np.asarray(source.points), axis=0)
    center_T = np.mean(np.asarray(target.points), axis=0)
    
    trans = np.eye(4)
    trans[:3, 3] = center_S - center_T
    return trans

def multiscale_icp_point_to_plane(source, target, init_trans, max_iter=200):
    """ICP rigide (Rotation + Translation uniquement)."""
    object_size = get_object_size(source)
    
    # Rayons de recherche décroissants : 10%, 5% puis 2% de la taille de l'objet
    search_radii = [object_size * 0.1, object_size * 0.05, object_size * 0.02]
    current_trans = init_trans
    
    for radius in search_radii:
        reg_p2l = o3d.pipelines.registration.registration_icp(
            target, source, radius, current_trans,
            o3d.pipelines.registration.TransformationEstimationPointToPlane(),
            o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iter)
        )
        current_trans = reg_p2l.transformation
        
    return reg_p2l

def compute_chamfer_distance(source, target):
    """Évaluation mathématique : Distance de Chamfer."""
    dists_t_to_s = np.asarray(target.compute_point_cloud_distance(source))
    dists_s_to_t = np.asarray(source.compute_point_cloud_distance(target))
    chamfer = 0.5 * (np.mean(dists_t_to_s**2) + np.mean(dists_s_to_t**2))
    return chamfer

def evaluate_models(source_obj_path, target_obj_path):
    print("1. Chargement des modèles...")
    source_pcd, target_pcd = load_and_prepare_point_clouds(source_obj_path, target_obj_path)
    
    print("2. Initialisation : Translation des centres...")
    init_transformation = translation_initialization(source_pcd, target_pcd)
    
    print("3. Alignement : ICP Point-à-Plan...")
    final_icp = multiscale_icp_point_to_plane(source_pcd, target_pcd, init_transformation)
    
    # Application de la matrice (Rotation + Translation) au nuage cible
    target_pcd.transform(final_icp.transformation)
    
    # Calcul des échelles pour référence
    size_gt = get_object_size(source_pcd)
    size_nerf = get_object_size(target_pcd)
    
    print("\n--- RÉSULTATS ---")
    print(f"Échelle estimée (Ground Truth)      : {size_gt:.4f}")
    print(f"Échelle estimée (Reconstruction)    : {size_nerf:.4f}")
    print("-" * 30)
    print(f"Fitness (taux de points superposés) : {final_icp.fitness:.4f}")
    print(f"Inlier RMSE                         : {final_icp.inlier_rmse:.6f}")
    
    chamfer = compute_chamfer_distance(source_pcd, target_pcd)
    print(f"Distance de Chamfer                 : {chamfer:.6f}")

    return source_pcd, target_pcd

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alignement Translation + ICP")
    parser.add_argument("source", type=str, help="Fichier Ground Truth (.obj)")
    parser.add_argument("target", type=str, help="Fichier Reconstruction NeRFs (.obj)")
    parser.add_argument("--visualize", action="store_true", help="Affiche le résultat en 3D")

    args = parser.parse_args()

    try:
        source_pcd, target_pcd = evaluate_models(args.source, args.target)

        if args.visualize:
            print("\nOuverture de la fenêtre 3D... (Fermez la fenêtre pour quitter)")
            target_pcd.paint_uniform_color([0, 0, 1])        # Bleu (GT)
            source_pcd.paint_uniform_color([1, 0.65, 0])     # Orange (NeRF aligné)
            
            o3d.visualization.draw_geometries(
                [source_pcd, target_pcd],
                window_name="Ground Truth (Bleu) vs GS Aligné (Orange)",
                width=1024, height=768
            )
            
    except Exception as e:
        print(f"\n[Erreur] : {e}", file=sys.stderr)
        sys.exit(1)