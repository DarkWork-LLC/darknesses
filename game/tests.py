import json
from django.test import TransactionTestCase, TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Player, Room, NPC, Item, InventoryItem, ChatMessage, Party
from . import services


class GameLogicTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create rooms
        self.hub = Room.objects.create(id=1, name="Hub", description="The center.")
        self.other_room = Room.objects.create(id=2, name="Other", description="Elsewhere.")
        self.hub.exits = {"north": 2}
        self.hub.save()
        self.other_room.exits = {"south": 1}
        self.other_room.save()

        # Create user and player
        self.user = User.objects.create_user(username="neo", password="password")
        self.player = Player.objects.create(
            user=self.user,
            location=self.hub,
            hp=100,
            hp_max=100,
            attack=10,
            defense=5,
            money=50,
            online=True,
        )
        self.client.login(username="neo", password="password")

    def test_look_command(self):
        response = self.client.post(
            "/command/", data=json.dumps({"command": "look"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        output = response.json()["output"]
        self.assertIn("Hub", output)
        self.assertIn("The center.", output)

    def test_movement(self):
        response = self.client.post(
            "/command/", data=json.dumps({"command": "north"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertEqual(self.player.location.id, 2)
        self.assertIn("Other", response.json()["output"])

    def test_attack_npc(self):
        npc = NPC.objects.create(
            name="Drone",
            location=self.hub,
            hp=20,
            hp_max=20,
            attack=5,
            defense=2,
            lvl=1,
            money_drop=10,
            exp_drop=10,
        )
        response = self.client.post(
            "/command/",
            data=json.dumps({"command": "attack drone"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        npc.refresh_from_db()
        self.assertLess(npc.hp, 20)
        self.assertIn("You hit Drone", response.json()["output"])

    def test_buy_item(self):
        self.hub.shop_name = "General Store"
        self.hub.save()
        item = Item.objects.create(name="Battery", price=20, item_type="misc")

        response = self.client.post(
            "/command/",
            data=json.dumps({"command": "buy battery"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertEqual(self.player.money, 30)
        self.assertTrue(InventoryItem.objects.filter(player=self.player, item=item).exists())

    def test_equip_item(self):
        item = Item.objects.create(name="Laser", item_type="weapon", attack_bonus=5)
        InventoryItem.objects.create(player=self.player, item=item)

        response = self.client.post(
            "/command/",
            data=json.dumps({"command": "equip laser"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertEqual(self.player.attack, 15)

        ii = InventoryItem.objects.get(player=self.player, item=item)
        self.assertTrue(ii.equipped)

    def test_say_command(self):
        response = self.client.post(
            "/command/",
            data=json.dumps({"command": "say hello world"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("You say: hello world", response.json()["output"])
        self.assertTrue(ChatMessage.objects.filter(message="hello world").exists())

    def test_who_command(self):
        response = self.client.post(
            "/command/", data=json.dumps({"command": "who"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("neo", response.json()["output"])


class PartyTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create rooms
        self.hub = Room.objects.create(id=1, name="Hub", description="The center.")
        self.other_room = Room.objects.create(id=2, name="Other", description="Elsewhere.")
        self.hub.exits = {"north": 2}
        self.hub.save()
        self.other_room.exits = {"south": 1}
        self.other_room.save()

        # Create users and players
        self.leader_user = User.objects.create_user(username="leader", password="password")
        self.leader = Player.objects.create(
            user=self.leader_user,
            location=self.hub,
            hp=100,
            hp_max=100,
            attack=10,
            defense=5,
            money=50,
            online=True,
        )

        self.member_user = User.objects.create_user(username="member", password="password")
        self.member = Player.objects.create(
            user=self.member_user,
            location=self.hub,
            hp=100,
            hp_max=100,
            attack=10,
            defense=5,
            money=50,
            online=True,
        )

        self.other_user = User.objects.create_user(username="other", password="password")
        self.other = Player.objects.create(
            user=self.other_user,
            location=self.hub,
            hp=100,
            hp_max=100,
            attack=10,
            defense=5,
            money=50,
            online=True,
        )

    def test_create_party(self):
        result = services.create_party(self.leader, "Test Party")
        self.assertIn("Party 'Test Party' created", result)
        self.assertTrue(Party.objects.filter(name="Test Party").exists())
        self.assertEqual(Party.objects.first().leader, self.leader)

    def test_create_party_while_in_party(self):
        services.create_party(self.leader)
        result = services.create_party(self.leader, "Another Party")
        self.assertIn("already in a party", result)

    def test_invite_to_party(self):
        services.create_party(self.leader)
        result = services.invite_to_party(self.leader, "member")
        self.assertIn("Invited member to the party", result)
        self.member.refresh_from_db()
        self.assertIsNotNone(self.member.party_invite)

    def test_invite_not_in_party(self):
        result = services.invite_to_party(self.leader, "member")
        self.assertIn("not in a party", result)

    def test_invite_not_leader(self):
        # Create party with member as leader, then try to invite with leader
        services.create_party(self.member)
        result = services.invite_to_party(self.leader, "other")
        self.assertIn("not in a party", result)

    def test_invite_target_not_online(self):
        services.create_party(self.leader)
        self.member.online = False
        self.member.save()
        result = services.invite_to_party(self.leader, "member")
        self.assertIn("not found or not online", result)

    def test_accept_party_invite(self):
        services.create_party(self.leader)
        services.invite_to_party(self.leader, "member")
        self.member.refresh_from_db()
        result = services.accept_party_invite(self.member)
        self.assertIn("joined", result)
        self.assertTrue(self.member.parties.exists())

    def test_accept_no_invite(self):
        result = services.accept_party_invite(self.member)
        self.assertIn("No pending party invitation", result)

    def test_party_max_size(self):
        services.create_party(self.leader, "Full Party")
        services.invite_to_party(self.leader, "member")
        self.member.refresh_from_db()
        services.accept_party_invite(self.member)
        self.leader.refresh_from_db()
        services.invite_to_party(self.leader, "other")
        self.other.refresh_from_db()
        services.accept_party_invite(self.other)
        # Now try to invite a 4th player (should fail - party is full)
        # Create a 4th player
        fourth_user = User.objects.create_user(username="fourth", password="password")
        _fourth = Player.objects.create(
            user=fourth_user,
            location=self.hub,
            hp=100,
            hp_max=100,
            attack=10,
            defense=5,
            money=50,
            online=True,
        )
        self.leader.refresh_from_db()
        result = services.invite_to_party(self.leader, "fourth")
        self.assertIn("Party is full", result)

    def test_leave_party(self):
        services.create_party(self.leader)
        services.invite_to_party(self.leader, "member")
        self.member.refresh_from_db()
        services.accept_party_invite(self.member)
        self.member.refresh_from_db()
        result = services.leave_party(self.member)
        self.assertIn("left the party", result)
        self.assertFalse(self.member.parties.exists())

    def test_leave_party_as_leader_disbands(self):
        services.create_party(self.leader)
        services.invite_to_party(self.leader, "member")
        services.accept_party_invite(self.member)
        result = services.leave_party(self.leader)
        self.assertIn("disbanded the party", result)
        self.assertFalse(Party.objects.exists())

    def test_get_party_status(self):
        services.create_party(self.leader, "Status Test")
        result = services.get_party_status(self.leader)
        self.assertIn("Status Test", result)
        self.assertIn("leader", result.lower())

    def test_get_party_status_not_in_party(self):
        result = services.get_party_status(self.leader)
        self.assertIn("not in a party", result)

    def test_party_movement(self):
        services.create_party(self.leader)
        services.invite_to_party(self.leader, "member")
        self.member.refresh_from_db()
        services.accept_party_invite(self.member)
        self.member.refresh_from_db()
        result = services.move_party_leader(self.leader, "north")
        self.assertIn("Other", result)
        self.member.refresh_from_db()
        self.assertEqual(self.member.location.id, 2)  # Member moved with leader

    def test_party_movement_not_leader(self):
        services.create_party(self.leader)
        services.invite_to_party(self.leader, "member")
        self.member.refresh_from_db()
        services.accept_party_invite(self.member)
        self.member.refresh_from_db()
        result = services.move_party_leader(self.member, "north")
        self.assertIn("Only the party leader", result)


class BotAITests(TransactionTestCase):
    def setUp(self):
        # Create rooms
        self.hub = Room.objects.create(
            id=1, name="Hub", description="The center.", safe_zone=True, zone="hub"
        )
        self.combat_room = Room.objects.create(
            id=2, name="Combat Zone", description="Dangerous.", safe_zone=False, zone="slums"
        )
        self.hub.exits = {"north": 2}
        self.hub.save()
        self.combat_room.exits = {"south": 1}
        self.combat_room.save()

        # Create bot player
        self.bot_user = User.objects.create_user(username="TestBot", password="password")
        self.bot = Player.objects.create(
            user=self.bot_user,
            location=self.combat_room,
            hp=100,
            hp_max=100,
            attack=15,
            defense=5,
            money=50,
            online=True,
            is_bot=True,
            bot_aggression=70,
            bot_social=50,
            karma=-50,
            lvl=5,
        )

        # Create NPC
        self.npc = NPC.objects.create(
            name="Test NPC",
            location=self.combat_room,
            hp=30,
            hp_max=30,
            attack=5,
            defense=2,
            lvl=2,
            money_drop=10,
            exp_drop=20,
            aggressive=True,
        )

    def test_bot_attacks_npc(self):
        """Test that bots can attack NPCs and gain EXP."""
        # Set last_bot_action to the past to ensure bot acts immediately
        from django.utils import timezone
        import datetime

        self.bot.last_bot_action = timezone.now() - datetime.timedelta(seconds=30)
        self.bot.save(update_fields=["last_bot_action"])

        # Check that NPC exists in room
        npcs = NPC.objects.filter(location=self.combat_room, hp__gt=0)
        self.assertTrue(npcs.exists(), "NPC should exist in combat room")

        # Bot should be able to attack NPC
        result = services.process_bot_ai(self.bot)

        # Debug output
        self.bot.refresh_from_db()
        self.npc.refresh_from_db()

        # Check if bot attacked (either killed NPC or started combat)
        # The NPC has exp_drop=20, so bot should have gained 10 (50% rate) if killed
        # Or bot should be in combat if NPC survived
        self.assertTrue(
            self.bot.exp > 0 or self.bot.last_combat_npc is not None,
            f"Bot should have EXP or be in combat. EXP={self.bot.exp}, last_combat_npc={self.bot.last_combat_npc}, NPC HP={self.npc.hp}, result={result}",
        )

    def test_bot_combat_tick_in_combat(self):
        """Test that bots in combat get their combat ticks processed."""
        # Create a fresh NPC with more HP to survive the first attack
        npc = NPC.objects.create(
            name="Durable NPC",
            location=self.combat_room,
            hp=100,
            hp_max=100,
            attack=5,
            defense=2,
            lvl=2,
            money_drop=10,
            exp_drop=20,
        )

        # Start combat
        services.attack_target(self.bot, "Durable NPC", auto=True)
        self.bot.refresh_from_db()

        # Set last_combat_tick to the past to simulate time passing
        from django.utils import timezone
        import datetime

        self.bot.last_combat_tick = timezone.now() - datetime.timedelta(seconds=5)
        self.bot.save(update_fields=["last_combat_tick"])

        # Process combat tick
        result = services.process_combat_tick(self.bot)

        # Should have combat output
        self.assertTrue(len(result) > 0)
        self.assertIn("hit", result.lower())

    def test_npc_healing_when_low_hp(self):
        """Test that NPCs regenerate HP when critically low."""
        from django.utils import timezone

        # Create low-HP NPC
        npc = NPC.objects.create(
            name="Healing Test", location=self.combat_room, hp=20, hp_max=100,
            attack=5, defense=2, lvl=2, money_drop=10, exp_drop=50,
            aggressive=True, resistance="none", weakness="none",
        )

        initial_hp = npc.hp

        # Process NPC AI multiple times (with delay between calls)
        for i in range(20):
            result = services.process_npc_ai(npc)
            npc.refresh_from_db()
            # NPC should heal when below 40% HP
            if npc.hp > initial_hp:
                break

        # NPC should have some HP regen
        self.assertGreater(npc.hp, initial_hp)
        # NPC should approach 40% HP threshold but not exceed it
        self.assertGreaterEqual(npc.hp, initial_hp)
        self.assertLessEqual(npc.hp, npc.hp_max * 0.4 + 10)

    def test_bot_exp_gain_equal_to_human(self):
        """Test that bots gain full EXP from NPC kills like humans."""
        # Set last_bot_action to past to ensure bot acts immediately
        from django.utils import timezone
        import datetime

        self.bot.last_bot_action = timezone.now() - datetime.timedelta(seconds=30)
        self.bot.save(update_fields=["last_bot_action"])

        # Delete setUp NPC to create a clean environment
        if self.npc:
            self.npc.delete()

        # Create fresh NPC for bot
        npc = NPC.objects.create(
            name="Exp Test NPC", location=self.combat_room, hp=1, hp_max=1,
            attack=5, defense=2, lvl=2, money_drop=10, exp_drop=200,
            aggressive=True, resistance="none", weakness="none",
        )

        # Bot kills NPC via process_bot_ai (full AI flow)
        import unittest.mock as mock
        with mock.patch("random.random", return_value=1.0):
            services.process_bot_ai(self.bot)

        self.bot.refresh_from_db()
        npc.refresh_from_db()

        # Bot should gain full EXP from NPC kill
        self.assertEqual(self.bot.exp, 200)
        # NPC should be dead
        self.assertFalse(npc.hp > 0)



def _make_room(room_id, name, zone, safe_zone=False):
    return Room.objects.create(
        id=room_id, name=name, description=name, zone=zone, safe_zone=safe_zone
    )


class AdvancedMoveTests(TestCase):
    """Tests for the new Lv 35-50 class moves."""

    def setUp(self):
        self.hub = _make_room(1, "Hub", "hub", safe_zone=True)
        self.combat_room = _make_room(2, "Combat Room", "slums")
        self.hub.exits = {"north": 2}
        self.hub.save()
        self.combat_room.exits = {"south": 1}
        self.combat_room.save()

        self.user = User.objects.create_user(username="samurai", password="password")
        self.player = Player.objects.create(
            user=self.user,
            location=self.combat_room,
            race="Cyborg",
            game_class="Street Samurai",
            lvl=35,
            hp=500,
            hp_max=500,
            mana=200,
            mana_max=200,
            attack=30,
            defense=10,
            money=100,
            online=True,
        )

    def _make_npc(self, name, hp=1, defense=2, exp_drop=40, money_drop=10, lvl=5):
        return NPC.objects.create(
            name=name,
            location=self.combat_room,
            hp=hp,
            hp_max=hp,
            attack=5,
            defense=defense,
            lvl=lvl,
            money_drop=money_drop,
            exp_drop=exp_drop,
        )

    def test_new_move_deals_damage_costs_mana_and_awards_exp(self):
        npc = self._make_npc("Rogue Drone", hp=1, exp_drop=40)
        mana_before = self.player.mana

        output = services.use_ability(self.player, "ronin_wrath", "rogue")

        self.player.refresh_from_db()
        npc.refresh_from_db()
        self.assertIn("RONIN_WRATH", output.upper())
        self.assertLessEqual(npc.hp, 0)
        self.assertLess(self.player.mana, mana_before)
        self.assertEqual(self.player.exp, 40)  # EXP awarded exactly once

    def test_new_move_requires_level(self):
        self.player.lvl = 1
        self.player.save(update_fields=["lvl"])
        output = services.use_ability(self.player, "ronin_wrath", "rogue")
        self.assertIn("Level required", output)

    def test_new_move_requires_mana(self):
        self.player.mana = 0
        self.player.save(update_fields=["mana"])
        output = services.use_ability(self.player, "ronin_wrath", "rogue")
        self.assertIn("INSUFFICIENT BUFFER", output)

    def test_true_strike_ignores_defense(self):
        self.player.lvl = 45
        self.player.save(update_fields=["lvl"])
        npc = self._make_npc("Armored Tank", hp=10000, defense=5000)

        output = services.use_ability(self.player, "ghost_edge", "tank")

        npc.refresh_from_db()
        self.assertIn("PIERCE", output)
        self.assertLess(npc.hp, 10000)  # damage despite massive defense


class AOECombatTests(TestCase):
    """Room-wide AOE: the whole sector is hit, every kill gives EXP, and
    survivors aggro the caster based on NPC/bot personalities."""

    def setUp(self):
        self.hub = _make_room(1, "Hub", "hub", safe_zone=True)
        self.combat_room = _make_room(2, "Combat Room", "slums")
        self.hub.exits = {"south": 2}
        self.hub.save()
        self.combat_room.exits = {"north": 1}
        self.combat_room.save()

        self.caster_user = User.objects.create_user(username="ninja", password="password")
        self.caster = Player.objects.create(
            user=self.caster_user,
            location=self.combat_room,
            race="Elf",
            game_class="Ninja",
            lvl=20,
            hp=500,
            hp_max=500,
            mana=200,
            mana_max=200,
            attack=30,
            defense=10,
            agi_stat=10,
            int_stat=10,
            money=100,
            online=True,
        )

    def _make_npc(self, name, hp=1, defense=2, exp_drop=40, aggressive=False):
        return NPC.objects.create(
            name=name,
            location=self.combat_room,
            hp=hp,
            hp_max=hp,
            attack=5,
            defense=defense,
            lvl=10,
            money_drop=10,
            exp_drop=exp_drop,
            aggressive=aggressive,
        )

    def test_aoe_hits_room_awards_exp_for_kills_and_aggros(self):
        weak_npc = self._make_npc("Weak Drone", hp=1, exp_drop=40, aggressive=False)
        tank_npc = self._make_npc("Heavy Drone", hp=100000, defense=0, aggressive=False)
        enemy_user = User.objects.create_user(username="victim", password="password")
        enemy = Player.objects.create(
            user=enemy_user,
            location=self.combat_room,
            game_class="Fixer",
            lvl=18,
            hp=1,
            hp_max=100,
            mana=50,
            mana_max=50,
            attack=10,
            defense=5,
            money=100,
            online=True,
        )

        output = services.use_ability(self.caster, "phantom_sweep", "")

        weak_npc.refresh_from_db()
        tank_npc.refresh_from_db()
        enemy.refresh_from_db()
        self.caster.refresh_from_db()

        # Whole room was hit
        self.assertIn("[AOE]", output)
        self.assertLessEqual(weak_npc.hp, 0)
        self.assertLess(tank_npc.hp, 100000)
        # EXP awarded for every kill: NPC exp_drop + PvP lvl*50
        self.assertEqual(self.caster.exp, 40 + 18 * 50)
        # Defeated player respawns at the hub with half HP and lost credits
        self.assertEqual(enemy.location.id, 1)
        self.assertEqual(enemy.hp, enemy.hp_max // 2)
        self.assertEqual(enemy.money, 75)
        # Survivors AGGRO: NPC turns hostile and engages
        self.assertTrue(tank_npc.aggressive)
        self.assertIsNotNone(self.caster.last_combat_npc)

    def test_aoe_spares_party_members(self):
        member_user = User.objects.create_user(username="partygoer", password="password")
        member = Player.objects.create(
            user=member_user,
            location=self.combat_room,
            game_class="Medie",
            lvl=20,
            hp=100000,
            hp_max=100000,
            mana=50,
            mana_max=50,
            attack=10,
            defense=5,
            money=0,
            online=True,
        )
        self._make_npc("Bait Drone", hp=100000)
        services.create_party(self.caster, "Crew")
        services.invite_to_party(self.caster, "partygoer")
        member.refresh_from_db()  # pick up the pending party_invite
        services.accept_party_invite(member)

        services.use_ability(self.caster, "phantom_sweep", "")

        member.refresh_from_db()
        self.assertEqual(member.hp, 100000)  # untouched

    def test_aoe_blocked_in_safe_zone(self):
        self.caster.location = self.hub
        self.caster.save(update_fields=["location"])
        output = services.use_ability(self.caster, "phantom_sweep", "")
        self.assertIn("prohibited", output)

    def test_aoe_aggros_bots_by_personality(self):
        self._make_npc("Bait Drone", hp=100000)
        vicious_user = User.objects.create_user(username="viciousbot", password="password")
        vicious = Player.objects.create(
            user=vicious_user,
            location=self.combat_room,
            game_class="Heavy",
            lvl=20,
            hp=1000,
            hp_max=1000,
            mana=50,
            mana_max=50,
            attack=10,
            defense=5,
            money=0,
            online=True,
            is_bot=True,
            bot_aggression=80,
        )
        coward_user = User.objects.create_user(username="cowardbot", password="password")
        coward = Player.objects.create(
            user=coward_user,
            location=self.combat_room,
            game_class="Medie",
            lvl=20,
            hp=1000,
            hp_max=1000,
            mana=50,
            mana_max=50,
            attack=10,
            defense=5,
            money=0,
            online=True,
            is_bot=True,
            bot_aggression=10,
        )

        output = services.use_ability(self.caster, "phantom_sweep", "")

        vicious.refresh_from_db()
        coward.refresh_from_db()
        # Vicious bot counter-attacks the caster...
        self.assertEqual(vicious.last_combat_player.id, self.caster.id)
        self.assertTrue(vicious.auto_attack)
        # ...while the coward flees the sector.
        self.assertNotEqual(coward.location.id, self.combat_room.id)
        self.assertIn("AGGRO", output)


class AFKTeleportTests(TestCase):
    """The starting location randomly teleports AFK players and bots to
    level-appropriate sectors after 2 minutes; stuck bots get rescued."""

    def setUp(self):
        self.hub = _make_room(1, "Hub", "hub", safe_zone=True)
        self.empty_room = _make_room(2, "Dead Alley", "slums")
        self.hunting_room = _make_room(3, "Hunting Grounds", "slums")
        self.hunting_room.exits = {"south": 1}
        self.hunting_room.save()
        NPC.objects.create(
            name="Prey Drone",
            location=self.hunting_room,
            hp=50,
            hp_max=50,
            attack=5,
            defense=2,
            lvl=2,
            money_drop=10,
            exp_drop=20,
        )

    def _make_player(self, username, **kwargs):
        user = User.objects.create_user(username=username, password="password")
        defaults = dict(
            location=self.hub,
            hp=100,
            hp_max=100,
            mana=50,
            mana_max=50,
            attack=10,
            defense=5,
            money=100,
            online=True,
        )
        defaults.update(kwargs)
        return Player.objects.create(user=user, **defaults)

    def _age(self, player, seconds, move_seconds=None):
        from django.utils import timezone

        stamp = timezone.now() - timezone.timedelta(seconds=seconds)
        player.last_activity = stamp
        player.last_seen = stamp
        player.last_move_time = timezone.now() - timezone.timedelta(
            seconds=move_seconds if move_seconds is not None else seconds
        )
        player.save(update_fields=["last_activity", "last_seen", "last_move_time"])

    def test_afk_user_in_hub_teleported_after_2_minutes(self):
        player = self._make_player("idler", lvl=1)
        self._age(player, 360)  # 6 minutes AFK -> teleport is guaranteed

        services.process_afk_players(force=True)
        player.refresh_from_db()

        self.assertEqual(player.location.id, self.hunting_room.id)
        self.assertIn("[TELEPORT]", player.notification)
        # Relocation costs the player nothing
        self.assertEqual(player.money, 100)
        self.assertEqual(player.hp, 100)

    def test_active_user_in_hub_not_teleported(self):
        player = self._make_player("active", lvl=1)
        self._age(player, 5)

        services.process_afk_players(force=True)
        player.refresh_from_db()

        self.assertEqual(player.location.id, self.hub.id)

    def test_afk_user_outside_hub_is_not_relocated(self):
        player = self._make_player("wanderer", lvl=1, location=self.empty_room)
        self._age(player, 1800)  # 30 min AFK outside the hub: no teleport

        services.process_afk_players(force=True)
        player.refresh_from_db()

        self.assertEqual(player.location.id, self.empty_room.id)
        self.assertTrue(player.online)  # not kicked either (under 1 hour)

    def test_afk_user_in_combat_is_never_teleported(self):
        player = self._make_player("fighter", lvl=10, location=self.hunting_room)
        self._age(player, 360)
        player.last_combat_npc = NPC.objects.filter(location=self.hunting_room).first()
        player.save(update_fields=["last_combat_npc"])

        services.process_afk_players(force=True)
        player.refresh_from_db()

        self.assertEqual(player.location.id, self.hunting_room.id)

    def test_stuck_bot_is_teleported_back_into_action(self):
        bot = self._make_player(
            "stuckbot",
            lvl=2,
            is_bot=True,
            bot_aggression=70,
            location=self.empty_room,
        )
        self._age(bot, 660)  # stuck for 11 minutes -> guaranteed rescue

        services.process_afk_players(force=True)
        bot.refresh_from_db()

        self.assertEqual(bot.location.id, self.hunting_room.id)
        self.assertIn("[TELEPORT]", bot.notification)


class InactivityKickTests(TestCase):
    """Players who do nothing for 1 hour are kicked to the login page and
    lose absolutely nothing."""

    def setUp(self):
        self.hub = _make_room(1, "Hub", "hub", safe_zone=True)
        self.user = User.objects.create_user(username="lazy", password="password")
        self.player = Player.objects.create(
            user=self.user,
            location=self.hub,
            lvl=7,
            hp=100,
            hp_max=100,
            mana=50,
            mana_max=50,
            attack=30,
            defense=5,
            money=100,
            exp=50,
            online=True,
        )
        self.client = Client()
        self.client.login(username="lazy", password="password")

    def _go_idle(self, seconds=3700):
        from django.utils import timezone

        self.player.last_activity = timezone.now() - timezone.timedelta(seconds=seconds)
        self.player.last_seen = self.player.last_activity
        self.player.save(update_fields=["last_activity", "last_seen"])

    def test_command_view_kicks_after_1_hour_with_no_losses(self):
        self._go_idle()

        response = self.client.post(
            "/command/", data=json.dumps({"command": "look"}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 401)
        self.player.refresh_from_db()
        self.assertFalse(self.player.online)
        # Kicked players lose NOTHING
        self.assertEqual(self.player.money, 100)
        self.assertEqual(self.player.exp, 50)
        self.assertEqual(self.player.hp, 100)
        self.assertIn("log back in", response.json()["message"])

    def test_poll_view_kicks_after_1_hour(self):
        self._go_idle()

        response = self.client.get("/poll/")
        data = response.json()

        self.assertFalse(data["authenticated"])
        self.assertEqual(data["status"], "kicked_inactivity")
        self.player.refresh_from_db()
        self.assertFalse(self.player.online)
        self.assertEqual(self.player.money, 100)  # nothing lost

    def test_recently_active_player_not_kicked(self):
        self._go_idle(30)

        response = self.client.get("/poll/")

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json().get("status"), "kicked_inactivity")
        self.player.refresh_from_db()
        self.assertTrue(self.player.online)

    def test_idle_sweep_marks_player_offline(self):
        self._go_idle()
        services.process_afk_players(force=True)
        self.player.refresh_from_db()
        self.assertFalse(self.player.online)


class BotEnhancementTests(TestCase):
    """Bots recover from rest, auto-equip upgrades and can be wiped/regenerated."""

    def setUp(self):
        self.hub = _make_room(1, "Hub", "hub", safe_zone=True)
        self.alley = _make_room(2, "Alley", "slums")
        self.grounds = _make_room(3, "Grounds", "slums")
        self.grounds.exits = {"south": 1}
        self.grounds.save()
        NPC.objects.create(
            name="Target Drone",
            location=self.grounds,
            hp=50,
            hp_max=50,
            attack=5,
            defense=2,
            lvl=2,
            money_drop=10,
            exp_drop=20,
        )

    def test_resting_bot_actually_recovers(self):
        from django.utils import timezone

        bot_user = User.objects.create_user(username="restbot", password="password")
        bot = Player.objects.create(
            user=bot_user,
            location=self.alley,
            game_class="Heavy",
            lvl=5,
            hp=20,
            hp_max=100,
            mana=10,
            mana_max=50,
            attack=10,
            defense=5,
            money=0,
            online=True,
            is_bot=True,
            hea_stat=10,
            int_stat=10,
            resting=True,
            rest_started_at=timezone.now() - timezone.timedelta(seconds=60),
            last_bot_action=timezone.now() - timezone.timedelta(seconds=60),
        )

        services.process_bot_ai(bot)
        bot.refresh_from_db()

        # Bots used to rest forever; now they regenerate and rejoin the fight
        self.assertGreater(bot.hp, 20)

    def test_bot_auto_equips_upgrade(self):
        bot_user = User.objects.create_user(username="gearbot", password="password")
        bot = Player.objects.create(
            user=bot_user,
            location=self.alley,
            game_class="Street Samurai",
            lvl=5,
            hp=100,
            hp_max=100,
            mana=50,
            mana_max=50,
            attack=30,  # includes the +5 from the starter weapon
            defense=5,
            money=0,
            online=True,
            is_bot=True,
        )
        starter = Item.objects.create(
            name="Rusty Shiv", item_type="weapon", subtype="one-handed", attack_bonus=5
        )
        upgrade = Item.objects.create(
            name="Mono Katana", item_type="weapon", subtype="one-handed", attack_bonus=20
        )
        InventoryItem.objects.create(player=bot, item=starter, equipped=True)

        equipped = services.bot_auto_equip(bot, upgrade)
        bot.refresh_from_db()

        self.assertTrue(equipped)
        self.assertEqual(bot.attack, 45)  # 30 - 5 (old) + 20 (new)
        self.assertTrue(
            InventoryItem.objects.filter(player=bot, item=upgrade, equipped=True).exists()
        )
        self.assertFalse(
            InventoryItem.objects.filter(player=bot, item=starter, equipped=True).exists()
        )

    def test_bot_ignores_non_upgrade_gear(self):
        bot_user = User.objects.create_user(username="pickybot", password="password")
        bot = Player.objects.create(
            user=bot_user,
            location=self.alley,
            game_class="Street Samurai",
            lvl=5,
            hp=100,
            hp_max=100,
            mana=50,
            mana_max=50,
            attack=30,
            defense=5,
            money=0,
            online=True,
            is_bot=True,
        )
        good = Item.objects.create(
            name="Good Blade", item_type="weapon", subtype="one-handed", attack_bonus=25
        )
        junk = Item.objects.create(
            name="Junk Blade", item_type="weapon", subtype="one-handed", attack_bonus=1
        )
        InventoryItem.objects.create(player=bot, item=good, equipped=True)

        self.assertFalse(services.bot_auto_equip(bot, junk))

    def test_wipe_users_and_create_fresh_bots(self):
        from django.contrib.auth.models import User as DjangoUser
        from django.core.management import call_command

        human_user = DjangoUser.objects.create_user(username="human1", password="password")
        Player.objects.create(
            user=human_user,
            location=self.hub,
            hp=100,
            hp_max=100,
            mana=50,
            mana_max=50,
            attack=10,
            defense=5,
            money=10,
            online=True,
        )
        DjangoUser.objects.create_superuser("admin", "admin@example.com", "password")

        call_command("create_bots", wipe_users=True, count=5)

        self.assertFalse(DjangoUser.objects.filter(username="human1").exists())
        self.assertTrue(DjangoUser.objects.filter(username="admin").exists())
        bots = Player.objects.filter(is_bot=True)
        self.assertEqual(bots.count(), 5)
        for bot in bots:
            self.assertIsNotNone(bot.last_activity)
            self.assertIsNotNone(bot.last_move_time)
