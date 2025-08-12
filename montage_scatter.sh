#!/usr/bin/env bash
set -euo pipefail

ROOT="${VSC_SCRATCH}/fao_validation"

# Helper: build a montage if all files exist
montage_safe () {
  local out="$1"; shift
  local files=("$@")
  for f in "${files[@]}"; do
    [[ -f "$f" ]] || { echo "Missing: $f" >&2; exit 2; }
  done
  # -tile CxR, add small gaps, keep original sizes
  montage "${files[@]}" -tile "$TILE" -geometry +10+10 -background white -strip -quality 95 "$out"
  echo "Saved: $out"
}

# 2020 -> 2 x 3 (6 species: no duck/horse)
TILE="2x3"
Y=2020
D="${ROOT}/plots${Y}"
montage_safe "${D}/scatter_grid_${Y}.png" \
  "${D}/scatter_buffalo_${Y}.png" \
  "${D}/scatter_cattle_${Y}.png" \
  "${D}/scatter_chicken_${Y}.png" \
  "${D}/scatter_goat_${Y}.png" \
  "${D}/scatter_pig_${Y}.png" \
  "${D}/scatter_sheep_${Y}.png"

# 2015 -> 2 x 4 (8 species incl. duck & horse)
TILE="2x4"
Y=2015
D="${ROOT}/plots${Y}"
montage_safe "${D}/scatter_grid_${Y}.png" \
  "${D}/scatter_buffalo_${Y}.png" \
  "${D}/scatter_cattle_${Y}.png"  \
  "${D}/scatter_chicken_${Y}.png" \
  "${D}/scatter_goat_${Y}.png"    \
  "${D}/scatter_pig_${Y}.png"     \
  "${D}/scatter_sheep_${Y}.png"   \
  "${D}/scatter_duck_${Y}.png"    \
  "${D}/scatter_horse_${Y}.png"

# 2010 -> 2 x 4
Y=2010
D="${ROOT}/plots${Y}"
montage_safe "${D}/scatter_grid_${Y}.png" \
  "${D}/scatter_buffalo_${Y}.png" \
  "${D}/scatter_cattle_${Y}.png"  \
  "${D}/scatter_chicken_${Y}.png" \
  "${D}/scatter_goat_${Y}.png"    \
  "${D}/scatter_pig_${Y}.png"     \
  "${D}/scatter_sheep_${Y}.png"   \
  "${D}/scatter_duck_${Y}.png"    \
  "${D}/scatter_horse_${Y}.png"

