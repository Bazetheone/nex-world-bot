from tinydb import TinyDB, Query

db = TinyDB('nexworld.json')
players = db.table('players')
prefixes_table = db.table('prefixes')
market_table = db.table('market')
raids_table = db.table('raids')

Player = Query()
Prefix = Query()
