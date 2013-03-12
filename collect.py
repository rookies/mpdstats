#!/usr/bin/python3
#  collect.py
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
import sys
import libs.mpd as mpd

class StatsCollector (object):
	client = None
	
	def __init__ (self, host="localhost", port=6600, timeout=None, password=None):
		self.client = mpd.MPDClient()
		self.client.timeout = timeout
		self.client.connect(host, port)
		if password is not None:
			self.client.password(password)
	def __del__ (self):
		self.client.disconnect()
	def getsong (self):
		## Get current song:
		res = self.client.currentsong()
		## Check if title and artist are set:
		if not "title" in res or not "artist" in res:
			## ... and abort if not:
			return False
		## Create return array:
		ret = {
			"title": res["title"],
			"artist": res["artist"]
		}
		## Set album title:
		if "album" in res:
			ret["album"] = res["album"]
		## Set genre:
		if "genre" in res:
			ret["genre"] = res["genre"]
		## Set date:
		if "date" in res:
			try:
				ret["date"] = int(res["date"])
			except:
				pass
		## Set track:
		if "track" in res:
			if res["track"].find("/"):
				tmp = res["track"].split("/")
				try:
					ret["track"] = int(tmp[0])
				except:
					pass
				try:
					ret["trackall"] = int(tmp[1])
				except:
					pass
			else:
				try:
					ret["track"] = int(res["track"])
				except:
					pass
		## Return the result:
		return ret
	def wait (self):
		self.client.idle("player")

if __name__ == "__main__":
	c = StatsCollector()
	try:
		while True:
			print(c.getsong())
			c.wait()
	except KeyboardInterrupt:
		sys.exit(0)
