#!/usr/bin/python3
import sqlite3
import io
import sys

class Database:
	'''Server database implementation
	To save changes after modifying the database it is necessary to call the method save_changes'''

	def __init__(self, name = ':memory:'):
		'''Init the database'''

		self.con = sqlite3.connect(name, check_same_thread = False)
		try:
			self.create_tables()
		except:
			print("Error creating tables")
			pass
		
	def print_database(self):
		'''This function is useful for DEBUG'''

		cursor = self.con.cursor()
		
		def print_lines_db():
			try:
				for line in cursor.fetchall():
					print (line)
			except:
				print("ERROR")

		print('clients:')
		cursor.execute( """ SELECT * FROM clients;""")
		print_lines_db()

		print('tasks:')
		cursor.execute( """ SELECT * FROM tasks;""")
		print_lines_db()

	def connect_client(self, name):
		''' Insert client in clients table
		If client already exists, put it as connected'''

		cursor = self.con.cursor()

		cursor.execute('SELECT client FROM clients WHERE client = ?', (name,))
		exists = cursor.fetchone()
		
		if not exists:
			#First time that the client connect to server
			cursor.execute("""
				INSERT INTO clients (client, done_tasks, connected)
				VALUES (?, ?, ?)
				""", (name, 0, True))
		else:
			#Client has been connected sometime, so now, just update the status to online
			self.set_client(name, True)

	def set_client(self, name, connected):
		'''To use this method the client needs to be in clients table
		Put in clients table from database if client is connected(1) or disconnected(0) at the moment'''
		
		cursor = self.con.cursor()

		cursor.execute("""
			UPDATE clients SET connected = ? WHERE client = ?
			""", (connected, name))

	def add_tasks(self, arguments):
		''' Inserts tasks in tasks table
		arguments should be a tuple list
		Each tuple represents argument_1, argument_2 and sent(0) at tasks table from database'''

		cursor = self.con.cursor()

		cursor.executemany("""
			INSERT INTO tasks (argument_1, argument_2, sent, command, ftp)
			VALUES (?, ?, ?, ?, ?)
			""", arguments)

		self.save_changes()

	def get_client_tasks(self, name):
		'''Returns a tasks list where client is executing and haven't send the output file, in other words, unfinished tasks'''
	
		cursor = self.con.cursor()
		cursor.execute('SELECT id FROM tasks WHERE name_ip = ? and output IS NULL ', (name,))

		return cursor.fetchall()


	def get_task(self):
		'''Returns a tuple (arg_1, arg_2) if exists a task to execute, else returns None'''

		cursor = self.con.cursor()

		cursor.execute('SELECT id, argument_1, argument_2 FROM tasks WHERE sent = ?', (False,))
		return cursor.fetchone() 

	def get_all_tasks(self):
		''' Take all tasks. Returns a tasks tuple'''

		cursor = self.con.cursor()

		cursor.execute('SELECT id, argument_1, argument_2, command, ftp FROM tasks WHERE sent = ?', (False,))
		return cursor.fetchall()

	def get_task_id(self, argument_1, argument_2):
		'''Returns the task ID of argument_1 and argument_2'''

		cursor = self.con.cursor()

		cursor.execute('SELECT id FROM tasks WHERE argument_1 = ? and argument_2 = ?', (argument_1, argument_2))
		return cursor.fetchone()

	def update_incomplete_task(self, update):
		'''Take tasks IDs list that were not sucessfully completed by client and change sent value to False '''

		cursor = self.con.cursor()

		cursor.executemany("""
			UPDATE tasks
			SET sent = ?
			WHERE id = ?
			""", update)

		self.save_changes()

	def update_output(self, arg_1, arg_2, task_received_date, output_filename):
		'''Update the output file and task reception time'''

		cursor = self.con.cursor()

		cursor.execute("""
			UPDATE tasks
			SET task_received_date = ?, output = ?
			WHERE argument_1 = ? and argument_2 = ?
			""", (task_received_date, output_filename, arg_1, arg_2))

		self.save_changes()

	def update_sent_task(self, update):
		'''Task sent to client, update: name_ip, task_sent_date and sent'''

		cursor = self.con.cursor()

		cursor.executemany("""
			UPDATE tasks
			SET name_ip = ?, task_sent_date = ?, sent = ?
			WHERE id = ?
			""", update)

		self.save_changes()

	def client_done_task(self, name):
		'''Increments the sent tasks number from client'''

		cursor = self.con.cursor()

		cursor.execute('SELECT done_tasks FROM clients WHERE client = ?', (name,))
		num_done_tasks = cursor.fetchone()
		num_done_tasks = num_done_tasks[0] + 1

		cursor.execute("""
			UPDATE clients
			SET done_tasks = ?
			WHERE client = ?
			""", (num_done_tasks, name)) 

		self.save_changes()

	def save_changes(self):
		'''Save changes at database'''

		self.con.commit()
	
	def create_tables(self):
		'''Create tables at database'''

		cursor = self.con.cursor()
		
		#Create clients table
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS clients(
			client TEXT NOT NULL PRIMARY KEY,
			done_tasks INTEGER NOT NULL,
			connected BOOLEAN NOT NULL
			);
			""")

		#Create tasks table
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS tasks(
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
			name_ip TEXT,
			argument_1 TEXT NOT NULL,
			argument_2 TEXT NOT NULL,
			task_sent_date DATE,
			sent BOOLEAN NOT NULL,
			command TEXT NOT NULL,
			task_received_date DATE,
			ftp TEXT NOT NULL,
			output TEXT,
			unique(argument_1,argument_2) ON CONFLICT IGNORE
			);
			""")