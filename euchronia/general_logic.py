import json
from termcolor import colored

#region JSON HANDLERS

def append_json(filepath, info): # Adiciona informações a um arquivo JSON existente.
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
    
        data.append(info)
    
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print(colored(f"{info} foi salvo ao banco de dados", "green"))
              
    except Exception as e:
        print(colored(f"Erro ao salvar {info} no banco de dados: {e}", "red"))

def load_json(filepath): # Carrega e retorna os dados de um arquivo JSON.
    with open(filepath, 'r', encoding='utf-8') as file:

        open_file = json.load(file)

    return open_file

#endregion


