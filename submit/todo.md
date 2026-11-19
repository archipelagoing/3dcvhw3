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

- [x] **2. Compute the visual hull.** `reconstruct_visual_hull.py` loads the
  eight calibration matrices and P4 silhouettes, projects every voxel center,
  and keeps only voxels supported by all eight views. With the 100 x 120 x 50
  grid, the visual hull contains 74,869 occupied voxels, or 0.124782 of the
  600,000-voxel grid.

- [x] **3. Identify surface voxels.** `reconstruct_visual_hull.py` uses the
  required six axis-aligned neighbors and treats an out-of-grid neighbor as
  empty. It found 26,311 surface voxels, or 0.043852 of the full 600,000-voxel
  grid.

- [x] **4. Generate output geometry.** `reconstruct_visual_hull.py` creates a
  face-center point for every exposed face and stores its outward normal/source
  voxel for later true-color visibility checks. It generated 49,292 points from
  26,311 surface voxels. The counts differ because one surface voxel can expose
  more than one face.

- [x] **5. Assign false colors.** `reconstruct_visual_hull.py` maps the output
  point X, Y, and Z ranges independently to unsigned-byte red, green, and blue
  values using the specified normalized-coordinate formula. A zero-size range
  uses the safe constant value 128.

- [x] **6. Export the false-color PLY.** Wrote
  `visual_hull_false_color.ply` as ASCII PLY with 49,292 vertices and six
  fields per row: x y z r g b. Header and row-count verification passed.
  MeshLab visual inspection remains to be performed locally.

- [ ] **7. Assign true colors with visibility.** Implemented as
  `assign_true_colors(...)` in `reconstruct_visual_hull.py`. It accepts only
  foreground projections whose outward point-to-camera ray is unoccluded by a
  3D DDA voxel traversal, then uses the per-channel median; gray `(128,128,128)`
  is the documented no-visible-camera fallback. Full-scene execution and visual
  validation remain to be completed before this item is checked.

- [ ] **8. Export the true-color PLY.** Write and inspect the final ASCII PLY
  using the true-color values.

## Submission package

- [ ] Add all authored source code and a short explanation of the approach.
- [ ] Include images/screenshots of the resulting model.
- [ ] Include the final true-color PLY model (and clearly label the false-color
  PLY if it is included as an intermediate result).
- [ ] Place the required items in the format requested by Canvas: a zip file
  containing one PDF with the source code, explanations, and screenshots, plus
  the final PLY model.

## Optional bonus

- [ ] Add two point lights, estimate 3D shadows from the reconstructed shape,
  reproject darker shadow regions and lighter light-to-shape regions into every
  input image, show the light locations, and explain the method in the report.
