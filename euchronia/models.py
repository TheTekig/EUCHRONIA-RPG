from enum import Enum, auto 

class HitResult(Enum):
    MISS = auto()
    SCRATCH = auto()
    HIT = auto()


class AliveModel():
    def __init__(self, name, hp, strength, defense, speed):
        self.name = name
        self.maxhp = hp
        self.hp = hp
        self.strength = strength
        self.defense = defense
        self.speed = speed
        self.action_time = 0
        self.effect = []
        self.efeitos_ativos = {}
        self.action_time = 0
    
    #region Combat 
    
    def is_alive(self):
        return self.hp > 0
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
    
    def heal(self, amount):
        self.hp += amount
        if self.hp > self.maxhp:
            self.hp = self.maxhp
            
    #endregion

    #region Effects/Control
    
    def apply_effect(self, nome, dados):
        """Adiciona ou atualiza um efeito ativo."""
        self.efeitos_ativos[nome] = dados

    def has_effect(self, nome):
        return nome in self.efeitos_ativos

    def remove_effect(self, nome):
        if nome in self.efeitos_ativos:
            del self.efeitos_ativos[nome]

    def get_effect_multiplier(self, atributo):
        """
        Retorna o multiplicador final de um atributo considerando todos os efeitos ativos.
        Exemplo: defense_multiplier = 1.5 em um efeito e 0.8 em outro => resultado 1.2
        """
        multiplicador_total = 1.0
        for dados in self.efeitos_ativos.values():
            efeitos = dados.get("efeitos", {})
            if f"{atributo}_multiplier" in efeitos:
                multiplicador_total *= efeitos[f"{atributo}_multiplier"]
        return multiplicador_total
        
    #endregion

class PlayerModel(AliveModel):
    def __init__(self, name, classes_data, position = None):
        super().__init__(
            name = name, 
            hp = classes_data['maxhp'], 
            strength = classes_data['strength'], 
            defense = classes_data['defense'], 
            speed = classes_data['speed'],
            action_time = 0
            )

        self.level = 1
        self.experience = 0

        self.position = position

        self.gold = 0

        self.class_name = classes_data['name']
        self.class_data = classes_data
        self.skills = []

        self.inventory = []
        self.key_itens = []

        self.equipment = {'weapon': [], 'armor' : [], 'accessory': []}
        self.max_equipment = {'weapon': 1, 'armor' : 1, 'accessory': 2}    


    def _status(self, all_itens_data):
        """Exibe o status completo do jogador."""
        print("\n--- STATUS DO HERÓI ---")
        print(f"Nome: {self.name} | Classe: {self.class_name}")
        print(f"Nível: {self.level} | XP: {self.experience}")
        print(f"Vida: {self.hp}/{self.maxhp}")
        print("-" * 20)
        # As propriedades 'total_strength', etc., agora precisam dos dados dos itens
        print(f"Força Total: {self.total_strength(all_itens_data)}")
        print(f"Defesa Total: {self.total_defense(all_itens_data)}")
        print(f"Velocidade Total: {self.total_speed(all_itens_data)}")
        print("-" * 20)
        print("Equipamento:")
        for slot, items in self.equipment.items():
            item_names = ", ".join(items) if items else "Vazio"
            print(f"  - {slot.capitalize()}: {item_names}")
        print("-----------------------\n")
        input("Pressione Enter para continuar...")

    
    #region Equipment Attribute

    def _get_total_attribute(self, attribute_name: str, base_value: int, all_items_data: dict):
        total_bonus = 0
        for equipment in self.equipment.values():
            for item in equipment:
                item_info = all_items_data.get(item,{})
                if item_info and "bonus" in item_info:
                    total_bonus += item_info["bonus"].get(attribute_name,0)
        return base_value + total_bonus
    
    @property
    def total_defense(self, all_items_data:dict):
        return self._get_total_attribute("defense", self.defense, all_items_data)
    
    @property
    def total_strength(self, all_items_data:dict):
        return self._get_total_attribute("strength", self.strength, all_items_data)
    
    @property
    def total_speed(self, all_items_data:dict):
        return self._get_total_attribute("speed", self.speed, all_items_data)
    
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
        self.max_hp += self.class_data['upgrade']['hp']
        self.strength += self.class_data['upgrade']['strength'] 
        self.defense += self.class_data['upgrade']['defense']
        self.speed += self.class_data['upgrade']['speed']
        self.hp = self.max_hp

    #endregion

class EnemyModel(AliveModel):
    def __init__(self, enemy_data):
        super().__init__(
            name = enemy_data.get('name', 'Unknow Enemy'), 
            hp = enemy_data.get('maxhp', 10), 
            strength = enemy_data.get('strength', 5), 
            defense = enemy_data.get('defense', 0), 
            speed =  enemy_data.get('speed', 10),
            action_time = 0
            )
        self.type = enemy_data.get('type', "Unknow Creature")
        self.experience = enemy_data.get('experience', 10)
        self.loot = enemy_data.get('loot', 'Nothing Userfull')
        self.region = enemy_data['region']
        self.skills = enemy_data['skills']
