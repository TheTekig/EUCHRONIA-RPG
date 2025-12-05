from termcolor import colored
from time import sleep

def _logo():
    logo = """
        ███████ ██    ██  ██████ ██   ██ ██████   ██████  ███    ██ ██  █████
        ██      ██    ██ ██      ██   ██ ██   ██ ██    ██ ████   ██ ██ ██   ██
        █████   ██    ██ ██      ███████ ██████  ██    ██ ██ ██  ██ ██ ███████
        ██      ██    ██ ██      ██   ██ ██   ██ ██    ██ ██  ██ ██ ██ ██   ██
        ███████  ██████   ██████ ██   ██ ██   ██  ██████  ██   ████ ██ ██   ██
    """
    return logo

def _inital_menu():
    print(colored(_logo(), 'magenta'))
    print("\u2500" * 85)
    print(colored("1. New Game", 'cyan', attrs=['bold']).center(95))
    print(colored("2. Load Game", 'cyan', attrs=['bold']).center(95))
    print(colored("3. Settings", 'cyan', attrs=['bold']).center(95))
    print(colored("4. Exit", 'cyan', attrs=['bold']).center(95))

def _combat_menu(hero, enemy, _log):
    _combat_logo = """
 ██████  ██████  ███    ███ ██████   █████  ████████ 
██      ██    ██ ████  ████ ██   ██ ██   ██    ██    
██      ██    ██ ██ ████ ██ ██████  ███████    ██    
██      ██    ██ ██  ██  ██ ██   ██ ██   ██    ██    
 ██████  ██████  ██      ██ ██████  ██   ██    ██                                                                                                                         
"""
    print(colored(f"{_combat_logo}" , 'magenta'))
    print("\u2500" * 85)
    print(colored(f"🧑 {hero.name}     ", "cyan", attrs=["bold"]), colored("❤ HP:", "red", attrs=["bold"]), colored(f"{hero.hp}", "red"),"/",colored(f"{hero.maxhp}     ", "red"), colored("⚔ STR:", "blue", attrs=["bold"]),colored(f"{hero.strength}      ", "blue"), colored("🛡 DEF:", "magenta", attrs=["bold"]), colored(f"{hero.defense}", "magenta"))
    print(colored(f"👹 {enemy.name}    ", "cyan", attrs=["bold"]), colored("❤ HP:", "red", attrs=["bold"]), colored(f"{enemy.hp}", "red"),"/",colored(f"{enemy.maxhp}   ", "red"), colored("⚔ STR:", "blue", attrs=["bold"]),colored(f"{enemy.strength}     ", "blue"), colored("🛡 DEF:", "magenta", attrs=["bold"]), colored(f"{enemy.defense}", "magenta"))
    print("\u2500" * 85)

    for char in _log:
        print(char, end="")
        sleep(0.1)
    
    print("\u2500" * 85)
    input(colored("Press Enter to Continue", "green"))

def _combat_menu_actions():
    print(colored("✨[S]kill", "cyan"), colored("🎒[I]nventory", "cyan"), colored("📖[ST]atus", "cyan"), colored("💨[R]un", "yellow"))
    print("\u2500" * 85)

def _Hud(location_name):
    hub = """
                                      ╻ ╻╻ ╻╺┳┓
                                      ┣━┫┃ ┃ ┃┃
                                      ╹ ╹┗━┛╺┻┛
"""
    print(colored(f"{hub}", "magenta"))
    print("\u2500" * 30, colored("Você está em:","magenta", attrs=["bold"]),colored(f"{location_name}", "green", attrs=["bold"]),"\u2500" * 30)
    print(colored("     ✨[A]ctions  ", "cyan"), colored("🎒[I]nventory  ", "cyan"), colored("📖[S]tatus ", "cyan"), colored("🗺 [M]apa   ", "cyan"), colored("💤[R]est   ", "cyan"), colored("💨[Q]uit", "yellow"))
    print("\u2500" * 85)

def _sub_Hud():
    _sub_hub ="""
                                ┏━┓┏━╸╺┳╸╻┏━┓┏┓╻┏━┓
                                ┣━┫┃   ┃ ┃┃ ┃┃┗┫┗━┓
                                ╹ ╹┗━╸ ╹ ╹┗━┛╹ ╹┗━┛
"""    
    print(colored(f"{_sub_hub}", "magenta"))
    print("\u2500" * 85)
    print(colored("              🐎 [E]xplore     ", "cyan"), colored("🤼[F]ight   ", "cyan"), colored("🔭[O]bserve    ", "cyan"), colored("💨[R]eturn     ", "yellow"))
    print("\u2500" * 85)
