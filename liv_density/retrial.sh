#!/bin/bash
#SBATCH --job-name=regrid_utrecht
#SBATCH --output=regrid_utrecht.log
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --partition=skylake   # or zen4

set -e   # ← abort script on *any* non-zero exit code

module load cdo
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK   # let CDO use all cores

in_fao="fao_density_renamed_2010/fao_cattle_2010.nc"
gridfile="fao_grid.txt"
in_ut="Liv_Pop_1980_2019.nc"
out_ut="Liv_Pop_1980_2019_regrid.nc"
log="regrid_cdo.log"

echo "Step 1 ▸ building FAO grid from $in_fao ..."
if [ ! -f "$gridfile" ]; then
    cdo griddes "$in_fao" > "$gridfile"
fi
echo "   ↳ grid written to $gridfile (first 6 lines):"
head -n 6 "$gridfile"

echo "Step 2 ▸ regridding Utrecht → FAO grid ..."
# -L = large-file mode; -f nc4c = NetCDF4-classic output
# send stdout/stderr to log so the SLURM log stays clean
cdo -L -f nc4c remapbil,"$gridfile" "$in_ut" "$out_ut" &> "$log"

# Step-3 sanity check: file exists and has >0 bytes
if [ -s "$out_ut" ]; then
    echo "✅ regridding finished: $out_ut"
else
    echo "❌ regridding failed — see $log for details"
    exit 1
fi

echo "Step 4 ▸ quick summary of the regridded file:"
cdo sinfo "$out_ut" | head
cdo info  "$out_ut" | head
echo "🚀 all done."

