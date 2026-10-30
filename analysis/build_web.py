"""Phase 8 - Build the single-file web page from the template + data.json + district shapes.

Usage: python3 -I analysis/build_web.py
Output: output/web/index.html (self-contained; the poster is the same page with ?poster)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "output/web"

def slim_geo():
    """Round to 3 decimals (~100 m) and drop repeated points: same shapes, a third of the bytes."""
    g = json.load(open(ROOT / "assets/geo/rwa_adm2.geojson"))
    def ring(r):
        out = []
        for x, y in r:
            p = [round(x, 3), round(y, 3)]
            if not out or out[-1] != p:
                out.append(p)
        return out
    def orient(r, cw):
        area = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(r, r[1:]))  # >0 = counter-clockwise
        return r[::-1] if (area > 0) == cw else r
    feats = []
    for f in g["features"]:
        geom = f["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        # d3 wants exterior rings clockwise (GeoJSON spec says counter-clockwise), else it fills the globe.
        polys = [[orient(ring(r), cw=(k == 0)) for k, r in enumerate(poly)] for poly in polys]
        feats.append({"type": "Feature", "properties": {"name": f["properties"]["shapeName"]},
                      "geometry": {"type": "MultiPolygon", "coordinates": polys}})
    assert len(feats) == 30
    return {"type": "FeatureCollection", "features": feats}

def main():
    data = json.load(open(WEB / "data.json"))
    data["geo"] = slim_geo()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (WEB / "template.html").read_text().replace("/*__DATA__*/null", blob)
    assert "/*__DATA__*/" not in html, "data placeholder not replaced"
    (WEB / "index.html").write_text(html)
    print(f"output/web/index.html written ({len(html)//1024} KB)")

if __name__ == "__main__":
    main()
