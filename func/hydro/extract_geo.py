#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-10-17T15:10:01
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this functions without the author's permission

import shutil

import networkx as nx

import rasterio
import geopandas as gpd

from shapely.geometry import Point, LineString
from shapely.ops import linemerge, substring

from whitebox import WhiteboxTools

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion


def extract_main_channel(
    channel_path,
    snapped_outlet_path,
    raw_stream_path,
    main_df_channel_path,
    dem_crs,
    extend_m=5000,
):

    # (1) read all streams inside the catchment, one row per segment
    streams = gpd.read_file(channel_path).explode(index_parts=False)
    outlet = gpd.read_file(snapped_outlet_path).geometry.iloc[0]

    # (2) graph: node = segment end point, edge = segment
    G = nx.Graph()
    for g in streams.geometry:
        G.add_edge(g.coords[0][:2], g.coords[-1][:2], length=g.length, geom=g)

    # (3) longest path from the outlet to the farthest head
    outlet_node = min(G.nodes, key=lambda n: Point(n).distance(outlet))  # type: ignore
    dist = nx.single_source_dijkstra_path_length(G, outlet_node, weight="length")
    head_node = max(dist, key=dist.get)  # type: ignore
    path = nx.shortest_path(G, head_node, outlet_node, weight="length")

    # (4) join the segments into one line, ordered head -> outlet
    line = linemerge([G[u][v]["geom"] for u, v in zip(path[:-1], path[1:])])
    if Point(line.coords[0]).distance(outlet) < Point(line.coords[-1]).distance(outlet):  # type: ignore
        line = LineString(line.coords[::-1])

    gpd.GeoDataFrame(geometry=[line], crs=dem_crs).to_file(main_df_channel_path)

    # (5) extend the main channel by extend_m metres below the outlet, using the raw streams
    # work in UTM, because extend_m is in metres and the DEM may be in degrees
    raw = gpd.read_file(raw_stream_path).set_crs(dem_crs, allow_override=True)
    utm_crs = raw.estimate_utm_crs()

    raw = raw.to_crs(utm_crs).explode(index_parts=False)
    line_utm = gpd.GeoSeries([line], crs=dem_crs).to_crs(utm_crs).iloc[0]
    outlet_utm = gpd.GeoSeries([outlet], crs=dem_crs).to_crs(utm_crs).iloc[0]  # type: ignore

    segments = list(raw.geometry)
    starts = {}
    for g in segments:
        starts.setdefault(g.coords[0][:2], []).append(g)

    # the raw segment under the outlet, cut at the outlet and keep the downstream part
    seg = min(segments, key=lambda g: g.distance(outlet_utm))  # type: ignore
    coords = list(substring(seg, seg.project(outlet_utm), seg.length).coords)  # type: ignore

    # follow the raw streams downstream until extend_m is reached
    while LineString(coords).length < extend_m if len(coords) > 1 else True:
        next_segments = starts.get(coords[-1][:2])
        if not next_segments:
            break
        coords = coords + list(next_segments[0].coords)[1:]

    below = substring(LineString(coords), 0, extend_m)
    line_ext = LineString(list(line_utm.coords) + list(below.coords))  # type: ignore

    main_df_channel_path = Path(main_df_channel_path)
    main_df_channel_ext_path = main_df_channel_path.parent / f"main_df_channel_extend_{extend_m}m.shp"
    gpd.GeoDataFrame(geometry=[line_ext], crs=utm_crs).to_file(main_df_channel_ext_path)

    return main_df_channel_path


def geo_extracter(
    dem_path,
    outlet_lon,
    outlet_lat,
    output_dir,
    threshold=500,  # m**2, 500 cell * 30 m * 30 m >> upstream area before a stream begins
    snap_dist=0.001,  # degree, about 1 cell (30 m)
    delete_cache=True,
):

    # region (1) define the tool and the paths
    wbt = WhiteboxTools()
    wbt.verbose = False  # show the prograss bar or not

    # saved file path
    channel_path = Path(output_dir) / "channel.shp"
    channel_path.parent.mkdir(parents=True, exist_ok=True)
    main_df_channel_path = Path(output_dir) / "main_df_channel.shp"

    outlet_path = Path(output_dir) / "outlet.shp"
    catchment_path = Path(output_dir) / "catchment.shp"

    # temp file path
    temp_dir = Path(output_dir) / "temp"

    raw_stream_path = Path(temp_dir) / "raw_streams.shp"
    raw_stream_path.parent.mkdir(parents=True, exist_ok=True)

    snapped_outlet_path = Path(temp_dir) / "snapped_outlet.shp"
    # endregion

    # region (2) make the outlet from outlet_lon, outlet_lat, in the same CRS as the DEM
    with rasterio.open(dem_path) as src:
        dem_crs = src.crs

    outlet = gpd.GeoDataFrame(geometry=[Point(outlet_lon, outlet_lat)], crs="EPSG:4326")  # degree area
    outlet.to_crs(dem_crs).to_file(outlet_path)
    # endregion

    # region (3) fill the sink, flow direction and flow accumulation
    filled_dem_path = temp_dir / "filled_dem.tif"
    filled_dem_path.unlink(missing_ok=True)

    wbt.fill_depressions_wang_and_liu(
        dem=str(dem_path),
        output=str(filled_dem_path),
    )
    if not filled_dem_path.exists():
        raise RuntimeError("DEM filling failed. Check the WhiteboxTools output above.")

    wbt.d8_pointer(
        dem=str(temp_dir / "filled_dem.tif"),
        output=str(temp_dir / "flow_dir.tif"),
    )
    wbt.d8_flow_accumulation(
        i=str(temp_dir / "filled_dem.tif"),
        output=str(temp_dir / "flow_acc.tif"),
        out_type="cells",
    )
    # endregion

    # region (4) extract the streams
    wbt.extract_streams(
        flow_accum=str(temp_dir / "flow_acc.tif"),
        output=str(temp_dir / "streams.tif"),
        threshold=threshold,
    )
    wbt.raster_streams_to_vector(
        streams=str(temp_dir / "streams.tif"),
        d8_pntr=str(temp_dir / "flow_dir.tif"),
        output=str(raw_stream_path),
    )
    # endregion

    # region (5) extract the catchment
    wbt.snap_pour_points(
        pour_pts=str(outlet_path),
        flow_accum=str(temp_dir / "flow_acc.tif"),
        output=str(snapped_outlet_path),
        snap_dist=snap_dist,
    )
    wbt.watershed(
        d8_pntr=str(temp_dir / "flow_dir.tif"),
        pour_pts=str(snapped_outlet_path),
        output=str(temp_dir / "watershed.tif"),
    )
    wbt.raster_to_vector_polygons(
        i=str(temp_dir / "watershed.tif"),
        output=str(catchment_path),
    )
    # endregion

    # region (6) set the crs and overwrite it
    for path in [raw_stream_path, catchment_path, snapped_outlet_path]:
        gpd.read_file(path).set_crs(dem_crs, allow_override=True).to_file(path)
    # endregion

    # region (7) keep only the streams upstream of the snapped outlet
    raw_stream = gpd.read_file(raw_stream_path)
    watershed = gpd.read_file(catchment_path)

    streams = gpd.clip(raw_stream, watershed, keep_geom_type=True)
    # reconnect endpoints separated by tiny coordinate differences
    streams.geometry = streams.geometry.set_precision(1e-8)
    streams = streams[~streams.geometry.is_empty]
    streams.to_file(channel_path)

    # keep the main debris-flow channel
    main_df_channel_path = extract_main_channel(
        channel_path=channel_path,
        snapped_outlet_path=snapped_outlet_path,
        raw_stream_path=raw_stream_path,
        main_df_channel_path=main_df_channel_path,
        dem_crs=dem_crs,
    )
    # endregion

    # region (8) delete the cache
    if delete_cache and temp_dir.exists():
        shutil.rmtree(temp_dir)
    # endregion


def usage():
    # outlet
    outlet_lat, outlet_lon = 46.286520, 7.627125

    dem_path = Path(project_root) / "data/hydro_raw/Illgraben/Illgraben_Copernicus_30m.tif"
    output_dir = Path(project_root) / "data/hydro_cooked/Illgraben"

    geo_extracter(
        dem_path=dem_path,
        outlet_lon=outlet_lon,
        outlet_lat=outlet_lat,
        output_dir=output_dir,
        threshold=500,  # cells, about 0.4 km² at 30 m
        snap_dist=0.001,  # degree, about 100 m
    )
