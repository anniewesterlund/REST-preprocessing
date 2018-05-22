#!/bin/bash

n_replicas=10;
sim_tag='transition_sim';
mdp_file='step7_production.mdp';
top_file='topol.top'
standard_folder='standard'
minT=303.15
maxT=320.0
heat_regions=('PROA' 'PROB' 'PROC' 'PROD')


python preprocess_REST.py -f $mdp_file -minT $minT -maxT $maxT -ex_dir $standard_folder -label $sim_tag -n_rep $n_replicas -heat_reg ${heat_regions[@]} -p $top_file

