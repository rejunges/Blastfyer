#!/usr/bin/python3
import argparse

from client_framework import Client

def main():
	'''Call the Client class to execute the blast activities from Server'''

	parser = argparse.ArgumentParser(description = 'Executing blast activities')

	parser.add_argument('-host', action = 'store', dest = 'host', required = True,
		help = 'Server ip')
	parser.add_argument('-port', action = 'store', dest = 'port', default = 9995, type = int, required = False,
		help = 'Server port')
	parser.add_argument('-num_threads', action = 'store', dest = 'num_threads', default = 1, type = int, required = False,
		help = 'Number of threads (CPUs) to use in the BLAST search')

	arguments = parser.parse_args()

	client = Client(host = arguments.host , port = arguments.port, num_threads = arguments.num_threads)
	client.main()

if __name__ == "__main__":
	main()