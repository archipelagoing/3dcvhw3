from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re
import struct
import time
import zlib


# This stores the world-space limits and the occupancy volume. I keep the
# centers in three separate lists instead of building a large XYZ array.
@dataclass(frozen=True)
class VoxelGrid:
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float
    dx: float
    dy: float
    dz: float
    x_centers: tuple[float, ...]
    y_centers: tuple[float, ...]
    z_centers: tuple[float, ...]
    occupied: bytearray
    nx: int
    ny: int
    nz: int

    @property
    def shape(self) -> tuple[int, int, int]:
        return (self.nx, self.ny, self.nz)

    @property
    def total_voxels(self) -> int:
        return len(self.occupied)


# A P4 silhouette is a one-bit image used to decide whether a projected voxel
# is still a possible part of the object.
@dataclass(frozen=True)
class BinarySilhouette:
    width: int
    height: int
    row_bytes: int
    pixels: bytes

    def is_foreground(self, x: int, y: int) -> bool:
        # PBM pixels are packed left to right, most-significant bit first.
        byte_index = y * self.row_bytes + x // 8
        bit_mask = 1 << (7 - (x % 8))
        return bool(self.pixels[byte_index] & bit_mask)


# Each output point is the center of an exposed voxel face. The normal and
# source voxel are kept for the later camera visibility test.
@dataclass(frozen=True)
class SurfacePoint:
    x: float
    y: float
    z: float
    normal: tuple[int, int, int]
    voxel: tuple[int, int, int]


# This is the same point geometry after an RGB value has been assigned.
@dataclass(frozen=True)
class ColoredPoint:
    x: float
    y: float
    z: float
    red: int
    green: int
    blue: int


# The PNG loader stores decoded RGB bytes in one flat row-major array.
@dataclass(frozen=True)
class RGBImage:
    width: int
    height: int
    pixels: bytes

    def rgb(self, x: int, y: int) -> tuple[int, int, int]:
        # Every pixel uses three consecutive bytes: red, green, and blue.
        index = 3 * (y * self.width + x)
        return self.pixels[index], self.pixels[index + 1], self.pixels[index + 2]


def define_voxel_grid(voxel_size_m: float = 0.05) -> VoxelGrid:
    # Step 1 assignment requirement:
    # Define a voxel grid over x=[-2.5,2.5] m, y=[-3,3] m, and z=[0,2.5] m.
    # Choose a discretization that fits comfortably in memory. The purpose of
    # this grid is to estimate which small volume cells are occupied and which
    # cells are free space. Here I use 0.05 m voxels, giving 600,000 cells.
    # The occupancy array starts empty and is filled during Step 2.
    #
    # Step 1 implementation: make the assignment volume and store voxel centers.
    if voxel_size_m <= 0:
        raise ValueError("voxel_size_m must be positive")

    xmin, xmax = -2.5, 2.5
    ymin, ymax = -3.0, 3.0
    zmin, zmax = 0.0, 2.5

    nx = round((xmax - xmin) / voxel_size_m)
    ny = round((ymax - ymin) / voxel_size_m)
    nz = round((zmax - zmin) / voxel_size_m)

    if abs(nx * voxel_size_m - (xmax - xmin)) > 1e-12:
        raise ValueError("x bounds must be exactly divisible by voxel_size_m")
    if abs(ny * voxel_size_m - (ymax - ymin)) > 1e-12:
        raise ValueError("y bounds must be exactly divisible by voxel_size_m")
    if abs(nz * voxel_size_m - (zmax - zmin)) > 1e-12:
        raise ValueError("z bounds must be exactly divisible by voxel_size_m")

    x_centers = tuple(xmin + (ix + 0.5) * voxel_size_m for ix in range(nx))
    y_centers = tuple(ymin + (iy + 0.5) * voxel_size_m for iy in range(ny))
    z_centers = tuple(zmin + (iz + 0.5) * voxel_size_m for iz in range(nz))
    # One byte per voxel: 0 means empty, 1 will mean occupied in Step 2.
    occupied = bytearray(nx * ny * nz)

    return VoxelGrid(
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        zmin=zmin,
        zmax=zmax,
        dx=voxel_size_m,
        dy=voxel_size_m,
        dz=voxel_size_m,
        x_centers=x_centers,
        y_centers=y_centers,
        z_centers=z_centers,
        occupied=occupied,
        nx=nx,
        ny=ny,
        nz=nz,
    )


def load_projection_matrix(path: Path) -> tuple[tuple[float, ...], ...]:
    # The XML wrapper contains the 3 rows of a 3x4 camera matrix.
    text = path.read_text()
    match = re.search(r"<camera>\s*(.*?)\s*</camera>", text, re.DOTALL)
    if match is None:
        raise ValueError(f"Could not find a <camera> matrix in {path}")
    values = [float(value) for value in re.findall(
        r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", match.group(1)
    )]
    if len(values) != 12:
        raise ValueError(f"Expected 12 projection values in {path}, got {len(values)}")
    return tuple(tuple(values[4 * row:4 * row + 4]) for row in range(3))


def _read_pbm_token(stream) -> bytes:
    # PBM headers contain whitespace and may contain comments.
    token = bytearray()
    while True:
        char = stream.read(1)
        if not char:
            raise ValueError("Unexpected end of PBM header")
        if char.isspace():
            continue
        if char == b"#":
            stream.readline()
            continue
        token.extend(char)
        break
    while True:
        char = stream.read(1)
        if not char or char.isspace():
            return bytes(token)
        token.extend(char)


def load_p4_pbm(path: Path) -> BinarySilhouette:
    # P4 stores one bit per pixel, with each row padded to a whole byte.
    with path.open("rb") as stream:
        magic = _read_pbm_token(stream)
        if magic != b"P4":
            raise ValueError(f"Expected P4 PBM file at {path}, got {magic!r}")
        width = int(_read_pbm_token(stream))
        height = int(_read_pbm_token(stream))
        row_bytes = (width + 7) // 8
        pixels = stream.read(row_bytes * height)
    if len(pixels) != row_bytes * height:
        raise ValueError(f"PBM pixel data is truncated: {path}")
    return BinarySilhouette(width, height, row_bytes, pixels)


def load_rgb_png(path: Path) -> RGBImage:
    # The supplied images are simple 8-bit RGB PNGs. Decode their scanline filters.
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    offset, chunks = 8, []
    while offset < len(raw):
        length = struct.unpack(">I", raw[offset:offset + 4])[0]
        kind, data = raw[offset + 4:offset + 8], raw[offset + 8:offset + 8 + length]
        offset += length + 12
        chunks.append((kind, data))
        if kind == b"IEND": break
    ihdr = next(data for kind, data in chunks if kind == b"IHDR")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", ihdr)
    if (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
        raise ValueError("Expected 8-bit non-interlaced RGB PNG")
    encoded = zlib.decompress(b"".join(data for kind, data in chunks if kind == b"IDAT"))
    stride, previous, output, pos = width * 3, bytearray(width * 3), bytearray(), 0
    for _ in range(height):
        # Each PNG row starts with a filter byte. Reverse that filter so the
        # stored values become the actual RGB bytes.
        filter_type, row = encoded[pos], bytearray(encoded[pos + 1:pos + 1 + stride])
        pos += stride + 1
        for i in range(stride):
            left = row[i - 3] if i >= 3 else 0
            above = previous[i]
            upper_left = previous[i - 3] if i >= 3 else 0
            if filter_type == 1: row[i] = (row[i] + left) & 255
            elif filter_type == 2: row[i] = (row[i] + above) & 255
            elif filter_type == 3: row[i] = (row[i] + ((left + above) // 2)) & 255
            elif filter_type == 4:
                p, pa, pb, pc = left + above - upper_left, 0, 0, 0
                pa, pb, pc = abs(p-left), abs(p-above), abs(p-upper_left)
                row[i] = (row[i] + (left if pa <= pb and pa <= pc else above if pb <= pc else upper_left)) & 255
            elif filter_type != 0: raise ValueError("Unsupported PNG filter")
        output.extend(row); previous = row
    return RGBImage(width, height, bytes(output))


def project_point(
    matrix: tuple[tuple[float, ...], ...], x: float, y: float, z: float
) -> tuple[float, float, float]:
    # P [x,y,z,1]^T gives homogeneous image coordinates.
    # Perspective division happens later: u = u_tilde / w_tilde and
    # v = v_tilde / w_tilde.
    p = (x, y, z, 1.0)
    return tuple(sum(row[k] * p[k] for k in range(4)) for row in matrix)


def camera_center(matrix: tuple[tuple[float, ...], ...]) -> tuple[float, float, float]:
    # For P=[M|p4], the camera center satisfies M C + p4 = 0.
    # Therefore C = -M^-1 p4. The following is the explicit 3x3 inverse.
    a,b,c = matrix[0][:3]; d,e,f = matrix[1][:3]; g,h,i = matrix[2][:3]
    det = a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
    if abs(det) < 1e-12: raise ValueError("Singular camera matrix")
    inv = ((e*i-f*h, c*h-b*i, b*f-c*e), (f*g-d*i, a*i-c*g, c*d-a*f), (d*h-e*g, b*g-a*h, a*e-b*d))
    q = (-matrix[0][3], -matrix[1][3], -matrix[2][3])
    return tuple(sum(inv[row][k]*q[k] for k in range(3))/det for row in range(3))


def ray_is_unoccluded(grid: VoxelGrid, point: SurfacePoint, camera: tuple[float, float, float]) -> bool:
    # Step 7: traverse the ray from just outside the face toward the camera.
    eps = 1e-6
    # Start just outside the face so the point's own occupied voxel does not
    # incorrectly count as an occluder.
    ox, oy, oz = point.x + eps*point.normal[0], point.y + eps*point.normal[1], point.z + eps*point.normal[2]
    dx, dy, dz = camera[0]-ox, camera[1]-oy, camera[2]-oz
    t0, t1 = 0.0, 1.0
    # Find the part of the point-to-camera segment that lies inside the grid.
    for origin, delta, low, high in ((ox,dx,grid.xmin,grid.xmax),(oy,dy,grid.ymin,grid.ymax),(oz,dz,grid.zmin,grid.zmax)):
        if abs(delta) < 1e-12:
            if origin < low or origin > high: return True
            continue
        enter, exit = (low-origin)/delta, (high-origin)/delta
        if enter > exit: enter, exit = exit, enter
        t0, t1 = max(t0, enter), min(t1, exit)
    if t0 > t1: return True
    t = max(t0, 0.0) + 1e-9
    px,py,pz = ox+t*dx, oy+t*dy, oz+t*dz
    ix,iy,iz = min(grid.nx-1,max(0,int((px-grid.xmin)/grid.dx))), min(grid.ny-1,max(0,int((py-grid.ymin)/grid.dy))), min(grid.nz-1,max(0,int((pz-grid.zmin)/grid.dz)))
    steps, next_t, delta_t = [], [], []
    # For each axis, record the direction and the next voxel boundary crossing.
    # This is the setup for the 3D DDA grid traversal.
    for index, position, direction, low, size in ((ix,px,dx,grid.xmin,grid.dx),(iy,py,dy,grid.ymin,grid.dy),(iz,pz,dz,grid.zmin,grid.dz)):
        if direction > 0: steps.append(1); next_t.append(t + (low+(index+1)*size-position)/direction); delta_t.append(size/direction)
        elif direction < 0: steps.append(-1); next_t.append(t + (low+index*size-position)/direction); delta_t.append(-size/direction)
        else: steps.append(0); next_t.append(float('inf')); delta_t.append(float('inf'))
    # A segment can cross at most Nx + Ny + Nz cells; the cap also protects
    # against a numerical tie at a voxel corner causing an endless DDA loop.
    for _ in range(grid.nx + grid.ny + grid.nz + 3):
        if t > t1:
            break
        # Skip the source voxel. Any other occupied voxel blocks the camera.
        if (ix,iy,iz) != point.voxel and grid.occupied[voxel_index(grid,ix,iy,iz)]: return False
        axis = min(range(3), key=lambda k: next_t[k]); t = next_t[axis]; next_t[axis] += delta_t[axis]
        if axis == 0: ix += steps[0]
        elif axis == 1: iy += steps[1]
        else: iz += steps[2]
        if ix<0 or ix>=grid.nx or iy<0 or iy>=grid.ny or iz<0 or iz>=grid.nz: break
    return True


def assign_true_colors(grid: VoxelGrid, points: list[SurfacePoint], dataset_dir: Path,
                       show_progress: bool = False) -> tuple[list[ColoredPoint], int]:
    """Step 7: assign true RGB colors using only non-occluded camera views.

    Each output surface point is projected into all eight RGB images. A camera
    contributes only when the projection is in front of the camera, inside the
    image, and on a foreground silhouette pixel. The point-to-camera segment
    is then checked with 3D DDA; occupied voxels between the face and camera
    reject the sample because the point is hidden. The accepted samples are
    combined with a per-channel median. Points with no visible camera use the
    neutral-gray fallback value (128, 128, 128).
    """
    # Step 7: keep only foreground samples with an unblocked camera ray.
    matrices = [load_projection_matrix(dataset_dir / "calibration" / f"cam{i:02d}.xml") for i in range(8)]
    cameras = [camera_center(matrix) for matrix in matrices]
    silhouettes = [load_p4_pbm(dataset_dir / f"silh_cam{i:02d}_00023_0000008550.pbm") for i in range(8)]
    images = [load_rgb_png(dataset_dir / f"cam{i:02d}_00023_0000008550.png") for i in range(8)]
    colored, fallback_count = [], 0
    started = time.perf_counter()
    total = len(points)
    for point_number, point in enumerate(points, start=1):
        samples=[]
        for matrix, camera, silhouette, image in zip(matrices,cameras,silhouettes,images):
            ut,vt,wt=project_point(matrix,point.x,point.y,point.z)
            if wt<=0: continue
            # Convert homogeneous image coordinates to the nearest pixel.
            u,v=int(ut/wt+0.5),int(vt/wt+0.5)
            # A sample is useful only if it is inside the image and foreground.
            if u<0 or u>=image.width or v<0 or v>=image.height or not silhouette.is_foreground(u,v): continue
            # A foreground projection can still belong to a nearer surface.
            # The ray test filters out that hidden-surface color sample.
            if ray_is_unoccluded(grid,point,camera): samples.append(image.rgb(u,v))
        if samples:
            # The channelwise median is less sensitive to one bad camera sample.
            channels=tuple(sorted(sample[k] for sample in samples)[len(samples)//2] for k in range(3))
        else: channels=(128,128,128); fallback_count += 1
        colored.append(ColoredPoint(point.x,point.y,point.z,*channels))
        if show_progress and (point_number % 500 == 0 or point_number == total):
            elapsed = time.perf_counter() - started
            remaining = elapsed * (total - point_number) / point_number
            print(f"True-color visibility: {point_number}/{total} "
                  f"({100 * point_number / total:5.1f}%) | "
                  f"elapsed {elapsed / 60:.1f} min | ETA {remaining / 60:.1f} min",
                  flush=True)
    return colored, fallback_count


def compute_visual_hull(grid: VoxelGrid, dataset_dir: Path) -> tuple[int, float]:
    """Step 2: start with EMPTY voxels and keep only centers inside all silhouettes.

    The visual-hull result is reported as both the occupied-voxel count and
    occupied_count / total_voxels. With the current grid, the result is 74,869
    occupied voxels, which is 0.124782 of the 600,000-voxel volume.
    """
    # Step 2: a voxel survives only if its center is inside every silhouette.
    matrices = [load_projection_matrix(dataset_dir / "calibration" / f"cam{i:02d}.xml")
                for i in range(8)]
    silhouettes = [load_p4_pbm(dataset_dir / f"silh_cam{i:02d}_00023_0000008550.pbm")
                   for i in range(8)]

    occupied_count = 0
    linear_index = 0
    for z in grid.z_centers:
        for y in grid.y_centers:
            for x in grid.x_centers:
                # Start optimistic, then carve the voxel away as soon as one
                # camera sees its center outside the foreground silhouette.
                keep = True
                for matrix, silhouette in zip(matrices, silhouettes):
                    u_tilde, v_tilde, w_tilde = project_point(matrix, x, y, z)
                    if w_tilde <= 0:
                        keep = False
                        break
                    # MATLAB/Python image arrays are zero-indexed after loading.
                    # A point behind a camera or outside the image cannot
                    # provide silhouette evidence for this voxel.
                    u = int(u_tilde / w_tilde + 0.5)
                    v = int(v_tilde / w_tilde + 0.5)
                    if (u < 0 or u >= silhouette.width or v < 0 or
                            v >= silhouette.height or
                            not silhouette.is_foreground(u, v)):
                        keep = False
                        break
                if keep:
                    grid.occupied[linear_index] = 1
                    occupied_count += 1
                linear_index += 1

    return occupied_count, occupied_count / grid.total_voxels


def voxel_index(grid: VoxelGrid, ix: int, iy: int, iz: int) -> int:
    # Flatten (x,y,z) while keeping x as the fastest-changing index.
    return ix + grid.nx * (iy + grid.ny * iz)


def find_surface_voxels(grid: VoxelGrid) -> tuple[bytearray, int, float]:
    """Step 3: find occupied voxels with at least one empty neighbor.

    A surface voxel is occupied and has an empty or outside-the-grid neighbor
    among the six axis-aligned neighbors. This step reports the surface count
    and surface_count / total_voxels. The current result is 26,311 surface
    voxels, or 0.043852 of the 600,000-voxel grid.
    """
    # Step 3: an occupied voxel is surface material if one of six neighbors is empty.
    surface = bytearray(grid.total_voxels)
    surface_count = 0
    neighbor_offsets = ((-1, 0, 0), (1, 0, 0), (0, -1, 0),
                        (0, 1, 0), (0, 0, -1), (0, 0, 1))

    for iz in range(grid.nz):
        for iy in range(grid.ny):
            for ix in range(grid.nx):
                index = voxel_index(grid, ix, iy, iz)
                if not grid.occupied[index]:
                    continue
                for dx, dy, dz in neighbor_offsets:
                    nx, ny, nz = ix + dx, iy + dy, iz + dz
                    neighbor_is_empty = (
                        # A neighbor outside the volume is treated as empty,
                        # so boundary voxels contribute exposed faces.
                        nx < 0 or nx >= grid.nx or
                        ny < 0 or ny >= grid.ny or
                        nz < 0 or nz >= grid.nz or
                        not grid.occupied[voxel_index(grid, nx, ny, nz)]
                    )
                    if neighbor_is_empty:
                        surface[index] = 1
                        surface_count += 1
                        break

    return surface, surface_count, surface_count / grid.total_voxels


def generate_output_geometry(grid: VoxelGrid, surface: bytearray) -> list[SurfacePoint]:
    """Step 4: create one output point at each exposed voxel-face center.

    A face is included when its neighboring voxel is EMPTY or outside the
    grid. The current model contains 49,292 face-center points from 26,311
    surface voxels. These numbers are not expected to be equal because one
    surface voxel can have multiple exposed faces, from one through six.
    """
    # Step 4: emit the center of every face next to an empty voxel.
    points: list[SurfacePoint] = []
    face_directions = ((-1, 0, 0), (1, 0, 0), (0, -1, 0),
                       (0, 1, 0), (0, 0, -1), (0, 0, 1))

    for iz in range(grid.nz):
        for iy in range(grid.ny):
            for ix in range(grid.nx):
                index = voxel_index(grid, ix, iy, iz)
                if not surface[index]:
                    continue
                cx = grid.x_centers[ix]
                cy = grid.y_centers[iy]
                cz = grid.z_centers[iz]
                for dx, dy, dz in face_directions:
                    nx, ny, nz = ix + dx, iy + dy, iz + dz
                    neighbor_is_empty = (
                        nx < 0 or nx >= grid.nx or
                        ny < 0 or ny >= grid.ny or
                        nz < 0 or nz >= grid.nz or
                        not grid.occupied[voxel_index(grid, nx, ny, nz)]
                    )
                    if neighbor_is_empty:
                        # Move half a voxel along the face normal to reach the
                        # center of the exposed face.
                        points.append(SurfacePoint(
                            x=cx + dx * grid.dx / 2,
                            y=cy + dy * grid.dy / 2,
                            z=cz + dz * grid.dz / 2,
                            normal=(dx, dy, dz),
                            voxel=(ix, iy, iz),
                        ))
    return points


def _coordinate_channel(value: float, low: float, high: float) -> int:
    # Normalize a coordinate range to an 8-bit color channel.
    if high == low:
        return 128
    return max(0, min(255, round(255 * (value - low) / (high - low))))


def assign_false_colors(points: list[SurfacePoint]) -> list[ColoredPoint]:
    """Step 5: assign false RGB colors from the reconstructed coordinates.

    First find X_min/X_max, Y_min/Y_max, and Z_min/Z_max over all output
    points. Then use

        RED   = 255 * (X - X_min) / (X_max - X_min)
        GREEN = 255 * (Y - Y_min) / (Y_max - Y_min)
        BLUE  = 255 * (Z - Z_min) / (Z_max - Z_min)

    The values are rounded and clamped to unsigned-byte RGB values. A channel
    whose coordinate range is zero uses the safe value 128 instead.
    """
    # Step 5: red follows X, green follows Y, and blue follows Z.
    # Each channel is round(255 * (coordinate - minimum) / range).
    if not points:
        return []
    xmin, xmax = min(p.x for p in points), max(p.x for p in points)
    ymin, ymax = min(p.y for p in points), max(p.y for p in points)
    zmin, zmax = min(p.z for p in points), max(p.z for p in points)
    return [ColoredPoint(
        x=point.x,
        y=point.y,
        z=point.z,
        red=_coordinate_channel(point.x, xmin, xmax),
        green=_coordinate_channel(point.y, ymin, ymax),
        blue=_coordinate_channel(point.z, zmin, zmax),
    ) for point in points]


def write_ascii_ply(path: Path, points: list[ColoredPoint]) -> None:
    """Step 6/8: write the colored point cloud as an ASCII PLY file.

    The header's ``element vertex`` value is the exact number of output
    points. Each following row contains three floating-point coordinates and
    three unsigned-byte RGB values. The resulting PLY can be opened in
    MeshLab, which is useful for checking the reconstructed model visually.
    """
    # Step 6/8: write one ASCII PLY row for every colored 3D point.
    # The vertex count in the header must equal the number of rows written.
    header = (
        "ply\n"
        "format ascii 1.0\n"
        f"element vertex {len(points)}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar red\n"
        "property uchar green\n"
        "property uchar blue\n"
        "element face 0\n"
        "end_header\n"
    )
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(header)
        for point in points:
            stream.write(
                f"{point.x:.6f} {point.y:.6f} {point.z:.6f} "
                f"{point.red} {point.green} {point.blue}\n"
            )


def write_ppm(path: Path, image: RGBImage) -> None:
    """Write an RGB image in simple binary PPM format for visual inspection."""
    with path.open("wb") as stream:
        stream.write(f"P6\n{image.width} {image.height}\n255\n".encode("ascii"))
        stream.write(image.pixels)


def render_two_light_bonus(points: list[SurfacePoint], grid: VoxelGrid,
                           dataset_dir: Path, output_dir: Path) -> None:
    """Step 9 bonus: reproject approximate two-light shadows into each camera.

    Two point lights are placed outside the voxel volume. A surface point is
    considered lit by a light when the 3D DDA ray from the point to that light
    does not hit another occupied voxel. Points blocked from both lights are
    darkened in each input image. Points visible to at least one light are
    blended slightly lighter. The light positions are marked with red pixels
    after projection into each camera. The result is saved as PPM images.
    """
    lights = ((-4.0, -4.0, 5.0), (4.0, 2.0, 4.0))
    matrices = [load_projection_matrix(dataset_dir / "calibration" / f"cam{i:02d}.xml") for i in range(8)]
    silhouettes = [load_p4_pbm(dataset_dir / f"silh_cam{i:02d}_00023_0000008550.pbm") for i in range(8)]
    images = [load_rgb_png(dataset_dir / f"cam{i:02d}_00023_0000008550.png") for i in range(8)]
    output_dir.mkdir(parents=True, exist_ok=True)

    for camera_number, (matrix, silhouette, image) in enumerate(zip(matrices, silhouettes, images)):
        # Start with the original image and change only projected foreground
        # points. This keeps the background untouched.
        pixels = bytearray(image.pixels)
        for point in points:
            ut, vt, wt = project_point(matrix, point.x, point.y, point.z)
            if wt <= 0:
                continue
            u, v = int(ut / wt + 0.5), int(vt / wt + 0.5)
            if (u < 0 or u >= image.width or v < 0 or v >= image.height or
                    not silhouette.is_foreground(u, v)):
                continue

            # The existing DDA routine works for a point-to-camera segment;
            # using a light as the endpoint gives the same occlusion test.
            lit_by_light = any(ray_is_unoccluded(grid, point, light) for light in lights)
            pixel_index = 3 * (v * image.width + u)
            if lit_by_light:
                # Add a small amount of white to represent direct illumination.
                for channel in range(3):
                    pixels[pixel_index + channel] = min(
                        255, round(0.75 * pixels[pixel_index + channel] + 0.25 * 255)
                    )
            else:
                # The point is behind the reconstructed shape from both lights.
                for channel in range(3):
                    pixels[pixel_index + channel] = round(0.45 * pixels[pixel_index + channel])

        # Mark each light if its projection lands inside this image.
        for light in lights:
            ut, vt, wt = project_point(matrix, *light)
            if wt <= 0:
                continue
            u, v = int(ut / wt + 0.5), int(vt / wt + 0.5)
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    mark_u, mark_v = u + dx, v + dy
                    if (0 <= mark_u < image.width and 0 <= mark_v < image.height and
                            dx * dx + dy * dy <= 16):
                        pixel_index = 3 * (mark_v * image.width + mark_u)
                        pixels[pixel_index:pixel_index + 3] = bytes((255, 0, 0))

        output_image = RGBImage(image.width, image.height, bytes(pixels))
        write_ppm(output_dir / f"cam{camera_number:02d}_two_light_bonus.ppm", output_image)


def main() -> None:
    parser = argparse.ArgumentParser(description="Voxel-based visual-hull reconstruction")
    parser.add_argument("--true-color", action="store_true",
                        help="run the full visibility-aware true-color pass with progress")
    parser.add_argument("--bonus", action="store_true",
                        help="render the two-light shadow bonus images")
    args = parser.parse_args()

    # Step 1: define the voxel grid.
    grid = define_voxel_grid()
    print(f"Grid: {grid.shape[0]} x {grid.shape[1]} x {grid.shape[2]} = "
          f"{grid.total_voxels} voxels")
    print(f"Voxel dimensions: {grid.dx:.3f} x {grid.dy:.3f} x "
          f"{grid.dz:.3f} meters")
    print(f"Occupancy storage: {len(grid.occupied) / 2**20:.2f} MiB")
    dataset_dir = Path(__file__).resolve().parent.parent / "cs532_HW03"

    # Step 2: carve the grid using all eight silhouettes.
    occupied_count, occupied_fraction = compute_visual_hull(grid, dataset_dir)
    print(f"Visual-hull occupied voxels: {occupied_count}")
    print(f"Visual-hull fraction: {occupied_fraction:.6f}")

    # Step 3: find occupied voxels with an empty six-connected neighbor.
    surface, surface_count, surface_fraction = find_surface_voxels(grid)
    print(f"Surface voxels: {surface_count}")
    print(f"Surface fraction of full grid: {surface_fraction:.6f}")

    # Step 4: turn exposed voxel faces into the point-cloud geometry.
    points = generate_output_geometry(grid, surface)
    print(f"Exposed face-center points: {len(points)}")

    # Step 5: color points by their normalized world-space coordinates.
    false_colored_points = assign_false_colors(points)

    # Step 6: write the false-color ASCII PLY.
    ply_path = Path(__file__).resolve().parent / "visual_hull_false_color.ply"
    write_ascii_ply(ply_path, false_colored_points)
    print(f"Wrote false-color PLY: {ply_path.name} "
          f"({len(false_colored_points)} vertices)")
    # Step 7: assign true colors using foreground and visibility checks.
    # This is optional at the command line because the ray casting is slower.
    if args.true_color:
        true_colored_points, fallback_count = assign_true_colors(
            grid, points, dataset_dir, show_progress=True
        )
        true_ply_path = Path(__file__).resolve().parent / "visual_hull_true_color.ply"

        # Step 8: write the true-color ASCII PLY.
        write_ascii_ply(true_ply_path, true_colored_points)
        print(f"True-color pass complete: {len(true_colored_points)} vertices; "
              f"{fallback_count} neutral-gray fallback points.")
        print(f"Wrote true-color PLY: {true_ply_path.name} "
              f"({len(true_colored_points)} vertices)")

    # Step 9 bonus: project approximate two-light shadow and relighting effects.
    if args.bonus:
        bonus_dir = Path(__file__).resolve().parent / "two_light_bonus"
        render_two_light_bonus(points, grid, dataset_dir, bonus_dir)
        print(f"Wrote two-light bonus images to: {bonus_dir}")


if __name__ == "__main__":
    main()
