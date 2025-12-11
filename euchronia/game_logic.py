#region Imports

import os
from time import sleep
from termcolor import colored
from euchronia import models, general_logic
from UI.ui_menu import _Hud, _sub_Hud

#endregion

#region SAVE/LOAD

def save_game(hero, lore_resume, slot="slot_1"): # Salva o progresso do jogo
    """"""

    # Import tardio para evitar import circular
    import json         
    from pathlib import Path    
    
    save_dir = Path(f"saves/{slot}")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Salva dados do herói
    hero_data = hero._to_dict()
    with open(save_dir / "hero.json", 'w', encoding='utf-8') as f:
        json.dump(hero_data, f, indent=4, ensure_ascii=False) # Formata JSON com indentação e suporta caracteres UTF-8
    
    # Salva lore
    lore_path = save_dir / "lore.txt"
    current_lore = ""
    if lore_path.exists(): # Verifica se o arquivo de lore já existe
        try:
            with open(lore_path, 'r', encoding='utf-8') as f:
                current_lore = f.read()
        except Exception as e:
            print(colored(f"Aviso: Não foi possível ler lore anterior: {e}", "yellow"))
    
    # Se lore_resume estiver vazio ou for None, usa o lore atual do arquivo
    if not lore_resume or lore_resume.strip() == "":
        lore_to_save = current_lore
        print(colored("⚠ Lore vazio detectado, mantendo lore anterior.", "yellow"))
    else:
        lore_to_save = lore_resume
    
    # Salva lore
    with open(lore_path, 'w', encoding='utf-8') as f:
        f.write(lore_to_save)
    
    print(colored(f"✓ Jogo salvo no slot {slot}!", "green"))
    print(colored(f"  - Herói: {hero.name} (Level {hero.level})", "cyan"))
    print(colored(f"  - Lore: {len(lore_to_save)} caracteres salvos", "cyan"))
    sleep(2)

def load_game(slot="slot_1"): #Receber slot como argumento diretamente do Euchronia.py e retorna herói e lore carregados
    """Carrega um save"""
    import json
    from pathlib import Path
    from euchronia import models
    
    save_dir = Path(f"saves/{slot}") # Diretório do save
    
    if not save_dir.exists():
        print(colored(f"Save não encontrado: {slot}", "red"))
        return None, None
    
    # Carrega herói
    with open(save_dir / "hero.json", 'r', encoding='utf-8') as f:
        hero_data = json.load(f)
    hero = models.PlayerModel._from_dict(hero_data) # Reconstrói o objeto PlayerModel a partir do dicionário carregado
    
    # Carrega lore
    with open(save_dir / "lore.txt", 'r', encoding='utf-8') as f:
        lore_resume = f.read() # Lê o conteúdo do arquivo de lore
    
    print(colored(f"Save {slot} carregado!", "green"))
    print(colored(f"  - Herói: {hero.name} (Level {hero.level})", "cyan"))
    sleep(2)
    return hero, lore_resume # Retorna herói e lore carregados (necessarios para o jogo)

def choose_save_slot(): # Permite ao jogador escolher um slot de save
    """
    """
    print(colored("Escolha um slot de save:", 'cyan'))
    
    for slot in range(1, 5):        # 4 slots de save disponíveis
        print(colored(f"{slot} - slot_{slot}", 'yellow'))
    
    slot_choice = input(">> ")
    while slot_choice not in ['1', '2', '3', '4']:
        print("Invalid option. Please try again.")
        slot_choice = input(">>")
    
    return f"slot_{slot_choice}" # Retorna o slot escolhido pelo jogador

#endregion

#region Game Initialization

def initialize_game_services(slot="slot_1"): # Inicializa os serviços de IA do jogo
    """(import tardio)"""
    # Import aqui dentro para evitar circular import
    from euchronia.ai_services import GameConfig, OpenAIClient, LoreManager, GamePackageProcessor
    
    config = GameConfig()
    config.SAVE_SLOT = f"saves/{slot}"
    
    openai_client = OpenAIClient(config)
    lore_manager = LoreManager(config)
    game_processor = GamePackageProcessor(config, openai_client, lore_manager)
    
    return game_processor

def create_hero(classes): # Cria o herói com base na escolha do jogador
    os.system("cls") # Limpa a tela

    # Criação do Herói - Nome
    while True:
        print(colored("Qual seu nome herói?", "magenta", attrs=["bold"]).center(90))
        name = input(">> ")
        print(colored(f"Então seu nome é {name}?", "magenta").center(90))
        confirm = input("[S/N]>> ")
        while confirm.upper() not in ["S","N"]:
            confirm = input("[S/N]>> ")
        
        if confirm.upper() ==  "S":
            break
        else:
            continue

    os.system("cls") # Limpa a tela - Escolha da Classe
    print(colored("Com Qual Classe Você se Identifica?", "magenta", attrs=['bold']).center(90))
    for i, e in enumerate(classes.values()):
        print(f"{i+1} - {e.get('name')} - {e.get('description')}")
        
    # Escolha da Classe
    while True:
        try:
            choice = input(">> ")
            choice = int(choice) - 1
            if choice in range(len(classes)):
                pass
            else:
                print(colored("Escolha inválida. Tente novamente.", "red"))
                continue
        except ValueError:
            print(colored("Escolha inválida. Tente novamente.", "red"))
            continue

        chosen_class = list(classes.values())[choice] # Obtém a classe escolhida
        print(colored(f"Então você é um {chosen_class['name']}?", "magenta").center(90)) # Confirmação da Classe

        confirm = input("[S/N]>> ")
        while confirm.upper() not in ["S","N"]:
            confirm = input("[S/N]>> ")
        
        if confirm.upper() ==  "S":
            break
        else:
            continue
    try:
        hero = models.PlayerModel(name, chosen_class) # Cria o herói com a classe escolhida
        print(colored(f"Herói {hero.name} da classe {hero.class_name} criado com sucesso!", "green"))
        for skill in chosen_class['initial_Skills']: # Para cada skill inicial da classe
            hero.skills.append(skill) # Adiciona skills iniciais ao herói
        return hero

    except Exception as e: # Erro ao criar herói
        print(colored(f"Erro ao criar herói: {e}", "red"))
        return None

    input(colored("Pressione Enter para continuar...", "green"))
            
#endregion

#region Menu Logic

def initial_hud_menu(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, game_processor, slot): # Menu inicial do HUD do jogo | Gera o loop principal do jogo | Responsável por chamar submenus
    """Menu principal do jogo durante a exploração"""
    
    while True:
        os.system('cls') # Limpa a tela
        # Obtém o nome do local atual do herói
        current_location_info = atlas.get(hero.position, {"nome": "Lugar Desconhecido"}) 
        location_name = current_location_info['nome']
        
        _Hud(location_name) # Exibe o HUD principal
        choice = input(">> ").upper()
        
        if choice == "A":
            action_submenu(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, game_processor) # Chama o submenu de ações | Explorar, Lutar, Observar
        
        elif choice == "I":
            manage_inventory(hero, all_items_data) # Chama o gerenciador de inventário | Usar, Equipar, Descartar
        
        elif choice == "S":
            hero._status(all_items_data) # Exibe o status completo do herói
        
        elif choice == "M":
            show_map_from_file() # Exibe o mapa do mundo (ASCII art ou PNG)
        
        elif choice == "R": # Descansar | Recupera HP
            hero.heal(10)
            print(colored("Você descansa e recupera 10 HP.", "green"))
            input("Pressione Enter para continuar...")
        
        elif choice == "Q": # Sair do jogo
            print("Obrigado por jogar EUCHRONIA!")
            try:
                updated_lore = game_processor.lore_manager.read() # Tenta ler o lore atualizado do LoreManager
                save_game(hero, updated_lore, slot) # Salva o jogo com o lore atualizado
            except Exception as e:
                print(colored(f"Erro ao ler lore atualizado: {e}", "red"))
                print(colored("Salvando com lore anterior...", "yellow"))
                save_game(hero, lore_resume, slot) # Salva o jogo com o lore anterior
                
            return "QUIT" # Sai do loop principal do jogo

def action_submenu(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, game_processor): # Submenu de ações | Responsável por chamar funções de explorar, lutar e observar | Chamdas Iniciais Para ações
    """Submenu de ações"""
    os.system("cls")
    past_hero_position = hero.position # Armazena a posição anterior do herói
    _sub_Hud() # Exibe o HUD secundário
    choice = input(">> ").upper()
    
    if choice == "E":
        explore_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor) # Chama a função de explorar
    
    elif choice == "F":
        fight_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor) # Chama a função de lutar
    
    elif choice == "O":
        observe_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor) # Chama a função de observar
    
    elif choice == "R": # Retorna ao menu anterior
        return

def explore_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor): # Ação de explorar | Permite ao jogador escolher um novo local para viajar

    print("\nPara onde você quer ir?")
    possible_destinations = gps.get(hero.position, []) # Obtém destinos possíveis a partir da posição atual do herói

    destination_map = {} # Mapeia opções de entrada para IDs de localizações
    for i, place_id in enumerate(possible_destinations):
        place_name = atlas[place_id]['nome']
        destination_map[str(i + 1)] = place_id
        print(f"  [{i + 1}] {place_name}")

    if not destination_map: # Se não houver destinos disponíveis
        print("Não há para onde ir a partir daqui.")
        input("Pressione Enter para continuar...")
        return

    travel_choice = input(">> ")

    while travel_choice not in destination_map: # Valida a escolha do jogador
        print("Opção inválida.")
        travel_choice = input(">> ")

    chosen_id = destination_map[travel_choice] # Obtém o ID do local escolhido
    hero.position = chosen_id       # Atualiza a posição do herói para o novo local
    new_location_name = atlas[chosen_id]['nome'] # Obtém o nome do novo local

    action = f"Travelling from {past_hero_position} to {new_location_name}" # Descreve a ação de viajar | usada no prompt do Game Master AI
    
    prompt = game_processor.prompt_builder.build_game_master_prompt(action, lore_resume, atlas, gps, hero, past_hero_position) # Constrói o prompt para o Game Master AI
    narrativa, quest = game_processor.process_package(prompt, hero, enemy, all_items_data, skills) # Processa o prompt e obtém a narrativa resultante

    print(colored(narrativa, "cyan"))
    print(f"\nVocê viaja para {new_location_name}...")
    input(colored("Pressione Enter para continuar...", "green"))

def fight_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor): # Ação de lutar | Inicia um combate
    
    action = "Start Fight" # Descreve a ação de iniciar um combate | usada no prompt do Game Master AI
    prompt = game_processor.prompt_builder.build_game_master_prompt(action, lore_resume, atlas, gps, hero, past_hero_position) # Constrói o prompt para o Game Master AI
    narrativa, quest = game_processor.process_package(prompt, hero, enemy, all_items_data, skills) # Processa o prompt e obtém a narrativa resultante

    print(colored(narrativa, "cyan"))
    input(colored("Pressione Enter para continuar...", "green"))

def observe_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor): # Ação de observar | Permite ao jogador observar o ambiente atual e obter informações | Chamadas Iniciais Para ações "livre"
    from euchronia.ai_services import PromptBuilder # Import tardio do PromptBuilder | Responsável por construir prompts para o Game Master AI
    
    action = input("Your Action >> ") # Permite ao jogador descrever o que deseja observar
    prompt = game_processor.prompt_builder.build_game_master_prompt(action, lore_resume, atlas, gps, hero, past_hero_position) # Constrói o prompt para o Game Master AI
    narrativa, quest = game_processor.process_package(prompt, hero, enemy, all_items_data, skills) # Processa o prompt e obtém a narrativa resultante
    print(colored(narrativa, "cyan"))
    input(colored("Pressione Enter para continuar...", "green"))

def open_map_png(filepath="./data/mapconfig/EuchroniaMap.png"): # Abre e exibe um mapa a partir de um ficheiro PNG
    """
    Abre e exibe um mapa a partir de um ficheiro PNG.
    """
    try:
        from PIL import Image # Biblioteca Pillow para manipulação de imagens
        import matplotlib.pyplot as plt # Biblioteca Matplotlib para exibição de imagens

        img = Image.open(filepath) # Abre a imagem do mapa
        plt.imshow(img) # Exibe a imagem usando Matplotlib
        plt.axis('off')  # Oculta os eixos
        plt.show() # Mostra a janela com o mapa
    except ImportError:
        print("\nErro: As bibliotecas necessárias para exibir o mapa PNG não estão instaladas.")
        print("Por favor, instale Pillow e matplotlib para usar esta funcionalidade.")
        input("Pressione Enter para continuar...")
    except FileNotFoundError:
        print(f"\nErro: O ficheiro do mapa '{filepath}' não foi encontrado.")
        input("Pressione Enter para continuar...")

def show_map_from_file(filepath="./data/mapconfig/map.txt"): # Exibe o mapa do mundo a partir de um ficheiro de texto (ASCII art) ou PNG
    """
    Abre e exibe um mapa a partir de um ficheiro de texto (ASCII art).
    """
    print("\nDeseja ver o mapa em PNG ou ASCII art?")
    choice = input("[P]NG / [A]SCI >> ").upper()
    if choice not in ['P', 'A']:
        print("Opção inválida. Retornando ao menu anterior.")
        return
    if choice == 'P':
        open_map_png() # Chama a função para abrir o mapa em PNG
    else:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                map_content = f.read() # Lê o conteúdo do ficheiro de texto | ASCII art
                print("\n" + "\u2500"*20 + colored(" MAPA DO MUNDO ", "magenta") + "\u2500"*20)
                print(map_content)
                print("\u2500"*56)
                input("Pressione Enter para fechar o mapa...")
    
        except FileNotFoundError:
            print(f"\nErro: O ficheiro do mapa '{filepath}' não foi encontrado.")
            input("Pressione Enter para continuar...")

#endregion

#region Inventary Logic

def list_player_inventory(hero): # Lista os itens no inventário do jogador de forma clara e numerada
    """

    """
    print(colored("\n\u2500 Inventário \u2500", "magenta"))
    if not hero.inventory: # Verifica se o inventário está vazio
        print("Vazio.")
        input(">>")
        return

    for i, item_name in enumerate(hero.inventory): # Lista os itens com numeração
        print(f"[{i + 1}] {item_name}")
    print("\u2500" * 20)

def manage_inventory(hero, all_items_data): # Gerencia o inventário do jogador | Permite usar, equipar ou descartar itens
    """
    Permite ao jogador escolher um item do inventário e decidir o que fazer com ele.
    """
    list_player_inventory(hero) # Lista o inventário do jogador
    
    if not hero.inventory: 
        return 

    try:
        choice_input = input("Escolha um item pelo número (ou 's' para sair): ")
        if choice_input.lower() == 's':
            return

        item_index = int(choice_input) - 1

        if not 0 <= item_index < len(hero.inventory): # Valida o índice do item
            print("Número inválido.")
            return

        item_name = hero.inventory[item_index] # Obtém o nome do item escolhido
        item_data = all_items_data[item_name] # Obtém os dados do item a partir da base de dados de itens

        print(f"\nItem selecionado: {item_name}")
        print(f"Descrição: {item_data.get('description', 'N/A')}")
        
        item_type = item_data.get("type", "Unknown") # Obtém o tipo do item
        
        if item_type == "Potion":   # Se for uma poção
            action = input("[U]sar item ou [V]oltar? ").upper()
            if action == 'U':
                use_potion(hero, item_data) # Usa a poção
                hero.inventory.pop(item_index) # Remove a poção do inventário após o uso
                print(f"{item_name} foi utilizado.")

        elif item_type in ["Weapon", "Armor", "Accessory"]: # Se for um equipamento
            action = input("[E]quipar item ou [V]oltar? ").upper()
            if action == 'E':
                equip_item(hero, item_name, item_data) # Equipa o item

        elif item_type == "Material": # Se for um material de crafting encaminha mensagem | não pode ser usado ou equipado
            print("Este é um material de criação e não pode ser usado ou equipado diretamente.")

        input("Pressione Enter para continuar...")

    except (ValueError, IndexError):
        print("Entrada inválida. Por favor, digite um número da lista.")
    except KeyError:
        print(f"Erro: O item '{item_name}' não foi encontrado na base de dados de itens.")

def use_potion(hero, item_data): # Aplica o efeito de uma poção no herói.
    """
    Aplica o efeito de uma poção no herói.
    """
    effects = item_data.get("effect", {}) # Obtém os efeitos da poção
    if "heal" in effects: # Se a poção cura
        heal_amount = effects["heal"] # Quantidade de cura
        hero.heal(heal_amount) # Aplica a cura ao herói
        print(f"Você recuperou {heal_amount} de HP. Vida atual: {hero.hp}/{hero.maxhp}")
    else:
        print("Esta poção não parece ter efeito algum.")
    
def equip_item(hero, item_name, item_data): # Equipa uma arma, armadura ou acessório, respeitando os limites de slots.
    """
    """
    item_type = item_data.get("type").lower() # Obtém o tipo do item em minúsculas (weapon, armor, accessory)

    if len(hero.equipment[item_type]) >= hero.max_equipment[item_type]: # Verifica se o slot já está cheio
        equipped_item_name = hero.equipment[item_type][0]       # Obtém o nome do item equipado no slot
        print(f"O slot de '{item_type}' já está ocupado por: {equipped_item_name}.")
        
        choice = input(f"Deseja substituir {equipped_item_name} por {item_name}? [S/N]: ").upper()
        
        if choice == 'S':
            hero.inventory.append(equipped_item_name) # Move o item equipado de volta para o inventário
            hero.equipment[item_type].remove(equipped_item_name) # Remove o item equipado do slot
            print(f"{equipped_item_name} foi movido para o inventário.")
        else:
            print("Operação cancelada.")
            return

    hero.inventory.remove(item_name) # Remove o item do inventário
    hero.equipment[item_type].append(item_name) # Equipa o novo item no slot
    
    print(f"{item_name} foi equipado.")

#endregion
