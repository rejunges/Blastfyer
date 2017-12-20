#!/usr/bin/python3
from ftplib import FTP 

class FTP_Transfer():
	'''Class for transfer files from Server to Client and verify files and folders'''
	
	def __init__(self, FTP_server, login = '', password = ''):
		'''Store the ip ftp server, login and password '''
		
		self.FTP_server = FTP_server
		self.login = login
		self.password = password

	def pick_files(self, path):
		'''Pick the filenames in path and return them or return -1 if the path was not found at FTP Server'''

		result = self.FTP_connect()
		abs_path = self.ftp.pwd()

		if not result == True:
			#Occurs some error
			print('Error at FTP connection.')
			return False

		if not self.check_folder(path):
			return -1
		
		files_and_folders = self.ftp.nlst()
		files = []

		for file_or_folder in files_and_folders:
			try:
				#If the filename is a file then it has a size, otherwise, except
				self.ftp.size(file_or_folder) 
				files.append(file_or_folder)
			except:
				continue

		self.ftp.cwd(abs_path)
		self.FTP_close()

		return files

	def check_folder(self, path):
		'''Verify if folder exist'''

		path_ftp = self.ftp.pwd()
		try:
			self.ftp.cwd(path)
		except:
			return False

		return True

	def check_or_create_folder(self, path):
		'''If the folders in path do not exist it is created'''

		result = self.FTP_connect()
		abs_path = self.ftp.pwd()

		if not result == True:
			#Occurs some error
			print('Error at FTP connection.')
			return False

		list_folders = path.split('/')

		for folder in list_folders:
			if not self.check_folder(folder):
				try:
					self.ftp.mkd(folder)
				except:
					return False
				self.ftp.cwd(folder)

		self.ftp.cwd(abs_path)
		self.FTP_close()
		return True 
		
	def download(self, file):
		'''Download a file from Server
		If occurs some connection error the function returns:
			-1 (for TimeoutError)
			-2 (for login and password error)
			-3 (for download file error)
		Else the fuction returns True'''

		result = self.FTP_connect()
		abs_path = self.ftp.pwd()
		
		if not result == True:
			#Occurs some error
			return result

		file = file.split('/') 
		path = file[:-1] 
		path = '/'.join(path)

		result = True
		try:
			self.ftp.cwd(path)
			self.ftp.retrbinary('RETR ' + file[-1], open(file[-1], 'wb').write)

		except:
			result = -3

		self.ftp.cwd(abs_path)
		self.FTP_close()

		return result
		

	def FTP_connect(self):
		'''Connect to FTP Server using login and password
		If occurs some connection error the function returns: 
			-1 (for TimeoutError)
			-2 (for login and password error)
		Else the function returns True.'''

		try:
			self.ftp = FTP(self.FTP_server)
		except TimeoutError:
			#Server is not connected
			return -1

		if self.login and self.password:
			result = self.ftp.login(self.login, self.password)
		else:
			result =self.ftp.login()

		if '230' in result:
			return True
		else:
			return -2

	def upload(self, file, upload_path):
		''' Upload a file to Server
		If occurs some connection error the function returns:
			-1 (for TimeoutError)
			-2 (for login and password error)
			-3 (for upload error)
		Else the function returns True'''

		result = self.FTP_connect()
		abs_path = self.ftp.pwd()

		if not result == True:
			#Occurs some error
			return result

		upload_file = open(file, 'rb')
		result = True

		try:
			self.ftp.cwd(upload_path)
			self.ftp.storbinary('STOR ' + file, upload_file)
		except:
			result = -3

		upload_file.close()
		self.ftp.cwd(abs_path)
		self.FTP_close()

		return result

	def FTP_close(self):
		'''Close FTP connection'''
		
		self.ftp.quit()
