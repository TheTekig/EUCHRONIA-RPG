
#region IMPORTS

import os

from termcolor import colored
from euchronia.models import HitResult
from random import choices,random,randint
from time import sleep

import euchronia.game_logic as gl
from UI.ui_menu import _combat_menu , _combat_menu_actions

#endregion

#region   Calculate Base Functions

def _use_skill(attacker, defender, skill_data): # Verifica se a skill pode ser usada (usos restantes) e decrementa o contador de usos.
    """
    """
    if "uses" in skill_data and skill_data["uses"] <= 0:
        #skill não pode ser usada
        return "NoAttack"
        
    if "uses" in skill_data:
        # decrementa usos restantes
        skill_data["uses"] -= 1
        return "Attack"
        
def _action_time(Hero, Enemy, all_items_data): # Calcula quem age baseado no sistema de Action Time, ou seja quem chega a ao limite primeiro tem o turno.
    """
    """
    combat = [Hero, Enemy]  #Lista de combatentes
    limit = 100            # Valor de limite para ação

    while True:
        for fighter in combat:
            lucky = randint(-2, 10)      # Variação aleatória para velocidade

            fighter.action_time += fighter.total_speed(all_items_data) + lucky

            if fighter.action_time >= limit:
                fighter.action_time -= limit
                return fighter                      # Retorna o combatente que agirá
        
def _calculate_precision(precision): # Calcula se o ataque acerta, erra ou causa dano parcial baseado na precisão da skill.
    """ 
    """

    Results = [HitResult.MISS, HitResult.SCRATCH, HitResult.HIT]  # Possíveis resultados

    hit_chance = precision
    scratch_chance = (1.0 - hit_chance) * 0.7
    miss_chance = (1.0 - hit_chance) * 0.3

    weights = [miss_chance, scratch_chance, hit_chance] # Pesos para cada resultado
    return choices(Results, weights=weights, k=1)[0] # Retorna o resultado baseado nos pesos

def _calculate_damage(defender, damage, skill_effect, all_items_data): # Calcula o dano final após considerar a defesa do defensor e possíveis efeitos da skill.
    """ 
    """
    
    defense_reduction_percent = defender.total_defense(all_items_data) * (1 - skill_effect.get("defense_ignore", 0)) # Defesa efetiva após ignorância
    defense_reduction_percent = defense_reduction_percent / (defense_reduction_percent + 100) # Fórmula de redução de dano
    damage = damage * (1 - defense_reduction_percent) # Dano após o processamento da defesa

    return max(1, int(damage)) #Retorna dano mínimo de 1 garantindo que sempre cause dano

#endregion

#region   Skills Functions

def _attack_skill(attacker, defender, skill_data, all_items_data): # Processa as Skills do tipo Ataque
    """ 
    """
    skill_effect = skill_data.get("effect", {}) # Busca os efeitos da skill no dicionário de dados
    damage = attacker.total_strength(all_items_data) * skill_effect.get('damage_multiplier', 1.0) # Calcula dano base da skill  | total_strength(soma força base + bônus de itens) | damage_multiplier (multiplicador de dano da skill)

    if random() < skill_effect.get('critical_chance', 0):   # Chance de acerto crítico
        damage *= 2
    
    accuracy = _calculate_precision(skill_data.get('precision', 1.0))   # Calcula precisão do ataque

    match accuracy:
        case HitResult.MISS:
            return "MISS"

        case HitResult.SCRATCH:
            damage *= 0.5
            damage = _calculate_damage(defender, damage, skill_effect, all_items_data)  # Calcula dano final considerando defesa (chamada da função)
            defender.take_damage(damage)           # Aplica dano ao defensor
            return f"Half Damage - {damage} Damage"

        case HitResult.HIT:
            damage = _calculate_damage(defender, damage, skill_effect, all_items_data) # Calcula dano final considerando defesa (chamada da função)
            defender.take_damage(damage)          # Aplica dano ao defensor
            return f"Full Damage - {damage} Damage"
        
def _buff_skill(attacker, skill_data): # Processa as Skills do tipo Buff
    """ 
    """
    skill_effect = skill_data.get("effect", {})
    
    duration = skill_data.get('duration', 0)    # Duração do buff
    applied_effect = {}     # Dicionário para armazenar os efeitos aplicados

    if "defense_multiplier" in skill_effect:
        applied_effect["defense_multiplier"] = skill_effect["defense_multiplier"]   # Aplica aumento de defesa
    if "strength_multiplier" in skill_effect:
        applied_effect["strength_multiplier"] = skill_effect["strength_multiplier"] # Aplica aumento de força
    if "speed_multiplier" in skill_effect:
        applied_effect["speed_multiplier"] = skill_effect["speed_multiplier"] # Aplica aumento de velocidade
    
    if not applied_effect:  # Nenhum efeito válido para aplicar
        return f"{attacker.name} tried to buff, but nothing happend!"
    
    attacker.apply_effect(
        nome=f"Buff_{attacker.name}",
        dados={"effect" : applied_effect, "duration" : duration}
    )     # Chama Função para aplicar efeito no atacante

    return f"{attacker.name} got a buff during {duration} rounds!"

def _debuff_skill(defender, skill_data): # Processa as Skills do tipo Debuff
    """ 
    """
    skill_effect = skill_data.get("effect", {})
    applied_effect = {}     # Dicionário para armazenar os efeitos aplicados

    duration = skill_data.get("duration", 0) # Duração do debuff

    if "speed_reduce" in skill_effect:
         applied_effect["speed_reduce"] = skill_effect["speed_reduce"]  # Reduz velocidade
    if "defense_reduce" in skill_effect:
         applied_effect["defense_reduce"] = skill_effect["defense_reduce"]  # Reduz defesa
    if "burn_chance" in skill_effect:
         applied_effect["damage_per_turn"] = skill_effect.get("burn_damage", 5)  # Dano por turno de queimadura
    if "damage_per_turn" in skill_effect:
         applied_effect["damage_per_round"] = skill_effect["damage_per_turn"] # Dano por turno (veneno, queimadura, etc)

    if not applied_effect:
        return f"{defender.name} tried to debuff, but nothing happend!"
    
    defender.apply_effect(
        nome=f"Debuff_{defender.name}",
        dados={"effect" : applied_effect, "duration" : duration}
    ) # Chama Função para aplicar efeito no defensor

    return  f"{defender.name} got a debuff during {duration} rounds"

def _control_skill(defender, skill_data): # Processa as Skills do tipo Controle
    """ 
    """
    skill_effect = skill_data.get("effect", {}) # Busca os efeitos da skill no dicionário de dados
    freeze = skill_effect.get("freeze_chance", 1) # Chance de congelamento

    duration = skill_data.get("duration", 0)   # Duração do efeito

    if random() <= freeze:  # Verifica se o efeito é aplicado
        defender.apply_effect(
            nome= "Freezed",
            dados= {"effect" : {"lost_round" : True}, "duration" : duration} 
        )                                                                               # Chama Função para aplicar efeito no defensor
        return f"{defender.name} got freeze"
    else:
        return f"{defender.name} resisted to freeze"

def _skill_manager(attacker, defensor, skill_data, all_items_data): # Gerencia o uso de skills baseado no tipo delas, enviando elas para processamento correto de cada uma.
    """ 
    """   

    skill_name = skill_data.get("name", "Unknow Attack")        # Nome da skill
    skill_type = skill_data.get("type", "ATTACK")               # Tipo da skill

    if skill_type in ["ATTACK", "DEBUFF", "CONTROL"]:           # Tipos que requerem verificação de precisão / Verifica se o ataque acerta
        accuracy = _calculate_precision(skill_data.get("precision", 1))
        if accuracy == HitResult.MISS:
            return "MISS"

    match skill_type:
        case "ATTACK":
            return _attack_skill(attacker, defensor, skill_data, all_items_data) # Processa skill de ataque
        
        case "BUFF":
            return _buff_skill(attacker, skill_data)    # Processa skill de buff

        case "DEBUFF":
            return _debuff_skill(defensor, skill_data)  # Processa skill de debuff
        
        case "CONTROL":
            return _control_skill(defensor, skill_data) # Processa skill de controle
        case _: 
            return "INVALID"    # Tipo inválido

def _process_active_effects(fighter): # Processa efeitos ativos (dano por turno, etc)
    """
    """
    for effect_name, effect_data in list(fighter.efeitos_ativos.items()): # Usa list() para evitar modificação durante iteração
        effects = effect_data.get("effect", {})
        
        # Dano por turno (veneno, queimadura)
        if "damage_per_round" in effects:
            damage = effects["damage_per_round"]    # Dano por turno
            fighter.take_damage(damage) # Aplica dano ao lutador
            print(f"{fighter.name} sofre {damage} de dano de {effect_name}!")

def _reduce_effect_duration(fighter, effect_name): # Reduz duração de um efeito e remove se necessário
    """
    """
    if effect_name in fighter.efeitos_ativos:   # Verifica se o efeito está ativo
        fighter.efeitos_ativos[effect_name]["duration"] -= 1
        
        if fighter.efeitos_ativos[effect_name]["duration"] <= 0: # Verifica se a duração acabou
            fighter.remove_effect(effect_name)
            print(f"O efeito {effect_name} de {fighter.name} terminou!")

#endregion 

#region   Combat Loop Functions

def combat_loop(Hero, Enemy, Skills, items_data): # Loop principal de combate entre Hero e Enemy.
    """
    """
    log = ""    # Log de ações do combate
    loop = True
    while loop:
        # Processa efeitos ativos no início do turno
        os.system("cls")
        _combat_menu(Hero, Enemy, log, items_data) # Exibe menu de combate atualizado | Log de ações do turno anterior
        log = ""

        if Hero.is_alive() and Enemy.is_alive():    # Continua o combate enquanto ambos estiverem vivos
            _process_active_effects(Hero)   # Verifica e aplica efeitos ativos no Herói
            _process_active_effects(Enemy)
            
            # Determina quem age
            active_fighter = _action_time(Hero, Enemy, items_data)
            log += f"⚠ {active_fighter.name} Turn!\n"

            # Verifica se está congelado
            if active_fighter.has_effect("Freezed"):
                log += f"{active_fighter.name} está congelado e não pode agir!\n"
                _reduce_effect_duration(active_fighter, "Freezed")
                continue

            
            # Executa turno do lutador ativo
            if active_fighter == Hero:
                skill_log, action = _hero_turn(Hero, Enemy, Skills, items_data) # Turno do Herói - Retorna log da skill usada e ação realizada
            else:
                skill_log, action = _enemy_turn(Enemy, Hero, Skills, items_data) # Turno do Inimigo - Retorna log da skill usada e ação realizada

            log += (skill_log + "\n")
            log += (action + "\n")

        else:   # Termina o combate se um dos lutadores morrer
            loop = False    
        
    if Hero.is_alive(): # Vitória do Herói
        
        # Recompensas por vitória
        Hero.gain_experience(Enemy) # Ganha XP do inimigo
        Loot = Enemy._get_one_item_loot(items_data) # Obtém um item de loot do inimigo
        Hero._add_item_to_inventory(Loot) # Adiciona item ao inventário do herói

        print(colored(f"{Enemy.name} foi derrotado!", "green"))
        sleep(0.5)
        print(colored(f"{Hero.name} recebeu {Enemy.experience} XP", "cyan"))
        sleep(0.5)
        print(colored(f"{Hero.name} recebeu {Loot}", "yellow"))
        sleep(0.5)

        input(colored("Press Enter to Continue", "green"))
        return f"{Hero.name} derrotou o inimigo"    # Vitória do Herói | Passa mensagem de vitória para o build_post_combat prompt para processamento pós-combate

    else:
        input(colored("Press Enter to Continue", "green"))
        return f"{Hero.name} foi derrotado"     # Derrota do Herói | Passa mensagem de vitória para o build_post_combat prompt para processamento pós-combate

def _hero_turn(Hero, Enemy, Skills, items_data): # Ações do herói durante o seu turno no combate.
    """
    """
    _combat_menu_actions()
                
    option = input(">> ")
    while option.upper() not in ["S", "I", "ST", "R"]:  # Validação de entrada
        option = input(">> ")

    match option.upper():
        case "S":
            print("Skills:")
            skill_option = {}   # Dicionário para mapear opções de skills
            for i, skill_name in enumerate(Hero.skills):    # Lista de skills do herói | para cada skill, cria uma opção numérica
                print(colored(f"[{i+1}].{skill_name} / ", "cyan", attrs=["bold"]), end="")
                skill_option[str(i+1)] = skill_name

            skill_choice = input(">> ")     # Escolha da skill
            while skill_choice not in skill_option: # Validação de entrada
                skill_choice = input(">> ")

            selected_skill_option = skill_option[skill_choice]  # Obtém o nome da skill selecionada
            skilluse = _use_skill(Hero, Enemy, Skills[selected_skill_option]) # Verifica se a skill pode ser usada
            
            skill_log = selected_skill_option

            if skilluse == "NoAttack":
                return skill_log, f"{Hero.name} tentou usar {selected_skill_option}, mas não tinha usos restantes!" # Skill sem usos restantes
                
            else:
                action = _skill_manager(Hero, Enemy, Skills[selected_skill_option], items_data) # Processa a skill selecionada
                
            return skill_log , action   # Retorna log da skill usada e ação realizada | Retorna sempre 2 valores para consistência 

        case "I":
            gl.manage_inventory(Hero, items_data) # Gerencia inventário do herói
            return "", "" # Retorna vazio para log e ação, pois gerenciar inventário não afeta o combate diretamente

        case "ST":
            print("Status:") # Exibe status do herói
            Hero._status()
            return "", "" # Retorna vazio para log e ação, pois exibir status não afeta o combate diretamente

        case "R":
            print("Run")
            return "You Runaway", "💨" # Tenta Fugir, retorna para indicacao no build_post_combat
        case _:
            pass
 
def _enemy_turn(Enemy, Hero, Skills, items_data): # Ações do inimigo durante o seu turno no combate.
    """
    """

    size = len(Enemy.skills)    # Tamanho da lista de skills do inimigo
    if size > 0:    # Inimigo escolhe skill aleatória
        skill_option = randint(0, size - 1) # Índice aleatório da skill
        skill_option = Enemy.skills[skill_option] # Nome da skill selecionada
        action = _skill_manager(Enemy, Hero, Skills[skill_option], items_data) # Processa a skill selecionada
        skill_log = skill_option # Log da skill usada
        return skill_log, action
    else: # Inimigo usa ataque básico se não tiver skills
        skill_option = 0
        action = _skill_manager(Enemy, Hero, Skills[skill_option], items_data)
        return action

#endregion           
