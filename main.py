import asyncio
import pygame as pg
import sys
import math
from screeninfo import get_monitors
import random

class Player:
    def __init__(self, game, sprite_path, scale_factor=0.5):
        self.game = game
        self.original_sprite = pg.image.load(sprite_path).convert_alpha()
        width, height = self.original_sprite.get_size()
        new_size = (int(width * scale_factor), int(height * scale_factor))
        self.sprite = pg.transform.scale(self.original_sprite, new_size)
        self.original_sprite = self.sprite
        self.rect = self.sprite.get_rect()
        self.x, self.y = pg.mouse.get_pos()
        self.prev_x, self.prev_y = self.x, self.y
        self.rotated_sprite_cache = {}

    def update(self):
        self.prev_x, self.prev_y = self.x, self.y
        self.x, self.y = pg.mouse.get_pos()
        angle = self.calculate_angle(self.game.balls[-1].position) + 90
        if angle not in self.rotated_sprite_cache:
            self.rotated_sprite_cache[angle] = pg.transform.rotate(self.original_sprite, -angle)
        self.sprite = self.rotated_sprite_cache[angle]
        self.rect = self.sprite.get_rect(center=(self.x, self.y))
        self.sprite = pg.transform.rotozoom(self.sprite, 0, 1 + 0.1 * math.sin(pg.time.get_ticks() / 1000))

    def draw(self, surface):
        surface.blit(self.sprite, self.rect)

    def calculate_angle(self, target_pos):
        dx = target_pos[0] - self.x
        dy = target_pos[1] - self.y
        angle = math.degrees(math.atan2(dy, dx))
        return angle

    def get_mouse_speed(self):
        dx = self.x - self.prev_x
        dy = self.y - self.prev_y
        return math.sqrt(dx**2 + dy**2)

class Ball:
    def __init__(self, game, radius, position, velocity):
        self.game = game
        self.radius = radius
        self.position = pg.Vector2(position)
        self.velocity = pg.Vector2(velocity)
        self.rect = pg.Rect(self.position.x - self.radius, self.position.y - self.radius, self.radius * 2, self.radius * 2)
        self.friction = 0.98
        self.color = pg.Color('black')
        self.border_color = pg.Color('black')
        self.initial_velocity = pg.Vector2(velocity)
        self.color_change_interval = 500
        self.color_change_time = pg.time.get_ticks()
        self.sound_played = False

    def update(self):
        self.velocity += self.initial_velocity * 0.01 * (pg.time.get_ticks() / 10000)
        self.velocity *= self.friction
        self.position += self.velocity
        self.rect.topleft = (self.position.x - self.radius, self.position.y - self.radius)
        self.check_boundaries()
        self.check_collisions_with_other_balls()
        if pg.time.get_ticks() - self.color_change_time > self.color_change_interval:
            self.color = pg.Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            self.color_change_time = pg.time.get_ticks()

    def draw(self, surface):
        pg.draw.circle(surface, self.border_color, self.position, self.radius + 2)
        pg.draw.circle(surface, self.color, self.position, self.radius)

    def check_boundaries(self):
        if self.position.x - self.radius < 0 or self.position.x + self.radius > self.game.screen.get_width():
            self.velocity.x *= -1
            self.position.x = max(self.radius, min(self.position.x, self.game.screen.get_width() - self.radius))
        if self.position.y - self.radius < 0 or self.position.y + self.radius > self.game.screen.get_height():
            self.velocity.y *= -1
            self.position.y = max(self.radius, min(self.position.y, self.game.screen.get_height() - self.radius))

    def hit_by_player(self, player_rect):
        if player_rect.colliderect(self.rect):
            mouse_speed = self.game.player.get_mouse_speed()
            direction = pg.Vector2(self.position - player_rect.center).normalize()
            self.velocity += direction * mouse_speed

    def check_collisions_with_other_balls(self):
        to_remove = []
        repelling_force_scale = 1.5
        
        for other_ball in self.game.balls:
            if other_ball != self and self.rect.colliderect(other_ball.rect):
                distance = self.position.distance_to(other_ball.position)
                if distance < self.radius + other_ball.radius:
                    normal = (self.position - other_ball.position).normalize()
                    overlap = (self.radius + other_ball.radius) - distance
                    
                    self.velocity += normal * overlap * repelling_force_scale
                    other_ball.velocity -= normal * overlap * repelling_force_scale
                    
                    overlap_distance = self.radius + other_ball.radius - distance
                    self.position += normal * (overlap_distance / 2)
                    other_ball.position -= normal * (overlap_distance / 2)
                    
                    to_remove.append(self)
                    to_remove.append(other_ball)
                    
                    if not self.sound_played:
                        self.game.scream.play()
                        self.sound_played = True

        for ball in to_remove:
            if ball in self.game.balls:
                self.game.balls.remove(ball)
                if ball in self.game.balls:
                    self.game.balls.remove(ball)
                    self.game.explosions += 1

        self.sound_played = False

class Obstacle:
    def __init__(self, game, position, size):
        self.game = game
        self.position = pg.Vector2(position)
        self.size = size
        self.rect = pg.Rect(self.position.x, self.position.y, size, size)
        self.color = pg.Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def draw(self, surface):
        pg.draw.rect(surface, self.color, self.rect)

class Game:
    def __init__(self):
        pg.init()
        pg.mouse.set_visible(False)
        monitor = get_monitors()[0]
        self.screen = pg.display.set_mode((monitor.width, monitor.height), pg.FULLSCREEN | pg.DOUBLEBUF | pg.HWSURFACE)
        self.player = Player(self, 'assets/cursor.jpg', 0.15)
        self.balls = [Ball(self, 12.5, (self.screen.get_width() // 2, self.screen.get_height() // 2), (5, 5))]
        self.ball_spawn_interval = 3000
        self.last_ball_spawn_time = pg.time.get_ticks()
        self.obstacles = [Obstacle(self, (random.randint(0, self.screen.get_width()), random.randint(0, self.screen.get_height())), random.randint(20, 50)) for _ in range(5)]
        self.clock = pg.time.Clock()
        self.background_color_change_speed = 0.1
        self.start_time = pg.time.get_ticks()
        self.screen_offset = pg.Vector2(0, 0)
        pg.mixer.init()
        pg.mixer.music.load('assets/bgm.ogg')
        pg.mixer.music.set_volume(0.3)
        pg.mixer.music.play(-1)
        self.scream = pg.mixer.Sound('assets/scream.ogg')
        self.explosions = 0
        self.max_balls = len(self.balls)

    def update(self):
        elapsed_time = pg.time.get_ticks() - self.start_time
        r = int((math.sin(self.background_color_change_speed * elapsed_time / 1000) + 1) * 127.5)
        g = int((math.sin(self.background_color_change_speed * elapsed_time / 1000 + 2) + 1) * 127.5)
        b = int((math.sin(self.background_color_change_speed * elapsed_time / 1000 + 4) + 1) * 127.5)
        self.background_color = pg.Color(r, g, b)

        self.draw_surface = pg.Surface(self.screen.get_size())
        self.draw_surface.fill(self.background_color)
        self.player.update()

        if pg.time.get_ticks() - self.last_ball_spawn_time > self.ball_spawn_interval:
            new_ball = Ball(self, 12.5, (random.randint(0, self.screen.get_width()), random.randint(0, self.screen.get_height())), (random.uniform(-5, 5), random.uniform(-5, 5)))
            self.balls.append(new_ball)
            self.last_ball_spawn_time = pg.time.get_ticks()
            self.max_balls = max(self.max_balls, len(self.balls))

        to_remove = []
        for ball in self.balls:
            ball.update()
            ball.hit_by_player(self.player.rect)
            if ball not in self.balls:
                to_remove.append(ball)
                self.explosions += 1
            ball.draw(self.draw_surface)

        for ball in to_remove:
            if ball in self.balls:
                self.balls.remove(ball)

        if not self.balls:
            self.display_win_message()
            pg.display.update()
            pg.time.wait(1000)
            pg.quit()
            sys.exit()

        self.player.draw(self.draw_surface)

        for obstacle in self.obstacles:
            obstacle.draw(self.draw_surface)

        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        self.screen.blit(self.draw_surface, (offset_x, offset_y))

        pg.display.update()

    def display_win_message(self):
        font = pg.font.SysFont(None, 72)
        text = font.render('You Win!', True, pg.Color('black'))
        self.screen.fill(pg.Color('white'))
        self.screen.blit(text, (self.screen.get_width() // 2 - text.get_width() // 2, self.screen.get_height() // 2 - text.get_height() // 2))

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

    def handle_input(self):
        for ball in self.balls:
            ball.hit_by_player(self.player.rect)

async def main():
    game = Game()
    while True:
        game.check_events()
        game.update()
        game.handle_input()
        game.clock.tick(60)
        await asyncio.sleep(0)

if __name__ == '__main__':
    asyncio.run(main())
