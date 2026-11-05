import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db import OperationalError
from django.utils import timezone
from .models import Player, Room
from . import services


def index(request):
    try:
        return render(request, "game/game.html")
    except OperationalError:
        return JsonResponse(
            {"error": "Database is being initialized. Please refresh in a moment."}, status=503
        )


@csrf_exempt
def register_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        password = request.POST.get("password")
        race = request.POST.get("race", "Human")
        gender = request.POST.get("gender", "Other")
        game_class = request.POST.get("gameClass", "Street Samurai")

        # User customized stats
        custom_stats_json = request.POST.get("stats")
        custom_stats = {}
        if custom_stats_json:
            try:
                custom_stats = json.loads(custom_stats_json)
            except json.JSONDecodeError:
                pass

        if not name or not password:
            return JsonResponse({"message": "Name and password required."}, status=400)

        try:
            if User.objects.filter(username=name).exists():
                return JsonResponse({"message": "Handle already in use."}, status=400)

            user = User.objects.create_user(username=name, password=password)
            start_room = Room.objects.get_or_create(
                id=1,
                defaults={
                    "name": "The Neon Hub",
                    "description": "A bustling intersection of neon lights and rainy streets.",
                    "zone": "hub",
                    "theme": "urban",
                    "safe_zone": True,
                },
            )[0]

            # Starting Stats based on Race
            stats = {
                "str_stat": 10,
                "int_stat": 10,
                "wil_stat": 10,
                "agi_stat": 10,
                "hea_stat": 10,
                "cha_stat": 10,
            }

            race_base_stats = {
                "Cyborg": {
                    "str_stat": 13,
                    "hea_stat": 12,
                    "agi_stat": 10,
                    "int_stat": 11,
                    "cha_stat": 8,
                    "wil_stat": 10,
                },
                "Bio-hacked": {
                    "hea_stat": 13,
                    "str_stat": 11,
                    "cha_stat": 9,
                    "agi_stat": 11,
                    "int_stat": 10,
                    "wil_stat": 10,
                },
                "Android": {
                    "int_stat": 14,
                    "wil_stat": 12,
                    "cha_stat": 7,
                    "hea_stat": 10,
                    "str_stat": 10,
                    "agi_stat": 10,
                },
                "Mutant": {
                    "str_stat": 12,
                    "hea_stat": 13,
                    "wil_stat": 10,
                    "cha_stat": 8,
                    "agi_stat": 11,
                    "int_stat": 10,
                },
                "Human": {
                    "cha_stat": 12,
                    "wil_stat": 11,
                    "str_stat": 10,
                    "hea_stat": 10,
                    "agi_stat": 10,
                    "int_stat": 10,
                },
                "Dark Elf": {
                    "str_stat": 10,
                    "int_stat": 10,
                    "wil_stat": 11,
                    "agi_stat": 12,
                    "hea_stat": 8,
                    "cha_stat": 10,
                },
                "Void-Walker": {
                    "wil_stat": 14,
                    "agi_stat": 11,
                    "str_stat": 8,
                    "hea_stat": 10,
                    "int_stat": 10,
                    "cha_stat": 8,
                },
                "Synth-Soul": {
                    "int_stat": 15,
                    "cha_stat": 7,
                    "wil_stat": 12,
                    "str_stat": 8,
                    "hea_stat": 10,
                    "agi_stat": 10,
                },
                "Orc": {
                    "str_stat": 13,
                    "agi_stat": 13,
                    "int_stat": 8,
                    "cha_stat": 8,
                    "hea_stat": 10,
                    "wil_stat": 10,
                },
                "Elf": {
                    "agi_stat": 12,
                    "wil_stat": 10,
                    "hea_stat": 9,
                    "cha_stat": 11,
                    "str_stat": 9,
                    "int_stat": 10,
                },
                "Goblin": {
                    "cha_stat": 12,
                    "agi_stat": 11,
                    "str_stat": 8,
                    "int_stat": 10,
                    "hea_stat": 10,
                    "wil_stat": 10,
                },
            }

            if race in race_base_stats:
                stats.update(race_base_stats[race])

            # Apply user customized distribution (bonus points added to racial base)
            if custom_stats:
                total_sum = 0
                for s_key in ["str", "int", "wil", "agi", "hea", "cha"]:
                    val = int(custom_stats.get(s_key, 10))
                    total_sum += val
                    # Apply the user's deviation from the standard base (10) to the racial base
                    delta = val - 10
                    stats[f"{s_key}_stat"] += delta

                if total_sum > 80:
                    return JsonResponse(
                        {
                            "message": f"Stat point allocation error. Max total points is 80 "
                            f"(You assigned {total_sum})."
                        },
                        status=400,
                    )

            # Class Modifiers
            class_mods = {
                "Street Samurai": {"attack": 5},
                "Netrunner": {"mana_max": 40},
                "Techie": {"defense": 3},
                "Medie": {"hp_max": 40},
                "Fixer": {"money": 50},
                "Thief": {"attack": 3},
                "Heavy": {"defense": 5, "hp_max": 30},
                "Psycher": {"mana_max": 40},
                "Warlock": {"mana_max": 40},
                "Priest": {"hp_max": 45},
                "Jade Dragon": {"attack": 3, "hp_max": 25},
                "Trickster": {"mana_max": 30},
            }

            c_mods = class_mods.get(game_class, {})
            for k, v in c_mods.items():
                if k in stats:
                    stats[k] += v

            # Initialize derived stats
            stats["attack"] = 10 + (stats["str_stat"] // 2) + c_mods.get("attack", 0)
            stats["defense"] = 5 + (stats["agi_stat"] // 2) + c_mods.get("defense", 0)
            stats["hp_max"] = 100 + (stats["hea_stat"] * 2) + c_mods.get("hp_max", 0)
            stats["hp"] = stats["hp_max"]
            stats["mana_max"] = 20 + (stats["wil_stat"] * 2) + c_mods.get("mana_max", 0)
            stats["mana"] = stats["mana_max"]

            initial_money = 25 + c_mods.get("money", 0)

            Player.objects.create(
                user=user,
                race=race,
                gender=gender,
                game_class=game_class,
                location=start_room,
                money=initial_money,
                last_activity=timezone.now(),
                last_move_time=timezone.now(),
                **stats,
            )
            return JsonResponse({"message": f"Character initialized! Welcome to the grid, {name}."})
        except OperationalError:
            return JsonResponse(
                {"message": "System initializing. Try again in 10 seconds."}, status=503
            )


@csrf_exempt
def login_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        password = request.POST.get("password")
        try:
            user = authenticate(username=name, password=password)
            if user:
                login(request, user)
                player = user.player
                player.online = True
                player.last_seen = timezone.now()
                player.last_activity = timezone.now()
                player.save()
                return JsonResponse({"success": True})
            return JsonResponse({"success": False, "message": "Invalid credentials"})
        except OperationalError:
            return JsonResponse({"success": False, "message": "Database not ready."})


@csrf_exempt
def command_view(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"message": "Not authenticated"}, status=401)

        player = request.user.player

        # Inactivity kick (1 hour of doing NOTHING). Kicked players lose
        # nothing - they just have to log back in from the login page.
        now = timezone.now()
        last_active = player.last_activity or player.last_seen
        if last_active and (now - last_active).total_seconds() >= services.AFK_KICK_SECONDS:
            services.kick_player_for_inactivity(player)
            logout(request)
            return JsonResponse(
                {
                    "message": "Kicked: 1 hour of inactivity. You lost nothing - log back in.",
                    "action": "exit",
                },
                status=401,
            )

        # Update last_seen and record real activity (any command counts)
        player.last_seen = now
        player.save(update_fields=["last_seen"])
        services.touch_player_activity(player)

        try:
            cmd_data = json.loads(request.body)
            full_cmd = cmd_data.get("command", "").strip()
        except (json.JSONDecodeError, AttributeError):
            full_cmd = ""

        if not full_cmd:
            return JsonResponse({"output": "", "status": services.get_status_str(player)})

        parts = full_cmd.split(" ", 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        output = ""
        # Handle EXIT command
        if command == "exit":
            player.online = False
            player.save()
            logout(request)
            return JsonResponse({"output": "LOGGING OUT...", "status": "OFFLINE", "action": "exit"})

        if command in ["look", "l"]:
            output = services.get_look(player, args)
        elif command in ["n", "north", "s", "south", "e", "east", "w", "west"]:
            output = services.move_player(player, command)
        elif command == "who":
            online_players = Player.objects.filter(online=True)
            lines = ["\n=== Nodes Currently Linked ==="]
            for p in online_players:
                bot_marker = " (bot)" if p.is_bot else ""
                lines.append(f"  {p.user.username}{bot_marker} (Lvl {p.lvl}) - {p.game_class}")
            output = "\n".join(lines)
        elif command == "top":
            output = services.get_top_ten()
        elif command == "wall":
            output = services.get_wall_of_death()
        elif command in ["attack", "a", "kill", "k"]:
            output = services.attack_target(player, args, auto=False)
        elif command in ["autoattack", "aa"]:
            output = services.attack_target(player, args, auto=True)
        elif command in ["inventory", "i"]:
            output = services.get_inventory(player)
        elif command in ["status", "st", "stats"]:
            output = services.get_status_detailed(player)
        elif command in ["get", "g"]:
            output = services.get_item(player, args)
        elif command == "drop":
            output = services.drop_item(player, args)
        elif command == "equip":
            output = services.equip_item(player, args)
        elif command in ["list", "li"]:
            output = services.list_shop(player)
        elif command == "buy":
            output = services.buy_item(player, args)
        elif command == "sell":
            output = services.sell_item(player, args)
        elif command == "sellall":
            output = services.sell_all_items(player)
        elif command in ["say", "'"]:
            output = services.handle_say(player, args)
        elif command in ["broadcast", "bcast"]:
            output = services.handle_broadcast(player, args)
        elif command in ["help", "?"]:
            output = services.get_help(player)
        elif command == "guide":
            output = "Opening user guide in browser..."
            return JsonResponse({"output": output, "status": services.get_status_str(player), "action": "open_guide"})
        elif command == "use":
            output = services.use_item(player, args)
        elif command == "train":
            output = services.train_stat(player, args)
        elif command == "transport":
            output = services.transport_player(player, args)
        elif command == "rest":
            output = services.rest_command(player)
        elif command == "disengage":
            output = services.disengage_combat(player)
        elif command == "steal":
            output = services.steal_from_target(player, args)
        elif command == "party":
            if not args:
                output = "Party commands: CREATE, INVITE <player>, ACCEPT, LEAVE, STATUS"
            else:
                parts = args.split(" ", 1)
                subcmd = parts[0].lower()
                subargs = parts[1] if len(parts) > 1 else ""
                if subcmd == "create":
                    output = services.create_party(player, subargs)
                elif subcmd == "invite":
                    output = services.invite_to_party(player, subargs)
                elif subcmd == "accept":
                    output = services.accept_party_invite(player)
                elif subcmd == "leave":
                    output = services.leave_party(player)
                elif subcmd == "status":
                    output = services.get_party_status(player)
                else:
                    output = "Party commands: CREATE, INVITE <player>, ACCEPT, LEAVE, STATUS"
        else:
            # Check for special moves dynamically
            move_output = services.use_ability(player, command, args)
            if move_output is not None:
                output = move_output
            else:
                output = "COMMAND ERROR: UNKNOWN INSTRUCTION."

        chat_output = services.get_recent_chat(player)
        if chat_output:
            output = chat_output + "\n" + output

        return JsonResponse({"output": output, "status": services.get_status_str(player)})
    except OperationalError:
        return JsonResponse({"output": "Database error. Reconnecting...", "status": "OFFLINE"})


@csrf_exempt
def poll_view(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"status": "idle", "authenticated": False})

        player = request.user.player

        # Inactivity kick (1 hour of doing NOTHING). Kicked players lose
        # nothing; the web client reloads straight to the login page.
        now = timezone.now()
        last_active = player.last_activity or player.last_seen
        if last_active and (now - last_active).total_seconds() >= services.AFK_KICK_SECONDS:
            services.kick_player_for_inactivity(player)
            logout(request)
            return JsonResponse({"status": "kicked_inactivity", "authenticated": False})

        return JsonResponse(services.get_poll_data(player))
    except (OperationalError, Exception):
        return JsonResponse({"status": "db_not_ready", "authenticated": False})


@csrf_exempt
def map_api_view(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"rooms": [], "authenticated": False})
        player = request.user.player
        map_json = services.get_map_data(player)
        return JsonResponse({"rooms": json.loads(map_json)})
    except (OperationalError, Exception):
        return JsonResponse({"rooms": [], "authenticated": False})


@csrf_exempt
def player_info_view(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"player_name": "Unknown", "authenticated": False})

        player = request.user.player
        return JsonResponse(
            {
                "player_name": request.user.username,
                "level": player.lvl,
                "hp": player.hp,
                "hp_max": player.hp_max,
            }
        )
    except (OperationalError, Exception):
        return JsonResponse({"player_name": "Unknown", "authenticated": False})


def user_guide_view(request):
    """Render the user guide HTML page."""
    return render(request, "user_guide.html")
