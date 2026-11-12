#!/usr/bin/env python3
"""
Procedural Cyberpunk World Generator for Darkness BBS.
Generates rooms, items, NPCs, and maps with seeded RNG.
"""
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from game.models import NPC, Item, Room, GameWorld, Player


# ── Data Tables ──────────────────────────────────────────────────────────────

WEAPON_TABLE = [
    ("Stun Baton", "Standard issue security baton.", 5, 50, "common", 2, "one-handed", {}),
    (
        "Mono-Blade",
        "Vibrating edge for clean cuts.",
        12,
        300,
        "uncommon",
        5,
        "one-handed",
        {"agi_bonus": 2},
    ),
    (
        "Heavy Slugger",
        "High-caliber kinetic pistol.",
        20,
        750,
        "uncommon",
        -2,
        "one-handed",
        {"str_bonus": 1},
    ),
    (
        "Laser Drill",
        "Industrial tool repurposed for violence.",
        15,
        450,
        "uncommon",
        0,
        "one-handed",
        {"int_bonus": 2},
    ),
    (
        "Plasma Caster",
        "Superheated plasma bolt launcher.",
        28,
        1200,
        "rare",
        -3,
        "two-handed",
        {"wil_bonus": 3},
    ),
    (
        "Neural Spike",
        "Disrupts cybernetic implants.",
        35,
        2000,
        "rare",
        8,
        "one-handed",
        {"int_bonus": 5},
    ),
    (
        "Railgun",
        "Electromagnetic accelerator.",
        50,
        5000,
        "epic",
        -5,
        "two-handed",
        {"str_bonus": 8},
    ),
    (
        "Void Blade",
        "Cuts through dimensions.",
        80,
        15000,
        "legendary",
        10,
        "one-handed",
        {"agi_bonus": 10, "wil_bonus": 10},
    ),
    ("EMP Grenade", "Disables electronics in radius.", 10, 200, "common", 0, "one-handed", {}),
    (
        "Cyber Katana",
        "Monomolecular edge blade.",
        25,
        900,
        "rare",
        6,
        "one-handed",
        {"agi_bonus": 4},
    ),
    (
        "Phase Ripper",
        "High-frequency claw.",
        30,
        1500,
        "rare",
        7,
        "one-handed",
        {"agi_bonus": 3, "str_bonus": 2},
    ),
    (
        "Gravity Hammer",
        "Crushes armor with ease.",
        45,
        3500,
        "epic",
        -8,
        "two-handed",
        {"str_bonus": 12},
    ),
    (
        "Hand Cannon",
        "Massive firepower in a small package.",
        35,
        2500,
        "rare",
        -4,
        "one-handed",
        {"str_bonus": 5, "hea_bonus": 2},
    ),
    (
        "Vibro-Knife",
        "Rapid vibration cuts through mesh.",
        18,
        600,
        "uncommon",
        12,
        "one-handed",
        {"agi_bonus": 5},
    ),
    (
        "Shock Gloves",
        "Deliver lethal voltage on contact.",
        15,
        800,
        "uncommon",
        8,
        "one-handed",
        {"str_bonus": 2, "agi_bonus": 2},
    ),
    (
        "Sniper Rail gun",
        "Long-range magnetic projectile.",
        55,
        6000,
        "epic",
        -10,
        "two-handed",
        {"int_bonus": 8, "agi_bonus": 4},
    ),
    (
        "Toxic Dart Gun",
        "Injects neurotoxins silently.",
        22,
        1800,
        "rare",
        5,
        "one-handed",
        {"int_bonus": 6, "cha_bonus": 3},
    ),
    # Ninja Weapons
    (
        "Kunai",
        "A throwing blade favored by ninjas.",
        12,
        300,
        "uncommon",
        15,
        "ninja",
        {"agi_bonus": 3},
    ),
    ("Shuriken", "Five-pointed throwing star.", 8, 150, "common", 18, "ninja", {"agi_bonus": 2}),
    (
        "Katana",
        "Curved blade for swift cuts.",
        20,
        800,
        "rare",
        10,
        "ninja",
        {"agi_bonus": 5, "str_bonus": 2},
    ),
    (
        "Ninjato",
        "Shorter, straighter cousin of the katana.",
        15,
        500,
        "uncommon",
        12,
        "ninja",
        {"agi_bonus": 4},
    ),
    (
        "Kusarigama",
        "Sickle attached to a weighted chain.",
        18,
        600,
        "rare",
        8,
        "ninja",
        {"agi_bonus": 3, "wil_bonus": 2},
    ),
    (
        "Tanto",
        "A dagger for close-quarters stealth.",
        10,
        200,
        "common",
        14,
        "ninja",
        {"agi_bonus": 2},
    ),
    (
        "Fuuma Shuriken",
        "Massive ninja star that returns.",
        25,
        1200,
        "epic",
        12,
        "ninja",
        {"agi_bonus": 6},
    ),
    (
        "Kakushi Kama",
        "Concealed sickle for surprise attacks.",
        16,
        450,
        "uncommon",
        11,
        "ninja",
        {"agi_bonus": 3, "str_bonus": 2},
    ),
    # Street Samurai Weapons
    (
        "Samurai Blade",
        "Traditional blade for the discerning warrior.",
        22,
        700,
        "rare",
        10,
        "one-handed",
        {"str_bonus": 3, "agi_bonus": 3},
    ),
    (
        "Wakizashi",
        "Shorter companion blade.",
        12,
        350,
        "uncommon",
        12,
        "one-handed",
        {"agi_bonus": 2},
    ),
    (
        "Nodachi",
        "Long saber for powerful strikes.",
        28,
        1000,
        "rare",
        6,
        "two-handed",
        {"str_bonus": 5},
    ),
    (
        "Tachi",
        "Curved cavalry blade.",
        20,
        600,
        "uncommon",
        8,
        "one-handed",
        {"str_bonus": 2, "agi_bonus": 2},
    ),
    (
        "Butterfly Sword",
        "Paired blades for rapid strikes.",
        16,
        500,
        "uncommon",
        14,
        "one-handed",
        {"agi_bonus": 4},
    ),
    # Netrunner Weapons
    (
        "Data Spike",
        "Hacks systems with electrical discharge.",
        10,
        200,
        "common",
        10,
        "one-handed",
        {"int_bonus": 2},
    ),
    (
        "Logic Bomb",
        "Explodes with digital fury.",
        18,
        400,
        "uncommon",
        5,
        "one-handed",
        {"int_bonus": 3},
    ),
    (
        "Black ICE Injector",
        "Injects hostile code directly.",
        25,
        800,
        "rare",
        8,
        "one-handed",
        {"int_bonus": 4, "wil_bonus": 2},
    ),
    (
        "Neural Lance",
        "Pierces cybernetic defenses.",
        20,
        600,
        "uncommon",
        12,
        "one-handed",
        {"int_bonus": 3, "agi_bonus": 2},
    ),
    # Techie Weapons
    (
        "Tesla Wrench",
        "Electrifies targets on contact.",
        14,
        350,
        "uncommon",
        6,
        "one-handed",
        {"int_bonus": 2, "str_bonus": 2},
    ),
    (
        "Plasma Cutter",
        "Sears through armor.",
        18,
        500,
        "uncommon",
        8,
        "one-handed",
        {"int_bonus": 3},
    ),
    (
        "Drone Controller",
        "Commands mechanical allies.",
        12,
        400,
        "common",
        10,
        "one-handed",
        {"int_bonus": 2},
    ),
    (
        "Nanite Injector",
        "Releases swarm of repair drones.",
        16,
        450,
        "uncommon",
        4,
        "one-handed",
        {"int_bonus": 2, "hea_bonus": 2},
    ),
    # Medie Weapons
    (
        "Surgical Scalpel",
        "Precise medical blade.",
        8,
        150,
        "common",
        14,
        "one-handed",
        {"int_bonus": 2, "hea_bonus": 2},
    ),
    (
        "Biotech Injector",
        "Heals allies, harms enemies.",
        12,
        300,
        "uncommon",
        8,
        "one-handed",
        {"hea_bonus": 3, "int_bonus": 2},
    ),
    (
        "Trauma Saw",
        "Industrial medical tool.",
        15,
        250,
        "common",
        6,
        "one-handed",
        {"hea_bonus": 2},
    ),
    (
        "Stim Gun",
        "Delivers healing nanites.",
        10,
        200,
        "common",
        12,
        "one-handed",
        {"hea_bonus": 2},
    ),
    # Fixer Weapons
    (
        "Credit Pistol",
        "Fires solid gold slugs.",
        16,
        500,
        "uncommon",
        6,
        "one-handed",
        {"cha_bonus": 3, "str_bonus": 2},
    ),
    (
        "Bribe Blade",
        "Convinces targets to surrender.",
        12,
        350,
        "common",
        10,
        "one-handed",
        {"cha_bonus": 2},
    ),
    (
        "Contract Rifle",
        "Long-range elimination tool.",
        24,
        800,
        "rare",
        4,
        "two-handed",
        {"cha_bonus": 4},
    ),
    (
        "Market Grenade",
        "Explodes with economic chaos.",
        14,
        250,
        "uncommon",
        8,
        "one-handed",
        {"cha_bonus": 2},
    ),
    # Heavy Weapons
    (
        "Titan Fist",
        "Massive gauntlet for crushing.",
        30,
        1000,
        "rare",
        -4,
        "one-handed",
        {"str_bonus": 6, "hea_bonus": 3},
    ),
    (
        "Siege Axe",
        "Devastating two-handed cleaver.",
        35,
        1200,
        "rare",
        -6,
        "two-handed",
        {"str_bonus": 8},
    ),
    (
        "Bulwark Shield",
        "Defensive barrier.",
        0,
        600,
        "uncommon",
        -2,
        "one-handed",
        {"hea_bonus": 5, "str_bonus": 2},
    ),
    (
        "War Club",
        "Brutal bludgeoning weapon.",
        22,
        500,
        "uncommon",
        -2,
        "one-handed",
        {"str_bonus": 4},
    ),
    (
        "Juggernaut Cannon",
        "Area suppression weapon.",
        28,
        900,
        "rare",
        -8,
        "two-handed",
        {"str_bonus": 5, "hea_bonus": 3},
    ),
    # Psycher Weapons
    (
        "Mind Lance",
        "Psychic spear of pure thought.",
        18,
        500,
        "uncommon",
        8,
        "one-handed",
        {"int_bonus": 4},
    ),
    (
        "Psionic Orb",
        "Floating sphere of mental energy.",
        14,
        350,
        "common",
        10,
        "one-handed",
        {"int_bonus": 3},
    ),
    (
        "Telekinetic Gauntlet",
        "Moves objects with force.",
        16,
        400,
        "uncommon",
        6,
        "one-handed",
        {"int_bonus": 3, "str_bonus": 2},
    ),
    (
        "Mental Blaster",
        "Direct neural assault.",
        22,
        600,
        "rare",
        4,
        "one-handed",
        {"int_bonus": 4, "wil_bonus": 2},
    ),
    # Warlock Weapons
    (
        "Soul Reaver",
        "Drains life force.",
        18,
        550,
        "uncommon",
        6,
        "one-handed",
        {"int_bonus": 3, "cha_bonus": -1},
    ),
    (
        "Chaos Staff",
        "Unpredictable dark energy.",
        20,
        600,
        "uncommon",
        2,
        "two-handed",
        {"int_bonus": 4},
    ),
    (
        "Blood Dagger",
        "Sacrificial blade.",
        12,
        300,
        "common",
        10,
        "one-handed",
        {"int_bonus": 2, "wil_bonus": 2},
    ),
    (
        "Shadow Wand",
        "Channels necrotic power.",
        14,
        350,
        "common",
        8,
        "one-handed",
        {"int_bonus": 3},
    ),
    # Priest Weapons
    ("Divine Rod", "Channel holy energy.", 14, 400, "uncommon", 6, "one-handed", {"wil_bonus": 3}),
    (
        "Blessed Mace",
        "Sacred crushing weapon.",
        18,
        500,
        "uncommon",
        4,
        "one-handed",
        {"wil_bonus": 3, "str_bonus": 2},
    ),
    (
        "Prayer Book",
        "Grants protective blessings.",
        0,
        200,
        "common",
        0,
        "one-handed",
        {"wil_bonus": 2},
    ),
    (
        "Holy Water Sprayer",
        "Sprays sanctified liquid.",
        12,
        300,
        "common",
        8,
        "one-handed",
        {"wil_bonus": 2},
    ),
    # Trickster Weapons
    (
        "Joke Pistol",
        "Fires explosive laughter.",
        10,
        250,
        "common",
        10,
        "one-handed",
        {"cha_bonus": 2},
    ),
    (
        "Card Shooter",
        "Fires razor-edged cards.",
        14,
        350,
        "uncommon",
        12,
        "one-handed",
        {"cha_bonus": 3},
    ),
    ("Confetti Bomb", "Blinds and confuses.", 8, 200, "common", 14, "one-handed", {"cha_bonus": 2}),
    (
        "Lucky Dice",
        "Random effect generator.",
        16,
        400,
        "uncommon",
        8,
        "one-handed",
        {"cha_bonus": 3},
    ),
    # Thief Weapons
    (
        "Backstab Blade",
        "Perfect for stealth kills.",
        14,
        400,
        "uncommon",
        12,
        "one-handed",
        {"agi_bonus": 4},
    ),
    (
        "Poison Dagger",
        "Coated in neurotoxin.",
        10,
        250,
        "common",
        14,
        "one-handed",
        {"agi_bonus": 3, "int_bonus": 2},
    ),
    (
        "Garrote Wire",
        "Silent strangulation tool.",
        8,
        200,
        "common",
        16,
        "one-handed",
        {"agi_bonus": 2},
    ),
    (
        "Smoke Pellet",
        "Creates cover for escape.",
        6,
        150,
        "common",
        18,
        "one-handed",
        {"agi_bonus": 2},
    ),
    # Jade Dragon Weapons
    (
        "Jade Nunchuks",
        "Twin dragon-engraved nunchuks. Only a Jade Dragon can wield them.",
        18,
        1200,
        "rare",
        15,
        "jade",
        {"str_bonus": 5, "agi_bonus": 5},
    ),
    (
        "Jade Bo Staff",
        "A staff carved from ancient jade. Channels chi with every strike.",
        25,
        2000,
        "rare",
        10,
        "jade",
        {"str_bonus": 8, "agi_bonus": 3},
    ),
    (
        "Jade Sai",
        "Three-pronged jade daggers. Swift and precise.",
        15,
        1500,
        "rare",
        18,
        "jade",
        {"agi_bonus": 8, "str_bonus": 2},
    ),
    (
        "Jade Tonfa",
        "Jade-reinforced tonfa. Blocks and strikes in fluid motion.",
        22,
        1800,
        "rare",
        8,
        "jade",
        {"str_bonus": 6, "hea_bonus": 4},
    ),
    (
        "Jade War Fans",
        "Deadly folding fans edged with jade. Elegant and lethal.",
        20,
        2200,
        "epic",
        20,
        "jade",
        {"agi_bonus": 10, "cha_bonus": 5},
    ),
    (
        "Jade Crescent Blades",
        "Twin crescent-shaped jade blades. Whirlwind of death.",
        30,
        3500,
        "epic",
        12,
        "jade",
        {"str_bonus": 10, "agi_bonus": 8},
    ),
]

DRUG_TABLE = [
    # 5-6 New Drugs with bonuses and penalties across stats
    (
        "Neuro-Jack",
        "Sharpens the mind but rots the body.",
        150,
        "uncommon",
        0.25,
        {"int_bonus": 5, "wil_bonus": 3, "str_bonus": -2, "hea_bonus": -2},
    ),
    (
        "Combat-Rush",
        "Unlocks raw power at the cost of sanity.",
        200,
        "uncommon",
        0.30,
        {"str_bonus": 6, "agi_bonus": 4, "wil_bonus": -3, "cha_bonus": -3},
    ),
    (
        "Synth-Ghost",
        "Phase slightly out of reality. Evasive but frail.",
        300,
        "rare",
        0.20,
        {"agi_bonus": 8, "hea_bonus": -5, "str_bonus": -3},
    ),
    (
        "Neon-Glow",
        "Radiate charismatic energy, but suffer memory leaks.",
        150,
        "uncommon",
        0.15,
        {"cha_bonus": 10, "int_bonus": -4, "wil_bonus": -2},
    ),
    (
        "Over-Clock",
        "Maximum performance across all systems. Lethal dependency.",
        600,
        "epic",
        0.50,
        {
            "str_bonus": 4,
            "int_bonus": 4,
            "wil_bonus": 4,
            "agi_bonus": 4,
            "hea_bonus": 4,
            "cha_bonus": 4,
        },
    ),
    (
        "Iron-Skin",
        "Hardens tissue into armor. Slows reflexes.",
        250,
        "rare",
        0.35,
        {"hea_bonus": 10, "agi_bonus": -5, "cha_bonus": -2},
    ),
]

BOSS_WEAPONS = {
    "slums": [
        (
            "Street King's Shiv",
            "A jagged blade that reeks of the gutters.",
            40,
            0,
            "epic",
            12,
            "one-handed",
            {"agi_bonus": 8, "cha_bonus": 5},
        ),
        (
            "Gutter Brawler's Knuckles",
            "Weighted with lead and street history.",
            35,
            0,
            "epic",
            8,
            "one-handed",
            {"str_bonus": 10, "hea_bonus": 5},
        ),
    ],
    "industrial": [
        (
            "Forge-Master's Wrench",
            "Massive industrial tool.",
            55,
            0,
            "epic",
            -4,
            "two-handed",
            {"str_bonus": 15, "hea_bonus": 5},
        ),
        (
            "Steam-Powered Piercer",
            "Hisses with pressure.",
            50,
            0,
            "epic",
            2,
            "one-handed",
            {"str_bonus": 8, "wil_bonus": 5},
        ),
    ],
    "corporate": [
        (
            "CEO's Golden Handgun",
            "Fires solid gold rounds.",
            70,
            0,
            "legendary",
            5,
            "one-handed",
            {"cha_bonus": 20, "int_bonus": 10},
        ),
        (
            "Director's Neural Whip",
            "Agony in fiber-optic form.",
            60,
            0,
            "legendary",
            15,
            "one-handed",
            {"int_bonus": 15, "cha_bonus": 10},
        ),
    ],
    "undergrid": [
        (
            "Source Code Fragment",
            "Pure data manifested as a weapon.",
            85,
            0,
            "legendary",
            15,
            "one-handed",
            {"int_bonus": 25},
        ),
        (
            "Malware Spike",
            "Infects reality itself.",
            75,
            0,
            "legendary",
            10,
            "one-handed",
            {"int_bonus": 20, "wil_bonus": 10},
        ),
    ],
    "neon": [
        (
            "Diva's Sonic Lash",
            "Vibrates at lethal frequencies.",
            50,
            0,
            "rare",
            10,
            "one-handed",
            {"cha_bonus": 12, "agi_bonus": 5},
        ),
        (
            "Club Owner's Cane",
            "Hidden blade, refined taste.",
            45,
            0,
            "rare",
            5,
            "one-handed",
            {"cha_bonus": 15, "wil_bonus": 5},
        ),
    ],
    "wastes": [
        (
            "Wasteland Harvester",
            "A brutal tool of survival.",
            65,
            0,
            "epic",
            -2,
            "two-handed",
            {"str_bonus": 10, "hea_bonus": 15},
        ),
        (
            "Scavenger's Crossbow",
            "Fires rusted rebar.",
            60,
            0,
            "epic",
            -5,
            "two-handed",
            {"agi_bonus": 12, "hea_bonus": 8},
        ),
    ],
    "nexus": [
        (
            "Nexus Core Blade",
            "Pulsing with infinite energy.",
            95,
            0,
            "legendary",
            12,
            "one-handed",
            {"int_bonus": 15, "wil_bonus": 15},
        ),
        (
            "Protocol Breaker",
            "A hammer that shatters firewalls.",
            90,
            0,
            "legendary",
            -5,
            "two-handed",
            {"str_bonus": 15, "int_bonus": 15},
        ),
    ],
    "undercity": [
        (
            "Shadow's Embrace",
            "A dagger that drinks light.",
            110,
            0,
            "legendary",
            20,
            "one-handed",
            {"agi_bonus": 25},
        ),
        (
            "Crypt-Keeper's Scythe",
            "Harvests the code of the dead.",
            105,
            0,
            "legendary",
            -10,
            "two-handed",
            {"wil_bonus": 30},
        ),
        (
            "Void Heart Amulet",
            "Pulsing with dark energy. Grants immense power.",
            0,
            0,
            "legendary",
            0,
            "one-handed",
            {
                "str_bonus": 20,
                "int_bonus": 20,
                "wil_bonus": 20,
                "agi_bonus": 20,
                "hea_bonus": 20,
                "cha_bonus": 20,
            },
        ),
        (
            "The Last Echo",
            "A gun that fires silenced screams.",
            130,
            0,
            "legendary",
            25,
            "one-handed",
            {"agi_bonus": 30, "int_bonus": 15},
        ),
        (
            "Oblivion's Gate",
            "A shield that devours light and hope.",
            0,
            0,
            "legendary",
            0,
            "one-handed",
            {"hea_bonus": 40, "str_bonus": 15, "wil_bonus": 15},
        ),
        (
            "Soul Reaver",
            "A blade that consumes the souls of the fallen.",
            150,
            0,
            "legendary",
            5,
            "two-handed",
            {"str_bonus": 35, "agi_bonus": 10},
        ),
    ],
}

ARMOR_TABLE = [
    ("Mesh Vest", "Basic kinetic protection.", 8, 150, "common", "leather", {"hea_bonus": 2}),
    (
        "Riot Shield",
        "Reinforced alloy shield.",
        20,
        1000,
        "uncommon",
        "heavy",
        {"str_bonus": 3, "hea_bonus": 5},
    ),
    ("Synth-Leathers", "Tough street fabric.", 4, 80, "common", "leather", {"agi_bonus": 2}),
    (
        "Titanium Exo-Frame",
        "Full body exoskeleton.",
        35,
        3000,
        "rare",
        "heavy",
        {"str_bonus": 10, "hea_bonus": 10},
    ),
    ("Ghost Cloak", "Active camouflage tech.", 15, 2500, "rare", "light", {"agi_bonus": 15}),
    (
        "Neural Shield",
        "Anti-hacking defense.",
        10,
        1500,
        "uncommon",
        "light",
        {"wil_bonus": 8, "int_bonus": 4},
    ),
    (
        "Adamantine Plate",
        "Near-indestructible armor.",
        50,
        8000,
        "epic",
        "heavy",
        {"hea_bonus": 20, "str_bonus": 5},
    ),
    (
        "Quantum Weave",
        "Shifts slightly out of reality.",
        25,
        6000,
        "rare",
        "light",
        {"agi_bonus": 10, "wil_bonus": 10},
    ),
    (
        "Reflective Trenchcoat",
        "Cool looks, decent protection.",
        12,
        1200,
        "uncommon",
        "leather",
        {"cha_bonus": 10, "agi_bonus": 2},
    ),
    (
        "Hazmat Suit",
        "Protects against toxic environments.",
        15,
        2000,
        "rare",
        "heavy",
        {"hea_bonus": 15, "wil_bonus": 5},
    ),
]

CONSUMABLE_TABLE = [
    ("Dog meat", "Fido tastes good.", 25, "common", 30),
    ("Health Stim", "Nanobot healing injection.", 25, "common", 30),
    ("Data Spike", "Buffer boost chip.", 60, "common", 0),
    ("Adrenaline Shot", "AGI boost injection.", 80, "uncommon", 0),
    ("Nano Repair Kit", "Full body repair unit.", 200, "rare", 100),
    ("Synth-Meat", "Synthetic protein bar.", 10, "common", 15),
    ("Neural Booster", "WIL enhancement chip.", 120, "uncommon", 0),
    ("Med-Kit", "Standard medical kit.", 75, "common", 50),
    ("Re-Gen Tank", "Portable healing vat.", 500, "rare", 250),
    ("Liquid Courage", "CHA boost drink.", 50, "common", 10),
]

MISC_TABLE = [
    ("Data Chip", "Encrypted data storage.", 0, "common"),
    ("Broken Cybernetic", "Salvaged cybernetic part.", 0, "common"),
    ("Access Keycard", "Opens locked doors.", 0, "uncommon"),
    ("Holographic Map", "Shows part of the grid.", 0, "rare"),
    ("Black Market Token", "Underground currency.", 0, "uncommon"),
    ("Golden Ticket", "Underground currency.", 0, "rare"),
    ("Strange Artifact", "Humming with ancient power.", 0, "epic"),
]

ZONE_TEMPLATES = [
    {
        "name": "The Slums",
        "desc": "Gritty rain-soaked streets and rusted pipes. Danger lurks in every alley.",
        "min_lvl": 1,
        "max_lvl": 3,
        "theme": "urban",
        "zone_id": "slums",
        "npc_prefix": "Street",
        "npc_types": ["drone", "gang", "scavenger", "thug"],
        "bosses": [
            {"name": "Rat King Vane", "desc": "A massive mutant sitting on a throne of scrap."},
            {
                "name": "Mama 'Doc' Voltage",
                "desc": "An illegal ripperdoc rogue with a power drill.",
            },
        ],
        "shop": "Black Market Stall",
        "room_names": [
            "Alley",
            "Street",
            "Block",
            "Corner",
            "Junction",
            "Dead End",
            "Roof",
            "Squat",
            "Drain",
        ],
        "room_details": [
            "Neon signs flicker above puddles of dirty water.",
            "Rusted fire escapes climb the walls like skeletal fingers.",
            "The smell of synthetic noodles hangs in the air.",
            "Graffiti covers every surface. Some of it glows.",
            "Trash fires provide the only warmth in the cold rain.",
            "Steam rises from a manhole cover, smelling of rot.",
            "A flickering terminal displays 'SYSTEM ERROR' in red.",
            "Discarded syringes crunch under your boots.",
            "A distant scream is cut short by a gunshot.",
        ],
    },
    {
        "name": "Industrial Zone",
        "desc": "Hissing steam, toxic fumes. The heart of the city's production.",
        "min_lvl": 3,
        "max_lvl": 6,
        "theme": "industrial",
        "zone_id": "industrial",
        "npc_prefix": "Factory",
        "npc_types": ["drone", "gang", "worker", "foreman"],
        "bosses": [
            {"name": "Unit 734-X", "desc": "A rogue heavy-lifting mech with blood-stained claws."},
            {"name": "Iron-Lung Igor", "desc": "A cyborg foreman who is more machine than man."},
        ],
        "shop": "Scrapyard Exchange",
        "room_names": [
            "Factory",
            "Warehouse",
            "Dock",
            "Plant",
            "Mill",
            "Forge",
            "Smelter",
            "Boiler",
            "Pipe-way",
        ],
        "room_details": [
            "Steam vents hiss from cracked pipes overhead.",
            "Conveyor belts carry unknown objects into darkness.",
            "The air tastes of ozone and burning metal.",
            "Heavy machinery drones echo through the chamber.",
            "Chemical runoff glows faintly in the shadows.",
            "Sparks fly from a malfunctioning welder arm.",
            "The floor vibrates with the rhythm of massive pistons.",
            "Soot covers everything, making the air hard to breathe.",
            "A pool of molten slag lights the room in a hellish orange.",
        ],
    },
    {
        "name": "Corporate Plaza",
        "desc": "Clean, sterile glass towers. Heavily guarded by the elite.",
        "min_lvl": 6,
        "max_lvl": 10,
        "theme": "corporate",
        "zone_id": "corporate",
        "npc_prefix": "Corp",
        "npc_types": ["corporate", "drone", "security", "agent"],
        "bosses": [
            {"name": "Executive Enforcer", "desc": "Security officer in custom power armor."},
            {
                "name": "VP of Acquisitions",
                "desc": "A suit-wearing shark with mono-molecular claws.",
            },
        ],
        "shop": "Corp Supply Depot",
        "room_names": [
            "Tower",
            "Office",
            "Lobby",
            "Suite",
            "Lab",
            "Boardroom",
            "Vault",
            "Heliport",
            "Archive",
        ],
        "room_details": [
            "Polished floors reflect the cold fluorescent lights.",
            "Security cameras track every movement.",
            "Holographic displays show stock tickers and news.",
            "The air is filtered and sterile. No warmth here.",
            "Glass walls reveal the city sprawling below.",
            "A receptionist bot stares blankly with synthetic eyes.",
            "Laser grids criss-cross the corridor ahead.",
            "The hum of invisible climate control is constant.",
            "Expensive synthetic plants line the corridors.",
        ],
    },
    {
        "name": "The Under-Grid",
        "desc": "Scrambled data-scapes and flickering holograms. A world of pure information.",
        "min_lvl": 8,
        "max_lvl": 12,
        "theme": "cyber",
        "zone_id": "undergrid",
        "npc_prefix": "Glitch",
        "npc_types": ["drone", "gang", "virus", "ghost"],
        "bosses": [
            {
                "name": "The Arch-Decompiler",
                "desc": "A semi-sentient AI virus taking physical form.",
            },
            {
                "name": "Root-Access Spectre",
                "desc": "Legendary hacker who uploaded his consciousness.",
            },
        ],
        "shop": "Data Market",
        "room_names": [
            "Node",
            "Port",
            "Terminal",
            "Gateway",
            "Matrix",
            "Buffer",
            "Stream",
            "Stack",
            "Heap",
        ],
        "room_details": [
            "Reality pixelates at the edges of vision.",
            "Data streams flow like rivers of light.",
            "Holographic ghosts flicker in and out of existence.",
            "The floor seems to shift between solid and code.",
            "Wireless signals buzz like electric insects.",
            "Fragments of deleted files float like autumn leaves.",
            "A waterfall of binary code pours from the ceiling.",
            "Visual artifacts trail behind your movements.",
            "The silence here is unnatural, purely digital.",
        ],
    },
    {
        "name": "Neon District",
        "desc": "Bright neon lights, crowded streets. Where the city never sleeps.",
        "min_lvl": 2,
        "max_lvl": 5,
        "theme": "neon",
        "zone_id": "neon",
        "npc_prefix": "Neon",
        "npc_types": ["gang", "drone", "bouncer", "pusher"],
        "bosses": [
            {"name": "Madam Pulse", "desc": "Gang leader with a deadly voice."},
            {"name": "Neon Dragon", "desc": "Yakuza boss with integrated holographic tattoos."},
        ],
        "shop": "Neon Bazaar",
        "room_names": [
            "Club",
            "Bar",
            "Lounge",
            "Arcade",
            "Stage",
            "Booth",
            "Rooftop",
            "Dancefloor",
            "VIP",
        ],
        "room_details": [
            "Neon lights paint everything in pink and blue.",
            "Bass-heavy music thumps through the walls.",
            "Crowds of augmented humans push past.",
            "Street vendors sell glowing street food.",
            "Prostitute bots line the alleyways.",
            "The floor is sticky with spilled synth-alcohol.",
            "Holographic dancers perform on high platforms.",
            "Confetti made of discarded data-strips falls from the ceiling.",
            "The smell of ozone and cheap perfume is overwhelming.",
        ],
    },
    {
        "name": "The Wastes",
        "desc": "Desolate wasteland outside city walls. Mutants and scavengers roam.",
        "min_lvl": 10,
        "max_lvl": 15,
        "theme": "wasteland",
        "zone_id": "wastes",
        "npc_prefix": "Waste",
        "npc_types": ["gang", "drone", "mutant", "raider"],
        "bosses": [
            {"name": "The Dust-Walker", "desc": "Survivor of acid rains for decades."},
            {"name": "War-Rig Warlord", "desc": "Massive mutant commanding a caravan of scrap."},
        ],
        "shop": None,
        "room_names": [
            "Ruin",
            "Camp",
            "Outpost",
            "Bunker",
            "Crater",
            "Scrapyard",
            "Dunes",
            "Bridge",
            "Settlement",
        ],
        "room_details": [
            "Acid rain pools in craters of fused glass.",
            "Rusted vehicles lie overturned in the dust.",
            "The wind howls through broken structures.",
            "Scavenger camps dot the horizon.",
            "Toxic clouds drift across the dead sky.",
            "Bone-dry remains of a cyber-beast lie half-buried.",
            "A derelict satellite dish points aimlessly at the stars.",
            "The radiation counter on your HUD clicks rhythmically.",
            "Sandstorms of ground-up silicon scour the landscape.",
        ],
    },
    {
        "name": "Data Nexus",
        "desc": "A massive server farm. The brain of the global network.",
        "min_lvl": 12,
        "max_lvl": 18,
        "theme": "cyber",
        "zone_id": "nexus",
        "npc_prefix": "Data",
        "npc_types": ["drone", "corporate", "guardian", "sentry"],
        "bosses": [
            {"name": "Protocol Prime", "desc": "Security program in a liquid-metal body."},
            {"name": "The Architect", "desc": "The sentient core of the city's infrastructure."},
        ],
        "shop": "Data Exchange",
        "room_names": [
            "Server",
            "Core",
            "Relay",
            "Hub",
            "Vault",
            "Uplink",
            "Processor",
            "Coolant",
            "Bus",
        ],
        "room_details": [
            "Rows of servers blink in perfect synchronization.",
            "Cooling fans create a constant drone.",
            "Fiber optic cables snake across the floor.",
            "The heat from the processors is intense.",
            "Holographic data visualizations float in mid-air.",
            "The hum of cooling systems is deafening.",
            "Super-cooled liquid nitrogen pipes frost over.",
            "Gravity feels slightly lower here, a side effect of the magnets.",
            "You feel the weight of billions of connections passing through you.",
        ],
    },
    {
        "name": "The Undercity",
        "desc": "Deep underground. Forgotten by the world above.",
        "min_lvl": 15,
        "max_lvl": 20,
        "theme": "underground",
        "zone_id": "undercity",
        "npc_prefix": "Shadow",
        "npc_types": ["gang", "drone", "cultist", "stalker"],
        "bosses": [
            {"name": "The Hollow One", "desc": "A creature of pure shadow and malicious code."},
            {"name": "Under-King Silas", "desc": "Corporate genius who built a sewer kingdom."},
            {"name": "The Lich Programmer", "desc": "Undead coder whose algorithms devour souls."},
            {
                "name": "Void Matriarch",
                "desc": "Queen of the forgotten depths, wielding ancient power.",
            },
            {"name": "The Null Entity", "desc": "An anti-existence being that erases matter."},
            {"name": "Corrupted Titan", "desc": "A colossal war machine gone rogue."},
        ],
        "shop": "Shadow Market",
        "room_names": [
            "Tunnel",
            "Cave",
            "Chamber",
            "Crypt",
            "Passage",
            "Sewer",
            "Catacomb",
            "Shrine",
            "Void",
        ],
        "room_details": [
            "Water drips from the cavern ceiling above.",
            "Bioluminescent fungi provide eerie light.",
            "Old subway tracks disappear into darkness.",
            "The walls are covered in ancient graffiti.",
            "Something moves in the shadows ahead.",
            "The air is thick with the smell of damp earth.",
            "Echoes of distant footsteps bounce off the walls.",
            "Ancient pre-fall machinery rusted into place.",
            "A smell of ozone and rot mixes in the still air.",
        ],
    },
]

NPC_ADJECTIVES = [
    "Abend",
    "Chromeo",
    "Neon",
    "Shadow",
    "Binary",
    "Cyber",
    "Dark",
    "Broken",
    "Glitch",
    "Hollow",
    "Iron",
    "Jacked",
    "Knotted",
    "Laser-brain",
    "Malware",
    "Neural",
    "Optic",
    "Phantom",
    "Quantum",
    "Rogue",
    "Static",
    "Turbo",
    "Void",
    "Wired",
    "Xeno",
    "Bumb",
    "Blazed",
    "Corroded",
    "Digital",
    "Flickering",
    "Ghostly",
    "Hyper",
    "Infused",
    "Jittery",
    "Kinetic",
    "Muffled",
    "Oily",
    "Pulsing",
    "Rad-sick",
    "Screaming",
    "Twisted",
]
NPC_NOUNS = [
    "Elite",
    "Hound",
    "Ghost",
    "Lousey",
    "Razor",
    "Berger",
    "Pulse",
    "Wraith",
    "Shade",
    "Spy",
    "Drone",
    "Bot",
    "Hunter",
    "Stalker",
    "Phantom",
    "Reaper",
    "Hacker",
    "Fixer",
    "Stupid",
    "Thug",
    "Sentinel",
    "Ward",
    "Derp",
    "Scout",
    "Flayer",
    "Dumb",
    "Breaker",
    "Crawler",
    "Drifter",
    "Enforcer",
    "Fragment",
    "Grendel",
    "Husk",
    "Icon",
    "Juggernaut",
    "Kill-joy",
    "Lurker",
]


class Command(BaseCommand):
    help = "Procedurally generate the Cyberpunk world"

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument("--rooms", type=int, default=350)
        parser.add_argument("--zones", type=int, default=16)

    def handle(self, *args, **kwargs):
        seed = kwargs.get("seed") or random.randint(1, 999999)
        num_rooms = kwargs.get("rooms")
        num_zones = min(kwargs.get("zones"), len(ZONE_TEMPLATES))
        random.seed(seed)

        self.stdout.write(f"Seed: {seed}")
        self.stdout.write("Purging existing grid data...")

        with transaction.atomic():
            NPC.objects.all().delete()
            Room.objects.all().delete()
            Item.objects.all().delete()

            items = self._create_items()
            zones = ZONE_TEMPLATES[:num_zones]
            rooms = self._create_rooms(zones, num_rooms)
            self._create_npcs(rooms, zones, items)

            hub = Room.objects.get(id=1)
            hub.refresh_from_db()
            if not hub.exits:
                self.stdout.write(self.style.WARNING("Hub isolation detected. Reconnecting..."))
                for zone_id in [z["zone_id"] for z in zones]:
                    entry = Room.objects.filter(zone=zone_id, name__icontains="Entry").first()
                    if entry:
                        if abs(entry.map_x) <= 2 and abs(entry.map_y) <= 2:
                            d_to_e = (
                                "east"
                                if entry.map_x > 0
                                else "west"
                                if entry.map_x < 0
                                else "south"
                                if entry.map_y > 0
                                else "north"
                            )
                            opp_dir = {
                                "east": "west",
                                "west": "east",
                                "south": "north",
                                "north": "south",
                            }[d_to_e]
                            self._connect_rooms(hub, entry, d_to_e, opp_dir)
                            break

            Player.objects.all().update(location=hub)

            # Create AI bots
            from django.core.management import call_command

            call_command("create_bots", count=12, reset=False)

            GameWorld.objects.all().delete()
            GameWorld.objects.create(
                seed=seed,
                total_rooms=Room.objects.count(),
                total_npcs=NPC.objects.count(),
                total_items=Item.objects.count(),
            )

        hub.refresh_from_db()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {Room.objects.count()} rooms, "
                f"{NPC.objects.count()} NPCs, {Item.objects.count()} items. "
                f"Hub exits: {list(hub.exits.keys())}."
            )
        )

    def _create_items(self):
        pool = []
        for name, desc, atk, pr, rarity, speed, subtype, bonuses in WEAPON_TABLE:
            pool.append(
                Item.objects.create(
                    name=name,
                    description=desc,
                    item_type="weapon",
                    attack_bonus=atk,
                    price=pr,
                    rarity=rarity,
                    speed_bonus=speed,
                    subtype=subtype,
                    **bonuses,
                )
            )
        for name, desc, dfn, pr, rarity, subtype, bonuses in ARMOR_TABLE:
            pool.append(
                Item.objects.create(
                    name=name,
                    description=desc,
                    item_type="armor",
                    defense_bonus=dfn,
                    price=pr,
                    rarity=rarity,
                    subtype=subtype,
                    **bonuses,
                )
            )
        for name, desc, pr, rarity, heal in CONSUMABLE_TABLE:
            pool.append(
                Item.objects.create(
                    name=name,
                    description=desc,
                    item_type="consumable",
                    price=pr,
                    rarity=rarity,
                    heal_amount=heal,
                )
            )
        for name, desc, pr, rarity, addic, bonuses in DRUG_TABLE:
            pool.append(
                Item.objects.create(
                    name=name,
                    description=desc,
                    item_type="drug",
                    price=pr,
                    rarity=rarity,
                    addiction_chance=addic,
                    **bonuses,
                )
            )
        for name, desc, pr, rarity in MISC_TABLE:
            pool.append(
                Item.objects.create(
                    name=name, description=desc, item_type="misc", price=pr, rarity=rarity
                )
            )
        return pool

    def _connect_rooms(self, r1, r2, d1, d2):
        r1.refresh_from_db()
        r2.refresh_from_db()
        exits1 = dict(r1.exits)
        exits1[d1] = r2.id
        r1.exits = exits1
        exits2 = dict(r2.exits)
        exits2[d2] = r1.id
        r2.exits = exits2
        r1.save()
        r2.save()

    def _create_rooms(self, zones, target_count):
        all_rooms = []
        opp = {"north": "south", "south": "north", "east": "west", "west": "east"}
        dir_coords = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}

        hub = Room.objects.create(
            id=1,
            name="The Neon Hub",
            description="Central nerve center. Terminals flicker with green text.",
            safe_zone=True,
            shop_name="Central Exchange",
            zone="hub",
            theme="urban",
            map_x=0,
            map_y=0,
        )
        hub.transporter_name = "Hub Transporter"
        hub.save()
        all_rooms.append(hub)

        rooms_per_zone = max(10, target_count // len(zones))
        occupied_coords = {(0, 0)}

        for zone in zones:
            zone_rooms = []
            start_room = random.choice(all_rooms)
            entry = None
            dirs = ["east", "west", "north", "south"]
            random.shuffle(dirs)
            for d in dirs:
                dx, dy = dir_coords[d]
                new_x, new_y = start_room.map_x + dx, start_room.map_y + dy
                if (new_x, new_y) not in occupied_coords:
                    entry = Room.objects.create(
                        name=f"{zone['name']} - Entry",
                        description=f"Entry to {zone['name']}. {zone['desc']}",
                        zone=zone["zone_id"],
                        theme=zone["theme"],
                        map_x=new_x,
                        map_y=new_y,
                    )
                    if zone.get("shop"):
                        entry.shop_name = zone["shop"]
                    entry.transporter_name = f"{zone['zone_id'].title()} Transporter"
                    entry.save()
                    self._connect_rooms(start_room, entry, d, opp[d])
                    occupied_coords.add((new_x, new_y))
                    break

            if not entry:
                continue
            zone_rooms.append(entry)
            prev = entry
            
            # Add a safe room with transporter in this zone
            # Safe room should be placed after entry, typically 2-3 rooms in
            safe_dirs = ["north", "south", "east", "west"]
            random.shuffle(safe_dirs)
            safe_room = None
            for d in safe_dirs:
                dx, dy = dir_coords[d]
                new_x, new_y = entry.map_x + dx, entry.map_y + dy
                if (new_x, new_y) not in occupied_coords:
                    safe_room = Room.objects.create(
                        name=f"{zone['name']} - Safe Zone",
                        description=f"A safe haven within {zone['name']}. {zone['desc']}",
                        zone=zone["zone_id"],
                        theme=zone["theme"],
                        map_x=new_x,
                        map_y=new_y,
                        safe_zone=True,
                    )
                    safe_room.save()
                    break
            
            if safe_room:
                zone_rooms.append(safe_room)
                prev = safe_room

            for i in range(1, rooms_per_zone):
                is_boss_room = i >= rooms_per_zone - 2
                rname = f"{zone['name']} - {random.choice(zone['room_names'])} {chr(65 + i)}"
                if is_boss_room:
                    rname = f"{zone['name']} - BOSS LAIR {chr(65 + i)}"
                detail = random.choice(zone["room_details"])
                rdesc = f"{zone['desc']} {detail}"

                new_room = None
                dirs = ["north", "south", "east", "west"]
                random.shuffle(dirs)
                for d in dirs:
                    dx, dy = dir_coords[d]
                    new_x, new_y = prev.map_x + dx, prev.map_y + dy
                    if (new_x, new_y) not in occupied_coords:
                        new_room = Room.objects.create(
                            name=rname,
                            description=rdesc,
                            zone=zone["zone_id"],
                            theme=zone["theme"],
                            map_x=new_x,
                            map_y=new_y,
                        )
                        occupied_coords.add((new_x, new_y))
                        self._connect_rooms(prev, new_room, d, opp[d])
                        break

                if new_room:
                    zone_rooms.append(new_room)
                    prev = new_room
                else:
                    prev = random.choice(zone_rooms)

                if len(zone_rooms) > 3 and random.random() > 0.4:
                    r1 = random.choice(zone_rooms)
                    r2 = random.choice(zone_rooms)
                    if r1 != r2:
                        for d in ["north", "south", "east", "west"]:
                            dx, dy = dir_coords[d]
                            if r1.map_x + dx == r2.map_x and r1.map_y + dy == r2.map_y:
                                if d not in r1.exits:
                                    self._connect_rooms(r1, r2, d, opp[d])
                                break
            all_rooms.extend(zone_rooms)

        # Populate shop inventories with weapons and items
        hub = Room.objects.get(id=1)
        if hub.shop_name:
            hub_weapons = random.sample(WEAPON_TABLE, min(4, len(WEAPON_TABLE)))
            for w_data in hub_weapons:
                name, desc, atk, pr, rarity, speed, subtype, bonuses = w_data
                weapon = Item.objects.create(
                    name=name,
                    description=desc,
                    item_type="weapon",
                    attack_bonus=atk,
                    price=pr,
                    rarity=rarity,
                    speed_bonus=speed,
                    subtype=subtype,
                    **bonuses,
                )
                hub.shop_inventory.add(weapon)
            hub_armor = random.sample(ARMOR_TABLE, min(3, len(ARMOR_TABLE)))
            for a_data in hub_armor:
                name, desc, dfn, pr, rarity, subtype, bonuses = a_data
                armor = Item.objects.create(
                    name=name,
                    description=desc,
                    item_type="armor",
                    defense_bonus=dfn,
                    price=pr,
                    rarity=rarity,
                    subtype=subtype,
                    **bonuses,
                )
                hub.shop_inventory.add(armor)
            hub_cons = random.sample(CONSUMABLE_TABLE, min(3, len(CONSUMABLE_TABLE)))
            for c_data in hub_cons:
                name, desc, pr, rarity, heal = c_data
                cons = Item.objects.create(
                    name=name,
                    description=desc,
                    item_type="consumable",
                    price=pr,
                    rarity=rarity,
                    heal_amount=heal,
                )
                hub.shop_inventory.add(cons)

        for zone in zones:
            if not zone.get("shop"):
                continue
            shop_rooms = [r for r in all_rooms if r.zone == zone["zone_id"] and r.shop_name]
            for shop_room in shop_rooms:
                num_weapons = random.randint(3, 5)
                zone_avg_lvl = (zone["min_lvl"] + zone["max_lvl"]) // 2
                price_max = zone_avg_lvl * 500
                avail_w = [w for w in WEAPON_TABLE if w[3] <= price_max] or WEAPON_TABLE
                selected_weapons = random.sample(avail_w, min(num_weapons, len(avail_w)))
                for w_data in selected_weapons:
                    name, desc, atk, pr, rarity, speed, subtype, bonuses = w_data
                    weapon = Item.objects.create(
                        name=name,
                        description=desc,
                        item_type="weapon",
                        attack_bonus=atk,
                        price=pr,
                        rarity=rarity,
                        speed_bonus=speed,
                        subtype=subtype,
                        **bonuses,
                    )
                    shop_room.shop_inventory.add(weapon)
                num_armor = random.randint(2, 3)
                selected_armor = random.sample(ARMOR_TABLE, min(num_armor, len(ARMOR_TABLE)))
                for a_data in selected_armor:
                    name, desc, dfn, pr, rarity, subtype, bonuses = a_data
                    armor = Item.objects.create(
                        name=name,
                        description=desc,
                        item_type="armor",
                        defense_bonus=dfn,
                        price=pr,
                        rarity=rarity,
                        subtype=subtype,
                        **bonuses,
                    )
                    shop_room.shop_inventory.add(armor)
                num_cons = random.randint(2, 3)
                sel_cons = random.sample(CONSUMABLE_TABLE, min(num_cons, len(CONSUMABLE_TABLE)))
                for c_data in sel_cons:
                    name, desc, pr, rarity, heal = c_data
                    cons = Item.objects.create(
                        name=name,
                        description=desc,
                        item_type="consumable",
                        price=pr,
                        rarity=rarity,
                        heal_amount=heal,
                    )
                    shop_room.shop_inventory.add(cons)
        return all_rooms

    def _create_npcs(self, rooms, zones, items):
        zone_map = {z["zone_id"]: z for z in zones}
        for room in rooms:
            if room.safe_zone:
                continue
            zone = zone_map.get(room.zone)
            if not zone:
                continue
            is_boss_room = "BOSS LAIR" in room.name
            if is_boss_room:
                lvl = zone["max_lvl"] + 2
                # Determine boss index from room letter: A=0, B=1, C=2, D=3, E=4, F=5
                boss_letter = (
                    room.name.split("BOSS LAIR ")[-1] if "BOSS LAIR " in room.name else "A"
                )
                boss_index = (ord(boss_letter) - ord("A")) % len(zone["bosses"])
                boss_info = zone["bosses"][boss_index]
                bw_list = BOSS_WEAPONS.get(room.zone, [])
                bw_index = boss_index % len(bw_list)
                bw_info = bw_list[bw_index]
                name, bdesc, batk, bpr, brarity, bspeed, bsub, bbonuses = bw_info
                unique_weapon = Item.objects.create(
                    name=name,
                    description=bdesc,
                    item_type="weapon",
                    attack_bonus=batk,
                    price=bpr,
                    rarity=brarity,
                    speed_bonus=bspeed,
                    subtype=bsub,
                    **bbonuses,
                )
                boss = NPC.objects.create(
                    name=boss_info["name"],
                    description=boss_info["desc"],
                    location=room,
                    attack=lvl * 8,
                    defense=lvl * 4,
                    hp=lvl * 50,
                    hp_max=lvl * 50,
                    lvl=lvl,
                    money_drop=lvl * 50,
                    exp_drop=lvl * 100,
                    aggressive=True,
                    npc_type="boss",
                )
                boss.drops.add(unique_weapon)
                # For undercity, add additional unique drops for extra bosses
                if room.zone == "undercity" and boss_index >= 2:
                    extra_drop = bw_list[(boss_index + 1) % len(bw_list)]
                    ename, edesc, eatk, epr, erarity, espeed, esub, ebonuses = extra_drop
                    extra_item = Item.objects.create(
                        name=ename,
                        description=edesc,
                        item_type="weapon",
                        attack_bonus=eatk,
                        price=epr,
                        rarity=erarity,
                        speed_bonus=espeed,
                        subtype=esub,
                        **ebonuses,
                    )
                    boss.drops.add(extra_item)
                    boss.money_drop = lvl * 100
                    boss.exp_drop = lvl * 200
                    boss.hp = lvl * 80
                    boss.hp_max = lvl * 80
                    boss.save()
                continue
            prob = 0.5 if "Entry" not in room.name else 0.2
            if random.random() < prob:
                num_npcs = random.randint(1, 3)
                for _ in range(num_npcs):
                    lvl = random.randint(zone["min_lvl"], zone["max_lvl"])
                    npc_type = random.choice(zone["npc_types"])
                    adj, noun = random.choice(NPC_ADJECTIVES), random.choice(NPC_NOUNS)
                    npc = NPC.objects.create(
                        name=f"{zone['npc_prefix']} {adj} {noun}",
                        description=f"A hostile {npc_type} patrolling {zone['name']}.",
                        location=room,
                        attack=lvl * 5,
                        defense=lvl * 2,
                        hp=lvl * 20,
                        hp_max=lvl * 20,
                        lvl=lvl,
                        money_drop=lvl * 10,
                        exp_drop=lvl * 15,
                        aggressive=(lvl > 1),
                        npc_type=npc_type,
                    )
                    # Give NPCs drops more often so bots and players can collect items
                    if random.random() > 0.76:
                        npc.drops.add(random.choice(items))
                    # Give NPCs a weapon sometimes
                    if random.random() > 0.84:
                        weapon = random.choice([i for i in items if i.item_type == "weapon"])
                        npc.weapon = weapon
                        npc.save()
