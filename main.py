import os
import logparser
import statistics
import mongo
import conf

# ================================
# Inspired from:
# https://github.com/baaron4/GW2-Elite-Insights-Parser/tree/master/LuckParser
# ================================

def parse(file):
	print(file)
	log = logparser.read_file(file)
	players = statistics.compute_statistics(log)

	for player in players:
		mongo.insert(player)

bosses = os.listdir(conf.path)

for boss in bosses:
	boss_dir = os.path.join(conf.path, boss)
	for boss_fight in os.listdir(boss_dir):
		file_path = os.path.join(boss_dir, boss_fight)
		parse(file_path)
