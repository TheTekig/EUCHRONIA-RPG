class AliveModel():
    def __init__(self, name, hp, strength, defense, speed):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.strength = strength
        self.defense = defense
        self.speed = speed
        self.effect = []
    
    def is_alive(self):
        return self.hp > 0
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
    
    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
    
class PlayerModel(AliveModel):
    def __init__(self, name, classes_data, skill_data, position = None):
        super().__init__(
            name = name, 
            hp = classes_data['maxlife'], 
            strength = classes_data['strength'], 
            defense = classes_data['defense'], 
            speed = classes_data['speed'],
            effect = []
            )

        self.level = 1
        self.experience = 0

        self.position = position

        self.gold = 0

        self.class_name = classes_data['name']
        self.skills = []

        self.inventory = []
        self.key_itens = []

        self.equipment = {'weapon': [], 'armor' : [], 'accessory': []}
        self.max_equipment = {'weapon': 1, 'armor' : 1, 'accessory': 2}    

    #region Equipment Attribute

    def _get_total_attribute(self, attribute_name: str, base_value: int):
        total_bonus = 0
        for equipment in self.equipment.values():
            for item in equipment:
                total_bonus += item.bonus.get(attribute_name, 0)
        return base_value + total_bonus
    
    @property
    def total_defense(self):
        return self._get_total_attribute("defense", self.defense)
    
    @property
    def total_strength(self):
        return self._get_total_attribute("strength", self.strength)
    
    @property
    def total_speed(self):
        return self._get_total_attribute("speed", self.speed)
    
    #endregion

    #region Leveling UP

    def gain_experience(self, enemy):
        self.experience += enemy.experience
        experience_to_next_level = self.level * 100
        if self.experience >= experience_to_next_level:
            self.experience -= experience_to_next_level
            self.level_up()
            experience_to_next_level = self.level * 100

    def level_up(self):
        self.level += 1
        self.max_hp += self.class_name['upgrade']['hp']
        self.strength += self.class_name['upgrade']['strength'] 
        self.defense += self.class_name['upgrade']['defense']
        self.speed += self.class_name['upgrade']['speed']
        self.hp = self.max_hp

    #endregion

class EnemyModel(AliveModel):
    def __init__(self, enemy_data):
        super().__init__(
            name = enemy_data.get('name', 'Unknow Enemy'), 
            hp = enemy_data.get('maxlife', 10), 
            strength = enemy_data.get('strength', 5), 
            defense = enemy_data.get('defense', 0), 
            speed =  enemy_data.get('speed', 10)
            )
        self.type = enemy_data.get('type', "Unknow Creature")
        self.experience = enemy_data.get('experience', 10)
        self.loot = enemy_data.get('loot', 'Nothing Userfull')
        self.region = enemy_data['region']
