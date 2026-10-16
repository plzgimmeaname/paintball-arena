import pygame, sys
from random import randrange

# init and basics
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("paintball arena")
clock = pygame.time.Clock()
normal_font = pygame.font.SysFont(None, 36)
title_font = pygame.font.SysFont(None, 64)

# color defs
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 50, 50)
blue = (50, 50, 255)
green = (34, 139, 34)
gray = (150, 150, 150)
dark_gray = (80, 80, 80)
yellow = (255, 255, 0)
orange = (255, 165, 0)

gravity = 0.7

# map and weapon data structures
arenas = {
    1: {
        "name": "flat arena", 
        "background_color": white, 
        "obstacles": [
            pygame.Rect(0, screen_height - 40, screen_width, 40), 
            pygame.Rect(200, screen_height - 150, 400, 20)
        ]
    },
    2: {
        "name": "the steppes", 
        "background_color": (84, 189, 84), 
        "obstacles": [
            pygame.Rect(0, screen_height - 40, screen_width, 40), 
            pygame.Rect(100, screen_height - 200, 150, 20), 
            pygame.Rect(550, screen_height - 200, 150, 20), 
            pygame.Rect(300, screen_height - 350, 200, 20)
        ]
    },
    3: {
        "name": "city ruins", 
        "background_color": (200, 200, 200), 
        "obstacles": [
            pygame.Rect(0, screen_height - 40, 250, 40), 
            pygame.Rect(550, screen_height - 40, 250, 40), 
            pygame.Rect(350, screen_height - 120, 100, 20), 
            pygame.Rect(150, screen_height - 250, 150, 20), 
            pygame.Rect(500, screen_height - 250, 150, 20), 
            pygame.Rect(350, screen_height - 400, 100, 20)
        ]
    }
}

toys = [
    {"name": "paintball", "fire_rate": 15, "damage": 20, "speed": 20, "spread": 0, "pellets": 1, "arcs": False, "bounces": 0},
    {"name": "ball", "fire_rate": 45, "damage": 40, "speed": 15, "spread": 3.4, "pellets": 3, "arcs": False, "bounces": 1},
    {"name": "hose", "fire_rate": 6, "damage": 6, "speed": 18, "spread": 1, "pellets": 1, "arcs": False, "bounces": 0},
    {"name": "BB", "fire_rate": 45, "damage": 50, "speed": 50, "spread": 0, "pellets": 1, "arcs": False, "bounces": 0},
    {"name": "pancake", "fire_rate": 40, "damage": 100, "speed": 10, "spread": 0, "pellets": 1, "arcs": True, "bounces": 3},
    {"name": "laser", "fire_rate": 1, "damage": 1, "speed": 40, "spread": 0, "pellets": 1, "arcs": False, "bounces": 0},
    {"name": "frisbee", "fire_rate": 45, "damage": 40, "speed": 15, "spread": 3.4, "pellets": 1, "arcs": False, "bounces": 1}
]

def draw_text(text_string, font, text_color, surface, center_x, center_y):
    text_surface = font.render(text_string, 1, text_color)
    text_rect = text_surface.get_rect(center=(center_x, center_y))
    surface.blit(text_surface, text_rect)

def draw_button(surface, button_rect, text_string, is_hovered, base_color=gray):
    if is_hovered:
        button_color = tuple(min(255, color_channel + 40) for color_channel in base_color)
    else:
        button_color = base_color
        
    pygame.draw.rect(surface, button_color, button_rect)
    pygame.draw.rect(surface, black, button_rect, 2)
    
    font_size = 24
        
    button_font = pygame.font.SysFont(None, font_size)
    draw_text(text_string, button_font, black, surface, button_rect.centerx, button_rect.centery)

projectiles = []

class Player:
    player_list = []
    current_map = None
    
    def __init__(self, player_id, start_x, start_y, color, controls, weapon_id):
        self.player_id = player_id
        self.rect = pygame.Rect(start_x, start_y, 30, 30)
        self.color = color
        self.controls = controls
        self.weapon = toys[weapon_id]
        self.velocity_x = 0
        self.velocity_y = 0
        
        if player_id == 1:
            self.direction = 1
        else:
            self.direction = -1
            
        self.is_on_ground = False
        self.paint_level = 0
        self.cooldown = 0
        
        Player.player_list.append(self)
        
    @classmethod
    def setup(cls, map_id, weapon1_id, weapon2_id):
        cls.player_list.clear()
        projectiles.clear()
        cls.current_map = arenas[map_id]
        
        controls_p1 = [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s]
        Player(1, 50, screen_height // 2 - 200, red, controls_p1, weapon1_id)
        
        controls_p2 = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]
        Player(2, screen_width - 80, screen_height // 2 - 200, blue, controls_p2, weapon2_id)

    def jump(self):
        # vertical jump logic
        if self.is_on_ground:
            self.velocity_y = -17
            self.is_on_ground = False

    def pewpew(self):
        # projectile firing logic
        if self.cooldown == 0:
            for i in range(self.weapon["pellets"]):
                if self.weapon["spread"]:
                    if self.weapon["pellets"] > 1:
                        spread_offset = -self.weapon["spread"] + (2 * self.weapon["spread"] * i / (self.weapon["pellets"] - 1))
                    else:
                        spread_offset = (pygame.time.get_ticks() % (int(self.weapon["spread"]) * 2 + 1)) - self.weapon["spread"]
                else:
                    spread_offset = 0
                    
                if self.weapon["arcs"]:
                    projectile_velocity_y = -5 + spread_offset
                else:
                    projectile_velocity_y = spread_offset
                    
                start_x = self.rect.centerx + 20 * self.direction
                start_y = self.rect.centery
                velocity_x = self.weapon["speed"] * self.direction
                
                projectile_data = [
                    start_x, 
                    start_y, 
                    velocity_x, 
                    projectile_velocity_y, 
                    self.color, 
                    self.player_id, 
                    self.weapon["arcs"], 
                    self.weapon["damage"],
                    self.weapon.get("bounces", 0)
                ]
                projectiles.append(projectile_data)
                
            self.cooldown = self.weapon["fire_rate"]

    def check_death(self):
        # handle excessive paint
        if self.paint_level >= 100 or self.rect.top > screen_height:
            self.paint_level = 100

    def update(self, keys):
        # input polling and physics sequence
        if keys[self.controls[0]]:
            self.velocity_x = -6
            self.direction = -1
        elif keys[self.controls[1]]:
            self.velocity_x = 6
            self.direction = 1
        else:
            self.velocity_x = 0
        
        # horizontal
        self.rect.x += self.velocity_x
        for obstacle in self.current_map["obstacles"]:
            if self.rect.colliderect(obstacle):
                if self.velocity_x > 0:
                    self.rect.right = obstacle.left
                if self.velocity_x < 0:
                    self.rect.left = obstacle.right
                
        # jumping
        if keys[self.controls[2]]:
            self.jump()
        
        # gravity
        self.velocity_y = min(12, self.velocity_y + gravity)
        self.rect.y += self.velocity_y
        self.is_on_ground = False
        
        # vertical
        for obstacle in self.current_map["obstacles"]:
            if self.rect.colliderect(obstacle):
                if self.velocity_y > 0 and self.rect.bottom > obstacle.top and self.rect.top < obstacle.top:
                    self.rect.bottom = obstacle.top
                    self.velocity_y = 0
                    self.is_on_ground = True
                elif self.velocity_y < 0 and self.rect.top < obstacle.bottom:
                    self.rect.top = obstacle.bottom
                    self.velocity_y = 0
                    
        # bounds logic
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width
        
        # combat logic
        if keys[self.controls[3]]:
            self.pewpew()
            
        if self.cooldown > 0:
            self.cooldown -= 1
            
        self.check_death()

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, black, self.rect, 2)
        
        if self.direction == 1:
            eye_x = self.rect.right - 10
        else:
            eye_x = self.rect.left + 5
            
        pygame.draw.rect(screen, white, (eye_x, self.rect.y + 10, 5, 5))

    @classmethod
    def run(cls):
        # main menu sequence
        selected_map_id = 1
        player1_weapon_id = 0
        player2_weapon_id = 0
        player1_score = 0
        player2_score = 0
        speed_idx = 0
        speeds = [0, 8, 4, 2, 1]
        
        while True:
            screen.fill(white)
            draw_text("paintball arena", title_font, black, screen, screen_width // 2, 80)
            
            score_text = f"match score: p1 ({player1_score}) p2 ({player2_score})"
            draw_text(score_text, normal_font, black, screen, screen_width // 2, 130)
            
            mouse_position = pygame.mouse.get_pos()
            mouse_clicked = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
                
            current_y = 200
            draw_text("map:", normal_font, black, screen, screen_width // 2, current_y - 20)
            
            for index, (map_id, map_data) in enumerate(arenas.items()):
                button_rect = pygame.Rect(120 + index * 200, current_y, 160, 40)
                is_hovered = button_rect.collidepoint(mouse_position)
                
                if selected_map_id == map_id:
                    button_color = orange
                else:
                    button_color = gray
                    
                draw_button(screen, button_rect, map_data["name"], is_hovered, button_color)
                
                if is_hovered and mouse_clicked:
                    selected_map_id = map_id
                
            current_y += 100
            draw_text("p1 weapon (wasd):", normal_font, red, screen, screen_width // 2, current_y - 20)
            
            for index, weapon in enumerate(toys):
                button_rect = pygame.Rect(15 + index * 110, current_y, 100, 40)
                is_hovered = button_rect.collidepoint(mouse_position)
                
                if player1_weapon_id == index:
                    button_color = red
                else:
                    button_color = gray
                    
                draw_button(screen, button_rect, weapon["name"], is_hovered, button_color)
                
                if is_hovered and mouse_clicked:
                    player1_weapon_id = index
                
            current_y += 100
            draw_text("p2 weapon (arws):", normal_font, blue, screen, screen_width // 2, current_y - 20)
            
            for index, weapon in enumerate(toys):
                button_rect = pygame.Rect(15 + index * 110, current_y, 100, 40)
                is_hovered = button_rect.collidepoint(mouse_position)
                
                if player2_weapon_id == index:
                    button_color = blue
                else:
                    button_color = gray
                    
                draw_button(screen, button_rect, weapon["name"], is_hovered, button_color)
                
                if is_hovered and mouse_clicked:
                    player2_weapon_id = index
                
            play_button_rect = pygame.Rect(screen_width // 2 - 100, current_y + 80, 200, 50)
            is_hovered = play_button_rect.collidepoint(mouse_position)
            draw_button(screen, play_button_rect, "fight!", is_hovered, green)
            
            speed_text = f"speed level: {speed_idx + 1}"
            draw_text(speed_text, normal_font, black, screen, screen_width // 2, 550)
            
            slow_rect = pygame.Rect(screen_width // 2 - 180, 535, 80, 30)
            fast_rect = pygame.Rect(screen_width // 2 + 100, 535, 80, 30)
            is_hovered_slow = slow_rect.collidepoint(mouse_position)
            is_hovered_fast = fast_rect.collidepoint(mouse_position)
            
            draw_button(screen, slow_rect, "Slower", is_hovered_slow, red)
            draw_button(screen, fast_rect, "Faster", is_hovered_fast, green)
            
            if is_hovered_slow and mouse_clicked:
                speed_idx = max(0, speed_idx - 1)
            if is_hovered_fast and mouse_clicked:
                speed_idx = min(len(speeds) - 1, speed_idx + 1)
            
            if is_hovered and mouse_clicked:
                cls.setup(selected_map_id, player1_weapon_id, player2_weapon_id)
                match_result = cls.game_loop(speeds[speed_idx], speed_idx + 1)
                
                if match_result == 1:
                    player1_score += 1
                if match_result == 2:
                    player2_score += 1
                
            pygame.display.flip()
            clock.tick(60)

    @classmethod
    def game_loop(cls, tick_speed, speed_level):
        # primary game sequence
        is_running = True
        winner_id = 0
        
        while is_running:
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                
            screen.fill(cls.current_map["background_color"])
            
            for obstacle in cls.current_map["obstacles"]:
                pygame.draw.rect(screen, dark_gray, obstacle)
                pygame.draw.rect(screen, black, obstacle, 2)
                
            for player in cls.player_list:
                #lower tick_speed = faster sim speed
                player.update(keys)
                try:
                    if pygame.time.get_ticks() % tick_speed == 0: 
                        player.update(keys)
                except:
                    pass
                player.draw()
                
            # proj collision selection logic
            for i in range(len(projectiles) - 1, -1, -1):
                projectile = projectiles[i]
                
                if projectile[6]:
                    projectile[3] += gravity / 2
                    
                projectile[0] += projectile[2]
                projectile[1] += projectile[3]
                
                projectile_rect = pygame.Rect(projectile[0] - 5, projectile[1] - 5, 10, 10)
                
                hit_obstacle_or_bounds = False
                hit_solid = None
                for obstacle in cls.current_map["obstacles"]:
                    if projectile_rect.colliderect(obstacle):
                        hit_obstacle_or_bounds = True
                        hit_solid = obstacle
                        break
                        
                if projectile[0] < 0 or projectile[0] > screen_width or projectile[1] > screen_height:
                    hit_obstacle_or_bounds = True
                    hit_solid = "bounds"
                    
                has_hit = hit_obstacle_or_bounds
                
                hit_player = False
                for player in cls.player_list:
                    if projectile[5] != player.player_id and projectile_rect.colliderect(player.rect):
                        player.paint_level += projectile[7]
                        has_hit = True
                        hit_player = True
                        
                if has_hit:
                    if not hit_player and hit_solid and len(projectile) > 8 and projectile[8] > 0:
                        projectile[8] -= 1
                        
                        if hit_solid == "bounds":
                            if projectile[0] < 0:
                                projectile[2] *= -0.7
                                projectile[0] = 0
                            elif projectile[0] > screen_width:
                                projectile[2] *= -0.7
                                projectile[0] = screen_width
                            if projectile[1] > screen_height:
                                projectile[3] *= -0.7
                                projectile[1] = screen_height
                        else:
                            prev_rect = pygame.Rect(projectile[0] - projectile[2] - 5, projectile[1] - projectile[3] - 5, 10, 10)
                            if prev_rect.bottom <= hit_solid.top:
                                projectile[3] *= -0.7
                                projectile[1] = hit_solid.top - 5
                            elif prev_rect.top >= hit_solid.bottom:
                                projectile[3] *= -0.7
                                projectile[1] = hit_solid.bottom + 5
                            elif prev_rect.right <= hit_solid.left:
                                projectile[2] *= -0.7
                                projectile[0] = hit_solid.left - 5
                            elif prev_rect.left >= hit_solid.right:
                                projectile[2] *= -0.7
                                projectile[0] = hit_solid.right + 5
                            else:
                                projectile[3] *= -0.7
                                projectile[1] -= projectile[3]
                                
                        x_pos = int(projectile[0])
                        y_pos = int(projectile[1])
                        pygame.draw.circle(screen, projectile[4], (x_pos, y_pos), 6)
                        pygame.draw.circle(screen, black, (x_pos, y_pos), 6, 1)
                    else:
                        projectiles.pop(i)
                else:
                    x_pos = int(projectile[0])
                    y_pos = int(projectile[1])
                    pygame.draw.circle(screen, projectile[4], (x_pos, y_pos), 6)
                    pygame.draw.circle(screen, black, (x_pos, y_pos), 6, 1)

            player1 = cls.player_list[0]
            player2 = cls.player_list[1]
            
            pygame.draw.rect(screen, black, (10, 10, 304, 24), 2)
            player1_paint_percentage = min(player1.paint_level, 100)
            player1_bar_width = max(0, 300 - player1_paint_percentage * 3)
            pygame.draw.rect(screen, red, (12, 12, player1_bar_width, 20))
            draw_text(f"p1 paint: {int(player1_paint_percentage)}%", normal_font, black, screen, 160, 40)
            
            pygame.draw.rect(screen, black, (screen_width - 314, 10, 304, 24), 2)
            player2_paint_percentage = min(player2.paint_level, 100)
            player2_bar_start_x = screen_width - 312 + player2_paint_percentage * 3
            player2_bar_width = max(0, 300 - player2_paint_percentage * 3)
            pygame.draw.rect(screen, blue, (player2_bar_start_x, 12, player2_bar_width, 20))
            draw_text(f"p2 paint: {int(player2_paint_percentage)}%", normal_font, black, screen, screen_width - 160, 40)
            
            draw_text(f"speed: {speed_level}", normal_font, black, screen, screen_width // 2, 30)

            # win logic selection
            if player1.paint_level >= 100 and player2.paint_level >= 100:
                winner_id = 3
                is_running = False
            elif player1.paint_level >= 100:
                winner_id = 2
                is_running = False
            elif player2.paint_level >= 100:
                winner_id = 1
                is_running = False

            pygame.display.flip()
            clock.tick(60)

        if winner_id == 3:
            winner_text = "draw!"
        else:
            winner_text = f"player {winner_id} wins!"
            
        for offset_x, offset_y in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            draw_text(winner_text, title_font, white, screen, screen_width // 2 + offset_x, screen_height // 2 + offset_y)
            
        draw_text(winner_text, title_font, black, screen, screen_width // 2, screen_height // 2)
        
        pygame.display.flip()
        pygame.time.delay(3000)
        
        return winner_id

if __name__ == "__main__":
    Player.run()
    pygame.quit()

#               λ__λ
#   (meow)    =(^u ^)=
#               (,, ,\∫


