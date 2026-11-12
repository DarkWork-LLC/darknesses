#!/usr/bin/env python3
"""
AI Bot Generator for Darkness BBS.
Creates AI-controlled bot players with cyberpunk names that wander, fight, and interact.
"""
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from game.models import Player, User, Room, Item, InventoryItem


# Personality archetypes. Each defines default behavior traits and a stat/gear
# bias so bots of the same personality feel distinct in combat and social play.
BOT_PERSONALITIES = {
    "aggressive": {
        "aggression": (75, 100),
        "social": (0, 30),
        "karma": (-80, -20),
        "description": "Player-killer. Hunts humans and rarely groups.",
    },
    "mercenary": {
        "aggression": (40, 70),
        "social": (30, 60),
        "karma": (-20, 20),
        "description": "Fights for coin. Neutral, will work with or against anyone.",
    },
    "vigilante": {
        "aggression": (50, 80),
        "social": (40, 70),
        "karma": (20, 80),
        "description": "Hunts evil-aligned players and defends the weak.",
    },
    "social": {
        "aggression": (10, 40),
        "social": (70, 100),
        "karma": (0, 60),
        "description": "Loves parties, greets everyone, rarely starts fights.",
    },
    "trader": {
        "aggression": (10, 30),
        "social": (40, 70),
        "karma": (-10, 40),
        "description": "Hoards money, frequents shops, avoids pointless combat.",
    },
    "explorer": {
        "aggression": (20, 50),
        "social": (20, 50),
        "karma": (-20, 40),
        "description": "Wanders distant zones, avoids crowds, maps the grid.",
    },
    "coward": {
        "aggression": (0, 20),
        "social": (10, 40),
        "karma": (-30, 30),
        "description": "Flees at the first sign of danger, fights only NPCs.",
    },
    "berserker": {
        "aggression": (85, 100),
        "social": (0, 20),
        "karma": (-60, 20),
        "description": "Fights to the death, never retreats, low self-preservation.",
    },
    "hermit": {
        "aggression": (30, 60),
        "social": (0, 20),
        "karma": (-40, 20),
        "description": "Avoids players entirely, hunts NPCs in isolated sectors.",
    },
    "chaotic": {
        "aggression": (0, 100),
        "social": (0, 100),
        "karma": (-100, 100),
        "description": "Unpredictable. Could help you or backstab you next tick.",
    },
}

PERSONALITY_CHOICES = sorted(BOT_PERSONALITIES.keys())


def roll_trait(rng_tuple):
    """Roll a random integer within a (min, max) trait range."""
    return random.randint(rng_tuple[0], rng_tuple[1])


# Cyberpunk-themed bot names (diverse handles for a living grid)
BOT_NAMES = [
    "NeonShade", "ChromeWraith", "GlitchMonk", "ZeroCool", "RogueAI",
    "Circuitbreaker", "Synthrunner", "Dataphantom", "Voltstriker", "PixelSlayer",
    "NeuralJack", "CyberWitch", "BinaryStorm", "Quantumshade", "Echoprotocol",
    "Voidwalker", "Lasermonk", "Novablade", "Cipherpunk", "JadeSpirit",
    "KiraCode", "LynxSystem", "MakoShift", "NexusFlame", "OnyxData",
    "PrismHack", "RiftWalker", "SparkAgent", "TalonNet", "ViperCode",
    "Blitz", "CrackShell", "DuskLoader", "EmberSync", "FrostByte",
    "GrimAccess", "BurnShift", "DataDervish", "EchoJack", "FluxBishop",
    "Ghostwire", "HashQueen", "IceBreaker", "JunkRat", "KernelPanic",
    "LagSwitch", "MemeLord", "NullPtr", "Overclock", "PacketSniffer",
    "Rootkit", "ScriptKiddie", "Trojannon", "Uplink", "Vaporwave",
    "WarezKing", "XorGuru", "YoloSwan", "ZeroDay", "AcidBurn",
    "CrashOverride", "CerealKiller", "LordNikolai", "RazorBlade",
    "PhantomPulse", "NeonNecromancer", "ChromeCobra", "SteelSerpent",
    "IronWyrm", "SilverSpecter", "GoldGhoul", "CopperCryptid",
    "BrassBanshee", "TinMan", "LeadLich", "PlatinumPhantom",
    "ObsidianOracle", "OnyxOmen", "JetJinx", "EbonyEcho",
    "ShadowStalker", "NightShade", "DarkData", "GraveShift",
    "MorgueCode", "CoffinWare", "CryptKeeper", "ReaperNode",
    "DoomCookie", "HellfirePacket", "InfernoJack", "PyreProtocol",
    "AshWalker", "SootSpecter", "EmberEye", "CinderStrike",
    "SparkSiren", "BoltBanshee", "VoltViper", "AmpAssassin",
    "WattWraith", "JouleJuggernaut", "FaradFiend", "OhmOgre",
    "TeslaTroll", "EdisonEcho", "WestinghouseWraith", "VoltaVandal",
    "GalvaniGhost", "HertzHunter", "CyberSquid", "NetNinja",
    "WebWraith", "GridGhost", "MatrixMarauder", "ConsoleCowboy",
    "DeckHead", "Jackpointer", "RunnerX", "StreetDoc", "FixerFace",
    "JohnsonJr", "MrNobody", "MsMisfit", "BossBot", "MinionMax",
    "LackeyLex", "PeonPete", "DroneDelta", "UnitSeven", "ModelM",
    "SeriesS", "GenNine", "ProtoOne", "BetaZero", "AlphaPrime",
    "OmegaNull", "SigmaNine", "ThetaThirteen", "EpsilonEcho",
]


# Sensible race/class combinations expanded for personality variety
RACE_CLASS_COMBOS = [
    ("Cyborg", "Street Samurai"), ("Cyborg", "Heavy"), ("Cyborg", "Berserker"),
    ("Android", "Netrunner"), ("Android", "Techie"), ("Android", "Warlock"),
    ("Bio-hacked", "Medie"), ("Bio-hacked", "Psycher"), ("Bio-hacked", "Street Samurai"),
    ("Mutant", "Heavy"), ("Mutant", "Jade Dragon"), ("Mutant", "Berserker"),
    ("Human", "Fixer"), ("Human", "Trickster"), ("Human", "Street Samurai"),
    ("Elf", "Thief"), ("Elf", "Jade Dragon"), ("Elf", "Ranger"),
    ("Goblin", "Thief"), ("Goblin", "Trickster"), ("Goblin", "Berserker"),
    ("Void-Walker", "Psycher"), ("Void-Walker", "Warlock"), ("Void-Walker", "Thief"),
    ("Synth-Soul", "Netrunner"), ("Synth-Soul", "Warlock"), ("Synth-Soul", "Techie"),
    ("Orc", "Street Samurai"), ("Orc", "Heavy"), ("Orc", "Berserker"),
    ("Dark Elf", "Thief"), ("Dark Elf", "Assassin"),
]


class Command(BaseCommand):
    help = "Create AI bot players with cyberpunk names"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=25,
            help="Number of bots to create (5-60)",
        )
        parser.add_argument("--reset", action="store_true", help="Delete all existing bots first")
        parser.add_argument(
            "--wipe-users",
            action="store_true",
            help="Delete ALL user accounts (humans and bots) before creating new bots. "
            "Django superusers are preserved unless --purge-superusers is also given.",
        )
        parser.add_argument(
            "--purge-superusers",
            action="store_true",
            help="With --wipe-users: also delete Django superuser accounts.",
        )
        parser.add_argument(
            "--personality",
            type=str,
            default=None,
            help=f"Force all bots to this personality: {', '.join(PERSONALITY_CHOICES)}",
        )

    def handle(self, *args, **kwargs):
        count = min(max(5, kwargs.get("count", 25)), 60)  # Clamp between 5-60
        reset = kwargs.get("reset", False)
        wipe_users = kwargs.get("wipe_users", False)
        purge_superusers = kwargs.get("purge_superusers", False)
        force_personality = kwargs.get("personality")
        if force_personality and force_personality not in PERSONALITY_CHOICES:
            self.stdout.write(
                self.style.ERROR(
                    f"Invalid personality '{force_personality}'. "
                    f"Choices: {', '.join(PERSONALITY_CHOICES)}"
                )
            )
            return

        with transaction.atomic():
            if wipe_users:
                self.stdout.write("Wiping ALL user accounts...")
                users = User.objects.all()
                if not purge_superusers:
                    users = users.exclude(is_superuser=True)
                total = users.count()
                users.delete()
                note = (
                    " (superusers preserved)"
                    if not purge_superusers
                    else " (including superusers)"
                )
                self.stdout.write(self.style.SUCCESS(f"Deleted {total} users{note}."))
            elif reset:
                self.stdout.write("Removing existing bots...")
                # Delete bot users and their players
                bot_players = Player.objects.filter(is_bot=True)
                for bp in bot_players:
                    bp.user.delete()
                self.stdout.write(self.style.SUCCESS(f"Removed {bot_players.count()} bots."))

            # Get rooms organized by zone level ranges for appropriate bot placement
            zone_rooms = {}
            for room in Room.objects.filter(safe_zone=False):
                zone = room.zone
                if zone not in zone_rooms:
                    zone_rooms[zone] = []
                zone_rooms[zone].append(room)

            if not zone_rooms:
                self.stdout.write(self.style.WARNING("No rooms available. Run init_game first."))
                return

            # Get all items for equipping bots
            all_items = list(Item.objects.all())
            weapons = [i for i in all_items if i.item_type == "weapon"]
            armor = [i for i in all_items if i.item_type == "armor"]

            created_count = 0
            used_names = set(
                Player.objects.filter(is_bot=True).values_list("user__username", flat=True)
            )

            for _ in range(count):
                # Find unused bot name
                available_names = [n for n in BOT_NAMES if n not in used_names]
                if not available_names:
                    self.stdout.write(self.style.WARNING("Ran out of unique bot names!"))
                    break

                bot_name = random.choice(available_names)
                used_names.add(bot_name)

                # Random race/class combo
                race, game_class = random.choice(RACE_CLASS_COMBOS)

                # Random level 1-20 (higher ceiling for tougher bots)
                lvl = random.randint(1, 20)

                # Pick personality (forced or random, weighted toward common archetypes)
                if force_personality:
                    personality = force_personality
                else:
                    # Weighted: common personalities appear more often
                    weights = {
                        "aggressive": 12,
                        "mercenary": 12,
                        "social": 10,
                        "trader": 10,
                        "explorer": 8,
                        "coward": 6,
                        "vigilante": 6,
                        "berserker": 5,
                        "hermit": 5,
                        "chaotic": 4,
                    }
                    population = list(weights.keys())
                    weight_vals = [weights[p] for p in population]
                    personality = random.choices(population, weights=weight_vals, k=1)[0]

                traits = BOT_PERSONALITIES[personality]
                aggression = roll_trait(traits["aggression"])
                social = roll_trait(traits["social"])
                karma = roll_trait(traits["karma"])

                # Create user
                user = User.objects.create_user(username=bot_name, password="bot")

                # Choose level-appropriate room based on bot level
                appropriate_rooms = []
                for zone, rooms in zone_rooms.items():
                    # Match bot level to zone (simplified logic)
                    if lvl <= 5 and zone in ["slums", "neon", "hub"]:
                        appropriate_rooms.extend(rooms)
                    elif lvl <= 10 and zone in ["slums", "neon", "industrial", "corporate"]:
                        appropriate_rooms.extend(rooms)
                    elif lvl <= 15 and zone in ["industrial", "corporate", "undergrid"]:
                        appropriate_rooms.extend(rooms)
                    elif lvl >= 10:
                        # High level bots can go anywhere
                        appropriate_rooms.extend(rooms)

                # Fallback to any room if no appropriate rooms found
                if not appropriate_rooms:
                    appropriate_rooms = list(Room.objects.filter(safe_zone=False))

                location = random.choice(appropriate_rooms)

                # Personality-biased stat generation
                # Base stats scale with level
                str_stat = random.randint(8, 12 + lvl)
                int_stat = random.randint(8, 12 + lvl)
                wil_stat = random.randint(8, 12 + lvl)
                agi_stat = random.randint(8, 12 + lvl)
                hea_stat = random.randint(8, 12 + lvl)
                cha_stat = random.randint(8, 12 + lvl)

                # Apply personality stat bias
                if personality in ("aggressive", "berserker", "mercenary"):
                    str_stat += random.randint(2, 5)
                    hea_stat += random.randint(1, 3)
                elif personality in ("vigilante", "social"):
                    cha_stat += random.randint(2, 5)
                    wil_stat += random.randint(1, 3)
                elif personality == "trader":
                    cha_stat += random.randint(2, 5)
                elif personality in ("explorer", "coward", "hermit"):
                    agi_stat += random.randint(2, 5)
                    int_stat += random.randint(1, 3)
                elif personality == "chaotic":
                    # Randomize one stat way up, one way down
                    stats_list = [str_stat, int_stat, wil_stat, agi_stat, hea_stat, cha_stat]
                    boost_idx = random.randrange(6)
                    penal_idx = random.randrange(6)
                    while penal_idx == boost_idx:
                        penal_idx = random.randrange(6)
                    stats_list[boost_idx] += random.randint(4, 8)
                    stats_list[penal_idx] = max(3, stats_list[penal_idx] - random.randint(3, 6))
                    str_stat, int_stat, wil_stat, agi_stat, hea_stat, cha_stat = stats_list

                # Berserkers and aggressive bots have lower self-preservation (fight to death)
                # Cowards and traders have higher HP (run and survive)
                hp_max = 100 + (hea_stat * 2) + (lvl * 20)
                if personality == "berserker":
                    hp_max = int(hp_max * 0.85)  # glass cannon
                elif personality in ("coward", "trader", "explorer"):
                    hp_max = int(hp_max * 1.15)  # survivable

                mana_max = 20 + (wil_stat * 2) + (lvl * 10)

                attack = 10 + (str_stat // 2) + lvl
                defense = 5 + (agi_stat // 2) + lvl

                # Create bot player
                bot = Player.objects.create(
                    user=user,
                    race=race,
                    gender=random.choice(["Male", "Female", "Other"]),
                    game_class=game_class,
                    location=location,
                    lvl=lvl,
                    exp=random.randint(0, lvl * 120),
                    money=random.randint(25, 200 + (lvl * 50)),
                    hp=hp_max,
                    hp_max=hp_max,
                    mana=mana_max,
                    mana_max=mana_max,
                    str_stat=str_stat,
                    int_stat=int_stat,
                    wil_stat=wil_stat,
                    agi_stat=agi_stat,
                    hea_stat=hea_stat,
                    cha_stat=cha_stat,
                    attack=attack,
                    defense=defense,
                    karma=karma,
                    online=True,
                    is_bot=True,
                    bot_karma=karma,
                    bot_aggression=aggression,
                    bot_social=social,
                    bot_personality=personality,
                    stat_points=random.randint(0, lvl // 2),
                    last_bot_action=timezone.now()
                    - timezone.timedelta(seconds=random.randint(30, 60)),
                    last_activity=timezone.now(),
                    last_move_time=timezone.now(),
                )

                # Personality-biased gear equipping
                # Aggressive/berserker: more likely to have weapon
                weapon_chance = 0.7
                if personality in ("aggressive", "berserker", "mercenary"):
                    weapon_chance = 0.9
                elif personality in ("coward", "trader", "hermit"):
                    weapon_chance = 0.5

                if weapons and random.random() < weapon_chance:
                    weapon = random.choice(weapons)
                    InventoryItem.objects.create(player=bot, item=weapon, equipped=True)

                # Traders and social bots more likely to have armor (survival/social)
                armor_chance = 0.5
                if personality in ("trader", "social", "coward"):
                    armor_chance = 0.7
                elif personality == "berserker":
                    armor_chance = 0.3

                if armor and random.random() < armor_chance:
                    armor_piece = random.choice(armor)
                    InventoryItem.objects.create(player=bot, item=armor_piece, equipped=True)

                created_count += 1
                self.stdout.write(
                    f"Created bot: {bot_name} ({race} {game_class}, Lv {lvl}, {personality})"
                )

            self.stdout.write(self.style.SUCCESS(f"\nCreated {created_count} AI bots."))
