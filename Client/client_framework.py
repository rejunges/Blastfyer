#!/usr/bin/python3
import socket
import re
import datetime
import os
import time

from subprocess import Popen, PIPE
from ftp import FTP_Transfer

global FLAG
FLAG = True

class Client:
	'''Receive the activities from Server, execute it, and send the output filename'''

	def __init__(self, host, port, num_threads):
		'''Init the Client

		This method stores the number of threads used by the blast, the IP address, and the port where will be made the connection'''

		self.host = host
		self.port = port
		self.num_threads = num_threads
		self.list_files = []

	def main(self):
		'''Init the Client program'''

		self.create_TCP_connection()
		#Send sockname
		self.s.send(self.s.getsockname()[0].encode('utf-8'))
		try:
			while True:
				self.receive_server_message()
		except:
			self.close_client()

	def close_client(self):
		'''Proccess the CTRL+C exception'''

		self.send_message('/Exit', 1)
		self.close_TCP_connection()
		self.remove_files()
		os._exit(1)

	def remove_files(self):
		'''This method erase all auxiliary files'''

		try:
			for filename in self.list_files:
				os.remove(filename)
		except:
			print("You don't have permission to delete the files.")

	def download_filenames_FTP(self, arg_1, arg_2, output_server):
		'''Download files from FTP Server and store locally''' 

		result_1, result_2 = True, True
		file_name_1, file_name_2 = arg_1[arg_1.rfind('/') + 1:], arg_2[arg_2.rfind('/') + 1:]

		if not os.path.isfile(file_name_1):
			result_1 = self.ftp.download(arg_1)
		if not os.path.isfile(file_name_2):
			result_2 = self.ftp.download(arg_2)

		final_result = self.error_FTP_server(output_server, result_1, result_2, True)
		if final_result:
			if file_name_1 not in self.list_files:
				self.list_files.append(file_name_1)
			if file_name_2 not in self.list_files:
				self.list_files.append(file_name_2)
		
		return final_result

	def error_FTP_server(self, output_server, result_1, result_2 = True, flag = 0):
		'''Verify if occurred some errors in FTP server.
		If occurs a error, the Client send a error message to Server.'''

		if not result_1 == True or not result_2 == True:
			if result_1 == -1 or result_2 == -1:
				print("Timeout error trying to connect.")
			elif result_ == -2 or result_2 == -2:
				print("The login and password used to connect to the FTP server do not match.")
			elif flag == 1:
				print("Error downloading the files.")
			else:
				print("Error uploading files.")

			self.error_message(output_server)
			return False

		return True

	def execute_task(self, arg_1, arg_2, command, output_server):
		'''Execute tasks'''

		file_1, file_2 = arg_1.split('/')[-1], arg_2.split('/')[-1]
		variables = [file_1, file_2.split('.')[0], output_server[0]]
		sent = False
		index_upload = command.index('-out')
		upload_path = command[index_upload + 1]
		command[index_upload + 1] = '$'

		count = 0
		index = 0

		return_code = True

		db_file = file_2.split('.')[0]

		if not os.path.isfile(file_2.split('.')[0] + '.phr'):
			command_makeblastdb = ['makeblastdb', '-in', file_2, '-dbtype', 'prot', '-out', db_file]
			return_code = self.execute_command_line(command_makeblastdb, output_server[0]) #makeblastdb

		if not return_code:
			return

		if db_file + '.pin' not in self.list_files:
			self.list_files.append(db_file + '.pin') 
			self.list_files.append(db_file + '.psq')
			self.list_files.append(db_file + '.phr') 
		
		for parameter in command:
			if parameter == '$':
				command[index] = variables[count]
				count += 1
			index +=1

		command.append('-num_threads')
		command.append(str(self.num_threads))

		return_code = self.execute_command_line(command, output_server)

		if not return_code:
			return
		
		self.list_files.append(output_server[0])

		try:
			result = self.ftp.upload(output_server[0], upload_path)
			self.error_FTP_server(output_server, result)
			sent = True
		except KeyboardInterrupt:
			self.close_client()
		except:
			print('Error uploading files from Server.')

		if sent:
			#Send to Server the output filename to inform that task is finished.
			self.send_message(output_server)
			print('Completed task: {}\n'.format(output_server[0]))
		else:
			self.error_message(output_server)

	def execute_command_line(self, command, output_server):
		'''Execute a command line using proccess and treats its errors'''

		return_code = 0
		try:
			proccess = Popen(command, stdin = PIPE, stdout = PIPE, stderr = PIPE)
			output, error = proccess.communicate(b"input data that is passed to subprocess' stdin")
			return_code = proccess.returncode
			if error:
				return_code = 1
		except KeyboardInterrupt:
			self.close_client()
		except:
			print('This computer does not have the necessary tools.')
			self.error_message(output_server)
			return False
		
		if return_code is not 0:
			self.error_message(output_server)
			return False

		return True

	def error_message(self, output_server):
		'''Send message to Server, notifying in which execution occurred a error'''
		
		output_server.insert(0,'ERROR')
		try:
			self.send_message(output_server)
		except:
			print('Error message doesn\'t sent to Server. Server closed.')

	def connect_FTP_server(self, FTP_server):
		'''Connection with FTP Server'''

		address, login, senha = FTP_server
		self.ftp = FTP_Transfer(address, login, senha)
		
	def receive_server_message(self):
		'''Receive messages from Server. VerifY if it is a task or if it is to logout.
		If received '/Disconnect' command, it means that the Server doesn't have more tasks to distribute'''
	
		#Server sends: 'argument_1, argument_2, [command], (ftp)'
		task = self.s.recv(4096).decode('utf-8')
		arg_1 = task.split()[0]

		if arg_1 == '/Disconnect':
			print("Closing connection. Server doesn't have more tasks to distribute.")
			self.close_TCP_connection()
			self.remove_files()
			os._exit(1)		

		self.receive_task(arg_1, task)

	def receive_task(self, arg_1, task):
		'''Receive the task that needs to be executed. Method called by receive_server_message'''

		global FLAG

		format_XML = [5, 14]
		format_TXT = [0, 1, 2, 3, 4, 6, 7, 8, 10, 11]
		format_JSON = [12, 13]
		format_BIN = [9]

		arg_2 = task.split()[1]
		command = re.search(r"\[(.*)\]", task).group(1).replace('\'','').replace(' ', '').split(',')
		ftp = tuple(re.search(r"\((.*)\)", task).group(1).replace('\'','').replace(' ', '').split(','))

		if FLAG:
			self.connect_FTP_server(ftp)
			FLAG = False

		file_name_1, file_name_2 = arg_1.split('/')[-1], arg_2.split('/')[-1]
		value_outfmt = int(command[command.index('-outfmt') + 1])
		output_file = file_name_1[:file_name_1.rfind('.')] + '~' + file_name_2[:file_name_2.rfind('.')]
		
		if value_outfmt in format_XML:
			output_file = output_file + '.xml'
		elif value_outfmt in format_TXT:
			output_file = output_file + '.txt'
		elif value_outfmt in format_JSON:
			output_file = output_file + '.json'		

		output_server = [output_file, arg_1, arg_2]

		print("\tExecuting task:\nArgument 1: {}\nArgument 2: {}".format(arg_1, arg_2))
		return_code = self.download_filenames_FTP(arg_1, arg_2, output_server)
		
		if return_code:
			self.execute_task(arg_1, arg_2, command, output_server)


	def create_TCP_connection(self):
		'''Create a TCP connection with the Server'''

		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except:
			print("Error creating socket.")
			os._exit(1)
		try:
			self.s.connect((self.host, self.port))
		except:
			print('Server disconnected.')
			os._exit(1)

	def close_TCP_connection(self):
		'''Close the TCP connection'''
		
		self.s.close()

	def send_message(self, message, flag = 0):
		'''Send a message to the Server'''

		try:
			if (flag):
				self.s.send(''.join(message).encode('utf-8'))
			else:
				self.s.send(' '.join(message).encode('utf-8'))
		except:
			pass
