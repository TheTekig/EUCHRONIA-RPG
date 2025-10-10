#region Explore Logic





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
        print(f"Não há espaço para equipar mais itens do tipo '{item_type}'.")
        print("Funcionalidade de substituir item ainda não implementada.")
        return

    hero.inventory.remove(item_name)
    hero.equipment[item_type].append(item_name)
    
    print(f"{item_name} foi equipado.")

#endregion

