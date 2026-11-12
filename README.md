# Darkness BBS

A professional multi-user, terminal-style cyberpunk RPG (MUD) built with Django. Explore a procedurally generated grid, engage in tactical combat, and compete with other users in a gritty, neon-soaked world.

## Project Structure

- `darkness_django/`: Project configuration, middleware, and environment settings.
- `game/`: The core engine, featuring procedural generation, combat services, and player progression.
- `templates/`: ANSI-themed terminal interface using standard 16-color palettes.
- `static/`: Frontend assets including CSS scanline effects and terminal fonts.

## Core Features

- **Procedural Sectors**: 8 distinct zones from Corporate Plazas to the Undercity.
- **Deep Progression**: 10 Races and 13 Classes with unique abilities and stat modifiers.
- **Manual Training**: Earn 1 stat point per level to manually improve STR, INT, WIL, AGI, HEA, or CHA.
- **Tactical Combat**: PvP support (within 3 levels), weapon speed mechanics, and elemental damage (fire > air > earth > water > fire).
- **Karma System**: Alignment ranges from -100 (Villain) to 100 (Saint), affecting NPC aggression.
- **Stealth System**: Hide in shadows to perform backstab attacks with bonus damage.
- **Drug & Addiction System**: Temporary stat boosts with risk of dependency and withdrawal damage.
- **Unique Loot**: Sector bosses drop legendary gear not found in shops.
- **Leaderboards**: Use the `TOP` command to see the grid's most elite adventurers.
- **AI Bot System**: Autonomous AI-controlled players with cyberpunk names and 9 distinct personalities (Aggressive, Coward, Chaotic, Explorer, Hermit, Mercenary, Social, Trader, Vigilante) that wander, fight, trade, and interact with players.

## Quick Start

### Web Interface
1. Navigate to the terminal in your browser.
2. Click **"Initialize New Profile"** to create a character.
3. Select your **Race** and **Class**, then optionally customize your 6 base stats.
4. Log in and arrive at **The Neon Hub**, the grid's central safe zone.

### MUD Client (Telnet)
You can also connect using MUD clients like Mudlet, MUSHclient, or any Telnet client:

1. **Create your character** using the web interface first (character creation is web-only)
2. **Start the MUD server**: `python manage.py start_mud_server`
3. **Connect** using your MUD client to `localhost:4000` (or your server's IP and port)
4. **Log in** with your handle and password

For detailed MUD client setup instructions, see the [USER_GUIDE.md](USER_GUIDE.md#mud-client-setup).

### AI Bots
The grid is populated with AI-controlled players that:
- Have cyberpunk-themed names (e.g., NeonShade, ChromeWraith, GlitchMonk)
- Spawn with one of 9 distinct personalities that shape combat, social, and movement behavior:
  - **Aggressive**: Hunts players with high aggression
  - **Coward**: Flees from danger, fights only NPCs, rests early
  - **Chaotic**: Unpredictable - could help or backstab you
  - **Explorer**: Roams distant zones, avoids crowds, loves transporters
  - **Hermit**: Avoids players entirely, hunts NPCs in isolated sectors
  - **Mercenary**: Fights for coin, neutral alignment, works with anyone
  - **Social**: Loves parties, greets everyone, chats frequently
  - **Trader**: Hoards money, frequents shops, avoids pointless combat
  - **Vigilante**: Hunts evil-aligned players, defends the weak
- Automatically wander the grid, fight NPCs, and level up
- May attack players based on personality and karma alignment
- Can invite players to parties (social personalities most likely)
- Appear in the `WHO` list and `TOP` rankings with a `(bot)` marker
- Are created via `python manage.py create_bots` (default 25 bots, configurable with `--count` and `--personality`).
- Buy gear from shops, pick up loot, and auto-train their stats.

## Documentation
For a full manual of commands, combat formulas, and world lore, see the [USER_GUIDE.md](USER_GUIDE.md).
