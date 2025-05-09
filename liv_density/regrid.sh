#!/bin/bash
#SBATCH --job-name=regrid_utrecht
#SBATCH --output=regrid_utrecht.log
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=05:00:00
#SBATCH --partition=skylake

module purge
module load CDO/2.2.2-gompi-2023a 
#input_file="Liv_Pop_1980_2019.nc"
#output_file="Liv_Pop_1980_2019_regrid.nc"
#fao_grid_file="fao_grid.txt"

# Step 1: Generate the FAO grid definition (using Cattle as reference)
#echo "Generating FAO fao_density_renamed_2010/fao_cattle_2010.ncgrid from cattle file..."
#cdo griddes fao_density_renamed_2010/fao_cattle_2010.nc > fao_grid1.txt

#fao_grid_file = "fao_grid.txt"

#echo "✅ FAO grid definition saved to $fao_grid_file"

# Step 2: Regrid the Utrecht dataset to the FAO grid
echo "Regridding Utrecht dataset..."
#cdo -f nc4c remapcon,fao_grid.txt Liv_Pop_1980_2019.nc Liv_Pop_1980_2019_regrid.nc
# one-liner, conservative (area-weighted) regridding
cdo -L remapcon,fao_density_renamed_2010/fao_cattle_2010.nc \
        Liv_Pop_1980_2019.nc  Liv_Pop_1980_2019_regrid_con.nc \
        2>&1 | tee regrid_cdo.log

# Check for errors during regridding
if [ -s Liv_Pop_1980_2019_regrid_con.nc ]; then
    echo "✅ Regridding successful: Liv_Pop_1980_2019_regrid.nc"
else
    echo "❌ Regridding failed!"
    exit 1
fi

# Step 3: Verify the dimensions and variables of the regridded file
echo "Verifying regridded file..."
cdo sinfo Liv_Pop_1980_2019_regrid.nc
cdo info Liv_Pop_1980_2019_regrid.nc


echo "✅ Regridding process completed successfully."
