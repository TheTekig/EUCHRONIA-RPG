import os
from termcolor import colored

from UI.ui_menu import npc_hud

def talk_menu(npc, hero, all_items_data, skills, game_processor):
    while True:
        os.system('cls')
        npc_hud(npc)

        option = input(">>")
        while option.upper not in ["T", "G", "R"]:
            option = input(">>")
        
        match option:
            case "T":
                action = input(">>")
                prompt = game_processor.prompt_builder.build_npc_response_prompt()
                narrativa ,quest = game_processor.process_npc_response_package(prompt, hero, all_items_data, skills)
                pass

            case "G":
                pass

            case "R":
                pass

            case _:
                pass
            


