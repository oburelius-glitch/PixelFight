import pgzrun
import random
import math
import json
import os
import pygame
from pygame import Rect

# Matplotlib headless backend for 3D holographic ship previews without opening external windows
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Window Dimensions & Configuration
WIDTH = 1100
HEIGHT = 750
TITLE = "PixelFight: Galactic Rogue - Ultimate Edition"

# Game States (Oyun Durumları)
STATE_MENU = "menu"
STATE_GAME = "oyun"
STATE_PAUSE = "pause"
STATE_SHOP = "market"
STATE_GARAGE = "garaj"
STATE_LEADERBOARD = "skor_tablosu"
STATE_QUESTS = "gorevler"
STATE_STATS = "istatistikler"
STATE_SETTINGS = "ayarlar"
STATE_ACHIEVEMENTS = "basarimlar"
STATE_GAME_OVER = "oyun_bitti"

current_state = STATE_MENU
previous_state = STATE_MENU  # For pausing/returning

# Local Save File Path
SAVE_FILE = "save.json"

default_save = {
    "gold": 650,
    "high_score": 0,
    "max_distance": 0.0,
    "total_kills": 0,
    "boss_kills": 0,
    "total_shots": 0,
    "total_hits": 0,
    "total_damage": 0,
    "max_combo": 0,
    "max_level": 1,
    "play_time": 0,
    "active_ship": "Fighter",
    "owned_ships": ["Fighter"],
    "unlocked_paints": ["Cyan", "Kırmızı", "Mor", "Altın", "Neon Yeşil", "Void Black", "Solar Gold"],
    "ship_colors": {"Fighter": [0, 225, 255]},
    "upgrades": {
        "motor": 1,
        "weapon": 1,
        "armor": 1,
        "shield": 1
    },
    "skills": {
        "shield_boost": 0,
        "laser_power": 0,
        "speed_boost": 0,
        "critical_strike": 0,
        "rapid_fire": 0,
        "energy_recovery": 0
    },
    "inventory": ["Nano Repair Kit (x2)", "Energy Cell (x1)"],
    "jokers": ["Double Shot", "Magnet"],
    "achievements": [],
    "settings": {
        "effects": True,
        "anim_intensity": 2,
        "controls": "WASD / Ok Tuşları"
    }
}

game_data = default_save.copy()

def load_game():
    global game_data
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    game_data[k] = v
        except Exception as e:
            print(f"Kayıt yükleme hatası: {e}. Varsayılanlar kullanılıyor.")

def save_game():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=4)
    except Exception as e:
        print(f"Kayıt kaydetme hatası: {e}")

load_game()

player_pos = [WIDTH // 2, HEIGHT - 120]
player_speed = 6.0
player_hp = 150
player_max_hp = 150
player_shield = 60
player_max_shield = 60
player_energy = 100
player_max_energy = 100
current_weapon = "Basic Laser"

distance_score = 0.0
gold_collected_run = 0
enemies_killed_run = 0
shots_fired_run = 0
shots_hit_run = 0
combo = 0
combo_timer = 0

level = 1
xp = 0
xp_needed = 150

wave = 1
enemies_left_in_wave = 10
wave_active = False
wave_timer = 180

# Cooldowns & Timers
cooldown_timer = 0
dash_cooldown = 0
emp_cooldown = 0
nova_cooldown = 0

is_dashing = False
dash_duration = 0
dash_dir = [0, 0]

emp_active = False
emp_timer = 0

# Entity Lists
lasers = []
enemies = []
particles = []
floating_texts = []
powerups = []
stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)] for _ in range(90)]

current_sector = "Deep Space"
sector_timer = 0
active_event = None
event_timer = 0

# Matplotlib 3D Ship Preview Cache
cached_3d_surfaces = {}

def get_ship_3d_surface(ship_name, color_rgb):
    key = f"{ship_name}_{color_rgb[0]}_{color_rgb[1]}_{color_rgb[2]}"
    if key in cached_3d_surfaces:
        return cached_3d_surfaces[key]
    
    try:
        fig = plt.figure(figsize=(3, 3), dpi=80)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor('#080a16')
        fig.patch.set_facecolor('#080a16')
        
        norm_color = (color_rgb[0]/255, color_rgb[1]/255, color_rgb[2]/255)
        
        if ship_name == "Scout-X":
            xs = [0, -1, 1, 0]
            ys = [2, -1, -1, -2]
            zs = [0, 0, 0, 1]
            ax.scatter(xs, ys, zs, c=[norm_color], s=140)
        elif ship_name == "Titan":
            xs = [-1.8, 1.8, 1.8, -1.8, 0]
            ys = [1, 1, -1, -1, 2.5]
            zs = [-0.6, -0.6, 0.6, 0.6, 0]
            ax.plot(xs, ys, zs, color=norm_color, linewidth=3.5)
        elif ship_name == "Phantom":
            ax.plot([0, -1.2, 0, 1.2, 0], [2.2, -1, -1.5, -1, 2.2], [0, 0.5, 0.2, 0.5, 0], color=norm_color, linewidth=2.5)
        elif ship_name == "Nova":
            ax.plot([0, -1.5, 0, 1.5, 0], [2, -0.5, -2, -0.5, 2], [0, 0, 1.2, 0, 0], color=norm_color, linewidth=3)
        elif ship_name == "Void Reaper":
            ax.plot([0, -2, 0, 2, 0], [2.5, -1, -2.5, -1, 2.5], [1, -0.5, 1, -0.5, 1], color=norm_color, linewidth=3)
        else: # Fighter
            ax.plot([0, -1, 0, 1, 0], [2, -1, -2, -1, 2], [0, 0, 1, 0, 0], color=norm_color, linewidth=2.5)
            
        ax.axis('off')
        ax.view_init(elev=30, azim=45)
        
        fig.canvas.draw()
        raw_data = fig.canvas.buffer_rgba()
        pygame_image = pygame.image.frombuffer(raw_data, fig.canvas.get_width_height(), "RGBA")
        plt.close(fig)
        
        cached_3d_surfaces[key] = pygame_image
        return pygame_image
    except Exception as e:
        print(f"Matplotlib 3D render hatası: {e}")
        return None

ships_db = {
    "Scout-X": {"name": "Scout-X", "price": 0, "speed": 8.0, "hp": 110, "shield": 50, "desc": "Yüksek hız, düşük zırh."},
    "Fighter": {"name": "Fighter", "price": 0, "speed": 6.0, "hp": 150, "shield": 60, "desc": "Dengeli başlangıç gemisi."},
    "Titan": {"name": "Titan", "price": 1200, "speed": 4.0, "hp": 320, "shield": 160, "desc": "Ağır zırhlı uzay kalesi."},
    "Phantom": {"name": "Phantom", "price": 1800, "speed": 7.5, "hp": 130, "shield": 110, "desc": "Yüksek manevra kabiliyeti."},
    "Nova": {"name": "Nova", "price": 2600, "speed": 6.5, "hp": 190, "shield": 100, "desc": "Kritik vuruş odaklı."},
    "Void Reaper": {"name": "Void Reaper", "price": 4500, "speed": 7.2, "hp": 240, "shield": 200, "desc": "İleri teknoloji ölüm makinesi."}
}

weapons_db = {
    "Basic Laser": {"damage": 25, "rate": 10, "speed": 14, "color": (0, 255, 100)},
    "Rapid Laser": {"damage": 15, "rate": 5, "speed": 16, "color": (0, 225, 255)},
    "Plasma Laser": {"damage": 65, "rate": 22, "speed": 10, "color": (180, 0, 255)},
    "Rail Shot": {"damage": 90, "rate": 30, "speed": 22, "color": (255, 255, 0)}
}

def draw_pixel_ship(x, y, color, ship_name="Fighter"):
    screen.draw.filled_rect(Rect(x - 6, y - 22, 12, 38), color)
    screen.draw.filled_rect(Rect(x - 3, y - 30, 6, 10), (255, 255, 255))
    
    if ship_name == "Titan":
        screen.draw.filled_rect(Rect(x - 26, y - 4, 52, 14), color)
        screen.draw.filled_rect(Rect(x - 18, y + 10, 36, 8), (150, 150, 170))
    elif ship_name == "Scout-X":
        screen.draw.filled_rect(Rect(x - 16, y + 4, 12, 10), color)
        screen.draw.filled_rect(Rect(x + 4, y + 4, 12, 10), color)
    elif ship_name == "Phantom":
        screen.draw.filled_rect(Rect(x - 22, y, 14, 8), color)
        screen.draw.filled_rect(Rect(x + 8, y, 14, 8), color)
    elif ship_name == "Nova":
        screen.draw.filled_rect(Rect(x - 18, y - 6, 36, 10), (200, 50, 255))
    elif ship_name == "Void Reaper":
        screen.draw.filled_rect(Rect(x - 24, y - 8, 48, 12), (50, 50, 60))
        screen.draw.filled_rect(Rect(x - 12, y + 6, 24, 10), color)
    else:
        screen.draw.filled_rect(Rect(x - 20, y + 2, 14, 12), color)
        screen.draw.filled_rect(Rect(x + 6, y + 2, 14, 12), color)
        
    flame_height = random.choice([8, 14, 18]) if not is_dashing else 28
    screen.draw.filled_rect(Rect(x - 4, y + 16, 8, flame_height), (255, 120, 0))
    screen.draw.filled_rect(Rect(x - 2, y + 16, 4, flame_height // 2), (255, 255, 255))

def draw_pixel_enemy(enemy):
    x, y = enemy["pos"]
    etype = enemy["type"]
    color = enemy["color"]
    
    if etype == "Scout":
        screen.draw.filled_rect(Rect(x - 10, y - 10, 20, 20), color)
        screen.draw.filled_rect(Rect(x - 4, y - 14, 8, 4), (255, 255, 255))
    elif etype == "Tank":
        screen.draw.filled_rect(Rect(x - 20, y - 16, 40, 32), color)
        screen.draw.filled_rect(Rect(x - 12, y - 8, 24, 16), (90, 90, 110))
    elif etype == "Kamikaze":
        screen.draw.filled_rect(Rect(x - 12, y - 14, 24, 28), (255, 100, 0))
        screen.draw.filled_rect(Rect(x - 6, y - 6, 12, 12), (255, 255, 0))
    elif etype == "Shooter":
        screen.draw.filled_rect(Rect(x - 14, y - 12, 28, 24), color)
        screen.draw.filled_rect(Rect(x - 18, y - 2, 36, 6), (220, 50, 50))
    elif etype == "Elite":
        screen.draw.filled_rect(Rect(x - 18, y - 18, 36, 36), (180, 0, 255))
        screen.draw.filled_rect(Rect(x - 8, y - 8, 16, 16), (255, 255, 255))
    elif etype == "Boss":
        screen.draw.filled_rect(Rect(x - 50, y - 35, 100, 70), (140, 20, 40))
        screen.draw.filled_rect(Rect(x - 35, y - 20, 70, 40), (220, 50, 50))
        screen.draw.filled_rect(Rect(x - 12, y - 45, 24, 25), (255, 255, 0))
        hp_pct = max(0, enemy["hp"] / enemy["max_hp"])
        screen.draw.filled_rect(Rect(x - 55, y - 60, 110, 8), (50, 50, 50))
        screen.draw.filled_rect(Rect(x - 55, y - 60, int(110 * hp_pct), 8), (255, 0, 0))

def draw_pixel_laser(laser):
    x, y = laser["pos"]
    ltype = laser.get("type", "Basic Laser")
    cfg = weapons_db.get(ltype, weapons_db["Basic Laser"])
    col = cfg["color"]
    
    if ltype == "Plasma Laser":
        screen.draw.filled_rect(Rect(x - 5, y, 10, 20), col)
        screen.draw.filled_rect(Rect(x - 2, y + 3, 4, 14), (255, 220, 255))
    elif ltype == "Rail Shot":
        screen.draw.filled_rect(Rect(x - 1, y, 2, 26), col)
    else:
        screen.draw.filled_rect(Rect(x - 2, y, 4, 16), col)
        screen.draw.filled_rect(Rect(x - 4, y + 3, 8, 10), (220, 255, 220))

def create_explosion(x, y, color=(255, 150, 0), count=18):
    for _ in range(count):
        particles.append({
            "pos": [x, y],
            "vel": [random.uniform(-6, 6), random.uniform(-6, 6)],
            "color": color,
            "size": random.randint(3, 8),
            "life": random.randint(25, 45)
        })

def add_floating_text(text, x, y, color=(255, 255, 255)):
    floating_texts.append({
        "text": text,
        "pos": [x, y],
        "color": color,
        "life": 50
    })

def check_achievement(ach_id, title):
    if ach_id not in game_data["achievements"]:
        game_data["achievements"].append(ach_id)
        add_floating_text(f"🏆 Başarım Açıldı: {title}", WIDTH // 2 - 160, 130, (255, 215, 0))
        save_game()

def update():
    global current_state, distance_score, enemy_spawn_timer, cooldown_timer
    global player_hp, player_max_hp, player_shield, player_max_shield, player_energy
    global gold, enemies_left_in_wave, wave, wave_active, wave_timer
    global dash_cooldown, emp_cooldown, nova_cooldown, is_dashing, dash_duration, dash_dir
    global emp_active, emp_timer, combo, combo_timer, sector_timer, current_sector
    global active_event, event_timer, shots_fired_run, shots_hit_run

    for star in stars:
        star[1] += star[2] * (2 if active_event == "Energy Surge" else 1)
        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, WIDTH)

    for p in particles[:]:
        p["pos"][0] += p["vel"][0]
        p["pos"][1] += p["vel"][1]
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)

    for ft in floating_texts[:]:
        ft["pos"][1] -= 1
        ft["life"] -= 1
        if ft["life"] <= 0:
            floating_texts.remove(ft)

    if current_state != STATE_GAME:
        return

    game_data["play_time"] += 1/60
    sector_timer += 1
    if sector_timer > 1200:
        sectors = ["Deep Space", "Red Nebula", "Void Sector", "Alien Zone"]
        current_sector = random.choice(sectors)
        sector_timer = 0
        add_floating_text(f"Bölge: {current_sector}", WIDTH // 2 - 110, 85, (0, 225, 255))

    if active_event is None and random.random() < 0.0006:
        events = ["Gold Storm", "Space Anomaly", "Energy Surge", "Danger Zone"]
        active_event = random.choice(events)
        event_timer = 650
        add_floating_text(f"⚠️ OLAY: {active_event}!", WIDTH // 2 - 130, 105, (255, 50, 50))

    if active_event:
        event_timer -= 1
        if event_timer <= 0:
            active_event = None

    if combo_timer > 0:
        combo_timer -= 1
        if combo_timer <= 0:
            combo = 0

    distance_score += 0.3
    if distance_score > game_data["max_distance"]:
        game_data["max_distance"] = distance_score

    if dash_cooldown > 0: dash_cooldown -= 1
    if emp_cooldown > 0: emp_cooldown -= 1
    if nova_cooldown > 0: nova_cooldown -= 1

    if emp_active:
        emp_timer -= 1
        if emp_timer <= 0:
            emp_active = False

    if is_dashing:
        player_pos[0] += dash_dir[0] * 15
        player_pos[1] += dash_dir[1] * 15
        dash_duration -= 1
        if dash_duration <= 0:
            is_dashing = False

    speed_bonus = 1.6 if active_event == "Energy Surge" else 1.0
    active_ship_stats = ships_db[game_data["active_ship"]]
    current_speed = (active_ship_stats["speed"] + game_data["upgrades"]["motor"] * 0.8) * speed_bonus

    if not is_dashing:
        dx, dy = 0, 0
        if keyboard.left or keyboard.a: dx = -1
        if keyboard.right or keyboard.d: dx = 1
        if keyboard.up or keyboard.w: dy = -1
        if keyboard.down or keyboard.s: dy = 1
        
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        player_pos[0] += dx * current_speed
        player_pos[1] += dy * current_speed

        player_pos[0] = max(35, min(WIDTH - 35, player_pos[0]))
        player_pos[1] = max(35, min(HEIGHT - 35, player_pos[1]))

    if keyboard.q and emp_cooldown == 0:
        emp_active = True
        emp_timer = 180
        emp_cooldown = 320
        add_floating_text("⚡ EMP ALANI AKTİF!", player_pos[0], player_pos[1] - 35, (0, 255, 255))

    if keyboard.e and dash_cooldown == 0 and not is_dashing:
        is_dashing = True
        dash_duration = 10
        dash_cooldown = 130
        dx_val = (1 if keyboard.right or keyboard.d else (-1 if keyboard.left or keyboard.a else 0))
        dy_val = (1 if keyboard.down or keyboard.s else (-1 if keyboard.up or keyboard.w else -1))
        dash_dir = [dx_val, dy_val]

    if keyboard.r and nova_cooldown == 0:
        nova_cooldown = 480
        create_explosion(player_pos[0], player_pos[1], (0, 255, 255), 45)
        for enemy in enemies[:]:
            enemy["hp"] -= 120
            if enemy["hp"] <= 0:
                enemies.remove(enemy)
                game_data["gold"] += 20
                gain_xp(35)
        add_floating_text("💥 NOVA DALGASI!", player_pos[0], player_pos[1] - 45, (255, 215, 0))

    cooldown_timer += 1
    wcfg = weapons_db[current_weapon]
    fire_rate_limit = max(3, wcfg["rate"] - game_data["upgrades"]["weapon"])
    
    if keyboard.space and cooldown_timer >= fire_rate_limit:
        shots_fired_run += 1
        game_data["total_shots"] += 1
        if "Double Shot" in game_data["jokers"] or current_weapon == "Double Shot":
            lasers.append({"pos": [player_pos[0] - 12, player_pos[1] - 25], "type": current_weapon})
            lasers.append({"pos": [player_pos[0] + 12, player_pos[1] - 25], "type": current_weapon})
        else:
            lasers.append({"pos": [player_pos[0], player_pos[1] - 30], "type": current_weapon})
        cooldown_timer = 0

    for laser in lasers[:]:
        laser["pos"][1] -= wcfg["speed"]
        if laser["pos"][1] < 0:
            lasers.remove(laser)

    if not wave_active:
        wave_timer -= 1
        if wave_timer <= 0:
            wave_active = True
            enemies_left_in_wave = 10 + wave * 4
            add_floating_text(f"🚀 DALGA {wave} BAŞLADI!", WIDTH // 2 - 130, 160, (255, 255, 0))

    if wave_active and len(enemies) < 7 and enemies_left_in_wave > 0:
        if random.random() < 0.05:
            etype = random.choice(["Scout", "Tank", "Kamikaze", "Shooter", "Elite"])
            if wave % 5 == 0 and enemies_left_in_wave == 1:
                etype = "Boss"
            
            color_map = {"Scout": (230, 50, 50), "Tank": (50, 150, 230), "Kamikaze": (240, 220, 40), "Shooter": (190, 50, 230), "Elite": (255, 120, 0), "Boss": (255, 0, 0)}
            hp_map = {"Scout": 35, "Tank": 180, "Kamikaze": 45, "Shooter": 80, "Elite": 140, "Boss": 950}
            
            enemies.append({
                "pos": [random.randint(60, WIDTH - 60), -40],
                "type": etype,
                "color": color_map[etype],
                "hp": hp_map[etype],
                "max_hp": hp_map[etype],
                "speed": random.uniform(1.8, 3.8) if not emp_active else 0.6
            })
            enemies_left_in_wave -= 1

    for enemy in enemies[:]:
        speed_factor = 0.25 if emp_active else 1.0
        enemy["pos"][1] += enemy["speed"] * speed_factor
        
        if enemy["type"] == "Kamikaze":
            if enemy["pos"][0] < player_pos[0]: enemy["pos"][0] += 1.2
            elif enemy["pos"][0] > player_pos[0]: enemy["pos"][0] -= 1.2

        enemy_rect = Rect(enemy["pos"][0] - 18, enemy["pos"][1] - 18, 36, 36)

        for laser in lasers[:]:
            laser_rect = Rect(laser["pos"][0] - 4, laser["pos"][1], 8, 18)
            if enemy_rect.colliderect(laser_rect):
                shots_hit_run += 1
                game_data["total_hits"] += 1
                if laser in lasers: lasers.remove(laser)
                
                crit_mult = 1.5 if random.random() < (0.1 + game_data["skills"]["critical_strike"] * 0.05) else 1.0
                damage = int((wcfg["damage"] + game_data["upgrades"]["weapon"] * 8) * crit_mult)
                enemy["hp"] -= damage
                game_data["total_damage"] += damage
                
                create_explosion(laser["pos"][0], laser["pos"][1], (0, 255, 120), 4)
                
                if enemy["hp"] <= 0:
                    if enemy in enemies: enemies.remove(enemy)
                    gold_gain = 45 if enemy["type"] == "Boss" else (25 if enemy["type"] == "Elite" else 15)
                    if active_event == "Gold Storm": gold_gain *= 2
                    game_data["gold"] += gold_gain
                    global gold_collected_run
                    gold_collected_run += gold_gain
                    
                    gain_xp(60 if enemy["type"] == "Boss" else 25)
                    global enemies_killed_run
                    enemies_killed_run += 1
                    game_data["total_kills"] += 1
                    
                    if enemy["type"] == "Boss":
                        game_data["boss_kills"] += 1
                        check_achievement("boss_hunter", "Boss Avcısı")

                    combo += 1
                    combo_timer = 200
                    if combo > game_data["max_combo"]:
                        game_data["max_combo"] = combo

                    create_explosion(enemy["pos"][0], enemy["pos"][1], enemy["color"], 28)
                    add_floating_text(f"+{gold_gain} Altın", enemy["pos"][0], enemy["pos"][1], (255, 215, 0))
                    
                    if enemies_left_in_wave <= 0 and len(enemies) == 0:
                        wave_active = False
                        wave += 1
                        wave_timer = 160
                        add_floating_text(f"🏆 DALGA {wave-1} TAMAMLANDI!", WIDTH // 2 - 160, 190, (0, 255, 100))
                    break

        player_rect = Rect(player_pos[0] - 16, player_pos[1] - 16, 32, 32)
        if enemy_rect.colliderect(player_rect):
            if enemy in enemies: enemies.remove(enemy)
            damage = 35 if enemy["type"] == "Boss" else 22
            
            if player_shield > 0:
                player_shield -= damage
                if player_shield < 0:
                    player_hp += player_shield
                    player_shield = 0
            else:
                player_hp -= damage
                
            create_explosion(player_pos[0], player_pos[1], (255, 0, 0), 22)
            if player_hp <= 0:
                current_state = STATE_GAME_OVER
                if distance_score > game_data["high_score"]:
                    game_data["high_score"] = int(distance_score)
                save_game()

        elif enemy["pos"][1] > HEIGHT + 40:
            if enemy in enemies: enemies.remove(enemy)

def gain_xp(amount):
    global xp, level, xp_needed, player_hp, player_max_hp, player_shield, player_max_shield
    xp += amount
    if xp >= xp_needed:
        level += 1
        xp -= xp_needed
        xp_needed = int(xp_needed * 1.6)
        player_max_hp += 35
        player_hp = player_max_hp
        player_max_shield += 20
        player_shield = player_max_shield
        if level > game_data["max_level"]:
            game_data["max_level"] = level
        add_floating_text(f"⭐ SEVİYE ATLADIN! Lvl {level}", WIDTH // 2 - 130, 230, (0, 225, 255))
        check_achievement("novice_pilot", "Acemi Pilot")

def on_key_down(key):
    global current_state, previous_state, player_color, player_speed, player_max_hp, player_hp, current_weapon

    if key == keys.ESCAPE:
        if current_state == STATE_GAME:
            previous_state = STATE_GAME
            current_state = STATE_PAUSE
        elif current_state in [STATE_SHOP, STATE_GARAGE, STATE_LEADERBOARD, STATE_QUESTS, STATE_STATS, STATE_SETTINGS, STATE_ACHIEVEMENTS]:
            current_state = previous_state
        elif current_state == STATE_PAUSE:
            current_state = STATE_GAME

    if current_state == STATE_MENU:
        if key == keys.RETURN:
            reset_game()
            current_state = STATE_GAME
        elif key == keys.S:
            previous_state = STATE_MENU
            current_state = STATE_SHOP
        elif key == keys.G:
            previous_state = STATE_MENU
            current_state = STATE_GARAGE
        elif key == keys.L:
            previous_state = STATE_MENU
            current_state = STATE_LEADERBOARD
        elif key == keys.Q:
            previous_state = STATE_MENU
            current_state = STATE_QUESTS
        elif key == keys.A:
            previous_state = STATE_MENU
            current_state = STATE_ACHIEVEMENTS

    elif current_state == STATE_PAUSE:
        if key == keys.C:
            current_state = STATE_GAME
        elif key == keys.S:
            previous_state = STATE_PAUSE
            current_state = STATE_SHOP
        elif key == keys.G:
            previous_state = STATE_PAUSE
            current_state = STATE_GARAGE
        elif key == keys.L:
            previous_state = STATE_PAUSE
            current_state = STATE_LEADERBOARD
        elif key == keys.T:
            previous_state = STATE_PAUSE
            current_state = STATE_STATS
        elif key == keys.X:
            current_state = STATE_MENU

    elif current_state == STATE_GAME_OVER:
        if key == keys.RETURN:
            current_state = STATE_MENU

    elif current_state == STATE_SHOP:
        if key == keys.K_1: buy_ship("Titan")
        elif key == keys.K_2: buy_ship("Phantom")
        elif key == keys.K_3: buy_ship("Nova")
        elif key == keys.K_4: buy_ship("Void Reaper")

    elif current_state == STATE_GARAGE:
        if key == keys.K_1: upgrade_garage("motor")
        elif key == keys.K_2: upgrade_garage("weapon")
        elif key == keys.K_3: upgrade_garage("armor")
        elif key == keys.K_4: upgrade_garage("shield")

def reset_game():
    global current_state, distance_score, player_hp, player_max_hp, player_shield, player_max_shield
    global lasers, enemies, player_pos, wave, enemies_left_in_wave, wave_active
    distance_score = 0.0
    active_ship = game_data["active_ship"]
    sinfo = ships_db.get(active_ship, ships_db["Fighter"])
    player_max_hp = sinfo["hp"] + game_data["upgrades"]["armor"] * 35
    player_hp = player_max_hp
    player_max_shield = sinfo["shield"] + game_data["upgrades"]["shield"] * 30
    player_shield = player_max_shield
    player_pos = [WIDTH // 2, HEIGHT - 120]
    lasers.clear()
    enemies.clear()
    wave = 1
    enemies_left_in_wave = 12
    wave_active = True

def buy_ship(ship_key):
    ship = ships_db[ship_key]
    if ship_key not in game_data["owned_ships"] and game_data["gold"] >= ship["price"]:
        game_data["gold"] -= ship["price"]
        game_data["owned_ships"].append(ship_key)
        game_data["active_ship"] = ship_key
        check_achievement("collector", "Koleksiyoncu")
        save_game()
        add_floating_text(f"{ship['name']} Satın Alındı!", WIDTH // 2 - 130, 110, (255, 215, 0))
    elif ship_key in game_data["owned_ships"]:
        game_data["active_ship"] = ship_key
        save_game()
        add_floating_text(f"{ship['name']} Kuşanıldı!", WIDTH // 2 - 110, 110, (0, 255, 255))

def upgrade_garage(cat):
    costs = {"motor": 180, "weapon": 220, "armor": 200, "shield": 190}
    cost = costs[cat] * game_data["upgrades"][cat]
    if game_data["gold"] >= cost:
        game_data["gold"] -= cost
        game_data["upgrades"][cat] += 1
        save_game()
        add_floating_text(f"{cat.capitalize()} Geliştirildi!", WIDTH // 2 - 110, 110, (0, 255, 100))

def draw():
    screen.clear()
    screen.fill((6, 8, 20))

    for star in stars:
        screen.draw.filled_rect(Rect(star[0], star[1], star[2], star[2]), (190, 190, 230))

    if current_state == STATE_MENU:
        draw_menu()
    elif current_state == STATE_GAME:
        draw_game()
    elif current_state == STATE_PAUSE:
        draw_pause()
    elif current_state == STATE_SHOP:
        draw_shop()
    elif current_state == STATE_GARAGE:
        draw_garage()
    elif current_state == STATE_LEADERBOARD:
        draw_leaderboard()
    elif current_state == STATE_QUESTS:
        draw_quests()
    elif current_state == STATE_STATS:
        draw_stats()
    elif current_state == STATE_ACHIEVEMENTS:
        draw_achievements()
    elif current_state == STATE_GAME_OVER:
        draw_game_over()

def draw_menu():
    screen.draw.text("PIXELFIGHT: GALACTIC ROGUE", center=(WIDTH // 2, 140), fontsize=52, color="cyan", shadow=(1,1))
    screen.draw.text("Ultimate Code-Driven Space RPG", center=(WIDTH // 2, 195), fontsize=26, color="gold")

    box_w, box_h = 420, 52
    center_x = WIDTH // 2
    
    options = [
        ("[ENTER] Oyuna Başla", 270),
        ("[S] Uzay Gemileri & Market", 340),
        ("[G] Garaj & Geliştirmeler", 410),
        ("[L] Skor Tablosu", 480),
        ("[Q] Görevler", 550),
        ("[A] Başarımlar", 620)
    ]
    
    for text, y in options:
        screen.draw.filled_rect(Rect(center_x - box_w // 2, y, box_w, box_h), (22, 28, 52))
        screen.draw.rect(Rect(center_x - box_w // 2, y, box_w, box_h), (0, 225, 255))
        screen.draw.text(text, center=(center_x, y + box_h // 2), fontsize=24, color="white")

def draw_game():
    for laser in lasers:
        draw_pixel_laser(laser)
    for enemy in enemies:
        draw_pixel_enemy(enemy)

    active_ship = game_data["active_ship"]
    rgb = game_data["ship_colors"].get(active_ship, [0, 225, 255])
    draw_pixel_ship(player_pos[0], player_pos[1], rgb, active_ship)

    for p in particles:
        screen.draw.filled_rect(Rect(p["pos"][0], p["pos"][1], p["size"], p["size"]), p["color"])

    for ft in floating_texts:
        screen.draw.text(ft["text"], (ft["pos"][0], ft["pos"][1]), fontsize=22, color=ft["color"])

    screen.draw.filled_rect(Rect(0, 0, WIDTH, 70), (10, 14, 30))
    screen.draw.text(f"MESAFE: {int(distance_score)}m", (20, 16), fontsize=22, color="yellow")
    screen.draw.text(f"ALTIN: {game_data['gold']}", (220, 16), fontsize=22, color="gold")
    screen.draw.text(f"DALGA: {wave}", (380, 16), fontsize=22, color="cyan")
    screen.draw.text(f"SKOR: {game_data['high_score']}", (520, 16), fontsize=22, color="white")
    screen.draw.text(f"BÖLGE: {current_sector}", (720, 16), fontsize=20, color="magenta")

    screen.draw.text(f"CAN: {int(player_hp)}/{player_max_hp}", (20, 45), fontsize=18, color="lime")
    screen.draw.filled_rect(Rect(90, 47, 130, 12), (50, 50, 50))
    screen.draw.filled_rect(Rect(90, 47, int(130 * max(0, player_hp / player_max_hp)), 12), (0, 255, 0))

    screen.draw.text(f"KALKAN: {int(player_shield)}", (240, 45), fontsize=18, color="cyan")
    screen.draw.filled_rect(Rect(325, 47, 110, 12), (50, 50, 50))
    screen.draw.filled_rect(Rect(325, 47, int(110 * max(0, player_shield / player_max_shield)), 12), (0, 180, 255))

    if combo > 1:
        screen.draw.text(f"COMBO x{combo}!", (WIDTH - 190, 42), fontsize=26, color="orange")

    screen.draw.text("[ESC] Pause  |  [Q] EMP  |  [E] Dash  |  [R] Nova", (WIDTH - 440, HEIGHT - 30), fontsize=18, color="gray")

def draw_pause():
    panel_w, panel_h = 560, 500
    px = (WIDTH - panel_w) // 2
    py = (HEIGHT - panel_h) // 2
    
    screen.draw.filled_rect(Rect(px, py, panel_w, panel_h), (12, 16, 32))
    screen.draw.rect(Rect(px, py, panel_w, panel_h), (0, 225, 255))
    
    screen.draw.text("OYUN DURAKLATILDI", center=(WIDTH // 2, py + 40), fontsize=34, color="yellow")
    
    buttons = [
        ("[C] Oyuna Devam Et", py + 95),
        ("[S] Market", py + 145),
        ("[G] Garaj", py + 195),
        ("[L] Skor Tablosu", py + 245),
        ("[T] İstatistikler", py + 295),
        ("[X] Ana Menüye Dön", py + 345)
    ]
    
    for text, y in buttons:
        screen.draw.filled_rect(Rect(px + 60, y, panel_w - 120, 42), (22, 32, 58))
        screen.draw.text(text, center=(WIDTH // 2, y + 21), fontsize=20, color="white")

def draw_shop():
    screen.draw.text("--- UZAY GEMİSİ VE MARKET ---", center=(WIDTH // 2, 60), fontsize=34, color="yellow")
    screen.draw.text(f"Mevcut Altın: {game_data['gold']}", center=(WIDTH // 2, 105), fontsize=24, color="gold")

    y = 150
    i = 1
    for skey, ship in ships_db.items():
        if skey in ["Scout-X", "Fighter"]:
            continue
        owned = skey in game_data["owned_ships"]
        active = game_data["active_ship"] == skey
        
        status = "KUŞANILDI" if active else ("SAHİP OLUNDU" if owned else f"Fiyat: {ship['price']} Altın")
        
        screen.draw.filled_rect(Rect(100, y, WIDTH - 200, 80), (18, 24, 45))
        screen.draw.rect(Rect(100, y, WIDTH - 200, 80), (0, 225, 255) if active else (100, 100, 100))
        
        screen.draw.text(f"{i}. {ship['name']} - {status}", (125, y + 12), fontsize=22, color="white")
        screen.draw.text(ship["desc"] + f" (Hız: {ship['speed']} | Can: {ship['hp']})", (125, y + 44), fontsize=16, color="gray")
        
        surf = get_ship_3d_surface(ship["name"], game_data["ship_colors"].get(skey, [0, 225, 255]))
        if surf:
            screen.blit(surf, (WIDTH - 260, y + 5))

        y += 95
        i += 1

    screen.draw.text("Satın almak / seçmek için [1], [2], [3], [4] tuşlarına bas. Geri için [ESC].", center=(WIDTH // 2, HEIGHT - 45), fontsize=18, color="red")

def draw_garage():
    screen.draw.text("--- GARAJ & GELİŞTİRME MERKEZİ ---", center=(WIDTH // 2, 60), fontsize=34, color="cyan")
    screen.draw.text(f"Mevcut Altın: {game_data['gold']}", center=(WIDTH // 2, 105), fontsize=24, color="gold")

    upgrades = game_data["upgrades"]
    costs = {"motor": 180 * upgrades["motor"], "weapon": 220 * upgrades["weapon"], "armor": 200 * upgrades["armor"], "shield": 190 * upgrades["shield"]}
    
    items = [
        (f"[1] Motor Seviyesi: {upgrades['motor']} (Maliyet: {costs['motor']} Altın)", 180),
        (f"[2] Silah Seviyesi: {upgrades['weapon']} (Maliyet: {costs['weapon']} Altın)", 260),
        (f"[3] Zırh Seviyesi: {upgrades['armor']} (Maliyet: {costs['armor']} Altın)", 340),
        (f"[4] Kalkan Seviyesi: {upgrades['shield']} (Maliyet: {costs['shield']} Altın)", 420)
    ]
    
    for text, y in items:
        screen.draw.filled_rect(Rect(150, y, WIDTH - 300, 65), (20, 30, 52))
        screen.draw.text(text, (180, y + 20), fontsize=22, color="white")

    screen.draw.text("Yükseltmek için [1], [2], [3], [4] tuşlarına bas. Geri için [ESC].", center=(WIDTH // 2, HEIGHT - 55), fontsize=18, color="red")

def draw_leaderboard():
    screen.draw.text("--- YEREL SKOR TABLOSU ---", center=(WIDTH // 2, 85), fontsize=34, color="yellow")
    screen.draw.text(f"En Yüksek Skor: {game_data['high_score']}", center=(WIDTH // 2, 150), fontsize=26, color="lime")
    screen.draw.text(f"En Uzun Mesafe: {int(game_data['max_distance'])} Metre", center=(WIDTH // 2, 200), fontsize=22, color="cyan")
    screen.draw.text(f"Toplam Düşman İmha: {game_data['total_kills']}", center=(WIDTH // 2, 250), fontsize=22, color="white")

    screen.draw.text("Geri dönmek için [ESC] tuşuna bas.", center=(WIDTH // 2, HEIGHT - 90), fontsize=18, color="red")

def draw_quests():
    screen.draw.text("--- AKTİF GÖREVLER ---", center=(WIDTH // 2, 85), fontsize=34, color="cyan")
    
    quests = [
        ("İlk Kan: 1 Düşman Yok Et", game_data["total_kills"] >= 1),
        ("Acemi Pilot: Seviye 2'ye Ulaş", game_data["max_level"] >= 2),
        ("Boss Avcısı: 1 Boss Yok Et", game_data["boss_kills"] >= 1),
        ("Koleksiyoncu: 2 Gemi Aç", len(game_data["owned_ships"]) >= 2)
    ]
    
    y = 170
    for title, completed in quests:
        status = "TAMAMLANDI ✅" if completed else "DEVAM EDİYOR ⏳"
        color = "lime" if completed else "gray"
        screen.draw.text(f"- {title} [{status}]", (150, y), fontsize=22, color=color)
        y += 55

    screen.draw.text("Geri dönmek için [ESC] tuşuna bas.", center=(WIDTH // 2, HEIGHT - 90), fontsize=18, color="red")

def draw_stats():
    screen.draw.text("--- OYUN İSTATİSTİKLERİ ---", center=(WIDTH // 2, 85), fontsize=34, color="gold")
    
    stats = [
        f"Toplam Oynanan Süre: {int(game_data['play_time'])} saniye",
        f"Toplam Atış: {game_data['total_shots']}",
        f"İsabet Sayısı: {game_data['total_hits']}",
        f"Boss Öldürme Sayısı: {game_data['boss_kills']}",
        f"En Yüksek Combo: x{game_data['max_combo']}",
        f"En Yüksek Seviye: Lvl {game_data['max_level']}"
    ]
    
    y = 170
    for stat in stats:
        screen.draw.text(stat, (200, y), fontsize=20, color="white")
        y += 45

    screen.draw.text("Geri dönmek için [ESC] tuşuna bas.", center=(WIDTH // 2, HEIGHT - 90), fontsize=18, color="red")

def draw_achievements():
    screen.draw.text("--- BAŞARIMLAR ---", center=(WIDTH // 2, 85), fontsize=34, color="magenta")
    
    achs = [
        ("first_blood", "İlk Kan - İlk düşmanını yok et"),
        ("novice_pilot", "Acemi Pilot - Seviye atla"),
        ("collector", "Koleksiyoncu - Yeni bir gemi satın al"),
        ("boss_hunter", "Boss Avcısı - Bir uzay boss'unu alt et")
    ]
    
    y = 170
    for aid, desc in achs:
        unlocked = aid in game_data["achievements"]
        status = "AÇILDI 🏆" if unlocked else "KİLİTLİ 🔒"
        color = "gold" if unlocked else "gray"
        screen.draw.text(f"- {desc} [{status}]", (150, y), fontsize=20, color=color)
        y += 55

    screen.draw.text("Geri dönmek için [ESC] tuşuna bas.", center=(WIDTH // 2, HEIGHT - 90), fontsize=18, color="red")

def draw_game_over():
    screen.draw.text("OYUN BİTTİ", center=(WIDTH // 2, HEIGHT // 2 - 90), fontsize=58, color="red")
    screen.draw.text(f"Mesafe Skoru: {int(distance_score)} Metre", center=(WIDTH // 2, HEIGHT // 2 - 15), fontsize=26, color="white")
    screen.draw.text(f"Toplanan Altın: {gold_collected_run}", center=(WIDTH // 2, HEIGHT // 2 + 30), fontsize=24, color="gold")
    screen.draw.text("Ana Menüye Dönmek İçin [ENTER]'a bas", center=(WIDTH // 2, HEIGHT // 2 + 110), fontsize=20, color="yellow")

pgzrun.go()