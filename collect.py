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
import sys, threading
import libs.mpd as mpd

class StatsCollector (object):
	client = None
	songid = -1
	logged_songid = -1
	elapsed = 0
	duration = 0
	song_fancy = None
	
	def __init__ (self, host="localhost", port=6600, timeout=None, password=None):
		## Connect to mpd:
		self.client = mpd.MPDClient()
		self.client.timeout = timeout
		self.client.connect(host, port)
		if password is not None:
			self.client.password(password)
		## Init timer:
		self.init_timer()
	def __del__ (self):
		self.client.disconnect()
	def init_timer (self):
		self.timer = threading.Timer(1., self.elapse)
	def getstatus_state (self):
		## Get status:
		res = self.client.status()
		## Return state:
		return res["state"]
	def getstatus_time (self):
		## Get status:
		res = self.client.status()
		## Return time:
		return {
			"elapsed": int(res["time"].split(":")[0]),
			"duration": int(res["time"].split(":")[1])
		}
	def getsong_id (self):
		## Get current song:
		res = self.client.currentsong()
		## Return ID:
		return int(res["id"])
	def getsong_fancy (self):
		## Get current song:
		res = self.client.currentsong()
		## Check if title and artist are set:
		if not "title" in res or not "artist" in res:
			## ... and abort if not:
			return False
		## Create return array:
		ret = {
			"title": res["title"],
			"artist": res["artist"],
			"duration": int(res["time"])
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
					ret["tracks"] = int(tmp[1])
				except:
					pass
			else:
				try:
					ret["track"] = int(res["track"])
				except:
					pass
		## Return the result:
		return ret
	def log (self, msg):
		print(msg, file=sys.stderr)
	def wait (self):
		self.client.idle("player")
	def scrobble (self, song):
		print(song)
	def elapse (self):
		self.elapsed += 1
		if self.duration != 0 and self.elapsed > round(self.duration/2.) and self.songid != self.logged_songid:
			self.scrobble(self.song_fancy)
			self.logged_songid = self.songid
		self.init_timer()
		self.timer.start()
	def run (self):
		state = self.getstatus_state()
		if state == "play":
			self.log("Play state received.")
			t = self.getstatus_time()
			self.elapsed = t["elapsed"]
			self.duration = t["duration"]
			self.songid = self.getsong_id()
			self.song_fancy = self.getsong_fancy()
			self.timer.cancel()
			self.init_timer()
			self.timer.start()
		elif state == "stop":
			self.log("Stop state received.")
			self.elapsed = 0
			self.timer.cancel()
		elif state == "pause":
			self.log("Pause state received.")
			self.elapsed = self.getstatus_time()["elapsed"]
			self.songid = self.getsong_id()
			self.song_fancy = self.getsong_fancy()
			self.timer.cancel()
		self.wait()

if __name__ == "__main__":
	c = StatsCollector()
	try:
		while True:
			c.run()
	except KeyboardInterrupt:
		sys.exit(0)
