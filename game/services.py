import json
import random
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
import django.db.models as models

# In-game item data (single source of truth, shared with init_game world gen)
from game.management.commands.init_game import (
    WEAPON_TABLE,
    ARMOR_TABLE,
    CONSUMABLE_TABLE,
    DRUG_TABLE,
    MISC_TABLE,
)

from .models import (
    Player,
    Room,
    NPC,
    Item,
    InventoryItem,
    ChatMessage,
    ProceduralWeaponSpawn,
    Party,
    PartyMembership,
)

# Race Special Characteristics
RACE_CHARACTERISTICS = {
    "Cyborg": "Cybernetic Resilience: +10% resistance to debuffs and status effects.",
    "Bio-hacked": "Adrenal Efficiency: Natural healing 20% faster, reduced addiction.",
    "Android": "Systematic Mind: +15% mana efficiency, immune to mind-affecting effects.",
    "Mutant": "Adaptive Biology: Stats can exceed normal caps by 5 points.",
    "Human": "Versatile Potential: Gains 1.5x stat points on level up.",
    "Void-Walker": "Phase Shift: Can dodge 10% of incoming attacks.",
    "Synth-Soul": "Digital Presence: +20% stealth effectiveness, reduced physical stats.",
    "Orc": "Overclocked: +1 extra attack per combat round.",
    "Elf": "Ancient Grace: +10% crit chance, natural affinity for precision.",
    "Goblin": "Street Cunning: +15% chance to find extra loot from NPCs.",
}


# Class Ability Definitions - Learned every 5 levels until Lv 30
# Format: (level, ability_name, acronym, description)
CLASS_MOVES = {
    "Street Samurai": [
        (1, "blade", "BLD", "Precise physical strike. Scales with STR/ATK."),
        (5, "oni_strike", "ONI", "Fire-elemental strike. Scales with STR/ATK."),
        (10, "zansetsu", "ZAN", "High-critical physical strike. Scales with STR/ATK."),
        (
            15,
            "mirage",
            "MIR",
            "Technological displacement. Boosts Defense significantly based on AGI.",
        ),
        (20, "whirlwind", "WHL", "Multiple physical strikes. Scales with STR/ATK."),
        (25, "dragon_lunge", "DRG", "Heavy fire-elemental pierce. Scales with STR/ATK."),
        (30, "omnislash", "OMN", "Ultimate physical combo. Scales with STR/ATK."),
        (35, "ronin_wrath", "RNW", "Triple masterful strikes. Scales with STR/ATK."),
        (40, "blade_dance", "BDN", "Five-hit bladed flurry. Scales with STR/ATK."),
        (
            45,
            "ghost_edge",
            "GHT",
            "Phase-blade ignores defense entirely. Scales with STR/ATK.",
        ),
        (
            50,
            "shatter_soul",
            "SHS",
            "Ultimate fire strike that drains life. Scales with STR/ATK.",
        ),
    ],
    "Netrunner": [
        (1, "hack", "HCK", "System water/ice damage. Scales with INT."),
        (5, "overload", "OVR", "High air damage pulse. Scales with INT."),
        (10, "synapse_burn", "SYN", "Burn target memory (Fire). Scales with INT."),
        (15, "logic_bomb", "LGC", "Heavy air system corruption. Scales with INT."),
        (20, "blackout", "BKO", "Neural interference. Lowers target stats based on INT."),
        (25, "databreach", "DBR", "Siphon credits and deal water damage. Scales with INT."),
        (30, "zero_day", "ZER", "Critical system failure damage. Scales with INT."),
        (35, "ice_wall", "ICW", "Water barrier. Damage plus Defense boost based on INT."),
        (40, "daemon_host", "DMH", "Possess target: air damage and mana siphon. Scales with INT."),
        (45, "quantum_fracture", "QTF", "Twin quantum lances. Heavy air damage. Scales with INT."),
        (
            50,
            "neural_cascade",
            "NCS",
            "Ultimate triple ice cascade that shatters defense. Scales with INT.",
        ),
    ],
    "Techie": [
        (1, "calibrate", "CAL", "Drone earth damage. Scales with INT/AGI."),
        (5, "turret", "TUR", "Automated physical fire. Scales with INT/ATK."),
        (10, "overclock", "OVC", "System boost. Increases Attack and Speed based on INT."),
        (15, "nanobot_swarm", "NAN", "Healing and earth damage. Scales with INT."),
        (20, "plasma_arc", "PLA", "Heavy fire damage. Scales with INT."),
        (25, "tesla_coil", "TES", "Stun and air damage. Scales with INT."),
        (30, "singularity", "SIN", "Ultimate gravity collapse (Earth). Scales with INT."),
        (35, "drone_legion", "DLG", "Three drone strikes. Scales with INT/ATK."),
        (40, "emp_burst", "EMP", "Air pulse that scrambles target attack. Scales with INT."),
        (45, "rail_gun", "RGU", "Magnetic slug pierces all defense. Scales with INT/ATK."),
        (
            50,
            "orbital_laser",
            "OLR",
            "Ultimate orbital fire lance from the skies. Scales with INT.",
        ),
    ],
    "Medie": [
        (1, "patch", "PTC", "Biological repair. Heals based on INT."),
        (5, "detox", "DTX", "Cleanse toxins. Heals and clears addiction."),
        (10, "adrenaline", "ADR", "Boost stats. Increases Attack and Defense based on HEA."),
        (15, "biocortical_shock", "BIO", "Water damage to nervous system. Scales with INT/HEA."),
        (20, "regeneration", "REG", "Continuous cellular repair. Large heal based on HEA."),
        (25, "viral_burst", "VIR", "Heavy rot damage over time. Scales with HEA/INT."),
        (
            30,
            "nanomachine_army",
            "NMA",
            "Ultimate survival boost. Massive HP recovery based on HEA.",
        ),
        (35, "triage", "TRG", "Field surgery. Large heal and mana restore. Scales with HEA/INT."),
        (40, "immune_boost", "IMB", "Boost Attack and Defense. Scales with HEA."),
        (45, "leech_field", "LCF", "Drain target life to mend yourself. Scales with HEA/INT."),
        (
            50,
            "phoenix_protocol",
            "PHX",
            "Ultimate revival matrix. Full HP recovery and toxin purge.",
        ),
    ],
    "Fixer": [
        (1, "scheme", "SCH", "Drain credits from target. Scales with CHA."),
        (5, "call_in", "CAL", "Air-strike damage. Scales with CHA/ATK."),
        (10, "bribe", "BRI", "Lower target defense with credits. Effectiveness based on CHA."),
        (15, "contract_kill", "CTK", "High physical damage assassination. Scales with CHA/ATK."),
        (20, "market_crash", "MKT", "Siphon massive credits. Scales with CHA."),
        (25, "reinforcements", "REF", "Summon allies for extra hits. Scales with CHA/ATK."),
        (30, "hostile_takeover", "HTK", "Ultimate credit and soul drain. Scales with CHA."),
        (
            35,
            "insurance_fraud",
            "IFR",
            "Staged disaster pays out damage and credits. Scales with CHA.",
        ),
        (
            40,
            "dirty_cop",
            "DCP",
            "Pay off security to crush target defense. Scales with CHA.",
        ),
        (45, "union_strike", "UNS", "Organized double assault. Scales with CHA/ATK."),
        (
            50,
            "corporate_war",
            "CWR",
            "Ultimate hostile buyout. Massive damage and credit extraction. Scales with CHA.",
        ),
    ],
    "Thief": [
        (1, "backstab", "BSB", "Critical strike from shadows. Scales with AGI/ATK."),
        (5, "stealth", "STL", "Become hidden. Success chance scales with AGI."),
        (10, "poison_dart", "PSN", "Earth damage over time. Scales with AGI/INT."),
        (15, "smoke_bomb", "SMB", "Defense boost and escape. Scales with AGI."),
        (20, "shadow_strike", "SHD", "Critical hit from stealth. Scales with AGI/ATK."),
        (25, "assassinate", "ASN", "Execute target with low HP. Scales with AGI/ATK."),
        (30, "death_mark", "DMK", "Ultimate physical assassination. Scales with AGI/ATK."),
        (35, "veil_step", "VLS", "Vanish mid-strike and stay hidden. Scales with AGI."),
        (
            40,
            "garrote",
            "GRT",
            "Silent kill technique. Extra lethal from stealth. Scales with AGI/ATK.",
        ),
        (45, "shadow_clone", "SHC", "Three shadow duplicates strike. Scales with AGI/ATK."),
        (
            50,
            "void_theft",
            "VDT",
            "Ultimate larceny: massive damage, stolen credits, and vanish. Scales with AGI/CHA.",
        ),
    ],
    "Heavy": [
        (1, "smash", "SMH", "Heavy physical damage. Scales with STR."),
        (5, "taunt", "TNT", "Focus enemy attention. Lowers enemy stats based on HEA."),
        (10, "iron_skin", "IRN", "Harden armor. Boosts Defense based on HEA."),
        (15, "seismic_toss", "SMT", "Heavy earth damage. Scales with STR/HEA."),
        (20, "juggernaut", "JUG", "Boost Attack and Defense based on HEA/STR."),
        (25, "avalanche", "AVL", "Massive earth AOE. Scales with STR/HEA."),
        (30, "earthshaker", "EQK", "Ultimate earth blow. Scales with STR/HEA."),
        (35, "bulwark", "BLK", "Plant the line. Massive Defense boost. Scales with HEA/STR."),
        (40, "wrecking_ball", "WKB", "Swing with brutal momentum. Scales with STR."),
        (
            45,
            "berserker_rage",
            "BGR",
            "Trade blood for fury. Attack surge at HP cost. Scales with STR.",
        ),
        (
            50,
            "titan_fall",
            "TTF",
            "Ultimate seismic collapse. Double earth devastation. Scales with STR/HEA.",
        ),
    ],
    "Psycher": [
        (1, "mind_bolt", "MND", "Intelligence-based energy damage. Scales with INT."),
        (5, "soul_drain", "SDL", "Damage target, heal self. Scales with INT."),
        (10, "psionic_shield", "PSI", "Psychic barrier. Boosts Defense based on INT."),
        (15, "pyrokinesis", "PYR", "Massive fire mind damage. Scales with INT."),
        (20, "telekinesis", "TEK", "High physical mind damage. Scales with INT."),
        (25, "mind_control", "MNC", "Target strikes themselves. Effectiveness based on INT."),
        (30, "soul_annihilation", "SOL", "Ultimate psychic collapse. Scales with INT."),
        (35, "psychic_crush", "PCR", "Crush the target's mind. Scales with INT."),
        (40, "astral_veil", "ASV", "Project astrally: hide and harden defense. Scales with INT."),
        (45, "eidolon_swarm", "EID", "Summon three psychic constructs. Scales with INT."),
        (
            50,
            "mind_shatter",
            "MDS",
            "Ultimate psychic detonation. Ignores armor. Scales with INT.",
        ),
    ],
    "Warlock": [
        (1, "curse", "CRS", "Weaken target. Lowers ATK/DEF based on INT."),
        (5, "chaos_bolt", "CHB", "Random high-energy surge. Scales with INT."),
        (10, "blood_pact", "BLP", "Sacrifice HP for massive damage. Scales with INT/Current HP."),
        (15, "shadow_bolt", "SDB", "Dark water damage. Scales with INT."),
        (20, "necrosis", "NEC", "High rot damage over time. Scales with INT."),
        (25, "demonic_tether", "DMT", "Siphon HP and Mana. Scales with INT."),
        (30, "armageddon", "ARM", "Ultimate chaotic destruction. Scales with INT."),
        (35, "hex_mark", "HXM", "Brand target: attack and defense rot away. Scales with INT."),
        (40, "plague_wave", "PLW", "Corrosive rot tide. Scales with INT."),
        (45, "infernal_pact", "IFP", "Pay in blood for massive hellfire. Scales with INT/HP."),
        (
            50,
            "abyssal_rift",
            "ABR",
            "Ultimate void rift. Dark water devastation that feeds the caster. Scales with INT.",
        ),
    ],
    "Priest": [
        (1, "heal", "HEL", "Holy restoration. Heals based on WIL."),
        (5, "bless", "BLS", "Soul fortification. Boosts ATK/DEF based on WIL."),
        (10, "purify", "PUR", "Clear addiction and heal. Scales with WIL."),
        (15, "holy_fire", "HLF", "Fire damage to the wicked. Scales with WIL."),
        (20, "divine_shield", "DSH", "Temporary invulnerability. Large DEF boost based on WIL."),
        (25, "judgment", "JUD", "Air damage based on Karma and WIL."),
        (
            30,
            "heavenly_ascent",
            "HVA",
            "Ultimate divine power. Massive heal and damage based on WIL.",
        ),
        (35, "smite", "SMI", "Pillar of holy fire. Scales with WIL."),
        (40, "sanctuary", "SNC", "Consecrated ground: Defense boost and heal. Scales with WIL."),
        (45, "resurrect", "RSR", "Full system restoration and toxin purge. Scales with WIL."),
        (
            50,
            "rapture",
            "RAP",
            "Ultimate ascension. Heals to full and burns the wicked. Scales with WIL.",
        ),
    ],
    "Trickster": [
        (1, "bamboozle", "BAM", "Confuse target. Lowers DEF based on CHA/LUCK."),
        (5, "sneak", "SNK", "Attempt to hide. Chance based on AGI/CHA."),
        (10, "jackpot", "JAK", "Massive damage or credits. Scales with CHA."),
        (15, "sleight_of_hand", "SOH", "Steal item or credits. Success based on CHA."),
        (20, "mirror_image", "MIR", "Illusionary defense. Large DEF boost based on CHA."),
        (25, "wild_card", "WCD", "Random effect. Scaling based on primary stats."),
        (30, "royal_flush", "RFL", "Ultimate luck-based destruction. Scales with CHA."),
        (35, "loaded_dice", "LDD", "Weighted odds. Random heavy damage. Scales with CHA."),
        (40, "puppet_string", "PPS", "Force target to strike itself. Scales with CHA."),
        (45, "coin_flip", "CNF", "Fifty-fifty: brutal damage or full mend. Scales with CHA."),
        (
            50,
            "chaos_theory",
            "CHT",
            "Ultimate cascade of absurd fortune. Wildly random devastation. Scales with CHA.",
        ),
    ],
    "Jade Dragon": [
        (
            1,
            "palm_strike",
            "PLM",
            "Open-palm chi strike. Scales with AGI/STR. Unarmed bonus when no weapon equipped.",
        ),
        (5, "crane_kick", "CRK", "Soaring aerial kick. Scales with AGI/STR."),
        (10, "iron_palm", "IRP", "Reinforced chi palm. Boosts Defense based on AGI."),
        (15, "tiger_claw", "TGR", "Rending claw strikes. Scales with AGI/STR."),
        (20, "dragon_kick", "DGK", "Explosive spinning kick. Scales with AGI/STR."),
        (25, "chi_burst", "CHI", "Internal energy blast. Air damage. Scales with AGI/INT."),
        (
            30,
            "jade_ascension",
            "JDA",
            "Ultimate martial trance. Massive combo. Scales with AGI/STR.",
        ),
        (35, "phoenix_wing", "PHW", "Aerial fire strike on rising wings. Scales with AGI/STR."),
        (40, "thousand_hands", "TSH", "Barrage of chi palms. Scales with AGI/STR."),
        (
            45,
            "serpent_coil",
            "SRC",
            "Constrict and strike: lowers target defense. Scales with AGI.",
        ),
        (
            50,
            "dragon_god_fist",
            "DGF",
            "Ultimate five-hit dragon combo. Scales with AGI/STR.",
        ),
    ],
    "Ninja": [
        (1, "kunai_throw", "KUN", "Swift thrown blade. High crit from stealth."),
        (5, "stealth", "STL", "Become hidden. Success chance scales with AGI."),
        (10, "shadow_step", "SWP", "Teleport behind target for backstab bonus."),
        (15, "chakra_dart", "CHD", "Multiple chakra-infused projectiles."),
        (20, "phantom_sweep", "PHS", "Area attack that hits all enemies."),
        (25, "throw", "THR", "Destroy weapon to deal 3x its damage to target."),
        (30, "sharingan", "SHR", "Copy target stats and strike with perfect accuracy."),
        (35, "smoke_screen", "SMS", "Vanish in vapor and harden defense. Scales with AGI."),
        (40, "thousand_blades", "THB", "Four-blade assassination flurry. Scales with AGI/ATK."),
        (
            45,
            "forbidden_jutsu",
            "FRJ",
            "Forbidden technique: pay blood for lethal damage. Scales with AGI.",
        ),
        (
            50,
            "tsukuyomi",
            "TSK",
            "Ultimate genjutsu: copy stats, ignore defense, strike true. Scales with AGI.",
        ),
    ],
}

# Gear Restrictions
GEAR_LIMITS = {
    "Thief": {"armor": ["leather"], "weapon": ["one-handed"]},
    "Netrunner": {"armor": ["leather", "light"], "weapon": ["one-handed"]},
    "Trickster": {"armor": ["leather", "light"], "weapon": ["one-handed"]},
    "Heavy": {
        "armor": ["leather", "light", "medium", "heavy"],
        "weapon": ["one-handed", "two-handed"],
    },
    "Street Samurai": {
        "armor": ["leather", "light", "medium", "heavy"],
        "weapon": ["one-handed", "two-handed"],
    },
    "Jade Dragon": {"armor": ["light"], "weapon": ["jade"]},
    "Ninja": {"armor": ["light"], "weapon": ["ninja"]},
    "Medie": {"armor": ["leather", "light"], "weapon": ["one-handed"]},
    "Fixer": {"armor": ["leather", "light"], "weapon": ["one-handed"]},
    "Psycher": {"armor": ["leather", "light"], "weapon": ["one-handed"]},
    "Warlock": {"armor": ["leather", "light"], "weapon": ["one-handed"]},
    "Priest": {"armor": ["leather", "light"], "weapon": ["one-handed"]},
}


def get_reputation_title(karma):
    if karma >= 80:
        return "Saint"
    if karma >= 50:
        return "Paragon"
    if karma >= 20:
        return "Lawful"
    if karma > -20:
        return "Neutral"
    if karma > -50:
        return "Renegade"
    if karma > -80:
        return "Outlaw"
    return "Utter Villain"


def get_attribute_desc(stat_name, val):
    if stat_name == "str":
        if val < 8:
            return "feeble and scrawny"
        if val < 13:
            return "of average build"
        if val < 18:
            return "visibly toned and athletic"
        if val < 25:
            return "powerful and heavily muscled"
        return "a titan of pure physical power"
    if stat_name == "agi":
        if val < 8:
            return "clumsy and awkward"
        if val < 13:
            return "steady on their feet"
        if val < 18:
            return "lithe and graceful"
        if val < 25:
            return "incredibly swift and precise"
        return "moving with supernatural speed"
    if stat_name == "int":
        if val < 8:
            return "slow-witted"
        if val < 13:
            return "of average intelligence"
        if val < 18:
            return "sharp and analytical"
        if val < 25:
            return "brilliant and calculating"
        return "possessing a mind like a supercomputer"
    if stat_name == "wil":
        if val < 8:
            return "easily swayed"
        if val < 13:
            return "of average resolve"
        if val < 18:
            return "determined and focused"
        if val < 25:
            return "unshakeable in their will"
        return "radiating an aura of absolute mental dominance"
    if stat_name == "cha":
        if val < 8:
            return "unpleasant and abrasive"
        if val < 13:
            return "plain and unremarkable"
        if val < 18:
            return "charming and charismatic"
        if val < 25:
            return "strikingly beautiful"
        return "possessing an almost divine, otherworldly beauty"
    if stat_name == "hea":
        if val < 8:
            return "sickly and fragile"
        if val < 13:
            return "reasonably healthy"
        if val < 18:
            return "tough and resilient"
        if val < 25:
            return "exceptionally hardy"
        return "virtually indestructible"
    return "average"


def get_combat_desc(atk, dfn, is_self=False):
    pronoun = "You" if is_self else "They"
    if atk < 15:
        atk_desc = "minimal combat capability"
    elif atk < 30:
        atk_desc = "competent offensive skills"
    elif atk < 60:
        atk_desc = "deadly precision"
    elif atk < 100:
        atk_desc = "devastating power"
    else:
        atk_desc = "unstoppable destructive force"

    if dfn < 10:
        dfn_desc = "fragile defenses"
    elif dfn < 25:
        dfn_desc = "solid protection"
    elif dfn < 50:
        dfn_desc = "impenetrable shielding"
    else:
        dfn_desc = "the resilience of a fortress"

    return f"{pronoun} exhibit {atk_desc} and {dfn_desc}."


def get_threat_desc(lvl):
    if lvl < 5:
        return "minimal threat"
    if lvl < 10:
        return "moderate threat"
    if lvl < 15:
        return "significant threat"
    if lvl < 25:
        return "lethal threat"
    return "apocalyptic threat"


def get_rarity_desc(rarity):
    return rarity.upper()


def get_item_bonus_desc(bonus):
    if bonus <= 0:
        return "no noticeable"
    if bonus < 5:
        return "slight"
    if bonus < 10:
        return "modest"
    if bonus < 20:
        return "significant"
    return "massive"


def get_status_str(player):
    rep = get_reputation_title(player.karma)
    status = (
        f"HP:{player.hp}/{player.hp_max}|MA:{player.mana}/{player.mana_max}|"
        f"LV:{player.lvl}|CR:{player.money}|[{rep}]"
    )
    if player.stat_points > 0:
        status += f"|STATS:{player.stat_points}"
    if player.addiction_points > 0:
        status += f"|ADDICT:{player.addiction_points}%"
    return status


def _fmt_table(rows):
    """Format a list of (name, desc, extra) tuples into aligned help lines."""
    lines = []
    for name, desc, extra in rows:
        lines.append(f"  {name:<20} {desc}{extra}")
    return lines


def get_help(player):
    room = player.location
    sb = ["\n=== GRID COMMAND PROTOCOLS ===\n"]

    # ── Movement ──
    sb.append("MOVEMENT / NAVIGATION")
    sb.append("  N/NORTH, S/SOUTH, E/EAST, W/WEST   : Move to an adjacent sector")
    sb.append("  L/LOOK                             : Describe the current sector")
    sb.append("  L/LOOK <target>                    : Examine an NPC, item, or yourself (LOOK ME)")
    if room.exits:
        sb.append(f"  Exits here: {', '.join(k.upper() for k in room.exits.keys())}")
    sb.append("")

    # ── Observation ──
    sb.append("OBSERVATION")
    sb.append("  WHO      : List every active terminal node (players & bots) and their levels")
    sb.append("  TOP      : Display the top 25 adventurers by level/EXP")
    sb.append("  WALL     : View the Wall of Death (players with the most deaths)")
    sb.append("  ST/STATUS/STATS   : Your detailed profile (stats, gear, level, EXP, karma)")
    sb.append("  I/INVENTORY  : List equipped and carried hardware")
    sb.append("")

    # ── Combat ──
    sb.append("COMBAT")
    sb.append("  A/KILL <target>   : Regular attack (one combat round) against an NPC or player")
    sb.append("  AA <target>       : Auto-attack (repeats every round until target dies/flees)")
    sb.append("  DISENGAGE         : Stop combat and clear your current target")
    sb.append("  <ability name>    : Use a class special move (e.g. BLADE, HACK, ZANS).")
    sb.append("                    Type HELP to see the abilities your class has unlocked.")
    sb.append("  STEAL <target>    : Attempt to steal credits from a player")
    if not room.safe_zone:
        sb.append("  (You are in a hostile sector - you and NPCs can engage in combat.)")
    else:
        sb.append("  (This is a safe zone - violence is prohibited here.)")
    sb.append("")

    # ── Inventory / Gear ──
    sb.append("INVENTORY & GEAR")
    sb.append("  G/GET <item>      : Pick up an item lying in the current sector")
    sb.append("  DROP <item>       : Discard an item in the current sector")
    sb.append("  EQUIP <item>      : Equip or unequip a weapon or piece of armor")
    sb.append("  USE <item>        : Consume a consumable, drug, or activate a scroll")
    if InventoryItem.objects.filter(player=player).exists():
        sb.append("  You currently have equipped/carried hardware - use EQUIP/DROP/USE on it.")
    sb.append("")

    # ── Economy ──
    sb.append("ECONOMY")
    sb.append("  LIST/LI           : View the current sector shop's catalog")
    sb.append("  BUY <item>        : Purchase an item from the shop")
    sb.append("  SELL <item>       : Sell an item to the shop for credits")
    sb.append("  SELLALL           : Sell all unequipped carried hardware")
    dealer = NPC.objects.filter(location=room, npc_type="dealer", hp__gt=0).first()
    if dealer:
        sb.append(f"  SELL <drug> to {dealer.name} : Illegal drug trade with the local dealer")
    if room.shop_name:
        sb.append(f"  Shop here: {room.shop_name}")
    sb.append("")

    # ── Communication ──
    sb.append("COMMUNICATION")
    sb.append("  SAY <msg>         : Send a message to everyone in your current sector")
    sb.append("  BROADCAST <msg>   : Send a message to the entire world")
    sb.append("")

    # ── Progression ──
    sb.append("PROGRESSION")
    sb.append("  TRAIN <stat>      : Spend a stat point on STR, INT, WIL, AGI, HEA, or CHA")
    sb.append("  REST              : Recover HP while resting (broken by movement/combat/full HP)")
    sb.append("  EXIT              : Log out and disconnect from the grid")
    sb.append("  HELP / ?          : Display this manual")
    sb.append("  GUIDE             : Open the full User Guide in your browser")
    sb.append("")

    # ── Grid mechanics ──
    sb.append("GRID MECHANICS")
    sb.append("  AFK TELEPORT : Idling 2+ minutes in the Hub relocates you to a level-")
    sb.append("                 matched sector automatically.")
    sb.append("  IDLE KICK    : 1 hour of total inactivity disconnects you. You lose NOTHING")
    sb.append("                 (credits, EXP, and gear are all kept).")
    sb.append("  LEVEL UP     : Defeat NPCs/players to earn EXP. Every level grants +1 stat")
    sb.append("                 point (use TRAIN to spend it). Humans gain 1.5x stat points.")
    sb.append("  KARMA        : Alignment from -100 (Villain) to +100 (Saint). Killing evil")
    sb.append("                 NPCs raises karma; attacking players lowers it. Karma affects")
    sb.append("                 NPC aggression and some abilities.")
    sb.append("  STEALTH      : Hide in shadows to avoid detection and set up backstabs.")
    sb.append("  BOTS         : AI-controlled players wander the grid, fight, and level up")
    sb.append("                 just like humans - they appear with a (bot) marker on WHO.")
    sb.append("")

    # ── Races ──
    sb.append("=== RACES (AUGMENTATION PATHS) ===")
    sb.append("Each race grants stat modifiers and a unique Race Trait (picked at creation):")
    race_rows = [
        ("Human", "CHA+10 WIL+5 STR-5 HEA-5", "Versatile Potential: 1.5x stat points per level."),
        ("Elf", "AGI+8 WIL+4 HEA-5", "Ancient Grace: +10% critical hit chance."),
        ("Goblin", "CHA+10 AGI+5 STR-8", "Street Cunning: +15% chance for extra loot from NPCs."),
        ("Mutant", "Random (+7/-3)", "Adaptive Biology: Stats can exceed normal caps by 5."),
        ("Cyborg", "STR+5 HEA+2 AGI-2 INT+2", "Cybernetic Resilience: +10% resistance to debuffs."),
        ("Android", "INT+8 WIL+2 CHA-5 HEA-2", "Systematic Mind: +15% mana efficiency."),
        ("Bio-hacked", "HEA+5 STR+2 CHA-2", "Adrenal Efficiency: 20% faster healing."),
        ("Void-Walker", "WIL+12 AGI+5 STR-8 HEA-4", "Phase Shift: 10% chance to dodge any attack."),
        ("Synth-Soul", "INT+15 CHA-10", "Digital Presence: +20% stealth effectiveness."),
        ("Orc", "AGI+10 INT-10 CHA-5", "Overclocked: +1 extra attack per combat round."),
    ]
    for name, mods, trait in race_rows:
        sb.append(f"  {name:<14} {mods:<26} | {trait}")
    sb.append("")

    # ── Stats ──
    sb.append("=== STAT REFERENCE ===")
    sb.append("  STR  Strength   - Physical power, raises Attack and carrying capacity.")
    sb.append("  INT  Intelligence - Mana pool and ability damage (tech/psychic classes).")
    sb.append("  WIL  Willpower  - Mana regeneration and mental defense.")
    sb.append("  AGI  Agility    - Defense, critical hit chance, and turn order.")
    sb.append("  HEA  Health     - Maximum HP and healing effectiveness.")
    sb.append("  CHA  Charisma   - Social interactions, party influence, shop prices.")
    sb.append("")

    # ── Classes ──
    sb.append("=== CLASSES & ABILITIES ===")
    sb.append("Abilities are learned at the listed level and used by typing their name or acronym.")
    sb.append("Only abilities your character is high enough level to know are shown below.")
    moves = CLASS_MOVES.get(player.game_class, [])
    shown_any = False
    for lvl, name, acronym, desc in moves:
        if player.lvl >= lvl:
            sb.append(f"  {name.upper():14} ({acronym:<4}) Lv{lvl:<3} - {desc}")
            shown_any = True
    if not shown_any:
        sb.append("  (No abilities unlocked yet - your first ability is learned at level 1.)")
    sb.append("")
    sb.append("CLASS OVERVIEW:")
    class_overview = [
        ("Street Samurai", "Melee physical fighter - blade and fire strikes."),
        ("Netrunner", "Tech caster - water/ice, air, and system-corruption damage."),
        ("Techie", "Drone and gadget specialist - summons and tech damage."),
        ("Medie", "Healer - restores HP and removes afflictions."),
        ("Fixer", "Social operative - credits, haggling, and buffs."),
        ("Thief", "Stealthy skulker - backstab and extra loot."),
        ("Heavy", "Tank - high HP, heavy weapons, armor focus."),
        ("Psycher", "Psychic - mind and willpower-based abilities."),
        ("Warlock", "Dark caster - life drain and curses."),
        ("Priest", "Holy - healing, protection, and light damage."),
        ("Trickster", "Chaos - random effects and misdirection."),
        ("Jade Dragon", "Martial artist - unarmed strikes and ki damage."),
        ("Ninja", "Shadow warrior - stealth, dodge, and precision strikes."),
    ]
    for cname, cdesc in class_overview:
        sb.append(f"  {cname:<16} - {cdesc}")
    sb.append("")

    # ── Items ──
    sb.append("=== HARDWARE & ITEMS ===")
    sb.append("Weapons, armor, consumables, and drugs can be bought at shops, looted from")
    sb.append("defeated NPCs, or picked up from the ground. Use GET/DROP/EQUIP/USE.")

    def _rarity_tag(rarity):
        tags = {
            "common": "(common)", "uncommon": "(uncommon)", "rare": "(rare)",
            "epic": "(epic)", "legendary": "(legendary)",
        }
        return tags.get(rarity, f"({rarity})")

    sb.append("\n-- Weapons --")
    weapon_rows = []
    for name, desc, atk, pr, rarity, speed, subtype, bonuses in WEAPON_TABLE:
        bonus_txt = ""
        if bonuses:
            kv = ", ".join(f"{k.upper()}+{v}" for k, v in bonuses.items())
            bonus_txt = f" [{kv}]"
        weapon_rows.append((name, f"{desc}  ATK+{atk}  {_rarity_tag(rarity)}{bonus_txt}", ""))
    sb.extend(_fmt_table(weapon_rows))

    sb.append("\n-- Armor --")
    armor_rows = []
    for name, desc, dfn, pr, rarity, subtype, bonuses in ARMOR_TABLE:
        bonus_txt = ""
        if bonuses:
            kv = ", ".join(f"{k.upper()}+{v}" for k, v in bonuses.items())
            bonus_txt = f" [{kv}]"
        armor_rows.append((name, f"{desc}  DEF+{dfn}  {_rarity_tag(rarity)}{bonus_txt}", ""))
    sb.extend(_fmt_table(armor_rows))

    sb.append("\n-- Consumables --")
    cons_rows = []
    for name, desc, pr, rarity, heal in CONSUMABLE_TABLE:
        heal_txt = f" heals {heal} HP" if heal else ""
        cons_rows.append((name, f"{desc}{heal_txt}  {_rarity_tag(rarity)}", ""))
    sb.extend(_fmt_table(cons_rows))

    sb.append("\n-- Drugs --")
    drug_rows = []
    for name, desc, pr, rarity, addic, bonuses in DRUG_TABLE:
        bonus_txt = ""
        if bonuses:
            kv = ", ".join(f"{k.upper()}+{v}" for k, v in bonuses.items())
            bonus_txt = f" [{kv}]"
        drug_desc = f"{desc}  addiction {addic:.0%}  {_rarity_tag(rarity)}{bonus_txt}"
        drug_rows.append((name, drug_desc, ""))
    sb.extend(_fmt_table(drug_rows))

    sb.append("\n-- Miscellaneous --")
    misc_rows = []
    for name, desc, pr, rarity in MISC_TABLE:
        misc_rows.append((name, f"{desc}  {_rarity_tag(rarity)}", ""))
    sb.extend(_fmt_table(misc_rows))

    sb.append("")
    sb.append("=== GRID TERMINAL CREATED BY DARK WORK ===")

    return "\n".join(sb)


def get_top_ten():
    top_players = Player.objects.order_by("-lvl", "-exp")[:25]
    sb = ["\n=== TOP 25 ADVENTURERS ==="]
    for i, p in enumerate(top_players, 1):
        bot_marker = " (bot)" if p.is_bot and p.user.id % 2 == 0 else ""
        sb.append(
            f"{i:2}. {p.user.username}{bot_marker:15} | Lv {p.lvl:2} | EXP: {p.exp:5} | "
            f"Class: {p.game_class}"
        )
    return "\n".join(sb)


def get_wall_of_death():
    """Display the top players by death count."""
    top_deaths = Player.objects.order_by("-deaths", "-lvl")[:25]
    sb = ["\n=== WALL OF DEATH ==="]
    sb.append("The most fallen souls in the grid:")
    for i, p in enumerate(top_deaths, 1):
        if p.deaths > 0:
            sb.append(
                f"{i:2}. {p.user.username:15} | {p.deaths:3} deaths | Lv {p.lvl:2} | {p.game_class}"
            )
    if not any(p.deaths > 0 for p in top_deaths):
        sb.append("The wall is empty... for now.")
    return "\n".join(sb)


def get_procedural_desc(obj, viewer=None):
    if isinstance(obj, Player):
        is_self = viewer and obj.id == viewer.id
        equipped_items = InventoryItem.objects.filter(player=obj, equipped=True).select_related("item")
        armor = equipped_items.filter(item__item_type="armor").first()
        weapon = equipped_items.filter(item__item_type="weapon").first()
        other_equipped = equipped_items.exclude(item__item_type__in=["armor", "weapon"])

        rep = get_reputation_title(obj.karma)
        gender_pronoun = obj.gender.lower()
        if gender_pronoun == "male":
            pronoun_cap = "He"
        elif gender_pronoun == "female":
            pronoun_cap = "She"
        else:
            pronoun_cap = "They"

        if is_self:
            desc = f"You are a {obj.race} {obj.game_class} known as a {rep}. "
            if armor:
                desc += f"You are wearing {armor.item.name}. "
            else:
                desc += "You are wearing standard-issue synth-rags. "
            if weapon:
                desc += f"You are wielding {weapon.item.name}. "
            if other_equipped.exists():
                names = [ei.item.name for ei in other_equipped]
                desc += f"You also have {', '.join(names)} active. "
        else:
            verb_are = "are" if pronoun_cap == "They" else "is"
            verb_wearing = "are" if pronoun_cap == "They" else "is"
            verb_wielding = "are" if pronoun_cap == "They" else "is"
            verb_has = "have" if pronoun_cap == "They" else "has"
            desc = f"{pronoun_cap} {verb_are} a {obj.race} {obj.game_class} known as a {rep}. "
            if armor:
                desc += f"{pronoun_cap} {verb_wearing} wearing {armor.item.name}. "
            else:
                desc += f"{pronoun_cap} {verb_wearing} wearing standard-issue synth-rags. "
            if weapon:
                desc += f"{pronoun_cap} {verb_wielding} wielding {weapon.item.name}. "
            if other_equipped.exists():
                names = [ei.item.name for ei in other_equipped]
                desc += f"{pronoun_cap} also {verb_has} {', '.join(names)} active. "

        desc += f"{get_combat_desc(obj.attack, obj.defense, is_self=is_self)} "

        pronoun = "you" if is_self else "they"
        subject = "You" if is_self else "They"
        verb = "are" if is_self else "appear"
        seem_verb = "seem" if is_self else "seem"

        desc += (
            f"Physically, {pronoun} {verb} {get_attribute_desc('str', obj.str_stat)} and "
            f"{get_attribute_desc('agi', obj.agi_stat)}. {subject} {verb} "
            f"{get_attribute_desc('hea', obj.hea_stat)}, yet {seem_verb} "
            f"{get_attribute_desc('int', obj.int_stat)} and "
            f"{get_attribute_desc('wil', obj.wil_stat)}. "
            f"Furthermore, {pronoun} {verb} {get_attribute_desc('cha', obj.cha_stat)}. "
        )

        if is_self:
            if obj.hp < obj.hp_max * 0.3:
                desc += "Your health is critical, systems flickering."
            elif obj.hp < obj.hp_max * 0.7:
                desc += "You show signs of recent combat."
            else:
                desc += "You look ready for action."
        else:
            if obj.hp < obj.hp_max * 0.3:
                desc += "Their health critical, systems flickering."
            elif obj.hp < obj.hp_max * 0.7:
                desc += "They show signs of recent combat."
            else:
                desc += "They look ready for action."
        return desc

    if isinstance(obj, NPC):
        desc = f"{obj.description} This entity appears to be a {get_threat_desc(obj.lvl)}. "
        desc += f"{get_combat_desc(obj.attack, obj.defense, is_self=False)} "
        
        # Show weapon if equipped
        if obj.weapon:
            desc += f"It wields {obj.weapon.name}. "
        
        effective_element = obj.get_effective_element()
        desc += f"It radiates an energy signature associated with {effective_element.upper()}."

        if obj.hp < obj.hp_max * 0.3:
            desc += " It's badly damaged and near failure."
        elif obj.hp < obj.hp_max * 0.7:
            desc += " It looks somewhat worn down."

        if obj.npc_type == "boss":
            desc += " It radiates a crushing aura of power. Caution advised."
        elif obj.npc_type == "dealer":
            desc += " They keep looking over their shoulder."

        if obj.karma_alignment > 50:
            desc += " It seems to represent local law and order."
        elif obj.karma_alignment < -50:
            desc += " It has a distinctly predatory and malevolent presence."

        return desc

    if isinstance(obj, Item):
        desc = obj.description
        desc += f" [Rarity: {get_rarity_desc(obj.rarity)}]"
        if obj.item_type == "weapon":
            desc += f" It provides a {get_item_bonus_desc(obj.attack_bonus)} boost to offense."
        elif obj.item_type == "armor":
            desc += f" It provides a {get_item_bonus_desc(obj.defense_bonus)} boost to defense."
        return desc

    return "No detailed data available."


def get_look(player, target_name=None):
    room = player.location
    if not room:
        return "THE VOID."

    if target_name:
        target_name_lower = target_name.lower().strip()
        # Handle common syntax like "look at me"
        if target_name_lower.startswith("at "):
            target_name_lower = target_name_lower[3:].strip()

        if target_name_lower in ["me", "sel"] or target_name_lower == player.user.username.lower():
            return f"\n[SCAN: {player.user.username}]\n{get_procedural_desc(player, viewer=player)}"

        # Look at NPC
        npc = NPC.objects.filter(location=room, name__icontains=target_name_lower, hp__gt=0).first()
        if npc:
            return f"\n[SCAN: {npc.name}]\n{get_procedural_desc(npc)}"

        # Look at Player
        other = (
            Player.objects.filter(
                location=room, user__username__icontains=target_name_lower, online=True
            )
            .exclude(id=player.id)
            .first()
        )
        if other:
            return f"\n[SCAN: {other.user.username}]\n{get_procedural_desc(other, viewer=player)}"

        # Look at Item in room
        item = room.items.filter(name__icontains=target_name_lower).first()
        if item:
            return f"\n[SCAN: {item.name}]\n{get_procedural_desc(item)}"

        # Look at Item in inventory
        ii = InventoryItem.objects.filter(
            player=player, item__name__icontains=target_name_lower
        ).first()
        if ii:
            return f"\n[SCAN: {ii.item.name}]\n{get_procedural_desc(ii.item)}"

        return f"Target '{target_name_lower}' not detected in local sector."

    sb = [f"\n[Location] {room.name}"]
    sb.append(f"DATA: {room.description}")

    if room.shop_name:
        sb.append(f"\n[TERMINAL] A commerce node is active here: {room.shop_name}")

    # Advertise Wall of Death in the hub
    if room.zone == "hub":
        top_deaths = Player.objects.order_by("-deaths", "-lvl")[:3]
        if top_deaths and top_deaths[0].deaths > 0:
            sb.append(
                f"\n[WALL OF DEATH] Type WALL to see the most fallen. "
                f"Current leader: {top_deaths[0].user.username} ({top_deaths[0].deaths} deaths)"
            )

    npcs = NPC.objects.filter(location=room, hp__gt=0)
    if npcs.exists():
        sb.append("\nDETECTED ENTITIES:")
        for n in npcs:
            indicator = " [BOSS]" if n.npc_type == "boss" else ""
            sb.append(f"  > {n.name} ({get_threat_desc(n.lvl)}){indicator}")

    if room.exits:
        sb.append(f"\n[Exits: {', '.join(room.exits.keys()).upper()}]")

    items = room.items.all()
    for item in items:
        sb.append(f"[Hardware] {item.name} is here.")

    others = Player.objects.filter(location=room, online=True).exclude(id=player.id)
    for o in others:
        sb.append(f"[User] {o.user.username} is here.")

    return "\n".join(sb)


def process_addiction(player):
    output = ""
    if player.addiction_points > 0:
        player.withdrawal_timer += 1
        if player.withdrawal_timer > 10:
            dmg = random.randint(1, player.addiction_points // 5 + 2)
            player.hp -= dmg
            output += f"\n[WITHDRAWAL] Your systems are crashing. -{dmg} HP."
            if player.hp <= 0:
                output += "\n[CRITICAL ERROR] SYSTEM FAILURE: OVERDOSE/WITHDRAWAL."
                player.hp = player.hp_max // 2
                player.money = max(0, player.money - 20)
                player.addiction_points = max(0, player.addiction_points - 10)
                player.location = Room.objects.get(id=1)
                output += "\nRebooted at The Neon Hub."

        if player.withdrawal_timer > 50:
            player.addiction_points = max(0, player.addiction_points - 1)
            player.withdrawal_timer = 40

    player.save(update_fields=["hp", "money", "addiction_points", "withdrawal_timer", "location"])
    return output


def respawn_npcs(room):
    if not room.respawn_npcs:
        return ""

    now = timezone.now()
    if room.last_npc_spawn and (now - room.last_npc_spawn).total_seconds() < room.respawn_timer:
        return ""

    room.last_npc_spawn = now
    room.save(update_fields=["last_npc_spawn"])

    # Respawn existing dead NPCs
    dead_npcs = NPC.objects.filter(location=room, hp__lte=0, respawnable=True)
    respawned_count = 0
    npc_ids = []
    for n in dead_npcs:
        n.hp = n.hp_max
        npc_ids.append(n.pk)
        respawned_count += 1
        # Give respawned NPCs a chance to have drops and weapons
        if not n.drops.exists() and random.random() < 0.5:
            drop_item = Item.objects.order_by("?").first()
            if drop_item:
                n.drops.add(drop_item)
        if not n.weapon and random.random() < 0.3:
            weapon = Item.objects.filter(item_type="weapon").order_by("?").first()
            if weapon:
                n.weapon = weapon
                n.save(update_fields=["weapon"])

    # Bulk update respawned NPCs
    if npc_ids:
        NPC.objects.filter(pk__in=npc_ids).update(hp=models.F("hp_max"))

    # Occasionally generate a new random NPC if none exist
    alive_npcs = NPC.objects.filter(location=room, hp__gt=0)
    if not alive_npcs.exists() and room.zone != "hub" and random.random() < 0.2:
        # Enforce hard limit: max 50 NPCs per zone
        zone_npc_count = NPC.objects.filter(location__zone=room.zone, hp__gt=0).count()
        if zone_npc_count >= 50:
            return ""
        is_boss = random.random() < 0.05
        is_miniboss = not is_boss and random.random() < 0.15

        npc_names = [
            "Rogue Drone",
            "Scavenger",
            "Corporate Enforcer",
            "Street Punk",
            "Glitch-Hulk",
            "Vigilante",
            "Paladin-Mech",
            "Cyber-Assassin",
        ]
        name = random.choice(npc_names)
        lvl = random.randint(1, 10)

        karma_alignment = random.randint(-100, 100)

        npc_type = "drone"
        if is_boss:
            npc_type = "boss"
            name = f"ELITE: {name.upper()}"
            lvl += 5
        elif is_miniboss:
            npc_type = "mini-boss"
            name = f"VETERAN: {name}"
            lvl += 2
        else:
            if "Vigilante" in name or "Paladin" in name:
                npc_type = "vigilante"
                karma_alignment = random.randint(50, 100)
            elif "Assassin" in name or "Punk" in name:
                npc_type = "gang"
                karma_alignment = random.randint(-100, -50)
            else:
                npc_type = random.choice(["drone", "gang", "corporate"])

        multiplier = 4 if is_boss else (2 if is_miniboss else 1)

        new_npc = NPC.objects.create(
            name=f"{name} {random.randint(100, 999)}",
            description=f"A hostile {name.lower()} wandering the grid.",
            location=room,
            attack=(5 + lvl * 2) * (2 if is_boss else 1),
            defense=(2 + lvl) * multiplier,
            hp=(20 + lvl * 10) * multiplier * 2,
            hp_max=(20 + lvl * 10) * multiplier * 2,
            lvl=lvl,
            money_drop=lvl * 10 * multiplier,
            exp_drop=lvl * 40 * multiplier,
            aggressive=(random.random() < 0.3 or is_boss),
            karma_alignment=karma_alignment,
            npc_type=npc_type,
        )
        # Give new NPCs drops and weapons so bots can collect items
        if random.random() < 0.5:
            drop_item = Item.objects.order_by("?").first()
            if drop_item:
                new_npc.drops.add(drop_item)
        if random.random() < 0.3:
            weapon = Item.objects.filter(item_type="weapon").order_by("?").first()
            if weapon:
                new_npc.weapon = weapon
                new_npc.save(update_fields=["weapon"])

        return f"\n[SENSORS] {'MASSIVE ' if is_boss else ''}NEW ENTITIES DETECTED."

    if respawned_count > 0:
        return "\n[SENSORS] Local entities have rebooted."
    return ""


def move_player(player, direction):
    dir_map = {"n": "north", "s": "south", "e": "east", "w": "west"}
    direction = dir_map.get(direction, direction)

    if direction not in player.location.exits:
        return "PATH BLOCKED."

    new_room_id = player.location.exits[direction]
    try:
        # Store old room for broadcast
        old_room = player.location

        # Interrupt rest if player moves
        if player.resting:
            player.resting = False
            player.rest_started_at = None
            player.save(update_fields=["resting", "rest_started_at"])

        player.location = Room.objects.get(id=new_room_id)
        player.last_move_time = timezone.now()
        player.save(update_fields=["location", "last_move_time"])
        touch_player_activity(player)

        # Broadcast exit to old room
        broadcast_room_event(player, old_room, None, "exit")

        # Broadcast entry to new room
        broadcast_room_event(player, None, player.location, "enter")

        # If hidden and moving, re-roll stealth detection for the new room
        stealth_break_msg = ""
        if player.hidden:
            npcs = NPC.objects.filter(location=player.location, hp__gt=0)
            max_npc_lvl = max([n.lvl for n in npcs]) if npcs.exists() else 0
            players_here = Player.objects.filter(location=player.location, online=True).exclude(
                id=player.id
            )
            max_player_lvl = max([p.lvl for p in players_here]) if players_here.exists() else 0
            threat_lvl = max(max_npc_lvl, max_player_lvl)

            stay_chance = 40 + player.agi_stat // 3
            if threat_lvl > 0:
                lvl_penalty = max(0, (threat_lvl - player.lvl) * 15)
                stay_chance -= lvl_penalty

            if random.randint(1, 100) > stay_chance:
                player.hidden = False
                player.save(update_fields=["hidden"])
                stealth_break_msg = (
                    f"\n[ALERT] Your cover is blown in the new sector! "
                    f"({stay_chance}% stay hidden)"
                )
            else:
                stealth_break_msg = f"\n[STEALTH] You remain hidden. ({stay_chance}% stay hidden)"

        respawn_msg = respawn_npcs(player.location)
        look_text = get_look(player)
        addiction_msg = process_addiction(player)

        auto_attack_msg = ""
        if not player.location.safe_zone and player.lvl >= 5 and not player.hidden:
            # NPC Aggression Logic - hidden players avoid auto-attack
            npcs = NPC.objects.filter(location=player.location, hp__gt=0)
            attacker = None
            for npc in npcs:
                if npc.aggressive:
                    attacker = npc
                    break
                if npc.karma_alignment > 40 and player.karma < -40:
                    attacker = npc
                    break
                if npc.karma_alignment < -40 and player.karma > 40:
                    attacker = npc
                    break
                if abs(npc.karma_alignment - player.karma) > 130:
                    attacker = npc
                    break

            if attacker:
                auto_attack_msg = f"\n[DANGER] {attacker.name} detects your presence and engages!"
                # Trigger combat start
                player.last_combat_npc = attacker
                player.save(update_fields=["last_combat_npc"])

        return (
            look_text
            + stealth_break_msg
            + addiction_msg
            + respawn_msg
            + auto_attack_msg
        )
    except Room.DoesNotExist:
        return "NAVIGATION ERROR."


def broadcast_room_event(player, old_room, new_room, event_type):
    """Broadcast room entry/exit events to players in the affected rooms."""
    if event_type == "exit" and old_room:
        players_in_old = Player.objects.filter(location=old_room, online=True).exclude(id=player.id)
        for p in players_in_old:
            if len(p.notification) > 0:
                p.notification += "\n"
            p.notification += f"[GRID] {player.user.username} leaves the sector."
        if players_in_old:
            Player.objects.bulk_update(players_in_old, ["notification"])

    if event_type == "enter" and new_room:
        players_in_new = Player.objects.filter(location=new_room, online=True).exclude(id=player.id)
        for p in players_in_new:
            if len(p.notification) > 0:
                p.notification += "\n"
            p.notification += f"[GRID] {player.user.username} enters the sector."
        if players_in_new:
            Player.objects.bulk_update(players_in_new, ["notification"])


def broadcast_npc_movement(npc, old_room, new_room):
    """Broadcast NPC movement between rooms."""
    if old_room and old_room != new_room:
        players_in_old = Player.objects.filter(location=old_room, online=True)
        for p in players_in_old:
            if len(p.notification) > 0:
                p.notification += "\n"
            p.notification += f"[GRID] {npc.name} leaves the sector."
        if players_in_old:
            Player.objects.bulk_update(players_in_old, ["notification"])

    if new_room:
        players_in_new = Player.objects.filter(location=new_room, online=True)
        for p in players_in_new:
            if len(p.notification) > 0:
                p.notification += "\n"
            p.notification += f"[GRID] {npc.name} enters the sector."
        if players_in_new:
            Player.objects.bulk_update(players_in_new, ["notification"])


# ─────────────────────────────────────────────────────────────────────────────
# AFK / Idle System
# - The starting location (The Neon Hub) randomly teleports idle players and
#   bots to random level-appropriate sectors after 2 minutes of inactivity.
# - Players who do NOTHING for 1 hour are kicked and must log back in.
#   Kicked players lose absolutely nothing (no credits, EXP or items).
# ─────────────────────────────────────────────────────────────────────────────
HUB_ROOM_ID = 1
AFK_TELEPORT_SECONDS = 120  # 2 minutes idle in the hub -> random relocation
AFK_KICK_SECONDS = 3600  # 1 hour of total inactivity -> kicked to login
STUCK_BOT_SECONDS = 300  # bots that haven't moved for 5 min get relocated
_last_afk_sweep = None

# Zone id -> (min level, max level). Mirrors ZONE_TEMPLATES in init_game.
ZONE_LEVEL_RANGES = {
    "slums": (1, 3),
    "neon": (2, 5),
    "industrial": (3, 6),
    "corporate": (6, 10),
    "undergrid": (8, 12),
    "wastes": (10, 15),
    "nexus": (12, 18),
    "undercity": (15, 20),
}


def touch_player_activity(player):
    """Record that a player/bot just DID something (command, move, fight)."""
    player.last_activity = timezone.now()
    try:
        player.save(update_fields=["last_activity"])
    except Exception:
        pass


def get_level_appropriate_zones(level):
    """Zones whose level band fits the given player level."""
    zones = [
        zone
        for zone, (min_lvl, max_lvl) in ZONE_LEVEL_RANGES.items()
        if level >= min_lvl and level <= max_lvl + 2
    ]
    if not zones:
        # High-level players can be dropped anywhere dangerous
        zones = list(ZONE_LEVEL_RANGES.keys())
    return zones


def pick_teleport_room(level):
    """Pick a random level-appropriate room, preferring rooms with living NPCs
    so relocated players and bots have something to fight for EXP."""
    zones = get_level_appropriate_zones(level)
    rooms = list(Room.objects.filter(zone__in=zones, safe_zone=False))
    if not rooms:
        rooms = list(Room.objects.filter(safe_zone=False).exclude(id=HUB_ROOM_ID))
    if not rooms:
        return None

    # Prefer hunting grounds that actually have NPCs
    populated = [r for r in rooms if r.npc_set.filter(hp__gt=0).exists()]
    return random.choice(populated or rooms)


def teleport_player_to_room(player, room, reason):
    """Move a player/bot to a room, clearing combat state, and announce it."""
    old_room = player.location
    now = timezone.now()
    player.location = room
    player.last_move_time = now
    player.last_activity = now
    player.resting = False
    player.rest_started_at = None
    player.auto_attack = False
    player.save(
        update_fields=[
            "location",
            "last_move_time",
            "last_activity",
            "resting",
            "rest_started_at",
            "auto_attack",
        ]
    )
    if old_room:
        broadcast_room_event(player, old_room, None, "exit")
    broadcast_room_event(player, None, room, "enter")
    if len(player.notification) > 0:
        player.notification += "\n"
    player.notification += f"\n[TELEPORT] {reason} You materialize in {room.name}."
    player.save(update_fields=["notification"])
    return player


def kick_player_for_inactivity(player):
    """Kick an idle human player from the grid. They lose NOTHING - credits,
    EXP, items and location are all preserved. They simply have to log back
    in from the login page."""
    player.online = False
    player.last_combat_npc = None
    player.last_combat_player = None
    player.auto_attack = False
    player.resting = False
    player.rest_started_at = None
    player.save(
        update_fields=[
            "online",
            "last_combat_npc",
            "last_combat_player",
            "auto_attack",
            "resting",
            "rest_started_at",
        ]
    )
    return f"[SYSTEM] {player.user.username} disconnected (1 hour of inactivity, no losses)."


def process_afk_players(force=False):
    """Periodic sweep handling idle players and bots:
    1. Humans AFK for 1 hour get kicked (lose nothing).
    2. Anyone idling 2+ minutes in the starting location gets randomly
       teleported to a level-appropriate sector (random chance per sweep so
       it happens 'randomly' shortly after the 2-minute mark, guaranteed by
       5 minutes).
    3. Bots stuck anywhere without moving for 5+ minutes (and not fighting)
       are teleported back into action."""
    global _last_afk_sweep

    now = timezone.now()
    if not force:
        if _last_afk_sweep is not None:
            if (now - _last_afk_sweep).total_seconds() < 10:
                return
        _last_afk_sweep = now

    for p in Player.objects.filter(online=True).select_related("location", "user"):
        last_active = p.last_activity or p.last_seen

        # 1. Kick humans that have done nothing for 1 hour (bots never kick)
        if not p.is_bot:
            if last_active and (now - last_active).total_seconds() >= AFK_KICK_SECONDS:
                kick_player_for_inactivity(p)
                continue

        # Skip anyone actively fighting or resting
        if p.last_combat_npc or p.last_combat_player or p.resting:
            continue
        if not p.location:
            continue

        afk_seconds = (now - last_active).total_seconds() if last_active else 0
        in_starting_location = p.location.id == HUB_ROOM_ID or p.location.zone == "hub"

        # 2. Random relocation from the starting location after 2 min AFK
        if in_starting_location and afk_seconds >= AFK_TELEPORT_SECONDS:
            if random.random() < 0.4 or afk_seconds >= AFK_TELEPORT_SECONDS * 2 + 60:
                room = pick_teleport_room(p.lvl)
                if room and room != p.location:
                    teleport_player_to_room(
                        p, room, "Idle-link detected. Grid relocation protocol engaged."
                    )
            continue

        # 3. Stuck bots: no movement and no activity for a long stretch
        if p.is_bot and not in_starting_location:
            last_move = p.last_move_time or last_active
            stuck_seconds = (now - last_move).total_seconds() if last_move else 0
            if stuck_seconds >= STUCK_BOT_SECONDS and afk_seconds >= AFK_TELEPORT_SECONDS:
                if random.random() < 0.4 or stuck_seconds >= STUCK_BOT_SECONDS * 2:
                    room = pick_teleport_room(p.lvl)
                    if room and room != p.location:
                        teleport_player_to_room(
                            p,
                            room,
                            "Stuck-node reset. You are dropped into a live sector.",
                        )


def calculate_damage(
    atk, dfn, element="physical", weakness="none", resistance="none", crit_chance=0
):
    base_dmg = max(1, atk - dfn // 2)
    dmg = random.randint(max(1, base_dmg - 2), base_dmg + 2)

    # Critical strike check
    is_crit = False
    if crit_chance > 0 and random.randint(1, 100) <= crit_chance:
        is_crit = True
        dmg = int(dmg * 2)  # Critical hits do 2x damage

    strong_against = {"fire": "air", "air": "earth", "earth": "water", "water": "fire"}

    if element != "physical":
        if weakness == element or strong_against.get(element) == weakness:
            dmg = int(dmg * 1.5)
        elif resistance == element:
            dmg = int(dmg * 0.5)

    return dmg, is_crit


# ─────────────────────────────────────────────────────────────────────────────
# Room-wide AOE System
# These special moves/spells blast the ENTIRE sector: every living NPC and
# every eligible player takes damage, anything that dies awards EXP/loot,
# and the survivors aggro the caster (NPCs turn hostile; bots react based
# on their aggression/karma personality).
# Format: move name -> (damage multiplier per hit, element)
# ─────────────────────────────────────────────────────────────────────────────
AOE_MOVES = {
    "whirlwind": (1.2, "physical"),  # Street Samurai 20
    "phantom_sweep": (1.2, "physical"),  # Ninja 20
    "chi_burst": (1.5, "air"),  # Jade Dragon 25
    "viral_burst": (1.5, "earth"),  # Medie 25
    "avalanche": (1.8, "earth"),  # Heavy 25
    "earthshaker": (2.0, "earth"),  # Heavy 30
    "singularity": (2.0, "earth"),  # Techie 30
    "armageddon": (2.2, "fire"),  # Warlock 30
    "plague_wave": (1.6, "earth"),  # Warlock 40
    "eidolon_swarm": (1.5, "air"),  # Psycher 45
    "neural_cascade": (1.7, "water"),  # Netrunner 50
    "orbital_laser": (2.2, "fire"),  # Techie 50
    "titan_fall": (2.0, "earth"),  # Heavy 50
    "chaos_theory": (1.8, "air"),  # Trickster 50
}

# Bonus damage multiplier AOE moves get against their primary target
AOE_DIRECT_HIT_BONUS = 1.5


def get_class_primary_stat(player):
    """The class's main scaling stat (mirrors use_ability's damage logic)."""
    if player.game_class in ("Street Samurai", "Heavy"):
        return player.str_stat
    if player.game_class == "Jade Dragon":
        return player.agi_stat
    if player.game_class in ("Netrunner", "Techie", "Psycher", "Warlock"):
        return player.int_stat
    if player.game_class == "Priest":
        return player.wil_stat
    if player.game_class in ("Thief", "Ninja"):
        return player.agi_stat
    if player.game_class == "Medie":
        return max(player.int_stat, player.hea_stat)
    if player.game_class in ("Fixer", "Trickster"):
        return player.cha_stat
    return 10


def get_unarmed_mult(player):
    """Jade Dragon-style bonus: 1.5x damage when no weapon is equipped."""
    if InventoryItem.objects.filter(
        player=player, equipped=True, item__item_type="weapon"
    ).exists():
        return 1.0
    return 1.5


def award_npc_kill(player, npc):
    """Award EXP, credits, karma and loot for neutralizing an NPC.
    Returns the output message (includes level-up checks)."""
    output = ""
    exp_gain = npc.exp_drop
    player.exp += exp_gain
    player.money += npc.money_drop

    if npc.karma_alignment < -30:
        player.karma += 5
    elif npc.karma_alignment > 30:
        player.karma -= 10
    else:
        player.karma += 1
    player.karma = max(-100, min(100, player.karma))
    player.save(update_fields=["exp", "money", "karma"])

    output += f"\nTarget neutralized! +{exp_gain} exp, +{npc.money_drop} credits."
    output += drop_npc_weapon(npc)
    for item in npc.drops.all():
        ii, created = InventoryItem.objects.get_or_create(player=player, item=item)
        if not created:
            ii.quantity += 1
        ii.save()
        output += f"\nRetrieved: {item.name}"
    output += check_level_up(player)
    return output


def award_player_kill(player, target):
    """Award EXP/credits for defeating another player and respawn them at the
    hub. Returns the output message."""
    exp_gain = target.lvl * 50
    stolen = target.money // 4
    player.exp += exp_gain
    player.money += stolen
    player.save(update_fields=["exp", "money", "karma"])

    hub = Room.objects.filter(id=HUB_ROOM_ID).first()
    target.hp = target.hp_max // 2
    target.money = max(0, target.money - stolen)
    if hub:
        target.location = hub
    target.last_combat_npc = None
    target.last_combat_player = None
    target.auto_attack = False
    target.notification = (
        f"\nYou were neutralized by {player.user.username}! Lost {stolen} credits."
    )
    target.save(
        update_fields=[
            "hp",
            "money",
            "location",
            "last_combat_npc",
            "last_combat_player",
            "auto_attack",
            "notification",
        ]
    )
    output = f"\nYou neutralized {target.user.username}! +{exp_gain} exp, +{stolen} credits."
    output += check_level_up(player)
    return output


def execute_room_aoe(player, ability_name, mult, element, req_lvl):
    """Unleash a room-wide AOE strike. Every living NPC and every eligible
    player in the sector takes damage; kills award EXP/loot; survivors AGGRO
    the caster (NPCs turn hostile, aggressive bots strike back, cowardly bots
    flee). The named target (if any) takes bonus damage."""
    room = player.location
    res = f"\n[AOE] {ability_name.upper()} erupts across the entire sector!"

    # Damage scaling (mirrors use_ability's deal_dmg logic)
    primary_stat = get_class_primary_stat(player)
    power_val = (primary_stat * 1.5) + (player.attack * 0.5)
    req_mult = 1.0 + (req_lvl / 20.0)
    final_atk = int(power_val * mult * req_mult)
    if element == "physical":
        crit_chance = min(10, max(1, player.agi_stat // 5))
    else:
        crit_chance = min(10, max(1, player.int_stat // 5))

    # Party members are never caught in the blast
    party_member_ids = set()
    party = player.parties.first()
    if party:
        party_member_ids = set(party.members.values_list("id", flat=True))

    def strike(target, direct=False):
        """Damage one entity. Returns (message, killed)."""
        if target.hp <= 0:
            return "", False
        if isinstance(target, NPC):
            dmg, is_crit = calculate_damage(
                final_atk,
                target.defense,
                element=element,
                weakness=target.weakness,
                resistance=target.resistance,
                crit_chance=crit_chance,
            )
        else:
            dmg, is_crit = calculate_damage(
                final_atk, target.defense, element=element, crit_chance=crit_chance
            )
        if direct:
            dmg = int(dmg * AOE_DIRECT_HIT_BONUS)
        t_name = target.name if isinstance(target, NPC) else target.user.username
        target.hp -= dmg
        msg = f"\n[AOE] {t_name} takes {dmg} {element} damage!"
        if is_crit:
            msg = f"\n[AOE][CRIT] {t_name} takes {dmg} {element} damage!"
        killed = False
        if isinstance(target, Player):
            player.karma -= 2
            player.save(update_fields=["karma"])
            target.save(update_fields=["hp"])
            if target.hp <= 0:
                killed = True
                msg += award_player_kill(player, target)
        else:
            target.save(update_fields=["hp"])
            if target.hp <= 0:
                killed = True
                msg += award_npc_kill(player, target)
        return msg, killed

    hit_targets = 0
    kill_count = 0

    # 1. Blast every living NPC in the room
    for npc in NPC.objects.filter(location=room, hp__gt=0):
        direct = (
            player.last_combat_npc and npc.id == player.last_combat_npc.id
        ) or False
        msg, killed = strike(npc, direct=direct)
        if msg:
            res += msg
            hit_targets += 1
            if killed:
                kill_count += 1

    # 2. Splash every eligible player (standard PvP rules: lvl 5+, +/-4 lvls)
    for other in (
        Player.objects.filter(location=room, online=True)
        .exclude(id=player.id)
        .exclude(id__in=party_member_ids)
    ):
        if other.lvl < 5 or abs(player.lvl - other.lvl) > 4:
            continue
        direct = (
            player.last_combat_player and other.id == player.last_combat_player.id
        ) or False
        msg, killed = strike(other, direct=direct)
        if msg:
            res += msg
            hit_targets += 1
            if killed:
                kill_count += 1

    if hit_targets == 0:
        res += "\nThe sector is empty. The blast dissipates harmlessly."
        return res

    res += f"\n[AOE] {hit_targets} entities caught in the blast radius. ({kill_count} down)"
    return aoe_aggro_survivors(player, res, room, ability_name)


def aoe_aggro_survivors(player, res, room, ability_name):
    """Survivors of an AOE blast react: NPCs turn hostile and engage, vicious
    bots counter-attack, cowardly bots flee. Broadcasts the carnage too."""
    # AGGRO - surviving NPCs become hostile
    surviving_npcs = list(NPC.objects.filter(location=room, hp__gt=0))
    for npc in surviving_npcs:
        if not npc.aggressive:
            npc.aggressive = True
            npc.save(update_fields=["aggressive"])

    if surviving_npcs and not player.last_combat_npc and not player.last_combat_player:
        engager = random.choice(surviving_npcs)
        player.last_combat_npc = engager
        player.save(update_fields=["last_combat_npc"])
        res += f"\n[AGGRO] {engager.name} survived the blast and engages you!"

    # Bots respond based on personality: vicious ones counter-attack,
    # peaceful ones panic and run.
    for bot in Player.objects.filter(
        location=room, online=True, is_bot=True
    ).exclude(id=player.id):
        if bot.hp <= 0 or bot.last_combat_npc or bot.last_combat_player:
            continue
        if bot.bot_aggression >= 60 or bot.karma <= -20:
            if abs(bot.lvl - player.lvl) <= 4:
                bot.last_combat_player = player
                bot.auto_attack = True
                bot.last_combat_tick = timezone.now()
                bot.save(
                    update_fields=["last_combat_player", "auto_attack", "last_combat_tick"]
                )
                res += f"\n[AGGRO] {bot.user.username} witnessed the blast and turns on you!"
        elif bot.bot_aggression < 30 and room.exits:
            direction = random.choice(list(room.exits.keys()))
            move_player(bot, direction)
            res += f"\n[AGGRO] {bot.user.username} panics and flees the sector!"

    # Broadcast the carnage to everyone else in the room
    room_players = list(
        Player.objects.filter(location=room, online=True)
        .exclude(id=player.id)
        .only("id", "notification")
    )
    broadcast_combat_to_room(
        player,
        ability_name.upper(),
        f"{player.user.username} unleashes {ability_name.upper()} on the whole sector!",
        room_players,
    )
    return res


def true_strike_damage(player, target, mult, element, req_lvl):
    """Ability damage that IGNORES the target's defense entirely.
    Returns the output message (handles kills via the award helpers)."""
    if not target or target.hp <= 0:
        return "\nTarget required."
    primary = get_class_primary_stat(player)
    power_val = (primary * 1.5) + (player.attack * 0.5)
    final_atk = int(power_val * mult * (1.0 + req_lvl / 20.0))
    if element == "physical":
        crit_chance = min(10, max(1, player.agi_stat // 5))
    else:
        crit_chance = min(10, max(1, player.int_stat // 5))
    dmg, is_crit = calculate_damage(final_atk, 0, element=element, crit_chance=crit_chance)
    t_name = target.name if isinstance(target, NPC) else target.user.username
    target.hp -= dmg
    target.save(update_fields=["hp"])
    if is_crit:
        msg = (
            f"\n[PIERCE][CRIT] The strike phases through armor! "
            f"{t_name} takes {dmg} {element} damage."
        )
    else:
        msg = (
            f"\n[PIERCE] The strike phases through armor! "
            f"{t_name} takes {dmg} {element} damage."
        )
    if isinstance(target, Player):
        player.karma -= 2
        player.save(update_fields=["karma"])
        if target.hp <= 0:
            msg += award_player_kill(player, target)
    elif target.hp <= 0:
        msg += award_npc_kill(player, target)
    return msg


def handle_player_defeat(player, victor_player=None):
    """Common logic for when a player's HP reaches zero."""
    output = "\n[CRITICAL ERROR] YOU HAVE BEEN NEUTRALIZED. INITIATING SYSTEM RESET."
    stolen = player.money // 4
    player.hp = player.hp_max // 2
    player.money = max(0, player.money - stolen)
    player.location = Room.objects.get(id=1)
    player.last_combat_npc = None
    player.last_combat_player = None
    player.auto_attack = False
    player.save(update_fields=["hp", "money", "location", "last_combat_npc", "last_combat_player", "auto_attack"])
    output += f"\nRespawned at The Neon Hub. Lost {stolen} credits."

    if victor_player:
        victor_player.money += stolen
        victor_player.exp += player.lvl * 50
        victor_player.notification = (
            f"\nYou neutralized {player.user.username}! "
            f"+{player.lvl * 50} exp, +{stolen} credits."
        )
        victor_player.save(update_fields=["money", "exp", "notification"])

    return output


def combat_round(player):
    """Performs one round of combat for the player and their current target."""
    output = ""
    target_npc = player.last_combat_npc
    target_player = player.last_combat_player

    if not target_npc and not target_player:
        player.auto_attack = False
        player.save(update_fields=["auto_attack"])
        return ""

    target = target_npc or target_player

    # Check if target is still valid/in room
    if isinstance(target, NPC):
        if target.hp <= 0 or target.location != player.location:
            player.last_combat_npc = None
            player.auto_attack = False
            player.save(update_fields=["last_combat_npc", "auto_attack"])
            return f"\n[COMBAT] {target.name} is no longer here."
    else:
        if target.hp <= 0 or target.location != player.location or not target.online:
            player.last_combat_player = None
            player.auto_attack = False
            player.save(update_fields=["last_combat_player", "auto_attack"])
            return f"\n[COMBAT] {target.user.username} is no longer here."

    # Get all players in the room for combat broadcasting
    room_players = list(
        Player.objects.filter(location=player.location, online=True)
        .exclude(id=player.id)
        .only("id", "notification")
    )
    if target_player:
        room_players = [p for p in room_players if p.id != target_player.id]

    # Player attacks
    equipped_weapon_qs = InventoryItem.objects.filter(
        player=player, equipped=True, item__item_type="weapon"
    ).first()
    equipped_weapon = equipped_weapon_qs
    speed_bonus = equipped_weapon.item.speed_bonus if equipped_weapon else 0
    agi_attacks = player.agi_stat // 10
    base_attacks = 1 + (speed_bonus // 10) if speed_bonus > 0 else 1
    p_attacks = base_attacks + agi_attacks

    target_name = target.name if target_npc else target.user.username

    # Get weapon name for display
    weapon_name = equipped_weapon.item.name if equipped_weapon else "fists"

    # Calculate critical strike chance based on agility (for physical attacks)
    # AGI stat: 1-25+ gives 1-5% crit chance, capping at 10%
    agi_crit_chance = min(10, max(1, player.agi_stat // 5))

    for _ in range(p_attacks):
        if isinstance(target, NPC):
            dmg, is_crit = calculate_damage(
                player.attack,
                target.defense,
                element="physical",
                weakness=target.weakness,
                resistance=target.resistance,
                crit_chance=agi_crit_chance,
            )
        else:
            dmg, is_crit = calculate_damage(
                player.attack, target.defense, crit_chance=agi_crit_chance
            )

        target.hp -= dmg
        target.save(update_fields=["hp"] if isinstance(target, Player) else ["hp"])
        if is_crit:
            output += f"\n[CRIT] You hit {target_name} for {dmg} damage with {weapon_name}!"
            # Broadcast crit to room
            broadcast_combat_to_room(
                player,
                target_name,
                f"[CRIT] {player.user.username} hits {target_name} for {dmg} damage with {weapon_name}!",
                room_players,
            )
        else:
            output += f"\nYou hit {target_name} for {dmg} damage with {weapon_name}."
            # Broadcast hit to room
            broadcast_combat_to_room(
                player,
                target_name,
                f"{player.user.username} hits {target_name} for {dmg} damage with {weapon_name}.",
                room_players,
            )

        if target.hp <= 0:
            # Win logic
            if target_npc:
                exp_gain = target.exp_drop
                player.exp += exp_gain
                player.money += target.money_drop
                player.last_combat_npc = None
                player.auto_attack = False

                if target.karma_alignment < -30:
                    player.karma += 5
                elif target.karma_alignment > 30:
                    player.karma -= 10
                else:
                    player.karma += 1

                player.karma = max(-100, min(100, player.karma))
                player.save(update_fields=["exp", "money", "last_combat_npc", "auto_attack", "karma"])

                output += (
                    f"\nTarget neutralized! +{exp_gain} exp, " f"+{target.money_drop} credits."
                )
                # Drop NPC's weapon
                output += drop_npc_weapon(target)
                # Broadcast victory to room
                broadcast_combat_to_room(
                    player,
                    target_name,
                    f"{player.user.username} neutralized {target_name}!",
                    room_players,
                )
                for item in target.drops.all():
                    ii, created = InventoryItem.objects.get_or_create(player=player, item=item)
                    if not created:
                        ii.quantity += 1
                    ii.save()
                    output += f"\nRetrieved: {item.name}"
                output += check_level_up(player)
            else:
                exp_gain = target.lvl * 50
                player.exp += exp_gain
                stolen = target.money // 4
                player.money += stolen
                player.last_combat_player = None
                player.save(update_fields=["exp", "money", "last_combat_player", "auto_attack"])

                hub = Room.objects.get(id=1)
                target.hp = target.hp_max // 2
                target.money -= stolen
                target.location = hub
                notif_msg = (
                    f"\nYou were neutralized by {player.user.username}! " f"Lost {stolen} credits."
                )
                target.notification = notif_msg
                target.save(update_fields=["hp", "money", "location", "notification"])
                output += (
                    f"\nYou neutralized {target_name}! +{exp_gain} exp, " f"+{stolen} credits."
                )
                # Broadcast PvP victory to room
                broadcast_combat_to_room(
                    player,
                    target_name,
                    f"{player.user.username} neutralized {target_name}!",
                    room_players,
                )
                output += check_level_up(player)

            player.auto_attack = False
            player.save(update_fields=["auto_attack"])
            return output

    # Target counter-attacks
    output += execute_opponent_attack(player, target)

    # Broadcast counter-attack to room
    if "hits you" in output:
        counter_msg = f"{target_name} hits {player.user.username}!"
        broadcast_combat_to_room(player, target_name, counter_msg, room_players)

    return output


def execute_opponent_attack(player, target):
    """Internal logic for the opponent striking the player."""
    output = ""
    target_npc = isinstance(target, NPC)

    if target_npc:
        # Use NPC's effective attack and element (including weapon bonuses)
        effective_attack = target.get_effective_attack()
        effective_element = target.get_effective_element()
        target_dmg, _ = calculate_damage(effective_attack, player.defense, element=effective_element)
        player.hp -= target_dmg
        # Show NPC's element in the attack message
        element_str = f" {effective_element}" if effective_element and effective_element != "physical" else ""
        output += f"\n{target.name} hits you for {target_dmg} damage{element_str}."
    else:
        # opponent is a Player - can also crit based on their AGI
        t_weapon = InventoryItem.objects.filter(
            player=target, equipped=True, item__item_type="weapon"
        ).first()
        t_speed = t_weapon.item.speed_bonus if t_weapon else 0
        t_agi_attacks = target.agi_stat // 10
        t_base_attacks = 1 + (t_speed // 10) if t_speed > 0 else 1
        t_attacks = t_base_attacks + t_agi_attacks
        t_crit_chance = min(10, max(1, target.agi_stat // 5))

        for _ in range(t_attacks):
            counter_dmg, is_crit = calculate_damage(
                target.attack, player.defense, crit_chance=t_crit_chance
            )
            player.hp -= counter_dmg
            if is_crit:
                output += f"\n[CRIT] {target.user.username} hits you for {counter_dmg} damage!"
            else:
                output += f"\n{target.user.username} hits you for {counter_dmg} damage."
            if player.hp <= 0:
                break

    player.save(update_fields=["hp"])

    if player.hp <= 0:
        # Broadcast death to room before handling defeat
        if target_npc:
            death_msg = f"{player.user.username} has been splattered by {target.name}! "
            death_msg += "Blood and circuitry everywhere!"
        else:
            death_msg = f"{player.user.username} has been neutralized by {target.user.username}! "
            death_msg += "A brutal end!"
        room_players = list(
            Player.objects.filter(location=player.location, online=True)
            .exclude(id=player.id)
            .only("id", "notification")
        )
        for p in room_players:
            if len(p.notification) > 0:
                p.notification += "\n"
            p.notification += f"[DEATH] {death_msg}"
        if room_players:
            Player.objects.bulk_update(room_players, ["notification"])
        output += handle_player_defeat(player, victor_player=(None if target_npc else target))

    return output


def broadcast_combat_to_room(attacker, target_name, message, room_players):
    """Broadcast combat message to all other players in the room."""
    for p in room_players:
        if len(p.notification) > 0:
            p.notification += "\n"
        p.notification += f"[COMBAT] {message}"
    if room_players:
        Player.objects.bulk_update(room_players, ["notification"])


def disengage_combat(player):
    """Disengage from current combat, stopping auto-attack and clearing target."""
    if not player.last_combat_npc and not player.last_combat_player:
        return "You are not in combat."

    target_name = None
    if player.last_combat_npc:
        target_name = player.last_combat_npc.name
    elif player.last_combat_player:
        target_name = player.last_combat_player.user.username

    player.last_combat_npc = None
    player.last_combat_player = None
    player.auto_attack = False
    player.save(update_fields=["last_combat_npc", "last_combat_player", "auto_attack"])

    return f"\n[COMBAT] You disengage from {target_name}."


def attack_target(player, target_name, auto=False):
    if not target_name:
        # If already in combat and no target specified, just do a round
        if player.last_combat_npc or player.last_combat_player:
            player.auto_attack = auto
            player.save(update_fields=["auto_attack"])
            return combat_round(player)
        return "Specify target."

    if player.location.safe_zone:
        return "Violence is prohibited in this sector."

    # Try to find NPC
    npc = NPC.objects.filter(
        location=player.location, name__icontains=target_name, hp__gt=0
    ).first()
    # Try to find Player
    other = None
    if not npc:
        other = (
            Player.objects.filter(
                location=player.location, user__username__icontains=target_name, online=True
            )
            .exclude(id=player.id)
            .first()
        )

    if not npc and not other:
        return "Target not found."

    if other:
        if abs(player.lvl - other.lvl) > 4:
            return "Target level too distant. Range: +/- 4 levels."
        player.last_combat_player = other
        player.last_combat_npc = None
        player.karma -= 10
    else:
        player.last_combat_npc = npc
        player.last_combat_player = None

    player.auto_attack = auto
    player.last_combat_tick = timezone.now()
    player.save(update_fields=["last_combat_npc", "last_combat_player", "auto_attack", "last_combat_tick", "karma"])

    # Backstab bonus if hidden
    output = ""
    if player.hidden:
        player.hidden = False
        player.save(update_fields=["hidden"])
        output += "\n[BACKSTAB] Strike from the shadows! They never saw you coming."

    output += combat_round(player)
    return output


def process_combat_tick(player):
    """Called during polling to check if an auto-attack or opponent strike should happen."""
    target_npc = player.last_combat_npc
    target_player = player.last_combat_player

    # Validate target before proceeding
    if target_npc:
        if target_npc.hp <= 0 or target_npc.location != player.location:
            player.last_combat_npc = None
            player.auto_attack = False
            player.save(update_fields=["last_combat_npc", "auto_attack"])
            return ""
    elif target_player:
        if (
            target_player.hp <= 0
            or target_player.location != player.location
            or not target_player.online
        ):
            player.last_combat_player = None
            player.auto_attack = False
            player.save(update_fields=["last_combat_player", "auto_attack"])
            return ""
    else:
        return ""

    target = target_npc or target_player

    now = timezone.now()
    if not player.last_combat_tick:
        player.last_combat_tick = now
        player.save(update_fields=["last_combat_tick"])
        return ""

    # Combat tick every 3 seconds
    if (now - player.last_combat_tick).total_seconds() >= 3:
        player.last_combat_tick = now
        player.save(update_fields=["last_combat_tick"])
        # Fighting counts as activity - never AFK while exchanging blows
        touch_player_activity(player)
        if player.auto_attack:
            return combat_round(player)
        else:
            # Player is IDLE in combat, opponent takes advantage
            t_name = target.name if hasattr(target, "name") else target.user.username
            output = f"\n[COMBAT] You are idle! {t_name} strikes!"
            output += execute_opponent_attack(player, target)
            return output

    return ""


def rest_command(player):
    """Allows player to rest and regenerate HP and Mana over time."""
    # Can't rest if in combat
    if player.last_combat_npc or player.last_combat_player:
        return "Cannot rest while engaged in combat."

    # Can't rest if already at full HP and Mana
    if player.hp >= player.hp_max and player.mana >= player.mana_max:
        return "Already at full health and mana. No need to rest."

    # Can't rest if already resting
    if player.resting:
        return "Already resting."

    # Start resting
    player.resting = True
    player.rest_started_at = timezone.now()
    player.save(update_fields=["resting", "rest_started_at"])

    return "\nYou settle down to rest and recover HP and Mana..."


def process_resting(player):
    """Process HP and Mana regeneration for resting players. Called during polling."""
    if not player.resting:
        return ""

    # Check if rest should be interrupted
    # Interrupted by: combat, movement (handled elsewhere), or full HP and Mana
    if player.hp >= player.hp_max and player.mana >= player.mana_max:
        player.resting = False
        player.rest_started_at = None
        player.save(update_fields=["resting", "rest_started_at"])

        # Kick out of safe zones (like Neon Hub) after resting
        if player.location and player.location.safe_zone and player.location.exits:
            exits = list(player.location.exits.keys())
            if exits:
                direction = random.choice(exits)
                move_player(player, direction)
                return "\n[REST] You feel fully recovered. The bouncer kicks you out!"

        return "\n[REST] You feel fully recovered. Ready to move."

    if player.last_combat_npc or player.last_combat_player:
        player.resting = False
        player.rest_started_at = None
        player.save(update_fields=["resting", "rest_started_at"])
        return "\n[REST] Combat detected! Rest interrupted!"

    # Calculate HP regeneration
    # Base regen: 1 HP per 3 seconds, modified by health stat
    # Higher HEA = faster regen
    hp_regen_rate = max(1, player.hea_stat // 5)  # 1-4 HP per tick depending on HEA
    # Mana regen: 1 Mana per tick, modified by INT stat
    mana_regen_rate = max(1, player.int_stat // 5)  # 1-4 Mana per tick depending on INT
    regen_interval = max(2, 5 - (player.hea_stat // 10))
    # 2-5 seconds between regen

    if not player.rest_started_at:
        player.rest_started_at = timezone.now()
        player.save(update_fields=["rest_started_at"])
        return ""

    time_resting = (timezone.now() - player.rest_started_at).total_seconds()

    if time_resting >= regen_interval:
        # Regenerate HP
        old_hp = player.hp
        player.hp = min(player.hp_max, player.hp + hp_regen_rate)
        # Regenerate Mana
        old_mana = player.mana
        player.mana = min(player.mana_max, player.mana + mana_regen_rate)
        player.rest_started_at = timezone.now()
        player.save(update_fields=["hp", "mana", "rest_started_at"])

        msg_parts = []
        if player.hp != old_hp:
            msg_parts.append(f"Recovered {player.hp - old_hp} HP")
        if player.mana != old_mana:
            msg_parts.append(f"Recovered {player.mana - old_mana} Mana")
        if msg_parts:
            return (
                f"\n[REST] {' and '.join(msg_parts)}. "
                f"({player.hp}/{player.hp_max} HP, {player.mana}/{player.mana_max} Mana)"
            )

    return ""


def use_ability(player, ability_name, target_name):
    ability_name = ability_name.lower()

    # Universal sneak/stealth - works for any class, but success varies
    if ability_name in ("stealth", "sneak"):
        # ENHANCED: Can only sneak outside combat
        if player.last_combat_npc or player.last_combat_player:
            return "\nCannot hide while engaged in combat. Disengage first."

        # ENHANCED: Can't sneak while resting
        if player.resting:
            player.resting = False
            player.rest_started_at = None
            player.save(update_fields=["resting", "rest_started_at"])
            return "\nYou stop resting and stand up to attempt stealth."

        if player.location.safe_zone:
            return "\nNo need to hide in a safe sector."

        npcs = NPC.objects.filter(location=player.location, hp__gt=0)
        max_npc_lvl = max([n.lvl for n in npcs]) if npcs.exists() else 0
        players_here = Player.objects.filter(location=player.location, online=True).exclude(
            id=player.id
        )
        max_player_lvl = max([p.lvl for p in players_here]) if players_here.exists() else 0
        threat_lvl = max(max_npc_lvl, max_player_lvl)

        # ENHANCED: Sneaking tied to agility stat
        # Base chance heavily influenced by AGI stat
        if player.game_class in ("Thief", "Trickster") and player.lvl >= 4:
            # Thief/Trickster: AGI is primary stat, get excellent stealth
            base_chance = 50 + (player.agi_stat * 2)  # 70-130 base, capped at 95
        else:
            # Other classes: AGI still matters but less so
            base_chance = 20 + (player.agi_stat * 1.5)  # 35-95 base
            if player.lvl < 4:
                base_chance = max(5, base_chance - 20)

        # Threat level penalty
        if threat_lvl > 0:
            lvl_penalty = max(0, (threat_lvl - player.lvl) * 10)
            base_chance -= lvl_penalty

        # Clamp chance between 5% and 95%
        base_chance = max(5, min(95, base_chance))

        if random.randint(1, 100) <= base_chance:
            player.hidden = True
            player.save(update_fields=["hidden"])
            agi_bonus = (
                f" (AGI: {player.agi_stat})"
                if player.game_class not in ("Thief", "Trickster")
                else ""
            )
            return f"\nYou melt into the shadows. Hidden!{agi_bonus}"
        else:
            player.hidden = False
            player.save(update_fields=["hidden"])
            return "\nFailed to hide. You remain visible."

    # Check if this command is actually a move for this class
    moves = CLASS_MOVES.get(player.game_class, [])
    req_lvl = 999
    for lvl, name, acronym, desc in moves:
        # Match by full name or acronym
        if name.lower() == ability_name or acronym.lower() == ability_name:
            req_lvl = lvl
            break

    if req_lvl == 999:  # Not a move for this class
        return None

    if player.lvl < req_lvl:
        return f"Level required for {ability_name.upper()}."

    npc = None
    target_player = None
    if target_name:
        npc = NPC.objects.filter(
            location=player.location, name__icontains=target_name, hp__gt=0
        ).first()
        target_player = (
            Player.objects.filter(
                location=player.location, user__username__icontains=target_name, online=True
            )
            .exclude(id=player.id)
            .first()
        )

    if target_player:
        if player.lvl < 5:
            return "Neural safety lock engaged. Level 5 required to target users."
        if abs(player.lvl - target_player.lvl) > 4:
            return "Target level too distant. Range: +/- 4 levels."
        if player.location.safe_zone:
            return "Violence is prohibited in this sector."

    target = npc or target_player
    cost = 5 + (req_lvl // 2)

    # Room-wide AOE moves blast the ENTIRE sector instead of one target.
    # Any combat nearby gets dragged into it: everything in the room takes
    # damage, deaths award EXP, and survivors aggro the caster.
    if ability_name in AOE_MOVES:
        if player.location.safe_zone:
            return "Violence is prohibited in this sector."
        if player.mana < cost:
            return "INSUFFICIENT BUFFER (MANA)."
        player.mana -= cost
        player.save(update_fields=["mana"])
        aoe_mult, aoe_element = AOE_MOVES[ability_name]
        return execute_room_aoe(player, ability_name, aoe_mult, aoe_element, req_lvl)

    if player.mana < cost:
        return "INSUFFICIENT BUFFER (MANA)."

    player.mana -= cost
    player.save(update_fields=["mana", "karma"])

    res = f"You use {ability_name.upper()}."

    # Damage calculation helper
    def deal_dmg(mult, element="physical"):
        nonlocal res
        if not target:
            res += "\nTarget required."
            return
        if target.hp <= 0:
            # Already neutralized by an earlier hit in this combo -
            # never award EXP twice for the same kill.
            return

        # Calculate critical strike chance based on INT for spells, AGI for physical
        if element == "physical":
            crit_chance = min(10, max(1, player.agi_stat // 5))
        else:
            crit_chance = min(10, max(1, player.int_stat // 5))

        # Improved scaling logic
        # Scaling stats based on class primary attributes
        primary_stat = 10
        if player.game_class in ("Street Samurai", "Heavy"):
            primary_stat = player.str_stat
        elif player.game_class == "Jade Dragon":
            primary_stat = player.agi_stat
        elif player.game_class in ("Netrunner", "Techie"):
            primary_stat = player.int_stat
        elif player.game_class in ("Psycher", "Warlock"):
            primary_stat = player.int_stat
        elif player.game_class in ("Priest",):
            primary_stat = player.wil_stat
        elif player.game_class in ("Thief", "Ninja"):
            primary_stat = player.agi_stat
        elif player.game_class in ("Medie",):
            primary_stat = max(player.int_stat, player.hea_stat)
        elif player.game_class in ("Fixer", "Trickster"):
            primary_stat = player.cha_stat

        # Base power: primary stat influence + base attack influence
        power_val = (primary_stat * 1.5) + (player.attack * 0.5)

        # Scaling by ability requirement level (more advanced moves are inherently stronger)
        req_mult = 1.0 + (req_lvl / 20.0)

        final_atk = int(power_val * mult * req_mult)

        dmg, is_crit = calculate_damage(
            final_atk, target.defense, element=element, crit_chance=crit_chance
        )
        target.hp -= dmg

        if isinstance(target, Player):
            player.karma -= 2
            target.save(update_fields=["hp"])
            if is_crit:
                res += f"\n[CRIT] You hit {target.user.username} for {dmg} {element} damage!"
            else:
                res += f"\nYou hit {target.user.username} for {dmg} {element} damage."
            if target.hp <= 0:
                exp_gain = target.lvl * 50
                player.exp += exp_gain
                stolen = target.money // 4
                player.money += stolen
                player.save(update_fields=["exp", "money", "karma"])

                hub = Room.objects.get(id=1)
                target.hp = target.hp_max // 2
                target.money -= stolen
                target.location = hub
                target.save(update_fields=["hp", "money", "location"])
                res += f"\nYou neutralized {target.user.username}! "
                res += f"+{exp_gain} exp, +{stolen} CR."
        else:
            target.save(update_fields=["hp"])
            if is_crit:
                res += f"\n[CRIT] You hit {target.name} for {dmg} {element} damage!"
            else:
                res += f"\nYou hit {target.name} for {dmg} {element} damage."
            if target.hp <= 0:
                player.exp += target.exp_drop
                player.money += target.money_drop
                player.save(update_fields=["exp", "money"])
                res += (
                    f"\nTarget neutralized! +{target.exp_drop} exp, "
                    f"+{target.money_drop} credits."
                )
                for item in target.drops.all():
                    ii, created = InventoryItem.objects.get_or_create(player=player, item=item)
                    if not created:
                        ii.quantity += 1
                    ii.save()
                    res += f"\nRetrieved: {item.name}"
                res += check_level_up(player)
        return

    # Abilities Logic - High level mappings
    if ability_name == "blade":
        deal_dmg(1.2)
    elif ability_name == "oni_strike":
        deal_dmg(2.5, "fire")
    elif ability_name == "zansetsu":
        deal_dmg(3.0)
    elif ability_name == "mirage":
        buff = 20 + (player.agi_stat // 2)
        player.defense += buff
        player.save(update_fields=["defense"])
        res += "\nDefense boosted significantly."
    elif ability_name == "whirlwind":
        deal_dmg(1.5)
        deal_dmg(1.5)
    elif ability_name == "dragon_lunge":
        deal_dmg(4.0, "fire")
    elif ability_name == "omnislash":
        deal_dmg(2.0)
        deal_dmg(2.0)
        deal_dmg(2.0)
        deal_dmg(2.0)

    elif ability_name == "hack":
        deal_dmg(2.0, "water")
    elif ability_name == "overload":
        deal_dmg(2.5, "air")
    elif ability_name == "synapse_burn":
        deal_dmg(3.0, "fire")
    elif ability_name == "logic_bomb":
        deal_dmg(3.5, "air")
    elif ability_name == "blackout":
        if target:
            debuff = 10 + (player.int_stat // 3)
            target.attack = max(1, target.attack - debuff)
            target.defense = max(1, target.defense - debuff)
            target.save(update_fields=["attack", "defense"])
            res += "\nTarget systems crippled."
        else:
            res += "\nTarget required."
    elif ability_name == "databreach":
        if npc:
            stolen = random.randint(10, 50) + (player.int_stat // 2)
            player.money += stolen
            player.save(update_fields=["money"])
            res += f"\nSiphoned {stolen} credits!"
        deal_dmg(3.0, "water")
    elif ability_name == "zero_day":
        deal_dmg(10.0, "water")

    elif ability_name == "patch":
        heal = 20 + (player.int_stat * 2)
        player.hp = min(player.hp_max, player.hp + heal)
        player.save(update_fields=["hp"])
        res += "\nHealed HP."
    elif ability_name == "detox":
        player.addiction_points = max(0, player.addiction_points - 15 - (player.int_stat // 5))
        player.save(update_fields=["addiction_points"])
        res += "\nToxins cleared."
    elif ability_name == "heal":
        heal = 40 + (player.wil_stat * 2)
        player.hp = min(player.hp_max, player.hp + heal)
        player.save(update_fields=["hp"])
        res += "\nHealed HP."
    elif ability_name == "bless":
        buff = 10 + (player.wil_stat // 5)
        player.defense += buff
        player.attack += buff // 2
        player.save(update_fields=["defense", "attack"])
        res += "\nYou are blessed."

    # ── Advanced Class Moves (Lv 35-50) ──
    # Street Samurai
    elif ability_name == "ronin_wrath":
        if target:
            for _ in range(3):
                deal_dmg(2.2)
        else:
            res += "\nTarget required."
    elif ability_name == "blade_dance":
        if target:
            for _ in range(5):
                deal_dmg(1.6)
        else:
            res += "\nTarget required."
    elif ability_name == "ghost_edge":
        res += true_strike_damage(player, target, 2.6, "physical", req_lvl)
    elif ability_name == "shatter_soul":
        if target:
            deal_dmg(3.2, "fire")
            heal = int(player.hp_max * 0.15)
            player.hp = min(player.hp_max, player.hp + heal)
            player.save(update_fields=["hp"])
            res += f"\n[SOUL DRAIN] You absorb {heal} HP from the shattered soul."
        else:
            res += "\nTarget required."
    # Netrunner
    elif ability_name == "ice_wall":
        deal_dmg(2.0, "water")
        buff = 15 + (player.int_stat // 3)
        player.defense += buff
        player.save(update_fields=["defense"])
        res += f"\n[WALL] Ice barrier raised. Defense +{buff}."
    elif ability_name == "daemon_host":
        if target:
            deal_dmg(2.4, "air")
            drained = 10 + (player.int_stat // 2)
            if isinstance(target, Player):
                drained = min(drained, target.mana)
                target.mana = max(0, target.mana - drained)
                target.save(update_fields=["mana"])
            player.mana = min(player.mana_max, player.mana + drained // 2 + 5)
            player.save(update_fields=["mana"])
            res += f"\n[DAEMON] Possession siphons {drained} mana from the host."
        else:
            res += "\nTarget required."
    elif ability_name == "quantum_fracture":
        if target:
            deal_dmg(3.0, "air")
            deal_dmg(3.0, "air")
        else:
            res += "\nTarget required."
    # Techie
    elif ability_name == "drone_legion":
        if target:
            for _ in range(3):
                deal_dmg(1.8)
        else:
            res += "\nTarget required."
    elif ability_name == "emp_burst":
        if target:
            debuff = 10 + (player.int_stat // 3)
            target.attack = max(1, target.attack - debuff)
            target.save(update_fields=["attack"])
            res += f"\n[EMP] Weapon systems scrambled. Target ATK -{debuff}."
            deal_dmg(2.2, "air")
        else:
            res += "\nTarget required."
    elif ability_name == "rail_gun":
        res += true_strike_damage(player, target, 3.0, "physical", req_lvl)
    # Medie
    elif ability_name == "triage":
        heal = 40 + ((player.hea_stat + player.int_stat) * 2)
        player.hp = min(player.hp_max, player.hp + heal)
        player.mana = min(player.mana_max, player.mana + 10)
        player.save(update_fields=["hp", "mana"])
        res += f"\n[TRIAGE] Field surgery complete. +{heal} HP."
    elif ability_name == "immune_boost":
        buff = 10 + (player.hea_stat // 3)
        player.attack += buff
        player.defense += buff
        player.save(update_fields=["attack", "defense"])
        res += f"\n[BOOST] Immune response amplified. ATK/DEF +{buff}."
    elif ability_name == "leech_field":
        if target:
            deal_dmg(2.5, "water")
            heal = 15 + (player.hea_stat * 2)
            player.hp = min(player.hp_max, player.hp + heal)
            player.save(update_fields=["hp"])
            res += f"\n[LEECH] Drained vitality. +{heal} HP."
        else:
            res += "\nTarget required."
    elif ability_name == "phoenix_protocol":
        player.hp = player.hp_max
        player.mana = player.mana_max
        player.addiction_points = 0
        player.save(update_fields=["hp", "mana", "addiction_points"])
        res += "\n[PHOENIX] Nanomachine revival. Fully restored and purified."
    # Fixer
    elif ability_name == "insurance_fraud":
        if target:
            deal_dmg(2.2)
            loot = random.randint(20, 80) + (player.cha_stat * 2)
            player.money += loot
            player.save(update_fields=["money"])
            res += f"\n[FRAUD] The payout clears: +{loot} CR."
        else:
            res += "\nTarget required."
    elif ability_name == "dirty_cop":
        if target:
            debuff = 12 + (player.cha_stat // 3)
            target.defense = max(1, target.defense - debuff)
            target.save(update_fields=["defense"])
            res += f"\n[BRIBE] Security looks away. Target DEF -{debuff}."
            deal_dmg(1.8)
        else:
            res += "\nTarget required."
    elif ability_name == "union_strike":
        if target:
            deal_dmg(2.0)
            deal_dmg(2.0)
        else:
            res += "\nTarget required."
    elif ability_name == "corporate_war":
        if target:
            deal_dmg(3.5)
            loot = random.randint(100, 300) + (player.cha_stat * 3)
            player.money += loot
            player.save(update_fields=["money"])
            res += f"\n[WAR] Hostile buyout completes. Extracted {loot} CR."
        else:
            res += "\nTarget required."
    # Thief
    elif ability_name == "veil_step":
        if target:
            deal_dmg(1.8)
        else:
            res += "\nTarget required."
        player.hidden = True
        player.save(update_fields=["hidden"])
        res += "\n[VEIL] You slip back into the shadows, unseen."
    elif ability_name == "garrote":
        if target:
            if player.hidden:
                player.hidden = False
                player.save(update_fields=["hidden"])
                res += "\n[GARROTE] Strike from total silence!"
                deal_dmg(3.5)
            else:
                deal_dmg(2.2)
        else:
            res += "\nTarget required."
    elif ability_name == "shadow_clone":
        if target:
            for _ in range(3):
                deal_dmg(1.7)
        else:
            res += "\nTarget required."
    elif ability_name == "void_theft":
        if target:
            deal_dmg(2.8)
            loot = random.randint(30, 120) + (player.cha_stat * 2)
            if isinstance(target, Player):
                loot = min(loot, target.money)
                target.money = max(0, target.money - loot)
                target.save(update_fields=["money"])
            player.money += loot
            player.save(update_fields=["money"])
            player.hidden = True
            player.save(update_fields=["hidden"])
            res += f"\n[VOID] You vanish with {loot} CR into the void."
        else:
            res += "\nTarget required."
    # Heavy
    elif ability_name == "bulwark":
        buff = 25 + (player.hea_stat // 2) + (player.str_stat // 4)
        player.defense += buff
        player.save(update_fields=["defense"])
        res += f"\n[BULWARK] You plant the line. Defense +{buff}."
    elif ability_name == "wrecking_ball":
        deal_dmg(3.0)
    elif ability_name == "berserker_rage":
        buff = 15 + (player.str_stat // 3)
        cost_hp = max(1, int(player.hp_max * 0.1))
        player.attack += buff
        player.hp = max(1, player.hp - cost_hp)
        player.save(update_fields=["attack", "hp"])
        res += f"\n[RAGE] Fury at a price: ATK +{buff}, -{cost_hp} HP."
    # Psycher
    elif ability_name == "psychic_crush":
        deal_dmg(2.6, "air")
    elif ability_name == "astral_veil":
        buff = 12 + (player.int_stat // 3)
        player.hidden = True
        player.defense += buff
        player.save(update_fields=["hidden", "defense"])
        res += f"\n[ASTRAL] You project astrally: hidden, Defense +{buff}."
    elif ability_name == "mind_shatter":
        res += true_strike_damage(player, target, 3.2, "air", req_lvl)
    # Warlock
    elif ability_name == "hex_mark":
        if target:
            debuff = 12 + (player.int_stat // 3)
            target.attack = max(1, target.attack - debuff)
            target.defense = max(1, target.defense - debuff)
            target.save(update_fields=["attack", "defense"])
            res += f"\n[HEX] The mark rots their gear. Target ATK/DEF -{debuff}."
        else:
            res += "\nTarget required."
    elif ability_name == "infernal_pact":
        if target:
            cost_hp = max(1, int(player.hp_max * 0.12))
            player.hp = max(1, player.hp - cost_hp)
            player.save(update_fields=["hp"])
            res += f"\n[PACT] Blood price paid: -{cost_hp} HP."
            deal_dmg(3.4, "fire")
        else:
            res += "\nTarget required."
    elif ability_name == "abyssal_rift":
        if target:
            deal_dmg(3.0, "water")
            heal = int(player.hp_max * 0.12)
            player.hp = min(player.hp_max, player.hp + heal)
            player.save(update_fields=["hp"])
            res += f"\n[RIFT] The abyss feeds you: +{heal} HP."
        else:
            res += "\nTarget required."
    # Priest
    elif ability_name == "smite":
        deal_dmg(2.6, "fire")
    elif ability_name == "sanctuary":
        buff = 12 + (player.wil_stat // 3)
        heal = 20 + (player.wil_stat * 2)
        player.defense += buff
        player.hp = min(player.hp_max, player.hp + heal)
        player.save(update_fields=["defense", "hp"])
        res += f"\n[SANCTUARY] Consecrated ground: DEF +{buff}, +{heal} HP."
    elif ability_name == "resurrect":
        player.hp = player.hp_max
        player.mana = max(player.mana, player.mana_max // 2)
        player.addiction_points = 0
        player.save(update_fields=["hp", "mana", "addiction_points"])
        res += "\n[RESURRECT] Full system restoration. Toxins purged."
    elif ability_name == "rapture":
        player.hp = player.hp_max
        player.save(update_fields=["hp"])
        res += "\n[RAPTURE] You ascend briefly, fully renewed."
        if target:
            deal_dmg(2.4, "fire")
        else:
            res += "\nNo wicked target present."
    # Trickster
    elif ability_name == "loaded_dice":
        if target:
            roll = random.choice([1.5, 2.0, 2.5, 3.0, 3.5])
            res += f"\n[DICE] The weighted dice land... x{roll}!"
            deal_dmg(roll)
        else:
            res += "\nTarget required."
    elif ability_name == "puppet_string":
        if target:
            self_dmg = max(1, (target.attack - target.defense // 2) + player.cha_stat)
            t_name = target.name if isinstance(target, NPC) else target.user.username
            target.hp -= self_dmg
            target.save(update_fields=["hp"])
            res += f"\n[PUPPET] {t_name} is forced to strike itself for {self_dmg} damage!"
            if isinstance(target, Player):
                player.karma -= 2
                player.save(update_fields=["karma"])
                if target.hp <= 0:
                    res += award_player_kill(player, target)
            elif target.hp <= 0:
                res += award_npc_kill(player, target)
        else:
            res += "\nTarget required."
    elif ability_name == "coin_flip":
        if random.random() < 0.5:
            res += "\n[COIN] Heads! Brutal fortune."
            if target:
                deal_dmg(3.2)
            else:
                res += "\nTarget required."
        else:
            player.hp = player.hp_max
            player.save(update_fields=["hp"])
            res += "\n[COIN] Tails! Full mend."
    # Jade Dragon
    elif ability_name == "phoenix_wing":
        deal_dmg(2.8 * get_unarmed_mult(player), "fire")
    elif ability_name == "thousand_hands":
        if target:
            for _ in range(4):
                deal_dmg(1.5 * get_unarmed_mult(player))
        else:
            res += "\nTarget required."
    elif ability_name == "serpent_coil":
        if target:
            debuff = 10 + (player.agi_stat // 3)
            target.defense = max(1, target.defense - debuff)
            target.save(update_fields=["defense"])
            res += f"\n[COIL] Constricted! Target DEF -{debuff}."
            deal_dmg(2.0 * get_unarmed_mult(player))
        else:
            res += "\nTarget required."
    elif ability_name == "dragon_god_fist":
        if target:
            for _ in range(5):
                deal_dmg(2.0 * get_unarmed_mult(player))
        else:
            res += "\nTarget required."
    # Ninja
    elif ability_name == "smoke_screen":
        buff = 12 + (player.agi_stat // 3)
        player.hidden = True
        player.defense += buff
        player.save(update_fields=["hidden", "defense"])
        res += f"\n[SMOKE] You vanish in vapor. Hidden, Defense +{buff}."
    elif ability_name == "thousand_blades":
        if target:
            for _ in range(4):
                deal_dmg(1.6)
        else:
            res += "\nTarget required."
    elif ability_name == "forbidden_jutsu":
        if target:
            cost_hp = max(1, int(player.hp_max * 0.12))
            player.hp = max(1, player.hp - cost_hp)
            player.save(update_fields=["hp"])
            res += f"\n[FORBIDDEN] Blood price: -{cost_hp} HP."
            deal_dmg(3.4)
        else:
            res += "\nTarget required."
    elif ability_name == "tsukuyomi":
        res += true_strike_damage(player, target, 3.0, "air", req_lvl)

    # Generic keyword-based handlers for other moves
    elif any(
        x in ability_name
        for x in [
            "strike",
            "slash",
            "blade",
            "lunge",
            "storm",
            "whirlwind",
            "stab",
            "smash",
            "toss",
            "bolt",
            "burn",
            "plasma",
            "arc",
            "shock",
            "flare",
            "pulse",
            "assassinate",
            "judgment",
            "annihilation",
            "destruction",
            "armageddon",
        ]
    ):
        mult = 2.0 + (req_lvl / 15.0)
        elem = "physical"
        if any(x in ability_name for x in ["bolt", "pulse", "arc", "tesla"]):
            elem = "air"
        if any(x in ability_name for x in ["burn", "fire", "flare", "oni", "plasma", "armageddon"]):
            elem = "fire"
        if any(x in ability_name for x in ["seismic", "earth", "singularity", "dart", "nanobot"]):
            elem = "earth"
        if any(x in ability_name for x in ["hack", "water", "ice", "black", "zero", "siphon"]):
            elem = "water"
        deal_dmg(mult, elem)
    elif any(
        x in ability_name
        for x in [
            "boost",
            "shield",
            "iron",
            "protocol",
            "vanish",
            "smoke",
            "mirage",
            "image",
            "bless",
        ]
    ):
        stat_val = (
            player.int_stat
            if player.game_class == "Psycher"
            else (
                player.wil_stat
                if player.game_class == "Priest"
                else (player.agi_stat if player.game_class == "Thief" else player.hea_stat)
            )
        )
        buff = 10 + req_lvl + (stat_val // 2)
        player.defense += buff
        player.save(update_fields=["defense"])
        res += "\nDefense boosted."
    elif any(
        x in ability_name
        for x in ["heal", "patch", "purify", "restoration", "resuscitate", "regeneration"]
    ):
        stat_val = player.wil_stat if player.game_class == "Priest" else player.int_stat
        heal = 20 + req_lvl * 3 + (stat_val * 2)
        player.hp = min(player.hp_max, player.hp + heal)
        player.save(update_fields=["hp"])
        res += "\nHealed HP."
    elif ability_name == "soul_drain":
        if target:
            soul_stat = player.int_stat if player.game_class == "Psycher" else player.wil_stat
            dmg, _ = calculate_damage(int(soul_stat * 2.5), target.defense, element="water")
            target.hp -= dmg
            player.hp = min(player.hp_max, player.hp + dmg // 2)
            target.save(update_fields=["hp"])
            player.save(update_fields=["hp"])
            res += "\nDrained HP!"
        else:
            res += "\nTarget required."
    elif ability_name in ("scheme", "sleight_of_hand"):
        if npc:
            stolen = random.randint(1, 20) + player.cha_stat
            player.money += stolen
            player.save(update_fields=["money"])
            res += "\nDrained credits."
        else:
            res = "Requires NPC target."
    elif ability_name == "jackpot":
        if target:
            if random.random() > 0.5:
                dmg = int(player.cha_stat * 6)
                target.hp -= dmg
                target.save(update_fields=["hp"])
                res += "\nJACKPOT! Damage dealt!"
            else:
                loot = random.randint(50, 300) + (player.cha_stat * 2)
                player.money += loot
                player.save(update_fields=["money"])
                res += "\nJACKPOT! Credits siphoned!"
        else:
            res += "\nTarget required."
    # Jade Dragon abilities
    elif ability_name == "palm_strike":
        # Unarmed bonus: +50% damage if no weapon equipped
        unarmed_mult = (
            1.5
            if not InventoryItem.objects.filter(
                player=player, equipped=True, item__item_type="weapon"
            ).exists()
            else 1.0
        )
        deal_dmg(1.2 * unarmed_mult)
    elif ability_name == "crane_kick":
        unarmed_mult = (
            1.5
            if not InventoryItem.objects.filter(
                player=player, equipped=True, item__item_type="weapon"
            ).exists()
            else 1.0
        )
        deal_dmg(2.0 * unarmed_mult, "air")
    elif ability_name == "iron_palm":
        buff = 15 + (player.agi_stat // 3)
        player.defense += buff
        player.save(update_fields=["defense"])
        res += "\nYour chi hardens your body. Defense boosted."
    elif ability_name == "tiger_claw":
        unarmed_mult = (
            1.5
            if not InventoryItem.objects.filter(
                player=player, equipped=True, item__item_type="weapon"
            ).exists()
            else 1.0
        )
        deal_dmg(2.5 * unarmed_mult)
        deal_dmg(2.5 * unarmed_mult)
    elif ability_name == "dragon_kick":
        unarmed_mult = (
            1.5
            if not InventoryItem.objects.filter(
                player=player, equipped=True, item__item_type="weapon"
            ).exists()
            else 1.0
        )
        deal_dmg(4.0 * unarmed_mult, "fire")
    elif ability_name == "chi_burst":
        deal_dmg(3.5, "air")
    elif ability_name == "jade_ascension":
        unarmed_mult = (
            1.5
            if not InventoryItem.objects.filter(
                player=player, equipped=True, item__item_type="weapon"
            ).exists()
            else 1.0
        )
        deal_dmg(2.5 * unarmed_mult)
        deal_dmg(2.5 * unarmed_mult)
        deal_dmg(2.5 * unarmed_mult)
        deal_dmg(2.5 * unarmed_mult)
    elif ability_name == "bamboozle":
        if target:
            debuff = 15 + (player.cha_stat // 3)
            target.defense = max(1, target.defense - debuff)
            target.save(update_fields=["defense"])
            res += "\nTarget bamboozled!"
        else:
            res += "\nTarget required."
    # Ninja abilities
    elif ability_name == "kunai_throw":
        # High crit from stealth
        deal_dmg(1.5, "physical")
    elif ability_name == "shadow_step":
        # Teleport behind target for backstab bonus
        if target:
            player.hidden = True
            player.save(update_fields=["hidden"])
            res += "\nYou vanish and reappear behind your target!"
            # Then deal backstab damage
            deal_dmg(2.0)
        else:
            res += "\nTarget required."
    elif ability_name == "chakra_dart":
        # Multiple chakra-infused projectiles
        for _ in range(3):
            deal_dmg(1.0, "air")
    elif ability_name == "phantom_sweep":
        # Area attack - hit all enemies in room
        npcs = NPC.objects.filter(location=player.location, hp__gt=0)
        players_here = Player.objects.filter(location=player.location, online=True).exclude(
            id=player.id
        )
        for npc_obj in npcs:
            deal_dmg(1.2, "physical")
        for p in players_here:
            if p.lvl >= 5 and abs(player.lvl - p.lvl) <= 4:
                deal_dmg(1.2, "physical")
    elif ability_name == "rasengan":
        # Spiral energy sphere - massive damage
        deal_dmg(4.0, "air")
    elif ability_name == "throw":
        # Ninja throw ability - destroy weapon to deal 3x its damage
        if target:
            # Find weapon in inventory (not equipped)
            weapon_ii = InventoryItem.objects.filter(
                player=player, item__item_type="weapon"
            ).first()
            if weapon_ii:
                weapon = weapon_ii.item
                # Calculate damage: 3x weapon's attack bonus
                throw_dmg = weapon.attack_bonus * 3
                # Add player's AGI for scaling
                throw_dmg += player.agi_stat

                # Apply damage to target
                target.hp -= throw_dmg
                target.save(update_fields=["hp"])

                # Destroy the weapon
                if weapon_ii.quantity > 1:
                    weapon_ii.quantity -= 1
                    weapon_ii.save()
                else:
                    weapon_ii.delete()

                target_name_str = target.user.username if target_player else target.name
                res += f"\nYou hurl {weapon.name} at {target_name_str}!"
                res += f"\n[THROW] {throw_dmg} damage! Weapon destroyed."

                if target.hp <= 0:
                    if target_player:
                        exp_gain = target.lvl * 50
                        player.exp += exp_gain
                        stolen = target.money // 4
                        player.money += stolen
                        player.save(update_fields=["exp", "money"])
                        hub = Room.objects.get(id=1)
                        target.hp = target.hp_max // 2
                        target.money -= stolen
                        target.location = hub
                        target.save(update_fields=["hp", "money", "location"])
                        res += f"\nYou neutralized {target.user.username}! "
                        res += f"+{exp_gain} exp, +{stolen} CR."
                    else:
                        player.exp += target.exp_drop
                        player.money += target.money_drop
                        player.save(update_fields=["exp", "money"])
                        res += f"\nTarget neutralized! +{target.exp_drop} exp, "
                        res += f"+{target.money_drop} credits."
                        for item in target.drops.all():
                            ii, created = InventoryItem.objects.get_or_create(
                                player=player, item=item
                            )
                            if not created:
                                ii.quantity += 1
                            ii.save()
                            res += f"\nRetrieved: {item.name}"
                        res += check_level_up(player)
            else:
                res += "\nNo weapon in inventory to throw."
        else:
            res += "\nTarget required."
    else:
        # Fallback for anything else in CLASS_MOVES
        deal_dmg(1.5 + (req_lvl / 15.0))

    if npc and npc.hp > 0:
        npc_dmg, _ = calculate_damage(npc.attack, player.defense, element=npc.element)
        player.hp -= npc_dmg
        player.save(update_fields=["hp"])
        res += f"\n{npc.name} counters for {npc_dmg} damage!"

    return res


def use_item(player, item_name):
    if not item_name:
        return "Use what?"
    ii = InventoryItem.objects.filter(player=player, item__name__icontains=item_name).first()
    if not ii:
        return "Not in inventory."

    item = ii.item
    output = f"You use {item.name}."

    if item.item_type == "consumable":
        if item.heal_amount > 0:
            player.hp = min(player.hp_max, player.hp + item.heal_amount)
            output += "\nHealed HP."
    elif item.item_type == "drug":
        player.str_stat += item.str_bonus
        player.int_stat += item.int_bonus
        player.wil_stat += item.wil_bonus
        player.agi_stat += item.agi_bonus
        player.hea_stat += item.hea_bonus
        player.cha_stat += item.cha_bonus

        player.attack += item.str_bonus * 2
        player.defense += item.agi_bonus
        player.hp_max += item.hea_bonus * 10
        player.mana_max += item.int_bonus * 5

        player.hp = min(player.hp_max, player.hp + 20)
        player.withdrawal_timer = 0
        if random.random() < item.addiction_chance:
            player.addiction_points += 20
            output += "\n[DANGER] Neuro-dependency increased."
        output += "\nNeural spike detected. Systems modified."

    elif item.item_type == "scroll":
        target_room = item.warp_to_room or Room.objects.get(id=1)
        player.location = target_room
        player.save(update_fields=["location"])
        return output + (
            f"\n[TELEPORT] Transferred to {player.location.name}.\n" + get_look(player)
        )

    ii.quantity -= 1
    if ii.quantity <= 0:
        ii.delete()
    else:
        ii.save()
    player.save(update_fields=[
        "hp", "mana", "str_stat", "int_stat", "wil_stat", "agi_stat", "hea_stat", "cha_stat",
        "attack", "defense", "hp_max", "mana_max", "addiction_points", "withdrawal_timer"
    ])
    return output


def train_stat(player, stat):
    if player.stat_points <= 0:
        return "You have no stat points to spend."

    stat = stat.upper()
    if stat == "STR":
        player.str_stat += 1
        player.attack += 2
    elif stat == "INT":
        player.int_stat += 1
        player.mana_max += 5
    elif stat == "WIL":
        player.wil_stat += 1
        player.mana_max += 5
    elif stat == "AGI":
        player.agi_stat += 1
        player.defense += 1
    elif stat == "HEA":
        player.hea_stat += 1
        player.hp_max += 10
    elif stat == "CHA":
        player.cha_stat += 1
    else:
        return "Invalid stat. Choose STR, INT, WIL, AGI, HEA, or CHA."

    player.stat_points -= 1
    player.save(update_fields=[
        "str_stat", "int_stat", "wil_stat", "agi_stat", "hea_stat", "cha_stat",
        "attack", "defense", "hp_max", "mana_max", "stat_points"
    ])
    return f"You trained {stat}. Points remaining: {player.stat_points}"


def get_map_data(player):
    room = player.location
    if not room:
        return "[]"
    visited = set()
    to_visit = [(room, 0)]
    room_data = []
    while to_visit:
        r, depth = to_visit.pop(0)
        if r.id in visited or depth > 4:
            continue
        visited.add(r.id)
        # Batch query player counts for all rooms at once
        player_counts = {
            p["location_id"]: p["count"]
            for p in Player.objects.filter(
                location_id__in=[r.id for r in Room.objects.filter(pk__in=visited)]
            )
            .exclude(id=player.id)
            .values("location_id")
            .annotate(count=models.Count("id"))
        }
        room_data.append(
            {
                "id": r.id,
                "name": r.name,
                "x": r.map_x,
                "y": r.map_y,
                "current": (r.id == room.id),
                "players": Player.objects.filter(location=r, online=True)
                .exclude(id=player.id)
                .exclude(is_bot=True)
                .count(),
                "bots": Player.objects.filter(location=r, online=True, is_bot=True)
                .exclude(id=player.id)
                .count(),
                "npcs": NPC.objects.filter(location=r, hp__gt=0).count(),
                "safe": r.safe_zone,
            }
        )
        for rid in r.exits.values():
            try:
                nr = Room.objects.get(id=rid)
                if nr.id not in visited:
                    to_visit.append((nr, depth + 1))
            except Room.DoesNotExist:
                pass
    return json.dumps(room_data)


def get_status_detailed(player):
    sb = [f"\n=== User Profile: {player.user.username} ==="]
    sb.append(f"Level: {player.lvl}")
    sb.append(
        f"Credits: {player.money} | Stat Points: {player.stat_points} | "
        f"Karma: {player.karma} ({get_reputation_title(player.karma)})"
    )
    sb.append(f"Path (Race): {player.race} | Class: {player.game_class}")
    race_char = RACE_CHARACTERISTICS.get(player.race, "")
    if race_char:
        sb.append(f"Race Trait: {race_char}")
    if player.addiction_points > 0:
        sb.append(f"ADDICTION: {player.addiction_points}%")

    sb.append("\nBiological & Cybernetic Data:")
    sb.append(f"  Strength:  {player.str_stat:2} ({get_attribute_desc('str', player.str_stat)})")
    sb.append(f"  Agility:   {player.agi_stat:2} ({get_attribute_desc('agi', player.agi_stat)})")
    sb.append(f"  Intellect: {player.int_stat:2} ({get_attribute_desc('int', player.int_stat)})")
    sb.append(f"  Willpower: {player.wil_stat:2} ({get_attribute_desc('wil', player.wil_stat)})")
    sb.append(f"  Health:    {player.hea_stat:2} ({get_attribute_desc('hea', player.hea_stat)})")
    sb.append(f"  Charm:     {player.cha_stat:2} ({get_attribute_desc('cha', player.cha_stat)})")

    # Show equipped weapon
    equipped_weapon = InventoryItem.objects.filter(
        player=player, equipped=True, item__item_type="weapon"
    ).select_related("item").first()
    if equipped_weapon:
        sb.append(f"\nEquipped Weapon: {equipped_weapon.item.name}")

    sb.append("\nCombat Assessment:")
    sb.append(f"  ATK: {player.attack:2} | DEF: {player.defense:2}")
    sb.append(f"  {get_combat_desc(player.attack, player.defense, is_self=True)}")

    sb.append("\nLearned Moves:")
    moves = CLASS_MOVES.get(player.game_class, [])
    found = False
    for lvl, name, acronym, desc in moves:
        if player.lvl >= lvl:
            sb.append(f"  {name.upper():15} ({acronym}): {desc}")
            found = True
    if not found:
        sb.append("  None")

    sb.append("\nPersonal Narrative Assessment:")
    sb.append(get_procedural_desc(player, viewer=player))

    return "\n".join(sb)


def check_level_up(player):
    output = ""
    while player.exp >= player.lvl * 120:
        player.exp -= player.lvl * 120
        player.lvl += 1
        player.stat_points += 1
        player.hp_max += 20
        player.hp = player.hp_max
        player.mana_max += 10
        player.mana = player.mana_max
        player.save(update_fields=["exp", "lvl", "stat_points", "hp_max", "hp", "mana_max", "mana"])
        output += f"\n*** LEVEL UP! Now level {player.lvl}! ***"
        output += "\nGranted 1 stat point. Use TRAIN <stat> to spend it."

        # Notify about new moves
        moves = CLASS_MOVES.get(player.game_class, [])
        for lvl, name, acronym, _ in moves:
            if player.lvl == lvl:
                output += f"\n[SYSTEM] New move unlocked: {name.upper()} ({acronym})!"

        if player.lvl == 5:
            output += "\n[NEW ABILITIES UNLOCKED! Type HELP for details]"
            output += "\n[ALERT] NPC AGGRESSION PROTOCOLS ACTIVATED."
    return output


def handle_say(player, message):
    if not message:
        return "Say what?"
    ChatMessage.objects.create(sender=player, room=player.location, message=message)
    return f"You say: {message}"


def handle_broadcast(player, message):
    if not message:
        return "Broadcast what?"
    ChatMessage.objects.create(sender=player, room=None, message=message)
    return f"You broadcast to the world: {message}"


def get_recent_chat(player):
    cutoff = timezone.now() - timezone.timedelta(seconds=30)
    # Get room messages or world messages
    msgs = (
        ChatMessage.objects.filter(Q(room=player.location) | Q(room=None), timestamp__gt=cutoff)
        .exclude(sender=player)
        .order_by("timestamp")
    )
    if not msgs:
        return ""

    chat_lines = []
    for m in msgs:
        label = "[Local]" if m.room else "[Global]"
        chat_lines.append(f"{label} {m.sender.user.username}: {m.message}")
    return "\n".join(chat_lines)


def get_inventory(player):
    items = InventoryItem.objects.filter(player=player).select_related("item")
    if not items.exists():
        return "Memory slots empty."
    sb = ["\n=== Hardware Inventory ==="]
    for ii in items:
        eq = " [E]" if ii.equipped else ""
        qty = f" x{ii.quantity}" if ii.quantity > 1 else ""
        sb.append(f"  {ii.item.name}{qty}{eq} ({ii.item.subtype})")
    return "\n".join(sb)


def get_item(player, item_name):
    if not item_name:
        return "Get what?"
    item = player.location.items.filter(name__icontains=item_name).first()
    if not item:
        return "Item not found."
    player.location.items.remove(item)
    ii, created = InventoryItem.objects.get_or_create(player=player, item=item)
    if not created:
        ii.quantity += 1
    ii.save()
    return f"Retrieved {item.name}."


def drop_item(player, item_name):
    if not item_name:
        return "Drop what?"
    ii = InventoryItem.objects.filter(player=player, item__name__icontains=item_name).first()
    if not ii:
        return "You don't have that."
    if ii.equipped:
        return "Unequip first."
    player.location.items.add(ii.item)
    name = ii.item.name
    if ii.quantity > 1:
        ii.quantity -= 1
        ii.save()
    else:
        ii.delete()
    return f"Discarded {name}."


def equip_item(player, item_name):
    if not item_name:
        return "Equip what?"
    ii = InventoryItem.objects.filter(player=player, item__name__icontains=item_name).first()
    if not ii:
        return "Not in inventory."

    if ii.equipped:
        ii.equipped = False
        player.attack -= ii.item.attack_bonus
        player.defense -= ii.item.defense_bonus
        player.str_stat -= ii.item.str_bonus
        player.int_stat -= ii.item.int_bonus
        player.wil_stat -= ii.item.wil_bonus
        player.agi_stat -= ii.item.agi_bonus
        player.hea_stat -= ii.item.hea_bonus
        player.cha_stat -= ii.item.cha_bonus
        ii.save(update_fields=["equipped"])
        player.save(update_fields=["attack", "defense", "str_stat", "int_stat", "wil_stat", "agi_stat", "hea_stat", "cha_stat"])
        return f"Unequipped {ii.item.name}."

    # Check restrictions
    if ii.item.item_type in ["weapon", "armor"]:
        limits = GEAR_LIMITS.get(player.game_class)
        if limits:
            allowed_subtypes = limits.get(ii.item.item_type, [])
            if allowed_subtypes and ii.item.subtype not in allowed_subtypes:
                allowed_str = ", ".join(allowed_subtypes)
                return (
                    f"Incompatible hardware. {player.game_class} can only equip "
                    f"{allowed_str} {ii.item.item_type}s."
                )

    if ii.item.item_type == "weapon":
        old = InventoryItem.objects.filter(
            player=player, equipped=True, item__item_type="weapon"
        ).select_related("item").first()
        if old:
            player.attack -= old.item.attack_bonus
            player.str_stat -= old.item.str_bonus
            player.int_stat -= old.item.int_bonus
            player.wil_stat -= old.item.wil_bonus
            player.agi_stat -= old.item.agi_bonus
            player.hea_stat -= old.item.hea_bonus
            player.cha_stat -= old.item.cha_bonus
            old.equipped = False
            old.save(update_fields=["equipped"])
    elif ii.item.item_type == "armor":
        old = InventoryItem.objects.filter(
            player=player, equipped=True, item__item_type="armor"
        ).select_related("item").first()
        if old:
            player.defense -= old.item.defense_bonus
            player.str_stat -= old.item.str_bonus
            player.int_stat -= old.item.int_bonus
            player.wil_stat -= old.item.wil_bonus
            player.agi_stat -= old.item.agi_bonus
            player.hea_stat -= old.item.hea_bonus
            player.cha_stat -= old.item.cha_bonus
            old.equipped = False
            old.save(update_fields=["equipped"])

    ii.equipped = True
    player.attack += ii.item.attack_bonus
    player.defense += ii.item.defense_bonus
    player.str_stat += ii.item.str_bonus
    player.int_stat += ii.item.int_bonus
    player.wil_stat += ii.item.wil_bonus
    player.agi_stat += ii.item.agi_bonus
    player.hea_stat += ii.item.hea_bonus
    player.cha_stat += ii.item.cha_bonus
    ii.save(update_fields=["equipped"])
    player.save(update_fields=["attack", "defense", "str_stat", "int_stat", "wil_stat", "agi_stat", "hea_stat", "cha_stat"])
    return f"Equipped {ii.item.name}."


def list_shop(player):
    if not player.location.shop_name:
        return "No terminal shop detected."

    if player.location.shop_inventory.exists():
        items = player.location.shop_inventory.all().order_by("item_type", "name")
    else:
        # Default shops only sell common and uncommon items
        items = (
            Item.objects.filter(price__gt=0)
            .exclude(rarity__in=["rare", "epic", "legendary"])
            .order_by("item_type", "name")
        )

    sb = [f"\n=== {player.location.shop_name} Inventory ==="]

    current_type = None
    for item in items:
        if item.item_type != current_type:
            current_type = item.item_type
            sb.append(f"\n[{current_type.upper()}]")
        sb.append(f"  {item.name:25} ({item.subtype:10}) {item.price} CR")
    return "\n".join(sb)


def buy_item(player, item_name):
    if not player.location.shop_name:
        return "No shop here."

    if player.location.shop_inventory.exists():
        item = player.location.shop_inventory.filter(name__icontains=item_name, price__gt=0).first()
    else:
        item = (
            Item.objects.filter(name__icontains=item_name, price__gt=0)
            .exclude(rarity__in=["rare", "epic", "legendary"])
            .first()
        )

    if not item:
        return "Item not in database or unavailable at this terminal."
    if player.money < item.price:
        return "Insufficient credits."
    player.money -= item.price
    player.save(update_fields=["money"])
    ii, created = InventoryItem.objects.get_or_create(player=player, item=item)
    if not created:
        ii.quantity += 1
        ii.save()
    return f"Purchased {item.name}."


def sell_item(player, item_name):
    # Selling to shop or NPC dealer
    target_npc = None
    if " to " in item_name.lower():
        parts = item_name.lower().split(" to ")
        item_name = parts[0].strip()
        npc_name = parts[1].strip()
        target_npc = NPC.objects.filter(
            location=player.location, name__icontains=npc_name, hp__gt=0
        ).first()
        if not target_npc:
            return f"Target '{npc_name}' not found."

    ii = InventoryItem.objects.filter(player=player, item__name__icontains=item_name).first()
    if not ii:
        return "You don't have that."
    if ii.equipped:
        return "Unequip first."

    if target_npc:
        if target_npc.npc_type == "dealer" and ii.item.item_type == "drug":
            price = int(ii.item.price * 1.2)  # Dealers pay more for drugs
            player.money += price
            player.karma -= 5  # Selling drugs is significantly bad
            player.save(update_fields=["money", "karma"])
            name = ii.item.name
            if ii.quantity > 1:
                ii.quantity -= 1
                ii.save()
            else:
                ii.delete()
            return f"Sold {name} to {target_npc.name} for {price} credits. [Karma -5]"
        return f"{target_npc.name} doesn't want that."

    if not player.location.shop_name:
        return "No shop here to sell to."

    price = ii.item.price // 2
    player.money += price
    player.save(update_fields=["money"])
    name = ii.item.name
    if ii.quantity > 1:
        ii.quantity -= 1
        ii.save()
    else:
        ii.delete()
    # Add sold item to shop inventory
    player.location.shop_inventory.add(ii.item)
    return f"Sold {name} for {price} credits."


def sell_all_items(player):
    """Sell all unequipped items in the player's inventory to the current shop."""
    if not player.location.shop_name:
        return "No shop here to sell to."

    unequipped = InventoryItem.objects.filter(player=player, equipped=False)
    if not unequipped.exists():
        return "No unequipped items to sell."

    total_credits = 0
    sold_count = 0
    sold_names = []

    for ii in unequipped:
        price = ii.item.price // 2
        total_credits += price * ii.quantity
        sold_count += ii.quantity
        sold_names.append(ii.item.name)
        # Add sold item to shop inventory
        player.location.shop_inventory.add(ii.item)
        ii.delete()

    player.money += total_credits
    player.save(update_fields=["money"])

    names_str = ", ".join(sold_names[:5])
    extra = f" and {len(sold_names) - 5} more" if len(sold_names) > 5 else ""
    return (
        f"Sold {sold_count} item(s) ({names_str}{extra}) for {total_credits} credits."
    )


def generate_random_weapon(zone):
    """Generate a procedurally spawned weapon with random stat bonuses/penalties."""
    # Weapon name components
    prefixes = [
        "Glitched",
        "Corrupted",
        "Enhanced",
        "Mutated",
        "Volatile",
        "Unstable",
        "Charged",
        "Infused",
        "Tainted",
        "Blessed",
        "Cursed",
        "Radiant",
        "Dark",
        "Quantum",
        "Neural",
        "Cyber",
        "Void",
        "Chaos",
        "Harmonic",
        "Resonant",
    ]

    weapon_types = [
        "Blade",
        "Cutter",
        "Driver",
        "Piercer",
        "Crusher",
        "Striker",
        "Launcher",
        "Emitter",
        "Projector",
        "Rifle",
        "Pistol",
        "Cannon",
        "Gauntlet",
        "Claw",
        "Sword",
        "Axe",
        "Mace",
        "Spear",
        "Dagger",
        "Fist",
    ]

    suffixes = [
        "of Pain",
        "of Speed",
        "of Power",
        "of Shadows",
        "of Light",
        "of Chaos",
        "of Order",
        "of the Grid",
        "of the Void",
        "of the Street",
        "of the Corp",
        "of the Net",
        "of the Wastes",
        "of the Neon",
        "of the Deep",
    ]

    # Generate name with uniqueness guarantee
    max_attempts = 50
    for _ in range(max_attempts):
        if random.random() < 0.6:  # 60% chance for prefix
            name = f"{random.choice(prefixes)} {random.choice(weapon_types)}"
        else:
            name = random.choice(weapon_types)

        if random.random() < 0.4:  # 40% chance for suffix
            name += f" {random.choice(suffixes)}"

        # Check if this name already exists
        if not Item.objects.filter(name=name).exists():
            break
    else:
        # If we couldn't find a unique name, add a random number suffix
        name = f"{name} {random.randint(100, 999)}"

    # Random stats
    attack_bonus = random.randint(5, 25)
    speed_bonus = random.randint(-5, 10)

    # Random stat bonuses (1-3 stats affected)
    stat_bonuses = {}
    num_bonuses = random.randint(1, 3)
    available_stats = ["str_bonus", "int_bonus", "wil_bonus", "agi_bonus", "hea_bonus", "cha_bonus"]

    for _ in range(num_bonuses):
        stat = random.choice(available_stats)
        available_stats.remove(stat)
        # Can be positive or negative (sagging stats)
        bonus = random.randint(-5, 8)
        stat_bonuses[stat] = bonus

    # Determine rarity based on total power
    total_power = attack_bonus + sum(stat_bonuses.values())
    if total_power > 20:
        rarity = "rare"
    elif total_power > 12:
        rarity = "uncommon"
    else:
        rarity = "common"

    # Price based on power
    price = max(50, total_power * 30)

    # Create description
    desc_parts = [f"A procedurally generated weapon from {zone}."]
    if attack_bonus > 15:
        desc_parts.append("It hums with dangerous energy.")
    elif attack_bonus > 10:
        desc_parts.append("It feels balanced and deadly.")
    else:
        desc_parts.append("It looks serviceable.")

    # Add stat description
    positive_bonuses = [k.replace("_bonus", "").upper() for k, v in stat_bonuses.items() if v > 0]
    negative_bonuses = [k.replace("_bonus", "").upper() for k, v in stat_bonuses.items() if v < 0]

    if positive_bonuses:
        desc_parts.append(f"Boosts: {', '.join(positive_bonuses)}.")
    if negative_bonuses:
        desc_parts.append(f"Sags: {', '.join(negative_bonuses)}.")

    description = " ".join(desc_parts)

    # Create the item
    item = Item.objects.create(
        name=name,
        description=description,
        item_type="weapon",
        attack_bonus=attack_bonus,
        speed_bonus=speed_bonus,
        rarity=rarity,
        price=price,
        subtype=random.choice(["one-handed", "two-handed"]),
        **stat_bonuses,
    )

    return item


# Cache for last procedural weapon spawn check time
_last_procedural_spawn_check = None


def check_procedural_weapon_spawns():
    """Check all zones and spawn new weapons if 30 minutes have passed since last spawn.
    Uses module-level cache to avoid repeated checks across multiple poll requests."""
    global _last_procedural_spawn_check
    
    now = timezone.now()
    
    # Only check once every 60 seconds regardless of how many users poll
    if _last_procedural_spawn_check is not None:
        if (now - _last_procedural_spawn_check).total_seconds() < 60:
            return []
    
    _last_procedural_spawn_check = now
    
    zones = [
        "slums",
        "industrial",
        "corporate",
        "undergrid",
        "neon",
        "wastes",
        "nexus",
        "undercity",
    ]

    spawned_weapons = []

    for zone in zones:
        # Get the most recent spawn for this zone
        last_spawn = ProceduralWeaponSpawn.objects.filter(zone=zone).order_by("-spawned_at").first()

        # If no spawn exists, or last spawn was more than 30 minutes ago
        if not last_spawn or (now - last_spawn.spawned_at).total_seconds() >= 1800:
            # Get a random room in this zone (not hub, not safe zone)
            zone_rooms = list(Room.objects.filter(zone=zone, safe_zone=False))

            if zone_rooms:
                spawn_room = random.choice(zone_rooms)

                # Generate a new weapon
                weapon = generate_random_weapon(zone)

                # Add it to the room
                spawn_room.items.add(weapon)

                # Record the spawn
                ProceduralWeaponSpawn.objects.create(zone=zone, room=spawn_room, item=weapon)

                spawned_weapons.append(
                    {"zone": zone, "room": spawn_room.name, "weapon": weapon.name}
                )

    return spawned_weapons


def bot_auto_equip(bot, item):
    """Equip dropped/bought loot if it upgrades the bot's current gear.
    Mirrors equip_item's stat adjustments. Returns True if equipped."""
    if item.item_type not in ("weapon", "armor"):
        return False
    limits = GEAR_LIMITS.get(bot.game_class, {})
    if item.item_type == "weapon":
        allowed = limits.get("weapon")
        current = (
            InventoryItem.objects.filter(
                player=bot, equipped=True, item__item_type="weapon"
            )
            .select_related("item")
            .first()
        )
        better = not current or item.attack_bonus > current.item.attack_bonus
    else:
        allowed = limits.get("armor")
        current = (
            InventoryItem.objects.filter(
                player=bot, equipped=True, item__item_type="armor"
            )
            .select_related("item")
            .first()
        )
        better = not current or item.defense_bonus > current.item.defense_bonus

    if not better or (allowed and item.subtype not in allowed):
        return False

    # Unequip the old piece (removing its stat bonuses)
    if current:
        old = current.item
        bot.attack -= old.attack_bonus
        bot.defense -= old.defense_bonus
        bot.str_stat -= old.str_bonus
        bot.int_stat -= old.int_bonus
        bot.wil_stat -= old.wil_bonus
        bot.agi_stat -= old.agi_bonus
        bot.hea_stat -= old.hea_bonus
        bot.cha_stat -= old.cha_bonus
        current.equipped = False
        current.save(update_fields=["equipped"])

    ii, _created = InventoryItem.objects.get_or_create(player=bot, item=item)
    ii.equipped = True
    ii.save(update_fields=["equipped"])
    bot.attack += item.attack_bonus
    bot.defense += item.defense_bonus
    bot.str_stat += item.str_bonus
    bot.int_stat += item.int_bonus
    bot.wil_stat += item.wil_bonus
    bot.agi_stat += item.agi_bonus
    bot.hea_stat += item.hea_bonus
    bot.cha_stat += item.cha_bonus
    bot.save(
        update_fields=[
            "attack",
            "defense",
            "str_stat",
            "int_stat",
            "wil_stat",
            "agi_stat",
            "hea_stat",
            "cha_stat",
        ]
    )
    return True


def bot_try_use_ability(bot, target_name):
    """Have a bot cast one of its learned class moves at its target so bots
    actually level up like players. Returns True if an ability was attempted."""
    if bot.mana < 8:
        return False
    learned = []
    for lvl, name, _acr, _desc in CLASS_MOVES.get(bot.game_class, []):
        if lvl > bot.lvl or name in ("stealth", "sneak"):
            continue
        if bot.mana >= 5 + (lvl // 2):
            learned.append(name)
    if not learned:
        return False
    move_name = random.choice(learned)
    use_ability(bot, move_name, target_name)
    touch_player_activity(bot)
    return True


def process_bot_ai(bot):
    """Process AI behavior for bot players. Called during polling or by process_bots command."""
    if not bot.is_bot or not bot.online:
        return ""

    # Process combat tick for bots in combat (auto-attack continues)
    if bot.last_combat_npc or bot.last_combat_player:
        process_combat_tick(bot)
        return ""

    # Bots resting now actually RECOVER. (Previously they rested forever
    # unless a human was polling their room - leaving them stuck in place.)
    if bot.resting:
        process_resting(bot)
        return ""

    # Only act every 10-30 seconds (using persistent database field)
    now = timezone.now()
    if bot.last_bot_action:
        time_since_last = (now - bot.last_bot_action).total_seconds()
        if time_since_last < random.randint(10, 30):
            return ""

    # Update last action time (acting = not AFK)
    bot.last_bot_action = now
    bot.save(update_fields=["last_bot_action"])
    touch_player_activity(bot)

    # AI Decision Making
    room = bot.location
    if not room:
        return ""

    # Check if bot should rest (low HP) - but NOT if in combat
    if bot.hp < bot.hp_max * 0.3 and not bot.last_combat_npc and not bot.last_combat_player:
        rest_command(bot)
        return ""  # Bot is now resting or already resting

    # Look for targets in current room
    npcs = NPC.objects.filter(location=room, hp__gt=0)
    players_here = Player.objects.filter(location=room, online=True).exclude(id=bot.id)

    # Find a target (only if not in safe zone)
    target_npc = None
    target_player = None

    if not room.safe_zone:
        # Attack players within 4 levels based on bot aggression trait
        if not target_npc and not target_player:
            for p in players_here:
                if abs(bot.lvl - p.lvl) <= 4:
                    # Aggressive bots attack anyone; others attack based on karma
                    if bot.bot_aggression > 60 or p.karma < -20:
                        target_player = p
                        break

        # Priority 3: Attack nearby NPCs (any NPC within level range, not just aggressive)
        if not target_npc and not target_player:
            if npcs.exists():
                valid_npcs = [n for n in npcs if abs(n.lvl - bot.lvl) <= 5]
                if valid_npcs:
                    target_npc = random.choice(valid_npcs)

    # Execute combat (without broadcasting to players - bots fight silently)
    if target_npc or target_player:
        target_name = target_npc.name if target_npc else target_player.user.username
        # Mix class abilities into the fight (~35% of engagements) so bots
        # actually fight like players and gain EXP/levels.
        if random.random() < 0.35 and bot_try_use_ability(bot, target_name):
            return ""
        attack_target(bot, target_name, auto=True)
        return ""

    # Party behavior: invite players if social enough
    if bot.bot_social > 60 and not bot.parties.exists() and players_here.exists():
        for p in players_here:
            if abs(bot.lvl - p.lvl) <= 4 and not p.parties.exists():
                invite_to_party(bot, p.user.username)
                break

    # Random chat/say to players in room
    if players_here.exists() and random.random() < 0.15:  # 15% chance to say something
        if bot.karma < -30:
            taunts = [
                "You're gonna die in the gutter, choom.",
                "Pathetic. I'll scrap you for parts.",
                "Your blood will look good on my chrome.",
                "I've killed better players before breakfast.",
                "Run along, meat. This sector's mine.",
                "You smell like weakness.",
                "I'll turn your corpse into street art.",
                "Hope you got your affairs in order, fool.",
                "You're just another corpse waiting to happen.",
                "I'll gut you and sell your organs.",
                "Your screams will echo in the wastes.",
                "I've got a special place in my kill list for you.",
            ]
            message = random.choice(taunts)
        else:
            greetings = [
                "Hey there, choom.",
                "Watch your back in this sector.",
                "Looking for a party?",
                "Stay frosty.",
                "The grid's been weird lately.",
                "Heard there's good loot in the wastes.",
                "Beware the corporate enforcers.",
                "Need a heal? I'm a Medie.",
                "Let's wreck some drones.",
                "Karma's a bitch, watch yours.",
            ]
            message = random.choice(greetings)
        ChatMessage.objects.create(sender=bot, room=room, message=message)

    # Pick up items from the ground and EQUIP any upgrades
    # (bots used to hoard loot without ever using it)
    if room.items.exists() and random.random() < 0.5:  # 50% chance to pick up
        item = room.items.first()
        if item:
            room.items.remove(item)
            ii, created = InventoryItem.objects.get_or_create(player=bot, item=item)
            if not created:
                ii.quantity += 1
            ii.save()
            bot_auto_equip(bot, item)

    # Auto-train stats if bot has stat points
    if bot.stat_points > 0:
        # Train primary stat based on class
        primary_stats = {
            "Street Samurai": "STR",
            "Heavy": "STR",
            "Jade Dragon": "AGI",
            "Ninja": "AGI",
            "Thief": "AGI",
            "Netrunner": "INT",
            "Techie": "INT",
            "Psycher": "INT",
            "Warlock": "INT",
            "Medie": "HEA",
            "Priest": "WIL",
            "Fixer": "CHA",
            "Trickster": "CHA",
        }
        stat_to_train = primary_stats.get(bot.game_class, "STR")
        while bot.stat_points > 0:
            train_stat(bot, stat_to_train)

    # Wander: actively hunt for NPCs to fight. Bots linger a little in rooms
    # that still have targets but leave empty sectors quickly (they used to
    # get stuck oscillating in dead zones).
    npcs_nearby = npcs.exists()
    if room.exits:
        move_chance = 0.35 if npcs_nearby else 0.85
        if random.random() < move_chance:
            direction = random.choice(list(room.exits.keys()))
            move_player(bot, direction)
    else:
        # Dead-end room with no exits and nothing to fight: relocate to a
        # live hunting ground instead of being stuck forever.
        rescue_room = pick_teleport_room(bot.lvl)
        if rescue_room and rescue_room != room:
            teleport_player_to_room(
                bot, rescue_room, "Pathfinder rerouted this stranded runner."
            )

    return ""


def get_poll_data(player):
    # Process auto-combat tick
    combat_msg = process_combat_tick(player)

    # Process resting HP regeneration
    rest_msg = process_resting(player)

    # Process AI for ALL online bots (not just those in this player's room).
    # Bots only act when process_bot_ai() is invoked, and the background
    # `process_bots` daemon is not always running. By advancing every online
    # bot on each poll, bots reliably wander, fight NPCs, gain EXP and level
    # up even when no human player happens to be in their sector. Each bot is
    # internally throttled by last_bot_action (10-30s), so most polls return
    # immediately without acting.
    bot_msg = ""
    all_bots = Player.objects.filter(is_bot=True, online=True)
    for bot in all_bots:
        bot_result = process_bot_ai(bot)
        if bot_result:
            bot_msg += bot_result

    # Only process NPC AI for NPCs in the player's current room
    npc_ai_msg = ""
    room_npcs = NPC.objects.filter(location=player.location, hp__gt=0)
    for npc in room_npcs:
        npc_result = process_npc_ai(npc)
        if npc_result:
            npc_ai_msg += npc_result

    # Check for procedural weapon spawns (once per process, using module-level cache)
    check_procedural_weapon_spawns()

    # Idle handling: random 2-min hub AFK teleports, stuck-bot rescues and
    # the 1-hour inactivity kick (rate-limited internally).
    process_afk_players()

    cutoff = timezone.now() - timezone.timedelta(seconds=30)
    # Poll world chat and local chat
    msgs = ChatMessage.objects.filter(
        Q(room=player.location) | Q(room=None), timestamp__gt=cutoff
    ).order_by("timestamp")
    chat = [
        {"player": m.sender.user.username, "message": m.message, "world": (m.room is None)}
        for m in msgs
    ]
    npcs = list(
        NPC.objects.filter(location=player.location, hp__gt=0).values(
            "id", "name", "hp", "hp_max", "lvl", "npc_type"
        )
    )
    room_items = list(player.location.items.all().values("id", "name")) if player.location else []
    players_here = list(
        Player.objects.filter(location=player.location, online=True)
        .exclude(id=player.id)
        .values("id", "user__username", "lvl", "game_class", "is_bot")
    )

    # PvP notification
    notification = player.notification
    if notification:
        player.notification = ""
        player.save(update_fields=["notification"])

    if combat_msg:
        notification = (notification + "\n" + combat_msg).strip()

    if rest_msg:
        notification = (notification + "\n" + rest_msg).strip()

    if bot_msg:
        notification = (notification + "\n" + bot_msg).strip()

    if npc_ai_msg:
        notification = (notification + "\n" + npc_ai_msg).strip()

    return {
        "chat": chat,
        "npcs": npcs,
        "items": room_items,
        "players": players_here,
        "status": get_status_str(player),
        "location": (player.location.name if player.location else "Unknown"),
        "notification": notification,
    }


# NPC AI processing
def process_npc_ai(npc):
    """Process AI behavior for NPCs. Called during polling."""
    output = ""
    room = npc.location

    # Only process NPC AI every 10-15 seconds
    now = timezone.now()
    if npc.last_move_time:
        time_since_last = (now - npc.last_move_time).total_seconds()
        if time_since_last < random.randint(10, 15):
            return ""

    npc.last_move_time = now
    npc.save(update_fields=["last_move_time"])

    # Check if NPC is currently in combat (any player has this NPC as their target)
    in_combat = NPC.objects.filter(
        pk=npc.pk,
        combating_players__isnull=False
    ).exists()

    if in_combat:
        # Small percentage (10%) will flee mid-combat
        if random.random() < 0.1 and room.exits:
            direction = random.choice(list(room.exits.keys()))
            new_room_id = room.exits[direction]
            if new_room_id:
                try:
                    new_room = Room.objects.get(id=new_room_id)
                    if new_room and new_room != room:
                        old_room = npc.location
                        npc.location = new_room
                        npc.save(update_fields=["location"])
                        # Clear all players targeting this NPC
                        Player.objects.filter(last_combat_npc=npc).update(
                            last_combat_npc=None,
                            auto_attack=False
                        )
                        broadcast_npc_movement(npc, old_room, new_room)
                        output = f"\n[COMBAT] {npc.name} flees from combat into the shadows!"
                        return output
                except Room.DoesNotExist:
                    pass
        # Most NPCs stay put while in combat
        return ""

    # NPC wanders to adjacent rooms (only when not in combat, and reduced chance)
    if room.exits and random.random() < 0.2:
        direction = random.choice(list(room.exits.keys()))
        new_room_id = room.exits[direction]
        if new_room_id:
            try:
                new_room = Room.objects.get(id=new_room_id)
                if new_room and new_room != room:
                    old_room = npc.location
                    npc.location = new_room
                    npc.save(update_fields=["location"])
                    broadcast_npc_movement(npc, old_room, new_room)
                    output = f"\n[GRID] {npc.name} wanders off."
            except Room.DoesNotExist:
                pass

    # NPC rest: heal when HP drops below threshold (bypasses combat)
    if not in_combat:
        rest_msg = process_npc_rest(npc)
        if rest_msg:
            output += rest_msg

    return output

def process_npc_rest(npc):
    """Heal NPC when HP is critically low. Called by process_npc_ai each turn."""
    output = ""

    # Skip if NPC is at full HP
    if npc.hp >= npc.hp_max:
        return output

    # NPCs can rest when HP drops below 40% of max
    if npc.hp >= npc.hp_max * 0.4:
        return output

    # Don't heal if the NPC is being attacked or is blocked by a player
    in_combat = NPC.objects.filter(
        pk=npc.pk,
        combating_players__isnull=False
    ).exists()
    if in_combat:
        return output

    # Calculate healing rate based on NPC level and a "sturdiness" modifier
    # Low-level NPCs heal slower; higher-level NPCs recover faster
    # NPCs with higher resistance/evasion stats heal slightly faster
    heal_rate = max(1, min(4, int(npc.lvl / 3)))
    heal_amount = random.randint(heal_rate, heal_rate + 2)

    old_hp = npc.hp
    npc.hp = min(npc.hp_max, npc.hp + heal_amount)
    npc.save(update_fields=["hp"])

    if npc.hp > old_hp and npc.hp < npc.hp_max:
        output = f"\n[REST] {npc.name} regenerates {heal_amount} HP. HP: {npc.hp}/{npc.hp_max}."

    if npc.hp >= npc.hp_max:
        output += f"\n[REST] {npc.name} is fully healed."

    return output


def process_bot_help(bot):
    """Process help for bots: check if bot needs assistance with stats or resting."""
    output = ""

    # Bots with very low HP should rest and recover
    if bot.hp < bot.hp_max * 0.3 and bot.hp > 0:
        if not bot.resting:
            # Bot can rest by using rest_command-like logic
            rest_command(bot)
            output += f"\n[BOT] {bot.user.username} is low on HP and begins to rest."

    return output


# Party System Functions


# Party System Functions

def create_party(player, party_name=None):
    """Create a new party with the player as leader."""
    if player.parties.exists():
        return "You are already in a party. Leave it first to create a new one."

    party = Party.objects.create(
        leader=player, name=party_name or f"{player.user.username}'s Party"
    )
    PartyMembership.objects.create(party=party, player=player, invited=False)

    return f"Party '{party.name}' created. You are the leader."


def invite_to_party(leader, target_name):
    """Invite another player to join the party."""
    if not leader.parties.exists():
        return "You are not in a party. Create one with PARTY CREATE first."

    party = Party.objects.get(id=leader.parties.first().id)

    if party.leader != leader:
        return "Only the party leader can invite members."

    if party.members.count() >= 3:
        return "Party is full (max 3 members). Cannot invite more."

    target = Player.objects.filter(user__username__icontains=target_name, online=True).first()

    if not target:
        return "Player not found or not online."

    if target.location != leader.location:
        return "Target must be in the same sector to invite."

    if target.parties.exists():
        return "That player is already in a party."

    if target.party_invite and target.party_invite == party:
        return "That player already has a pending invite from your party."

    target.party_invite = party
    target.save(update_fields=["party_invite"])

    return f"Invited {target.user.username} to the party. They have 60 seconds to accept."


def accept_party_invite(player):
    """Accept a pending party invitation."""
    if not player.party_invite:
        return "No pending party invitation."

    party = Party.objects.get(id=player.party_invite.id)

    if not party.members.exists():
        player.party_invite = None
        player.save(update_fields=["party_invite"])
        return "Party no longer exists."

    if party.members.count() >= 3:
        player.party_invite = None
        player.save(update_fields=["party_invite"])
        return "Party is now full. Cannot join."

    PartyMembership.objects.create(party=party, player=player, invited=True)
    player.party_invite = None
    player.save(update_fields=["party_invite"])

    for member in party.members.all():
        if member != player:
            member.notification = (
                f"\n[PARTY] {player.user.username} has joined the party."
            ).strip()
            member.save(update_fields=["notification"])

    return f"You have joined {party.name}."


def leave_party(player):
    """Leave the current party."""
    if not player.parties.exists():
        return "You are not in a party."

    party = player.parties.first()

    if party.leader == player:
        for member in party.members.all():
            if member != player:
                member.notification = (
                    f"\n[PARTY] {player.user.username} has disbanded the party. "
                    "You are no longer in a party."
                ).strip()
                member.party_invite = None
                member.save(update_fields=["notification", "party_invite"])

        party.delete()
        return "You have disbanded the party."

    PartyMembership.objects.filter(party=party, player=player).delete()

    for member in party.members.all():
        member.notification = (f"\n[PARTY] {player.user.username} has left the party.").strip()
        member.save(update_fields=["notification"])

    return "You have left the party."


def get_party_status(player):
    """Get the current party status for a player."""
    if not player.parties.exists():
        return "You are not in a party."

    party = player.parties.first()
    members = list(party.members.all().values_list("user__username", flat=True))
    leader_name = party.leader.user.username

    sb = [f"\n=== Party: {party.name} ==="]
    sb.append(f"Leader: {leader_name}")
    sb.append("Members:")
    for m in members:
        if m == leader_name:
            sb.append(f"  - {m} (Leader)")
        else:
            sb.append(f"  - {m}")
    sb.append(f"Size: {len(members)}/3")

    return "\n".join(sb)


def move_party_leader(player, direction):
    """Move the party leader and all party members together."""
    if not player.parties.exists():
        return "You are not in a party. Create one with PARTY CREATE first."

    party = player.parties.first()
    if party.leader != player:
        return "Only the party leader can move the party."

    party_id = party.id

    result = move_player(player, direction)

    party = Party.objects.get(id=party_id)

    for member in party.members.all():
        if member != player and member.online:
            old_room = member.location
            member.location = player.location
            member.save(update_fields=["location"])

            if old_room and old_room != member.location:
                broadcast_room_event(member, old_room, None, "exit")
                broadcast_room_event(member, None, member.location, "enter")

    return result


def steal_from_target(player, args):
    """Steal from NPCs or players. Only works for Thief and Trickster classes while sneaking."""
    if not player.hidden:
        return "You must be sneaking to attempt theft."

    if player.game_class not in ["Thief", "Trickster"]:
        return "Your class cannot steal."

    if not args:
        return "Steal from whom?"

    target_npc = NPC.objects.filter(location=player.location, name__iexact=args, hp__gt=0).first()
    target_player = Player.objects.filter(location=player.location, online=True, user__username__iexact=args).first()

    if not target_npc and not target_player:
        return f"No target named '{args}' here."

    # Enforce level range for stealing from players before attempting
    if target_player and abs(player.lvl - target_player.lvl) > 4:
        return "Target level too distant. Range: +/- 4 levels."

    base_chance = 0.15 if player.game_class == "Thief" else 0.10
    agi_bonus = player.agi_stat * 0.01
    steal_chance = min(0.50, base_chance + agi_bonus)

    if random.random() > steal_chance:
        player.hidden = False
        player.save(update_fields=["hidden"])
        if target_player:
            return f"You failed to steal from {target_player.user.username}. You were spotted!"
        else:
            return f"You failed to steal from {target_npc.name}. You were spotted!"

    player.hidden = False
    player.save(update_fields=["hidden"])

    if target_player:
        stolen = target_player.money // 4
        if stolen > 0:
            target_player.money -= stolen
            target_player.save(update_fields=["money"])
            player.money += stolen
            player.save(update_fields=["money"])
            return f"You pilfered {stolen} credits from {target_player.user.username}!"
        else:
            return f"{target_player.user.username} has nothing worth taking."

    # NPC steal
    if target_npc:
        stolen = min(target_npc.money_drop, random.randint(1, 50) + player.agi_stat)
        if stolen > 0:
            player.money += stolen
            player.save(update_fields=["money"])
            return f"You lifted {stolen} credits from {target_npc.name}!"
        else:
            return f"{target_npc.name} has nothing worth taking."

    return "No target found."


def drop_npc_weapon(npc):
    """Drop NPC's weapon to the room floor when NPC is defeated."""
    if npc.weapon:
        item_name = npc.weapon.name
        npc.location.items.add(npc.weapon)
        npc.weapon = None
        npc.save(update_fields=["weapon"])
        return f"\n{npc.name} drops {item_name}!"
    return ""
