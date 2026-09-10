import logging
import random
from pathlib import Path

import cv2
import numpy as np
import math
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
logger = logging.getLogger(__name__)

# ==========================================================
# CONFIGURATION
# ==========================================================
REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DATASET_DIR = REPO_ROOT / "Raw_images"
SEG_DATASET_DIR = REPO_ROOT / "Filtered_images"

# Création du dossier s'il n'existe pas
SEG_DATASET_DIR.mkdir(parents=True, exist_ok=True)

# =======================================
# Détection du flotteur
# =======================================
def get_float_points(
    img,
    min_area_px=300,
    min_radius_px=20,
    max_radius_px=150,
    min_circularity=0.40,
) -> tuple[np.ndarray, tuple[int, int], int]:
    # 1. Espace HSV avec seuillage
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_teal = np.array([30, 80, 30], dtype=np.uint8)
    upper_teal = np.array([105, 120, 100], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_teal, upper_teal)

    # 2. Nettoyage morphologique
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 3. Extraction des contours
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    valid_candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area_px:
            continue

        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        hull_perimeter = cv2.arcLength(hull, True)

        if hull_perimeter == 0:
            continue

        circularity = 4 * np.pi * hull_area / (hull_perimeter**2)
        if circularity < min_circularity:
            continue

        (x, y), radius = cv2.minEnclosingCircle(hull)

        if min_radius_px <= radius <= max_radius_px:
            valid_candidates.append(
                {"center": (int(x), int(y)), "radius": int(radius), "circularity": circularity}
            )

    if not valid_candidates:
        raise ValueError("Aucun cercle conforme détecté.")

    # 4. Sélection du cercle le plus circulaire (meilleur contour)
    target = max(valid_candidates, key=lambda item: item["circularity"])
    cx, cy = target["center"]
    r_circle = target["radius"]

    # 4 points cardinaux stricts
    image_points = np.array(
        [
            [cx - r_circle, cy],
            [cx, cy - r_circle],
            [cx + r_circle, cy],
            [cx, cy + r_circle],
        ],
        dtype=np.float32,
    )

    # On retourne les points 3D, MAIS AUSSI le centre et le rayon exacts
    return image_points, (cx, cy), r_circle

# =======================================
# Estimation de la profondeur PnP
# =======================================
def estimate_float_pose(camera, image_points, radius_mm):
    object_points = np.array(
        [[-radius_mm, 0, 0], [0, -radius_mm, 0], [radius_mm, 0, 0], [0, radius_mm, 0]],
        dtype=np.float32,
    )

    ok, rvecs, tvecs, errors = cv2.solvePnPGeneric(
        object_points, image_points, camera.K, camera.dist, flags=cv2.SOLVEPNP_IPPE
    )

    if not ok:
        raise RuntimeError("solvePnPGeneric a échoué.")

    best = None
    bestErr = np.inf

    for rvec, tvec, err in zip(rvecs, tvecs, errors):
        R, _ = cv2.Rodrigues(rvec)
        if tvec[2][0] <= 0:
            continue
        if err < bestErr:
            bestErr = err
            best = (R, tvec.reshape(3))

    if best is None:
        raise RuntimeError("Aucune solution PnP valide vers l'avant (Z > 0).")

    return best[1]

# ======================================================
# Conversion pixel -> repère caméra (3D)
# ======================================================
def get_lens_position(camera, lens_pixel, water_level):
    u, v = lens_pixel
    z = float(water_level)

    dist_np = np.array(camera.dist, dtype=np.float32)
    point_2d = np.array([[[u, v]]], dtype=np.float32)

    undistorted_pt = cv2.undistortPoints(point_2d, camera.K, dist_np)

    x_norm = undistorted_pt[0, 0, 0]
    y_norm = undistorted_pt[0, 0, 1]

    x = x_norm * z
    y = y_norm * z

    return np.array([x, y, z], dtype=np.float32)

# ======================================================
# Pipeline Principale
# ======================================================
def main(img, camera, float_radius_mm=25.0):
    output_img = img.copy()
    checkpoints_3d = np.empty((0, 3), dtype=np.float32)
    water_level = 0.0

    # 1. Traitement du flotteur
    try:
        # On récupère les points ET le centre/rayon
        float_img_points, float_center_2d, float_radius_px = get_float_points(img)
        
        # Dessiner les 4 points cardinaux (cyan)
        for pt in float_img_points:
            cv2.circle(output_img, (int(pt[0]), int(pt[1])), 4, (255, 255, 0), -1)

        # Dessiner le centre réel corrigé (rouge)
        cv2.circle(output_img, float_center_2d, 5, (0, 0, 255), -1)
        
        cv2.putText(
            output_img,
            "Flotteur",
            (float_center_2d[0] + 10, float_center_2d[1]),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2,
        )

        tvec = estimate_float_pose(camera, float_img_points, float_radius_mm)
        float_center_3d = tvec
        water_level = tvec[2] 

    except Exception as e:
        logger.error(f"Erreur flotteur : {e}")
        return None, None, checkpoints_3d

    text = f"Profondeur Z estimee: {water_level:.1f} mm"
    cv2.putText(
        output_img, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
    )

    filename = SEG_DATASET_DIR / "latest.png"
    
    # Attention: On ne convertit RGB2BGR que si l'image vient d'une source RGB (comme matplotlib). 
    # Si tu utilises cv2.imread(), commente la ligne ci-dessous :
    output_img = cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR) 
    
    cv2.imwrite(str(filename), output_img)
    cv2.destroyAllWindows()
    logger.info(f"Image de controle sauvegardee sous : {filename}")

    return float_center_3d, water_level,