import os
from termcolor import colored
from euchronia import models, general_logic

# REMOVA este import do topo:
# from euchronia.ai_services import GameConfig, OpenAIClient, LoreManager, GamePackageProcessor

#region SAVE/LOAD

def save_game(hero, lore_resume, slot="slot_1"):
    """Salva o progresso do jogo"""
    import json
    from pathlib import Path
    
    save_dir = Path(f"saves/{slot}")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Salva dados do herói
    hero_data = hero._to_dict()
    with open(save_dir / "hero.json", 'w', encoding='utf-8') as f:
        json.dump(hero_data, f, indent=4, ensure_ascii=False)
    
    # Salva lore
    lore_path = save_dir / "lore.txt"
    current_lore = ""
    if lore_path.exists():
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

def load_game(slot="slot_1"):
    """Carrega um save"""
    import json
    from pathlib import Path
    from euchronia import models
    
    save_dir = Path(f"saves/{slot}")
    
    if not save_dir.exists():
        print(colored(f"Save não encontrado: {slot}", "red"))
        return None, None
    
    # Carrega herói
    with open(save_dir / "hero.json", 'r', encoding='utf-8') as f:
        hero_data = json.load(f)
    hero = models.PlayerModel._from_dict(hero_data)
    
    # Carrega lore
    with open(save_dir / "lore.txt", 'r', encoding='utf-8') as f:
        lore_resume = f.read()
    
    print(colored(f"Save {slot} carregado!", "green"))
    return hero, lore_resume

def choose_save_slot():
    """Permite ao jogador escolher um slot de save"""
    print(colored("Escolha um slot de save:", 'cyan'))
    
    for slot in range(1, 4):
        print(colored(f"{slot} - slot_{slot}", 'yellow'))
    
    slot_choice = input(">> ")
    while slot_choice not in ['1', '2', '3', '4']:
        print("Invalid option. Please try again.")
        slot_choice = input(">>")
    
    return f"slot_{slot_choice}"
#endregion

# NOVA FUNÇÃO: Inicializa serviços de IA
def initialize_game_services(slot="slot_1"):
    """Inicializa os serviços de IA do jogo (import tardio)"""
    # Import aqui dentro para evitar circular import
    from euchronia.ai_services import GameConfig, OpenAIClient, LoreManager, GamePackageProcessor
    
    config = GameConfig()
    config.SAVE_SLOT = f"saves/{slot}"
    
    openai_client = OpenAIClient(config)
    lore_manager = LoreManager(config)
    game_processor = GamePackageProcessor(config, openai_client, lore_manager)
    
    return game_processor

def create_hero(classes):
    os.system("cls")
    
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

    os.system("cls")
    print(colored("Com Qual Classe Você se Identifica?", "magenta", attrs=['bold']).center(90))
    for i, e in enumerate(classes.values()):
        print(f"{i+1} - {e.get('name')} - {e.get('description')}")
        
    
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

        chosen_class = list(classes.values())[choice]
        print(colored(f"Então você é um {chosen_class['name']}?", "magenta").center(90))

        confirm = input("[S/N]>> ")
        while confirm.upper() not in ["S","N"]:
            confirm = input("[S/N]>> ")
        
        if confirm.upper() ==  "S":
            break
        else:
            continue
    try:
        hero = models.PlayerModel(name, chosen_class)
        print(colored(f"Herói {hero.name} da classe {hero.class_name} criado com sucesso!", "green"))
        for skill in chosen_class['initial_Skills']:
            hero.skills.append(skill)
        return hero

    except Exception as e:
        print(colored(f"Erro ao criar herói: {e}", "red"))
        return None

    input(colored("Pressione Enter para continuar...", "green"))
            
#region Explore Logic
def initial_hud_menu(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, game_processor):
    """Menu principal do jogo durante a exploração"""
    
    while True:
        os.system('cls')
        current_location_info = atlas.get(hero.position, {"nome": "Lugar Desconhecido"})
        location_name = current_location_info['nome']
        
        print(f"\n============== VOCÊ ESTÁ EM: {location_name.upper()} ==============")
        print("[A]ctions / [I]nventário / [S]tatus / [M]apa / [R]est / [Q]uit")
        
        choice = input(">> ").upper()
        
        if choice == "A":
            action_submenu(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, game_processor)
        
        elif choice == "I":
            manage_inventory(hero, all_items_data)
        
        elif choice == "S":
            hero._status(all_items_data)
        
        elif choice == "M":
            show_map_from_file()
        
        elif choice == "R":
            hero.heal(10)
            print(colored("Você descansa e recupera 10 HP.", "green"))
            input("Pressione Enter para continuar...")
        
        elif choice == "Q":
            print("Obrigado por jogar EUCHRONIA!")
            try:
                updated_lore = game_processor.lore_manager.read()
                save_game(hero, updated_lore)
            except Exception as e:
                print(colored(f"Erro ao ler lore atualizado: {e}", "red"))
                print(colored("Salvando com lore anterior...", "yellow"))
                save_game(hero, lore_resume)
                
            return "QUIT"

def action_submenu(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, game_processor):
    """Submenu de ações"""
    
    past_hero_position = hero.position
    print("\n[E]xplore / [F]ight / [O]bserve / [R]eturn")
    choice = input(">> ").upper()
    
    if choice == "E":
        explore_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor)
    
    elif choice == "F":
        fight_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor)
    
    elif choice == "O":
        observe_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor)
    
    elif choice == "R":
        return

def explore_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor):
    # Import tardio do PromptBuilder
    from euchronia.ai_services import PromptBuilder
    
    print("\nPara onde você quer ir?")
    possible_destinations = gps.get(hero.position, [])

    destination_map = {}
    for i, place_id in enumerate(possible_destinations):
        place_name = atlas[place_id]['nome']
        destination_map[str(i + 1)] = place_id
        print(f"  [{i + 1}] {place_name}")

    if not destination_map:
        print("Não há para onde ir a partir daqui.")
        input("Pressione Enter para continuar...")
        return

    travel_choice = input(">> ")

    while travel_choice not in destination_map:
        print("Opção inválida.")
        travel_choice = input(">> ")

    chosen_id = destination_map[travel_choice]
    hero.position = chosen_id
    new_location_name = atlas[chosen_id]['nome']

    action = f"Travelling from {past_hero_position} to {new_location_name}"
    
    prompt = PromptBuilder.build_game_master_prompt(action, lore_resume, atlas, gps, hero, past_hero_position)
    narrativa, quest = game_processor.process_package(prompt, hero, enemy, all_items_data, skills)

    print(colored(narrativa, "cyan"))
    print(f"\nVocê viaja para {new_location_name}...")
    input(colored("Pressione Enter para continuar...", "green"))

def fight_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor):
    from euchronia.ai_services import PromptBuilder
    
    action = "Start Fight"
    prompt = PromptBuilder.build_game_master_prompt(action, lore_resume, atlas, gps, hero, past_hero_position)
    narrativa, quest = game_processor.process_package(prompt, hero, enemy, all_items_data, skills)

    print(colored(narrativa, "cyan"))
    input(colored("Pressione Enter para continuar...", "green"))

def observe_action(hero, atlas, gps, all_items_data, enemy, skills, lore_resume, past_hero_position, game_processor):
    from euchronia.ai_services import PromptBuilder
    
    action = input("Your Action >> ")
    prompt = PromptBuilder.build_game_master_prompt(action, lore_resume, atlas, gps, hero, past_hero_position)
    narrativa, quest = game_processor.process_package(prompt, hero, enemy, all_items_data, skills)
    print(colored(narrativa, "cyan"))
    input(colored("Pressione Enter para continuar...", "green"))

def show_map_from_file(filepath="map.txt"):
    """
    Abre e exibe um mapa a partir de um ficheiro de texto (ASCII art).
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            map_content = f.read()
            print("\n" + "="*20 + " MAPA DO MUNDO " + "="*20)
            print(map_content)
            print("="*56)
            input("Pressione Enter para fechar o mapa...")
    except FileNotFoundError:
        print(f"\nErro: O ficheiro do mapa '{filepath}' não foi encontrado.")
        input("Pressione Enter para continuar...")

#endregion

#region Inventary Logic

def list_player_inventory(hero):
    """
    Lista os itens no inventário do jogador de forma clara e numerada.
    """
    print("\n--- Inventário ---")
    if not hero.inventory:
        print("Vazio.")
        return

    for i, item_name in enumerate(hero.inventory):
        print(f"[{i + 1}] {item_name}")
    print("------------------")

def manage_inventory(hero, all_items_data):
    """
    Permite ao jogador escolher um item do inventário e decidir o que fazer com ele.
    """
    list_player_inventory(hero)
    
    if not hero.inventory:
        return 

    try:
        choice_input = input("Escolha um item pelo número (ou 's' para sair): ")
        if choice_input.lower() == 's':
            return

        item_index = int(choice_input) - 1

        if not 0 <= item_index < len(hero.inventory):
            print("Número inválido.")
            return

        item_name = hero.inventory[item_index]
        item_data = all_items_data[item_name]

        print(f"\nItem selecionado: {item_name}")
        print(f"Descrição: {item_data.get('description', 'N/A')}")
        
        item_type = item_data.get("type", "Unknown")
        
        if item_type == "Potion":
            action = input("[U]sar item ou [V]oltar? ").upper()
            if action == 'U':
                use_potion(hero, item_name, item_data)
                hero.inventory.pop(item_index)
                print(f"{item_name} foi utilizado.")

        elif item_type in ["Weapon", "Armor", "Accessory"]:
            action = input("[E]quipar item ou [V]oltar? ").upper()
            if action == 'E':
                equip_item(hero, item_name, item_data)

        elif item_type == "Material":
            print("Este é um material de criação e não pode ser usado ou equipado diretamente.")
            input("Pressione Enter para continuar...")

    except (ValueError, IndexError):
        print("Entrada inválida. Por favor, digite um número da lista.")
    except KeyError:
        print(f"Erro: O item '{item_name}' não foi encontrado na base de dados de itens.")

def use_potion(hero, item_name, item_data):
    """
    Aplica o efeito de uma poção no herói.
    """
    effects = item_data.get("effects", {})
    if "heal" in effects:
        heal_amount = effects["heal"]
        hero.heal(heal_amount)
        print(f"Você recuperou {heal_amount} de HP. Vida atual: {hero.hp}/{hero.max_hp}")
    else:
        print("Esta poção não parece ter efeito algum.")

def equip_item(hero, item_name, item_data):
    """
    Equipa uma arma, armadura ou acessório, respeitando os limites de slots.
    """
    item_type = item_data.get("type").lower()

    if len(hero.equipment[item_type]) >= hero.max_equipment[item_type]:
        equipped_item_name = hero.equipment[item_type][0]
        print(f"O slot de '{item_type}' já está ocupado por: {equipped_item_name}.")
        
        choice = input(f"Deseja substituir {equipped_item_name} por {item_name}? [S/N]: ").upper()
        
        if choice == 'S':
            hero.inventory.append(equipped_item_name)
            hero.equipment[item_type].remove(equipped_item_name)
            print(f"{equipped_item_name} foi movido para o inventário.")
        else:
            print("Operação cancelada.")
            return

    hero.inventory.remove(item_name)
    hero.equipment[item_type].append(item_name)
    
    print(f"{item_name} foi equipado.")
