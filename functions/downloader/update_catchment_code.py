#!/usr/bin/python
# -*- coding: UTF-8 -*-

#__modification time__ = 2025-09-08
#__author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
#__find me__ = qi.zhou@gfz-potsdam.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd
# Please do not distribute this code without the author's permission

import geojson
import pandas as pd
import numpy as np

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>



def catchment_code(project_root):

    df = pd.read_csv(f"{project_root}/data/event_catalog/Flow_Bench_Catalog_work.txt", header=0)

    features = []
    for _, row in df.iterrows():
        feature = geojson.Feature(
            geometry=geojson.Point((row['Longitude_sta'], row['Latitude'])),
            properties={
                "Catchment": row['Catchment'],
                "Client": row['Client'],
                "Network": row['Network'],
                "Station": row['Station'],
                "Component": row['Component']
            }
        )
        features.append(feature)

    feature_collection = geojson.FeatureCollection(features)

    # Write to data.geojson
    with open(f"{project_root}/docs/data1.geojson", "w", encoding="utf-8") as f:
        geojson.dump(feature_collection, f, ensure_ascii=False, indent=2)

    print("data.geojson successfully created!")

catchment_code(project_root)