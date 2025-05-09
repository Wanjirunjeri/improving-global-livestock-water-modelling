#!/bin/bash

# Directory containing the FAO files
input_dir="fao_density_2010"
output_dir="fao_density_renamed_2010"
mkdir -p $output_dir

# Declare associative arrays for animal name mapping
declare -A animal_map
animal_map=( ["Ct"]="cattle" ["Bf"]="buffalo" ["Sh"]="sheep" ["Gt"]="goat" ["Ho"]="horse" ["Pg"]="pig" ["Ch"]="chicken" ["Dk"]="duck" )

echo "Step 1: Renaming FAO variables and files..."

# Loop through each file in the input directory
for file in $input_dir/*.nc; do
    # Extract the animal code (e.g., Ct, Bf, Sh) from the filename
    basename=$(basename "$file")
    animal_code=$(echo "$basename" | cut -d'_' -f2)

    # Map the animal code to the full name using the associative array
    animal_name=${animal_map[$animal_code]}

    # Construct the output filename using the mapped animal name
    output_file="$output_dir/fao_${animal_name}_2010.nc"

    # Rename the variable from Band1 to population_density and save with the new name
    echo "Renaming variable and file: $basename -> fao_${animal_name}_2010.nc"
    cdo chvar,Band1,population_density "$file" "$output_file"
done

echo "✅ Step 1 complete: Variable and file names harmonized."

