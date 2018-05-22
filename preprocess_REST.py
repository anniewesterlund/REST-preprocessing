import os
import sys
import shutil
import re
import numpy as np
import argparse

def get_fields(line):
	fields = line.split(' ')
	new_fields = []
	for i in range(len(fields)):
		if fields[i] != '':
			new_fields.append(fields[i]);
	return new_fields

def set_underscore(line):
	fields = get_fields(line)
	
	if fields[0] == ';':
		return line

	if len(fields) != 11:
		return line

	new_line = '';
	for i in range(len(fields)):
		if i == 1:
			new_line = new_line + '\t' + fields[i] + '_'
		else:
			new_line = new_line + '\t' + fields[i]
	
	return new_line

def update_pairtypes(line,scaling_factor):
	fields = get_fields(line)
	new_line = line 
	if line[0] != ';' and line[0] != '[' and len(line) > 1:
		new_line = new_line + '\t' +fields[0]+'_\t' + fields[1]+'_'
		for i in range(2,len(fields)-2):
			new_line = new_line + '\t' + fields[i]
		
		last_num = float(fields[-2])
		new_line = new_line + '\t' + str(scaling_factor*last_num) + '\t ; scaled \n'
	
	return new_line

def update_cmaptypes(line,scaling_factor):
	
	fields = get_fields(line)
	if fields[0] == ';':
		return line;
	
	new_line = ''
	if (len(fields) == 6 or len(fields) == 10) and fields[0][0] != ';':
		for i in range(len(fields)-1):
			num = float(fields[i])
			new_line = new_line + str(scaling_factor*num) + '\t'
		
		num = float(fields[-1][:-2])
		new_line = new_line + str(scaling_factor*num) +'\ \n'
	
	else:
		new_line = line

	return new_line;

def get_temperature_list(nReplicas, minT, maxT):
	
	T_list = np.zeros(nReplicas)
	
	# Set temperatures
	for iTemp in range(int(nReplicas)):
		T_list[iTemp]=minT*np.exp(float(iTemp)*np.log(maxT/minT)/(nReplicas-1.0))
	
	return T_list;

def main(args):
	
	# Set parameters
	minT = float(args.min_temperature)
	maxT = float(args.max_temperature)
	
	nReplicas = float(args.number_of_replicas)
	
	system_name = args.system_label
	
	standard_folder_name = args.example_directory
	if standard_folder_name[-1] != '/':
		standard_folder_name += '/'
	
	mdp_file = args.mdp_file
	top_file = args.topology;
	
	heating_regions = args.heat_regions
	
	T_list = get_temperature_list(nReplicas, minT, maxT)
	
	# Create processed.top
	os.system('gmx grompp -f '+ standard_folder_name + mdp_file +' -c '+ standard_folder_name + system_name +'.gro -pp '+ standard_folder_name +'processed.top -n '+ standard_folder_name +'index.ndx -p '+ standard_folder_name + top_file)
	
	os.system('rm topol.tpr')
	os.system('rm mdout.mdp')
	
	# Create an empty plumed.dat file
	os.system('touch '+standard_folder_name+'plumed.dat')
	
	# Process each replica
	for iTemp in range(int(nReplicas)):
		
		scaling_factor = T_list[0]/T_list[iTemp]
		
		print('lambda = ' + str(scaling_factor))
		
		# Copy entire standard folder to new folder
		current_folder = system_name+str(iTemp)+'/'
		
		if not os.path.exists(current_folder):
			shutil.copytree(standard_folder_name,current_folder)
		
		# Write updated .top file to processed2.top
		fID1 = open(current_folder+'processed.top','r')
		fID2 = open(current_folder+'processed2.top','w')
		
		cmaptypes=False
		pairtypes=False
		moleculetype=False
		atoms=False
	
		in_heating_region = False

		do_underscore = False
	
		for line in fID1:
			find_bracket = re.search('\[',line)
			if find_bracket is not None:
				cmaptypes=False 
				pairtypes=False
				atoms=False
				moleculetype=False
				do_underscore=False
				
				find_atoms = re.search('\[ atoms \]',line)
				find_cmaptypes = re.search('cmaptypes',line)
				find_pairtypes = re.search('\[ pairtypes \]',line)
				find_moleculetype = re.search('\[ moleculetype \]',line)	
				
				if find_cmaptypes is not None:
					cmaptypes=True 
				
				if find_pairtypes is not None:
					pairtypes=True
			
				if find_moleculetype is not None:
					moleculetype=True
					in_heating_region = False
			
				if find_atoms is not None:
					atoms=True
				
					if in_heating_region:
						do_underscore=True
		
			if moleculetype:
				for iRegion in range(len(heating_regions)):
					find_heat_reg = re.search(heating_regions[iRegion],line)
					if find_heat_reg is not None:
						in_heating_region = True
		
			new_line = line		
			
			if do_underscore:
				new_line = set_underscore(line)
		
			if pairtypes:
				new_line = update_pairtypes(line, scaling_factor)
		
			if cmaptypes:
				new_line = update_cmaptypes(line, scaling_factor)
		
			fID2.write(new_line)
			
		
		fID1.close()
		fID2.close()
		
		# Perform partial tempering with plumed to get new_topol.top
		os.system('plumed partial_tempering '+ str(scaling_factor) +' < ' + current_folder + 'processed2.top > ' + current_folder + 'new_topol.top' )

parser = argparse.ArgumentParser(epilog='Create REST folders and perform scaling or selected region. Annie Westerlund 2018.');
parser.add_argument('-minT','--min_temperature',help='Minimum temperature',type=float);
parser.add_argument('-maxT','--max_temperature',help='Maximum temperature',type=float);
parser.add_argument('-n_rep','--number_of_replicas',help='Number of replicas to use',type=float);
parser.add_argument('-label','--system_label',help='Name of the system.',type=str);
parser.add_argument('-ex_dir','--example_directory',help='Name of the standard folder (will be copied).',type=str, default='standard/');
parser.add_argument('-f','--mdp_file',help='Name of the production .mdp file.',type=str, default='step7_production.mdp');
parser.add_argument('-heat_reg','--heat_regions',help='Name(s) of the moleculetypes to heat.',type=str, nargs='+', default='step7_production.mdp');
parser.add_argument('-p','--topology',help='Name of topology file, default topol.top',default='topol.top')

args = parser.parse_args();
main(args);

