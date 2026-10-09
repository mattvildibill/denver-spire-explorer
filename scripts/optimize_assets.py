"""Build exact indexed city meshes and a lighter decorative-detail variant.

The geometry path uses only Python's standard library. It consumes the original
``city.bin.gz`` and never modifies that source, world.json, or realism.json.

Binary layout (all offsets are bytes):
    uint32 little-endian padded JSON header length
    UTF-8 JSON header, padded with spaces to a 4-byte boundary
    payload: group vertices followed by that group's uint32 little-endian indices

The existing DENV1 header and stride=9 are retained. Each group's ``offset`` and
``count`` describe its unique interleaved float32 vertices; ``indexOffset`` and
``indexCount`` describe its triangle indices, relative to the same payload start.
The nine float32 attributes are never decoded, rounded, or reconstructed: exact
36-byte records are the deduplication keys, preserving normals, UV seams and AO.
Triangle order, winding, and every attribute bit are preserved for kept groups.

Aerial imagery is managed separately and is never modified by this script.
There are no third-party runtime or build dependencies.
"""

from __future__ import annotations

import argparse
from array import array
from copy import deepcopy
import gzip
import io
import json
from pathlib import Path
import struct
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VERTEX_BYTES = 9 * 4
DECORATIVE_GROUPS = frozenset({
    "Realism sandstone surrounds",
    "Realism anodized aluminium",
    "Realism recessed glazing",
    "Blackened street furniture",
})
INDEX_FIELDS = frozenset({"offset", "count", "indexOffset", "indexCount"})


def _integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def unpack_geometry(raw: bytes) -> tuple[dict, memoryview]:
    """Parse a DENV1 container, validating all vertex/index buffer bounds."""
    if len(raw) < 4:
        raise ValueError("Geometry is missing its header length")
    header_length = struct.unpack_from("<I", raw)[0]
    if header_length % 4 or header_length > len(raw) - 4:
        raise ValueError("Geometry header length is unaligned or out of bounds")
    try:
        header = json.loads(raw[4:4 + header_length])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Geometry has an invalid JSON header") from error
    if not isinstance(header, dict) or header.get("format") != "DENV1" or header.get("stride") != 9:
        raise ValueError("Expected DENV1 geometry with interleaved stride 9")
    if not isinstance(header.get("groups"), list):
        raise ValueError("Geometry header must contain a groups list")
    payload = memoryview(raw)[4 + header_length:]
    for group in header["groups"]:
        if not isinstance(group, dict):
            raise ValueError("Every geometry group must be an object")
        name = group.get("name", "unnamed group")
        offset = _integer(group.get("offset"), f"{name} offset")
        count = _integer(group.get("count"), f"{name} count")
        if offset % 4 or offset + count * VERTEX_BYTES > len(payload):
            raise ValueError(f"{name} vertex buffer is unaligned or out of bounds")
        indexed = "indexOffset" in group or "indexCount" in group
        if indexed:
            index_offset = _integer(group.get("indexOffset"), f"{name} indexOffset")
            index_count = _integer(group.get("indexCount"), f"{name} indexCount")
            if index_offset % 4 or index_offset + index_count * 4 > len(payload):
                raise ValueError(f"{name} index buffer is unaligned or out of bounds")
            if index_count % 3:
                raise ValueError(f"{name} index count is not a triangle list")
        elif count % 3:
            raise ValueError(f"{name} vertex count is not a triangle list")
    return header, payload


def pack_geometry(header: dict, payload: bytes | bytearray) -> bytes:
    encoded = json.dumps(header, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    return struct.pack("<I", len(encoded)) + encoded + payload


def indexed_variants(raw: bytes) -> tuple[bytes, bytes]:
    """Index the source once, assembling full and explicitly filtered variants."""
    header, source = unpack_geometry(raw)
    if any("indexOffset" in group for group in header["groups"]):
        raise ValueError("The optimizer requires the original nonindexed city.bin.gz")
    full_header, light_header = deepcopy(header), deepcopy(header)
    full_header["groups"], light_header["groups"] = [], []
    full_payload, light_payload = bytearray(), bytearray()

    for group in header["groups"]:
        vertices = bytearray()
        indices = array("I")
        if indices.itemsize != 4:
            raise RuntimeError("This Python platform does not provide 32-bit unsigned arrays")
        seen: dict[bytes, int] = {}
        start = group["offset"]
        stop = start + group["count"] * VERTEX_BYTES
        for offset in range(start, stop, VERTEX_BYTES):
            record = bytes(source[offset:offset + VERTEX_BYTES])
            index = seen.get(record)
            if index is None:
                index = len(seen)
                if index >= 2**32:
                    raise ValueError("A geometry group exceeds the uint32 index range")
                seen[record] = index
                vertices.extend(record)
            indices.append(index)
        if sys.byteorder != "little":
            indices.byteswap()
        index_bytes = indices.tobytes()

        targets = [(full_header, full_payload)]
        if group.get("name") not in DECORATIVE_GROUPS:
            targets.append((light_header, light_payload))
        for target_header, target_payload in targets:
            indexed_group = deepcopy(group)
            indexed_group.update(
                offset=len(target_payload),
                count=len(seen),
                indexOffset=len(target_payload) + len(vertices),
                indexCount=group["count"],
            )
            target_header["groups"].append(indexed_group)
            target_payload.extend(vertices)
            target_payload.extend(index_bytes)

    return pack_geometry(full_header, full_payload), pack_geometry(light_header, light_payload)


def verify_equivalence(original: bytes, indexed: bytes, omitted_groups: frozenset[str] = frozenset()) -> dict:
    """Check every kept triangle attribute byte and all non-layout metadata."""
    source_header, source = unpack_geometry(original)
    target_header, target = unpack_geometry(indexed)
    if any("indexOffset" in group for group in source_header["groups"]):
        raise ValueError("Verification requires a nonindexed source")
    if {key: value for key, value in source_header.items() if key != "groups"} != {
        key: value for key, value in target_header.items() if key != "groups"
    }:
        raise ValueError("Top-level geometry metadata changed")
    expected = [group for group in source_header["groups"] if group.get("name") not in omitted_groups]
    if len(expected) != len(target_header["groups"]):
        raise ValueError("The optimized geometry has the wrong groups")
    checked_vertices = 0
    for original_group, group in zip(expected, target_header["groups"]):
        metadata = lambda item: {key: value for key, value in item.items() if key not in INDEX_FIELDS}
        if metadata(original_group) != metadata(group):
            raise ValueError("Group order or material metadata changed")
        if group.get("indexCount") != original_group["count"]:
            raise ValueError(f"{group.get('name')} triangle count changed")
        index_offset = group["indexOffset"]
        index_data = target[index_offset:index_offset + group["indexCount"] * 4]
        for position, (index,) in enumerate(struct.iter_unpack("<I", index_data)):
            if index >= group["count"]:
                raise ValueError(f"{group.get('name')} has an out-of-range index")
            original_offset = original_group["offset"] + position * VERTEX_BYTES
            target_offset = group["offset"] + index * VERTEX_BYTES
            if source[original_offset:original_offset + VERTEX_BYTES] != target[target_offset:target_offset + VERTEX_BYTES]:
                raise ValueError(f"{group.get('name')} triangle attribute bytes changed at vertex {position}")
        checked_vertices += original_group["count"]
    return {"groups": len(expected), "triangle_vertices": checked_vertices, "triangles": checked_vertices // 3}


def deterministic_gzip(raw: bytes) -> bytes:
    buffer = io.BytesIO()
    # GzipFile fixes MTIME and omits both source filenames and platform OS bytes.
    with gzip.GzipFile(filename="", fileobj=buffer, mode="wb", compresslevel=9, mtime=0) as stream:
        stream.write(raw)
    return buffer.getvalue()


def _write_atomic(path: Path, data: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _statistics(raw: bytes, compressed_bytes: int) -> dict:
    header, payload = unpack_geometry(raw)
    return {
        "groups": len(header["groups"]),
        "vertices": sum(group["count"] for group in header["groups"]),
        "triangles": sum(group.get("indexCount", group["count"]) for group in header["groups"]) // 3,
        "payload_bytes": len(payload),
        "decoded_bytes": len(raw),
        "compressed_bytes": compressed_bytes,
    }


def build_assets(data_dir: Path = ROOT / "data") -> dict:
    compressed_source = (data_dir / "city.bin.gz").read_bytes()
    source = gzip.decompress(compressed_source)
    full, light = indexed_variants(source)
    # Verify before publishing either file; this is intentionally part of builds.
    verified = {
        "full": verify_equivalence(source, full),
        "light": verify_equivalence(source, light, DECORATIVE_GROUPS),
    }
    report = {"source": _statistics(source, len(compressed_source))}
    for name, raw in (("city-indexed.bin.gz", full), ("city-light.bin.gz", light)):
        compressed = deterministic_gzip(raw)
        _write_atomic(data_dir / name, compressed)
        report[name] = _statistics(raw, len(compressed))
    header, _ = unpack_geometry(source)
    report["omitted_light_groups"] = [group["name"] for group in header["groups"] if group.get("name") in DECORATIVE_GROUPS]
    report["verified"] = verified
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    print(json.dumps(build_assets(args.data_dir), indent=2))


if __name__ == "__main__":
    main()
