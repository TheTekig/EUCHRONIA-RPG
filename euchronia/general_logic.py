import json
from termcolor import colored

def append_json(filepath, info):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
    
        data.append(info)
    
        with open(filepath, 'w', encoding= 'utf-8') as file:
            json.dump(data)

        print(colored(f"{info} foi salvo ao banco de dados")
              
    except Exception:
        print(colored(f"Erro ao salvar {info} no banco de dados") 

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(filedata, file, indent=4, ensure_ascii=False)




