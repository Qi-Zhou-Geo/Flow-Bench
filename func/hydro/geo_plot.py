#!/usr/bin/python
# -*- coding: UTF-8 -*-

# __modification time__ = Last modified: 2026-09-25T13:48:36
# __author__ = Qi Zhou, GFZ Helmholtz Centre for Geosciences
# __find me__ = qi.zhou@gfz.de, qi.zhou.geo@gmail.com, https://github.com/Qi-Zhou-Geo
# Please do not distribute this code without the author's permission

import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.ticker import StrMethodFormatter

import geopandas as gpd
import pyogrio


import rasterio
from rasterio.plot import show
from rasterio.vrt import WarpedVRT

# region ### add the sys.path to search for custom modules ###
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent

sys.path.append(str(project_root))
# endregion
from func.hydro.geo_tool import project_dem, point2gpd

plt.rcParams.update(
    {
        "font.size": 7,
        "axes.formatter.limits": (-2, 3),
        "axes.formatter.use_mathtext": True,
    },
)


def plot_catchment(
    projected_dem_path,
    catchment_path,
    channel_path=None,
    ##
    head_path=None,
    snapped_head_path=None,
    ##
    outlet_path=None,
    snapped_outlet_path=None,
    ##
    seismic_sta_path=None,
    ##
    ax=None,
    save_path=None,
    ##
    crs="EPSG:4326",
):

    # rebuild the shapefile’s index file
    pyogrio.set_gdal_config_options({"SHAPE_RESTORE_SHX": "YES"})

    if ax is None:
        fig = plt.figure(figsize=(4, 4))
        gs = gridspec.GridSpec(1, 1, figure=fig)
        ax = plt.subplot(gs[0])
    else:
        fig = ax.figure

    # (1) plot the DEM
    with rasterio.open(projected_dem_path) as src, WarpedVRT(src, crs=crs) as vrt:
        dem_crs = src.crs

        show(
            vrt.read(1, masked=True),
            transform=vrt.transform,
            ax=ax,
            cmap="gist_earth",
        )

    # (2) plot the catchment boundary
    catchment = gpd.read_file(catchment_path)
    if catchment.crs is None:
        catchment = catchment.set_crs(dem_crs)

    catchment = catchment.to_crs(crs)
    catchment.boundary.plot(ax=ax, color="black", linewidth=1, label="Catchment boundary")

    # (3) plot the river network
    if channel_path is not None:
        channel = gpd.read_file(channel_path)

        if channel.crs is None:
            channel = channel.set_crs(dem_crs)

        channel = channel.to_crs(crs)
        # only show the streams within the catchment
        channel = gpd.clip(channel, catchment, keep_geom_type=True)

        channel.plot(ax=ax, color="dodgerblue", linewidth=1)

    # (4) plot the head and outlet points
    points = [
        (head_path, "orange", "x", "Defined head"),
        (snapped_head_path, "limegreen", "^", "Snapped head"),
        (outlet_path, "magenta", "x", "Defined outlet"),
        (snapped_outlet_path, "red", "o", "Snapped outlet"),
        (seismic_sta_path, "C3", "s", "Seismic station"),
    ]

    for file_path, color, marker, label in points:
        if file_path is not None:
            layer = gpd.read_file(file_path)

            # reproject it if necessary
            if layer.crs is None:
                layer = layer.set_crs(dem_crs)

            layer = layer.to_crs(crs)
            layer.plot(ax=ax, color=color, marker=marker, label=label, zorder=5, alpha=0.8)

    # (5) format the axes
    ax.set_xlabel("Longitude [°]", fontweight="bold")
    ax.set_ylabel("Latitude [°]", fontweight="bold")
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.2f}°"))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}°"))

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, fontsize=6)

    # (6) save the figure
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        plt.tight_layout()
        fig.savefig(save_path, dpi=600, bbox_inches="tight")

    return fig, ax


def usage():

    seis_cat = "Tianmo"
    resolution = 30  # unit by m

    raw_dem = Path(project_root) / f"data/hydro_raw/{seis_cat}_Copernicus_{resolution}m.tif"
    projected_dem_path = Path(project_root) / f"data/hydro_cooked/{seis_cat}/{seis_cat}_{resolution}_UTM.tif"

    catchment_path = Path(project_root) / f"data/hydro_cooked/{seis_cat}/catchment.shp"
    channel_path = Path(project_root) / f"data/hydro_cooked/{seis_cat}/main_channel.shp"

    outlet_path = Path(project_root) / f"data/hydro_cooked/{seis_cat}/outlet.shp"
    head_path = Path(project_root) / f"data/hydro_cooked/{seis_cat}/head.shp"

    snapped_head_path = None  # Path(project_root) / f"data/hydro_cooked/{seis_cat}/snapped_head.shp"
    snapped_outlet_path = None  # Path(project_root) / f"data/hydro_cooked/{seis_cat}/snapped_outlet.shp"

    seismic_sta_path = Path(project_root) / f"data/hydro_cooked/{seis_cat}/seis_sta.shp"

    # (1) reprojected the DEM to UTM
    # You do NOT need this if you have the shp file
    project_dem(dem_path=raw_dem, projected_dem_path=projected_dem_path, resolution=resolution)

    # (2) conver the seismic station
    # You do NOT need this if you have the shp file
    point2gpd(
        lon=95.309,  # float, unit by degree
        lat=29.9796,  # float, unit by degree
        save_path=seismic_sta_path,
        crs="EPSG:4326",
    )

    # (2) check the shp results
    save_path = Path(project_root) / f"plots/plot_geo/{seis_cat}.png"

    fig, ax = plot_catchment(
        projected_dem_path=projected_dem_path,
        catchment_path=catchment_path,
        channel_path=channel_path,
        ##
        head_path=head_path,
        snapped_head_path=snapped_head_path,
        ##
        outlet_path=outlet_path,
        snapped_outlet_path=snapped_outlet_path,
        ##
        seismic_sta_path=seismic_sta_path,
        ##
        save_path=save_path,
    )
    plt.show()
