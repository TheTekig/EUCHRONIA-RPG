#region IMPORTS

import json
import logging # Logging
import os
from pathlib import Path # Manipulação de caminhos de arquivos
from typing import Dict, List, Optional, Tuple, Any # Tipagem estática
from dataclasses import dataclass # Criação de classes de dados
from openai import OpenAI # Cliente OpenAI
from dotenv import load_dotenv # Carrega variáveis de ambiente
from termcolor import colored # Cores no terminal
from time import sleep # Delay de execução
from string import Template

#Importação do Projeto
from euchronia import general_logic as gl # Importa a lógica geral do jogo
from euchronia import combat_logic as cl # Importa a lógica de combate do jogo
from euchronia import models # Importa os modelos de dados do jogo

#endregion

logging.basicConfig( 
    level = logging.INFO,
    format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
) # Configuração básica do logging4
logger = logging.getLogger(__name__)


@dataclass # Define uma classe de configuração do jogo
class GameConfig: # Configurações do jogo | constantes

    LORE_MAX_LENGTH : int = 5000 # Tamanho máximo da lore antes de resumir
    LORE_RESUME_TOKENS : int = 2000 # Tokens máximos para resumo da lore
    DEFAULT_MAX_TOKENS : int = 1000 # Tokens máximos padrão para respostas da IA
    SAVE_SLOT : str = f"saves/slot_1" # Slot de salvamento padrão
    AI_MODEL : str = "gpt-4o-mini" # Modelo de IA padrão

class JSONCleaner: # Limpa e parseia respostas JSON da IA
    
    @staticmethod # Método estático
    def clean_and_parse(text: str) -> Optional[Dict]: # Limpa e parseia o texto JSON retornado pela IA
        try:
            cleaned = text.strip() # Remove espaços em branco no início e fim

            #Limpeza do Json
            if cleaned.startswith("```json"): # Remove blocos de código markdown
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

class PromptBuilder: # Constrói prompts para a IA

    def __init__(self): # Inicializa o construtor de prompts
        self.prompts = self._load_prompts() # Carrega os prompts de arquivos JSON

    def _load_prompts(self) -> Dict: # Carrega os prompts de arquivos JSON
        try:
            with open('data/prompts/build_prompts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(colored("Arquivo build_prompts.json não encontrado.", "red"))
            return {}
    
    #region Creation Prompts

    def build_enemy_prompt(self, enemy_examples : Dict, hero : Any, items_data : Dict, skills : Dict, enemy_name : str, enemy_description : str ) -> List[str]: # Constrói o prompt para criação de inimigo

            """ Funcionamento Similar em todos os outros **build** | Mudança somente no arquivo e os dados do data_for_template"""

            prompt_data = self.prompts.get("EnemyPrompt", {}) #Busca o prompt no arquivo build_prompts.json

            #Prompt cru para tratamento | Formato de Lista
            raw_system_prompt_list = prompt_data.get("system_prompt", ["Erro : Prompt de Sistema não encontrado"])
            raw_user_prompt_list = prompt_data.get("user_prompt", ["Erro: Prompt de Usuário não encontrado"])

            #Transformando a Lista(prompt) em string
            raw_system_str = "\n".join(raw_system_prompt_list)
            raw_user_str = "\n".join(raw_user_prompt_list)
            
            #Dataset para substituir mocks para os dados reais
            data_for_template = {
                "prompt_enemy_examples" : json.dumps(enemy_examples, indent=2, ensure_ascii=False),
                "prompt_hero_hp" : str(hero.hp),
                "prompt_hero_strength" : str(hero.strength),
                "prompt_hero_defense" : str(hero.defense),
                "prompt_hero_speed" : str(hero.speed),
                "prompt_skill_d" : json.dumps(skills, indent=4, ensure_ascii=False),
                "prompt_item_d" : json.dumps(items_data, indent=2, ensure_ascii=False),
                "prompt_enemy_name" : enemy_name,
                "prompt_enemy_description" : enemy_description
            }

            #Resultado Final do prompt
            system_prompt = Template(raw_system_str).safe_substitute(data_for_template)    #Template|safe_substitute - Subistitui os mocks pelos dados no data_for_template
            user_prompt = Template(raw_user_str).safe_substitute(data_for_template)
            
            return [system_prompt, user_prompt] #prompt tratados para execução
        
    def build_skill_prompt(self, skill_examples : Dict, skill_name : str, skill_description : str) -> List[str]: # Constrói o prompt para criação de skill

            prompt_data = self.prompts.get("SkillPrompt", {})

            raw_system_prompt_list = prompt_data.get("system_prompt", ["Erro : Prompt de Sistema não encontrado"])
            raw_user_prompt_list = prompt_data.get("user_prompt", ["Erro: Prompt de Usuário não encontrado"])

            raw_system_str = "\n".join(raw_system_prompt_list)
            raw_user_str = "\n".join(raw_user_prompt_list)
            
            data_for_template = {
                "prompt_skill_name" : skill_name,
                "prompt_skill_description" : skill_description,
                "prompt_skill_examples" : json.dumps(skill_examples, indent=2, ensure_ascii=False)

            }

            system_prompt = Template(raw_system_str).safe_substitute(data_for_template)   
            user_prompt = Template(raw_user_str).safe_substitute(data_for_template)
            
            return [system_prompt, user_prompt]

    def build_item_prompt(self, itens_examples : Dict, item_name : str, item_description : str) -> List[str]: # Constrói o prompt para criação de item
        
        prompt_data = self.prompts.get("ItemPrompt", {})

        raw_system_prompt_list = prompt_data.get("system_prompt", ["Erro : Prompt de Sistema não encontrado"])
        raw_user_prompt_list = prompt_data.get("user_prompt", ["Erro: Prompt de Usuário não encontrado"])

        raw_system_str = "\n".join(raw_system_prompt_list)
        raw_user_str = "\n".join(raw_user_prompt_list)
        
        data_for_template = {
            "prompt_itens_examples" : json.dumps(itens_examples, indent=2, ensure_ascii=False),
            "prompt_item_name" : item_name,
            "prompt_item_description" : item_description
        }

        system_prompt = Template(raw_system_str).safe_substitute(data_for_template)   
        user_prompt = Template(raw_user_str).safe_substitute(data_for_template)
        
        return [system_prompt, user_prompt]

    def build_npc_prompt(self, npc_examples : Dict, npc_name : str, npc_description : str, lore_resume: str, location_name: str) -> List[str]: # Constrói o prompt para criação de npc
        
        prompt_data = self.prompts.get("NpcPrompt", {})

        raw_system_prompt_list = prompt_data.get("system_prompt", ["Erro : Prompt de Sistema não encontrado"])
        raw_user_prompt_list = prompt_data.get("user_prompt", ["Erro: Prompt de Usuário não encontrado"])

        raw_system_str = "\n".join(raw_system_prompt_list)
        raw_user_str = "\n".join(raw_user_prompt_list)

        data_mapping = {
            "prompt_location": location_name,
            "prompt_lore_resume": lore_resume,
            "prompt_npc_hint": npc_examples,
            "prompt_nome_npc" : npc_name,
            "prompt_desc_npc" : npc_description
        }

        system_prompt = Template(raw_system_str).safe_substitute(data_mapping)
        user_prompt = Template(raw_user_str).safe_substitute(data_mapping)

        return [system_prompt, user_prompt]

    #endregion

    #region Packdge Actions

    def build_post_combat_prompt(self, winner: str, enemy_name: str, lore_resume: str, hero: Any, location: str) -> List[str]: # Constrói o prompt para pós-combate

        prompt_data = self.prompts.get("PostCombatPrompt", {})

        raw_system_prompt_list = prompt_data.get("system_prompt", ["Erro : Prompt de Sistema não encontrado"])
        raw_user_prompt_list = prompt_data.get("user_prompt", ["Erro: Prompt de Usuário não encontrado"])

        raw_system_str = "\n".join(raw_system_prompt_list)
        raw_user_str = "\n".join(raw_user_prompt_list)
        
        data_for_template = {
            "prompt_hero_name" : str(hero.name),
            "prompt_enemy_name" : enemy_name,
            "prompt_hero_class_name" : str(hero.class_name),
            "prompt_winner" : winner,
            "prompt_hero_hp" : str(hero.hp),
            "prompt_location" : location,
            "prompt_lore_resume" : lore_resume
        }

        system_prompt = Template(raw_system_str).safe_substitute(data_for_template)   
        user_prompt = Template(raw_user_str).safe_substitute(data_for_template)
        
        return [system_prompt, user_prompt]

    def build_game_master_prompt(self, action : str, lore_resume : str, game_map : Dict, gps : Any, hero : Any, past_position : Any, mood: str = 'criativo' ) -> List[str]: # Constrói o prompt para o Mestre de Jogo

            prompt_data = self.prompts.get("GameMasterPrompt", {})

            raw_system_prompt_list = prompt_data.get("system_prompt", ["Erro : Prompt de Sistema não encontrado"])
            raw_user_prompt_list = prompt_data.get("user_prompt", ["Erro: Prompt de Usuário não encontrado"])

            raw_system_str = "\n".join(raw_system_prompt_list)
            raw_user_str = "\n".join(raw_user_prompt_list)
            
            data_for_template = {
                "prompt_mood" : mood,
                "prompt_hero_name" : str(hero.name),
                "prompt_hero_class_name" : str(hero.class_name),
                "prompt_hero_hp" : str(hero.hp),
                "prompt_hero_strength" : str(hero.strength),
                "prompt_hero_defense" : str(hero.defense),
                "prompt_hero_speed" : str(hero.speed),
                "prompt_past_position" : past_position,
                "prompt_hero_position" : str(hero.position),
                "prompt_game_map" : json.dumps(game_map, indent=4, ensure_ascii=False),
                "prompt_gps" : gps,
                "prompt_lore_resume" : lore_resume,
                "prompt_action" : action

            }

            system_prompt = Template(raw_system_str).safe_substitute(data_for_template)   
            user_prompt = Template(raw_user_str).safe_substitute(data_for_template)
            
            return [system_prompt, user_prompt]
    
    #endregion

    def build_npc_response_prompt(self, npc_name: str, npc_data : Dict, player_input: str, lore_resume: str, hero_name: str, location_name: str) -> List[str]:
        # Tenta pegar traços de personalidade, se não tiver, usa padrão
        personality = npc_data.get("personality", "Neutro e observador")
        description = npc_data.get("description", "Um habitante local")
        
        data_mapping = {
            "prompt_npc_name": npc_name,
            "prompt_npc_description": description,
            "prompt_npc_personality": personality,
            "prompt_location_name": location_name,
            "prompt_lore_resume": lore_resume,
            "prompt_hero_name": hero_name,
            "prompt_player_input": player_input
        }

        system = self._get_template("NpcChatPrompt", "system_prompt").safe_substitute(data_mapping)
        user = self._get_template("NpcChatPrompt", "user_prompt").safe_substitute(data_mapping)

        return [system, user]

    def build_resume_prompt(self, lore_text: str, npcs: Dict, quests : Dict ) -> List[str]: # Constrói prompt responsavel por resumir o arquivo lore.txt

            prompt_data = self.prompts.get("ResumePrompt", {})

            raw_system_prompt_list = prompt_data.get("system_prompt", ["Erro : Prompt de Sistema não encontrado"])
            raw_user_prompt_list = prompt_data.get("user_prompt", ["Erro: Prompt de Usuário não encontrado"])

            raw_system_str = "\n".join(raw_system_prompt_list)
            raw_user_str = "\n".join(raw_user_prompt_list)
            
            data_for_template = {
                "prompt_lore_text" : lore_text,
                "prompt_npcs" : json.dumps(npcs, indent=2, ensure_ascii=False),
                "prompt_quests" : json.dumps(quests, indent=2, ensure_ascii=False)
            }

            system_prompt = Template(raw_system_str).safe_substitute(data_for_template)   
            user_prompt = Template(raw_user_str).safe_substitute(data_for_template)
            
            return [system_prompt, user_prompt]

class OpenAIClient: # Cliente para interagir com a API OpenAI

    def __init__(self, config : GameConfig): #Chama as configuraçoes do sistema
        self.config = config
        self.client = self._initialize_client() #Inicializa o cliente OpenAI

    def _initialize_client(self) -> Optional[OpenAI]: # Inicializa o contato com o Servidor da OpenAI
        load_dotenv("venv/.env") #Faz load do arquivo .env
        api_key = os.getenv("OPENAI_API_KEY") #pega o dado armazenado na var "OPENAI_API_KEY"

        if not api_key:
            logger.error("OPENAI_API_KEY não encontrado no arquivo .env")
            return None
        
        try:
            return OpenAI(api_key = api_key) #Passa a chave da API
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente OpenAI: {e}")
            return None

    def execute(self, prompt : List[str], max_tokens: Optional[int] = None ) -> Optional[str]:  # Executa os prompts | Envia o prompt para API

            if not self.client: # Verifica se o cliente foi inicializado/online
                logger.error("Cliente OpenAI não inicializado")
                return None

            if len(prompt) != 2: #Verifica se o prompt contem o System e User
                logger.error("Prompt deve conter exatamente 2 elementos")
                return None
            max_tokens = max_tokens or self.config.DEFAULT_MAX_TOKENS #define uma quantidade maxima de tokens a serem utilizados | pode se passado por max tokens ou no config geral

            try: #Envio do prompt
                response = self.client.chat.completions.create(
                    model=self.config.AI_MODEL,
                    messages=[
                        {"role": "system", "content" : prompt[0]},
                        {"role": "user", "content" : prompt[1]},
                    ],
                    max_tokens = max_tokens) # Resposta da API
                return response.choices[0].message.content # Resposta selecionada (API retorna lista - resposta localizada no inicio [0])
            except Exception as e:
                logger.error(f"Erro ao executar chamada OpenAI: {e}")
                return None

class LoreManager: # Gerencia a lore do jogo

    def __init__(self, config: GameConfig): # Configurações para lore
        self.config = config
        self.lore_path = Path(config.SAVE_SLOT) / "lore.txt" # Caminho da Lore e Slot

    #region Lore Manipulation Functions

    def read(self) -> str: #Realiza a leitura do lore.txt

        try:
            if not self.lore_path.exists():
                logger.warning(f"Arquivo de lore não existe: {self.lore_path}")
                return ""
            
            return self.lore_path.read_text(encoding= 'utf-8')
        except Exception as e:
            logger.error(f"Erro ao ler lore: {e}")
            return ""

    def write(self, content: str) -> bool: #Realiza a escrita da Lore

        try:
            self.lore_path.parent.mkdir(parents=True, exist_ok=True) # Cria uma pasta e arquivo caso não exista 
            self.lore_path.write_text(content, encoding= 'utf-8')
            return True
        except Exception as e:
            logger.error(f"Erro ao escrever lore: {e}")
            return False
    
    def append(self, new_content: str) -> bool: # Realizada a adição da narrativa gerada pela IA

        current = self.read() # Faz a leitura do conteudo atual
        updated = current + "\n" + new_content # Adiciona o conteudo atual com o gerado da IA
        return self.write(updated) # Reescreve o novo conteudo atualizado

    def should_resume(self) -> bool: # Verifica o tamanho do lore.txt (Ajuda na economia de tokens)

        content = self.read()
        return len(content) > self.config.LORE_MAX_LENGTH # Retorna verdadeiro(deve resumir) se o a quantidade de caracteres for maior que o maximo permitido

    #endregion

class GamePackageProcessor: # Processa pacotes de ações do jogo

    def __init__(self, config: GameConfig, openai_client: OpenAIClient, lore_manager: LoreManager): #Inicializa todas as configurações necessarias para processamento dos pacotes e tratamento |HUB GERAL DA IA
        self.config = config
        self.openai_client = openai_client
        self.lore_manager = lore_manager
        self.json_cleaner = JSONCleaner() #Cria um objeto JSONCleaner
        self.prompt_builder = PromptBuilder() #Cria um objeto PromptBuilder

    #region Processamento de Pacotes | Regular/Pós-Combate

    def process_package(self, prompt: List[str], hero: Any, enemy_examples: Dict, items_data: Dict, skills: Dict, npcs_data: Dict) -> List[str]: # Processa pacotes de ações e redireciona para as próximas ações

        raw_response = self.openai_client.execute(prompt) #Resposta Crua da IA
        if not raw_response: 
            logger.error("Falha ao obter resposta da IA")
            return["Erro ao processar ação.", ""]

        package = self.json_cleaner.clean_and_parse(raw_response) #Realiza a limpeza da resposta da IA
        if not package:
            logger.error("Falha ao parsear pacote de ação")
            return ["Erro ao interpretar resposta da IA", ""]
        
        logger.info(colored(f"Pacote recebido: {package}", "green"))

        if package.get('new_enemy', False): #Verifica se um novo inimigo deve ser criado
            narrative = self._process_new_enemy(package, hero, enemy_examples, items_data, skills) #processa um novo inimigo | Retorna a post_combat_narrativa (narrativa após o termino de um combate)
            return[narrative, ""]

        if package.get('newskill', False): #Verifica se uma nova skill deve ser criada
            skill_name = self._process_new_skill(package, skills) #Processa uma nova skill
            hero._learn_skill(skill_name) #Permite que o jogador receba a nova skill criada

        if package.get('newitem', False): #Verifica se um novo item deve ser criado
            self._process_new_item(package, items_data) #Processa o novo item

        if package.get('newnpc', False):
            self._process_new_npc(package, npcs_data)

        self._update_lore(package) #Processa e Atualiza a Lore criada pela IA

        narrative = package.get('narrativa', 'Nada acontece...')
        quest = package.get('quest', '')

        return [narrative, quest] #Devolve a narrativa criada pela IA

    def post_combat_process(self, prompt: List[str], hero: Any, enemy_examples: Dict, items_data: Dict, skills: Dict) -> List[str]: # Processa um mini pacote de ações após o jogador terminar uma batalha

        raw_response = self.openai_client.execute(prompt) #Recebe a reposta crua da IA
        if not raw_response:
            logger.error("Falha ao obter resposta da IA")
            return["Erro ao processar ação.", ""]

        package = self.json_cleaner.clean_and_parse(raw_response) # Faz tratamento/limpeza da Resposta
        if not package:
            logger.error("Falha ao parsear pacote de ação")
            return ["Erro ao interpretar resposta da IA", ""]
        
        logger.info(colored(f"Pacote pós-combate recebido: {package}", "green"))

        if package.get('newskill', False): #Verifica se uma nova skill deve ser criada após finalizar o combate
            skill_name = self._process_new_skill(package, skills) #Faz a criação e processamento da nova skill
            hero._learn_skill(skill_name) #Adiciona a skill as skills do jogador

        self._update_lore(package) #update na Narrativa após o termino do combate (post_combat_narrativa)

        narrative = package.get('narrativa', 'Nada acontece...')
        return [narrative, ""]

    def process_npc_response_package(self):
        pass
    #endregion

    #region Processar Criações da IA | Enemy/Item/Skill/Npc

    def _process_new_enemy(self, package: Dict, hero: Any, enemy_examples: Dict, items_data: Dict, skills: Dict): #Realiza Processamento/Criação de um inimigo e Inicialização do Combate
        # Import tardio para evitar circular import
        from euchronia import combat_logic as cl
        
        narrativa = package.get('narrativa', 'Um inimigo espreita pelas sombras') #pega a Narrativa Inicial do combate

        enemy_name = package.get('new_enemy_name', 'Inimigo Desconhecido') #pega nome do inimigo a ser criado
        enemy_desc = package.get('new_enemy_description', '') #descrição do inimigo a ser criado

        if enemy_name in enemy_examples: # Verifica se o inimigo ja existe no banco de dados pelo nome
            enemy_data = enemy_examples[enemy_name]

            try:
                enemy = models.EnemyModel(enemy_data) #Cria o inimigo com as informações no banco de dados de inimigos

                if package.get('use_enemy_in_combat', False) or package.get('iniciar_combate', False): #verifica se deve iniciar um combate se deve usar o mesmo inimigo no combate

                    print(colored(f"{package.get('narrativa', '...')}", "yellow")) #Narrativa inicial para inicio de combate (aproximação do inimigo ou algo esta errado)
                    
                    input(">>")

                    result = cl.combat_loop(hero, enemy, skills, items_data) # Inicia o loop de combate no combat_logic.py | Retorna o resultado do combate/vencedor do combate
                    prompt = self.prompt_builder.build_post_combat_prompt(result, enemy_name, package.get('narrativa'), hero, hero.position) #Inicializa o prompt de build_post_combat
                    narrativa_combate = self.post_combat_process(prompt, hero, enemy_examples, items_data, skills) #retorna a narrativa do resultado do combate e realiza processamento do prompt
                    narrativa = narrativa_combate[0]

            except Exception as e:
                logger.error(f"Erro ao criar modelo de inimigo: {e}")
            
            return narrativa #retorna a narrativa do post_combat

        logger.info(f"Criando novo inimigo: {enemy_name}")

        enemy_prompt = self.prompt_builder.build_enemy_prompt(
            enemy_examples, hero, items_data, skills, enemy_name, enemy_desc) #Inicializa o prompt de criação de inimigos (cria status de um inimigo com base na descrição e nome)

        raw_enemy = self.openai_client.execute(enemy_prompt) #Obtem o json cru do inimigo
        if not raw_enemy: #verifica se foi retornado o inimigo ou não
            logger.error("Falha ao gerar inimigo")
            return narrativa #retorna narrativa padrão

        enemy_data = self.json_cleaner.clean_and_parse(raw_enemy) #Realiza tratamento e limpeza do json do inimigo
        if not enemy_data:
            logger.error("Falha ao parsear dados do inimigo")
            return narrativa #retorna narrativa padrão

        logger.info(colored(f"Inimigo criado: {enemy_data}", "yellow"))

        try: #Inicializa o Combate com utilizando o inimigo criado pela IA

            enemy = models.EnemyModel(enemy_data) # Cria Inimigo com informações passadas no Json da IA
            self._save_enemy_to_json(enemy_data, enemy_examples) #Salva Inimigo novo gerado no banco de dados
            
            if package.get('use_enemy_in_combat', False) or package.get('iniciar_combate', False): #Verifica se deve iniciar o combate
                print(colored(f"{package.get('narrativa', '...')}", "yellow")) 

                input(">>")

                #Mesmo procedimento que o superior para inicio de combate e resultado
                result = cl.combat_loop(hero, enemy, skills, items_data)
                prompt = self.prompt_builder.build_post_combat_prompt(result, enemy_name, package.get('narrativa'), hero, hero.position)
                narrativa_combate = self.post_combat_process(prompt, hero, enemy_examples, items_data, skills)
                narrativa = narrativa_combate[0] 

        except Exception as e:
            logger.error(f"Erro ao criar modelo de inimigo: {e}")
        
        return narrativa #retorna narrativa do post_combat

    def _process_new_skill(self, package: Dict, skills: Dict): #Realiza o Processamento/Criação da nova skill com base no nome e descrição dada para skill
    
        skill_name = package.get('newskill_name', 'Habilidade Desconhecida')
        skill_desc = package.get('newskill_description', '')
    
        logger.info(f"Criando nova skill: {skill_name}")
    
        skill_prompt = self.prompt_builder.build_skill_prompt(
            skills, skill_name, skill_desc) #prompt de criação de skill
    
        raw_skill = self.openai_client.execute(skill_prompt) #executa o prompt e retorna a skill crua
        if not raw_skill:
            logger.error("Falha ao gerar skill")
            return
    
        skill_data = self.json_cleaner.clean_and_parse(raw_skill) #Realiza a limpeza e tratamento da skill crua
        if skill_data: #Se retornado corretamente
            self._save_skill_to_json(skill_data, skills) #Salva a skill no banco de dados de skills
            logger.info(colored(f"Skill criada: {skill_name}", "cyan"))
            return skill_name #Retorna o nome da skill criada 
    
    def _process_new_item(self, package: Dict, items_data: Dict ): #Realiza o Processamento/Criação do novo Item com base no nome e descrição para item
    
        item_name = package.get('newitem_name', 'Habilidade Desconhecida')
        item_desc = package.get('newitem_description', '')
    
        logger.info(f"Criando novo item: {item_name}")
    
        item_prompt = self.prompt_builder.build_item_prompt(
            items_data, item_name, item_desc) #cria o prompt para o item
    
        raw_item = self.openai_client.execute(item_prompt) #Executa o prompt do item / retorna o json cru do item
        if not raw_item:
            logger.error("Falha ao gerar item")
            return
    
        item_data = self.json_cleaner.clean_and_parse(raw_item) #Trata o json cru e retorna o data do item
        if item_data:
            self._save_item_to_json(item_data, items_data) #Salva Item no banco de dados de itens
            logger.info(colored(f"Item criado: {item_name}", "cyan"))
    
    def _process_new_npc(self, package: Dict, npcs_data: Dict, lore_resume: str , hero: Any ): # Realiza processamento/criação de um novo Npc

        npc_name = package.get('newnpc_name', 'Desconhecido')
        npc_desc = package.get('newnpc_description', '')

        logger.info(f"Criando novo NPC: {npc_name}")

        npc_prompt = self.prompt_builder.build_npc_prompt(npcs_data, npc_name, npc_desc, lore_resume, hero.location)
        
        raw_npc = self.openai_client.execute(npc_prompt)

        if not raw_npc:
            logger.error("Falha ao gerar NPC")
            return
        npc_data = self.json_cleaner.clean_and_parse(raw_npc)

        if npc_data:
            logger.info(colored(f"Npc Criado: {npc_name}", "cyan"))
            return npc_name

    #endregion

    #region IA Lore Functions  | Update/Resume

    def _update_lore(self, package: Dict): #Realiza o update da lore utilizando o Lore_Manager
        narrative = package.get('narrativa', '')
    
        if narrative:
            self.lore_manager.append(narrative) #Adiciona a narrativa ao lore.txt
    
            if self.lore_manager.should_resume():   #Verifica se deve resumir o lore.txt
                self._resume_lore() #realiza o resumo
                
    def _resume_lore(self): #Realiza o Resumo da lore.txt

        logger.info("Lore muito longa, iniciando resumo...")
        current_lore = self.lore_manager.read() #faz a leitura da lore
        resume_prompt = self.prompt_builder.build_resume_prompt(
            current_lore, {}, {}) #cria o prompt para realizar o resumo

        resumed = self.openai_client.execute(
            resume_prompt,
            max_tokens=self.config.LORE_RESUME_TOKENS ) #Executa o resumo e retorna um resumo do lore.txt

        if resumed: #verifica se foi resumido
            print(colored("Lore resumido para manter contexto.", "yellow"))
            sleep(2)
            self.lore_manager.write(resumed) # Escreve a lore resumida no lore.txt
            logger.info("Lore resumido com sucesso")

    #endregion

    #region Save to Json

    def _save_enemy_to_json(self, enemy_data: Dict, enemy_dict: Dict, filepath: str = 'data/enemy.json'): #Salva o Inimigo Criado pela IA no enemy.json 
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
    
    def _save_skill_to_json(self, skill_data: Dict, skill_dict: Dict, filepath: str = 'data/skills.json'): #Salva a Skill criada pela IA no skills.json
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

    def _save_item_to_json(self, Itens_data: Dict, Itens_dict: Dict, filepath: str = 'data/itens.json'): #Salva o Item criado pela IA no itens.json
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

    #endregion
