import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv
from termcolor import colored
from time import sleep

#Importação do Projeto
from euchronia import general_logic as gl
from euchronia import combat_logic as cl
from euchronia import models


logging.basicConfig(
    level = logging.INFO,
    format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class GameConfig:

    LORE_MAX_LENGTH : int = 5000
    LORE_RESUME_TOKENS : int = 2000
    DEFAULT_MAX_TOKENS : int = 1000
    SAVE_SLOT : str = f"saves/slot_1"
    AI_MODEL : str = "gpt-4o-mini"

class JSONCleaner:
    @staticmethod
    def clean_and_parse(text: str) -> Optional[Dict]:
        try:
            cleaned = text.strip()

            #Limpeza do Json
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            logger.error(f"Error ao parsear JSON: {e}")
            logger.debug(f"Texto que causou erro: {text[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao processar JSON: {e}")
            return None

class PromptBuilder:

    @staticmethod
    def build_enemy_prompt(enemy_examples : Dict, hero : Any, items_data : Dict, skills : Dict, enemy_name : str, enemy_description : str ) -> List[str]:
                
            system_prompt = f"""
            Você é um especialista em design de inimigos para RPG. Sua tarefa é criar um inimigo balanceado 
seguindo a estrutura JSON abaixo. RETORNE APENAS UM JSON válido!

### ESTRUTURA DO INIMIGO (JSON) ###

{{
  "name": (string) - Nome do inimigo,
  "type": (string) - Tipo: "humanoide" ou "fera",
  "region": (list) - Lista de strings com locais onde pode ser encontrado,
  "hp": (int) - Vida atual,
  "maxhp": (int) - Vida máxima,
  "strength": (int) - Poder de ataque,
  "defense": (int) - Defesa,
  "speed": (int) - Velocidade,
  "experience": (int) - XP concedido ao ser derrotado,
  "skills": (list) - Lista de nomes de skills (use apenas do skills.json),
  "loot": (dict) - Dicionário com {{item: chance_drop}} (use apenas do items.json)
}}

### DADOS PARA BALANCEAMENTO ###

Exemplos de inimigos: {json.dumps(enemy_examples, indent=2)}

Herói atual:
- HP: {hero.hp}
- Força: {hero.strength}
- Defesa: {hero.defense}
- Velocidade: {hero.speed}

###OBJETIVOS DE BALANCEAMENTO###
1. O inimigo deve ser desafiador, mas derrotável.
2. Use habilidades que complementem suas estatísticas.
3. Itens de loot devem ter chances razoáveis de drop.
4. Considere o nível e habilidades do herói ao definir estatísticas.
5. Inimigos não devem ter mais de 20% de chance de derrotar o herói em um combate direto.
6. Inimigos devem ter statos proximos ao herói, com pequenas variações para cima ou para baixo.

Skills disponíveis: {json.dumps(skills, indent=2)}

Itens disponíveis: {json.dumps(items_data, indent=2)}
"""

            user_prompt = f"""
### CRIAR NOVO INIMIGO ###

Nome: {enemy_name}
Descrição: {enemy_description}

Gere um inimigo balanceado em formato JSON puro (sem markdown).
"""
            return [system_prompt, user_prompt]
        
    @staticmethod
    def build_skill_prompt(skill_examples : Dict, skill_name : str, skill_description : str) -> List[str]:

            system_prompt = f"""
Você é um especialista em design de habilidades para RPG. Crie uma skill seguindo a estrutura JSON.
RETORNE APENAS UM JSON válido!

### EFEITOS POSSÍVEIS ###

Attack Skills:
  - damage_multiplier: (float >= 1.0) - Multiplicador de dano
  - defense_ignore: (float 0.0-1.0) - Ignora % da defesa
  - critical_chance: (float 0.0-1.0) - Chance de crítico

Buff Skills:
  - defense_multiplier: (float >= 1.0) - Aumenta defesa
  - speed_multiplier: (float >= 1.0) - Aumenta velocidade
  - strength_multiplier: (float >= 1.0) - Aumenta força

Debuff Skills:
  - damage_per_round: (int) - Dano por turno
  - burn_chance: (float 0.0-1.0) - Chance de queimadura
  - defense_multiplier: (float <= 1.0) - Reduz defesa

Control Skills:
  - speed_reduce: (float 0.0-1.0) - Reduz velocidade
  - freeze_chance: (float 0.0-1.0) - Chance de congelar

### ESTRUTURA DA SKILL (JSON) ###

{{
  "name": (string) - Nome da skill,
  "description": (string) - Descrição detalhada,
  "type": (string) - "Ataque", "Buff", "Debuff" ou "Controle",
  "maxuses": (int) - Usos máximos antes do reset,
  "uses": (int) - Usos atuais disponíveis,
  "precision": (float 0.0-1.0) - Taxa de acerto,
  "duration": (int) - Duração em turnos,
  "effect": (dict) - Dicionário com os efeitos
}}

Exemplos de skills: {json.dumps(skill_examples, indent=2)}
"""
            user_prompt = f"""
### CRIAR NOVA SKILL ###

Nome: {skill_name}
Descrição: {skill_description}

Gere uma skill balanceada em formato JSON puro (sem markdown).
"""
            return [system_prompt, user_prompt]

    @staticmethod
    def build_item_prompt(itens_examples : Dict, item_name : str, item_description : str) -> List[str]:
        system_prompt = f"""
Você é um especialista em design de itens para RPG. Crie um item seguindo a estrutura JSON.
RETORNE APENAS UM JSON válido!

### REGRAS DE CATEGORIA ###

1. Weapon / Armor / Accessory (Equipamentos):
   - DEVEM ter o campo "bonus".
   - NÃO DEVEM ter o campo "effect".
   - Atributos comuns: strength, defense, speed.

2. Potion / Consumable:
   - DEVEM ter o campo "effect".
   - NÃO DEVEM ter o campo "bonus".
   - Efeitos comuns: heal (cura HP).

3. Material:
   - NÃO possui "bonus" nem "effect".
   - Serve apenas para venda ou crafting.

### LIMITES DE BALANCEAMENTO POR RARIDADE ###
Use estes valores como base para os atributos (bonus/effect):
 - Comum: 1 a 5
 - Raro: 6 a 15
 - Épico: 16 a 30
 - Lendário: 31+

### ESTRUTURA DO ITEM (JSON) ###

 {{
  "Nome do Item": {{
    "type": (string) - "Weapon", "Armor", "Accessory", "Potion" ou "Material",
    "gold": (int) - Valor de venda,
    "rarity": (string) - "A Raridade segundo o Balancemaneto",
    "description": (string) - Lore curta e envolvente,
    "bonus": (Dict) - (Opcional: Apenas para equipamentos),
    "effect": (Dict) - (Opcional: Apenas para poções)
  }}

Exemplos de skills: {json.dumps(itens_examples, indent=2)}
"""
        user_prompt = f"""
### CRIAR NOVO ITEM ###

Nome: {item_name}
Descrição: {item_description}

Gere um item balanceada em formato JSON puro (sem markdown).
"""
        return [system_prompt, user_prompt]

    @staticmethod
    def build_post_combat_prompt(winner: str, enemy_name: str, lore_resume: str, hero: Any, location: str) -> List[str]:

        system_prompt = f"""
Você é o Mestre de Jogo narrando o FIM de um combate. 
Seu objetivo é descrever o desfecho e determinar recompensas especiais (Epifania de Batalha).

RETORNE APENAS UM JSON válido seguindo a estrutura abaixo.

### REGRAS DE GERAÇÃO ###

1. NARRATIVA:
   - Se Vencedor = "{hero.name}": Descreva o golpe final ou a queda do inimigo (max 40 palavras).
   - Se Vencedor = "{enemy_name}": Descreva o herói caindo derrotado ou fugindo (sem morte permanente).

2. SAQUE (LOOT):
   - 'loot_found': true se o inimigo deixou cair algo (se o herói venceu).

3. NOVA SKILL (EPIFANIA DE BATALHA):
   - O Herói tem uma CHANCE BAIXA (aprox. 5% a 10%) de aprender uma skill nova após vencer.
   - CRITÉRIO: Só gere 'newskill': true se o combate foi difícil ou se a IA "rolar" essa chance baixa.
   - A skill deve ser temática com a Classe do Herói ({hero.class_name}) ou copiar um traço do Inimigo.

### ESTRUTURA DO JSON ###

{{
  "narrativa": (string) - O desfecho da luta,
  "loot_found": (boolean) - Se encontrou itens,
  "xp_gained": (int) - Sugestão de XP baseada no inimigo,
  
  // Geração de Skill (Sistema de Epifania)
  "newskill": (boolean) - true APENAS se ocorrer a chance baixa (5-10%),
  "newskill_name": (string) - Nome criativo da nova skill,
  "newskill_description": (string) - Descrição do que a skill faz
}}
"""
        user_prompt = f"""
### RELATÓRIO DE COMBATE ###

Vencedor: {winner}
Inimigo Enfrentado: {enemy_name}

CONTEXTO DO HERÓI:
Nome: {hero.name} | Classe: {hero.class_name} | HP Restante: {hero.hp}
Local Atual: {location}

CONTEXTO DA HISTÓRIA ANTERIOR:
{lore_resume}

Gere o JSON de pós-combate. Lembre-se: a chance de nova skill é BAIXA.
"""
        return [system_prompt, user_prompt]

    @staticmethod
    def build_game_master_prompt(action : str, lore_resume : str, game_map : Dict, gps : Any, hero : Any, past_position : Any, mood: str = 'criativo' ) -> List[str]:

            system_prompt = f"""
Você é o Mestre de Jogo para um RPG de terminal. Seu estilo é {mood}, descritivo e atmosférico.

Interprete a ação do jogador e retorne um "Pacote de Ações" em JSON. Seja criativo, adapte 
eventos à história e localização. Se o jogador mudar de local, descreva a transição de cenário.

IMPORTANTE: Evite criar muitos NPCs. Prefira criar inimigos e desafios!

### ESTRUTURA DO PACOTE DE AÇÕES (JSON) ###

{{
  "narrativa": (string) - Descrição imersiva da cena (máximo 50 palavras),
  "quest": (string ou null) - Nova quest (ou null se não houver),
  "iniciar_combate": (boolean) - true para iniciar combate,
  "encontrar_npc": (boolean) - true se encontrar NPC,
  "encontrar_item": (boolean) - true se encontrar item,
  
  // Criação de novo inimigo
  "new_enemy": (boolean) - true para criar novo inimigo,
  "new_enemy_name": (string) - Nome do inimigo,
  "new_enemy_description": (string) - Descrição do inimigo,
  "use_enemy_in_combat": (boolean) - true para usar no combate imediato,
  
  // Criação de nova skill
  "newskill": (boolean) - true para criar nova skill,
  "newskill_name": (string) - Nome da skill,
  "newskill_description": (string) - Descrição da skill,
  
  // Criação de novo item
  "newitem": (boolean) - true para criar novo item,
  "newitem_name": (string) - Nome do item,
  "newitem_description": (string) - Descrição do item,
  
  // Criação de novo NPC
  "newnpc": (boolean) - true para criar novo NPC,
  "newnpc_name": (string) - Nome do NPC,
  "newnpc_description": (string) - Descrição do NPC
}}
"""
            user_prompt = f"""
### CONTEXTO ATUAL ###

Herói: {hero.name}
Classe: {hero.class_name}
Nível: {hero.level}
Status: HP {hero.hp} | Força {hero.strength} | Defesa {hero.defense} | Velocidade {hero.speed}

### LOCALIZAÇÃO ###
Posição anterior: {past_position}
Posição atual: {hero.position}
Mapa: {json.dumps(game_map, indent=2)}
GPS: {gps}

### HISTÓRIA ###
{lore_resume}

### AÇÃO DO JOGADOR ###
{action}

Gere o Pacote de Ações em JSON puro (sem markdown).
"""
            return [system_prompt, user_prompt]

    @staticmethod
    def build_resume_prompt(lore_text: str, npcs: Dict, quests : Dict ) -> List[str]:

            system_prompt = """
Você é um especialista em resumos e contextualização. Resuma o arquivo de lore de um RPG
de forma que sirva como contexto e memória para uma IA.

Use NPCs e quests fornecidos para manter foco nos objetivos e personagens importantes.
Mantenha eventos-chave, decisões importantes e progressão da história.
"""
            user_prompt = f"""
### RESUMIR HISTÓRIA ###

História completa:
{lore_text}

NPCs importantes:
{json.dumps(npcs, indent=2)}

Quest atual:
{json.dumps(quests, indent=2)}

Crie um resumo conciso mantendo informações essenciais.
"""
            return [system_prompt, user_prompt]

class OpenAIClient:

    def __init__(self, config : GameConfig):
        self.config = config
        self.client = self._initialize_client()

    def _initialize_client(self) -> Optional[OpenAI]:
        load_dotenv("venv/.env")
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.error("OPENAI_API_KEY não encontrado no arquivo .env")
            return None
        
        try:
            return OpenAI(api_key = api_key)
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente OpenAI: {e}")
            return None

    def execute(self, prompt : List[str], max_tokens: Optional[int] = None ) -> Optional[str]:

            if not self.client:
                logger.error("Cliente OpenAI não inicializado")
                return None

            if len(prompt) != 2:
                logger.error("Prompt deve conter exatamente 2 elementos")
                return None
            max_tokens = max_tokens or self.config.DEFAULT_MAX_TOKENS

            try:
                response = self.client.chat.completions.create(
                    model=self.config.AI_MODEL,
                    messages=[
                        {"role": "system", "content" : prompt[0]},
                        {"role": "user", "content" : prompt[1]},
                    ],
                    max_tokens = max_tokens)
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Erro ao executar chamada OpenAI: {e}")
                return None

class LoreManager:

    def __init__(self, config: GameConfig):
        self.config = config
        self.lore_path = Path(config.SAVE_SLOT) / "lore.txt"

    def read(self) -> str:

        try:
            if not self.lore_path.exists():
                logger.warning(f"Arquivo de lore não existe: {self.lore_path}")
                return ""
            
            return self.lore_path.read_text(encoding= 'utf-8')
        except Exception as e:
            logger.error(f"Erro ao ler lore: {e}")
            return ""

    def write(self, content: str) -> bool:

        try:
            self.lore_path.parent.mkdir(parents=True, exist_ok=True)
            self.lore_path.write_text(content, encoding= 'utf-8')
            return True
        except Exception as e:
            logger.error(f"Erro ao escrever lore: {e}")
            return False
    
    def append(self, new_content: str) -> bool:

        current = self.read()
        updated = current + "\n" + new_content
        return self.write(updated)

    def should_resume(self) -> bool:

        content = self.read()
        return len(content) > self.config.LORE_MAX_LENGTH

class GamePackageProcessor:

    def __init__(self, config: GameConfig, openai_client: OpenAIClient, lore_manager: LoreManager):
        self.config = config
        self.openai_client = openai_client
        self.lore_manager = lore_manager
        self.json_cleaner = JSONCleaner()
        self.prompt_builder = PromptBuilder()

    def process_package(self, prompt: List[str], hero: Any, enemy_examples: Dict, items_data: Dict, skills: Dict) -> List[str]:

        raw_response = self.openai_client.execute(prompt)
        if not raw_response:
            logger.error("Falha ao obter resposta da IA")
            return["Erro ao processar ação.", ""]

        package = self.json_cleaner.clean_and_parse(raw_response)
        if not package:
            logger.error("Falha ao parsear pacote de ação")
            return ["Erro ao interpretar resposta da IA", ""]
        
        logger.info(colored(f"Pacote recebido: {package}", "green"))

        if package.get('new_enemy', False):
            narrative = self._process_new_enemy(package, hero, enemy_examples, items_data, skills)
            return[narrative, ""]

        if package.get('newskill', False):
            self._process_new_skill(package, skills)

        if package.get('newitem', False):
            self._process_new_item(package, items_data)

        self._update_lore(package)

        narrative = package.get('narrativa', 'Nada acontece...')
        quest = package.get('quest', '')

        return [narrative, quest]

    def _process_new_enemy(self, package: Dict, hero: Any, enemy_examples: Dict, items_data: Dict, skills: Dict):
        # Import tardio para evitar circular import
        from euchronia import combat_logic as cl
        
        enemy_name = package.get('new_enemy_name', 'Inimigo Desconhecido')
        enemy_desc = package.get('new_enemy_description', '')

        if enemy_name in enemy_examples:
            enemy_data = enemy_examples[enemy_name]
            try:
                enemy = models.EnemyModel(enemy_data)

                if package.get('use_enemy_in_combat', False) or package.get('iniciar_combate', False):
                    print(colored(f"{package.get('narrativa', '...')}", "yellow"))
                    input(">>")
                    result = cl.combat_loop(hero, enemy, skills, items_data)
                    prompt = PromptBuilder.build_post_combat_prompt(result, enemy_name, package.get('narrativa'), hero, hero.position)
                    narrativa = self.process_package(prompt[0], hero, enemy_examples, items_data, skills)
            except Exception as e:
                logger.error(f"Erro ao criar modelo de inimigo: {e}")
            
            return [narrativa, ""]

        logger.info(f"Criando novo inimigo: {enemy_name}")

        enemy_prompt = self.prompt_builder.build_enemy_prompt(
            enemy_examples, hero, items_data, skills, enemy_name, enemy_desc)

        raw_enemy = self.openai_client.execute(enemy_prompt)
        if not raw_enemy:
            logger.error("Falha ao gerar inimigo")
            return

        enemy_data = self.json_cleaner.clean_and_parse(raw_enemy)
        if not enemy_data:
            logger.error("Falha ao parsear dados do inimigo")
            return

        logger.info(colored(f"Inimigo criado: {enemy_data}", "yellow"))

        try:
            enemy = models.EnemyModel(enemy_data)
            self._save_enemy_to_json(enemy_data, enemy_examples)
            
            if package.get('use_enemy_in_combat', False) or package.get('iniciar_combate', False):
                print(colored(f"{package.get('narrativa', '...')}", "yellow"))
                input(">>")
                result = cl.combat_loop(hero, enemy, skills, items_data)
                prompt = PromptBuilder.build_post_combat_prompt(result, enemy_name, package.get('narrativa'), hero, hero.position)
                narrativa = self.process_package(prompt[0], hero, enemy_examples, items_data, skills)

        except Exception as e:
            logger.error(f"Erro ao criar modelo de inimigo: {e}")
        
        return [narrativa, ""]

    def _process_new_skill(self, package: Dict, skills: Dict):
    
        skill_name = package.get('newskill_name', 'Habilidade Desconhecida')
        skill_desc = package.get('newskill_description', '')
    
        logger.info(f"Criando nova skill: {skill_name}")
    
        skill_prompt = self.prompt_builder.build_skill_prompt(
            skills, skill_name, skill_desc)
    
        raw_skill = self.openai_client.execute(skill_prompt)
        if not raw_skill:
            logger.error("Falha ao gerar skill")
            return
    
        skill_data = self.json_cleaner.clean_and_parse(raw_skill)
        if skill_data:
            self._save_skill_to_json(skill_data, skills)
            logger.info(colored(f"Skill criada: {skill_name}", "cyan"))
    
    def _process_new_item(self, package: Dict, items_data: Dict ):
    
        item_name = package.get('newskill_name', 'Habilidade Desconhecida')
        item_desc = package.get('newskill_description', '')
    
        logger.info(f"Criando nova skill: {item_name}")
    
        item_prompt = self.prompt_builder.build_item_prompt(
            items_data, item_name, item_desc)
    
        raw_item = self.openai_client.execute(item_prompt)
        if not raw_item:
            logger.error("Falha ao gerar skill")
            return
    
        item_data = self.json_cleaner.clean_and_parse(raw_item)
        if item_data:
            self._save_item_to_json(item_data, items_data)
            logger.info(colored(f"Item criado: {item_name}", "cyan"))
    
    def _update_lore(self, package: Dict):
        narrative = package.get('narrativa', '')
    
        if narrative:
            self.lore_manager.append(narrative)
    
            if self.lore_manager.should_resume():
                self._resume_lore()
                
    def _resume_lore(self):

        logger.info("Lore muito longa, iniciando resumo...")
        current_lore = self.lore_manager.read()
        resume_prompt = self.prompt_builder.build_resume_prompt(
            current_lore, {}, {})

        resumed = self.openai_client.execute(
            resume_prompt,
            max_tokens=self.config.LORE_RESUME_TOKENS )

        if resumed:
            self.lore_manager.write(resumed)
            logger.info("Lore resumido com sucesso")
                
    def _save_enemy_to_json(self, enemy_data: Dict, enemy_dict: Dict, filepath: str = 'data/enemy.json'):
        try:
            enemy_name = enemy_data.get('name', 'Inimigo Desconhecido')

            if enemy_name in enemy_dict:
                logger.warning(f"Inimigo {enemy_name} já existe no banco de dados.")
            
            enemy_dict[enemy_name] = enemy_data

            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    all_enemies = json.load(file)
            except FileNotFoundError:
                all_enemies = {}
            
            all_enemies[enemy_name] = enemy_data

            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(all_enemies, file, indent=4, ensure_ascii=False)
            
            logger.info(colored(f"Inimigo {enemy_name} salvo no banco de dados.", "green"))
            print(colored(f"Inimigo salvo: {enemy_name}", "green"))

        except Exception as e:
            logger.error(f"Erro ao salvar inimigo no banco de dados: {e}")
    
    def _save_skill_to_json(self, skill_data: Dict, skill_dict: Dict, filepath: str = 'data/skills.json'):
        try:
            skill_name = skill_data.get('name', 'Inimigo Desconhecido')

            if skill_name in skill_dict:
                logger.warning(f"Skill {skill_name} já existe no banco de dados.")
            
            skill_dict[skill_name] = skill_data

            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    all_skills = json.load(file)
            except FileNotFoundError:
                all_skills = {}
            
            all_skills[skill_name] = skill_data

            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(all_skills, file, indent=4, ensure_ascii=False)
            
            logger.info(colored(f"Skill {skill_name} salvo no banco de dados.", "green"))
            print(colored(f"Skill salvo: {skill_name}", "green"))

        except Exception as e:
            logger.error(f"Erro ao salvar Skill no banco de dados: {e}")

    def _save_item_to_json(self, Itens_data: Dict, Itens_dict: Dict, filepath: str = 'data/itens.json'):
        try:
            Itens_name = Itens_data.get('name', 'Item Desconhecido')

            if Itens_name in Itens_dict:
                logger.warning(f"Skill {Itens_name} já existe no banco de dados.")
            
            Itens_dict[Itens_name] = Itens_data

            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    all_itens = json.load(file)
            except FileNotFoundError:
                all_itens = {}
            
            all_itens[Itens_name] = Itens_data

            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(all_itens, file, indent=4, ensure_ascii=False)
            
            logger.info(colored(f"Skill {Itens_name} salvo no banco de dados.", "green"))
            print(colored(f"Skill salvo: {Itens_name}", "green"))

        except Exception as e:
            logger.error(f"Erro ao salvar Skill no banco de dados: {e}")
