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

- [ ] **1. Define the voxel grid.** Use bounds x = [-2.5, 2.5] m, y = [-3, 3]
  m, and z = [0, 2.5] m. Choose a resolution that fits memory (an optional
  tighter initial volume is allowed). Record the voxel size and grid dimensions.

- [ ] **2. Compute the visual hull.** Initialize voxels as empty. Project each
  voxel center into all eight views and mark it occupied only if its projection
  lies inside every silhouette. Report the occupied-voxel count and its fraction
  of the complete grid.

- [ ] **3. Identify surface voxels.** Mark occupied voxels that have at least
  one empty neighbor. Report the surface-voxel count and its fraction of the
  complete grid.

- [ ] **4. Generate output geometry.** For every face of a surface voxel that
  borders empty space, add that face center to the point cloud. Report the point
  count, compare it to the surface-voxel count, and explain why they differ.

- [ ] **5. Assign false colors.** Find the min/max X, Y, and Z values of the
  reconstructed points. Map X to red, Y to green, and Z to blue using the
  specified 0-255 normalized-coordinate formula. Handle any zero-size range
  safely.

- [ ] **6. Export the false-color PLY.** Write an ASCII PLY whose `element
  vertex` count matches the output points; each vertex must contain x y z and
  unsigned-char r g b values. Verify it opens in MeshLab.

- [ ] **7. Assign true colors with visibility.** For each surface output point,
  collect RGB samples from cameras with an unoccluded view of the associated
  surface voxel, then assign the per-channel median. Implement and document the
  visibility/occlusion test (the outward-vector method is one suggested option).

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
