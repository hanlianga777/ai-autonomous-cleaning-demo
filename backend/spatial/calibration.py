"""Four-point image-to-SLAM homography mapping without external dependencies."""

from __future__ import annotations

from spatial.spatial_data import CAMERAS


class CalibrationError(ValueError):
    pass


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting for the 8×8 homography system."""
    size = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-10:
            raise CalibrationError("Calibration points are degenerate")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [value - factor * pivot_value for value, pivot_value in zip(augmented[row], augmented[column])]
    return [augmented[row][-1] for row in range(size)]


def _homography(points: list[dict]) -> list[float]:
    if len(points) != 4:
        raise CalibrationError("Exactly four calibration points are required")
    matrix: list[list[float]] = []
    vector: list[float] = []
    for point in points:
        u, v = point["pixel"]["u"], point["pixel"]["v"]
        x, y = point["slam"]["x"], point["slam"]["y"]
        matrix += [[u, v, 1, 0, 0, 0, -u * x, -v * x], [0, 0, 0, u, v, 1, -u * y, -v * y]]
        vector += [x, y]
    return _solve_linear_system(matrix, vector)


def map_pixel_to_slam(camera_id: str, u: float, v: float) -> dict:
    camera = next((item for item in CAMERAS if item["camera_id"] == camera_id), None)
    if camera is None:
        raise CalibrationError("Unknown camera")
    if not camera["calibration_points"]:
        raise CalibrationError("Camera has no calibration points in Phase 2")
    h11, h12, h13, h21, h22, h23, h31, h32 = _homography(camera["calibration_points"])
    denominator = h31 * u + h32 * v + 1
    if abs(denominator) < 1e-10:
        raise CalibrationError("Mapped point is at infinity")
    x = (h11 * u + h12 * v + h13) / denominator
    y = (h21 * u + h22 * v + h23) / denominator
    return {"camera_id": camera_id, "pixel": {"u": u, "v": v}, "location": {"building": camera["building"], "floor": camera["floor"], "zone": camera["zone"], "x": round(x, 3), "y": round(y, 3)}}
