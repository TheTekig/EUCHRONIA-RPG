#region IMPORTS

import json # Manipulação de arquivos JSON
from euchronia import ai_services, general_logic, models, combat_logic, game_logic # Lógica do jogo
from UI import ui_menu # Interface do usuário
import os  # Operações do sistema operacional
from termcolor import colored # Cores no terminal

#endregion

#region LOAD DATA

classes = general_logic.load_json('data/classes.json') # Carrega os dados das classes do jogo
enemies = general_logic.load_json('data/enemy.json')    # Carrega os dados dos inimigos do jogo
items = general_logic.load_json('data/itens.json')   # Carrega os dados dos itens do jogo
skills = general_logic.load_json('data/skills.json')   # Carrega os dados das habilidades do jogo
shopkeepers = general_logic.load_json('data/shopkeepers.json') # Carrega os dados dos lojistas do jogo

atlas = general_logic.load_json('data/mapconfig/atlas.json') # Carrega os dados do atlas do mapa
gps = general_logic.load_json('data/mapconfig/gps_map.json') # Carrega os dados do gps do mapa

def load_lore(slot): # Carrega a lore do jogo a partir do arquivo de texto salvo
    with open (f'saves/{slot}/lore.txt', "r") as lore_text:
        lore = lore_text.read() 
        return lore

#endregion

def main(): # Função principal do jogo | ponto de entrada | main loop

    while True:

        os.system('cls' if os.name == 'nt' else 'clear')
        ui_menu._inital_menu() # Exibe o menu inicial

        choice = input(">> ")
        while choice not in ['1', '2', '3', '4']: # Validação da escolha do usuário
            print("Invalid option. Please try again.")
            choice = input(">>")

        match choice:
            case '1': # New Game

                hero = game_logic.create_hero(classes) # Cria o herói do jogador
                slot = game_logic.choose_save_slot() # Escolhe o slot de salvamento

                game_processor = game_logic.initialize_game_services(slot) # Inicializa os serviços do jogo

                lore = load_lore(slot) # Carrega a lore do jogo

                game_logic.save_game(hero, lore, slot) # Salva o jogo inicial
                input(colored("Pressione Enter para continuar...", "green"))
                
                game_logic.initial_hud_menu(hero,atlas,gps,items,enemies,skills,lore, game_processor, slot) # Inicia o menu HUD inicial

            case '2': # Load Game
                slot = game_logic.choose_save_slot() # Escolhe o slot de salvamento
                game_processor = game_logic.initialize_game_services(slot) # Inicializa os serviços do jogo
                lore = load_lore(slot) # Carrega a lore do jogo
                try:
                    hero , narrativa = game_logic.load_game(slot) # Carrega o jogo salvo
                    print(colored(narrativa, 'cyan'))
                    input(colored("Pressione Enter para continuar...", "green"))
                    game_logic.initial_hud_menu(hero,atlas,gps,items,enemies,skills,lore, game_processor, slot) # Inicia o menu HUD inicial
                
                except Exception as e:
                    print(colored(f"Erro ao carregar o jogo: {e}", "red"))
                    input(colored("Pressione Enter para continuar...", "green"))

            case '3': # Settings
                print(colored("Settings menu is under construction.", 'yellow'))
                input(colored("Pressione Enter para continuar...", "green"))
            case '4': # Exit
                print(colored("Exiting the game. Goodbye!", 'red'))
                break
            case _: #Invalid option
                print("Invalid option. Please try again.")

main() # Inicia o jogo chamando a função principal
