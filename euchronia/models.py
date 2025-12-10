from termcolor import colored
from random import choices
from enum import Enum, auto 

class HitResult(Enum): # Enum para representar o resultado de um ataque | Combat_logic
    MISS = auto()
    SCRATCH = auto()
    HIT = auto()

class AliveModel(): # Classe base para entidades vivas no jogo (heróis e inimigos)
    def __init__(self, name, hp, maxhp, strength, defense, speed):
        self.name = name
        self.maxhp = maxhp
        self.hp = hp
        self.strength = strength
        self.defense = defense
        self.speed = speed
        self.effect = []
        self.efeitos_ativos = {}
    
    #region Combat 
    
    def is_alive(self): # Verifica se o personagem está vivo
        return self.hp > 0
    
    def take_damage(self, damage): # Reduz a vida do personagem ao receber dano
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
    
    def heal(self, amount): # Cura o personagem
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

class PlayerModel(AliveModel): # Classe para o herói do jogador | herda de AliveModel
    def __init__(self, name, classes_data, position = "C"):
        super().__init__(
            name = name, 
            hp = classes_data['maxhp'], 
            maxhp = classes_data['maxhp'],
            strength = classes_data['strength'], 
            defense = classes_data['defense'], 
            speed = classes_data['speed'],
            ) # Chama o construtor da classe base AliveModel

        #region Player Attributes

        self.level = 1
        self.experience = 0
        self.action_time = 0        # Tempo de ação para o sistema ATB
        self.position = position    # Onde o jogador está no mapa

        self.gold = 0

        self.class_name = classes_data['name'] # Nome da classe do jogador
        self.class_data = classes_data # Dados completos da classe do jogador
        self.skills = []

        self.inventory = [] # Itens no inventário do jogador
        self.key_itens = [] # Itens chave do jogador

        self.equipment = {'weapon': [], 'armor' : [], 'accessory': []}  # Equipamentos do jogador
        self.max_equipment = {'weapon': 1, 'armor' : 1, 'accessory': 2}     # Limites de equipamentos

        #endregion


    def _status(self, all_itens_data): # Exibe o status completo do jogador
        """
        """

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
        
    #region  OBJECT TO/FROM DICT
    
    def _to_dict(self): # Converte o objeto PlayerModel em um dicionário para salvar em JSON
        return { 
            'name'       : self.name,
            'hp'         : self.hp,
            'maxhp'      : self.maxhp,
            'strength'   : self.strength,
            'defense'    : self.defense,
            'speed'      : self.speed,
            'level'      : self.level,
            'experience' : self.experience,
            'position'   : self.position,
            'gold'       : self.gold,
            'class_name' : self.class_name,
            'class_data' : self.class_data,
            'skills'     : [skill for skill in self.skills],
            'inventory'  : [item for item in self.inventory],
            'key_itens'  : [item for item in self.key_itens],
            'equipment'  : self.equipment
        } 
        
    @classmethod # Construtor de classe para criar um PlayerModel a partir de um dicionário
    def _from_dict(cls, player_data): # Cria um objeto PlayerModel a partir de um dicionário
        player = cls( 
            name=player_data['name'],
            classes_data=player_data['class_data'],
            position=player_data['position']
        ) # Inicializa o objeto com os dados básicos
        
        # Preenche os atributos restantes | Player_data é um dicionário com os dados do jogador
        player.hp=player_data['hp']
        player.maxhp=player_data['maxhp']
        player.strength=player_data['strength']
        player.defense=player_data['defense']
        player.speed=player_data['speed']
        player.level=player_data['level']
        player.experience=player_data['experience']
        player.gold=player_data['gold']
        player.class_name=player_data['class_name']
        player.class_data=player_data['class_data']
        player.skills=player_data['skills']
        player.inventory=player_data['inventory']
        player.key_itens=player_data['key_itens']
        player.equipment=player_data['equipment']

        return player
    
    #endregion
    
    #region Equipment Attribute

    def _get_total_attribute(self, attribute_name: str, base_value: int, all_items_data: dict): # Calcula o valor total de um atributo considerando os bônus dos equipamentos
        total_bonus = 0
        for equipment in self.equipment.values(): # Para cada tipo de equipamento
            for item in equipment: # Para cada item equipado
                item_info = all_items_data.get(item,{}) # Obtém os dados do item a partir do dicionário de todos os itens
                if item_info and "bonus" in item_info: # Se o item existe e tem bônus
                    total_bonus += item_info["bonus"].get(attribute_name,0) # Adiciona o bônus do atributo ao total
        return base_value + total_bonus # Retorna o valor base mais o total de bônus dos equipamentos
    
    def total_defense(self, all_items_data:dict): # Calcula a defesa total do jogador considerando os equipamentos
        return self._get_total_attribute("defense", self.defense, all_items_data)
    
    def total_strength(self, all_items_data:dict): # Calcula a força total do jogador considerando os equipamentos
        return self._get_total_attribute("strength", self.strength, all_items_data)
    
    def total_speed(self, all_items_data:dict): # Calcula a velocidade total do jogador considerando os equipamentos
        return self._get_total_attribute("speed", self.speed, all_items_data)
    
    #endregion
    
    #region Leveling UP

    def gain_experience(self, enemy): # Ganha experiência ao derrotar um inimigo e verifica se sobe de nível
        self.experience += enemy.experience # Adiciona a experiência do inimigo derrotado
        experience_to_next_level = self.level * 100
        if self.experience >= experience_to_next_level:
            self.experience -= experience_to_next_level
            self.level_up() # Sobe de nível
            experience_to_next_level = self.level * 100 # Atualiza a experiência necessária para o próximo nível

    def level_up(self): # Sobe de nível e aumenta os atributos do jogador
        self.level += 1
        # Aumenta os atributos baseados nos dados da classe
        self.maxhp += self.class_data['upgrade']['maxhp'] 
        self.strength += self.class_data['upgrade']['strength'] 
        self.defense += self.class_data['upgrade']['defense']
        self.speed += self.class_data['upgrade']['speed']
        # Restaura a vida ao subir de nível
        self.hp = self.maxhp
        

    #endregion
    
    #region Add Item to Invetory

    def _add_item_to_inventory(self, item): # Adiciona um item ao inventário do jogador
        self.inventory.append(item)
        
    #endregion
    
    #region Add Skill to Skillset
    
    def _learn_skill(self, skill_name): # Adiciona uma habilidade ao conjunto de habilidades do jogador
        if skill_name not in self.skills:
            self.skills.append(skill_name)
    
    #endregion

class EnemyModel(AliveModel): # Classe para inimigos | herda de AliveModel
    def __init__(self, enemy_data): # Inicializa o inimigo com os dados fornecidos | Enemy_data é um dicionário com os dados do inimigo
        super().__init__(
            name = enemy_data.get('name', 'Unknow Enemy'), 
            hp = enemy_data.get('maxhp', 10), 
            maxhp = enemy_data.get('maxhp', 10),
            strength = enemy_data.get('strength', 5), 
            defense = enemy_data.get('defense', 0), 
            speed =  enemy_data.get('speed', 10),
            ) # Chama o construtor da classe base AliveModel

        #region Enemy Attributes
        
        self.action_time = 0
        self.type = enemy_data.get('type', "Unknow Creature")
        
        self.experience = enemy_data.get('experience', 10)
        self.loot = enemy_data.get('loot', 'Nothing Userfull') # Itens que o inimigo pode dropar
        
        self.region = enemy_data.get('region', 'Unknown Region') # Região onde o inimigo pode ser encontrado
        
        self.skills = enemy_data.get('skills', ["Flechada"]) # Habilidades do inimigo | lista de strings | caso não tenha habilidades, atribui "Flechada" como padrão
        self.equipment = enemy_data.get('equipment', {'weapon': [], 'armor' : [], 'accessory': []})
        
        #endregion
    #region Equipment Attribute

    def _get_total_attribute(self, attribute_name: str, base_value: int, all_items_data: dict): # Calcula o valor total de um atributo considerando os bônus dos equipamentos
        total_bonus = 0
        for equipment in self.equipment.values(): # Para cada tipo de equipamento
            for item in equipment: # Para cada item equipado
                item_info = all_items_data.get(item,{}) # Obtém os dados do item a partir do dicionário de todos os itens
                if item_info and "bonus" in item_info: # Se o item existe e tem bônus
                    total_bonus += item_info["bonus"].get(attribute_name,0) # Adiciona o bônus do atributo ao total
        return base_value + total_bonus # Retorna o valor base mais o total de bônus dos equipamentos
    
        total_bonus = 0
        for equipment in self.equipment.values():
            for item in equipment:
                item_info = all_items_data.get(item,{})
                if item_info and "bonus" in item_info:
                    total_bonus += item_info["bonus"].get(attribute_name,0)
        return base_value + total_bonus
    
    def total_defense(self, all_items_data:dict): # Calcula a defesa total do Inimigo considerando os equipamentos
        return self._get_total_attribute("defense", self.defense, all_items_data)
    
    def total_strength(self, all_items_data:dict): # Calcula a força total do Inimigo considerando os equipamentos
        return self._get_total_attribute("strength", self.strength, all_items_data)
    
    def total_speed(self, all_items_data:dict): # Calcula a velocidade total do Inimigo considerando os equipamentos
        return self._get_total_attribute("speed", self.speed, all_items_data)
    
    #endregion
    
    def _get_one_item_loot(self, items_data): # Retorna um item de loot baseado na raridade dos itens
        
        # Mapeamento de raridade para peso
        rarity_map = {
            "Comum" : 60,
            "Rare" : 30,
            "Epic" : 10,
            "Legendary" : 5
        }
        
        items = []  # Lista de itens possíveis
        weights = [] # Lista de pesos correspondentes

        for loot_id in self.loot: # Para cada item na lista de loot do inimigo
            item = items_data.get(loot_id)
            
            if not item: # Se o item não existir,
                continue
            
            rarity = item.get('rarity', 'Comum') # Obtém a raridade do item, padrão é 'Comum'
            weight = rarity_map.get(rarity, 0) # Obtém o peso baseado na raridade

            if weight > 0:
                items.append(loot_id)
                weights.append(weight)
        
        if not items:
            return None
        
        result = choices(items, weights=weights, k=1) # Escolhe um item baseado nos pesos

        return result[0]

        
            

        

           
