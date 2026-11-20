# CS 532 Homework 3 Notes: Voxel-Based Reconstruction

## The big picture
? How can multiple 2D Camera views be combined to estimate 3d shape?
? How do voxel grids & sillhouettes work?
? Why are visibility checks necessary for realistic colors and shadows?

Here, I reconstruct an approximate 3D dancer from multiple calibrated camera
images and their binary silhouettes. Instead of guessing a smooth surface
directly, I divide a known 3D region into small boxes called voxels. I keep
only boxes that agree with every silhouette, turn the boundary of the kept
boxes into a point cloud, color the points, and export them as a PLY model.

## If you only read one section

The short version is this: each camera gives me a different 2D view of the
same dancer. A silhouette tells me where the dancer could be in that view, but
it does not tell me the depth. I solve this by testing many tiny 3D boxes. If a
box would look like part of the dancer from every camera, I keep it. If even
one camera says the box is impossible, I remove it.

The kept boxes form a rough 3D shape called a **visual hull**. I then keep the
outside faces of that shape as points. Finally, I color the points in two ways:
false color shows where a point is in space, while true color samples the
original photographs after checking whether a camera can actually see the
point. That combination of simple 2D evidence, 3D geometry, and visibility
checking is what makes the assignment interesting.

The reconstruction is called a **visual hull**. It should contain the real
object if the silhouettes are accurate, but it cannot recover inward dents that
never change the outline in any camera view. For example, a hollow indentation
can remain filled in the visual hull. The silhouettes tell me what the dancer
could occupy, not every detail of the dancer's actual surface.

## Dataset and camera math

I have eight color images, eight silhouette images, and eight 3x4 camera
projection matrices. A world-space point is written in homogeneous form as

```text
X = [X, Y, Z, 1]^T.
```

For camera `i`, its projection matrix `P_i` is the calibration information
that tells me where a 3D point should appear in that image. It maps the point
to temporary image coordinates:

```text
[u_tilde, v_tilde, w_tilde]^T = P_i X.
u = u_tilde / w_tilde
v = v_tilde / w_tilde
```

After dividing by `w_tilde`, `(u, v)` is the pixel location in that camera. A projection is useful only
when `w_tilde` is positive and `(u, v)` lies inside the image. In my code, I
round the projected coordinates to the nearest pixel before reading a
silhouette or RGB value.

## 1. Define the voxel grid

A **voxel** is a three-dimensional pixel: a small box that represents a small
region of space. The smaller the voxels are, the more detail I can represent,
but the more boxes I have to test. The assignment bounding box is

```text
x in [-2.5, 2.5] meters
y in [-3.0, 3.0] meters
z in [ 0.0, 2.5] meters.
```

Choose `Nx`, `Ny`, and `Nz`, the number of voxels along x, y, and z. The voxel side lengths are

```text
dx = (xmax - xmin) / Nx
dy = (ymax - ymin) / Ny
dz = (zmax - zmin) / Nz.
```

Voxel `(ix, iy, iz)` has lower corner

```text
[xmin + ix*dx, ymin + iy*dy, zmin + iz*dz]
```

and center

```text
c(ix,iy,iz) = [xmin + (ix + 0.5)*dx,
               ymin + (iy + 0.5)*dy,
               zmin + (iz + 0.5)*dz].
```

There are `Nx * Ny * Nz` total voxels. Increasing the resolution makes the
shape less blocky, but also increases memory use and runtime. I found this to
be a tradeoff between seeing more detail and waiting longer for every camera
projection.

For the implementation, keep at least an occupancy array such as
`occupied[Nx, Ny, Nz]`. This code uses a one-byte flat `bytearray`; zero means
EMPTY and one means OCCUPIED. Initially, every value is zero.

## 2. Build the visual hull

Now I ask the same question for every voxel: “Would this voxel project inside
the dancer in every camera?” Each binary silhouette says which image pixels
might belong to the dancer. A
voxel is consistent with camera `i` when its center projects onto a foreground
silhouette pixel in that camera. The visual-hull occupancy test is

```text
occupied(v) = AND over cameras i of
              [project_i(center(v)) is valid AND silhouette_i(u_i, v_i) is foreground].
```

In plain language, I start by treating every voxel as possible dancer space.
Then I *reject* a voxel as soon as one camera sees its center outside the dancer
silhouette. This is the discrete version of intersecting the generalized cones
formed by back-projecting all of the silhouettes into 3D. Watching the 2D
silhouettes gradually turn into a 3D volume was one of the most satisfying
parts of the assignment.

The two numbers I keep track of are:

```text
visual_hull_count = number of occupied voxels
visual_hull_fraction = visual_hull_count / (Nx * Ny * Nz).
```

## 3. Find surface voxels

After carving, most kept voxels are inside the shape. I only need the boundary
for the point-cloud output, so I look for kept voxels that touch empty space. A
**surface voxel** is an occupied voxel with at least one neighboring voxel that
is empty. With 6-connected neighbors, the neighboring offsets are

```text
(+/-1, 0, 0), (0, +/-1, 0), (0, 0, +/-1).
```

For each occupied voxel, I inspect these six locations. A neighbor outside the
grid is treated as *empty* because the grid boundary *exposes a face.* The test is

```text
surface(v) = occupied(v) AND (at least one 6-neighbor is empty).
```

Interior occupied voxels are not surface voxels because they are completely surrounded by occupied volume. Report the surface count and `surface_count / total_voxel_count`.

## 4. Create the output geometry

The assignment asks for points rather than a closed triangle mesh. For every
surface voxel, I
add one point at the center of each face next to an empty neighbor. If the
voxel center is `(cx, cy, cz)`, the six possible face centers are

```text
(cx - dx/2, cy,          cz)          (cx + dx/2, cy,          cz)
(cx,          cy - dy/2, cz)          (cx,          cy + dy/2, cz)
(cx,          cy,          cz - dz/2) (cx,          cy,          cz + dz/2).
```

Add only the face corresponding to an empty neighbor. A surface voxel can have one through six exposed faces, so the output-point count is generally different from the number of surface voxels. Adjacent occupied voxels share an internal face, which is not emitted, while a voxel on a corner can contribute multiple points.

I also store the voxel index and outward face normal with each point. At first
this seemed like extra bookkeeping, but it becomes important when I need to
start a visibility ray just outside the surface.

## 5. Assign false colors

False color visualizes position, not the image appearance of the dancer. I
first find the coordinate bounds of the generated output points:

```text
Xmin, Xmax, Ymin, Ymax, Zmin, Zmax.
```

For a point `(X, Y, Z)`, assign

```text
R = round(255 * (X - Xmin) / (Xmax - Xmin))
G = round(255 * (Y - Ymin) / (Ymax - Ymin))
B = round(255 * (Z - Zmin) / (Zmax - Zmin)).
```

Clamp every result to `[0, 255]` and write it as an unsigned byte. If a range
such as `Xmax - Xmin` is zero, use a safe constant (for example 0 or 128) for
that channel instead of dividing by zero. This color scheme is a debugging
aid. Red changes along x, green along y, and blue along z, so flipped axes or
incorrectly positioned geometry are easier to notice.

## 6. Export the false-color PLY

Write an ASCII PLY header with an exact vertex count followed by one row per point:

```text
ply
format ascii 1.0
element vertex NUMBER_OF_POINTS
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
element face 0
end_header
x y z r g b
```

The `element vertex` number must equal the actual number of data rows. Opening
the file in MeshLab is a useful reality check: does the silhouette look like a
dancer, and do the coordinate colors change in the directions I expected?

## 7. Assign true colors with visibility

This is where the reconstruction starts to look more like the original
photographs. A point may project onto a dancer-colored pixel even when another
part of the shape is actually in front of it. I need to check the path between
the point and the camera before trusting that pixel.

True color estimates each surface point's color from the eight RGB camera
images. Project the point into every camera with the camera math above. A
camera can contribute an RGB sample only when:

1. The projection is in front of the camera and inside the image.
2. The projected pixel is inside that camera's silhouette.
3. The camera has an unoccluded line of sight to the point.

The third condition matters because a camera may project a rear or hidden surface point onto a foreground pixel that actually belongs to a nearer part of the dancer. Using that pixel would paint the hidden point with the wrong color.

### A voxel ray-visibility method

For an output face point `q` and camera center `C`, form the segment

```text
r(t) = q + t(C - q), where 0 < t < 1.
```

Traverse the voxels crossed by this ray (using a grid ray traversal such as 3D DDA). The point is visible from that camera if every voxel between the surface point and the camera is empty. The source surface voxel itself should be skipped; otherwise it would incorrectly occlude itself. A practical variant starts the ray a tiny distance outside the exposed face, using the stored outward normal, to avoid numerical self-intersection.

For every visible camera, read its RGB value at the projected pixel. If the valid samples are `(R_j, G_j, B_j)`, use the per-channel median:

```text
R = median_j(R_j)
G = median_j(G_j)
B = median_j(B_j).
```

The median is robust to small calibration errors, silhouette-edge pixels, and a bad sample from one view. If no camera passes the visibility test, use and document the neutral-gray fallback `(128,128,128)`. The implementation then exports another ASCII PLY using the same geometry and the true RGB values.

## 8. Write the true-color PLY

The true-color pass writes `visual_hull_true_color.ply` using the same
face-center geometry as the false-color model. The file is ASCII PLY with
49,292 vertices and the RGB values produced by the visibility-aware camera
fusion.

## 9. Bonus: two point lights and 3D shadows

The bonus treats the occupied visual hull as an object that blocks light. Pick two light positions `L1` and `L2` outside the reconstructed volume. For each reconstructed surface point `p`, test whether light `L` reaches it with the segment

```text
s(t) = L + t(p - L), where 0 < t < 1.
```

If this segment intersects an occupied voxel before reaching `p`, the point is in shadow from that light. This is the same ray-occlusion idea used for camera visibility, but the ray starts at a light rather than a camera.

A straightforward implementation for this project is:

1. Use the two selected lights `L1=(-4,-4,5)` and `L2=(4,2,4)` meters.
2. For each reconstructed surface point and each light, traverse the grid along
   the point-to-light segment with the existing 3D DDA routine.
3. If another occupied voxel blocks both light rays, darken the point after it
   is projected into a camera image.
4. If at least one light can reach the point, blend the projected pixel toward
   white.
5. Project each light into the camera image and draw a red marker when it is
   inside the image.
6. Save one annotated PPM image per camera in `submit/two_light_bonus/`.

These are my favorite three camera views of the bonus result:

![Two-light bonus: camera 1](cam1.png)

![Two-light bonus: camera 2](cam2.png)

![Two-light bonus: camera 3](cam3.png)

The implementation changes projected foreground surface pixels only. It does
not change the background. This is an approximate surface-point relighting
pass rather than a full volumetric shadow map.

These are approximate surface-point shadows because the object is a voxelized visual hull, not the exact dancer surface. That is acceptable as long as the method and limitations are stated clearly.

## 10. Submission format and report contents

The mandatory Canvas submission is one ZIP file containing one PDF and the
final true-color PLY model. The PDF must include the authored source code, a
brief explanation of the approach, and images or screenshots of the resulting
model. If the false-color PLY is included, it should be labeled as an
intermediate result.

For future reference, the PDF report should document the voxel bounds,
resolution, and memory choice; projection and silhouette carving; occupied and
surface voxel counts and fractions; face-center geometry and why its count
differs from the surface-voxel count; false-color normalization; ASCII PLY
format; true-color projection and visibility testing; median color fusion;
neutral-gray fallback behavior; and screenshots of the final models. If the
bonus is included, explain the two light locations, point-to-light ray test,
image reprojection and blending, output images, and limitations.

## What this assignment teaches

The purpose is to connect multi-view geometry, camera calibration, silhouettes, volumetric representations, and rendering in one pipeline. It demonstrates how multiple 2D views constrain 3D shape, why silhouette intersection produces a visual hull rather than an exact model, how to extract a usable surface point cloud from voxels, and how geometric visibility is needed for credible color and shadow estimates. The final PLY gives a concrete, inspectable result of that entire reconstruction process.

## Suggested implementation order

1. Parse one camera matrix and verify that a few known 3D points project into sensible image locations.
2. Build a low-resolution grid and implement silhouette occupancy for one camera, then all eight cameras.
3. Count and visualize occupied and surface voxels before generating a PLY.
4. Export the false-color PLY and inspect it in MeshLab.
5. Add camera-center recovery and ray traversal for true-color visibility.
6. Export and inspect the true-color PLY, then run and inspect the optional
   two-light shadow/relighting pass.

