import zipfile as zf
import struct
import const
import os

class Character:
	def __init__(self, buffer):
		(
			self.agent, 
			self.profession, 
			self.elite, 
			self.toughness,
			self.concentration,
			self.healing, 
			self.hitbox_width,
			self.condition, 
			self.hitbox_height,
			name
		) = struct.unpack("<QIIHHHHHH68s", buffer)
		self.name = name.decode("utf8").rstrip('\0')
		self.events = []
		self.instid = None

	def get_prof(self):
		if self.elite == 0xffffffff:
			if (self.profession & 0xffff0000) == 0xffff0000:
				return "Gadget"
			else:
				return "NPC"
		elif self.elite == 0x00000000:
			return const.professions[self.profession]
		else:
			return const.elites[self.elite]

	def is_player(self):
		return self.profession >= 1 and self.profession <= 9

	def link_events(self, events):
		self.events = events

	def assign_inst_id(self, id):
		self.instid = id

class Skill:
	def __init__(self, buffer):
		(
			self.skill_id, 
			name
		) = struct.unpack("<i64s", buffer)
		self.name = name.decode("utf8").rstrip('\0')

class Event:
	def __init__(self, buffer):
		(
			self.time,
			self.src_agent,
			self.dst_agent,
			self.value,
			self.buff_dmg,
			self.overstack_value,
			self.skill_id,
			self.src_instid,
			self.dst_instid,
			self.src_master_instid,
			self.dst_master_instid,
			self.iff,
			self.buff,
			self.result,
			self.is_activation,
			self.is_buffremove,
			self.is_ninety,
			self.is_fifty,
			self.is_moving,
			self.state_change,
			self.is_flanking,
			self.is_shields,
			self.is_offcycle,
			_
		) = struct.unpack("<qQQiiIIHHHHBBBBBBBBBBBB4s", buffer)

class Log:
	def __init__(self, evtc, version, instance_id, characters, skills, events, characters_dict, instid_agent):
		self.evtc = evtc
		self.version = version
		self.instance_id = instance_id
		self.characters = characters
		self.skills = skills
		self.events = events
		self.characters_dict = characters_dict
		self.instid_agent = instid_agent



def read_file(log_file):
	basename = os.path.basename(log_file)
	splitted_name = basename.split(".")

	filename = splitted_name[0]
	extension = ".".join(splitted_name[1:])

	if extension != "zevtc" and extension != "evtc.zip":
		raise Exception("Not a EVTC file")

	zip_file = zf.ZipFile(log_file, "r")

	try:
		file = zip_file.open(filename)
	except KeyError:
		try:
			file = zip_file.open("%s.evtc" % filename)
		except KeyError:
			file = zip_file.open("%s.evtc.tmp" % filename)

	evtc, version, _, instance_id, _ = struct.unpack("<4s8s1sH1s", file.read(16))

	if evtc != b"EVTC":
		raise Exception("Corrupted file")

	character_count, = struct.unpack("<i", file.read(4))
	all_characters = [Character(file.read(96)) for i in range(character_count)]

	skill_count, = struct.unpack("<i", file.read(4))
	all_skills = [Skill(file.read(68)) for i in range(skill_count)]

	events_byte_array = file.read()
	all_events = [Event(events_byte_array[i:i+64]) for i in range(0, len(events_byte_array), 64)]

	characters = {character.agent: character for character in all_characters}

	for event in all_events:
		if event.src_agent in characters:
			character = characters[event.src_agent]
			if not character.instid:
				character.assign_inst_id(event.src_instid)

	instid_agent = {character.instid: character.agent  for character in all_characters}

	return Log(evtc, version, instance_id, all_characters, all_skills, all_events, characters, instid_agent)