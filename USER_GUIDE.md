# Darkness BBS — User Guide

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Installation](#installation)
4. [Login & Registration](#login--registration)
5. [Game Commands](#game-commands)
6. [World Structure](#world-structure)
7. [Combat System](#combat-system)
8. [Items & Equipment](#items--equipment)
9. [Character Progression](#character-progression)
10. [Karma & Reputation](#karma--reputation)
11. [Stealth System](#stealth-system)
12. [Drug & Addiction System](#drug--addiction-system)
13. [NPC Aggression & Stalking](#npc-aggression--stalking)
14. [Party System](#party-system)
15. [Server Administration](#server-administration)

---

## Overview

**Darkness BBS** is a multi-user, terminal-style cyberpunk RPG inspired by classic BBS games like MajorMUD. Players explore a procedurally generated grid, engage in tactical combat, customize their builds via manual stat training, and compete with other users in a gritty, neon-soaked world.

Key Features:
- **Massive Procedural World**: 8 distinct sectors with 200+ rooms.
- **Deep Character Customization**: 10 races and 13 classes with unique abilities and traits.
- **Manual Stat Training**: Earn 1 point per level to spend on specific attributes.
- **Tactical Combat**: PvP support (+/- 3 levels), weapon speed, and elemental damage (fire > air > earth > water > fire).
- **Karma System**: Alignment from -100 (Villain) to +100 (Saint).
- **Stealth System**: Hide and perform backstab attacks with bonus damage.
- **Drug & Addiction**: Temporary stat boosts with dependency risk and withdrawal damage.
- **Leaderboards**: Competitive ranking of the top adventurers and a "Wall of Death".
- **Party System**: Team up with up to 3 players to explore the grid together.
- **AI Bot System**: Autonomous AI players that wander, fight, and interact.

---

## Getting Started

1. Navigate to the terminal in your browser.
2. Click **"Initialize New Profile"** to create a character.
3. Enter a handle (username) and password.
4. Select your **Race** (Augmentation Path) and **Class** (Operational Class).
5. Optionally customize your 6 base stats (STR, INT, WIL, AGI, HEA, CHA) — total must not exceed 80 points.
6. Log in and arrive at **The Neon Hub**, the grid's central safe zone.

---

## Login & Registration

### Races (Augmentation Paths)
Each race grants a specific set of stat modifiers and a unique **Race Trait**:

| Race | Modifiers | Special Trait |
|------|-----------|---------------|
| **Cyborg** | STR+5, HEA+2, AGI-2, INT+2 | **Cybernetic Resilience**: +10% resistance to debuffs. |
| **Bio-hacked** | HEA+5, STR+2, CHA-2 | **Adrenal Efficiency**: 20% faster healing, reduced addiction. |
| **Android** | INT+8, WIL+2, CHA-5, HEA-2 | **Systematic Mind**: +15% mana efficiency, mental immunity. |
| **Mutant** | Random (+7/-3) | **Adaptive Biology**: Stats can exceed normal caps by 5. |
| **Human** | CHA+10, WIL+5, STR-5, HEA-5 | **Versatile Potential**: Gains 1.5x stat points on level up. |
| **Void-Walker** | WIL+12, AGI+5, STR-8, HEA-4 | **Phase Shift**: 10% chance to dodge any attack. |
| **Synth-Soul** | INT+15, CHA-10 | **Digital Presence**: +20% stealth effectiveness. |
| **Orc, AGI+10, INT-10, CHA-5 | **Overclocked**: +1 extra attack per combat round. |
| **Elf** | AGI+8, WIL+4, HEA-5 | **Ancient Grace**: +10% critical hit chance. |
| **Dark Elf** | AGI+8, WIL+4, HEA-5 | **Sunlight Sensitivity**: -10% resistances in daylight, **Night Vision**: +15% perception in darkness, **Shadow Walk**: +10% chance to escape melee combat. |
| **Goblin** | CHA+10, AGI+5, STR-8 | **Street Cunning**: +15% chance for extra loot.

### Transporters
Transporters are special rooms that allow players to quickly travel between zones. Each zone hub room contains a transporter that can teleport you to other zone hubs. Look for the transporter examine option or use the `TRANSPORT` command. Transporters are also used by bots to navigate to level-appropriate hunting grounds. |

### Stats Reference
- **STR (Strength)**: Physical power. Increases Attack and carrying capacity. Essential for melee classes.
- **AGI (Agility)**: Speed and reflexes. Increases Defense, crit chance, and stealth effectiveness. Key for dodging and Thief/Ninja.
- **HEA (Health)**: Physical resilience. Increases max HP. Vital for survivability.
- **INT (Intelligence)**: Mental acuity. Powers tech, netrunning, and spellcasting. Increases mana for some classes.
- **WIL (Willpower)**: Mental fortitude. Increases max Mana and resistance to mind effects. Core for Priests.
- **CHA (Charisma)**: Social presence. Used by Fixers and Tricksters. Affects NPC interactions and some abilities.

### Classes (Operational Classes)
Abilities are learned at levels 1, 5, 10, 15, 20, 25, and 30.

| Class | Starting Focus | Specialization | Gear Restrictions |
|-------|----------------|----------------|-----------------|
| **Street Samurai** | ATK, STR, AGI | Multi-strike Melee | All armor, One/Two-handed weapons |
| **Netrunner** | INT, Mana | System Hacking (Water/Air) | Leather/Light armor, One-handed weapons |
| **Techie** | INT, WIL, DEF | Drones & Engineering | Leather/Light armor, One-handed weapons |
| **Medie** | HEA, HP | Healing & Detoxification | Leather/Light armor, One-handed weapons |
| **Fixer** | CHA, Money | Credit Siphoning & Contracts | Leather/Light armor, One-handed weapons |
| **Thief** | AGI, ATK | Stealth & Backstabbing | Leather armor, One-handed weapons |
| **Heavy** | STR, HEA, DEF | Tanking & Earth Damage | All armor, One/Two-handed weapons |
| **Psycher** | WIL, Mana | Neural Energy & Mind Control | Leather/Light armor, One-handed weapons |
| **Warlock** | INT, WIL, Mana | Debuffs & Chaos | Leather/Light armor, One-handed weapons |
| **Priest** | WIL, HEA, HP | Divine Restoration & Air Damage | Leather/Light armor, One-handed weapons |
| **Trickster** | CHA, AGI | Luck & Confusion | Leather/Light armor, One-handed weapons |
| **Jade Dragon** | AGI, STR, DEF | Unarmed Martial Arts | Light armor only, Jade weapons |
| **Ninja** | AGI, ATK | Stealth & Thrown Weapons | Light armor only, Ninja weapons |

**Class Strategies:**
- **Street Samurai**: Physical combat specialist. High attack, excels in direct confrontations.
- **Netrunner**: Tech-hacker. Uses water/ice and air-based attacks. High mana pool, debuffs enemies.
- **Techie**: Drone operator. Earth and fire damage, can heal with nanobots.
- **Medie**: Field medic. Healing and support abilities, can deal water/rot damage.
- **Fixer**: Social manipulator. Drains credits, calls in attacks.
- **Thief**: Stealth assassin. Backstab crits, poison, smoke bombs.
- **Heavy**: Tank specialist. High HP and defense, earth-based AOE attacks.
- **Psycher**: Psychic warrior. Mind-based attacks, telekinesis, shields.
- **Warlock**: Dark spellcaster. Curses, chaos damage, blood pacts.
- **Priest**: Holy healer. Healing, blessings, divine shields.
- **Trickster**: Chaos agent. Random effects, stealth, luck-based abilities.
- **Jade Dragon**: Martial artist. Chi-based attacks, unarmed combat bonus.
- **Ninja**: Shadow warrior. Stealth, teleport, kunai throws, high crit from concealment.

---

## Game Commands

### Navigation
- `N`, `S`, `E`, `W`: Movement.
- `EXIT`: Log out safely.

### Information
- `L` / `LOOK`: Scan sector. `LOOK <target>`: Examine entity.
- `WHO`: List active nodes.
- `TOP`: Top 25 ranking.
- `WALL`: Top 25 deaths.
- `ST` / `STATUS`: Detailed profile.
- `I` / `INVENTORY`: List gear.
- `HELP` / `?`: Command manual.

### Communication
- `SAY <msg>`: Local chat.
- `BROADCAST <msg>`: Global chat.

### Combat & Action
- `A <target>`: Attack one round.
- `AA <target>`: Auto-attack until victory/defeat.
- `<ABILITY> <target>`: Use class skill (e.g., `HCK`, `BLD`, `PTC`).
- `STEALTH` / `SNEAK`: Hide (influenced by AGI and Class).
- `REST`: Recover HP/Mana (requires standing still).

### Items
- `USE <item>`: Consumables/Drugs.
- `GET <item>` / `DROP <item>`: Ground interaction.
- `EQUIP <item>`: Manage hardware.
- `LIST` / `BUY` / `SELL`: Commerce.
- `SELLALL`: Sell all unequipped hardware in your inventory.

---

## Combat System

### Damage & Crits
Damage: `max(1, ATK - DEF/2)` ± variance. 
Critical Hits: 2.0x damage. Chance based on AGI (physical) or INT (abilities).

### Elemental Wheel
- **Fire** > **Air** > **Earth** > **Water** > **Fire**
- Strength: 1.5x damage. Weakness: 0.5x damage.

### Weapon Speed
10 Speed Bonus = 1 extra attack/round.
10 Agility = 1 extra attack/round.

---

## Party System

Team up with other players to explore and move together.

- `PARTY CREATE`: Start a new party as leader.
- `PARTY INVITE <player>`: Invite a player in your current room.
- `PARTY ACCEPT`: Join a party after receiving an invite.
- `PARTY LEAVE`: Exit your current party.
- `PARTY STATUS`: See current members.
- **Group Movement**: When the leader moves, all online party members move with them.

---

## Server Administration

- `make repair`: Full database reset (wipes players).
- `make clean`: Wipes world data but **keeps players**.
- `make init`: Generates new world state.
- `python manage.py process_bots`: Starts the AI daemon.

---

## MUD Client Setup

Darkness BBS supports traditional MUD clients like Mudlet, MUSHclient, and any standard Telnet client.

### Prerequisites

1. **Create your character** using the web interface first (character creation is web-only)
2. **Start the MUD server**: `python manage.py start_mud_server`
3. **Note the connection details**: By default, the server listens on port 4000

### Connecting with a MUD Client

#### Mudlet

1. Open Mudlet
2. Click **"Connect"** → **"Connect to..."**
3. Enter your server details:
   - **Host**: `localhost` (or your server's IP address)
   - **Port**: `4000`
   - **Name**: `Darkness BBS`
4. **Important**: Uncheck the **"Use SSL/TLS"** option (the server uses plain Telnet, not encrypted)
5. Click **"Connect"**
6. Log in with your handle and password when prompted

**Optional Mudlet Profile Setup:**
- Enable **ANSI Colors** in Settings → General
- Set **Command Separator** to `;` if you want to chain commands
- Create aliases for common commands (e.g., `l` for `look`)

#### MUSHclient

1. Open MUSHclient
2. Click **"File"** → **"Connect"**
3. Enter connection details:
   - **Host**: `localhost` (or your server's IP)
   - **Port**: `4000`
4. Click **"OK"**
5. Log in with your handle and password

#### Generic Telnet Client

From a terminal/command prompt:
```bash
telnet localhost 4000
```

Or using netcat:
```bash
nc localhost 4000
```

### MUD Client Configuration Tips

#### Recommended Settings

- **Encoding**: UTF-8 or ASCII
- **Line Endings**: CRLF (\r\n)
- **Terminal Type**: ANSI or VT100
- **Character Set**: ISO 8859-1 or UTF-8
- **Echo**: Local (client-side echo)

#### Mudlet-Specific Tips

1. **Enable ANSI Colors**: Settings → General → Check "Use ANSI colors"
2. **Set Prompt**: The game sends a status line after each command showing:
   ```
   HP:100/100|MA:20/20|LV:1|CR:25|[Neutral]
   ```
3. **Create Aliases** (optional):
   ```
   l = look
   n = north
   s = south
   e = east
   w = west
   i = inventory
   st = status
   ```

#### MUSHclient-Specific Tips

1. **Enable ANSI**: File → World Properties → General → Check "Use ANSI colors"
2. **Set Command Separator**: Use `;` to chain commands (e.g., `n;look`)
3. **Create Triggers** (optional):
   - Trigger on: `HP:(\d+)/(\d+)` to track health
   - Trigger on: `\[(.*?)\]` to track karma alignment

### Telnet Protocol Notes

- The server uses standard Telnet protocol (port 23 by default, but configurable)
- ANSI escape codes are used for screen clearing and text formatting
- Line endings are CRLF (\r\n)
- The server does not require Telnet option negotiation (works with basic clients)
- Character creation must be done via the web interface

### Troubleshooting

**Can't connect:**
- Ensure the MUD server is running: `python manage.py start_mud_server`
- Check firewall settings allow port 4000
- Verify the server is listening: `netstat -an | grep 4000`

**Garbled text:**
- Enable ANSI colors in your client
- Check encoding settings (use UTF-8 or ASCII)
- Ensure line endings are set to CRLF

**Commands not working:**
- Make sure you're logged in (you should see a room description)
- Check that you're typing commands in lowercase (most commands are case-insensitive)
- Use `HELP` or `?` to see available commands

**Disconnections:**
- The server has a 20-minute inactivity timeout
- Use `EXIT` to log out cleanly
- If disconnected unexpectedly, simply reconnect and log in again

### Running Both Web and MUD Simultaneously

You can run both the web interface and MUD server at the same time:

```bash
# Terminal 1: Start Django web server
python manage.py runserver

# Terminal 2: Start MUD server
python manage.py start_mud_server
```

Players can use either interface interchangeably - they share the same game state and database.

### PythonAnywhere Deployment

On PythonAnywhere, you can run both the web interface and MUD server:

**Web Interface:**
- Configured via the PythonAnywhere "Web" tab
- Runs on standard ports (80/443)
- Uses WSGI configuration

**MUD Telnet Server:**
- Run as an "Always-On Task" in the PythonAnywhere dashboard
- Default port: 4000
- You can customize the port with: `python manage.py start_mud_server --port 5000`
- **Important**: On PythonAnywhere free accounts, you can only run the web app. The MUD server requires a paid account to run as an always-on task.
- On paid accounts, configure the always-on task to run: `python manage.py start_mud_server --port 4000`

**Firewall/Port Configuration:**
- PythonAnywhere allows outbound connections on any port
- For inbound MUD connections, use a port like 4000, 5000, or 8000
- Players connect to: `yourusername.pythonanywhere.com:4000`

**Example PythonAnywhere Setup:**
1. Deploy web app via the "Web" tab (standard Django setup)
2. Go to "Tasks" tab → "Always-On Tasks"
3. Add command: `python manage.py start_mud_server --port 4000 --settings=darkness_django.settings.production`
4. Players can now connect via MUD client to `yourusername.pythonanywhere.com:4000`

### Security Notes

- The MUD server does not use encryption (standard Telnet)
- For production deployments, consider using SSH tunneling or a VPN
- Passwords are transmitted in plain text over Telnet
- Use strong passwords for your account
- The web interface uses HTTPS when properly configured
