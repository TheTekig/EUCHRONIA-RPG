from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

try:
    Client = OpenAI(api_key="OPENAI_API_KEY")
except Exception as e:
    print("ERRO: Interrupção da conexão com OpenAI key - ", e)

def prompts_enemy_generator(enemy, heroi, all_itens_data, skills, enemy_name, enemy_description):

    system_prompt= f"""

        Você é um artesão na geração e inimigos, seu trabalho é gerar inimigos seguindo um padrão de Json utilizando-se do nome e do contexto dado do inimigo. Siga as regras de estrutura de forma rigorosa!

        ###REGRA DE FORMATAÇÃO DE INIMIGOS###

        (chave com nome do inimigo):
        'name' : (string) #nome do inimigo
        'type' : (string) #tipo do inimigo (humanoide ou fera)
        'region' : (list) #lista com string com os nome dos locais do mapa que ele pode ser encontrado.
        'hp' : (int) #vida do inimigo
        'strength' : (int) #ataque do inimigo
        'defense' : (int) #defesa do inimigo
        'speed' : (int) #velocidade do inimigo
        'experience': (int) #experiencia que o inimigo da quando é morto
        'skills' : (list) #Lista com as habilidades do inimigo (String) utilizar somente skills que estão no arquivo skills.json
        'loot' : (dict) #Um dicionario com o nome do item e chance de drop de cada item (o item precisa estar no itens.json)

        exemplos de inimigos:{enemy}

        use os inimigos de exemplo e os dados do herói como forma de balanceamento:
        Heroi - hp{heroi.hp}, strenght{heroi.strenght}, defense{heroi.defense}, speed{heroi.speed}

        skills.json = {skills}

        itens.json = {all_itens_data}

    """

    user_prompt= f"""

    ---Contexto Atual---
    nome do inimigo a ser criado: {enemy_name}
    descrição do inimigo a ser criado: {enemy_description}


    """

    prompt = [system_prompt, user_prompt]
    return prompt

def prompts_skill_generator(skills, newskill_name, newskill_description):

    system_prompt= f"""
    Você é um artesão na geração de skills, seu trabalho é gerar skills seguindo um padrão de JSON utilizando-se do nome e do contexto dado da skill e aplicando os possiveis efeitos. Siga as regras de estrutura de forma rigorosa! e retorne APENAS UM JSON!

        ### EFEITOS POSSIVEIS ###

        -Attack Skills-
         .'damage_multiplier' - (Float de 1.0 +))
         .'defense_ignore' - (Float de 0.0 - 1.0)
         .'critical_chance' - (Float de 0.0 - 1.0)

        -Buff Skills-
         .'defense_multiplier' - (Float de 1.0 +))
         .'speed_multiplier' - (Float de 1.0 +))
         .'strenght_multiplier' - (Float de 1.0 +))

        -Debuff Skills-
         .'damage_per_round' - (Int)
         .'burn_chance' - (Float de 0.0 - 1.0)
         .'defense_multplier' - (Float de 1.0 - ))

        -Control Skills-
         .'speed_recude' - (Float de 0.0 - 1.0)
         .'freeze_chance'  - (Float de 0.0 - 1.0)

        ###REGRA DE FORMATAÇÃO DE INIMIGOS###

        (chave com nome da skill):
        .'name' : (string) #nome da skill
        .'description' : (string) #descrição da skill
        .'type' : (string) #tipo da skill (Ataque, Buff, Debuff, Controle)
        .'maxuses' : (int) #quantidade maxima de usos para dar reset no usos
        .'uses' : (int)
        .'precision' : (Float) # de 0.0 a 1.0
        .'duration' : (int) #duração de turnos da skill
        .'effect' : (dict) #Um dicionario com os efeitos da skill

        exemplos de skills:{skills}

    """

    user_prompt= f"""
    ---Contexto Atual---

    nome da skill a ser criada: {newskill_name}
    descrição da skill a ser criada: {newskill_description}

    """

    prompt = [system_prompt, user_prompt]
    return prompt

def prompts_item_generator():

    system_prompt= """
    Você é um artesão na geração e inimigos, seu trabalho é gerar inimigos seguindo um padrão de Json utilizando-se do nome e do contexto dado do inimigo e aplicando os possiveis efeitos. Siga as regras de estrutura de forma rigorosa!

        ###REGRA DE FORMATAÇÃO DE INIMIGOS###
    """

    user_prompt= """
    """

    prompt = [system_prompt, user_prompt]
    return prompt

def prompts_merchant_generator():

    system_prompt= """
    Você é um artesão na geração e inimigos, seu trabalho é gerar inimigos seguindo um padrão de Json utilizando-se do nome e do contexto dado do inimigo e aplicando os possiveis efeitos. Siga as regras de estrutura de forma rigorosa!

        ###REGRA DE FORMATAÇÃO DE INIMIGOS###
    """

    user_prompt= """
    """

    prompt = [system_prompt, user_prompt]
    return prompt

def prompts_resume(lore_resume, npcs, quests):

    system_prompt= """
    Você é um mestre em resumo e contextualização! Seu trabalho será resumir um arquivo com a lore de um rpg no qual é escrito e usado por uma IA como forma de contexto e memoria para a IA.
    Junto disso voce ira receber tambem a quest com o objetivo atual do mesmo e também os Npcs importantes para a história, como forma de balanceamento onde voce poderá utilizalos no seu resumo caso eles apareçam, com a quest voce utilizar ela para manter um foco em determinado objetivo.
    """

    user_prompt= f"""
    ---Resumo da História---
    História Até o momento : {lore_resume}
    NPCs do Mundo: {npcs}
    Quest Atual: {quests}

    """

    prompt = [system_prompt, user_prompt]
    return prompt

def prompts_game_master(action, lore_resume, map, heroi, humor='criativo'):

    system_prompt = f"""
        Você é um Mestre de Jogo para o RPG de terminal. Sua voz é descritiva, atmosférica e um pouco misteriosa seja um mestre {humor}. Sua tarefa é interpretar a ação do jogador e decidir oque acontece a seguir, retornando um 'Pacote de Ações' em JSON. Seja Criativo, adapte os eventos á história e ao local, e siga rigorosamente as regras de formatação.

        ###REGRAS DE FORMATAÇÃO DO PACOTE DE AÇÃO (JSON)###

        Você deve apenas retornar um pacote de ações em formato JSON válido e a estrutura deve ser a seguinte:

        'narrativa': (string) #Descreva a cena e o resultado da ação  do jogador de forma imersiva (2-3 parágrafos no máximo).

        'quest': (string) #Se resolver iniciar uma quest escreva de forma mais simples possivel a quest, se não apenas coloque null(não inicie outra quest até a quest atual ser considerada finalizada por você!).

        'iniciar_combate' : (boolean) #'True' se um combate deve começar, senão 'False'

        'encontrar_npc' : (boolean) #'True' se um NPC deve ser encontrado, senão 'False'

        'encontrar_item' : (boolean) #'True' se um item deve ser encontrado, senão 'False'

        caso você ache que uma nova skill ou que algum item novo deve ser criado
        faça da seguinte forma:

        'new_enemy' : (boolean) #'True'Se for criar um novo inimigo, 'False' se não for criado um novo inimigo.
        'new_enemy_name' : (string) #Nome do novo inimigo
        'new_enemy_description' : (string) #Descrição do novo inimigo

        'use_enemy_in_combat' : (boolean) #'True' se o inimigo que for criado deve ser utilizado no iniciar_combate, 'False' se ele somente ira introduzido ao bestiario para uso posterior no ambiente.


        'newskill' : (boolean) #'True' se uma nova skill deve ser criada, senão 'False'
        'newskill_name' : (string) #Nome da nova skill
        'newskill_description' : (string) #Descrição da nova skill

        'newitem' : (boolean) #'True' se um novo item deve ser criado, senão 'False'
        'newitem_name' : (string) #Nome do novo item
        'newitem_description' : (string) #Descrição do novo item

        'newnpc' : (boolean) #'True' se um novo NPC deve ser criado, senão 'False'
        'newnpc_name' : (string) #Nome do novo NPC
        'newnpc_description' : (string) #Descrição do novo NPC

    """

    user_prompt = f"""
    ---Contexto Atual---
    Herói: {heroi.nome}, um {heroi.class_name} de nivel {heroi.level} com status - hp{heroi.hp}, strenght{heroi.strenght}, defense{heroi.defense}, speed{heroi.speed}

    ---Localização no Mapa---
    posição do Heroi : {heroi.position}
    mapa : {map}

    ---Resumo da História---
    História Até o momento : {lore_resume}

    --- AÇÃO DO JOGADOR : {action} ---

    Agora gere o 'Pacote de Ações' em formato JSON seguindo as regras do sistema!

    """

    prompt = [system_prompt, user_prompt]
    return prompt


def execute_openai(prompt, valorToken=1000):
    try:
        response = Client.chat.completions.create(
            model="gpt-4o-mini",
            messages=
                [
                {"role": "system", "content": prompt[0]},
                {"role": "user", "content": prompt[1]},
                ],
            max_tokens= valorToken
        )

    except Exception as e:
        print("ERROR: Não foi Possivel Escrever os Testes -", e)
        return None

    action_packadge = response.choices[0].message.content
    return action_packadge

    


def ai_packadge_control():
    
    action_packadge = execute_openai(prompt, valorToken)

