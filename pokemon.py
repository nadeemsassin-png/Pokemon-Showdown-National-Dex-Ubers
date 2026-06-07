import random
import math
import json
import os
# Pokémon Showdown Ubers-style CLI battle simulator
# Author: Nadeem Sassin
# ----------------------------------------
# This file powers a text-based Pokémon battle experience with simplified
# Ubers rules and Elo rating progression.
#
# How to run:
#   python3 pokemon.py
# Compiler: Python, Visual Studio Code
#
# Data written locally:
#   - pokemon_data.json : team data and player rating
#   - pokemon_elo.json  : Elo ratings history and match results (legacy)
# 
# The code is organized around Move, Pokemon, Team, and Battle classes.
# It aims to keep the battle flow readable while preserving competitive flavor.
# Key features:
#   - 6v6 battles with Ubers-legal Pokémon and moves
#   - Simplified damage and status mechanics
#   - Elo rating system with milestones and titles
#   - Persistent data storage for teams and ratings
#   - Type effectiveness and item interactions
#   - Randomized opponent generation with scaling difficulty
#   - User-friendly CLI prompts for team management and battle actions
#   - Modular design for easy extension and maintenance
#   - Comments and docstrings for clarity
#   - Error handling for invalid inputs and edge cases
#   - Overall, a fun and nostalgic way to experience Pokémon battles in the terminal Vs. CPU!
# Potential future enhancements: more moves, abilities, item improvement, multiplayer support, CPU improvements, potential bug fixes, etc.

#─────────────────────────────────────────────────────────────
# GLOBAL CONSTANTS AND UTILITY FUNCTIONS (TYPE CHART, MOVES, DATA HANDLING, RATING CALCULATIONS, ETC.) 
# ─────────────────────────────────────────────────────────────

ELO_FILENAME = 'pokemon_elo.json'
DATA_FILENAME = 'pokemon_data.json'
FORMAT_NAME = 'National Dex Ubers'
RULES = [
    '6 Pokémon per team',
    'No duplicate species',
    '4 moves per Pokémon',
    'Ubers-legal Pokémon pool',
    'Team preview before lead selection',
    'Player chooses lead first',
    'Choice items lock move selection',
    'Abilities and items affect battle outcome',
]

# Rating thresholds for titles and milestones.
MIN_RATING = 1000
NO_LIFER_RATING = 1800
NO_LIFER_QUALITY = 1.0

# Type chart covers all major interactions.
# Values: 2.0 = super effective, 0.5 = not very effective, 0.0 = immune.
TYPE_CHART = {
    'Normal':   {'Rock': 0.5, 'Ghost': 0.0, 'Steel': 0.5},
    'Fire':     {'Fire': 0.5, 'Water': 0.5, 'Grass': 2.0, 'Ice': 2.0, 'Bug': 2.0, 'Rock': 0.5, 'Dragon': 0.5, 'Steel': 2.0},
    'Water':    {'Fire': 2.0, 'Water': 0.5, 'Grass': 0.5, 'Ground': 2.0, 'Rock': 2.0, 'Dragon': 0.5},
    'Electric': {'Water': 2.0, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0.0, 'Flying': 2.0, 'Dragon': 0.5},
    'Grass':    {'Fire': 0.5, 'Water': 2.0, 'Grass': 0.5, 'Poison': 0.5, 'Ground': 2.0, 'Flying': 0.5, 'Bug': 0.5, 'Rock': 2.0, 'Dragon': 0.5, 'Steel': 0.5},
    'Ice':      {'Fire': 0.5, 'Water': 0.5, 'Grass': 2.0, 'Ground': 2.0, 'Flying': 2.0, 'Dragon': 2.0, 'Steel': 0.5},
    'Fighting': {'Normal': 2.0, 'Ice': 2.0, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Rock': 2.0, 'Ghost': 0.0, 'Dark': 2.0, 'Steel': 2.0, 'Fairy': 0.5},
    'Poison':   {'Grass': 2.0, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0.0, 'Fairy': 2.0},
    'Ground':   {'Fire': 2.0, 'Electric': 2.0, 'Grass': 0.5, 'Poison': 2.0, 'Flying': 0.0, 'Bug': 0.5, 'Rock': 2.0, 'Steel': 2.0},
    'Flying':   {'Electric': 0.5, 'Grass': 2.0, 'Fighting': 2.0, 'Bug': 2.0, 'Rock': 0.5, 'Steel': 0.5},
    'Psychic':  {'Fighting': 2.0, 'Poison': 2.0, 'Psychic': 0.5, 'Dark': 0.0, 'Steel': 0.5},
    'Bug':      {'Fire': 0.5, 'Grass': 2.0, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 2.0, 'Ghost': 0.5, 'Dark': 2.0, 'Steel': 0.5, 'Fairy': 0.5},
    'Rock':     {'Fire': 2.0, 'Ice': 2.0, 'Fighting': 0.5, 'Ground': 0.5, 'Flying': 2.0, 'Bug': 2.0, 'Steel': 0.5},
    'Ghost':    {'Normal': 0.0, 'Psychic': 2.0, 'Ghost': 2.0, 'Dark': 0.5},
    'Dragon':   {'Dragon': 2.0, 'Steel': 0.5, 'Fairy': 0.0},
    'Dark':     {'Fighting': 0.5, 'Psychic': 2.0, 'Ghost': 2.0, 'Dark': 0.5, 'Fairy': 0.5},
    'Steel':    {'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Ice': 2.0, 'Rock': 2.0, 'Fairy': 2.0, 'Steel': 0.5},
    'Fairy':    {'Fire': 0.5, 'Fighting': 2.0, 'Poison': 0.5, 'Dragon': 2.0, 'Dark': 2.0, 'Steel': 0.5},
}

# Choice items that lock the user into one move until they switch out.
CHOICE_ITEMS = {'Choice Band', 'Choice Specs', 'Choice Scarf'}

# Items that grant passive SpDef boost (Assault Vest) or Eviolite bulk
DEFENSIVE_ITEMS = {'Assault Vest', 'Eviolite'}

# Abilities that affect battle mechanics (not fully implemented, but can be expanded in the future)
def type_effectiveness(move_type, defender_types):
    # Multiply effectiveness across each of the defender's types.
    modifier = 1.0
    for defender_type in defender_types:
        modifier *= TYPE_CHART.get(move_type, {}).get(defender_type, 1.0)
    return modifier

# Utility function to clamp values within a specified range.
def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))

#─────────────────────────────────────────────────────────────
#  DATA HANDLING FUNCTIONS (LOAD/SAVE PLAYER RATING, TEAMS, BATTLE HISTORY, ETC.)
#─────────────────────────────────────────────────────────────

# Data is stored in a single JSON file (pokemon_data.json) that contains player rating, teams, and battle history.
def get_data_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILENAME)

# Loads player rating, teams, and battle history from a JSON file. If the file doesn't exist or is corrupted, it returns default values.
def load_data():
    # Load saved player rating, teams, and battle history.
    # Falls back to legacy elo file, then fresh state if neither exists.
    path = get_data_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return {
                    'player': data.get('player', 1000),
                    'teams': data.get('teams', []),
                    'history': data.get('history', []),
                }
            except (json.JSONDecodeError, ValueError):
                return {'player': 1000, 'teams': [], 'history': []}

    # Support for older saves that used a separate elo file
    old_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ELO_FILENAME)
    if os.path.exists(old_path):
        with open(old_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return {'player': data.get('player', 1000), 'teams': [], 'history': []}
            except (json.JSONDecodeError, ValueError):
                return {'player': 1000, 'teams': [], 'history': []}

    return {'player': 1000, 'teams': [], 'history': []}

# Saves player rating, teams, and battle history to a JSON file. This overwrites the entire file each time, but since the data is small, it's not a performance concern.
def save_data(data):
    path = get_data_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def save_ratings(ratings):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ELO_FILENAME)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(ratings, f)

# RATING CALCULATIONS / TITLES
def progress_title(rating):
    if rating >= 1800: return 'No Lifer'
    if rating >= 1600: return 'Hall of Fame'
    if rating >= 1500: return 'Legend'
    if rating >= 1400: return 'Champion'
    if rating >= 1300: return 'Elite'
    if rating >= 1200: return 'Ace'
    if rating >= 1100: return 'Veteran'
    return 'Rookie'

# MILESTONES
def next_milestone(rating):
    thresholds = [
        (1100, 'Veteran rank and stronger opponents'),
        (1200, 'Ace rank with better team synergy'),
        (1300, 'Elite rank with higher-quality CPU teams'),
        (1400, 'Champion rank and expert challenger pools'),
        (1500, 'Legend rank and high-level opponents'),
        (1600, 'Hall of Fame rank and elite simulation'),
    ]
    for threshold, reward in thresholds:
        if rating < threshold:
            return threshold, reward
    return None, None

#─────────────────────────────────────────────────────────────
#  DIFFICULTY CALCULATIONS
#─────────────────────────────────────────────────────────────

def difficulty_offset(wins):
    # Gentle difficulty curve based on win count. Caps at +180 rating offset.
    return clamp(wins * 2, 0, 180)


def calculate_opponent_rating(player_rating, wins):
    # Opponent rating tracks slightly above the player's, with some variance.
    rating = clamp(player_rating + random.randint(-30, 50) + difficulty_offset(wins) // 3, 1200, 2800)
    # Occasional spike opponent once player reaches high ELO.
    if player_rating >= 1400 and random.random() < 0.10:
        extra = random.randint(0, 100)
        rating = max(rating, NO_LIFER_RATING + extra)
    return rating

#─────────────────────────────────────────────────────────────
#  STAT CALCULATIONS
#─────────────────────────────────────────────────────────────

# Gen 1+ stat stage multipliers. Stages range from -6 to +6.
def stage_multiplier(stage):
    # Classic gen 1+ boost formula: +1 = 1.5x, +2 = 2.0x, -1 = 0.67x, etc.
    if stage >= 0:
        return (2 + stage) / 2
    return 2 / (2 - stage)

# Stat calculation based on gen 3+ formula, with IVs=31, EVs=252, Level=100 by default.
def calc_stat(base, iv=31, ev=252, level=100, kind='hp'):
    if kind == 'hp':
        return math.floor(((2 * base + iv + ev // 4) * level) / 100) + level + 10
    return math.floor(math.floor(((2 * base + iv + ev // 4) * level) / 100) + 5)


# ─────────────────────────────────────────────────────────────
#  MOVE
# ─────────────────────────────────────────────────────────────

class Move:
    def __init__(self, name, mtype, category, power, accuracy, pp,
                 priority=0, target='normal', recoil=0, heal=0,
                 status=None, status_chance=0, boosts=None, self_boosts=None,
                 always_hit=False):
        self.name         = name
        self.type         = mtype
        self.category     = category
        self.power        = power
        self.accuracy     = accuracy
        self.pp           = pp
        self.priority     = priority
        self.target       = target
        self.recoil       = recoil
        self.heal         = heal
        self.status       = status
        self.status_chance= status_chance
        self.boosts       = boosts or {}
        self.self_boosts  = self_boosts or {}
        self.always_hit   = always_hit


# ─────────────────────────────────────────────────────────────
#  POKEMON
# ─────────────────────────────────────────────────────────────

class Pokemon:
    def __init__(self, nickname, species, types, base_stats, moves,
                 item='Leftovers', ability='Pressure'):
        self.nickname  = nickname
        self.species   = species
        self.types     = types
        self.base_stats= base_stats
        self.level     = 100
        self.item      = item
        self.ability   = ability

        self.ivs = {s: 31  for s in ['hp','atk','def','spa','spd','spe']}
        self.evs = {s: 252 for s in ['hp','atk','def','spa','spd','spe']}

        self.stats = {
            'hp':  calc_stat(base_stats['hp'],  self.ivs['hp'],  self.evs['hp'],  self.level, 'hp'),
            'atk': calc_stat(base_stats['atk'], self.ivs['atk'], self.evs['atk'], self.level),
            'def': calc_stat(base_stats['def'], self.ivs['def'], self.evs['def'], self.level),
            'spa': calc_stat(base_stats['spa'], self.ivs['spa'], self.evs['spa'], self.level),
            'spd': calc_stat(base_stats['spd'], self.ivs['spd'], self.evs['spd'], self.level),
            'spe': calc_stat(base_stats['spe'], self.ivs['spe'], self.evs['spe'], self.level),
        }

        self.current_hp    = self.stats['hp']
        self.boosts        = {s: 0 for s in ['atk','def','spa','spd','spe','accuracy','evasion']}
        self.status        = None
        self.status_counter= 0
        self.sleep_turns   = 0   # how many turns of sleep remain
        self.volatiles     = {}
        self.fainted       = False
        self.choice_locked = None
        self.item_revealed = False

        self.moves = []
        for move_name in moves:
            if move_name not in MOVES:
                raise ValueError(f"Undefined move '{move_name}' for {species}.")
            self.moves.append(MOVES[move_name])
        self.pp = {move.name: move.pp for move in self.moves}

    def reset(self):
        self.current_hp     = self.stats['hp']
        self.boosts         = {s: 0 for s in ['atk','def','spa','spd','spe','accuracy','evasion']}
        self.status         = None
        self.status_counter = 0
        self.sleep_turns    = 0
        self.volatiles      = {}
        self.fainted        = False
        self.choice_locked  = None
        self.item_revealed  = False
        self.pp             = {move.name: move.pp for move in self.moves}

    def effective_stat(self, stat):
        base_value = self.stats[stat]
        if stat in ['atk', 'def', 'spa', 'spd', 'spe']:
            base_value = int(base_value * stage_multiplier(self.boosts[stat]))

        # Assault Vest boosts special defense by 1.5x
        if stat == 'spd' and self.item == 'Assault Vest':
            base_value = int(base_value * 1.5)

        # Eviolite boosts Def and SpDef by 1.5x (for not-fully-evolved mons like Chansey)
        if stat in ['def', 'spd'] and self.item == 'Eviolite':
            base_value = int(base_value * 1.5)

        if stat == 'spe':
            if self.item == 'Choice Scarf':
                base_value = int(base_value * 1.5)
            if self.status == 'paralysis':
                base_value = max(1, math.floor(base_value * 0.5))

        return max(1, base_value)

    def is_alive(self):
        return self.current_hp > 0

    def apply_damage(self, amount):
        self.current_hp = max(0, self.current_hp - amount)
        fainted_now = self.current_hp == 0 and not self.fainted
        if fainted_now:
            self.fainted = True
            self.status  = None
            self.volatiles.clear()
            self.boosts  = {s: 0 for s in self.boosts}
        return fainted_now

    def heal(self, amount):
        self.current_hp = min(self.stats['hp'], self.current_hp + amount)

    def set_status(self, status):
        # Immunities: can't stack statuses, can't burn Fire types, can't freeze Ice types,
        # can't paralyze Electric types, can't poison Poison/Steel types, can't sleep if already asleep.
        if self.status or self.fainted:
            return False
        if status == 'burn'     and 'Fire'     in self.types: return False
        if status == 'freeze'   and 'Ice'      in self.types: return False
        if status == 'paralysis'and 'Electric' in self.types: return False
        if status in ('poison','toxic') and ('Poison' in self.types or 'Steel' in self.types): return False

        self.status         = status
        self.status_counter = 0
        if status == 'sleep':
            self.sleep_turns = random.randint(1, 3)  # 1-3 turn sleep like gen 5+
        return True

    def modify_boosts(self, boosts):
        for stat, change in boosts.items():
            self.boosts[stat] = clamp(self.boosts[stat] + change, -6, 6)

    def clear_boosts(self):
        # Used by Haze - resets all stat stages to 0
        self.boosts = {s: 0 for s in self.boosts}

    def reveal_item(self, reason='an effect'):
        if not self.item_revealed and self.item:
            self.item_revealed = True
            return f"{self.nickname}'s item was revealed as {self.item} by {reason}!"
        return None


# ─────────────────────────────────────────────────────────────
#  TEAM
# ─────────────────────────────────────────────────────────────

class Team:
    def __init__(self, name, pokemons, rating=1500):
        self.name         = name
        self.pokemons     = pokemons
        self.active_index = 0
        self.rating       = rating

    def active(self):
        if 0 <= self.active_index < len(self.pokemons):
            return self.pokemons[self.active_index]
        return None

    def has_alive(self):
        return any(p.is_alive() for p in self.pokemons)

    def alive_pokemons(self):
        return [p for p in self.pokemons if p.is_alive()]

    def switch(self, index):
        if index < 0 or index >= len(self.pokemons): return False
        if self.pokemons[index].fainted:              return False
        self.active_index = index
        return True

    def set_active(self, index):
        if index < 0 or index >= len(self.pokemons): return False
        if self.pokemons[index].fainted:              return False
        self.active_index = index
        return True

    def first_available(self):
        for i, p in enumerate(self.pokemons):
            if p.is_alive():
                return i
        return None

    def reset(self):
        for p in self.pokemons:
            p.reset()
        self.active_index = 0


# ─────────────────────────────────────────────────────────────
#  MOVE DEFINITIONS
# ─────────────────────────────────────────────────────────────

MOVES = {
    'Behemoth Blade':  Move('Behemoth Blade',  'Steel',    'Physical', 100, 100, 10),
    'Play Rough':      Move('Play Rough',       'Fairy',    'Physical',  90,  90, 10, status='flinch',    status_chance=10),
    'Close Combat':    Move('Close Combat',     'Fighting', 'Physical', 120, 100,  10, boosts={'def': -1, 'spd': -1}),
    'Protect':         Move('Protect',          'Normal',   'Status',     0,   0, 10, priority=4),
    'Oblivion Wing':   Move('Oblivion Wing',    'Flying',   'Special',   80, 100, 10, heal=0.75),  # heals 75% of dmg dealt, not 50%
    'Dark Pulse':      Move('Dark Pulse',       'Dark',     'Special',   80, 100, 15, status='flinch',    status_chance=20),
    'Sucker Punch':    Move('Sucker Punch',     'Dark',     'Physical',  70, 100,  10, priority=1),
    'Taunt':           Move('Taunt',            'Dark',     'Status',     0, 100, 20, status='taunt',     status_chance=100),
    'Moonblast':       Move('Moonblast',        'Fairy',    'Special',   95, 100, 10, boosts={'spa': -1}, status_chance=30),
    'Geomancy':        Move('Geomancy',         'Fairy',    'Status',     0,   0, 10, boosts={'spa': 2, 'spd': 2, 'spe': 2}),  # also boosts speed
    'Psychic':         Move('Psychic',          'Psychic',  'Special',   90, 100, 10, boosts={'spd': -1}, status_chance=10),
    'Thunderbolt':     Move('Thunderbolt',      'Electric', 'Special',   90, 100, 15, status='paralysis', status_chance=10),
    'Blue Flare':      Move('Blue Flare',       'Fire',     'Special',  130,  85,  10, status='burn',      status_chance=20),
    'Origin Pulse':    Move('Origin Pulse',     'Water',    'Special',  110,  85, 10),
    'Thunder':         Move('Thunder',          'Electric', 'Special',  110,  70, 10, status='paralysis', status_chance=30),
    'Ice Beam':        Move('Ice Beam',         'Ice',      'Special',   90, 100, 10, status='freeze',    status_chance=10),
    'Calm Mind':       Move('Calm Mind',        'Psychic',  'Status',     0,   0, 20, boosts={'spa': 1, 'spd': 1}),
    'Precipice Blades':Move('Precipice Blades', 'Ground',   'Physical', 120,  85, 10),
    'Fire Punch':      Move('Fire Punch',       'Fire',     'Physical',  75, 100, 15, status='burn',      status_chance=10),
    'Earthquake':      Move('Earthquake',       'Ground',   'Physical', 100, 100, 10),
    'Stone Edge':      Move('Stone Edge',       'Rock',     'Physical', 100,  80,  8),
    'Astral Barrage':  Move('Astral Barrage',   'Ghost',    'Special',  120, 100, 10),  # Ghost type, 120 power
    'Psyshock':        Move('Psyshock',         'Psychic',  'Special',   80, 100, 10),
    'Nasty Plot':      Move('Nasty Plot',       'Dark',     'Status',     0,   0, 20, boosts={'spa': 2}),
    'Will-O-Wisp':     Move('Will-O-Wisp',      'Fire',     'Status',     0,  85, 15, status='burn',      status_chance=100),
    'Roost':           Move('Roost',            'Flying',   'Status',     0,   0, 10, heal=0.5),
    'Sacred Fire':     Move('Sacred Fire',      'Fire',     'Physical', 100,  95,  12, status='burn',      status_chance=50),
    'Brave Bird':      Move('Brave Bird',       'Flying',   'Physical', 120, 100, 15, recoil=0.33),
    'Thunder Wave':    Move('Thunder Wave',     'Electric', 'Status',     0,  90, 20, status='paralysis', status_chance=100),
    'Recover':         Move('Recover',          'Normal',   'Status',     0,   0, 10, heal=0.5),
    'Flamethrower':    Move('Flamethrower',     'Fire',     'Special',   90, 100, 15, status='burn',      status_chance=10),
    'Sludge Bomb':     Move('Sludge Bomb',      'Poison',   'Special',   90, 100, 10, status='poison',    status_chance=30),
    'Dynamax Cannon':  Move('Dynamax Cannon',   'Dragon',   'Special',  100, 100,  16),
    'Earth Power':     Move('Earth Power',      'Ground',   'Special',   90, 100, 10, boosts={'spd': -1}, status_chance=10),
    'Aura Sphere':     Move('Aura Sphere',      'Fighting', 'Special',   80, 100, 10, always_hit=True),
    'Shadow Ball':     Move('Shadow Ball',      'Ghost',    'Special',   80, 100, 15, boosts={'spd': -1}, status_chance=20),
    'Psystrike':       Move('Psystrike',        'Psychic',  'Special',  100, 100, 10),
    'Judgment':        Move('Judgment',         'Normal',   'Special',  100, 100, 10),
    'Hyper Beam':      Move('Hyper Beam',       'Normal',   'Special',  150,  90,  8),
    'Giga Impact':     Move('Giga Impact',      'Normal',   'Physical', 150,  90,  8),
    'Spacial Rend':    Move('Spacial Rend',     'Dragon',   'Special',  100,  95,  8),
    'Shadow Force':    Move('Shadow Force',     'Ghost',    'Physical', 120, 100,  8),
    'Iron Head':       Move('Iron Head',        'Steel',    'Physical',  80, 100, 15, status='flinch',    status_chance=30),
    'Fire Blast':      Move('Fire Blast',       'Fire',     'Special',  110,  85,  10, status='burn',      status_chance=10),
    'Hydro Pump':      Move('Hydro Pump',       'Water',    'Special',  110,  80,  10),
    'Darkest Lariat':  Move('Darkest Lariat',   'Dark',     'Physical',  85, 100, 10),
    'Toxic':           Move('Toxic',            'Poison',   'Status',     0,  90, 10, status='toxic',     status_chance=100),
    'Stealth Rock':    Move('Stealth Rock',     'Rock',     'Status',     0,   0, 20),
    'Volt Switch':     Move('Volt Switch',      'Electric', 'Special',   70, 100, 20),
    'U-turn':          Move('U-turn',           'Bug',      'Physical',  70, 100, 20),
    'Quick Attack':    Move('Quick Attack',     'Normal',   'Physical',  40, 100, 30, priority=1),
    'Sacred Sword':    Move('Sacred Sword',     'Fighting', 'Physical',  90, 100, 15),
    'Dazzling Gleam':  Move('Dazzling Gleam',   'Fairy',    'Special',   80, 100, 10),
    'Foul Play':       Move('Foul Play',        'Dark',     'Physical',  95, 100, 15),
    'Heat Wave':       Move('Heat Wave',        'Fire',     'Special',   95,  90, 10, status='burn',      status_chance=10),
    'Water Spout':     Move('Water Spout',      'Water',    'Special',  150, 100,  12),
    'Rock Slide':      Move('Rock Slide',       'Rock',     'Physical',  75,  90, 10, status='flinch',    status_chance=30),
    'Focus Blast':     Move('Focus Blast',      'Fighting', 'Special',  120,  70,  8),
    'Dragon Pulse':    Move('Dragon Pulse',     'Dragon',   'Special',   85, 100, 10),
    'Moongeist Beam':  Move('Moongeist Beam',   'Ghost',    'Special',  100, 100,  12),
    'Zen Headbutt':    Move('Zen Headbutt',     'Psychic',  'Physical',  80,  90, 15, status='flinch',    status_chance=20),
    'Flare Blitz':     Move('Flare Blitz',      'Fire',     'Physical', 120, 100, 15, recoil=0.33, status='burn', status_chance=10),
    'Outrage':         Move('Outrage',          'Dragon',   'Physical', 120, 100, 10),
    'Extreme Speed':   Move('Extreme Speed',    'Normal',   'Physical',  80, 100,  16, priority=2),
    'Dragon Ascent':   Move('Dragon Ascent',    'Flying',   'Physical', 120, 100,  16, self_boosts={'def': -1, 'spd': -1}),
    'Scald':           Move('Scald',            'Water',    'Special',   80, 100, 15, status='burn',      status_chance=30),
    'Dragon Dance':    Move('Dragon Dance',     'Dragon',   'Status',     0,   0, 20, boosts={'atk': 1, 'spe': 1}),
    'Meteor Beam':     Move('Meteor Beam',      'Rock',     'Special',  120,  90,  10, self_boosts={'spa': 1}),
    'Sunsteel Strike': Move('Sunsteel Strike',  'Steel',    'Physical', 100, 100,  12),
    'Swords Dance':    Move('Swords Dance',     'Normal',   'Status',     0,   0, 20, boosts={'atk': 2}),
    'Dragon Claw':     Move('Dragon Claw',      'Dragon',   'Physical',  80, 100, 15),
    'Roar':            Move('Roar',             'Normal',   'Status',     0, 100, 20, priority = -2),
    'Haze':            Move('Haze',             'Ice',      'Status',     0, 100, 30),
    'Defog':           Move('Defog',            'Flying',   'Status',     0, 100, 15),
    'Rock Polish':     Move('Rock Polish',      'Rock',     'Status',     0, 100, 20, boosts={'spe': 2}),
    'Dragon Tail':     Move('Dragon Tail',      'Dragon',   'Physical',  60,  90, 10, priority=-6),
    'Ice Fang':        Move('Ice Fang',         'Ice',      'Physical',  65,  95, 15, status='freeze',    status_chance=10),
    'Thunder Fang':    Move('Thunder Fang',     'Electric', 'Physical',  65,  95, 15, status='paralysis', status_chance=10),
    'Fire Fang':       Move('Fire Fang',        'Fire',     'Physical',  65,  95, 15, status='burn',      status_chance=10),
    'Bug Buzz':        Move('Bug Buzz',         'Bug',      'Special',   90, 100, 10, boosts={'spd': -1}, status_chance=10),
    'Quiver Dance':    Move('Quiver Dance',     'Bug',      'Status',     0, 100, 20, boosts={'spa': 1, 'spd': 1, 'spe': 1}),
    'Fiery Dance':     Move('Fiery Dance',      'Fire',     'Special',   80, 100, 10, self_boosts={'spa': 1}),
    'Rapid Spin':      Move('Rapid Spin',       'Normal',   'Physical',  50, 100, 40),  # physical now, 50 power
    'Bullet Punch':    Move('Bullet Punch',     'Steel',    'Physical',  40, 100, 30, priority=1),
    'Power Whip':      Move('Power Whip',       'Grass',    'Physical', 120,  85, 10),
    'Gyro Ball':       Move('Gyro Ball',        'Steel',    'Physical',  80, 100,  5),
    'Soft-Boiled':     Move('Soft-Boiled',      'Normal',   'Status',     0,   0, 10, heal=0.5),
    'Slack Off':       Move('Slack Off',        'Normal',   'Status',     0,   0, 10, heal=0.5),
    'Seismic Toss':    Move('Seismic Toss',     'Fighting', 'Physical',   1, 100, 20),
    'Body Slam':       Move('Body Slam',        'Normal',   'Physical',  85, 100, 15, status='paralysis', status_chance=30),
    'Power Gem':       Move('Power Gem',        'Rock',     'Special',   80, 100, 20),
    'Spirit Break':    Move('Spirit Break',     'Fairy',    'Physical',  75, 100, 10, boosts={'spa': -1}),
    'Knock Off':       Move('Knock Off',        'Dark',     'Physical',  65, 100, 20),
    'Ice Punch':       Move('Ice Punch',        'Ice',      'Physical',  75, 100, 15, status='freeze',    status_chance=10),
    'Thunder Punch':   Move('Thunder Punch',    'Electric', 'Physical',  75, 100, 15, status='paralysis', status_chance=10),
    'Bulk Up':         Move('Bulk Up',          'Fighting', 'Status',     0,   0, 20, boosts={'atk': 1, 'def': 1}),
    'Flash Cannon':    Move('Flash Cannon',     'Steel',    'Special',   80, 100, 10, boosts={'spd': -1}, status_chance=10),
    'Leaf Blade':      Move('Leaf Blade',       'Grass',    'Physical',  90, 100, 15),
    'Draco Meteor':    Move('Draco Meteor',     'Dragon',   'Special',  130,  90,  5, self_boosts={'spa': -2}),
    'Substitute':      Move('Substitute',       'Normal',   'Status',     0,   0, 10),
    'Spore':           Move('Spore',            'Grass',    'Status',     0, 100, 15, status='sleep',     status_chance=100),
    'Sleep Powder':    Move('Sleep Powder',     'Grass',    'Status',     0,  75, 15, status='sleep',     status_chance=100),
}


# ─────────────────────────────────────────────────────────────
#  POKEMON POOL
# ─────────────────────────────────────────────────────────────

POKEMON_POOL = [
    {
        'name': 'Zacian-Crowned',
        'types': ['Fairy', 'Steel'],
        'base_stats': {'hp': 92, 'atk': 170, 'def': 115, 'spa': 80, 'spd': 115, 'spe': 148},
        'moves': ['Behemoth Blade', 'Play Rough', 'Close Combat', 'Protect', 'Swords Dance', 'Iron Head', 'Sacred Sword'],
        'item': ['Rusted Sword', 'Life Orb'],
    },
    {
        'name': 'Yveltal',
        'types': ['Dark', 'Flying'],
        'base_stats': {'hp': 126, 'atk': 131, 'def': 95, 'spa': 131, 'spd': 98, 'spe': 99},
        'moves': ['Oblivion Wing', 'Dark Pulse', 'Sucker Punch', 'Taunt', 'Roost', 'Foul Play', 'Heat Wave'],
        'item': ['Life Orb', 'Leftovers'],
    },
    {
        'name': 'Kyogre-Primal',
        'types': ['Water'],
        'base_stats': {'hp': 100, 'atk': 150, 'def': 90, 'spa': 180, 'spd': 160, 'spe': 90},
        'moves': ['Origin Pulse', 'Thunder', 'Ice Beam', 'Calm Mind', 'Water Spout', 'Scald', 'Protect'],
        'item': 'Blue Orb',
    },
    {
        'name': 'Groudon-Primal',
        'types': ['Ground', 'Fire'],
        'base_stats': {'hp': 100, 'atk': 180, 'def': 160, 'spa': 150, 'spd': 90, 'spe': 90},
        'moves': ['Precipice Blades', 'Fire Punch', 'Earthquake', 'Stone Edge', 'Rock Slide', 'Stealth Rock', 'Protect'],
        'item': 'Red Orb',
    },
    {
        # Fixed: was Ice Rider's stats/typing. Shadow Rider is Psychic/Ghost, special attacker.
        'name': 'Calyrex-Shadow',
        'types': ['Psychic', 'Ghost'],
        'base_stats': {'hp': 100, 'atk': 85, 'def': 80, 'spa': 165, 'spd': 100, 'spe': 150},
        'moves': ['Astral Barrage', 'Psyshock', 'Nasty Plot', 'Will-O-Wisp', 'Shadow Ball', 'Focus Blast', 'Calm Mind'],
        'item': ['Choice Scarf', 'Life Orb'],
    },
    {
        'name': 'Necrozma-Dusk-Mane',
        'types': ['Steel', 'Psychic'],
        'base_stats': {'hp': 97, 'atk': 157, 'def': 127, 'spa': 113, 'spd': 109, 'spe': 77},
        'moves': ['Sunsteel Strike', 'Earthquake', 'Meteor Beam', 'Swords Dance', 'Iron Head', 'Rock Slide'],
        'item': 'Weakness Policy',
    },
    {
        'name': 'Ho-Oh',
        'types': ['Fire', 'Flying'],
        'base_stats': {'hp': 106, 'atk': 130, 'def': 90, 'spa': 110, 'spd': 154, 'spe': 90},
        'moves': ['Sacred Fire', 'Brave Bird', 'Roost', 'Thunder Wave', 'Recover', 'Earthquake'],
        'item': 'Leftovers',
    },
    {
        'name': 'Eternatus',
        'types': ['Poison', 'Dragon'],
        'base_stats': {'hp': 140, 'atk': 85, 'def': 95, 'spa': 145, 'spd': 95, 'spe': 130},
        'moves': ['Dynamax Cannon', 'Sludge Bomb', 'Flamethrower', 'Recover', 'Dragon Pulse', 'Toxic'],
        'item': 'Choice Specs',
    },
    {
        'name': 'Mewtwo',
        'types': ['Psychic'],
        'base_stats': {'hp': 106, 'atk': 110, 'def': 90, 'spa': 154, 'spd': 90, 'spe': 130},
        'moves': ['Psychic', 'Ice Beam', 'Thunderbolt', 'Calm Mind', 'Psystrike', 'Aura Sphere'],
        'item': ['Life Orb', 'Choice Specs'],
    },
    {
        'name': 'Arceus',
        'types': ['Normal'],
        'base_stats': {'hp': 120, 'atk': 120, 'def': 120, 'spa': 120, 'spd': 120, 'spe': 120},
        'moves': ['Judgment', 'Recover', 'Calm Mind', 'Swords Dance', 'Shadow Force', 'Earthquake'],
        'item': ['Life Orb', 'Leftovers', 'Choice Band'],
    },
    {
        'name': 'Lunala',
        'types': ['Psychic', 'Ghost'],
        'base_stats': {'hp': 137, 'atk': 113, 'def': 89, 'spa': 137, 'spd': 107, 'spe': 97},
        'moves': ['Moongeist Beam', 'Psychic', 'Calm Mind', 'Shadow Ball', 'Roost', 'Thunderbolt'],
        'item': ['Choice Specs', 'Leftovers'],
    },
    {
        'name': 'Solgaleo',
        'types': ['Psychic', 'Steel'],
        'base_stats': {'hp': 137, 'atk': 137, 'def': 107, 'spa': 113, 'spd': 89, 'spe': 97},
        'moves': ['Sunsteel Strike', 'Flare Blitz', 'Zen Headbutt', 'Protect', 'Iron Head', 'Roost'],
        'item': ['Choice Band', 'Leftovers'],
    },
    {
        'name': 'Salamence-Mega',
        'types': ['Dragon', 'Flying'],
        'base_stats': {'hp': 95, 'atk': 145, 'def': 130, 'spa': 120, 'spd': 90, 'spe': 120},
        'moves': ['Dragon Dance', 'Outrage', 'Earthquake', 'Roost', 'Protect', 'Rock Slide'],
        'item': ['Life Orb', 'Choice Band', 'Choice Scarf'],
        'ability': ['Intimidate', 'Moxie'],
    },
    {
        'name': 'Palkia-Origin',
        'types': ['Water', 'Dragon'],
        'base_stats': {'hp': 90, 'atk': 120, 'def': 100, 'spa': 150, 'spd': 120, 'spe': 100},
        'moves': ['Spacial Rend', 'Hydro Pump', 'Thunderbolt', 'Ice Beam', 'Dragon Pulse', 'Protect'],
        'item': ['Choice Specs', 'Life Orb'],
    },
    {
        'name': 'Dialga',
        'types': ['Steel', 'Dragon'],
        'base_stats': {'hp': 100, 'atk': 120, 'def': 120, 'spa': 150, 'spd': 100, 'spe': 90},
        'moves': ['Spacial Rend', 'Aura Sphere', 'Thunder', 'Flash Cannon', 'Earth Power', 'Dragon Pulse', 'Calm Mind'],
        'item': ['Choice Specs', 'Life Orb'],
        'ability': ['Pressure', 'Regenerator'],
    },
    {
        'name': 'Kartana',
        'types': ['Grass', 'Steel'],
        'base_stats': {'hp': 59, 'atk': 181, 'def': 131, 'spa': 59, 'spd': 31, 'spe': 109},
        'moves': ['Leaf Blade', 'Sacred Sword', 'Close Combat', 'Swords Dance', 'Protect', 'Bulk Up'],
        'item': ['Choice Band', 'Focus Sash'],
        'ability': ['Beast Boost', 'Justified'],
    },
    {
        'name': 'Xurkitree',
        'types': ['Electric'],
        'base_stats': {'hp': 83, 'atk': 89, 'def': 71, 'spa': 173, 'spd': 71, 'spe': 83},
        'moves': ['Thunderbolt', 'Volt Switch', 'Thunder Punch', 'Heat Wave', 'Focus Blast', 'Protect'],
        'item': ['Choice Specs', 'Life Orb'],
        'ability': ['Beast Boost', 'Static'],
    },
    {
        'name': 'Zygarde-Complete',
        'types': ['Dragon', 'Ground'],
        'base_stats': {'hp': 216, 'atk': 100, 'def': 121, 'spa': 91, 'spd': 95, 'spe': 85},
        'moves': ['Dragon Dance', 'Outrage', 'Earthquake', 'Extreme Speed', 'Stone Edge', 'Protect'],
        'item': ['Life Orb', 'Leftovers'],
        'ability': ['Power Construct', 'Aura Break'],
    },
    {
        'name': 'Ferrothorn',
        'types': ['Grass', 'Steel'],
        'base_stats': {'hp': 91, 'atk': 124, 'def': 116, 'spa': 70, 'spd': 116, 'spe': 20},
        'moves': ['Power Whip', 'Gyro Ball', 'Protect', 'Stealth Rock', 'Knock Off', 'Toxic'],
        'item': ['Leftovers', 'Rocky Helmet'],
        'ability': ['Iron Barbs', 'Power Construct'],
    },
    {
        'name': 'Chansey',
        'types': ['Normal'],
        'base_stats': {'hp': 250, 'atk': 5, 'def': 5, 'spa': 35, 'spd': 105, 'spe': 50},
        'moves': ['Soft-Boiled', 'Thunder Wave', 'Toxic', 'Flamethrower', 'Ice Beam', 'Protect'],
        'item': ['Eviolite', 'Leftovers'],
        'ability': ['Natural Cure', 'Serene Grace'],
    },
    {
        'name': 'Blissey',
        'types': ['Normal'],
        'base_stats': {'hp': 255, 'atk': 10, 'def': 10, 'spa': 75, 'spd': 135, 'spe': 55},
        'moves': ['Soft-Boiled', 'Thunder Wave', 'Toxic', 'Flamethrower', 'Ice Beam', 'Protect'],
        'item': ['Leftovers', 'Flame Orb'],
        'ability': ['Natural Cure', 'Serene Grace'],
    },
    {
        'name': 'Dondozo',
        'types': ['Water'],
        'base_stats': {'hp': 150, 'atk': 100, 'def': 115, 'spa': 65, 'spd': 65, 'spe': 45},
        'moves': ['Scald', 'Earthquake', 'Stone Edge', 'Protect', 'Body Slam', 'Roost'],
        'item': ['Leftovers', 'Rocky Helmet'],
        'ability': ['Unaware', 'Water Veil'],
    },
    {
        'name': 'Glimmora',
        'types': ['Rock', 'Poison'],
        'base_stats': {'hp': 85, 'atk': 60, 'def': 106, 'spa': 105, 'spd': 86, 'spe': 50},
        'moves': ['Power Gem', 'Sludge Bomb', 'Stealth Rock', 'Recover', 'Thunderbolt', 'Protect'],
        'item': ['Leftovers', 'Life Orb'],
        'ability': ['Toxic Debris', 'Regenerator'],
    },
    {
        'name': 'Grimmsnarl',
        'types': ['Dark', 'Fairy'],
        'base_stats': {'hp': 95, 'atk': 120, 'def': 65, 'spa': 95, 'spd': 75, 'spe': 60},
        'moves': ['Foul Play', 'Thunder Wave', 'Taunt', 'Spirit Break', 'Protect', 'Knock Off'],
        'item': ['Leftovers', 'Assault Vest'],
        'ability': ['Prankster', 'Infiltrator'],
    },
    {
        'name': 'Dragonite',
        'types': ['Dragon', 'Flying'],
        'base_stats': {'hp': 91, 'atk': 134, 'def': 95, 'spa': 100, 'spd': 100, 'spe': 80},
        'moves': ['Dragon Dance', 'Outrage', 'Earthquake', 'Fire Punch', 'Roost', 'Thunder Punch'],
        'item': ['Weakness Policy', 'Choice Scarf', 'Leftovers'],
        'ability': ['Inner Focus', 'Multiscale'],
    },
    {
        'name': 'Garchomp',
        'types': ['Dragon', 'Ground'],
        'base_stats': {'hp': 108, 'atk': 130, 'def': 95, 'spa': 80, 'spd': 85, 'spe': 102},
        'moves': ['Dragon Claw', 'Earthquake', 'Stone Edge', 'Fire Fang', 'Swords Dance', 'Dragon Tail'],
        'item': ['Choice Band', 'Life Orb'],
        'ability': ['Rough Skin', 'Sand Veil'],
    },
    {
        'name': 'Hydreigon',
        'types': ['Dark', 'Dragon'],
        'base_stats': {'hp': 92, 'atk': 105, 'def': 90, 'spa': 125, 'spd': 90, 'spe': 98},
        'moves': ['Draco Meteor', 'Dark Pulse', 'Fire Blast', 'Flash Cannon', 'U-turn', 'Earth Power'],
        'item': ['Choice Specs', 'Life Orb'],
        'ability': ['Levitate', 'Moxie'],
    },
    {
        'name': 'Volcarona',
        'types': ['Bug', 'Fire'],
        'base_stats': {'hp': 85, 'atk': 60, 'def': 65, 'spa': 135, 'spd': 105, 'spe': 100},
        'moves': ['Quiver Dance', 'Fiery Dance', 'Bug Buzz', 'Fire Blast', 'Roost', 'Protect'],
        'item': ['Leftovers', 'Life Orb'],
        'ability': ['Flame Body', 'Swarm'],
    },
    {
        'name': 'Dragapult',
        'types': ['Dragon', 'Ghost'],
        'base_stats': {'hp': 88, 'atk': 120, 'def': 75, 'spa': 100, 'spd': 75, 'spe': 142},
        'moves': ['Dragon Pulse', 'Shadow Ball', 'U-turn', 'Thunderbolt', 'Fire Blast', 'Protect'],
        'item': ['Choice Specs', 'Life Orb'],
        'ability': ['Infiltrator', 'Cursed Body'],
    },
    {
        'name': 'Landorus-Therian',
        'types': ['Ground', 'Flying'],
        'base_stats': {'hp': 89, 'atk': 145, 'def': 90, 'spa': 105, 'spd': 80, 'spe': 91},
        'moves': ['Earthquake', 'Stone Edge', 'U-turn', 'Defog', 'Stealth Rock', 'Rock Polish'],
        'item': ['Choice Scarf', 'Leftovers'],
        'ability': ['Intimidate', 'Sheer Force'],
    },
    {
        'name': 'Corviknight',
        'types': ['Flying', 'Steel'],
        'base_stats': {'hp': 98, 'atk': 87, 'def': 105, 'spa': 59, 'spd': 85, 'spe': 67},
        'moves': ['Brave Bird', 'Iron Head', 'Roost', 'Defog', 'Bulk Up', 'Taunt'],
        'item': ['Leftovers', 'Rocky Helmet'],
        'ability': ['Pressure', 'Mirror Armor'],
    },
    {
        'name': 'Heatran',
        'types': ['Fire', 'Steel'],
        'base_stats': {'hp': 91, 'atk': 90, 'def': 106, 'spa': 130, 'spd': 106, 'spe': 77},
        'moves': ['Fire Blast', 'Flash Cannon', 'Earth Power', 'Stealth Rock', 'Protect', 'Taunt'],
        'item': ['Leftovers', 'Air Balloon'],
        'ability': ['Flash Fire', 'Iron Barbs'],
    },
    {
        'name': 'Toxapex',
        'types': ['Water', 'Poison'],
        'base_stats': {'hp': 50, 'atk': 63, 'def': 152, 'spa': 53, 'spd': 142, 'spe': 35},
        'moves': ['Scald', 'Recover', 'Toxic', 'Haze', 'Protect', 'Slack Off'],
        'item': ['Black Sludge', 'Leftovers'],
        'ability': ['Regenerator', 'Merciless'],
    },
    {
        'name': 'Clefable',
        'types': ['Fairy'],
        'base_stats': {'hp': 95, 'atk': 70, 'def': 73, 'spa': 95, 'spd': 90, 'spe': 60},
        'moves': ['Moonblast', 'Calm Mind', 'Soft-Boiled', 'Thunder Wave', 'Protect', 'Flamethrower'],
        'item': ['Leftovers', 'Wiki Berry'],
        'ability': ['Magic Guard', 'Unaware'],
    },
    {
        'name': 'Tapu Koko',
        'types': ['Electric', 'Fairy'],
        'base_stats': {'hp': 70, 'atk': 115, 'def': 85, 'spa': 95, 'spd': 75, 'spe': 130},
        'moves': ['Thunderbolt', 'Dazzling Gleam', 'Volt Switch', 'U-turn', 'Protect', 'Taunt'],
        'item': ['Choice Specs', 'Life Orb'],
        'ability': ['Electric Surge'],
    },
    {
        'name': 'Excadrill',
        'types': ['Ground', 'Steel'],
        'base_stats': {'hp': 110, 'atk': 135, 'def': 60, 'spa': 50, 'spd': 65, 'spe': 88},
        'moves': ['Earthquake', 'Iron Head', 'Rock Slide', 'Swords Dance', 'Protect', 'Rapid Spin'],
        'item': ['Choice Scarf', 'Life Orb'],
        'ability': ['Mold Breaker', 'Sand Rush'],
    },
    {
        'name': 'Scizor',
        'types': ['Bug', 'Steel'],
        'base_stats': {'hp': 70, 'atk': 130, 'def': 100, 'spa': 55, 'spd': 80, 'spe': 65},
        'moves': ['Bullet Punch', 'U-turn', 'Swords Dance', 'Roost', 'Knock Off', 'Iron Head'],
        'item': ['Leftovers', 'Choice Band'],
        'ability': ['Technician', 'Swarm'],
    },
    {
        'name': 'Machamp',
        'types': ['Fighting'],
        'base_stats': {'hp': 90, 'atk': 130, 'def': 80, 'spa': 65, 'spd': 85, 'spe': 55},
        'moves': ['Close Combat', 'Knock Off', 'Earthquake', 'Ice Punch', 'Bulk Up', 'Thunder Punch'],
        'item': ['Choice Band', 'Assault Vest'],
        'ability': ['No Guard', 'Guts'],
    },
    {
        'name': 'Zapdos',
        'types': ['Electric', 'Flying'],
        'base_stats': {'hp': 90, 'atk': 90, 'def': 85, 'spa': 125, 'spd': 90, 'spe': 100},
        'moves': ['Thunderbolt', 'Heat Wave', 'Roost', 'Defog', 'Thunder Wave', 'Volt Switch'],
        'item': ['Leftovers', 'Choice Specs'],
        'ability': ['Pressure', 'Static'],
    },
]


# ─────────────────────────────────────────────────────────────
#  BATTLE ENGINE
# ─────────────────────────────────────────────────────────────

class Battle:
    def __init__(self, player_team, opponent_team, data=None):
        self.player_team   = player_team
        self.opponent_team = opponent_team
        self.player_team.reset()
        self.opponent_team.reset()
        self.data          = data
        self.turn          = 1
        self.weather       = None
        self.weather_turns = 0
        self.terrain       = None
        # stealth_rock[0] = player side, stealth_rock[1] = opponent side
        self.stealth_rock  = [False, False]

    def log(self, message):
        print(message)

    #Damage calculation for each move and effectiveness
    def calculate_damage(self, attacker, defender, move):
        if move.name == 'Seismic Toss':
            # Deals flat damage equal to the user's level, ignores defenses
            return max(1, attacker.level)

        if move.category == 'Status' or move.power == 0:
            return 0

        attack_stat  = 'atk' if move.category == 'Physical' else 'spa'
        defense_stat = 'def' if move.category == 'Physical' else 'spd'

        attack  = attacker.effective_stat(attack_stat)
        defense = max(1, defender.effective_stat(defense_stat))

        level_factor = (2 * attacker.level) / 5 + 2
        base_damage  = ((level_factor * move.power * attack) / defense) / 50 + 2

        #STAB (Same Type Attack Bonus), if move is same type as pokemon apply 1.5x otherwise 1.0x
        stab          = 1.5 if move.type in attacker.types else 1.0
        effectiveness = type_effectiveness(move.type, defender.types)
        #Minor randomness in damage similarly to pokemon.
        random_factor = random.uniform(0.85, 1.0)
        modifier      = stab * effectiveness * random_factor

        if attacker.status == 'burn' and move.category == 'Physical':
            # Guts ignores the burn penalty - strong ability on fighting types
            if attacker.ability != 'Guts':
                #If pokemon doesnt have Guts, burn halves damage
                modifier *= 0.5

        #Attack admage items give
        item_bonus = 1.0
        #Life orb gives a 1.3x% damage boost
        if attacker.item == 'Life Orb':
            item_bonus *= 1.3
        #Choice moves give 1.5x bonus, band gives physical attack, specs give special attack, and scarf gives speed.
        if attacker.item == 'Choice Band'  and move.category == 'Physical':
            item_bonus *= 1.5
        if attacker.item == 'Choice Specs' and move.category == 'Special':
            item_bonus *= 1.5

        damage = int(base_damage * modifier * item_bonus)
        return max(1, damage)

    def team_index(self, pokemon):
        return 0 if pokemon in self.player_team.pokemons else 1

    
    def opponent_side_index(self, pokemon):
        return 1 - self.team_index(pokemon)

    # Apply entry hazard damage when a Pokemon switches in (more hazards could be implemented in future such as spikes, toxic spikes, etc)
    def apply_entry_hazard(self, pokemon):
        side = self.team_index(pokemon)
        if self.stealth_rock[side]:
            effectiveness    = type_effectiveness('Rock', pokemon.types)
            if effectiveness > 0:
                hazard_damage = max(1, int(pokemon.stats['hp'] * 0.125 * effectiveness))
                fainted = pokemon.apply_damage(hazard_damage)
                self.log(f"{pokemon.nickname} was hurt by Stealth Rock for {hazard_damage} HP!")
                if fainted:
                    self.log(f"{pokemon.nickname} fainted!")

    def apply_move(self, user, target, move):
        if user.fainted:
            return

        #Limited amount of each move can be used
        if user.pp.get(move.name, 0) <= 0:
            self.log(f"{user.nickname} has no PP left for {move.name}!")
            return

        # Choice lock: lock in on first move use
        if user.item in CHOICE_ITEMS:
            if user.choice_locked is None:
                user.choice_locked = move.name
            elif user.choice_locked != move.name:
                self.log(f"{user.nickname} is locked into {user.choice_locked}!")
                return

        # Clear last turn's protect
        if user.volatiles.get('protect') and move.name != 'Protect':
            user.volatiles.pop('protect', None)

        # ── Sleep check ───────────────────────────────────────
        if user.status == 'sleep':
            user.sleep_turns -= 1
            if user.sleep_turns <= 0:
                user.status = None
                user.status_counter = 0
                self.log(f"{user.nickname} woke up!")
            else:
                self.log(f"{user.nickname} is fast asleep!")
                user.pp[move.name] -= 1
                return

        # ── Freeze check ──────────────────────────────────────
        if user.status == 'freeze':
            #20% chance to thaw out each turn, otherwise still frozen
            if random.randint(1, 100) <= 20:
                user.status = None
                self.log(f"{user.nickname} thawed out!")
            else:
                self.log(f"{user.nickname} is frozen solid!")
                #Doesn't waste PP on moves when frozen
                user.pp[move.name] -= 1
                return

        # ── Paralysis check ───────────────────────────────────
        #25% chance to not be able to move during status
        if user.status == 'paralysis' and random.randint(1, 100) <= 25:
            self.log(f"{user.nickname} is paralyzed and can't move!")
            user.pp[move.name] -= 1
            return

        # ── Protect ───────────────────────────────────────────
        if move.name == 'Protect':
            user.volatiles['protect'] = True
            self.log(f"{user.nickname} protected itself!")
            user.pp[move.name] -= 1
            return

        # ── Healing status moves ───────────────────────────────
        if move.category == 'Status' and move.heal > 0:
            healed = int(user.stats['hp'] * move.heal)
            user.heal(healed)
            self.log(f"{user.nickname} healed {healed} HP with {move.name}.")
            user.pp[move.name] -= 1
            return

        # ── Stat boost moves ──────────────────────────────────
        if move.category == 'Status' and move.boosts:
            user.modify_boosts(move.boosts)
            boosts_str = ', '.join(f"{s} {v:+}" for s, v in move.boosts.items())
            self.log(f"{user.nickname} used {move.name}! ({boosts_str})")
            user.pp[move.name] -= 1
            return

        # ── Rapid Spin: clear own hazards ─────────────────────
        if move.name == 'Rapid Spin':
            side = self.team_index(user)
            if self.stealth_rock[side]:
                self.stealth_rock[side] = False
                self.log(f"{user.nickname} cleared Stealth Rock with Rapid Spin!")
            # Rapid Spin also deals damage now (handled below as physical move)

        # ── Stealth Rock: set hazard ──────────────────────────
        if move.name == 'Stealth Rock':
            opp_side = self.opponent_side_index(user)
            if not self.stealth_rock[opp_side]:
                self.stealth_rock[opp_side] = True
                self.log(f"Pointed stones floated around the opposing team!")
            else:
                self.log(f"Stealth Rock is already active on that side!")
            user.pp[move.name] -= 1
            return

        # ── Haze: clear ALL boosts on both sides ──────────────
        if move.name == 'Haze':
            user.clear_boosts()
            target.clear_boosts()
            self.log(f"{user.nickname} used Haze and eliminated all stat changes!")
            user.pp[move.name] -= 1
            return

        # ── Defog: clear hazards from both sides ───────────
        if move.name == 'Defog':
            opp_side = self.opponent_side_index(user)
            self.stealth_rock[0] = False
            self.stealth_rock[1] = False
            self.log(f"{user.nickname} used Defog and cleared entry hazards!")
            user.pp[move.name] -= 1
            return

        # ── Status-inflicting moves ───────────────────────────
        if move.category == 'Status' and move.status:
            if move.name == 'Taunt':
                if not target.fainted:
                    target.volatiles['taunt'] = 3
                    self.log(f"{user.nickname} taunted {target.nickname}!")
            elif move.name in ['Roar', 'Dragon Tail']:
                if not target.fainted:
                    target_team = self.player_team if target in self.player_team.pokemons else self.opponent_team
                    self.log(f"{user.nickname} forced {target.nickname} out!")
                    next_idx = target_team.first_available()
                    if next_idx is not None and next_idx != target_team.active_index:
                        target_team.switch(next_idx)
                        opp = self.player_team if target_team is self.opponent_team else self.opponent_team
                        self.on_switch_in(target_team.active(), opp)
            else:
                # Spore, Sleep Powder, Thunder Wave, Will-O-Wisp, Toxic, etc.
                if target.set_status(move.status):
                    self.log(f"{target.nickname} is now {move.status}!")
                else:
                    self.log(f"It didn't work on {target.nickname}.")
            user.pp[move.name] -= 1
            return

        # ── Air Balloon Ground immunity ────────────────────────
        if move.type == 'Ground' and target.item == 'Air Balloon':
            self.log(f"{target.nickname}'s Air Balloon protected it from {move.name}!")
            target.item = None
            target.item_revealed = True
            user.pp[move.name] -= 1
            return

        # ── Accuracy roll ─────────────────────────────────────
        if move.accuracy > 0 and not move.always_hit:
            if random.randint(1, 100) > move.accuracy:
                self.log(f"{user.nickname}'s {move.name} missed!")
                user.pp[move.name] -= 1
                return

        # ── Protect check ─────────────────────────────────────
        if target.volatiles.get('protect'):
            self.log(f"{target.nickname} protected itself!")
            target.volatiles.pop('protect', None)
            user.pp[move.name] -= 1
            return

        # ── Damage calculation ────────────────────────────────
        if move.category != 'Status':
            crit = random.random() < 1/24  # Gen 6+ crit rate

            if move.name == 'Foul Play':
                # Uses the target's attack stat against them
                t_atk  = target.effective_stat('atk')
                u_def  = user.effective_stat('def')
                lf     = (2 * user.level) / 5 + 2
                damage = max(1, int(((lf * move.power * t_atk) / u_def) / 50 + 2))
            else:
                damage = self.calculate_damage(user, target, move)
                if crit:
                    damage = int(damage * 1.5)

            fainted = target.apply_damage(damage)
            self.log(f"{user.nickname} used {move.name} on {target.nickname} for {damage} damage.")
            if fainted:
                self.log(f"{target.nickname} fainted!")

            effectiveness = type_effectiveness(move.type, target.types)
            if   effectiveness > 1:  self.log("It's super effective!")
            elif effectiveness == 0: self.log("It had no effect!")
            elif effectiveness < 1:  self.log("It's not very effective.")

            # ── Knock Off ─────────────────────────────────────
            if move.name == 'Knock Off' and target.item:
                self.log(f"{user.nickname} knocked off {target.nickname}'s {target.item}!")
                target.item_revealed = True
                target.item = None

            # ── Foul Play item reveal ──────────────────────────
            if move.name == 'Foul Play':
                target.reveal_item('Foul Play')

            # ── Rocky Helmet ──────────────────────────────────
            if target.item == 'Rocky Helmet' and move.category == 'Physical' and damage > 0 and target.is_alive():
                helmet_dmg = max(1, target.stats['hp'] // 6)
                fainted = user.apply_damage(helmet_dmg)
                self.log(f"{user.nickname} took {helmet_dmg} damage from {target.nickname}'s Rocky Helmet.")
                if fainted:
                    self.log(f"{user.nickname} fainted!")

            # ── Life Orb recoil ───────────────────────────────
            if user.item == 'Life Orb' and damage > 0 and user.is_alive():
                # Magic Guard prevents Life Orb recoil
                if user.ability != 'Magic Guard':
                    orb_recoil = max(1, int(user.stats['hp'] // 10))
                    fainted = user.apply_damage(orb_recoil)
                    self.log(f"{user.nickname} took {orb_recoil} recoil from Life Orb.")
                    if fainted:
                        self.log(f"{user.nickname} fainted!")

            # ── Weakness Policy ───────────────────────────────
            if (target.item == 'Weakness Policy'
                    and type_effectiveness(move.type, target.types) > 1
                    and target.is_alive()):
                target.modify_boosts({'atk': 2, 'spa': 2})
                self.log(f"{target.nickname}'s Weakness Policy activated! +2 Atk and SpA.")
                target.item = None

            # ── Rough Skin ────────────────────────────────────
            if (target.ability == 'Rough Skin'
                    and move.category == 'Physical'
                    and target.is_alive()):
                rough_dmg = max(1, target.stats['hp'] // 8)
                fainted = user.apply_damage(rough_dmg)
                self.log(f"{user.nickname} took {rough_dmg} from {target.nickname}'s Rough Skin.")
                if fainted:
                    self.log(f"{user.nickname} fainted!")

            # ── Iron Barbs (same mechanic as Rough Skin) ──────
            if (target.ability == 'Iron Barbs'
                    and move.category == 'Physical'
                    and target.is_alive()):
                barb_dmg = max(1, target.stats['hp'] // 8)
                fainted = user.apply_damage(barb_dmg)
                self.log(f"{user.nickname} took {barb_dmg} from {target.nickname}'s Iron Barbs.")
                if fainted:
                    self.log(f"{user.nickname} fainted!")

            # ── Static ────────────────────────────────────────
            if (target.ability == 'Static'
                    and move.category == 'Physical'
                    and user.status is None
                    and target.is_alive()
                    and random.randint(1, 100) <= 30):
                if user.set_status('paralysis'):
                    self.log(f"{user.nickname} was paralyzed by {target.nickname}'s Static!")

            # ── Flame Body ────────────────────────────────────
            if (target.ability == 'Flame Body'
                    and move.category == 'Physical'
                    and user.status is None
                    and target.is_alive()
                    and random.randint(1, 100) <= 30):
                if user.set_status('burn'):
                    self.log(f"{user.nickname} was burned by {target.nickname}'s Flame Body!")

            # ── Move recoil ───────────────────────────────────
            if move.recoil > 0 and user.is_alive():
                recoil_dmg = max(1, int(damage * move.recoil))
                fainted = user.apply_damage(recoil_dmg)
                self.log(f"{user.nickname} took {recoil_dmg} recoil damage.")
                if fainted:
                    self.log(f"{user.nickname} fainted!")

            # ── Drain moves ───────────────────────────────────
            if move.heal > 0 and user.is_alive():
                heal_amt = int(damage * move.heal)
                user.heal(heal_amt)
                self.log(f"{user.nickname} restored {heal_amt} HP.")

            # ── Secondary status chance ───────────────────────
            if (move.status and move.status != 'flinch'
                    and target.is_alive()
                    and random.randint(1, 100) <= move.status_chance):
                if target.set_status(move.status):
                    self.log(f"{target.nickname} is now {move.status}!")

            # ── Secondary stat drops on target ────────────────
            if (move.boosts and move.status_chance > 0
                    and random.randint(1, 100) <= move.status_chance
                    and target.is_alive()):
                target.modify_boosts(move.boosts)

            # ── Self boosts (e.g. Fiery Dance, Meteor Beam) ───
            if move.self_boosts and user.is_alive():
                user.modify_boosts(move.self_boosts)

        user.pp[move.name] -= 1

    def after_turn_effects(self, pokemon):
        if pokemon.fainted:
            return

        # ── Status damage ─────────────────────────────────────
        if pokemon.status == 'burn':
            # Guts pokemon get attack boost from burn instead of penalty, but still take damage
            dmg = max(1, pokemon.stats['hp'] // 16)
            fainted = pokemon.apply_damage(dmg)
            self.log(f"{pokemon.nickname} is hurt by its burn! ({dmg} HP)")
            if fainted:
                self.log(f"{pokemon.nickname} fainted!")

        elif pokemon.status == 'poison':
            dmg = max(1, pokemon.stats['hp'] // 8)
            fainted = pokemon.apply_damage(dmg)
            self.log(f"{pokemon.nickname} is hurt by poison! ({dmg} HP)")
            if fainted:
                self.log(f"{pokemon.nickname} fainted!")

        elif pokemon.status == 'toxic':
            pokemon.status_counter += 1
            dmg = max(1, pokemon.stats['hp'] * pokemon.status_counter // 16)
            fainted = pokemon.apply_damage(dmg)
            self.log(f"{pokemon.nickname} is hurt by badly poisoned! ({dmg} HP)")
            if fainted:
                self.log(f"{pokemon.nickname} fainted!")

        # ── Item effects ──────────────────────────────────────
        if pokemon.is_alive():
            if pokemon.item == 'Leftovers':
                heal_amt = max(1, pokemon.stats['hp'] // 16)
                pokemon.heal(heal_amt)
                self.log(f"{pokemon.nickname} recovered {heal_amt} HP from Leftovers.")

            elif pokemon.item == 'Black Sludge':
                # Black Sludge: heals Poison types, damages non-Poison
                if 'Poison' in pokemon.types:
                    heal_amt = max(1, pokemon.stats['hp'] // 16)
                    pokemon.heal(heal_amt)
                    self.log(f"{pokemon.nickname} recovered {heal_amt} HP from Black Sludge.")
                else:
                    dmg = max(1, pokemon.stats['hp'] // 8)
                    fainted = pokemon.apply_damage(dmg)
                    self.log(f"{pokemon.nickname} was hurt by Black Sludge! ({dmg} HP)")
                    if fainted:
                        self.log(f"{pokemon.nickname} fainted!")

        # ── Taunt counter ─────────────────────────────────────
        if pokemon.volatiles.get('taunt'):
            pokemon.volatiles['taunt'] -= 1
            if pokemon.volatiles['taunt'] <= 0:
                pokemon.volatiles.pop('taunt', None)
                self.log(f"{pokemon.nickname}'s Taunt wore off!")

    def on_switch_in(self, pokemon, opposing_team):
        if pokemon.fainted:
            return
        self.apply_entry_hazard(pokemon)
        if pokemon.fainted:
            return

        target = opposing_team.active()
        pokemon.volatiles.pop('protect', None)
        pokemon.choice_locked = None

        if pokemon.ability == 'Intimidate' and target and target.is_alive():
            # Mirror Armor bounces the Intimidate drop back
            if target.ability == 'Mirror Armor':
                pokemon.modify_boosts({'atk': -1})
                self.log(f"{target.nickname}'s Mirror Armor reflected Intimidate back at {pokemon.nickname}!")
            else:
                target.modify_boosts({'atk': -1})
                self.log(f"{pokemon.nickname}'s Intimidate lowered {target.nickname}'s Attack!")

        if pokemon.ability == 'Regenerator' and pokemon.current_hp < pokemon.stats['hp']:
            heal_amt = max(1, pokemon.stats['hp'] // 3)
            pokemon.heal(heal_amt)
            self.log(f"{pokemon.nickname}'s Regenerator restored {heal_amt} HP!")

        if pokemon.ability == 'Natural Cure' and pokemon.status:
            pokemon.status = None
            pokemon.status_counter = 0
            pokemon.sleep_turns = 0
            self.log(f"{pokemon.nickname}'s Natural Cure healed its status!")

    def valid_moves(self, pokemon):
        return [m for m in pokemon.moves if pokemon.pp[m.name] > 0]

    def opponent_decision(self):
        active = self.opponent_team.active()
        enemy  = self.player_team.active()

        if active.fainted:
            return {'action': 'switch', 'index': self.opponent_team.first_available()}

        available = [m for m in active.moves if active.pp[m.name] > 0]
        if not available:
            return {'action': 'move', 'move': random.choice(active.moves), 'target': enemy}

        # Score each move
        best_move, best_score = None, -1
        for move in available:
            score = 0
            if move.category != 'Status':
                score += self.calculate_damage(active, enemy, move)
                if type_effectiveness(move.type, enemy.types) > 1:
                    score += 30
            else:
                if move.name in ['Calm Mind', 'Nasty Plot', 'Dragon Dance', 'Quiver Dance', 'Swords Dance']:
                    # Only set up if we have a health lead and the boost isn't capped
                    if active.current_hp > active.stats['hp'] * 0.5:
                        score += 25 + 5 * sum(max(0, 6 - abs(active.boosts.get(s, 0))) for s in move.boosts)
                if move.name == 'Will-O-Wisp' and enemy.status is None and enemy.stats['atk'] > enemy.stats['spa']:
                    score += 45  # prioritize burning physical attackers
                if move.name == 'Thunder Wave' and enemy.status is None and not enemy.types in [['Electric'], ['Ground']]:
                    score += 30
                if move.name == 'Toxic' and enemy.status is None and not enemy.types in [['Poison'], ['Steel']]:
                    score += 25 #Poisons opponent if no status and not a poison or steel type.
                if move.name == 'Protect':
                    # Protect is more valuable when low on health
                    score += 25 if active.current_hp <= active.stats['hp'] * 0.4 else 5
                if move.name in ['Recover', 'Roost', 'Soft-Boiled', 'Slack Off'] and active.current_hp <= active.stats['hp'] * 0.5:
                    score += 45
                if move.name == 'Stealth Rock' and not self.stealth_rock[self.opponent_side_index(active)]:
                    score += 30
                if move.name in ['Rapid Spin', 'Defog'] and self.stealth_rock[self.team_index(active)]:
                    score += 35
                if move.name == 'Haze':
                    # Haze is useful if the player has significant boosts
                    total_player_boosts = sum(max(0, v) for v in enemy.boosts.values())
                    score += total_player_boosts * 10
                if move.name in ['Roar', 'Dragon Tail'] and enemy.is_alive():
                    total_enemy_boosts = sum(max(0, v) for v in enemy.boosts.values())
                    score += 15 + total_enemy_boosts * 8  # phazing is better vs boosted mons

            if score > best_score:
                best_score, best_move = score, move

        # Consider switching out if low HP
        skill_factor = clamp((self.opponent_team.rating - 1200) / 1000, 0.2, 0.95)
        if active.current_hp <= active.stats['hp'] * 0.30:
            best_switch_idx, best_switch_score = None, -1
            for idx, candidate in enumerate(self.opponent_team.pokemons):
                if candidate.fainted or idx == self.opponent_team.active_index:
                    continue
                sw_score = 20
                for m in candidate.moves:
                    if m.category != 'Status':
                        sw_score += self.calculate_damage(candidate, enemy, m) / 10
                if sw_score > best_switch_score:
                    best_switch_score, best_switch_idx = sw_score, idx
            if best_switch_idx is not None and best_switch_score > best_score * 0.1:
                return {'action': 'switch', 'index': best_switch_idx}

        # No Lifer opponents always make the optimal play
        if self.opponent_team.rating >= NO_LIFER_RATING:
            chosen = best_move or random.choice(available)
        elif random.random() < skill_factor:
            chosen = best_move or random.choice(available)
        else:
            chosen = random.choice(available)

        return {'action': 'move', 'move': chosen, 'target': enemy}

    def display_battle_screen(self):
        active = self.player_team.active()
        enemy  = self.opponent_team.active()

        def hp_bar(current, max_hp):
            filled = int((current / max(1, max_hp)) * 20)
            bar    = '[' + '#' * filled + ' ' * (20 - filled) + ']'
            pct    = int(current / max(1, max_hp) * 100)
            return f"{bar} {current}/{max_hp} ({pct}%)"

        def status_str(poke):
            if poke.status:
                return f"[{poke.status.upper()}]"
            return ''

        self.log('\n' + '=' * 60)
        self.log(f"  YOUR SIDE  | Turn {self.turn}")
        self.log(f"  {active.nickname} {status_str(active)}")
        self.log(f"  HP: {hp_bar(active.current_hp, active.stats['hp'])}")
        self.log(f"  Item: {active.item or 'None'} | Ability: {active.ability}")

        # Show active boosts if any
        active_boosts = {s: v for s, v in active.boosts.items() if v != 0}
        if active_boosts:
            boost_str = ', '.join(f"{s} {v:+}" for s, v in active_boosts.items())
            self.log(f"  Boosts: {boost_str}")

        self.log('-' * 60)
        item_display = enemy.item if enemy.item_revealed else '???'
        self.log(f"  OPPONENT   |")
        self.log(f"  {enemy.nickname} {status_str(enemy)}")
        self.log(f"  HP: {hp_bar(enemy.current_hp, enemy.stats['hp'])}")
        self.log(f"  Item: {item_display} | Ability: {enemy.ability}")

        enemy_boosts = {s: v for s, v in enemy.boosts.items() if v != 0}
        if enemy_boosts:
            boost_str = ', '.join(f"{s} {v:+}" for s, v in enemy_boosts.items())
            self.log(f"  Boosts: {boost_str}")

        # Show field conditions
        field_conditions = []
        if self.stealth_rock[0]: field_conditions.append("Stealth Rock (your side)")
        if self.stealth_rock[1]: field_conditions.append("Stealth Rock (their side)")
        if field_conditions:
            self.log(f"  Field: {', '.join(field_conditions)}")

        self.log('=' * 60)

    def prompt_player_action(self):
        self.display_battle_screen()
        active = self.player_team.active()
        enemy  = self.player_team.active()  # used for display only

        self.log("\nChoose an action:")
        for i, move in enumerate(active.moves, start=1):
            pp      = active.pp[move.name]
            locked  = ' (locked)' if active.choice_locked == move.name else ''
            no_pp   = ' (no PP)' if pp <= 0 else ''
            eff     = type_effectiveness(move.type, self.opponent_team.active().types)
            eff_str = ' [SE]' if eff > 1 else (' [NVE]' if 0 < eff < 1 else (' [immune]' if eff == 0 else ''))
            self.log(f"  {i}. {move.name} | {move.type} {move.category} | PP {pp}/{move.pp}{locked}{no_pp}{eff_str}")

        self.log("  s. Switch  | t. Teams  | h. Help  | q. Forfeit")

        choice = input('\n> ').strip().lower()

        if choice in ['t', 'team', 'teams']:
            self.show_teams()
            return self.prompt_player_action()

        if choice in ['h', 'help']:
            self.log("  Enter a move number to attack, s to switch, t to see all Pokemon, q to forfeit.")
            return self.prompt_player_action()

        if choice in ['q', 'forfeit', 'quit']:
            self.log("You forfeited.")
            return {'action': 'forfeit'}

        if choice in ['s', 'switch'] or choice.startswith('switch'):
            return self._prompt_switch()

        if choice.isdigit():
            move_idx = int(choice) - 1
            if 0 <= move_idx < len(active.moves):
                move = active.moves[move_idx]
                if active.pp[move.name] <= 0:
                    self.log("No PP left for that move.")
                    return self.prompt_player_action()
                # Taunt prevents status moves
                if active.volatiles.get('taunt') and move.category == 'Status':
                    self.log(f"{active.nickname} is taunted and can't use status moves!")
                    return self.prompt_player_action()
                return {'action': 'move', 'move': move, 'target': self.opponent_team.active()}
            self.log("Invalid move number.")

        else:
            self.log("Didn't catch that. Enter a number, s, t, h, or q.")

        return self.prompt_player_action()

    def _prompt_switch(self):
        active = self.player_team.active()
        self.log("\nChoose a Pokemon to switch to:")
        for i, poke in enumerate(self.player_team.pokemons, start=1):
            if poke.fainted:
                status_display = "FAINTED"
            else:
                hp_pct = int(poke.current_hp / poke.stats['hp'] * 100)
                status_display = f"{poke.current_hp}/{poke.stats['hp']} ({hp_pct}%)"
                if poke.status:
                    status_display += f" [{poke.status.upper()}]"
            active_mark = ' ← active' if i - 1 == self.player_team.active_index else ''
            self.log(f"  {i}. {poke.nickname} ({'/'.join(poke.types)}) {status_display}{active_mark}")

        while True:
            sel = input("Switch to: ").strip()
            if not sel.isdigit():
                self.log("Enter the number of the Pokemon to switch to.")
                continue
            idx = int(sel) - 1
            if idx == self.player_team.active_index:
                self.log(f"{active.nickname} is already active!")
                continue
            if self.player_team.switch(idx):
                self.log(f"Go, {self.player_team.active().nickname}!")
                return {'action': 'switch', 'index': idx}
            self.log("Can't switch there (fainted or invalid). Try again.")

    def show_teams(self):
        self.log("\nYour team:")
        for poke in self.player_team.pokemons:
            hp_str  = 'FAINTED' if poke.fainted else f"{poke.current_hp}/{poke.stats['hp']}"
            stat_str = f"[{poke.status.upper()}]" if poke.status else ''
            self.log(f"  - {poke.nickname} ({'/'.join(poke.types)}) {hp_str} {stat_str} | {poke.item} | {poke.ability}")

        self.log("\nOpponent team:")
        for poke in self.opponent_team.pokemons:
            hp_str    = 'FAINTED' if poke.fainted else f"{poke.current_hp}/{poke.stats['hp']}"
            item_disp = poke.item if poke.item_revealed else '???'
            stat_str  = f"[{poke.status.upper()}]" if poke.status else ''
            self.log(f"  - {poke.nickname} ({'/'.join(poke.types)}) {hp_str} {stat_str} | {item_disp}")

    def show_battle_intro(self):
        self.log(f"\nFormat: {FORMAT_NAME}")
        self.log(f"Opponent Elo: {self.opponent_team.rating} ({progress_title(self.opponent_team.rating)})")
        if self.opponent_team.rating >= NO_LIFER_RATING:
            self.log("  !! Warning: No Lifer-tier opponent. This will be rough.")
        self.log("\nOpponent team preview:")
        for poke in self.opponent_team.pokemons:
            self.log(f"  - {poke.nickname} ({'/'.join(poke.types)})")
        self.log("\nYour team:")
        for poke in self.player_team.pokemons:
            self.log(f"  - {poke.nickname} ({'/'.join(poke.types)})")
        self.log("\nChoose your lead. The opponent picks after you lock in.")
        self.log("Opponent item info stays hidden until revealed in battle.")

    def choose_opponent_lead(self):
        alive = [i for i, p in enumerate(self.opponent_team.pokemons) if p.is_alive()]
        if not alive:
            return 0
        # Smarter opponents lead with a fast threat; weaker ones are more random
        if self.opponent_team.rating >= 1800:
            return sorted(alive, key=lambda i: self.opponent_team.pokemons[i].effective_stat('spe'), reverse=True)[0]
        if self.opponent_team.rating <= 1400:
            return random.choice(alive)
        top_half = sorted(alive, key=lambda i: self.opponent_team.pokemons[i].effective_stat('spe'), reverse=True)
        return random.choice(top_half[:max(1, len(top_half)//2)])

    def choose_leads(self):
        self.log("\nChoose your lead:")
        for i, poke in enumerate(self.player_team.pokemons, start=1):
            self.log(f"  {i}. {poke.nickname} ({'/'.join(poke.types)})")

        while True:
            sel = input("Lead: ").strip()
            if sel.lower() in ['t', 'team']:
                self.show_teams()
                continue
            if not sel.isdigit():
                self.log("Enter the number of your lead Pokemon.")
                continue
            idx = int(sel) - 1
            if self.player_team.set_active(idx):
                break
            self.log("Invalid selection, try again.")

        self.log(f"You chose {self.player_team.active().nickname}.")
        opp_idx = self.choose_opponent_lead()
        self.opponent_team.set_active(opp_idx)
        self.log(f"Opponent sent out {self.opponent_team.active().nickname}!")

        self.on_switch_in(self.player_team.active(),   self.opponent_team)
        self.on_switch_in(self.opponent_team.active(), self.player_team)

    def update_elo(self, player_won):
        p_rating = self.player_team.rating
        o_rating = self.opponent_team.rating
        expected = 1.0 / (1.0 + 10 ** ((o_rating - p_rating) / 400))
        actual   = 1.0 if player_won else 0.0
        change   = int(round(32 * (actual - expected)))
        new_rating = max(MIN_RATING, p_rating + change)

        self.player_team.rating = new_rating
        self.log(f"\nRating change: {change:+}  →  {new_rating} ({progress_title(new_rating)})")

        next_thr, next_reward = next_milestone(new_rating)
        if next_thr:
            self.log(f"  Next milestone: {next_thr} ({next_reward})")

        if self.data is not None:
            self.data['player'] = new_rating
            self.data.setdefault('history', []).append({
                'result':         'win' if player_won else 'loss',
                'opponent_rating': o_rating,
                'team':            self.player_team.name,
                'opponent_team':  [p.nickname for p in self.opponent_team.pokemons],
                'rating_change':   change,
            })
            save_data(self.data)
        else:
            save_ratings({'player': new_rating})

    def fainted_check(self):
        # Player side
        if self.player_team.active().fainted and self.player_team.has_alive():
            self.log(f"\n{self.player_team.active().nickname} fainted! Choose a replacement:")
            for i, poke in enumerate(self.player_team.pokemons, start=1):
                if poke.is_alive():
                    self.log(f"  {i}. {poke.nickname} ({poke.current_hp}/{poke.stats['hp']})")
            while True:
                choice = input("> ").strip()
                if not choice.isdigit():
                    continue
                idx = int(choice) - 1
                if self.player_team.switch(idx):
                    new_active = self.player_team.active()
                    self.log(f"Go, {new_active.nickname}!")
                    self.on_switch_in(new_active, self.opponent_team)
                    break
                self.log("Invalid choice.")

        # Opponent side
        if self.opponent_team.active().fainted and self.opponent_team.has_alive():
            next_idx = self.opponent_team.first_available()
            if next_idx is not None:
                self.opponent_team.switch(next_idx)
                new_opp = self.opponent_team.active()
                self.log(f"Opponent sent out {new_opp.nickname}!")
                self.on_switch_in(new_opp, self.player_team)

    def run(self):
        self.log(f"\n{'='*60}")
        self.log(f"  BATTLE START: {self.player_team.name} vs {self.opponent_team.name}")
        self.log(f"{'='*60}")
        self.show_battle_intro()
        self.choose_leads()

        forfeited = False

        while self.player_team.has_alive() and self.opponent_team.has_alive():
            player_action   = self.prompt_player_action()

            if player_action['action'] == 'forfeit':
                forfeited = True
                break

            opponent_action = self.opponent_decision()

            # Process switches first (they happen before move resolution)
            if player_action['action'] == 'switch':
                self.player_team.switch(player_action['index'])
                self.log(f"{self.player_team.active().nickname} switched in!")
                self.on_switch_in(self.player_team.active(), self.opponent_team)

            if opponent_action['action'] == 'switch':
                self.opponent_team.switch(opponent_action['index'])
                self.log(f"Opponent switched to {self.opponent_team.active().nickname}!")
                self.on_switch_in(self.opponent_team.active(), self.player_team)

            # Resolve moves with priority and speed in mind
            if player_action['action'] == 'move' and opponent_action['action'] == 'move':
                p_move = player_action['move']
                o_move = opponent_action['move']

                p_prio = p_move.priority
                o_prio = o_move.priority

                if p_prio != o_prio:
                    first = 'player' if p_prio > o_prio else 'opponent'
                else:
                    p_spd = self.player_team.active().effective_stat('spe')
                    o_spd = self.opponent_team.active().effective_stat('spe')
                    if p_spd == o_spd:
                        # True speed tie: random coinflip, not player-favored
                        first = random.choice(['player', 'opponent'])
                    else:
                        first = 'player' if p_spd > o_spd else 'opponent'

                if first == 'player':
                    self.apply_move(self.player_team.active(), self.opponent_team.active(), p_move)
                    if self.opponent_team.active().is_alive():
                        self.apply_move(self.opponent_team.active(), self.player_team.active(), o_move)
                else:
                    self.apply_move(self.opponent_team.active(), self.player_team.active(), o_move)
                    if self.player_team.active().is_alive():
                        self.apply_move(self.player_team.active(), self.opponent_team.active(), p_move)

            elif player_action['action'] == 'move':
                self.apply_move(self.player_team.active(), self.opponent_team.active(), player_action['move'])
            elif opponent_action['action'] == 'move':
                self.apply_move(self.opponent_team.active(), self.player_team.active(), opponent_action['move'])

            # End-of-turn residual damage and item recovery
            self.after_turn_effects(self.player_team.active())
            self.after_turn_effects(self.opponent_team.active())

            # Handle faints and forced switches
            self.fainted_check()
            self.turn += 1

        # Battle result
        if forfeited:
            self.log("\nYou forfeited. Better luck next time.")
            self.update_elo(False)
        elif self.player_team.has_alive():
            self.log("\nYou won the battle!")
            self.update_elo(True)
        else:
            self.log("\nYou lost the battle.")
            self.update_elo(False)

        self.log("\nGG! Thanks for playing.")
        return self.player_team.has_alive() and not forfeited


# ─────────────────────────────────────────────────────────────
#  TEAM BUILDING HELPERS
# ─────────────────────────────────────────────────────────────

# Automatic moveset builder
def choose_moveset(move_pool):
    
    # Build a balanced moveset: try to include one physical, one special, one status move,
    # then fill the 4th slot randomly from whatever's left.
    physical  = [m for m in move_pool if m in MOVES and MOVES[m].category == 'Physical']
    special   = [m for m in move_pool if m in MOVES and MOVES[m].category == 'Special']
    status    = [m for m in move_pool if m in MOVES and MOVES[m].category == 'Status']
    chosen    = []

    if physical: chosen.append(random.choice(physical))
    if special:  chosen.append(random.choice(special))
    if status:   chosen.append(random.choice(status))

    remaining = [m for m in move_pool if m not in chosen and m in MOVES]
    while len(chosen) < 4 and remaining:
        pick = random.choice(remaining)
        chosen.append(pick)
        remaining.remove(pick)

    return chosen

# Species strength calculator, higher = stronger
def species_strength(species):
    base_total = sum(species['base_stats'].values())
    move_power = sum(MOVES[m].power for m in species.get('moves', []) if m in MOVES and MOVES[m].power > 0)
    item_bonus = 20 if species.get('item') else 0
    return base_total + move_power * 4 + item_bonus

#Higher elo, better opponents similarly to real game
def opponent_quality_from_elo(elo):
    if elo >= NO_LIFER_RATING:
        return NO_LIFER_QUALITY
    return clamp(0.35 + (elo - 1200) / 1200, 0.35, 0.95)

#Randomly create a team of 6 with stronger Pokemon as quality approaches 1.0 and elo becomes 1.5k
#Here is where the other helper functions such as strength and moveset are useful to efficiently create a team
def build_team(name, pool, count=6, quality=1.0, rating=1500):
    effective_pool = pool
    if 0.0 < quality < 1.0:
        sorted_pool = sorted(pool, key=species_strength)
        sample_size = max(count, int(len(sorted_pool) * quality))
        effective_pool = sorted_pool[-sample_size:] if quality >= 0.5 else sorted_pool[:sample_size]

    chosen   = random.sample(effective_pool, min(count, len(effective_pool)))
    pokemons = []
    for species in chosen:
        moves   = choose_moveset(species.get('moves', []))
        item    = species.get('item')
        ability = species.get('ability', 'Pressure')
        if isinstance(item,    list): item    = random.choice(item)
        if isinstance(ability, list): ability = random.choice(ability)
        pokemons.append(Pokemon(
            species['name'], species['name'],
            species['types'], species['base_stats'],
            moves, item, ability
        ))
    return Team(name, pokemons, rating=rating)

# Helper to save team data.
def serialize_team(team):
    return {
        'name': team.name,
        'pokemons': [
            {
                'name':       p.nickname,
                'species':    p.species,
                'types':      p.types,
                'base_stats': p.base_stats,
                'moves':      [m.name for m in p.moves],
                'item':       p.item,
                'ability':    p.ability,
            }
            for p in team.pokemons
        ],
    }


#Helper to LOAD team data
def deserialize_team(data, rating=1500):
    pokemons = []
    for e in data.get('pokemons', []):
        pokemons.append(Pokemon(
            e['name'], e.get('species', e['name']),
            e['types'], e['base_stats'], e['moves'],
            e.get('item', 'Leftovers'), e.get('ability', 'Pressure'),
        ))
    return Team(data.get('name', 'Custom Team'), pokemons, rating=rating)


# ─────────────────────────────────────────────────────────────
#  BATTLE HISTORY / ELO HELPERS
# ─────────────────────────────────────────────────────────────

#Calculates wins, losses, and streaks.
def battle_record(data):
    history = data.get('history', [])
    wins    = sum(1 for e in history if e.get('result') == 'win')
    losses  = sum(1 for e in history if e.get('result') == 'loss')
    streak  = 0
    for entry in reversed(history[-10:]):
        result = entry.get('result')
        if streak == 0:
            streak = 1 if result == 'win' else -1
        elif result == 'win'  and streak > 0: streak += 1
        elif result == 'loss' and streak < 0: streak -= 1
        else: break
    return wins, losses, streak

# Calculates the title based on rating. Also shows milestones and streak.
def show_user_summary(data):
    wins, losses, streak = battle_record(data)
    rating = data.get('player', 1000)
    title  = progress_title(rating)
    next_thr, reward = next_milestone(rating)

    print(f"\n{'─'*40}")
    print(f"  Elo: {rating}  |  Rank: {title}")
    print(f"  Record: {wins}W / {losses}L", end='')
    if streak > 1:   print(f"  |  Win streak: {streak}")
    elif streak < -1: print(f"  |  Loss streak: {-streak}")
    else:             print()
    if next_thr:
        print(f"  Next milestone: {next_thr} Elo  —  {reward}")
    print(f"  Saved teams: {len(data.get('teams', []))}")
    print(f"{'─'*40}\n")

#Shows last few battles with results, opponent rating, and team used.
def show_battle_history(data, limit=10):
    history = data.get('history', [])
    if not history:
        print("No battle history yet.")
        return
    print(f"\nLast {min(limit, len(history))} battles:")
    for entry in history[-limit:]:
        result  = 'W' if entry.get('result') == 'win' else 'L'
        team    = entry.get('team', '?')
        opp     = ', '.join(entry.get('opponent_team', []))
        change  = entry.get('rating_change', 0)
        opp_elo = entry.get('opponent_rating', '?')
        print(f"  {result} | {team} vs [{opp}] (opp Elo {opp_elo}) | {change:+}")


# ─────────────────────────────────────────────────────────────
#  TEAM MANAGEMENT
# ─────────────────────────────────────────────────────────────

#Builds team with user input, allowing rerolls until satisfied. Saves to data if accepted, and asks if you want to make more teams
def create_team(data):
    name = input("Team name: ").strip() or f"Team {len(data.get('teams', [])) + 1}"
    while True:
        team = build_team(name, POKEMON_POOL, quality=1.0)
        print(f"\nGenerated: {team.name}")
        for i, poke in enumerate(team.pokemons, start=1):
            print(f"  {i}. {poke.nickname} ({'/'.join(poke.types)}) | {poke.item} | {poke.ability}")
            print(f"     {', '.join(m.name for m in poke.moves)}")
        choice = input("\nKeep this team? [y / n / r to reroll]: ").strip().lower()
        if choice == 'y':
            data.setdefault('teams', []).append(serialize_team(team))
            save_data(data)
            print(f"Saved '{team.name}'.")
            return team
        if choice == 'n':
            return None
        if choice == 'r':
            continue
        print("Enter y, n, or r.")


#Describes a team in detail, showing each Pokemon's name, types, item, ability, and moves.
def describe_team(team_data):
    lines = [f"{team_data.get('name')}:"]
    for i, poke in enumerate(team_data.get('pokemons', []), start=1):
        lines.append(f"  {i}. {poke.get('name')} ({'/'.join(poke.get('types', []))})")
        lines.append(f"     Item: {poke.get('item')} | Ability: {poke.get('ability')}")
        lines.append(f"     Moves: {', '.join(poke.get('moves', []))}")
    return '\n'.join(lines)

# Renames team by index, asking for new name.
def rename_team(data, index):
    teams = data.get('teams', [])
    if not 0 <= index < len(teams): return False
    new_name = input(f"Rename '{teams[index].get('name')}' to: ").strip()
    if not new_name:
        print("Name can't be empty.")
        return False
    teams[index]['name'] = new_name
    #Saves data after renaming team
    save_data(data)
    print(f"Renamed to '{new_name}'.")
    return True

# Deletes team by index, asks for confirmation. 
def delete_team(data, index):
    teams = data.get('teams', [])
    if not 0 <= index < len(teams): return False
    confirm = input(f"Delete '{teams[index].get('name')}'? [y/N]: ").strip().lower()
    #If you confirm, pop (delete) team, otherwise cancels.
    if confirm == 'y':
        removed = teams.pop(index)
        #Saves after deletion
        save_data(data)
        print(f"Deleted '{removed.get('name')}'.")
        return True
    print("Cancelled.")
    return False

#Copys team by index, creating team with same pokemon
def copy_team(data, index):
    teams = data.get('teams', [])
    if not 0 <= index < len(teams):
        print("Invalid team number.")
        return False
    copied = json.loads(json.dumps(teams[index]))
    copied['name'] = f"{teams[index].get('name')} Copy"
    data.setdefault('teams', []).append(copied)
    save_data(data)
    print(f"Copied to '{copied['name']}'.")
    return True

#Exports team by index to file to therefore save data next time person plays.
def export_team(data, index):
    teams = data.get('teams', [])
    if not 0 <= index < len(teams):
        print("Invalid team number.")
        return False
    path = input("Export filename (e.g. my_team.json): ").strip()
    if not path: return False
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(teams[index], f, indent=2)
    print(f"Exported '{teams[index].get('name')}' to {path}.")
    return True

#Imports from file. 
def import_team(data):
    path = input("Import from file: ").strip()
    # When not in path, print error message and return to menu.
    if not path or not os.path.exists(path):
        print("File not found.")
        return None
    #If file found, open it and open as json.
    with open(path, 'r', encoding='utf-8') as f:
        try:
            imported = json.load(f)
            #If it isn't a list, make it an imported list.
            if not isinstance(imported, list):
                imported = [imported]
            #For each team in the imported list, check pokemon key.
            for td in imported:
                #If key isn't there skip index
                if 'pokemons' not in td:
                    print(f"Skipping invalid entry.")
                    continue
                #If key is valid, check name key, if it isn't there, name it imported + number of teams + 1. Then append team to data and print imported team name.
                td['name'] = td.get('name', f"Imported {len(data.get('teams', [])) + 1}")
                data.setdefault('teams', []).append(td)
                print(f"Imported '{td['name']}'.")
            save_data(data)
            return True
        except (json.JSONDecodeError, ValueError):
            print("Failed to parse file.")
            return None

#Team selection menu, allowing you to view, rename, delete, copy, export, and import teams. 
def choose_team(data):
    teams = data.get('teams', [])
    while True:
        if not teams:
            # Allows you to create a new team if you don't have any.
            print("No saved teams. Let's create one.")
            team = create_team(data)
            if team:
                return team
            continue
        # If you have teams, show them and give options to manage them or choose one to battle with.
        print("\nSaved Teams:")
        #Print each teams index number (first is 1, then +1 infinitely) and name.
        for i, td in enumerate(teams, start=1):
            print(f"  {i}. {td.get('name')}")
        #OPTIONS
        print("  a. Add team | v. View | r. Rename | d. Delete | p. Copy | x. Export | i. Import | c. Choose")
        
        action = input("Option: ").strip().lower()

        def get_idx(prompt):
            sel = input(prompt).strip()
            return int(sel) - 1 if sel.isdigit() else -1
        
        #Depending on choice, call each team helper function accordingly. As expected, calls none if invalid.
        if action == 'a':
            team = create_team(data)
            if team: teams = data.get('teams', [])
        elif action == 'v':
            idx = get_idx("Team number: ")
            if 0 <= idx < len(teams): print(describe_team(teams[idx]))
            else: print("Invalid.")
        elif action == 'r':
            idx = get_idx("Team number: ")
            if rename_team(data, idx): teams = data.get('teams', [])
        elif action == 'd':
            idx = get_idx("Team number: ")
            if delete_team(data, idx): teams = data.get('teams', [])
        elif action == 'p':
            idx = get_idx("Team number: ")
            if copy_team(data, idx): teams = data.get('teams', [])
        elif action == 'x':
            idx = get_idx("Team number: ")
            export_team(data, idx)
        elif action == 'i':
            if import_team(data): teams = data.get('teams', [])
        elif action == 'c':
            idx = get_idx("Team number: ")
            if 0 <= idx < len(teams):
                return deserialize_team(teams[idx], rating=data.get('player', 1000))
            print("Invalid selection.")
        else:
            print("Unknown option.")


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────

def main():
    #Random seed for team generation and opponent behavior.
    random.seed()
    #Loads data, then show users summary.
    data = load_data()
    show_user_summary(data)

    #Choose to view history, import team, or continue to team selection and battling.
    action = input("Enter h for history, or press Enter to continue: ").strip().lower()
    if action == 'h':
        show_battle_history(data)
    elif action == 'i':
        import_team(data)

    player_team = choose_team(data)

    # Battle loop
    while True:
        wins, _, _    = battle_record(data)
        player_rating = data.get('player', 1000)
        opp_rating    = calculate_opponent_rating(player_rating, wins)
        opp_quality   = clamp(opponent_quality_from_elo(opp_rating) + min(wins / 50, 0.15), 0.35, 0.99)

        opp_team = build_team('Opponent', POKEMON_POOL, quality=opp_quality, rating=opp_rating)

        print(f"\nYour Elo: {player_rating}  |  Opponent Elo: {opp_rating} ({progress_title(opp_rating)})")

        battle = Battle(player_team, opp_team, data)
        battle.run()

        again = input("\nBattle again? [Y/n]: ").strip().lower()
        if again == 'n':
            break

        # Ask them to switch teams between each battle
        switch = input("Switch teams? [y/N]: ").strip().lower()
        if switch == 'y':
            player_team = choose_team(data)
    #End of main loop, thanks for playing message.
    print("\nThanks for playing. See you next time!")


if __name__ == '__main__':
    main()