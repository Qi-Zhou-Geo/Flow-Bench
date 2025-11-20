#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = 2026-01-29
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission


import yaml
from pathlib import Path


# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent

# using ".parent" on "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>

project_root = Path(project_root)
yml_path = project_root / Path("config/Flow-Bench-env.yml")
out_path = project_root / Path("config/Flow-Bench-env.txt")


pip_deps = []

with open(yml_path) as f:
    env = yaml.safe_load(f)

for dep in env.get("dependencies", []):
    if isinstance(dep, str):
        name = dep.split("=")[0]

        # Skip non-pip / system packages
        if name.lower() in {"python", "pip", "cuda", "cudatoolkit"}:
            continue

        # Convert conda pinning → pip pinning
        if "=" in dep:
            parts = dep.split("=")
            if len(parts) >= 2:
                pip_deps.append(f"{parts[0]}=={parts[1]}")
            else:
                pip_deps.append(parts[0])
        else:
            pip_deps.append(dep)

    elif isinstance(dep, dict) and "pip" in dep:
        pip_deps.extend(dep["pip"])

# Remove duplicates, keep order
pip_deps = list(dict.fromkeys(pip_deps))

with open(out_path, "w") as f:
    f.write("\n".join(pip_deps))

print(f"Saved {len(pip_deps)} packages → {out_path}")