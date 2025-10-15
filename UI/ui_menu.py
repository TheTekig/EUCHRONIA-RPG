from termcolor import colored

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
    print(colored("1. New Game", 'cyan', attrs=['bold']).center(95))
    print(colored("2. Load Game", 'cyan', attrs=['bold']).center(95))
    print(colored("3. Settings", 'cyan', attrs=['bold']).center(95))
    print(colored("4. Exit", 'cyan', attrs=['bold']).center(95))
