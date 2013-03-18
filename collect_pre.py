#!/usr/bin/python3
#  collect_pre.py
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
import argparse
import libs.mpd as mpd
import libs.common as common

if __name__ == "__main__":
	## Parse command line arguments:
	parser = argparse.ArgumentParser(description='Logger daemon for MPDstats')
	parser.add_argument('-c', '--config', help="The config file to use.", required=True)
	parser.add_argument('-p', '--profile', help="The profile to use.", required=True)
	args = parser.parse_args()
	## Get configuration:
	config = common.read_config(args)
	## Wait until mpd is ready:
	while True:
		try:
			client = mpd.MPDClient()
			client.timeout = None
			client.connect(config["mpd"]["host"], config["mpd"]["port"])
			client.disconnect()
		except:
			pass
		else:
			break
