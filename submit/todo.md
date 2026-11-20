# CS 532 Homework 3 - Submission Checklist

This folder is the submission source-code directory. It currently contains
`CodeSnippet.m`, the provided MATLAB helper for loading the eight projection
matrices/camera centers and inspecting epipolar geometry. Keep any new source
files, generated final PLY files, report, and screenshots required for the
submission here.

## Input material (kept outside this folder)

- `../cs532_HW03/cam00_...png` through `cam07_...png`: eight color views.
- `../cs532_HW03/silh_cam00_...pbm` through `silh_cam07_...pbm`: silhouettes.
- `../cs532_HW03/calibration/cam00.xml` through `cam07.xml`: 3x4 projection
  matrices.
- `../cs532_HW03/coloredPtCloud.ply`: ASCII PLY formatting example.
- `../cs532_HW03/cs532_S27_HW3-1.pdf`: assignment specification.

## Required work

- [x] **1. Define the voxel grid.** Implemented in
  `reconstruct_visual_hull.py` with required bounds x = [-2.5, 2.5] m,
  y = [-3, 3] m, and z = [0, 2.5] m. The selected isotropic voxel size is
  0.05 m, giving a 100 x 120 x 50 grid (600,000 voxels). The logical occupancy
  mask requires approximately 0.57 MiB; centers are stored as three 1D vectors
  to avoid allocating a full 3D coordinate array.

  **Writeup must include:** the bounded ranges, chosen discretization or voxel
  size, total number of voxels, memory consideration, and how the grid estimates
  occupied versus free space.

- [x] **2. Compute the visual hull.** `reconstruct_visual_hull.py` loads the
  eight calibration matrices and P4 silhouettes, projects every voxel center,
  and keeps only voxels supported by all eight views. With the 100 x 120 x 50
  grid, the visual hull contains 74,869 occupied voxels, or 0.124782 of the
  600,000-voxel grid.

  **Writeup must include:** that all voxels begin EMPTY, voxel centers are
  projected into all images, only projections inside ALL silhouettes become
  OCCUPIED, the total visual-hull voxel count, and the relative portion of all
  voxels in the visual hull.

- [x] **3. Identify surface voxels.** `reconstruct_visual_hull.py` uses the
  required six axis-aligned neighbors and treats an out-of-grid neighbor as
  empty. It found 26,311 surface voxels, or 0.043852 of the full 600,000-voxel
  grid.

  **Writeup must include:** the definition of a surface voxel, the total
  surface-voxel count, and the relative portion of all voxels that are surface
  voxels.

- [x] **4. Generate output geometry.** `reconstruct_visual_hull.py` creates a
  face-center point for every exposed face and stores its outward normal/source
  voxel for later true-color visibility checks. It generated 49,292 points from
  26,311 surface voxels. The counts differ because one surface voxel can expose
  more than one face.

  **Writeup must include:** the number of 3D points in the model, a comparison
  with the number of surface voxels, whether the counts are equal, and why they
  differ. Explain that one surface voxel can contribute multiple exposed faces.

- [x] **5. Assign false colors.** `reconstruct_visual_hull.py` maps the output
  point X, Y, and Z ranges independently to unsigned-byte red, green, and blue
  values using the specified normalized-coordinate formula. A zero-size range
  uses the safe constant value 128.

  **Writeup must include:** the reconstructed-point bounding-box minima and
  maxima (`X_min`, `X_max`, `Y_min`, `Y_max`, `Z_min`, `Z_max`) and the required
  red/X, green/Y, and blue/Z formulas.

- [x] **6. Export the false-color PLY.** Wrote
  `visual_hull_false_color.ply` as ASCII PLY with 49,292 vertices and six
  fields per row: x y z r g b. Header and row-count verification passed.
  MeshLab visual inspection remains to be performed locally.

  **Writeup must include:** that the file is ASCII PLY, that the
  `element vertex` count equals the number of vertices/data rows, that each
  vertex contains three floating-point coordinates and three unsigned RGB
  values, and a MeshLab model image or screenshot.

- [x] **7. Assign true colors with visibility.** Implemented as
  `assign_true_colors(...)` in `reconstruct_visual_hull.py`. It accepts only
  foreground projections whose outward point-to-camera ray is unoccluded by a
  3D DDA voxel traversal, then uses the per-channel median; gray `(128,128,128)`
  is the documented no-visible-camera fallback. Full-scene execution completed
  for all 49,292 output points; 31,517 points used the neutral-gray fallback.
  Visual inspection of the resulting model remains to be completed.

  **Writeup must include:** per-channel median RGB fusion, how surface points
  are projected into the images, how non-occluded cameras are selected, the
  visibility method, and the fallback behavior when no camera can see a point.

- [x] **8. Export the true-color PLY.** Export code has been added to
  `reconstruct_visual_hull.py`, and `visual_hull_true_color.ply` was generated
  with 49,292 vertices using `--true-color`. Visual inspection in MeshLab
  remains to be completed.

  **Writeup must include:** the final true-color PLY filename, its correct
  vertex count and ASCII structure, and a screenshot/image of the true-color
  model.

## Bonus

- [x] **9. Add the two-light shadow and relighting bonus.** The voxel-based
  implementation and first output images are complete; visual inspection and
  report integration remain.

  Suggested implementation plan:

  - [x] Choose and document two point-light locations in world coordinates,
    for example `L1 = (-4.0, -4.0, 5.0)` and `L2 = (4.0, 2.0, 4.0)` meters.
  - [x] Use the reconstructed occupied voxel grid as the shadow-casting shape.
  - [x] For each surface point and each light, trace a ray
    from the light toward the point with the existing 3D DDA traversal. Mark
    the point as shadowed when another occupied voxel blocks the ray.
  - [x] For each camera image, project the shadowed 3D points into the image
    and darken valid foreground pixels. Avoid changing background pixels.
  - [x] Reproject points visible to at least one light and blend them toward a
    lighter color.
  - [x] Draw or annotate the projected light locations in the output images
    when their 3D positions project inside the image bounds.
  - [x] Save one clearly labeled composite per camera in
    `submit/two_light_bonus/` as PPM images.
  - [ ] Explain the light positions, ray-occlusion test, projection/blending
    rule, and limitations in the report.

  **Bonus writeup must include:** the two chosen point-light locations, how the
  3D shadows were determined from the estimated shape, how shadowed volume
  parts were reprojected as darker pixels, how regions between a light and the
  shape were reprojected as lighter pixels, the attained images with light
  locations shown, and an explanation of the complete method.

## Submission

- [ ] **10. Prepare the mandatory Canvas submission.** Submit one ZIP file
  containing the following required items:

  - [ ] One PDF report containing all authored source code.
  - [ ] A brief explanation of what was done and how the reconstruction works.
  - [ ] Images and screenshots of the reconstructed model, including false-
    color and true-color results. Include MeshLab screenshots when available.
  - [ ] The final true-color ASCII PLY model.
  - [ ] If the false-color PLY is included, label it clearly as an intermediate
    result rather than the final model.

### Required PDF report contents

- [ ] Identify the voxel bounds, voxel dimensions, grid resolution, total
  voxel count, and memory representation.
- [ ] Explain how voxel centers are projected into all eight calibrated views
  and how the silhouette intersection determines the visual hull.
- [ ] Report the visual-hull voxel count and fraction of the full grid.
- [ ] Explain the six-neighbor surface-voxel test, including how grid-boundary
  neighbors are handled, and report the surface count and fraction.
- [ ] Explain why the number of output face-center points differs from the
  number of surface voxels.
- [ ] Describe the false-color formula using normalized X, Y, and Z ranges.
- [ ] Describe the ASCII PLY structure and verify the vertex count.
- [ ] Describe true-color fusion: projection, foreground testing, visibility
  checking, per-channel median fusion, and the no-visible-camera fallback.
- [ ] Include the measured reconstruction results: 74,869 occupied voxels,
  26,311 surface voxels, and 49,292 output points.
- [ ] Include screenshots or rendered images of the final model and briefly
  discuss visible quality, gray fallback regions, and limitations.
- [ ] If completing Bonus Step 9, include the light positions, shadow-ray
  method, image reprojection/blending method, output images, and limitations.
