"""Crops the flow/ diagrams for slides: drops their own title + subtitle and outer whitespace.

Run (from repo root) after python flow/make_flows.py:  python rsp/ppt/crop_flows.py
"""
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "screens"
# fraction of the image height taken by each diagram's title + subtitle
HEADER = {"1_project_flow": 0.165, "2_techstack_flow": 0.098,
          "3_scenario_flow": 0.18, "4_development_flow": 0.18}

for name, frac in HEADER.items():
    im = Image.open(ROOT / "flow" / f"{name}.png").convert("RGB")
    im = im.crop((0, int(im.height * frac), im.width, im.height))
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    pad = 20
    im = im.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0),
                  min(bbox[2] + pad, im.width), min(bbox[3] + pad, im.height)))
    im.save(OUT / f"flow_{name}.png")
    print("saved", OUT / f"flow_{name}.png", im.size)
