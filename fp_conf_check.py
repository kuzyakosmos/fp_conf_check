#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from os import listdir
import glob, shutil
import subprocess
import zipfile
import sys
import yaml	
from datetime import datetime, date, time
import re
import json
import jinja2
from jinja2 import Template

lscomm="";
for i in range(80):
	lscomm=lscomm+"-";

# Проверка на ASCII символы
def is_ascii(s):
	print lscomm
	print "Проверка ASCII"
	print lscomm
	return all(ord(i) < 128 for i in s)

# Проверка структуры ФП
def fp_structure():
	print lscomm
	print "Проверка структуры ФП"
	print lscomm

	check = True

	# Проверка package/conf/config
	if (list(set(['parameters', 'definitions']) - set(os.listdir('package/conf/config'))) == []):
		print 'package/conf/config OK'
	else:
		print 'Ошибка в названии папки ', list(set(['parameters', 'definitions']) - set(os.listdir('package/conf/config')))
		check = False

	# Проверка package/conf
	if (list(set(['distrib.yml']) - set(os.listdir('package/conf'))) == []):
		print 'package/conf OK'
	else:
		print 'Ошибка в названии файла ', list(set(['distrib.yml']) - set(os.listdir('package/conf')))
		check = False

	if check == False:
		return False
	else:
		return True

#Проверка валидности yml файлов
def check_yaml():
	print lscomm
	print "Проверка корректности yaml файлов"
	print lscomm

	for root, dirs, files in os.walk(os.path.join('../..', sys.argv[1])):
		for file in files:
			if file.endswith('.yml'):
				with open (os.path.join(root, file), 'r') as stream:
					try:
						a = yaml.load(stream)
						print "OK " + file
					except yaml.YAMLError as exc:
						print "Ошибка в " + file
						print (exc)
						pass

def bom_check():
	print lscomm
	print "Проверка BOM"
	print lscomm

	check = True

	for root, dirs, files in os.walk(os.path.join('../..', sys.argv[1])):
		for file in files:
			if file.endswith('.yml'):
				
				raw2 = open(os.path.join(root,file), 'rb').read(2)
				byte2 = ":".join("{:02x}".format(ord(c)) for c in raw2)
				if byte2 == 'fe:ff':
					print "ERROR! BOM in " + os.path.join(root,file)
					check = False
				if byte2 == 'ff:fe':
					print "ERROR! BOM in " + os.path.join(root,file)
					check = False

				raw4 = open(os.path.join(root,file), 'rb').read(4)
				byte4 = ":".join("{:02x}".format(ord(c)) for c in raw4)
				if byte4 == '00:00:fe:ff':	
					print "ERROR! BOM in " + os.path.join(root,file)
					check = False
				if byte4 == 'fe:ff:00:00':
					print "ERROR! BOM in " + os.path.join(root,file)
					check = False
				if check: print "OK " + file
	
	if check == False:
		return False
	else:
		return True


def yml_comments_check():
	print lscomm
	print "Проверка комментариев в yml файлах"
	print lscomm

	check = True

	for root, dirs, files in os.walk(os.path.join('../..', sys.argv[1])):
		for file in files:
			if file.endswith('.yml'):
				with open (os.path.join(root,file), 'r') as stream:
					for i in stream:
						# print i
						if re.search(r'#', i) != None:
							result = re.split(r'#', i)
							if re.search(r'\S', result[0]) != None:
								print "В файле "+os.path.join(root,file)+" неправильный комментарий в строчке "+i
								check = False

	for root, dirs, files in os.walk('package'):
		for file in files:
			if file.endswith('.yml'):
				with open (os.path.join(root,file), 'r') as stream:
					for i in stream:
						# print i
						if re.search(r'#', i) != None:
							result = re.split(r'#', i)
							if re.search(r'\S', result[0]) != None:
								print "В файле "+os.path.join(root,file)+" неправильный комментарий в строчке "+i
								check = False

	if check == False:
		return False
	else:
		return True

def inventory_user_pass():
	print lscomm
	print "Проверка переменных inventory для доступа к хосту по SSH"
	print lscomm

	inventory = os.path.join('../..', sys.argv[1], 'inventory')	

	with open (inventory) as f:
		my_lines = f.read()

		for i in my_lines.split('['):

			section = i.split(']')[0].strip()
			check = True
			if re.search(r'^was', section):
				for data in i.split('\n'):
					row = ''.join(data.split())
					if not re.search(r'^was(.*)|^#(.*)', row) and row != '':
						if re.search(r'ansible_user="{{NODE_SSH_USER}}"', row) == None:
							print 'Переменная ansible_user отличается от шаблонного значения для группы [%s]' % section
							check = False
						if re.search(r'ansible_ssh_pass="{{NODE_SSH_PASS}}"', row) == None:
							print 'Переменная ansible_ssh_pass отличается от шаблонного значения для группы [%s]' % section
							check = False
				if check: print 'OK [%s]' % section

			check = True
			if re.search(r'^dmgr(.*)', section):
				for data in i.split('\n'):
					row = ''.join(data.split())
					if not re.search(r'^dmgr(.*)|^#(.*)', row) and row != '':
						if (re.search(r'ansible_user="{{DMGR_SSH_USER}}"', row) == None) and (re.search(r'ansible_user="{{NODE_SSH_USER}}"', row) == None):
							print 'Переменная ansible_user отличается от шаблонного значения для группы [%s]' % section
							check = False
						if (re.search(r'ansible_ssh_pass="{{DMGR_SSH_PASS}}"', row) == None) and (re.search(r'ansible_ssh_pass="{{NODE_SSH_PASS}}"', row) == None):
							print 'Переменная ansible_ssh_pass отличается от шаблонного значения для группы [%s]' % section
							check = False
				if check: print 'OK [%s]' % section

			check = True
			if re.search(r'^nginx(.*)', section) and not re.search(r'^nginx_was(.*)', section):
				for data in i.split('\n'):
					row = ''.join(data.split())
					if not re.search(r'^nginx(.*)|^#(.*)', row) and row != '':
						if re.search(r'ansible_user="{{NGINX_SSH_USER}}"', row) == None:
							print 'Переменная ansible_user отличается от шаблонного значения для группы [%s]' % section
							check = False
						if re.search(r'ansible_ssh_pass="{{NGINX_SSH_PASS}}"', row) == None:
							print 'Переменная ansible_ssh_pass отличается от шаблонного значения для группы [%s]' % section
							check = False
				if check: print 'OK [%s]' % section

			check = True
			if re.search(r'^wxs(.*)', section):
				for data in i.split('\n'):
					row = ''.join(data.split())
					if not re.search(r'^wxs(.*)|^#(.*)', row) and row != '':
						if re.search(r'ansible_user="{{WXS_SSH_USER}}"', row) == None:
							print 'Переменная ansible_user отличается от шаблонного значения для группы [%s]' % section
							check = False
						if re.search(r'ansible_ssh_pass="{{WXS_SSH_PASS}}"', row) == None:
							print 'Переменная ansible_ssh_pass отличается от шаблонного значения для группы [%s]' % section
							check = False
				if check: print 'OK [%s]' % section

	if check == False:
		return False
	else:
		return True

#Проверка валидности json файлов
def check_json():
	print lscomm
	print "Проверка корректности json файлов"
	print lscomm

	check = True
	for root, dirs, files in os.walk('package/conf/config/definitions'):
		for file in files:
			if file.endswith('.json'):
				with open (os.path.join(root, file), 'r') as stream:
					try:
						a = json.load(stream)
						print "OK " + file
					except Exception as exc:
						print "Ошибка в " + file
						print (exc)
						print "\n"
						pass
	if check == False:
		return False
	else:
		return True

# Проверка пустого inventory
def empty_inventory():
	print lscomm
	print "Проверка пустого inventory"
	print lscomm
	
	inventory = os.path.join('../..', sys.argv[1], 'inventory')
	
	if (os.stat(inventory).st_size == 0):
		return False
		print "Пустой inventory"
	else:
		with open (inventory, 'r') as f:
			for i in f:
				if i[0] != '#':
					print "Inventory OK"
					return True
		return False
		print "Пустой inventory"

def check_dmgr(): 
	print lscomm
	print "Проверка корректности заполнения inventory для серверов dmgr"
	print lscomm

	inventory = []
	custom_property = []

	if os.path.isfile(os.path.join('../..', sys.argv[1], 'inventory')):
		with open (os.path.join('../..', sys.argv[1], 'inventory'), "r") as stream:
			for i in stream.readlines():
				if i[0:5] == '[dmgr':
					i = re.sub(r':children','',i)
					i = re.sub(r']','',i)
					i = i[1:]
					inventory.append(i.rstrip('\r\n'))

	if os.path.isfile(os.path.join('../..', sys.argv[1], 'group_vars/hosts/distrib.yml')):
		with open(os.path.join('../..', sys.argv[1], 'group_vars/hosts/distrib.yml'), 'r') as stream:
			data_loaded = yaml.load(stream)

	if os.path.isfile(os.path.join('../..', sys.argv[1], 'group_vars/hosts/custom_property.yml')):
		with open(os.path.join('../..', sys.argv[1], 'group_vars/hosts/custom_property.yml'), 'r') as stream:
			data_loaded_custom = yaml.load(stream)

	if (data_loaded != None) and (data_loaded_custom != None) and ('applications' in data_loaded.keys()) and ('applications_custom' in data_loaded_custom.keys()):
		data_loaded['applications'] = data_loaded_custom['applications_custom']

	if (data_loaded != None) and ('applications' in data_loaded.keys()):
		if isinstance(data_loaded['applications'], dict):
			for k,v in data_loaded['applications'].items():
				if 'deploy_group' in data_loaded['applications'][k]:
					custom_property.append(data_loaded['applications'][k]['deploy_group'])
				else:
					custom_property.append('dmgr')
		elif isinstance(data_loaded['applications'], str):
			if re.search(r'{{',data_loaded['applications']) != None:
				print "applications описаны в виде шаблона jinja2. Не удалось выполнить проверку корректности заполнения inventory для серверов dmgr."
				return True
			else:
				dmgr_check = False
				print "Не удалось выполнить проверку корректности заполнения inventory для серверов dmgr."
				return False  
		else:
			dmgr_check = False
			print "Не удалось получить значение applications."
			return False
	else:
		dmgr_check = False
		print "Отсутствует applications. Не удалось выполнить проверку корректности заполнения inventory для серверов dmgr."
		return False

	dmgr_check = (list(set(custom_property) - set(inventory)) == [])
	# Результат проверки корректности заполнения inventory для серверов dmgr
	if dmgr_check == False:
		print "В файле inventory отсутствуют группы деплоя, описанные в distrib.yml"
		return False
	else:
		print "Dmgr OK"
		return True

def check_jinja2():
	print lscomm
	print "Проверка корректности заполнения переменных шаблонизатора jinja2 в yml файлах"
	print lscomm

	for root, dirs, files in os.walk(os.path.join('../..', sys.argv[1])):
		for file in files:
			if file.endswith('.yml'):
				check = True
				try:
					yml = open(os.path.join(root, file)).read()
					template = Template(yml)
					template.render()
					print "OK " + file
					print "\n"
				except Exception as exc:
					print 'Ошибка в  ' + file
					print exc
					print "\n"
					pass
					check = False

	if check == False:
		return False
	else:
		return True

def check_yaml_brackets():
	print lscomm
	print "Проверка наличия символов кавычек в yml файлах"
	print lscomm

	check = True
	for root, dirs, files in os.walk(os.path.join('../..', sys.argv[1])):
		for file in files:
			if file.endswith('.yml'):
				check = True
				with open (os.path.join(root,file), 'r') as stream:
					for i in stream:
						if re.search(r'{{',i) != None:
							string = i
							result = re.split(r'{{', string, maxsplit=1)
							if (re.search(r'"', result[0]) != None) or (re.search(r"'", result[0]) != None):
								pass
							else:
								print "Не хватает открывающих кавычек у jinja2 переменных в " + file
								print i
								check = False

							string = string[::-1]
							result = re.split(r'{{', string, maxsplit=1)
							if (re.search(r'"', result[0]) != None) or (re.search(r"'", result[0]) != None):
								pass
							else:
								print "Не хватает закрывающих кавычек у jinja2 переменных в " + file
								print i
								check = False
				if check: print 'OK [%s]' % file

	if check == False:
		return False
	else:
		return True

def invalid_characters():
	print lscomm
	print "Проверка конфигурационных файлов на валидность используемых символов"
	print lscomm

	for root, dirs, files in os.walk(os.path.join('../..', sys.argv[1])):
		for file in files:
			if file.endswith('.yml'):
				check = True
				with open (os.path.join(root,file), 'r') as stream:
					for i in stream:
						if re.findall('[^a-zA-Zа-яА-яёЁ0-9_.,!()\t\n-#\'\"\{\}\[\]\\\/@$%^&*<>:;? -=+|АаБбВвГгДдЕеЁёЖжЗзИиКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя]',i) != []:
							print i
							print 'Недопустимый символ в файле ' + file
							print re.findall('[^a-zA-Zа-яА-яёЁ0-9_.,!()\t\n-#\'\"\{\}\[\]\\\/@$%^&*<>:;? -=+|АаБбВвГгДдЕеЁёЖжЗзИиКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя]',i)
							check = False
				if check: print 'OK [%s]' % file

	if check == False:
		return False
	else:
		return True


def check_json_and_conf():
	print lscomm
	print "Проверка соотвествия файлов параметров и файлов json"
	print lscomm

	for root, dirs, files in os.walk('package/conf/config/definitions'):
		for file in files:
			if file.endswith('.json'):
				# Пробуем загрузить json файл
				try:
					with open (os.path.join(root, file), 'r') as stream:
						a = json.load(stream)
				except Exception as exc:
					print 'Не удается загрузить файл '+file
					print exc
					print
					continue

				# Пробуем загрузить conf файл
				try:
					conf = open(os.path.join('package/conf/config/parameters', file[:-4]+'conf'))
					conf.close()
				except Exception as exc:
					print 'Отсутствует файл '+file[:-4]+'conf'
					print exc
					print
					continue

				# Проверяем ли мы файл или пропускаем (есть ли в json item_name)
				check_file = None
				for i in a:
					if (type(a[i]) is dict) == True:
							if a[i].get('item_name') != None:
								check_file = True
				
				for i in a:

					if (type(a[i]) is dict) == True:
						if a[i].get('item_name') != None:

							item_name = a[i]['item_name']
							if a[i].get('type') == 'dataSource':
								item_name = 'jdbc.'+item_name
							
							conf = open(os.path.join('package/conf/config/parameters', file[:-4]+'conf'))
							check = False

							# Ищем значения в conf файле
							for j in conf:
								if re.match(item_name, j) != None:
									check = True
									break
							conf.close()

							if check == False:
								print 'Не найдено значений для '+str(item_name)+' в файле '+file[:-4]+'conf'
								print
								check_file = False
							

				if check_file == True:
					print 'Файл '+file[:-4]+'conf ОК'
					print

def check_global_conf():
	print lscomm
	print "Проверка соотвествия соответствия параметров в конфигурационных файлах <fp_name>.conf и _global.conf"
	print lscomm

	# Сливаем все global файлы в один
	filenames = ['../installer/system/efs/config/parameters/_global.jdbc.conf', '../installer/system/efs/config/parameters/_global.mq.conf', '../installer/system/efs/config/parameters/_global.resources.conf']
	with open ('../installer/system/efs/config/parameters/_global.concatenate.conf', 'w') as outfile:
		for fname in filenames:
			with open(fname) as infile:
				for line in infile:  
					outfile.write(line)

	for root, dirs, files in os.walk('package/conf/config/parameters'):
		for file in files:
			if file.endswith('.conf'):

				# Проверяем ли мы файл или пропускаем
				check_file = None
				with open (os.path.join(root,file), 'r') as stream:
					for i in stream:
						if re.search(r'\{global',i) != None:				
							check_file = True
							break

				with open (os.path.join(root,file), 'r') as stream:
					for i in stream:
						if re.search(r'\{global',i) != None:
							string = re.search(r'\{([_$0-9a-zA-Z.-]*)\}', i).group(1)

							outfile = open('../installer/system/efs/config/parameters/_global.concatenate.conf', 'r')
							check = False
							for j in outfile:
								if re.match(string, j) != None:
									check = True
									break
							outfile.close()		

							if check == False:
								print 'Не найдено значений для '+string+' в файле '+file
								print
								check_file = False

				if check_file == True:
					print 'Файл '+file+' ОК'
					print

	# Удаляем файл со всеми global
	os.remove('../installer/system/efs/config/parameters/_global.concatenate.conf')

def main():

	fp_structure()
	print "\n"
	check_yaml()
	print "\n"
	bom_check()
	print "\n"
	yml_comments_check()
	print "\n"
	inventory_user_pass()
	print "\n"
	check_json()
	print "\n"
	check_dmgr()
	print "\n"
	empty_inventory()
	print "\n"
	check_jinja2()
	print "\n"
	check_yaml_brackets()
	print "\n"
	invalid_characters()
	print "\n"
	check_json_and_conf()
	print "\n"
	check_global_conf()
	print "\n"

if __name__ == '__main__':
    main()