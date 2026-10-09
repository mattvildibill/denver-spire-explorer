"""Focused optimizer tests: python scripts/test_optimize_assets.py."""

from copy import deepcopy
import gzip
from pathlib import Path
import struct
import tempfile
import unittest

import optimize_assets as optimizer


def vertex(*, normal=(0.0, 1.0, 0.0), uv=(0.0, 0.0), ao=1.0, x=0.0):
    return struct.pack("<9f", x, 0.0, 0.0, *normal, *uv, ao)


def fixture(groups):
    header = {
        "format": "DENV1", "stride": 9,
        "ambient_visibility": "Original AO provenance",
        "world": {"origin": [-104.99, 39.74], "nested": [1, 2, 3]},
        "groups": [],
    }
    payload = bytearray()
    for name, vertices in groups:
        header["groups"].append({
            "name": name, "offset": len(payload), "count": len(vertices),
            "color": [0.1, 0.2, 0.3], "metal": 0.25, "rough": 0.75,
            "aerial": True, "aerial_mix": 0.5, "surface_base": [0.1, 0.2, 0.3],
            "custom": {"preserve": "all metadata"},
        })
        payload.extend(b"".join(vertices))
    return optimizer.pack_geometry(header, payload)


class GeometryTests(unittest.TestCase):
    def test_exact_record_deduplication_and_triangle_order(self):
        a, b, c = vertex(), vertex(x=1), vertex(x=2)
        source = fixture([("SPIRE", [a, b, c, c, b, a])])
        full, light = optimizer.indexed_variants(source)
        self.assertEqual(full, light)
        header, payload = optimizer.unpack_geometry(full)
        group = header["groups"][0]
        self.assertEqual(group["count"], 3)
        self.assertEqual(group["indexCount"], 6)
        self.assertEqual(group["indexOffset"], 108)
        self.assertEqual(struct.unpack_from("<6I", payload, group["indexOffset"]), (0, 1, 2, 2, 1, 0))
        self.assertEqual(optimizer.verify_equivalence(source, full)["triangles"], 2)

    def test_normal_uv_ao_and_signed_zero_seams_are_not_merged(self):
        vertices = [
            vertex(), vertex(normal=(1, 0, 0)), vertex(uv=(0.5, 0.25)),
            vertex(ao=0.5), vertex(x=-0.0), vertex(),
        ]
        source = fixture([("seams", vertices)])
        full, _ = optimizer.indexed_variants(source)
        header, _ = optimizer.unpack_geometry(full)
        self.assertEqual(header["groups"][0]["count"], 5)
        optimizer.verify_equivalence(source, full)

    def test_nan_payload_bits_are_preserved(self):
        original = bytearray(vertex())
        original[-4:] = struct.pack("<I", 0x7FC00001)
        other = bytearray(original)
        other[-4:] = struct.pack("<I", 0x7FC00002)
        source = fixture([("bit patterns", [bytes(original), bytes(other), bytes(original)])])
        full, _ = optimizer.indexed_variants(source)
        self.assertEqual(optimizer.unpack_geometry(full)[0]["groups"][0]["count"], 2)
        optimizer.verify_equivalence(source, full)

    def test_light_omits_only_exact_decorative_names_and_keeps_order(self):
        names = ["SPIRE fine glazing and mullions", *sorted(optimizer.DECORATIVE_GROUPS),
                 "Realism wall masonry", "Realism curb concrete", "Realism sandstone surrounds extra"]
        source = fixture([(name, [vertex()] * 3) for name in names])
        full, light = optimizer.indexed_variants(source)
        self.assertEqual(len(optimizer.unpack_geometry(full)[0]["groups"]), len(names))
        kept = [group["name"] for group in optimizer.unpack_geometry(light)[0]["groups"]]
        self.assertEqual(kept, [name for name in names if name not in optimizer.DECORATIVE_GROUPS])
        optimizer.verify_equivalence(source, full)
        optimizer.verify_equivalence(source, light, optimizer.DECORATIVE_GROUPS)

    def test_top_level_and_material_metadata_are_unchanged(self):
        source = fixture([("déjà 🏙", [vertex()] * 3), ("empty", [])])
        full, _ = optimizer.indexed_variants(source)
        original_header, _ = optimizer.unpack_geometry(source)
        header, payload = optimizer.unpack_geometry(full)
        self.assertEqual({k: v for k, v in original_header.items() if k != "groups"},
                         {k: v for k, v in header.items() if k != "groups"})
        self.assertEqual(header["groups"][0]["custom"], original_header["groups"][0]["custom"])
        self.assertEqual(header["groups"][1]["count"], 0)
        self.assertEqual(header["groups"][1]["indexCount"], 0)
        self.assertEqual((len(full) - len(payload)) % 4, 0)
        optimizer.verify_equivalence(source, full)

    def test_deduplication_is_scoped_to_material_group(self):
        source = fixture([("first", [vertex()] * 3), ("second", [vertex()] * 3)])
        full, _ = optimizer.indexed_variants(source)
        header, payload = optimizer.unpack_geometry(full)
        self.assertEqual([group["count"] for group in header["groups"]], [1, 1])
        self.assertEqual([group["offset"] for group in header["groups"]], [0, 48])
        for group in header["groups"]:
            self.assertEqual(group["offset"] % 4, 0)
            self.assertEqual(group["indexOffset"] % 4, 0)
            self.assertEqual(struct.unpack_from("<3I", payload, group["indexOffset"]), (0, 0, 0))

    def test_deterministic_gzip_has_no_timestamp_or_filename(self):
        raw = fixture([("first", [vertex()] * 3)])
        one = optimizer.deterministic_gzip(raw)
        self.assertEqual(one, optimizer.deterministic_gzip(raw))
        self.assertEqual(one[3], 0)
        self.assertEqual(one[4:8], b"\0" * 4)
        self.assertEqual(gzip.decompress(one), raw)

    def test_corruption_is_detected(self):
        source = fixture([("first", [vertex()] * 3)])
        full, _ = optimizer.indexed_variants(source)
        header, payload = optimizer.unpack_geometry(full)
        changed = bytearray(payload)
        changed[0] ^= 1
        with self.assertRaisesRegex(ValueError, "attribute bytes changed"):
            optimizer.verify_equivalence(source, optimizer.pack_geometry(header, changed))
        changed = bytearray(payload)
        struct.pack_into("<I", changed, header["groups"][0]["indexOffset"], 10)
        with self.assertRaisesRegex(ValueError, "out-of-range index"):
            optimizer.verify_equivalence(source, optimizer.pack_geometry(header, changed))
        changed_header = deepcopy(header)
        changed_header["groups"][0]["rough"] = 0
        with self.assertRaisesRegex(ValueError, "metadata changed"):
            optimizer.verify_equivalence(source, optimizer.pack_geometry(changed_header, payload))
        changed_header = deepcopy(header)
        changed_header["world"]["origin"][0] = 0
        with self.assertRaisesRegex(ValueError, "metadata changed"):
            optimizer.verify_equivalence(source, optimizer.pack_geometry(changed_header, payload))

    def test_malformed_input_is_rejected(self):
        source = fixture([("first", [vertex()] * 3)])
        header, payload = optimizer.unpack_geometry(source)
        cases = [b"", struct.pack("<I", 999999), struct.pack("<I", 3) + b"   ",
                 struct.pack("<I", 4) + b"oops"]
        for key, value in (("offset", -1), ("offset", 1), ("offset", 999999),
                           ("count", 4), ("count", True)):
            altered = deepcopy(header)
            altered["groups"][0][key] = value
            cases.append(optimizer.pack_geometry(altered, payload))
        for bad in cases:
            with self.subTest(bad=bad[:40]), self.assertRaises(ValueError):
                optimizer.indexed_variants(bad)
        indexed, _ = optimizer.indexed_variants(source)
        with self.assertRaisesRegex(ValueError, "original nonindexed"):
            optimizer.indexed_variants(indexed)

    def test_build_is_reproducible_and_never_modifies_sources(self):
        source = fixture([("structural", [vertex()] * 3),
                          ("Blackened street furniture", [vertex()] * 3)])
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            original = optimizer.deterministic_gzip(source)
            (data_dir / "city.bin.gz").write_bytes(original)
            (data_dir / "world.json").write_text('{"untouched":true}')
            first = optimizer.build_assets(data_dir)
            outputs = {name: (data_dir / name).read_bytes() for name in ("city-indexed.bin.gz", "city-light.bin.gz")}
            second = optimizer.build_assets(data_dir)
            self.assertEqual(first, second)
            self.assertEqual(first["city-light.bin.gz"]["triangles"], 1)
            self.assertEqual(first["verified"]["full"]["triangle_vertices"], 6)
            self.assertEqual((data_dir / "city.bin.gz").read_bytes(), original)
            self.assertEqual((data_dir / "world.json").read_text(), '{"untouched":true}')
            for name, content in outputs.items():
                self.assertEqual((data_dir / name).read_bytes(), content)



if __name__ == "__main__":
    unittest.main(verbosity=2)
