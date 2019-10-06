import re
import itertools
import datetime as dt
import const

# // State Change    
# public enum StateChange : byte
# {
#     Normal          =  0,
#     EnterCombat     =  1,
#     ExitCombat      =  2,
#     ChangeUp        =  3,
#     ChangeDead      =  4,
#     ChangeDown      =  5,
#     Spawn           =  6,
#     Despawn         =  7,
#     HealthUpdate    =  8,
#     LogStart        =  9,
#     LogEnd          = 10,
#     WeaponSwap      = 11,
#     MaxHealthUpdate = 12,
#     PointOfView     = 13,
#     CBTSLanguage    = 14,
#     GWBuild         = 15,
#     ShardId         = 16,
#     Reward          = 17,
#     BuffInitial     = 18,
#     Position        = 19,
#     Velocity        = 20,
#     Rotation        = 21,
#     TeamChange      = 22,
#     AttackTarget    = 23,
#     Targetable      = 24,
#     MapID           = 25,
#     ReplInfo        = 26,
#     StackActive     = 27,
#     StackReset      = 28,
#     Guild           = 29,
#     Unknown
# };

class Player:
	def __init__(self, name, account, profession, total_dps, power_dps, condi_dps, total_damage, power_damage, condi_damage, ratio_alive, downs):
		self.name = name 
		self.account = account
		self.profession = profession	

		self.total_dps = total_dps
		self.power_dps = power_dps
		self.condi_dps = condi_dps

		self.total_damage = total_damage
		self.power_damage = power_damage
		self.condi_damage = condi_damage

		self.ratio_alive = ratio_alive
		self.downs = downs

	def fill_missing_data(self, boss, success, ratio_health_left, start, end, duration):
		self.boss = boss
		self.success = success
		self.ratio_health_left = ratio_health_left

		self.start = start
		self.end = end
		self.duration = duration

	def compute_ratio_damage(self, all_damage_dealed):
		self.ratio_damage = round(self.total_damage*10000/all_damage_dealed)/100 if all_damage_dealed > 0 else 100

def get_damage(event):
	if event.buff == 1:
		return (0, event.buff_dmg)
	if event.buff == 0:
		return (event.value, 0)
	else:
		return (0, 0)

def is_valid(event):
	if event.is_buffremove == 0 and event.is_activation == 0 and event.iff > 0:
		return True
	return False
	
# def sort_and_print_damage_by_type(events):
# 	sorted_events = sorted(events, key=lambda x: x.skill_id)
# 	events_skills = {skill_id: list(event_group) for skill_id, event_group in itertools.groupby(sorted_events, key=lambda x: x.skill_id)}

# 	print(
# 		sorted(
# 			[(skills[skill_id], skill_id, sum([get_damage(event) for event in events])) for skill_id, events in events_skills.items()],
# 			key=lambda x: x[2]
# 		)
# 	)

def formatted_milli(milliseconds):
	timedelta = dt.timedelta(microseconds=milliseconds*1000)
	return str(timedelta)[:-3]

def compute_statistics(log):
	characters = log.characters_dict
	instid_agent = log.instid_agent

	group_function = lambda x: x.src_instid if x.src_master_instid == 0 else x.src_master_instid

	first_event = log.events[0]
	last_event = log.events[-1]

	timestamp_start = first_event.value
	timestamp_end = max(0, last_event.value)

	start = first_event.time
	end = last_event.time

	success = False
	ratio_health_left = 100

	players = []

	sorted_events = sorted(log.events, key=group_function)
	for src_instid, event_group in itertools.groupby(sorted_events, key=group_function):
		if src_instid in instid_agent and instid_agent[src_instid] in characters:
			agent = instid_agent[src_instid]
			characters[agent].link_events(list(event_group))
		else:
			for event in event_group:
				if event.state_change == 9:
					timestamp_start = event.value
					start = event.time

				elif event.state_change == 10:
					timestamp_end = event.value
					end = event.time

				elif event.state_change == 17:
					success = True
					ratio_health_left = 0

	datetime_start = dt.datetime.fromtimestamp(timestamp_start)
	datetime_end = dt.datetime.fromtimestamp(timestamp_end)

	duration_milli = end - start
	formatted_duration = formatted_milli(duration_milli)

	for character in log.characters:
		if character.profession in const.bosses:
			bossid = character.instid
			if not success:
				for event in character.events:
					if event.src_instid == bossid:
						if event.state_change == 8:
							ratio_health_left = event.dst_agent
				ratio_health_left /= 100

		elif character.is_player():
			splitted_name = re.split("\x00:?", character.name)

			name = splitted_name[0]
			account = splitted_name[1]
			profession = character.get_prof()

			damages = []
			downs = 0
			ratio_alive = 10000
			end_fight = end

			sorted_events = sorted(character.events, key=is_valid)
			for is_damage, event_group in itertools.groupby(sorted_events, key=is_valid):
				if is_damage:
					damages = [get_damage(event) for event in event_group]
				else:
					for event in event_group:
						if event.state_change == 5:
							downs += 1
						elif event.state_change == 4 and event.src_master_instid == 0:
							end_fight = event.time


			power_damage = sum(power for power, _ in damages)
			condi_damage = sum(condi for _, condi in damages)
			total_damage = power_damage + condi_damage

			power_dps = round(power_damage*1000/duration_milli)
			condi_dps = round(condi_damage*1000/duration_milli)
			total_dps = round(total_damage*1000/duration_milli)

			ratio_alive = round((end_fight-start)*10000/duration_milli)/100

			players.append(Player(name, account, profession, total_dps, power_dps, condi_dps, total_damage, power_damage, condi_damage, ratio_alive, downs))

	all_damage_dealed = sum(player.total_damage for player in players)	

	for player in players:
		player.fill_missing_data(const.bosses[log.instance_id], success, ratio_health_left, datetime_start, datetime_end, formatted_duration)
		player.compute_ratio_damage(all_damage_dealed)

	return players