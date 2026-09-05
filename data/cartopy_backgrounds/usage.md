# Setting up a High-Resolution Cartopy Background

## 1. Download the data
```sh
mkdir -p "/Users/qizhou/#python/Flow-Bench-geo/data/cartopy_backgrounds"
cd "/Users/qizhou/#python/Flow-Bench-geo/data/cartopy_backgrounds"

curl -O https://naciscdn.org/naturalearth/10m/raster/NE1_HR_LC_SR_W_DR.zip
```

## 2. Unzip the archive
```sh
unzip NE1_HR_LC_SR_W_DR.zip
```

## 3. Convert to PNG (high resolution)
```sh
gdal_translate NE1_HR_LC_SR_W_DR.tif NE1_HR_LC_SR_W_DR.png
```

## 4. Create a downsampled medium-resolution version
```sh
gdal_translate -outsize 25% 25% NE1_HR_LC_SR_W_DR.tif NE1_MED_LC_SR_W_DR.png
```

## 5. Create the `images.json` config file
```sh
cat > images.json << 'EOF'
{
  "NaturalEarthRelief": {
    "__projection__": "PlateCarree",
    "high": "NE1_HR_LC_SR_W_DR.png",
    "medium": "NE1_MED_LC_SR_W_DR.png"
  }
}
EOF
```

## 6. Verify
```sh
ls
```

Expected files:
```
NE1_HR_LC_SR_W_DR.README.html   NE1_HR_LC_SR_W_DR.tfw           NE1_MED_LC_SR_W_DR.png
NE1_HR_LC_SR_W_DR.VERSION.txt   NE1_HR_LC_SR_W_DR.tif           images.json
NE1_HR_LC_SR_W_DR.png           NE1_HR_LC_SR_W_DR.zip
NE1_HR_LC_SR_W_DR.png.aux.xml   NE1_HR_LC_SR_W_DR.prj
```

## 7. Usage in Python
```python
import os

os.environ["CARTOPY_USER_BACKGROUNDS"] = "/Users/qizhou/#python/Flow-Bench-geo/data/cartopy_backgrounds/"

ax.background_img(name="NaturalEarthRelief", resolution="medium")  # or "high"
```