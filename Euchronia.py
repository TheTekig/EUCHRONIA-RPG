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

with open ('saves/slot_1/lore.txt', "r") as lore_text:
    lore = lore_text.read()

#endregion

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    ui_menu._inital_menu()

    while True:
        choice = input(">> ")
        while choice not in ['1', '2', '3', '4']:
            print("Invalid option. Please try again.")
            choice = input(">>")

        match choice:
            case '1':

                hero = game_logic.create_hero(classes)

                input(colored("Pressione Enter para continuar...", "green"))
                
                game_logic.initial_hud_menu(hero,atlas,gps,items,enemies,skills,lore)

            case '2':
                print(colored("SAVE AND LOAD menu is under construction.", 'yellow'))
            case '3':
                print(colored("Settings menu is under construction.", 'yellow'))
            case '4':
                print(colored("Exiting the game. Goodbye!", 'red'))
                break
            case _:
                print("Invalid option. Please try again.")

main()
