#!/bin/bash

#SBATCH --job-name=test_planet
#SBATCH --partition=serial
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=12
#SBATCH --cpus-per-task=1
#SBATCH --time=6:00:00
#SBATCH --mem=20G

module load build/gcc-7.2.0
module load languages/anaconda2/5.0.1
module load tools/git/2.18.0

echo 'modules loaded'
module list

source activate isca_env

time python frierson_test_case_bc-run.py
