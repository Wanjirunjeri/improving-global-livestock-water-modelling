#!/bin/bash
#SBATCH -J val2020
#SBATCH --mem=16G
#SBATCH -t 01:00:00
#SBATCH -o log.out


source /scratch/brussel/111/vsc11128/venv_merge/bin/activate
#python -u valid_2020only.py
python summary_validation.py --years 2010 2015 2020 --root "$VSC_SCRATCH/fao_validation"
