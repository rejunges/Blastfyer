#!/usr/bin/python3
import socket
import threading
import datetime
import os
import time

from operator import itemgetter
from database import Database 

global MAX_TASKS
global CLOSE

CLOSE = False
MAX_TASKS = 1

class Server:
	'''Distribute the tasks to connected clients, paralleling the activities'''

	def __init__(self, host, port, command, FTP_server):
		'''Init the Server
		This method stores the IP server address and the port that will be done the connection. 
			"command" is the command line that the Client is going to execute
			FTP_server is a tuple with server address, login and password'''

		self.number_received_tasks = 0
		self.total_number_tasks = 0
		self.host = host
		self.port = port
		self.online_clients = {}
		self.lock = threading.Lock()
		self.lock_recv_tasks = threading.Lock()
		self.lock_clients_online = threading.Lock()
		self.db = Database()
		self.command = command
		self.tasks = []
		self.FTP_server = FTP_server

	def handler(self, signum, frame):
		pass

	def main(self):
		'''Begin the Server execution
		Here the threads are initialized and sent to respective methods'''

		self.create_TCP_connection()
		global CLOSE
		flag = True

		try:
			while True:
				try:
					if flag:

						#This thread accepts a client connection and calls a method to receive Client messages
						thread_recv_client = threading.Thread(target = self.accept_clients_connection)
						thread_recv_client.daemon = True
						thread_recv_client.start()

						#This thread controls if there are tasks and Clients available
						thread_controller = threading.Thread(target = self.controller_availability)
						thread_controller.daemon = True
						thread_controller.start()

						flag = False;
				except: 
					#Treats the CTRL+C, ESC
					CLOSE = True
					self.close()
		except:
			CLOSE = True
			self.close()
			
	def receive_message(self, name, con):
		'''Receive Client messages'''
		
		alive = True
		global CLOSE

		while alive:
			client_message = ''

			try:
				client_message = con.recv(4096).decode('utf-8')
			except:
				alive = False
				self.close_client(name, con)
				
			if client_message:
				client_message_list = client_message.split()

				if client_message_list[0] == '/Exit':
					alive = False
					self.close_client(name, con)
				elif client_message_list[0] == 'ERROR':
					arq_1, arq_2 = client_message_list[2], client_message_list[3]
					try:
						self.lock.acquire(True)
						id_db = self.db.get_task_id(arq_1, arq_2)
						update = []
						update.append((False, id_db[0]))
						self.db.update_incomplete_task(update)
					finally:
						self.lock.release()
					try:
						self.lock_clients_online.acquire(True)
						self.online_clients[(name,con)] -= 1
					finally:
						self.lock_clients_online.release()
				else:
					self.update_number_received_tasks()
					self.receive_filename(client_message_list, name, con)
					if self.number_received_tasks == self.total_number_tasks:
						CLOSE = True
						alive = False
						self.close()

	def close(self):
		'''Close the Server'''

		self.close_all_clients()
		self.close_server()
		os._exit(1)

	def update_number_received_tasks(self):
		'''Update the number of done tasks received to avoid conflicts when receives tasks at same time'''

		try:
			self.lock_recv_tasks.acquire(True)
			self.number_received_tasks += 1
		finally:
			self.lock_recv_tasks.release()

	def receive_filename(self, client_message_list, name, con):
		'''Receive the output filename from Client and update database'''
		
		arg_1, arg_2 = client_message_list[1], client_message_list[2]
		task_received_date = datetime.datetime.now()
		
		try:
			self.lock_clients_online.acquire(True)
			self.online_clients[(name,con)] -= 1
		finally:
			self.lock_clients_online.release()
		
		try:
			self.lock.acquire(True)
			self.db.update_output(arg_1, arg_2, task_received_date, client_message_list[0])
			self.db.client_done_task(name)
			print('\tReceive task:\nArgument 1: {}\nArgument 2: {}\nFrom: {}\n'.format(arg_1, arg_2, name))
		finally:
			self.lock.release()			

	def close_all_clients(self):
		'''Close all Clients connections'''

		message = '/Disconnect'
		for name, con in dict(self.online_clients):
			try:
				con.send(message.encode('utf-8'))
				self.close_client(name, con)
			except:
				continue

	def close_client(self, name, con):
		'''When the Client become offline, this method should be called.
		The Client is disconnected from database and their records in online_clients are removed'''

		flag = False

		try:
			self.lock_clients_online.acquire(True)
			del self.online_clients[(name, con)]
		except:
			flag = True
		finally:
			self.lock_clients_online.release()
			if flag:
				return

		try:			
			self.lock.acquire(True)
			incomplete_tasks = self.db.get_client_tasks(name)
			self.db.set_client(name, False)
			self.update_incomplete_task(incomplete_tasks)
			con.close()
			print('Connection {} closed.'.format(name))
		except:
			pass
		finally:
			self.lock.release()

	def update_incomplete_task(self, incomplete_tasks):
		'''Receive a ids list of uncompleted tasks to be sent to other Clients.
		This method does not applies a lock, it is called by another method that is already blocking in the other threads'''
		
		update_db = []
		
		for number_id in incomplete_tasks:
			number_id = number_id[0]
			update_db.append((False, number_id))

		self.db.update_incomplete_task(update_db)


	def arguments(self, argument_1, argument_2):
		'''Save the arguments that will be used to distribute tasks.'''

		for i in range(len(argument_1)):
			for j in range(len(argument_2)):
				self.total_number_tasks += 1
				self.tasks.append((argument_1[i], argument_2[j], False, self.command, self.FTP_server))
		
		self.db.add_tasks(self.tasks)

	def create_TCP_connection(self):
		'''Create a TCP connection'''

		destination = (self.host, self.port)
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		try:
			#Bind the socket to a particular address and port
			self.s.bind(destination)
		except:
			print ('Bind failed')
			os._exit(1)

		self.s.listen(5)

	def close_TCP_connection(self):
		'''Close the TCP connection'''

		self.s.close()

	def get_less_overloaded(self):
		'''Return the first free Client'''
		
		if self.online_clients:
			client = sorted(self.online_clients.items(), key = itemgetter(1))
			client = client[0]
			client, value = client
			return client

	def distribute_task(self):
		'''Internal method that should be called by the controller_availability. Does not apply a Lock.
		Send some task to connected Clients'''

		tasks_list = self.db.get_all_tasks()
		update_db = [] 
		
		for task in tasks_list: 
			if self.online_clients:
			#Choose the first free Client
				client = self.get_less_overloaded()
				name, con = client
				if self.online_clients[client] < MAX_TASKS:
					#Send task to Client
					try:
						self.send_task(con, name, task)
						#Necessary to sleep(1) when only exists just one online client and there is more than one activity
						time.sleep(1) 
						number_id, arg_1, arg_2,  command, ftp = task
						try:
							self.lock_clients_online.acquire(True)
							self.online_clients[client] += 1
						finally:
							self.lock_clients_online.release()
						task_sent_date = datetime.datetime.now()
						update_db.append((name, task_sent_date, True, number_id))
					except:
						continue
				else:
					self.db.update_sent_task(update_db)
					return
			else:
				break	
					
		self.db.update_sent_task(update_db)


	def send_task(self, con, name, task):
		'''Receive connection that should send the task'''
		
		number_id, arg_1, arg_2, command, ftp = task
		ftp = ftp.split()
		server = ftp[0]
		try:
			login = ftp[1]
			password = ftp[2]
		except:
			login = ''
			password = ''

		task = arg_1 + ' ' + arg_2 + ' ' + str(command.split()) + ' ' + str((server, login, password))
		print ('\tTask sent:\nArgument 1: {}\nArgument 2: {}\nTo: {}\n'.format(arg_1, arg_2, name))
		con.send(task.encode('utf-8'))

	def controller_availability(self):
		'''This method should be executed by a thread.
		Verify if exists tasks to be executed and Clients to execute them'''
		
		global CLOSE

		while not CLOSE:
			try:
				try:
					self.lock_clients_online.acquire(True)
					condition = self.online_clients and self.online_clients[self.get_less_overloaded()] < MAX_TASKS
				finally:
					self.lock_clients_online.release()
				
				if condition:		
					try:
						self.lock.acquire(True)
						if self.db.get_task():
							self.distribute_task()
					except:
						pass
					finally:
						self.lock.release()
			except:
				continue

	def accept_clients_connection(self):
		'''This method should be executed by a thread.
		Accept Clients connections'''

		global CLOSE

		while not CLOSE:
			con, addr = self.s.accept()
			name = con.recv(4096).decode('utf-8')

			try:
				self.lock.acquire(True)
				self.db.connect_client(name)
				print('\n{} connected to the Server.\n'.format(name))
			finally:
				self.lock.release()
			
			self.online_clients[(name,con)] = 0
			
			thread_recv_message = threading.Thread(target = self.receive_message, args = (name, con))
			thread_recv_message.daemon = True
			thread_recv_message.start() 

	def close_server(self):
		'''Close the TCP connection and write information in database when closes program. It can be close either by CTRL+C keys or by '/Exit' command'''

		self.close_TCP_connection()
		os._exit(1)