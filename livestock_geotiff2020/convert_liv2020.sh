#!/bin/bash

#module load gdal

module load GDAL/3.7.1-foss-2023a


for file in /user/brussel/111/vsc11128/GLWD/livestock_geotiff2020/Da_tiffs2020/*.tif;do
    base=$(basename "$file" .tif)
    echo "Processing $base..."
    gdalwarp -tr 0.5 0.5 -r average -t_srs EPSG:4326 "$file" "/user/brussel/111/vsc11128/GLWD/livestock_geotiff2020/liv_regrid2020/${base}_0.5deg.tif"
    gdal_translate -of netCDF "/user/brussel/111/vsc11128/GLWD/livestock_geotiff2020/liv_regrid2020/${base}_0.5deg.tif" "/user/brussel/111/vsc11128/GLWD/livestock_geotiff2020/liv_netcdf2020/${base}_0.5deg.nc"
done

