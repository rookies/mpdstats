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
import threading, time, json, argparse, sys
import libs.mpd as mpd
import libs.common as common
import pyodbc

class StatsCollector (object):
	#################
	### VARIABLES ###
	#################
	## Connections & general settings:
	config = None
	mode = 0 # 0=cachefile, 1=database
	client = None
	db = None
	cache = []
	timer = None
	## Status variables:
	songid = -1
	logged_songid = -1
	elapsed = 0
	duration = 0
	song_fancy = None
	#########################
	### GENERAL FUNCTIONS ###
	#########################
	def __init__ (self):
		self.init_timer()
	def __del__ (self):
		try:
			self.client.disconnect()
		except:
			pass
		if self.mode == 0:
			try:
				self.cache.close()
			except:
				pass
		else:
			try:
				self.db.close()
			except:
				pass
	def init_timer (self):
		self.timer = threading.Timer(1., self.elapse)
	def log (self, msg):
		print(msg, file=sys.stderr)
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
		self.client.idle("player")
	##################
	### CONNECTORS ###
	##################
	def mpd_connect (self):
		if self.client is None:
			self.client = mpd.MPDClient()
		self.client.timeout = None
		self.client.connect(self.config["mpd"]["host"], self.config["mpd"]["port"])
		if self.config["mpd"]["password"] is not None:
			self.client.password(self.config["mpd"]["password"])
	def db_connect (self):
		try:
			self.db = pyodbc.connect(self.config["database"])
			self.mode = 1
		except Exception as e:
			## Database connection failed, try to use cache file:
			try:
				f = open(self.config["cachefile"], 'a')
			except:
				raise Exception("Couldn't connect to database or cachefile. Database Error: %s" % e)
			else:
				f.close()
	#######################
	### CACHE FUNCTIONS ###
	#######################
	def open_cache (self):
		## Read from file:
		try:
			f = open(self.config["cachefile"], 'r')
		except IOError:
			self.cache = []
		else:
			data = f.read()
			f.close()
			## Try to parse as JSON:
			try:
				data = json.loads(data)
			except ValueError:
				self.cache = []
			else:
				self.cache = data
	def scrobble_cache (self):
		if self.mode is not 1:
			return
		for song in self.cache:
			self.scrobble_to_db(song)
		self.cache = []
		self.write_cache()
	def write_cache (self):
		try:
			f = open(self.config["cachefile"], 'w')
			f.write(json.dumps(self.cache))
			f.close()
		except Exception as e:
			self.log("Error while writing cache: %s" % e)
	############################
	### MPD STATUS FUNCTIONS ###
	############################
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
			"duration": int(res["time"]),
			"songid": int(res["id"])
		}
		## Set album title:
		if "album" in res:
			ret["album"] = res["album"]
		else:
			ret["album"] = ""
		## Set genre:
		if "genre" in res:
			ret["genre"] = res["genre"]
		else:
			ret["genre"] = ""
		## Set date:
		if "date" in res:
			try:
				ret["date"] = int(res["date"])
			except:
				ret["date"] = 0
		else:
			ret["date"] = 0
		## Set track:
		if "track" in res:
			if res["track"].find("/"):
				tmp = res["track"].split("/")
				try:
					ret["track"] = int(tmp[0])
				except:
					ret["track"] = 0
				try:
					ret["tracks"] = int(tmp[1])
				except:
					ret["tracks"] = 0
			else:
				ret["tracks"] = 0
				try:
					ret["track"] = int(res["track"])
				except:
					ret["track"] = 0
		else:
			ret["track"] = 0
			ret["tracks"] = 0
		## Return the result:
		return ret
	##########################
	### SCROBBLE FUNCTIONS ###
	##########################
	def scrobble_to_db (self, song):
		cursor = self.db.cursor()
		## Get last scrobbled song:
		row = cursor.execute("""
			SELECT
				`title`,
				`artist`,
				`duration`,
				`songid`
			FROM
				`scrobbles`
			ORDER BY
				`id` DESC
			LIMIT
				1
		""").fetchone()
		## Check if the same is playing now:
		if row is None or row[0] != song["title"] or row[1] != song["artist"] or row[2] != song["duration"] or row[3] != song["songid"]:
			## It's not the same, so write to database:
			cursor.execute("""
				INSERT INTO
					`scrobbles`
				SET
					`time` = ?,
					`title` = ?,
					`artist` = ?,
					`duration` = ?,
					`album` = ?,
					`genre` = ?,
					`date` = ?,
					`track` = ?,
					`tracks` = ?,
					`songid` = ?
			""", (
				time.mktime(time.gmtime()),
				song["title"],
				song["artist"],
				song["duration"],
				song["album"],
				song["genre"],
				song["date"],
				song["track"],
				song["tracks"],
				song["songid"],
			))
			self.log("Scrobbled %s" % str(song))
			cursor.commit()
		else:
			self.log("Ignored %s" % str(song))
		cursor.close()
	def scrobble_to_cache (self, song):
		self.cache.append(song)
		self.write_cache()
		self.log("Cached %s" % str(song))
	def scrobble (self, song):
		if self.mode is 1:
			try:
				self.scrobble_to_db(song)
			except Exception as e:
				self.log("Database error, switching to cachefile: %s" % e)
				self.mode = 0
				self.scrobble_to_cache(song)
		else:
			self.scrobble_to_cache(song)

if __name__ == "__main__":
	## Create StatsCollector class:
	stats = StatsCollector()
	## Parse command line arguments:
	parser = argparse.ArgumentParser(description='Logger daemon for MPDstats')
	parser.add_argument('-c', '--config', help="The config file to use.", required=True)
	parser.add_argument('-p', '--profile', help="The profile to use.", required=True)
	args = parser.parse_args()
	## Get configuration:
	stats.config = common.read_config(args)
	## Connect to mpd:
	try:
		stats.mpd_connect()
	except Exception as e:
		print("Error while connecting to MPD: %s" % e, file=sys.stderr)
		sys.exit(1)
	## Connect to database:
	try:
		stats.db_connect()
	except Exception as e:
		print("Error while connecting to database: %s" % e, file=sys.stderr)
		sys.exit(1)
	## Read cachefile:
	try:
		stats.open_cache()
	except Exception as e:
		print("Error while reading cachefile: %s" % e, file=sys.stderr)
		sys.exit(1)
	## Scrobble cache:
	try:
		stats.scrobble_cache()
	except Exception as e:
		print("Error while scrobbling from cache: %s" % e, file=sys.stderr)
	## Scrobble:
	while True:
		stats.run()
