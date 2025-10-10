<h1 align="center">🧭 EUCHRONIA</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python">
  <img src="https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow">
  <img src="https://img.shields.io/badge/License-MIT-green">
  <img src="https://img.shields.io/badge/OpenAI-Integrated-orange">
</p>

---

  
```
                      ███████╗██╗   ██╗ ██████╗██╗  ██╗██████╗  ██████╗ ███╗   ██╗██╗ █████╗
                      ██╔════╝██║   ██║██╔════╝██║  ██║██╔══██╗██╔═══██╗████╗  ██║██║██╔══██╗
                      █████╗  ██║   ██║██║     ███████║██████╔╝██║   ██║██╔██╗ ██║██║███████║
                      ██╔══╝  ██║   ██║██║     ██╔══██║██╔══██╗██║   ██║██║╚██╗██║██║██╔══██║
                      ███████╗╚██████╔╝╚██████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║██║██║  ██║
                      ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝
```



> 🜏 *Um RPG de terminal que une Programação Orientada a Objetos, narrativa procedural e Inteligência Artificial para criar um mundo vivo e imprevisível.*

---
<div align="center">
## 📜 Sobre o Projeto
</div>

**Euchronia** é um RPG de terminal em Python que combina:
- ⚙️ **POO estruturada** para um núcleo limpo e expansível.  
- ⚔️ **Combate estratégico por turnos com Action Time** e precisão probabilística.  
- 💎 **Buffs, debuffs, controle e habilidades configuráveis** via JSON.  
- 🧠 **Integração com IA (OpenAI)** para narrativa adaptativa e geração procedural.  

O resultado é uma engine narrativa de RPG que **reage às ações do jogador** — cada escolha molda o mundo.

---
<div align="center">
## 🧱 Estrutura do Projeto
</div>

    EUCHRONIA/
    │
    ├── euchronia/
    │   ├── models.py          # Classes: Player, Enemy, AliveModel
    │   ├── combat_logic.py    # Sistema de combate e skills
    │   ├── game_logic.py      # HUD, menus e exploração
    │   └── ai_services.py     # (futuro) integração com IA
    │
    ├── data/
    │   ├── classes.json       # Classes jogáveis
    │   ├── skills.json        # Habilidades e efeitos
    │   ├── itens.json         # Armas, poções e equipamentos
    │   ├── enemy.json         # Inimigos e loot tables
    │   ├── gps_map.json       # Conexões entre regiões
    │   └── atlas.json         # Locais do mundo
    │
    ├── saves/                 # Dados persistentes do jogador
    ├── docs/                  # GDD e documentação
    │   └── RPG - EUCHRONIA.pdf
    ├── main.py
    ├── requirements.txt
    └── README.md

---

<p align="center"> ⚔️ Mecânica de Combate </p>
Action Time: a velocidade define a ordem de ataque, com variação aleatória a cada rodada.

Precisão probabilística:

    MISS (erro total)
        
    SCRATCH (dano reduzido)
        
    HIT (dano completo)

Fórmula balanceada de dano:

    defense_reduction = defense / (defense + 100)
    damage_final = damage * (1 - defense_reduction)

---

<p align="center"> 🧩 Skills são categorizadas em: </p>

  Tipo	Exemplo	Efeito
  ATTACK	Golpe Pesado	Dano físico direto
  BUFF	Grito de Batalha	Aumenta força ou defesa
  DEBUFF	Adagas Envenenadas	Reduz defesa ou aplica veneno
  CONTROL	Prisão de Gelo	Paralisa o inimigo

Todas configuradas em skills.json — expansíveis sem alterar o código.
 
 ---
 
<p align="center"> 🎮 Prévia de Combate (Terminal) </p>

```
──────────────────────────────────────────────────────────────
👤 Herói (Lv 3)        ❤️ HP: 78/100   ⚔️ STR: 12   🛡 DEF: 9
vs
🐀 Rato Gigante        ❤️ HP: 0/25      ☠️ DERROTADO
──────────────────────────────────────────────────────────────
💥 Golpe Pesado causa 23 de dano crítico!
🧪 Efeito “Sangramento” aplicado por 3 turnos!
🩸 O inimigo sofre 4 de dano residual.
──────────────────────────────────────────────────────────────
🏆 Vitória! +15 XP | Loot: Pele de Rato (x1)
──────────────────────────────────────────────────────────────
```

Interface otimizada para cores com rich e termcolor, incluindo HUD dinâmica com Live() e logs coloridos.

---

 <p align="center">🧠 Arquitetura POO </p>

```

Classe	          Função	            Destaque
AliveModel	    Entidades       vivas	HP, força, defesa, efeitos
PlayerModel	    Jogador	        Inventário, XP, level, equips
EnemyModel	    Inimigos	      Dados carregados de enemy.json
CombatManager	  (planejado)	    Controla rodada e ordem de turnos

```

Cada entidade pode aplicar, atualizar e remover efeitos temporários de combate (buffs, debuffs, status).

---

<p align="center"> 🌍 Mundo e Exploração </p>
Baseado em grafo de conexões (gps_map.json), cada nó é uma região explorável.

O atlas contém lore, bioma e inimigos locais.

O jogador pode viajar, explorar e enfrentar batalhas aleatórias em cada zona.

---

<p align="center"> 💾 Saves e Persistência </p>
O progresso do jogador é salvo em saves/, incluindo:

Status e nível atual

Inventário e equipamentos

Efeitos ativos e buffs

Localização no mapa

player.save("saves/slot_1.json")
player.load("saves/slot_1.json")

---

<p align="center"> 🚀 Instalação e Execução </p>

1️⃣ Clonar o repositório

    git clone https://github.com/TheTekig/EUCHORNIA.git
    cd EUCHORNIA
    
2️⃣ Criar ambiente virtual

    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows
    
3️⃣ Instalar dependências

    pip install -r requirements.txt
    
4️⃣ Executar o jogo

    python main.py

---

<p align="center"> 🧩 Roadmap (v0.2 → v1.0) </p>

     Versão	                Foco	                        Status
      0.2	   Sistema de buffs/debuffs empilháveis	  🧩 Em andamento
      0.3	   Sistema de saves e load dinâmico	      🔄 Planejado
      0.4	   HUD visual com rich.Live()	            🔜
      0.5	   IA narrativa com OpenAI API	          ⚙️ Em design
      0.6+	 Interface visual e expansão de mundo	  🌌 Futuro

---

<p align="center"> 🧙 Autor </p>

Diogo Teodoro Dias Lamas

🎮 Desenvolvedor & Criador do universo Euchronia
📦 GitHub: @TheTekig
💬 “A fronteira entre o código e o imaginário é o que dá vida a Euchronia.”

📜 Licença
Distribuído sob MIT License — sinta-se livre para modificar, estudar e expandir o projeto.

<p align="center"> 🌒 <i>“Cada bug conta uma história. Cada linha, uma nova era de Euchronia.”</i> 🌘 </p> 
