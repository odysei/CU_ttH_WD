#!/usr/bin/python

#
# Contains a submission_maker class, which is the core of the .py file.
#

import logging
import os
import re
import shutil
import subprocess
import sys
import yaml
#import ROOT


#cmssw_base = os.environ['CMSSW_BASE']
#current_dir = os.environ['PWD']



class submission_maker:
	"""class is intended to serve as a simple, generic, and easily configurable
	cluster submission maker. Each submission packet must be provided by an
	external tool, which is defined in 'project_config'."""
	
	## options are supposed to be updated by config file(s)
	options = {'my_name': 'batch_cluster',
		'config_file': 'Configs/batch_cluster_reference.yaml',
		'log_filename': 'batch_cluster.log',
		'console_vebosity': 'errors',
		'submit_type': 'runtime',
		'submit_all_file': 'submit_all.run',
		'batch_executable': 'qsub',
		'allowed_maximum_jobs': 10000,
		'job_config_src_path': 'Utilities/module_warehouse/batch_cluster/',
		'job_config_src_file': 'batch_PBS_default_config.job',
		'submission_dirnames': 'submission_',
		'place_submission_dirs_in': 'Outputs',
		'expected_run_duration': '20:00:00',
		'job_nodes': '1',
		'processors_per_node': '1',
		'job_memory': '1000mb',
		'project_input_path': 'Input/examples/batch_cluster/',
		'project_config': 'example.yaml',
		'project_name': 'cluster_run',
		'submission_maker': 'create_submission.py',
		'outputs_a_dir': False,
		'output_dir_name': 'submit',
		'output_files': ['test.dat', 'test.sh'],
		'executable': 'run_me.sh',
		'execute_as': 'bash',
		}
	
	
	def __init__(self, config):
		self.load_yaml_config(config)
		
		## Load a submission paket maker's config
		self.load_yaml_config_dependent(
			os.path.join(self.options['project_input_path'],
				self.options['project_config']))
		
		self.initialize_logger(self.options['log_filename'])
		
		self.__loaded_job_config_src = False
	
	
	### Methods follow below
	def load_yaml_config(self, input_config=None):
		"""Used to initialize a class using parameters from a config file"""
		
		if os.path.lexists(input_config):
			with open(input_config, 'r') as config_file:
				config = yaml.load(config_file)
			
			self.options['config_file'] = input_config
			
			self.options['project_input_path'] = config[
				"Generic"]["project_input_path"]
			self.options['project_config'] = config[
				"Generic"]["project_config"]
			self.options['log_filename'] = config[
				"Generic"]["log_filename"]
			self.options['console_vebosity'] = config[
				"Generic"]["console_vebosity"]
			
			self.options['batch_executable'] = config[
				"submission_specifics"]["batch_executable"]
			self.options['allowed_maximum_jobs'] = config[
				"submission_specifics"]["allowed_maximum_jobs"]
			self.options['job_config_src_path'] = config[
				"submission_specifics"]["job_config_src_path"]
			self.options['job_config_src_file'] = config[
				"submission_specifics"]["job_config_src_file"]
			self.options['submission_dirnames'] = config[
				"submission_specifics"]["submission_dirnames"]
			self.options['place_submission_dirs_in'] = config[
				"submission_specifics"]["place_submission_dirs_in"]
			self.options['expected_run_duration'] = config[
				"submission_specifics"]["expected_run_duration"]
			self.options['job_nodes'] = config[
				"submission_specifics"]["nodes"]
			self.options['processors_per_node'] = config[
				"submission_specifics"]["processors_per_node"]
			self.options['job_memory'] = config[
				"submission_specifics"]["memory"]
			
			self.options['submit_type'] = config[
				"execution_specifics"]["task_submission_type"]
			self.options['submit_all_file'] = config[
				"execution_specifics"]["multiple_submission_file"]
			
		else:
			raise RuntimeError, 'A config file ' + input_config +\
				' does not exist.'
	
	
	def load_yaml_config_dependent(self, input_config=None):
		"""Used to read submission paket maker's config, which has common
		settings."""
		
		if os.path.lexists(input_config):
			with open(input_config, 'r') as config_file:
				config = yaml.load(config_file)
			
			self.options['project_name'] = config[
				"batch_cluster"]["project_name"]
			self.options['submission_maker'] = config[
				"batch_cluster"]["submission_maker"]
			self.options['outputs_a_dir'] = config[
				"batch_cluster"]["outputs_a_dir"]
			self.options['output_dir_name'] = config[
				"batch_cluster"]["output_dir_name"]
			self.options['output_files'] = config[
				"batch_cluster"]["output_files"]
			self.options['executable'] = config[
				"batch_cluster"]["executable"]
			self.options['execute_as'] = config[
				"batch_cluster"]["execute_as"]
			
			#Adjustments to names for local needs
			self.options['submission_maker'] = re.sub('.py', '',\
										self.options['submission_maker'])
			
		else:
			raise RuntimeError, 'A config file ' + input_config +\
				' does not exist.'
	
	
	def initialize_logger(self, log_filename):
		"""Loads a logger that is to be used by the class."""
		
		#if is_logger_initialized:
			#return 0
		
		log_existed = False

		if os.path.lexists(log_filename):
			log_existed = True
		
		# logging class format for both console and file outputs
		logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		
		logging.basicConfig(format=logging_format,\
			filename=log_filename,\
			level=logging.INFO)
		self.logger = logging.getLogger(self.options['my_name'])
		
		# console handler
		ch = logging.StreamHandler()
		if self.options['console_vebosity'] == 'errors':
			ch.setLevel(logging.ERROR)
		elif self.options['console_vebosity'] == 'warnings':
			ch.setLevel(logging.WARNING)
		else:
			ch.setLevel(logging.INFO)
		
		# create formatter
		formatter = logging.Formatter(logging_format)
		
		## add formatter to ch and to a log
		ch.setFormatter(formatter)
		
		# add ch to logger
		self.logger.addHandler(ch)
		
		if log_existed:
			self.logger.warning('A log file ' + log_filename +\
				' already exists. Appending.')
		
		#is_logger_initialized = True
	
	
	def make_submissions(self):
		"""Makes submissions based on provided config settings. Each
		submission packet is provided by an external code."""
		
		if not os.path.isfile(os.path.join(self.options['project_input_path'],
										   self.options['submission_maker'] +\
											   '.py')):
			raise RuntimeError, 'Submission maker does not exist!'
		
		## Dynamically load a provided submission-packet maker
		sys.path.append(self.options['project_input_path'])
		submission = __import__(self.options['submission_maker'], globals(),
								locals(), [], -1)
		
		## Easy to make string here. It is not necessarily used later
		src_dir = os.path.join(self.options['project_input_path'],
							   self.options['output_dir_name'])
		
		## Make and move submissions packets to their execution place
		for it in xrange(0, self.options['allowed_maximum_jobs']):
			if it == self.options['allowed_maximum_jobs']:
				raise RuntimeError, 'Maximum allowed number of jobs' +\
					' reached. Limit: ' +\
						str(self.options['allowed_maximum_jobs'])
			
			status = self.__make_submission_packet(submission, src_dir, it)
			
			## Trying to close a cycle
			if status != submission.EXIT_SUCCESS:
				break
		
		return 0
	
	
	def __make_submission_packet(self, packet_maker, src_dir, it):
		## Produce a submission packet, read out status
		status = packet_maker.main([self.options['project_name'], it])
		
		if status != packet_maker.EXIT_SUCCESS:
			if status == packet_maker.EXIT_CYCLE_ENDED:
				self.logger.info('A last job has been reached.' +\
					' Job number: ' + str(it))
			else:
				self.logger.error('An error in ' +\
					self.options['submission_maker'] +\
						' occured. Error code ' + str(status))
				return status
		
		## Create a path string for a designated submission
		target_dir = os.path.join(self.options['place_submission_dirs_in'],
							self.options['submission_dirnames']) +\
								self.options['project_name'] + str(it)
		target_dir = os.path.join(os.getcwd(), target_dir)
		
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)
		
		## Move produced submission packet to a designated location
		if self.options['outputs_a_dir']:
			shutil.move(src_dir, target_dir)
		else:
			for item in self.options['output_files']:
				src_file = os.path.join(self.options['project_input_path'],
										item)
				if not os.path.isfile(src_file):
					raise RuntimeError, 'File for submission ' +\
						src_file + ' is missing'
				shutil.move(src_file, os.path.join(target_dir, item))
		
		## Put an execution script for a cluster system in a designated loc
		job_runner = os.path.join(target_dir,
								  self.options['project_name'] + str(it) +\
									  '.job')
		self.__put_job_runner(target_dir, it, job_runner)
		
		## Submit created jobs
		if self.options['submit_type'] == "runtime":
			subprocess.check_output([self.options['batch_executable'],
									job_runner])
			
		elif self.options['submit_type'] == "file":
			with open(self.options['submit_all_file'], "a") as sumbmit_all_file:
				sumbmit_all_file.write(self.options['batch_executable'] +\
					' ' + job_runner + '\n')
		
		return status
	
	
	def __put_job_runner(self, target_dir, job_nr, job_runner=None):
		"""Produces an actual submission file to be processed by a cluster
		job submission system. This file serves mostly as a run initializer
		and a settings file."""
		
		## Load a default source file for default job config
		if not self.__loaded_job_config_src:
			self.__load_job_config_src()
		
		execution_file = os.path.join(target_dir,
												self.options['executable'])
		if not os.path.exists(execution_file):
			self.logger.error("Can't find %s" % execution_file)
			sys.exit(1)
			
		
		if self.options['submit_type'] == "file":
			if os.path.lexists(self.options['submit_all_file']):
				self.logger.warning('A submit file ' +\
					self.options['submit_all_file'] +\
						' already exists. Appending.')
		
		### Create specialized files for jobs. Submit jobs
		job_config = self.__make_substitutes(target_dir,
											 job_nr,
											 self.job_config_src)
		
		out_file_job_config = open(job_runner ,"w")
			
		for item in job_config:
			out_file_job_config.write("%s\n" % item)
				
		out_file_job_config.close()
	
	
	def __load_job_config_src(self):
		"""Loads a default source file for default job config"""
		
		job_config_src_file = os.path.join(
			self.options['job_config_src_path'],
			self.options['job_config_src_file'])
		
		if not os.path.exists(job_config_src_file):
			self.logger.error("Can't find %s" % job_config_src_file)
			sys.exit(1)
		
		with open(job_config_src_file) as inputfile:
			self.job_config_src = inputfile.read().splitlines()
		
		self.__loaded_job_config_src = True
	
	
	def __make_substitutes(self, target_dir, job_nr, job_config_src):
		"""Makes substitutes to a provided string list"""
		
		job_config = []
		
		## Loop over the file/strings in the memory
		for i2 in xrange(0, len(job_config_src)):
			# replace the dummy strings
			job_config.append(re.sub('<SUBMISSION>',
							target_dir,
							job_config_src[i2]))
			job_config[i2] = re.sub('<JOBNAME>',
						   self.options['project_name'] + str(job_nr),
						   job_config[i2])
			job_config[i2] = re.sub('<EXECUTE_THIS>',
						   self.options['executable'],
						   job_config[i2])
			job_config[i2] = re.sub('<RUN_DURATION>',
						   self.options['expected_run_duration'],
						   job_config[i2])
			job_config[i2] = re.sub('<NR_OF_NODES>',
						   self.options['job_nodes'],
						   job_config[i2])
			job_config[i2] = re.sub('<PROCESSORS_PER_NODE>',
						   self.options['processors_per_node'],
						   job_config[i2])
			job_config[i2] = re.sub('<PROCESS_MEMORY>',
						   self.options['job_memory'],
						   job_config[i2])
			
		return job_config



def main(argv=None):
	if argv is None:
		argv = sys.argv
	
	if len(argv) < 2:
		print 'Choose a config file for this task, like: ' +\
			submission_maker.options['config_file'] + '.\n' + '\tUsage: ' +\
			submission_maker.options['my_name'] + '.py ' +\
			submission_maker.options['config_file']
		
		sys.exit(1)
	
	### Load submission maker with a given config
	maker = submission_maker(argv[1])
	
	### Make submissions using an external packet maker
	maker.make_submissions()
	
	
	return 0



if __name__ == "__main__":
	sys.exit(main())

