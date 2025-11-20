#!/usr/bin/python
# -*- coding: UTF-8 -*-

#__modification time__ = 2025-08-12
#__author__ = Qi Zhou, Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences
#__find me__ = qi.zhou@gfz-potsdam.de, qi.zhou.geo@gmail.com, https://github.com/Nedasd
# Please do not distribute this code without the author's permission

import os
import py7zr

# <editor-fold desc="add the sys.path to search for custom modules">
from pathlib import Path
current_dir = Path(__file__).resolve().parent
# using ".parent" on a "pathlib.Path" object moves one level up the directory hierarchy
project_root = current_dir.parent.parent
import sys
sys.path.append(str(project_root))
# </editor-fold>


def seven_zip_folder(folder_path, output_path, password=None):

    with py7zr.SevenZipFile(output_path, 'w', password=password) as archive:
        archive.writeall(folder_path, arcname=os.path.basename(folder_path))

folder_to_zip = "/Users/qizhou/Desktop/seismic"
output_7z = "/Users/qizhou/Desktop/seismic.7z"
seven_zip_folder(folder_to_zip, output_7z)

# this is really slow, run this in terminal
# cd /Applications/7z
# ./7zz a -t7z -mx=1 -mmt=on /Users/qizhou/Desktop/seismic.7z /Users/qizhou/Desktop/seismic


