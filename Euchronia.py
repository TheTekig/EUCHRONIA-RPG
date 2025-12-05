import json
from euchronia import ai_services, general_logic, models, combat_logic, game_logic
from UI import ui_menu
import os
from termcolor import colored



#region LOAD DATA

classes = general_logic.load_json('data/classes.json')
enemies = general_logic.load_json('data/enemy.json')
items = general_logic.load_json('data/itens.json')
skills = general_logic.load_json('data/skills.json')
shopkeepers = general_logic.load_json('data/shopkeepers.json')

atlas = general_logic.load_json('data/mapconfig/atlas.json')
gps = general_logic.load_json('data/mapconfig/gps_map.json')

def load_lore(slot):
    with open (f'saves/{slot}/lore.txt', "r") as lore_text:
        lore = lore_text.read()
        return lore

#endregion

def main():

    while True:

        os.system('cls' if os.name == 'nt' else 'clear')
        ui_menu._inital_menu()

        choice = input(">> ")
        while choice not in ['1', '2', '3', '4']:
            print("Invalid option. Please try again.")
            choice = input(">>")

        match choice:
            case '1':

                hero = game_logic.create_hero(classes)
                slot = game_logic.choose_save_slot()

                game_processor = game_logic.initialize_game_services(slot)

                lore = load_lore(slot)

                game_logic.save_game(hero, lore, slot)
                input(colored("Pressione Enter para continuar...", "green"))
                
                game_logic.initial_hud_menu(hero,atlas,gps,items,enemies,skills,lore, game_processor, slot)

            case '2':
                slot = game_logic.choose_save_slot()
                game_processor = game_logic.initialize_game_services(slot)
                lore = load_lore(slot)
                try:
                    hero , narrativa = game_logic.load_game(slot)
                    print(colored(narrativa, 'cyan'))
                    input(colored("Pressione Enter para continuar...", "green"))
                    game_logic.initial_hud_menu(hero,atlas,gps,items,enemies,skills,lore, game_processor, slot)
                
                except Exception as e:
                    print(colored(f"Erro ao carregar o jogo: {e}", "red"))
                    input(colored("Pressione Enter para continuar...", "green"))

            case '3':
                print(colored("Settings menu is under construction.", 'yellow'))
                input(colored("Pressione Enter para continuar...", "green"))
            case '4':
                print(colored("Exiting the game. Goodbye!", 'red'))
                break
            case _:
                print("Invalid option. Please try again.")

main()
