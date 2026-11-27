"""Build the recycling directory from a Geofabrik India PBF using pyosmium."""

import argparse
import json
from pathlib import Path

import osmium

from backend.locator import MATERIAL_TAGS


class Recycling(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.centers = []
        self.ways = {}
        self.relations = {}

    @staticmethod
    def matches(tags):
        return tags.get("amenity") == "recycling" or tags.get("recycling_type") == "centre"

    def save(self, kind, key, tags, lat, lon):
        if tags.get("access") in {"private", "no"}:
            return
        self.centers.append(
            {
                "id": f"osm-{kind}-{key}",
                "name": tags.get("name")
                or ("Recycling center" if tags.get("recycling_type") == "centre" else "Recycling drop-off"),
                "lat": lat,
                "lon": lon,
                "materials": [
                    name
                    for name, variants in MATERIAL_TAGS.items()
                    if any(tags.get(f"recycling:{tag}") == "yes" for tag in variants)
                ],
                "source": "OpenStreetMap",
                "url": f"https://www.openstreetmap.org/{kind}/{key}",
            }
        )

    def node(self, node):
        if self.matches(node.tags) and node.location.valid():
            self.save("node", node.id, node.tags, node.location.lat, node.location.lon)

    def way(self, way):
        if self.matches(way.tags):
            self.ways[way.id] = (dict(way.tags), [node.ref for node in way.nodes])

    def relation(self, relation):
        if self.matches(relation.tags) and relation.tags.get("type") == "multipolygon":
            self.relations[relation.id] = (
                dict(relation.tags),
                [member.ref for member in relation.members if member.type == "w" and member.role == "outer"],
            )


class OuterWays(osmium.SimpleHandler):
    def __init__(self, ids):
        super().__init__()
        self.ids = ids
        self.refs = {}

    def way(self, way):
        if way.id in self.ids:
            self.refs[way.id] = [node.ref for node in way.nodes]


class Coordinates(osmium.SimpleHandler):
    def __init__(self, refs):
        super().__init__()
        self.refs = refs
        self.locations = {}

    def node(self, node):
        if node.id in self.refs and node.location.valid():
            self.locations[node.id] = (node.location.lat, node.location.lon)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pbf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    handler = Recycling()
    handler.apply_file(str(args.pbf))
    outer = OuterWays({ref for _, refs in handler.relations.values() for ref in refs})
    if outer.ids:
        outer.apply_file(str(args.pbf))
    areas = [("way", key, tags, refs) for key, (tags, refs) in handler.ways.items()] + [
        ("relation", key, tags, [node for ref in refs for node in outer.refs.get(ref, [])])
        for key, (tags, refs) in handler.relations.items()
    ]
    coordinates = Coordinates({node for _, _, _, refs in areas for node in refs})
    if coordinates.refs:
        coordinates.apply_file(str(args.pbf))
    for kind, key, tags, refs in areas:
        points = [coordinates.locations[node] for node in refs if node in coordinates.locations]
        if points:
            lat, lon = zip(*points, strict=True)
            handler.save(kind, key, tags, (min(lat) + max(lat)) / 2, (min(lon) + max(lon)) / 2)

    with osmium.io.Reader(str(args.pbf)) as reader:
        date = reader.header().get("osmosis_replication_timestamp")[:10]
    if not date or not handler.centers:
        raise SystemExit("The extract has no snapshot date or recycling listings.")
    snapshot = {"date": date, "centers": sorted(handler.centers, key=lambda center: center["id"])}
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(handler.centers)} listings from {date}")


if __name__ == "__main__":
    main()
