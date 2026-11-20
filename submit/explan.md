# CS 532 Homework 3: Voxel-Based Multi-View Reconstruction

## Purpose and implementation status

This document describes the Python algorithm used to reconstruct the dancer
from eight calibrated RGB images and their binary silhouettes. It is written as
the implementation plan and report narrative for the submission. The grid and
visual-hull results below were measured by the current program; later
surface/color/PLY results must be filled in after those steps are implemented
and checked in MeshLab.

The input set contains:

- eight color images `cam00` through `cam07`;
- eight binary silhouettes `silh_cam00` through `silh_cam07`;
- eight calibrated (3\times4) projection matrices (P_i).

The output is a point-cloud approximation of the dancer's **visual hull**:

1. a false-color PLY that colors geometry by world position; and
2. a true-color PLY that fuses only unoccluded RGB observations.

The current implementation completes Steps 1–8. At the selected 5 cm
resolution, it produces 74,869 occupied voxels, 26,311 surface voxels, and
49,292 exposed face-center points. It writes both
`visual_hull_false_color.ply` and `visual_hull_true_color.ply` as ASCII PLY
files with 49,292 vertices each. The true-color run used camera samples for
17,775 points and the neutral-gray fallback for 31,517 points; visual MeshLab
inspection remains part of final validation.

## 1. Camera model and coordinate conventions

A world point is represented in homogeneous coordinates as

\[
\tilde X=[X,Y,Z,1]^\top.
\]

For camera (i), its calibrated projection matrix maps world coordinates to
homogeneous pixel coordinates:

\[
\tilde x_i=
\begin{bmatrix}\tilde u_i\\\tilde v_i\\\tilde w_i\end{bmatrix}
=P_i\tilde X.
\]

The ordinary pixel coordinate is obtained by perspective division:

\[
u_i=\frac{\tilde u_i}{\tilde w_i},\qquad
v_i=\frac{\tilde v_i}{\tilde w_i}.
\]

A projection is valid only if (	ilde w_i>0) and the rounded or interpolated
pixel lies inside the corresponding image. This check prevents points behind a
camera or outside its image from being treated as silhouette evidence.

## 2. Define the voxel grid

The reconstruction volume is bounded by

\[
x\in[-2.5,2.5],\qquad y\in[-3,3],\qquad z\in[0,2.5]\ \text{meters}.
\]

I selected an isotropic (0.05\,\mathrm m) voxel size, giving

\[
(N_x,N_y,N_z)=(100,120,50),\qquad N_xN_yN_z=600{,}000.
\]

The voxel dimensions are

\[
\Delta x=\frac{5}{N_x},\qquad
\Delta y=\frac{6}{N_y},\qquad
\Delta z=\frac{2.5}{N_z}.
\]

For index ((a,b,c)), the voxel center is

\[
c_{a,b,c}=
\begin{bmatrix}
-2.5+(a+0.5)\Delta x\\
-3+(b+0.5)\Delta y\\
0+(c+0.5)\Delta z
\end{bmatrix}.
\]

The implementation stores a Boolean array `occupied[Nx, Ny, Nz]`. A moderate
resolution should be used during debugging, then increased only after camera
projection and image-coordinate indexing have been validated. The grid contains

\[
N=N_xN_yN_z
\]

candidate voxels, so the silhouette stage requires roughly (8N) projections.

### Pseudocode: initialize grid

```text
choose Nx, Ny, Nz
dx = 5.0 / Nx; dy = 6.0 / Ny; dz = 2.5 / Nz
occupied = false[Nx, Ny, Nz]

for ix = 0 .. Nx-1
  for iy = 0 .. Ny-1
    for iz = 0 .. Nz-1
      center[ix,iy,iz] = [-2.5+(ix+0.5)*dx,
                          -3.0+(iy+0.5)*dy,
                           0.0+(iz+0.5)*dz]
```

## 3. Reconstruct the visual hull from silhouettes

Each silhouette constrains the object to a generalized cone in world space. A
voxel is occupied only if its center projects onto foreground in **every** valid
camera:

\[
\operatorname{occupied}(v)=
\bigwedge_{i=1}^{8}
\left[
\tilde w_i>0\ \land\ (u_i,v_i)\in\Omega_i\ \land\ S_i(u_i,v_i)=1
\right].
\]

Equivalently, the result is the discrete approximation of

\[
\mathcal V=\bigcap_{i=1}^{8}C_i,
\]

where (C_i) is camera (i)'s silhouette cone. The visual hull contains the
real object but may additionally contain silhouette-consistent empty space:

\[
\mathcal O_{\mathrm{true}}\subseteq\mathcal V.
\]

Therefore the method cannot recover an inward concavity that does not alter any
silhouette.

### Pseudocode: visual hull

```text
for each voxel v with center c
  keep = true
  for i = 1 .. 8
    [ut, vt, wt] = P[i] * [c.x, c.y, c.z, 1]^T
    if wt <= 0
      keep = false; break
    end
    u = ut / wt; v = vt / wt
    if (u,v) is outside silhouette[i] OR silhouette[i](u,v) is background
      keep = false; break
    end
  end
  occupied[v] = keep
end

visualHullCount = count(occupied)
visualHullFraction = visualHullCount / (Nx*Ny*Nz)
```

**Record after execution:**

\[
N_{\mathrm{hull}}=74{,}869,\qquad
f_{\mathrm{hull}}=\frac{74{,}869}{600{,}000}=0.124782.
\]

## 4. Extract surface voxels and face-center points

An occupied voxel is on the surface if at least one of its six axis-aligned
neighbors is empty or outside the grid. Using the six offsets

\[
(\pm1,0,0),\quad(0,\pm1,0),\quad(0,0,\pm1),
\]

the test is

\[
\operatorname{surface}(v)=\operatorname{occupied}(v)\land
\left[\exists n\in\mathcal N_6(v):\neg\operatorname{occupied}(n)\right].
\]

For every exposed face, add a point at the face center. For voxel center
((c_x,c_y,c_z)), examples are

\[
(c_x+\Delta x/2,c_y,c_z),\qquad(c_x,c_y-\Delta y/2,c_z),
\]

and the four other signed-axis counterparts. Store both the originating voxel
index and the outward normal with each point; these are needed later for robust
visibility handling.

The output-point count differs from the surface-voxel count because one surface
voxel may have multiple exposed faces.

### Pseudocode: surface and points

```text
surfaceCount = 0
points = empty list
for each occupied voxel v
  for each of six neighbor directions d
    n = neighbor(v, d)
    if n is outside grid OR occupied[n] == false
      mark v as surface
      append faceCenter(v, d), outwardNormal(d), sourceVoxel(v) to points
    end
  end
  if v had at least one exposed face
    surfaceCount += 1
  end
end
```

**Record after execution:**

\[
N_{\mathrm{surface}}=26{,}311,\qquad
f_{\mathrm{surface}}=\frac{26{,}311}{600{,}000}=0.043852.
\]

The face-center procedure produced

\[
N_{\mathrm{points}}=49{,}292.
\]

This is larger than (N_{\mathrm{surface}}=26{,}311) because a surface voxel
can border empty space in more than one of its six directions. The algorithm
emits one point per exposed face, not one point per surface voxel.
\]

## 5. Assign false colors and export the diagnostic PLY

False color encodes the geometry itself rather than the dancer's appearance.
For output-point coordinate ranges ([X_{\min},X_{\max}]),
([Y_{\min},Y_{\max}]), and ([Z_{\min},Z_{\max}]), use

\[
R=\operatorname{round}\left(255\frac{X-X_{\min}}{X_{\max}-X_{\min}}\right),
\]
\[
G=\operatorname{round}\left(255\frac{Y-Y_{\min}}{Y_{\max}-Y_{\min}}\right),
\qquad
B=\operatorname{round}\left(255\frac{Z-Z_{\min}}{Z_{\max}-Z_{\min}}\right).
\]

Clamp every channel to ([0,255]). If a denominator is zero, use a fixed safe
channel value instead. Smooth coordinate-color gradients make wrong axes, flips,
and spatial offsets visually obvious in MeshLab.

### Pseudocode: false color and PLY

```text
compute min/max XYZ over points
for each point q
  q.R = clamp(round(255*(q.X-Xmin)/(Xmax-Xmin)))
  q.G = clamp(round(255*(q.Y-Ymin)/(Ymax-Ymin)))
  q.B = clamp(round(255*(q.Z-Zmin)/(Zmax-Zmin)))
end
write ASCII PLY header with element vertex = length(points)
write one "x y z r g b" row per point
```

## 6. Fuse true colors only from visible cameras

A projection inside a silhouette does not guarantee that a camera sees the
correct surface point. Another occupied voxel may lie closer to the camera.
For surface point (q) and camera center (C_i), test the open ray segment

\[
r_i(t)=q+t(C_i-q),\qquad 0<t<1.
\]

Traverse the voxel grid along this segment using 3D DDA (or an equivalent
grid-ray traversal). Start a small distance outside the source face so the
source voxel does not occlude itself. The camera can contribute only when no
other occupied voxel occurs on the ray and the projected pixel is valid and
foreground.

For the valid color samples \(\{(R_j,G_j,B_j)\}_{j\in\mathcal I(q)}\), use the
channelwise median:

\[
R(q)=\operatorname{median}_{j\in\mathcal I(q)}R_j,
\quad G(q)=\operatorname{median}_{j\in\mathcal I(q)}G_j,
\quad B(q)=\operatorname{median}_{j\in\mathcal I(q)}B_j.
\]

The median suppresses isolated incorrect samples caused by calibration or
silhouette-edge errors. If no camera is visible, use and document a fallback,
such as neutral gray or the nearest valid projection.

### Pseudocode: true color

```text
for each surface point q
  samples = empty list
  for i = 1 .. 8
    project q into RGB image i
    if projection invalid or projected pixel is background
      continue
    end
    if rayFromFaceToCamera(q, normal, C[i]) intersects occupied voxel
      continue
    end
    append RGBImage[i](projectedPixel) to samples
  end
  if samples is nonempty
    q.color = channelwiseMedian(samples)
  else
    q.color = documentedFallback
  end
end
write ASCII PLY using unchanged geometry and true colors
```

## 7. Validation and deliverables

I will validate the result with the following checks:

1. Check every projection against image bounds before indexing a silhouette.
2. Confirm that the PLY header vertex count equals the number of written rows.
3. Open both PLY outputs in MeshLab.
4. Inspect false-color gradients for flipped or misplaced world axes.
5. Reproject final points into each camera and compare their support to the
   original silhouettes.
6. Inspect true-color output for obvious rear-surface color bleeding, which
   would indicate an incorrect visibility test.
7. Report the selected grid dimensions, voxel size, counts, fractions, and
   fallback behavior for points with no visible camera.

## Final results to complete after execution

| Quantity | Result |
| --- | --- |
| Grid dimensions ((N_x,N_y,N_z)) | ((100,120,50)) |
| Voxel dimensions ((\Delta x,\Delta y,\Delta z)) | ((0.05,0.05,0.05)) m |
| Occupied voxels | 74,869 |
| Occupied fraction | 0.124782 (12.4782%) |
| Surface voxels | 26,311 |
| Surface fraction | 0.043852 (4.3852%) |
| Output face-center points | 49,292 |
| True-color fallback policy | Neutral gray `(128,128,128)` |
| False-color PLY filename | `visual_hull_false_color.ply` |
| True-color PLY filename | `visual_hull_true_color.ply` |

## 9. Bonus: two point lights and 3D shadows

The optional bonus is treated as Step 9 in the project checklist. Choose two
point lights outside the reconstructed volume and document their world-space
coordinates. For each light and each voxel or surface point, use a 3D DDA ray
from the light to the point. If another occupied voxel blocks the segment, the
point is shadowed from that light. Reproject shadowed points into each input
image and darken only valid foreground pixels. Reproject light-facing regions
and blend them lighter, then annotate the projected light locations when they
fall inside an image. Save the resulting images and explain the ray test,
projection, blending rule, and voxelized-visual-hull limitations.

## 10. Submission format

The mandatory Canvas submission is a ZIP file containing one PDF and the final
true-color PLY model. The PDF must contain the source code, a brief explanation
of what was done, and images or screenshots of the reconstructed model. The
report should include the grid and camera method, all measured counts and
fractions, surface and face-center reasoning, false-color and true-color
methods, visibility and median fusion, fallback behavior, PLY details, and
final screenshots. If the bonus is completed, include its light positions,
shadow/reprojection method, output images, and limitations. Clearly label the
false-color PLY as an intermediate file if it is also included.
