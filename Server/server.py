#!/usr/bin/python3
import argparse
import sys

from glob import glob
from shutil import rmtree
from os import getcwd, mkdir, chdir
from os.path import isfile, join, abspath
from server_framework import Server
from ftp import FTP_Transfer

global FTP_CONNECTION

def create_parameters( arguments):
	'''Create arguments to execute blast (blastp, blastx or blastn)'''

	reserved_words = ['host', 'port', 'ftp_server']
	store_true_list = ['lcase_masking', 'parse_deflines', 'show_gis', 'html', 'ungapped', 'remote', 'use_sw_tback']
	folders = ['query', 'db', 'subject'] 
	blast_versions = ['blastp', 'blastn', 'blastx']
	
	if (arguments.blastn):
		command = 'blastn '
	elif (arguments.blastx):
		command = 'blastx '
	else:
		command = 'blastp '

	for arg in vars(arguments):
		if arg not in reserved_words and arg not in blast_versions:
			value = getattr(arguments, arg)
			if arg in store_true_list:
				if value:
					command = command + '-' + arg + ' '
			elif value:
				if arg in folders:
					if arg == 'query':
						argument_1 = arguments_server(value)
					elif arg == 'db' or arg == 'subject':
						argument_2 = arguments_server(value)
						
					command = command + '-' + arg + ' ' + '$' + ' '
				elif arg == 'out':
					#Test if the folder exists, if not the folder is created
					if not FTP_CONNECTION.check_or_create_folder(value):
						print('The path ' + value + 'doesn\'t exist and you don\'t have permissions to create folders in FTP server.')
					command = command + '-' + arg + ' ' + str(value) + ' '
				else:
					command = command + '-' + arg + ' ' +  str(value) + ' '

	list_argv = sys.argv
	newCommand = command.split()[0]
	
	for argv in sys.argv:
		if argv in command.split():
			newCommand += ' ' + argv
			if (argv == '-query' or argv == '-db' or argv == '-subject'):
				newCommand += ' $'

	return (newCommand, argument_1, argument_2)

def arguments_server(paths):
	'''Call the pick_files function for each path in paths and return the arguments list'''

	argument = []

	if isinstance(paths, list):
		for path in paths:
			argument = argument + pick_files(path)
	else:
		argument = pick_files(paths)
	
	return argument

def pick_files(path):
	'''Pick files from FTP server and return their names in the list'''

	global FTP_CONNECTION
	
	temporary_folder = 'FTP-Files/'
	just_path = path[:path.rfind('/')]
	files = FTP_CONNECTION.pick_files(just_path)

	if not (isinstance(files, list)):
		print('The path ' + path + ' was not found.')
		exit()

	#Current directory
	cwd = getcwd() 
	mkdir(temporary_folder)
	abs_path = cwd + '/' + temporary_folder
	chdir(abs_path)

	for file in files:
		f = open(file, 'w+')
		f.close()

	files = []
	files_path = glob(abs_path + path.split('/')[-1]) 
	
	for file in files_path:
		file_name = file[file.rfind('/'):]
		files.append(just_path + '/' + file_name[1:])

	chdir(cwd)
	rmtree(temporary_folder)

	return files

def check_ftp_server(ftp_server):
	'''Verify if the FTP server is connected and if the login and password is correct as well
	Return the FTP parameters'''

	global FTP_CONNECTION
	
	ftp_server = ftp_server.strip()

	if ftp_server.find(':') is not -1 and ftp_server.find('@') is not -1:
		split = ftp_server.split(':')
		login, password, ftp_ip = split[0], split[1].split('@')[0], split[1].split('@')[1]
		FTP_server = ftp_ip + ' ' + login + ' ' + password 
		FTP_CONNECTION = FTP_Transfer(ftp_ip, login, password)
	else:
		if ftp_server.find(' ') is not -1:
			print('The ftp value should be like that:\n login:password@ftp_ip\nor\n ftp_ip\n')
			exit()
		FTP_server = ftp_server
		FTP_CONNECTION = FTP_Transfer(ftp_ip)

	#Verify if the data is correct:
	result = FTP_CONNECTION.FTP_connect()
	
	if result == -1:
		print('The ftp server is not connect at moment.')
		exit()
	elif result == -2:
		print('The ftp login or password is incorrect.')
		exit()

	FTP_CONNECTION.FTP_close()
	
	return FTP_server

def add_arguments_to_parser(parser):
	'''Add all blast arguments to the argparser'''
	
	run = parser.add_mutually_exclusive_group(required = True)
	parser.add_argument('-server', action = 'store', dest = 'host', default = '', required = False, metavar = '',
		help = 'Server ip')
	parser.add_argument('-port', action = 'store', dest = 'port', default = 9995, type = int, required = False, metavar = '',
		help = 'Server port')
	parser.add_argument('-ftp', action = 'store', dest = 'ftp_server', required = True,
	 help = 'FTP server you want to acess. The value should be like that: login:password@ftp_ip')
	parser.add_argument('-import_search_strategy', action = 'store', dest = 'import_search_strategy', type = str, required = False, metavar = '')
	parser.add_argument('-export_search_strategy', action = 'store', dest = 'export_search_strategy', type = str, required = False, metavar = '', help = 'File name to record the search strategy used')
	parser.add_argument('-task', action = 'store', dest = 'task', required = False, metavar = '')
	parser.add_argument('-dbsize', action = 'store', type = int, dest = 'dbsize', required = False, metavar = '')
	parser.add_argument('-gilist', action = 'store', dest = 'gilist', type = str, required = False, metavar = '')
	parser.add_argument('-seqidlist', action = 'store', dest = 'seqidlist', required = False, metavar = '')
	parser.add_argument('-negative_gilist', action = 'store', dest = 'negative_gilist', type = str, required = False, metavar = '')
	parser.add_argument('-entrez_query', action = 'store', dest = 'entrez_query', type = str, required = False, metavar = '')
	parser.add_argument('-db_soft_mask', action = 'store', dest = 'db_soft_mask', type = int,required = False, metavar = '')
	parser.add_argument('-db_hard_mask', action = 'store', dest = 'db_hard_mask', type = int, required = False, metavar = '')
	parser.add_argument('-subject_loc', action = 'store', dest = 'subject_loc', type = str, required = False, metavar = '')
	parser.add_argument('-query', action = 'store', dest = 'query', type = str, nargs = '+', required = True)
	run.add_argument('-db', action = 'store', dest = 'db', type = str, nargs = '+', required = False, metavar = '')
	run.add_argument('-subject', action = 'store', dest = 'subject', type = str, nargs = '+', required = False, metavar = '')
	parser.add_argument('-out', action = 'store', dest = 'out', type = str, required = True, help = 'Output folder\'s name where the output files will be stored.') 
	parser.add_argument('-evalue', action = 'store', dest = 'evalue', type = float, required = False, metavar = '')
	parser.add_argument('-word_size', action = 'store', dest = 'word_size', type = int, required = False, metavar = '')
	parser.add_argument('-gapopen', action = 'store', dest = 'gapopen', type = int, required = False, metavar = '')
	parser.add_argument('-gapextend', action = 'store', dest = 'gapextend', type = int, required = False, metavar = '')
	parser.add_argument('-qcov_hsp_perc', action = 'store', dest = 'qcov_hsp_perc', type = float, required = False, metavar = '')
	parser.add_argument('-max_hsps', action = 'store', dest = 'max_hsps', type = int, required = False, metavar = '')
	parser.add_argument('-xdrop_ungap', action = 'store', dest = 'xdrop_ungap', type = float, required = False, metavar = '')
	parser.add_argument('-xdrop_gap', action = 'store', dest = 'xdrop_gap', type = float, required = False, metavar = '')
	parser.add_argument('-xdrop_gap_final', action = 'store', dest = 'xdrop_gap_final', type = float, required = False, metavar = '')
	parser.add_argument('-searchsp', action = 'store', dest = 'searchsp', type = int, required = False, metavar = '')
	parser.add_argument('-sum_stats', action = 'store', dest = 'sum_stats', type = bool, required = False, metavar = '')
	parser.add_argument('-seg', action = 'store', dest = 'seg', type = str, required = False, metavar = '')
	parser.add_argument('-soft_masking', action = 'store', dest = 'soft_masking', type = bool, required = False, metavar = '')
	parser.add_argument('-matrix', action = 'store', dest = 'matrix', type = str, required = False, metavar = '')
	parser.add_argument('-threshold', action = 'store', dest = 'threshold', type = float, required = False, metavar = '')
	parser.add_argument('-culling_limit', action = 'store', dest = 'culling_limit', type = int, required = False, metavar = '')
	parser.add_argument('-best_hit_overhang', action = 'store', dest = 'best_hit_overhang', type = float, required = False, metavar = '')
	parser.add_argument('-best_hit_score_edge', action = 'store', dest = 'best_hit_score_edge', type = float, required = False, metavar = '')
	parser.add_argument('-window_size', action = 'store', dest = 'window_size', type = int, required = False, metavar = '')
	parser.add_argument('-lcase_masking', '--lcase_masking', action = 'store_true')
	parser.add_argument('-query_loc', action = 'store', dest = 'query_loc', type = str, required = False, metavar = '')
	parser.add_argument('-parse_deflines', '--parse_deflines', action = 'store_true')
	parser.add_argument('-outfmt', action = 'store', dest = 'outfmt', type = str, required = True)
	parser.add_argument('-show_gis', '--show_gis', action = 'store_true')
	parser.add_argument('-num_descriptions', action = 'store', dest = 'num_descriptions', type = int, required = False, metavar = '')
	parser.add_argument('-num_alignments', action = 'store', dest = 'num_alignments', type = int, required = False, metavar = '')
	parser.add_argument('-line_length', action = 'store', dest = 'line_length', required = False, metavar = '')
	parser.add_argument('-html', '--html', action = 'store_true')
	parser.add_argument('-max_target_seqs', action = 'store', dest = 'max_target_seqs', type = int, required = False, metavar = '')
	parser.add_argument('-ungapped', '--ungapped', action = 'store_true')
	parser.add_argument('-remote', '--remote', action = 'store_true')
	parser.add_argument('-comp_based_stats', action = 'store', dest = 'comp_based_stats', type = str, required = False, metavar = '')
	parser.add_argument('-use_sw_tback', '--use_sw_tback', action = 'store_true')
	parser.add_argument('-blastp', '--blastp', action = 'store_true')
	parser.add_argument('-blastn', '--blastn', action = 'store_true')
	parser.add_argument('-blastx', '--blastx', action = 'store_true')

def main():
	'''Call the Server class to parallelizing blast activities among clients'''

	parser = argparse.ArgumentParser(description = 'Parallelizing blast activities', 
	 epilog = 'For more information read the blast documentation.')
	add_arguments_to_parser(parser)
	arguments = parser.parse_args()
	list_args = sys.argv

	if int(arguments.outfmt) < 0 or int(arguments.outfmt) > 14:
		print('The outfmt must be between 0 and 14.') 
		exit()

	FTP_server = check_ftp_server(arguments.ftp_server)
	command, argument_1, argument_2 = create_parameters(arguments)

	server = Server(host = arguments.host, port = arguments.port, command = command, FTP_server = FTP_server)

	server.arguments(argument_1, argument_2)
	print('Server is online')
	server.main()

if __name__ == "__main__":
	main()