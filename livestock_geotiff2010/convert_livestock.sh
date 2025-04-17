#!/bin/bash
module load gdal

for file in /user/brussel/111/vsc11128/livestock_geotiff/*Da.tif; do
    base=$(basename "$file" .tif)
    echo "Processing $base..."
    gdalwarp -tr 0.5 0.5 -r average -t_srs EPSG:4326 "$file" "/user/brussel/111/vsc11128/livestock_regridded/${base}_0.5deg.tif"
    gdal_translate -of netCDF "/user/brussel/111/vsc11128/livestock_regridded/${base}_0.5deg.tif" "/user/brussel/111/vsc11128/livestock_netcdf/${base}_0.5deg.nc"
done

