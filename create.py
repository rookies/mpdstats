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
import time, sys, os.path, argparse
import libs.common as common
import pyodbc
from jinja2 import Template, FileSystemLoader
from jinja2.environment import Environment

if __name__ == "__main__":
	## Parse command line arguments:
	parser = argparse.ArgumentParser(description='Logger daemon for MPDstats')
	parser.add_argument('-c', '--config', help="The config file to use.", required=True)
	parser.add_argument('-p', '--profile', help="The profile to use.", required=True)
	parser.add_argument('-o', '--output', help="The output directory.", required=True)
	args = parser.parse_args()
	## Get configuration:
	config = common.read_config(args)
	## Get maindir:
	maindir = os.path.dirname(sys.argv[0])
	## Init template engine:
	print("Initializing template engine...", file=sys.stderr)
	env = Environment()
	env.loader = FileSystemLoader(maindir + "/templates")
	print("Initializing template engine... DONE", file=sys.stderr)
	## Open database connection:
	print("Opening database connection...", file=sys.stderr)
	db = pyodbc.connect(config["database"])
	cursor = db.cursor()
	print("Opening database connection... DONE", file=sys.stderr)
	## === OVERVIEW ===
	print("Creating index.html...", file=sys.stderr)
	## Get artists:
	artists = cursor.execute("""
		SELECT
			COUNT(`id`) AS `count`,
			`artist`
		FROM
			`scrobbles`
		GROUP BY
			`artist`
		ORDER BY
			`count` DESC
		LIMIT
			0, 15
	""").fetchall()
	all_artists = len(cursor.execute("""
		SELECT
			`artist`
		FROM
			`scrobbles`
		GROUP BY
			`artist`
	""").fetchall())
	## Get songs:
	songs = cursor.execute("""
		SELECT
			COUNT(`id`) AS `count`,
			`artist`,
			`title`
		FROM
			`scrobbles`
		GROUP BY
			`artist`,
			`title`
		ORDER BY
			`count` DESC
		LIMIT
			0, 15
	""").fetchall()
	all_songs = len(cursor.execute("""
		SELECT
			`title`
		FROM
			`scrobbles`
		GROUP BY
			`artist`,
			`title`
	""").fetchall())
	## Get albums:
	albums = cursor.execute("""
		SELECT
			COUNT(`id`) AS `count`,
			`artist`,
			`album`
		FROM
			`scrobbles`
		WHERE
			`album` != ''
		GROUP BY
			`artist`,
			`album`
		ORDER BY
			`count` DESC
		LIMIT
			0, 15
	""").fetchall()
	all_albums = len(cursor.execute("""
		SELECT
			`album`
		FROM
			`scrobbles`
		WHERE
			`album` != ''
		GROUP BY
			`artist`,
			`album`
	""").fetchall())
	## Load template:
	tpl = env.get_template("index.html")
	## ... and render it:
	f = open(args.output + "/index.html", "w")
	f.write(tpl.render(
		date=time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()),
		artists=artists,
		all_artists=all_artists,
		songs=songs,
		all_songs=all_songs,
		albums=albums,
		all_albums=all_albums
	))
	f.close()
	print("Creating index.html... DONE", file=sys.stderr)
	## Clean up:
	print("Cleaning up...", file=sys.stderr)
	cursor.close()
	print("Cleaning up... DONE", file=sys.stderr)
