from django.db import models
from django.contrib.auth.models import User
from django.db.models import Index


class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    # weapon, armor, consumable, misc, drug, scroll
    item_type = models.CharField(max_length=50)
    # e.g., 'leather', 'heavy', 'one-handed', 'two-handed'
    subtype = models.CharField(max_length=50, default="none")
    price = models.IntegerField(default=0)
    # common, uncommon, rare, epic, legendary
    rarity = models.CharField(max_length=20, default="common")

    # Weapon/Armor stats
    attack_bonus = models.IntegerField(default=0)
    defense_bonus = models.IntegerField(default=0)
    speed_bonus = models.IntegerField(default=0)
    heal_amount = models.IntegerField(default=0)

    # Stat bonuses
    str_bonus = models.IntegerField(default=0)
    int_bonus = models.IntegerField(default=0)
    wil_bonus = models.IntegerField(default=0)
    agi_bonus = models.IntegerField(default=0)
    hea_bonus = models.IntegerField(default=0)
    cha_bonus = models.IntegerField(default=0)

    # physical, fire, water, earth, air
    element = models.CharField(max_length=20, default="physical")

    # Drug/Scroll effects
    addiction_chance = models.FloatField(default=0.0)
    warp_to_room = models.ForeignKey(
        "Room", on_delete=models.SET_NULL, null=True, blank=True, related_name="warp_items"
    )
    # Poison/bleed venom fields for physical poison weapons
    poison_damage = models.IntegerField(default=0)  # Damage per tick
    poison_duration = models.IntegerField(default=0)  # Ticks lasting (3 rounds)
    bleed_damage = models.IntegerField(default=0)  # Damage per tick
    bleed_duration = models.IntegerField(default=0)  # Ticks lasting (3 rounds)

    class Meta:
        indexes = [
            Index(fields=["item_type", "subtype"]),
            Index(fields=["name"]),
            Index(fields=["price"]),
            Index(fields=["rarity"]),
        ]

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    exits = models.JSONField(default=dict)
    shop_name = models.CharField(max_length=255, null=True, blank=True)
    transporter_name = models.CharField(max_length=255, null=True, blank=True)
    safe_zone = models.BooleanField(default=False)
    zone = models.CharField(max_length=100, default="hub")  # zone identifier
    theme = models.CharField(max_length=100, default="urban")  # visual theme
    map_x = models.IntegerField(default=0)  # grid position for map
    map_y = models.IntegerField(default=0)
    items = models.ManyToManyField(Item, blank=True, related_name="rooms")
    shop_inventory = models.ManyToManyField(Item, blank=True, related_name="shops")
    # Procedural flags
    respawn_npcs = models.BooleanField(default=True)
    respawn_timer = models.IntegerField(default=600)  # seconds until NPC respawn (10 min)
    last_npc_spawn = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            Index(fields=["zone"]),
            Index(fields=["safe_zone"]),
        ]

    def __str__(self):
        return self.name


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    lvl = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    money = models.IntegerField(default=25)
    hp = models.IntegerField(default=100)
    hp_max = models.IntegerField(default=100)
    mana = models.IntegerField(default=20)
    mana_max = models.IntegerField(default=20)

    # Stats
    str_stat = models.IntegerField(default=10)
    int_stat = models.IntegerField(default=10)
    wil_stat = models.IntegerField(default=10)
    agi_stat = models.IntegerField(default=10)
    hea_stat = models.IntegerField(default=10)
    cha_stat = models.IntegerField(default=10)

    stat_points = models.IntegerField(default=0)

    attack = models.IntegerField(default=10)
    defense = models.IntegerField(default=5)

    location = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    # Cyborg, Bio-hacked, Android, Mutant, Human
    race = models.CharField(max_length=50)
    # Male, Female, Non-binary, Other
    gender = models.CharField(max_length=20, default="Other")
    # Street Samurai, Netrunner, Techie, Medie, Fixer
    game_class = models.CharField(max_length=50)
    online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    # Karma / alignment: -100 (Villain) to 100 (Saint)
    karma = models.IntegerField(default=0)

    # Death counter for wall of death
    deaths = models.IntegerField(default=0)

    inventory = models.ManyToManyField(Item, through="InventoryItem")

    # Drug/Addiction System
    addiction_points = models.IntegerField(default=0)  # 0 to 100
    withdrawal_timer = models.IntegerField(default=0)  # ticks since last use

    # Combat state
    last_combat_npc = models.ForeignKey(
        "NPC", on_delete=models.SET_NULL, null=True, blank=True, related_name="combating_players"
    )
    last_combat_player = models.ForeignKey(
        "Player",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="combating_players_target",
    )

    # Combat Mode
    auto_attack = models.BooleanField(default=False)
    last_combat_tick = models.DateTimeField(null=True, blank=True)

    # Sneaking state
    hidden = models.BooleanField(default=False)

    # Resting state
    resting = models.BooleanField(default=False)
    rest_started_at = models.DateTimeField(null=True, blank=True)

    # PvP notification - message shown to player on next poll
    notification = models.TextField(default="", blank=True)

    # Party invitation notification
    party_invite = models.ForeignKey(
        "Party", on_delete=models.SET_NULL, null=True, blank=True, related_name="invited_players"
    )

    # Bot identification
    is_bot = models.BooleanField(default=False)
    bot_karma = models.IntegerField(default=0)  # Bot's alignment for behavior
    bot_aggression = models.IntegerField(default=50)  # 0-100, likelihood to attack players
    bot_social = models.IntegerField(default=50)  # 0-100, likelihood to party with players
    # Bot personality archetype driving combat, social, and movement behavior.
    bot_personality = models.CharField(
        max_length=20,
        default="wanderer",
        help_text="Personality archetype: aggressive, mercenary, vigilante, social, trader, explorer, coward, berserker, hermit, chaotic",
    )
    last_bot_action = models.DateTimeField(null=True, blank=True)  # Track last AI action

    # AFK tracking: last time the player/bot actually DID something
    # (command, movement, combat, bot action). Used for the 2-minute
    # Hub AFK teleport and the 1-hour inactivity kick.
    last_activity = models.DateTimeField(null=True, blank=True)
    # Last time the player/bot physically changed rooms (stuck-bot detection)
    last_move_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            Index(fields=["online", "is_bot"]),
            Index(fields=["location", "online"]),
            Index(fields=["lvl", "exp"]),
            Index(fields=["karma"]),
            Index(fields=["deaths"]),
            Index(fields=["is_bot", "online"]),
        ]

    def __str__(self):
        return self.user.username


class InventoryItem(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    equipped = models.BooleanField(default=False)
    quantity = models.IntegerField(default=1)

    class Meta:
        indexes = [
            Index(fields=["player", "equipped"]),
            Index(fields=["player", "item"]),
        ]


class NPC(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.ForeignKey(Room, on_delete=models.CASCADE)
    attack = models.IntegerField()
    defense = models.IntegerField()
    hp = models.IntegerField()
    hp_max = models.IntegerField()
    lvl = models.IntegerField()
    money_drop = models.IntegerField()
    exp_drop = models.IntegerField()
    aggressive = models.BooleanField(default=True)
    # drone, gang, corporate, boss, dealer, vigilante
    npc_type = models.CharField(max_length=50, default="drone")
    respawnable = models.BooleanField(default=True)

    # Karma Alignment: -100 to 100.
    # Positive alignment NPCs attack negative karma players and vice versa.
    karma_alignment = models.IntegerField(default=0)

    # Elemental system
    element = models.CharField(max_length=20, default="physical")
    weakness = models.CharField(max_length=20, default="none")
    resistance = models.CharField(max_length=20, default="none")

    # Weapon the NPC is currently using
    weapon = models.ForeignKey(
        "Item", on_delete=models.SET_NULL, null=True, blank=True, related_name="wielding_npcs"
    )

    # Last time the NPC moved (for random movement)
    last_move_time = models.DateTimeField(null=True, blank=True)

    drops = models.ManyToManyField(Item, blank=True)

    class Meta:
        indexes = [
            Index(fields=["location", "hp"]),
            Index(fields=["hp"]),
            Index(fields=["npc_type"]),
            Index(fields=["location"]),
        ]

    def __str__(self):
        return self.name

    def get_effective_attack(self):
        """Calculate attack including weapon bonus."""
        base_attack = self.attack
        if self.weapon and self.weapon.attack_bonus:
            base_attack += self.weapon.attack_bonus
        return base_attack

    def get_effective_element(self):
        """Get element, preferring weapon element if available."""
        if self.weapon and self.weapon.element and self.weapon.element != "physical":
            return self.weapon.element
        return self.element


class ChatMessage(models.Model):
    sender = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            Index(fields=["timestamp"]),
            Index(fields=["room", "timestamp"]),
        ]


class GameWorld(models.Model):
    """Singleton model to store world generation metadata."""

    seed = models.IntegerField(default=0)
    generated_at = models.DateTimeField(auto_now=True)
    total_rooms = models.IntegerField(default=0)
    total_npcs = models.IntegerField(default=0)
    total_items = models.IntegerField(default=0)
    version = models.IntegerField(default=1)


class ProceduralWeaponSpawn(models.Model):
    """Tracks procedurally generated weapons in each zone."""

    zone = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    spawned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["zone", "item"]
        indexes = [
            Index(fields=["zone", "spawned_at"]),
        ]


class Party(models.Model):
    """A party of up to 3 players led by one player."""

    name = models.CharField(max_length=100, default="Unnamed Party")
    leader = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="led_parties")
    members = models.ManyToManyField(Player, through="PartyMembership", related_name="parties")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Leader: {self.leader.user.username})"

    @property
    def member_count(self):
        return self.members.count()

    @property
    def is_full(self):
        return self.member_count >= 3


class PartyMembership(models.Model):
    """Through model for Party membership with invitation status."""

    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    invited = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["party", "player"]
