"""Voxel reconstruction for CS 532 Homework 3.

Step 1 is implemented: define the assignment's metric voxel grid. Subsequent
steps will add camera/silhouette carving, surface extraction, color fusion, and
ASCII PLY export.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re
import struct
import time
import zlib


@dataclass(frozen=True)
class VoxelGrid:
    """World-space grid metadata and an initially empty occupancy volume."""

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


@dataclass(frozen=True)
class BinarySilhouette:
    """A Netpbm P4 bitmap; foreground pixels are black (bit value 1)."""

    width: int
    height: int
    row_bytes: int
    pixels: bytes

    def is_foreground(self, x: int, y: int) -> bool:
        byte_index = y * self.row_bytes + x // 8
        bit_mask = 1 << (7 - (x % 8))
        return bool(self.pixels[byte_index] & bit_mask)


@dataclass(frozen=True)
class SurfacePoint:
    """An exposed voxel-face center, its outward normal, and source voxel."""

    x: float
    y: float
    z: float
    normal: tuple[int, int, int]
    voxel: tuple[int, int, int]


@dataclass(frozen=True)
class ColoredPoint:
    """A point-cloud vertex with unsigned-byte RGB color."""

    x: float
    y: float
    z: float
    red: int
    green: int
    blue: int


@dataclass(frozen=True)
class RGBImage:
    width: int
    height: int
    pixels: bytes

    def rgb(self, x: int, y: int) -> tuple[int, int, int]:
        index = 3 * (y * self.width + x)
        return self.pixels[index], self.pixels[index + 1], self.pixels[index + 2]


def define_voxel_grid(voxel_size_m: float = 0.05) -> VoxelGrid:
    """Create the required [-2.5,2.5] x [-3,3] x [0,2.5] meter grid.

    A 5 cm isotropic spacing produces a 100 x 120 x 50 grid (600,000 voxels).
    Centers are stored as three 1D arrays so no full coordinate tensor is
    allocated until a later reconstruction step truly needs one.
    """
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
    """Load the 12 whitespace-delimited camera values from the XML wrapper."""
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
    """Read one P4 header token, skipping whitespace and # comments."""
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
    """Load a raw PBM (P4) silhouette using only the Python standard library."""
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
    """Load the supplied non-interlaced 8-bit RGB PNGs without dependencies."""
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
    """Project a world point, returning (u_tilde, v_tilde, w_tilde)."""
    p = (x, y, z, 1.0)
    return tuple(sum(row[k] * p[k] for k in range(4)) for row in matrix)


def camera_center(matrix: tuple[tuple[float, ...], ...]) -> tuple[float, float, float]:
    """Solve (C=-M^{-1}p_4) for a camera matrix (P=[M|p_4])."""
    a,b,c = matrix[0][:3]; d,e,f = matrix[1][:3]; g,h,i = matrix[2][:3]
    det = a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
    if abs(det) < 1e-12: raise ValueError("Singular camera matrix")
    inv = ((e*i-f*h, c*h-b*i, b*f-c*e), (f*g-d*i, a*i-c*g, c*d-a*f), (d*h-e*g, b*g-a*h, a*e-b*d))
    q = (-matrix[0][3], -matrix[1][3], -matrix[2][3])
    return tuple(sum(inv[row][k]*q[k] for k in range(3))/det for row in range(3))


def ray_is_unoccluded(grid: VoxelGrid, point: SurfacePoint, camera: tuple[float, float, float]) -> bool:
    """Use 3D DDA over the point-to-camera segment, excluding source voxel."""
    eps = 1e-6
    ox, oy, oz = point.x + eps*point.normal[0], point.y + eps*point.normal[1], point.z + eps*point.normal[2]
    dx, dy, dz = camera[0]-ox, camera[1]-oy, camera[2]-oz
    t0, t1 = 0.0, 1.0
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
    for index, position, direction, low, size in ((ix,px,dx,grid.xmin,grid.dx),(iy,py,dy,grid.ymin,grid.dy),(iz,pz,dz,grid.zmin,grid.dz)):
        if direction > 0: steps.append(1); next_t.append(t + (low+(index+1)*size-position)/direction); delta_t.append(size/direction)
        elif direction < 0: steps.append(-1); next_t.append(t + (low+index*size-position)/direction); delta_t.append(-size/direction)
        else: steps.append(0); next_t.append(float('inf')); delta_t.append(float('inf'))
    # A segment can cross at most Nx + Ny + Nz cells; the cap also protects
    # against a numerical tie at a voxel corner causing an endless DDA loop.
    for _ in range(grid.nx + grid.ny + grid.nz + 3):
        if t > t1:
            break
        if (ix,iy,iz) != point.voxel and grid.occupied[voxel_index(grid,ix,iy,iz)]: return False
        axis = min(range(3), key=lambda k: next_t[k]); t = next_t[axis]; next_t[axis] += delta_t[axis]
        if axis == 0: ix += steps[0]
        elif axis == 1: iy += steps[1]
        else: iz += steps[2]
        if ix<0 or ix>=grid.nx or iy<0 or iy>=grid.ny or iz<0 or iz>=grid.nz: break
    return True


def assign_true_colors(grid: VoxelGrid, points: list[SurfacePoint], dataset_dir: Path,
                       show_progress: bool = False) -> tuple[list[ColoredPoint], int]:
    """Median-fuse only foreground, unoccluded camera samples for each point."""
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
            u,v=int(ut/wt+0.5),int(vt/wt+0.5)
            if u<0 or u>=image.width or v<0 or v>=image.height or not silhouette.is_foreground(u,v): continue
            if ray_is_unoccluded(grid,point,camera): samples.append(image.rgb(u,v))
        if samples:
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
    """Carve ``grid`` against all eight calibrated binary silhouettes."""
    matrices = [load_projection_matrix(dataset_dir / "calibration" / f"cam{i:02d}.xml")
                for i in range(8)]
    silhouettes = [load_p4_pbm(dataset_dir / f"silh_cam{i:02d}_00023_0000008550.pbm")
                   for i in range(8)]

    occupied_count = 0
    linear_index = 0
    for z in grid.z_centers:
        for y in grid.y_centers:
            for x in grid.x_centers:
                keep = True
                for matrix, silhouette in zip(matrices, silhouettes):
                    u_tilde, v_tilde, w_tilde = project_point(matrix, x, y, z)
                    if w_tilde <= 0:
                        keep = False
                        break
                    # MATLAB/Python image arrays are zero-indexed after loading.
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
    """Return the x-fastest flat occupancy index for a valid voxel index."""
    return ix + grid.nx * (iy + grid.ny * iz)


def find_surface_voxels(grid: VoxelGrid) -> tuple[bytearray, int, float]:
    """Mark occupied voxels with at least one empty 6-connected neighbor."""
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
    """Create one output point for every exposed face of a surface voxel."""
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
                        points.append(SurfacePoint(
                            x=cx + dx * grid.dx / 2,
                            y=cy + dy * grid.dy / 2,
                            z=cz + dz * grid.dz / 2,
                            normal=(dx, dy, dz),
                            voxel=(ix, iy, iz),
                        ))
    return points


def _coordinate_channel(value: float, low: float, high: float) -> int:
    """Map a coordinate to [0, 255], including a zero-range safeguard."""
    if high == low:
        return 128
    return max(0, min(255, round(255 * (value - low) / (high - low))))


def assign_false_colors(points: list[SurfacePoint]) -> list[ColoredPoint]:
    """Color output geometry with normalized world X, Y, and Z coordinates."""
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
    """Write RGB point vertices in the assignment's required ASCII PLY format."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--true-color", action="store_true",
                        help="run the full visibility-aware true-color pass with progress")
    args = parser.parse_args()
    grid = define_voxel_grid()
    print(f"Grid: {grid.shape[0]} x {grid.shape[1]} x {grid.shape[2]} = "
          f"{grid.total_voxels} voxels")
    print(f"Voxel dimensions: {grid.dx:.3f} x {grid.dy:.3f} x "
          f"{grid.dz:.3f} meters")
    print(f"Occupancy storage: {len(grid.occupied) / 2**20:.2f} MiB")
    dataset_dir = Path(__file__).resolve().parent.parent / "cs532_HW03"
    occupied_count, occupied_fraction = compute_visual_hull(grid, dataset_dir)
    print(f"Visual-hull occupied voxels: {occupied_count}")
    print(f"Visual-hull fraction: {occupied_fraction:.6f}")
    surface, surface_count, surface_fraction = find_surface_voxels(grid)
    print(f"Surface voxels: {surface_count}")
    print(f"Surface fraction of full grid: {surface_fraction:.6f}")
    points = generate_output_geometry(grid, surface)
    print(f"Exposed face-center points: {len(points)}")
    false_colored_points = assign_false_colors(points)
    ply_path = Path(__file__).resolve().parent / "visual_hull_false_color.ply"
    write_ascii_ply(ply_path, false_colored_points)
    print(f"Wrote false-color PLY: {ply_path.name} "
          f"({len(false_colored_points)} vertices)")
    # Step 7 is intentionally exposed as assign_true_colors(...), rather than
    # run by default, because ray casting every point to every camera is slow.
    if args.true_color:
        true_colored_points, fallback_count = assign_true_colors(
            grid, points, dataset_dir, show_progress=True
        )
        print(f"True-color pass complete: {len(true_colored_points)} vertices; "
              f"{fallback_count} neutral-gray fallback points.")


if __name__ == "__main__":
    main()
