#!/usr/bin/python3
#  create.py
#  
#  Copyright 2013 Robert Knauer <robert@privatdemail.net>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#
import json, sys

def read_config (args):
	## Try to open config file:
	try:
		f = open(args.config, 'r')
	except IOError as e:
		## File not found / not readable:
		print("Error while reading configuration: %s" % e, file=sys.stderr)
		sys.exit(1)
	## Try to load JSON from config file:
	try:
		js = json.loads(f.read())
	except ValueError as e:
		print("Error while reading configuration: %s" % e, file=sys.stderr)
		sys.exit(1)
	## Check if profile exists in config file:
	if not args.profile in js:
		print("Error while reading configuration: Profile '%s' not found." % args.profile)
		sys.exit(1)
	config = js[args.profile]
	## Check existence of all config keys:
	try:
		if not "mpd" in config:
			raise ValueError("Config key 'mpd' not found.")
		if not isinstance(config["mpd"], dict):
			raise ValueError("Config key 'mpd' has invalid type.")
		if not "port" in config["mpd"]:
			raise ValueError("Config key 'mpd.port' not found.")
		if not "host" in config["mpd"]:
			raise ValueError("Config key 'mpd.host' not found.")
		if not "password" in config["mpd"]:
			raise ValueError("Config key 'mpd.password' not found.")
		if not "logfile" in config:
			raise ValueError("Config key 'logfile' not found.")
		if not "cachefile" in config:
			raise ValueError("Config key 'cachefile' not found.")
		if not "database" in config:
			raise ValueError("Config key 'database' not found.")
		## Check types of all config keys:
		if not isinstance(config["mpd"]["port"], int):
			raise ValueError("Config key 'mpd.port' has invalid type.")
		if not isinstance(config["mpd"]["host"], str):
			raise ValueError("Config key 'mpd.host' has invalid type.")
		if not isinstance(config["mpd"]["password"], str) and config["mpd"]["password"] is not None:
			raise ValueError("Config key 'mpd.password' has invalid type.")
		if not isinstance(config["logfile"], str):
			raise ValueError("Config key 'logfile' has invalid type.")
		if not isinstance(config["cachefile"], str):
			raise ValueError("Config key 'cachefile' has invalid type.")
		if not isinstance(config["database"], str):
			raise ValueError("Config key 'database' has invalid type.")
	except ValueError as e:
		print("Error while reading configuration: %s" % e, file=sys.stderr)
		sys.exit(1)
	else:
		return config
