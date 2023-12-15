
import json #Required to read modules_schema.json
import os.path as path
import concurrent.futures
import queue
import threading
import time
import shutil
import importlib.util
from contextlib import redirect_stdout
from io import StringIO

# ANSI Codes
G_COLOR = '\033[92m'
R_COLOR = '\033[91m'
O_COLOR = '\033[93m'
RESET_COLOR = '\033[0m'


'''
	Class Target: store information about targets found by modules
'''
class Target:
	def __init__(self, ip, mac, info=""):
		self.ip = ip 		#IP of target
		self.mac = mac 		#MAC of target
		self.info = info 	#Info of target

'''
	Class Display: Class Display: a structure responsible for creating objects that interact 
	with the console. Formats information to make it more readable.
'''
class Display:

	TARGETS = []  #Array of Target objects, using for store targets found by modules

	def __init__(self):
		#self.clear_console()
		self.header = self.makeHeader()		#Header of display
		self.targets_info = ""				#Information about targets found
		self.run_info = ""					#Information about the execution of the device scout

	'''
		makeHeader: make the display header
	'''
	def makeHeader(self):
		console_width, _ = shutil.get_terminal_size()	#width of terminal

		header = self.make_line()						#Add line to header

		title = "DEVICE SCOUT"							#Title of Device Scout

		for i in range((console_width-len(title))//2):	#Add space before title
			header = header + " "

		header = header + title 						#Add title

		for i in range((console_width-len(title))//2):  #Add space after title
			header = header + " "

		header = header+"\n\n"							#Add jump

		header = header + self.make_line()				#Add line 

		return header


	def setInfo(self, info):
		self.run_info = info

	def updateInfo(self, info):
		self.run_info = self.run_info + info

	def updateInfoRun(self, info, color=RESET_COLOR):
		self.run_info = color+info+"\n"+self.run_info
		self.display()

	def addTarget(self, target):
		self.TARGETS.append(target)
		self.updateTargetsInfo()

	def updateTargetsInfo(self):
		targets_info = ""
		for target in self.TARGETS:
			target_info = "\tIP: "+target.ip+"  |  MAC: "+target.mac+" |  INFO: "+target.info +"\n"
			targets_info = targets_info + target_info
		self.targets_info = targets_info
		self.display()

	def clear_console(self):
		print("\033c", end="")

	def make_line(self):
		console_width, _ = shutil.get_terminal_size()	#width of terminal
		line = ""

		for i in range(console_width):
			line =line+"-"
		line = line + "\n\n"
		return line

	def display(self):
		self.clear_console()
		print(self.header+self.targets_info+"\n"+self.make_line()+self.run_info)

'''
	Modules_Reader reads and loads all modules specified in modules_schema.json
'''

class Module:
	def __init__(self, module_name="", path="", execute_mode="", output_queue=None):
		self.module_name = module_name   	#Module name
		self.path = path 					#path of Module
		self.execute_mode = execute_mode	#Execute mode of Module
		self.output_queue = output_queue 	#Shared output queue
	'''
		Run the module depending on its programming language
		Add targets found by module to output_queue
	'''
	def run(self):
		if self.execute_mode == "python_module":
			self.python_module()
		#self.output_queue.put({'type':'target', 'value':Target('192.168.0.34', "00:11:22:33:44:55", "Linux Mint"), 'color':RESET_COLOR})
		#self.output_queue.put({'type':'run_info', 'value':self.module_name+": "+G_COLOR+"New device found"+RESET_COLOR, 'color':RESET_COLOR})

	def python_module(self):

		def get_target_module(targets):
			while True:
				if not targets.empty():
					data = targets.get()
					if data[0] == "END":
						break
					else:
						data_list = data.split("-")
						self.output_queue.put({'type':'target', 'value':Target(data_list[0],data_list[1],data_list[2]),'color':RESET_COLOR})
						self.output_queue.put({'type':'run_info','value':self.module_name+": Discover new target",'color':G_COLOR})

		module_name = self.module_name
		location_module = importlib.util.spec_from_file_location(module_name, self.path)
		module = importlib.util.module_from_spec(location_module)
		location_module.loader.exec_module(module)
		targets_module = module.get_targets()
		thread_get_targets = threading.Thread(target=get_target_module,args=(targets_module,))
		thread_get_targets.start()
		module.start_module()
		targets_module.put(['END'])
		thread_get_targets.join()



class Modules_Reader:

	MODULES = []					#Modules Array: contains Module Objects for running in parallel
	OUTPUT_QUEUE = queue.Queue()	#Queue that save outputs from threads


	def __init__(self):
		self.display = Display()	#Create Display Object
		self.display.display()		#Display
		self.load_modules()  		#Load modules from modules_schema.json
		self.run_modules()			#Run modules

	'''
		Load modules from modules_schema.json into self.MODULES
		and print the modules found
	'''
	def load_modules(self):

		#	Open and load the contents of modules_schema.json into the variable schema_data
		with open('modules_schema.json','r') as schema_file:
			schema_data = json.load(schema_file)


		#	Iterate through the data in schema_data and verify that
		#	the module exists at the path specified in modules_schema.json.
		#		If module exists -> load module
		for language_type in schema_data:


			#Print of programming language
			self.display.updateInfo(language_type.upper()+"\n")


			#Counter of modules
			modules_count = 0


			#Iterate modules into language_type and verify that the module exists at the path specified
			for module in schema_data[language_type]:
				run_info = ""  #info string for display

				#If module exists modules_count += 1 and print: module_name, path, execute_mode
				if path.exists(module['path']):
					modules_count = modules_count + 1
					run_info = "\t->"+G_COLOR+"MODULE NAME:\t"+module['module_name']+RESET_COLOR+"\n"
					run_info = run_info + "\t\t->"+G_COLOR+"PATH:\t"+module['path']+RESET_COLOR+"\n"
					run_info = run_info + "\t\t->"+G_COLOR+"EXECUTE MODE:\t"+module['execute_mode']+RESET_COLOR+"\n"

					#Load module
					module_obj = Module(module['module_name'], module['path'], module['execute_mode'], self.OUTPUT_QUEUE)
					self.MODULES.append(module_obj)


				#Else, print alert
				else:
					run_info = "\t->"+O_COLOR+"MODULE NAME:\t"+module['module_name']+RESET_COLOR+"\n"
					run_info = run_info + "\t\t->"+R_COLOR+"PATH:\t"+module['path']+RESET_COLOR+"\n"
					run_info = run_info + "\t\t->"+O_COLOR+"EXECUTE MODE:\t"+module['execute_mode']+RESET_COLOR+"\n"


				#Display modules info
				self.display.updateInfo(run_info)
				self.display.display()


			#Display modules count
			run_info = language_type + " modules load:\t"+str(modules_count)+"\n\n"
			self.display.updateInfo(run_info)
			self.display.display()

	'''
		print_queue: print data into OUTPUT_QUEUE while not finding the ending flag
	'''
	def print_queue(self):
		while(True):
			if not self.OUTPUT_QUEUE.empty():
				output_q = self.OUTPUT_QUEUE.get()
				if output_q['type'] == 'run_info' and output_q['value'] == "end of threads":	 #If find the ending flag, stop while
					break
				elif output_q['type'] == 'run_info':
					self.display.updateInfoRun(output_q['value'], output_q['color'])
				else:
					self.display.addTarget(output_q['value']) 


	'''
		Run modules from MODULES as threads in parallel and execute print_queue() to print their results
	'''
	def run_modules(self):

		with concurrent.futures.ThreadPoolExecutor() as executor:
			#Execute method run of Module Objects in self.MODULE like Threads
			threads = {executor.submit(Module.run, module): module for module in self.MODULES}

			#New Thread for print queue
			queue_thread = threading.Thread(target=self.print_queue)
			queue_thread.start()

			#Wait end of threads
			concurrent.futures.wait(threads)

			#Put finish flag into queue to stop queue_thread
			self.OUTPUT_QUEUE.put({'type':"run_info",'value':"end of threads"})
			#Wait end of queue_thread
			queue_thread.join()



'''
	Start point of Device Scout
'''
if __name__ == "__main__":
	Loader = Modules_Reader()
	