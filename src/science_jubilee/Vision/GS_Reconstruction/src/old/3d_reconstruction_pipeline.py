import os
import sys
from pathlib import Path
import numpy as np
import open3d as o3d
import cv2 
import time

SRC_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = SRC_ROOT.parent


def _windows_to_wsl_path(windows_path: str) -> str:
    path = Path(windows_path).resolve()
    drive_letter = path.drive.rstrip(":").lower()
    return "/mnt/" + drive_letter + path.as_posix()[2:]


for path in (SRC_ROOT, REPO_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import science_jubilee.Vision.GS_Reconstruction.src.old.filter_plants as filter_plants
import science_jubilee.Vision.GS_Reconstruction.src.old.meshing as meshing
import science_jubilee.Vision.GS_Reconstruction.src.old.scale as scale
import science_jubilee.Vision.GS_Reconstruction.src.old.filter_scene as filter_scene
import science_jubilee.Vision.GS_Reconstruction.src.old.scale_by_cameras as scale_by_cameras
from science_jubilee.tools.camera.toolheadcam import ToolheadCam
from science_jubilee.hal.motion_driver import MotionDriver
from science_jubilee.hal.tool_changer import ToolChanger
from science_jubilee.hal.transport.http import HTTPTransport
from science_jubilee.navigation.free_navigation import FreeNavigator

def deck_clear():
    return True 

def main(num_photos=100, dataset_name="Latest_reconstruction", iterations = 7000,camera=None, Show=True):
    """Run the full 3D reconstruction pipeline."""
    if num_photos <= 0:
        raise ValueError("num_photos must be a positive integer")


    dataset_path = (
        REPO_ROOT
        / "src/science_jubilee/Vision/GS_Reconstruction/Datasets"
        / dataset_name
    )
    images_dir = dataset_path / "input"
    output_path = (
        REPO_ROOT
        / "src/science_jubilee/Vision/GS_Reconstruction/Outputs"
        / f"{dataset_name}_results"
    )

    images_dir.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)
        
    
    grid_size = int(np.ceil(np.sqrt(num_photos/5)))
    start_x = 110.0
    start_y = 80.0
    finish_x = 250.0
    finish_y = 200.0
    start_z=280
    finish_z=220
    if grid_size == 1:
        step_x = 0.0
        step_y = 0.0
    else:
        step_x = int((finish_x - start_x) / (grid_size - 1))
        step_y = int((finish_y - start_y) / (grid_size - 1))

    span= np.array([(grid_size-1)*step_x, (grid_size-1)*step_y,start_z-finish_z])
    span= span*10e-3
    print(span)

    step_z=20 
    image_index = 0 
    """
    transport = HTTPTransport(address="10.0.9.6")
    driver = MotionDriver(transport)
    tool_changer = ToolChanger(transport)
    freenav= FreeNavigator(driver, tool_changer)
    transport.deck_clear_provider= deck_clear
    
    if camera is None:
        camera = ToolheadCam(motion=driver, tool_changer=tool_changer,address="10.0.9.55",calib_file=REPO_ROOT/ "src/science_jubilee/calibration/camera_params.yaml")
    

    for level in range(4):
        current_z = start_z - level * step_z
        freenav.move_to(z=current_z)   
        # Outer loop controls X
        for x_index in range(grid_size):
            if image_index >= num_photos:
                break
                
            # Snaking logic: even passes go forward (+Y), odd passes go backward (-Y)
            if x_index % 2 == 0:
                y_indices = range(grid_size)
            else:
                y_indices = reversed(range(grid_size))
                
            # Inner loop controls Y
            for y_index in y_indices:
                if image_index >= num_photos:
                    break
                
                # Calculate absolute positions
                current_x = start_x + (x_index * step_x)
                current_y = start_y + (y_index * step_y)
                
                # Move to position directly
                freenav.move_to(x=current_x, y=current_y)
                time.sleep(2)
                
                img = camera.get_image()
                # Z coordinate also updated to reflect current Z, not hardcoded 320
                image_name = f"img_n{image_index}_x{int(current_x)}_y{int(current_y)}_z{int(current_z)}.jpg"
                cv2.imwrite(str(images_dir / image_name), img)

                image_index += 1
    """
    colmap_wsl_path = REPO_ROOT / "src/science_jubilee/Vision/GS_Reconstruction/src" / "run_colmap.sh"
    print(colmap_wsl_path)
    if not colmap_wsl_path.exists():
        raise FileNotFoundError(f"WSL pipeline script not found: {colmap_wsl_path}")

    output_reconstruction = output_path / "GS_Reconstruction"

    colmap_wsl_path_wsl = _windows_to_wsl_path(str(colmap_wsl_path))
    dataset_path_wsl = _windows_to_wsl_path(str(dataset_path))
    output_reconstruction_wsl = _windows_to_wsl_path(str(output_reconstruction))

    commande = (
        f'start /wait cmd /k "wsl bash {colmap_wsl_path_wsl} '
        f'--dataset {dataset_path_wsl} '
    )

    print("Colmap conversion via WSL...")
    result = os.system(commande)
    if result != 0:
       raise RuntimeError(f"Colmap conversion failed with exit code {result}")

    reconstruction_wsl_path = REPO_ROOT / "src/science_jubilee/Vision/GS_Reconstruction/src" / "run_reconstruction.sh"
    print(reconstruction_wsl_path)
    if not reconstruction_wsl_path.exists():
            raise FileNotFoundError(f"WSL pipeline script not found: {reconstruction_wsl_path}")
    
    filter_scene.main(images_path= dataset_path / "images")
    
    reconstruction_wsl_path_wsl = _windows_to_wsl_path(str(reconstruction_wsl_path))
    commande = (
            f'start /wait cmd /k "wsl bash {reconstruction_wsl_path_wsl} '
            f'--dataset {dataset_path_wsl} '
            f'--output {output_reconstruction_wsl} '
            f'--iterations {iterations}"'
        )
    
    print("Gaussian training via WSL...")
    result = os.system(commande)
    if result != 0:
            raise RuntimeError(f"WSL reconstruction failed with exit code {result}")
    
    output_reconstruction = output_path / "GS_Reconstruction"

    ply_path = output_reconstruction / f"point_cloud/iteration_{iterations}" / "point_cloud.ply"
    if not ply_path.exists():
        raise FileNotFoundError(f"Expected point cloud not found: {ply_path}")

    filtered_ply_path = (
        output_reconstruction / "point_cloud/iteration_35000" / "point_cloud.ply"
    )
    os.makedirs(filtered_ply_path.parent, exist_ok=True)

    filter_plants.filter_gaussians(
        input_ply=str(ply_path),
        output_ply=str(filtered_ply_path),
        bbox_size=10000,
        bbox_center=[0.0, 2, 0.0],
        elongation_threshold=7.0,
        scale_threshold=1,
        std_ratio=3,
        opacity_threshold=0.07,
        nb_neighbors=60,
        white_sat_thresh=0.55,
        white_val_thresh=0.2,
    )

    # Step 3: Scaling by extracting the green Aruco codes and scaling and rotating thanks to them, then it references to the blue cube to scale its z axis
    scaled_ply_path = (output_reconstruction / "point_cloud/iteration_35000" / "point_cloud_scaled.ply")
    #scale.process_and_align(input_ply=str(filtered_ply_path), output_ply=str(scaled_ply_path))
    cameras_json_path=(output_reconstruction /"cameras.json")
    scale_by_cameras.main(input_ply=str(filtered_ply_path), output_ply=str(scaled_ply_path),cameras_json_path=cameras_json_path,cameras_span=None)
    # Step 4: Meshing
    mesh_path = output_path / "mesh.obj"
    mesh_path.parent.mkdir(parents=True, exist_ok=True)
    meshing.create_mesh_with_alpha_shape(
        input_ply=scaled_ply_path, output_obj=mesh_path, alpha=0.0038, decimate_ratio=0.8
    )

    if Show:
        Viewer_path = (
            REPO_ROOT / "src/science_jubilee/Vision/GS_Reconstruction/Viewer/bin"
        )
        # Gaussian Viewer
        os.system(
            f"cd {Viewer_path} && SIBR_gaussianViewer_app.exe -m {output_reconstruction }"
        )
        # Display the mesh
        mesh = o3d.io.read_triangle_mesh(str(mesh_path))
        o3d.visualization.draw_geometries([mesh], mesh_show_back_face=True)


if __name__ == "__main__":
    main(num_photos=100, dataset_name="Virtual_montserra_3",iterations=7000, Show=True)