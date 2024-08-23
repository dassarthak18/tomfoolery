import asyncio
import pygame as pg
import sys
import math
from screeninfo import get_monitors

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
        angle = self.calculate_angle(self.game.ball.position) + 90
        if angle not in self.rotated_sprite_cache:
            self.rotated_sprite_cache[angle] = pg.transform.rotate(self.original_sprite, -angle)
        self.sprite = self.rotated_sprite_cache[angle]
        self.rect = self.sprite.get_rect(center=(self.x, self.y))

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
        self.color = pg.Color('black')
        self.dampening_factor = 0.99  # Air dampening factor

    def update(self):
        self.velocity *= self.dampening_factor  # Apply air dampening
        self.position += self.velocity
        self.rect.topleft = (self.position.x - self.radius, self.position.y - self.radius)
        self.check_boundaries()

    def draw(self, surface):
        pg.draw.circle(surface, self.color, self.position, self.radius)

    def check_boundaries(self):
        if self.position.x - self.radius < 0 or self.position.x + self.radius > self.game.screen.get_width():
            self.velocity.x *= -1
            self.position.x = max(self.radius, min(self.position.x, self.game.screen.get_width() - self.radius))
        if self.position.y - self.radius < 0 or self.position.y + self.radius > self.game.screen.get_height():
            self.velocity.y *= -1
            self.position.y = max(self.radius, min(self.position.y, self.game.screen.get_height() - self.radius))

    def hit_by_player(self, player_rect, mouse_speed):
        if player_rect.colliderect(self.rect):
            direction = (self.position - pg.Vector2(player_rect.center)).normalize()
            self.velocity += direction * mouse_speed

class Game:
    def __init__(self):
        pg.init()
        pg.mouse.set_visible(False)
        monitor = get_monitors()[0]
        self.screen = pg.display.set_mode((monitor.width, monitor.height), pg.FULLSCREEN | pg.DOUBLEBUF | pg.HWSURFACE)
        self.player = Player(self, 'assets/controller.png', 0.25)
        self.ball = Ball(self, 15, (self.screen.get_width() // 2, self.screen.get_height() // 2), (5, 5))
        self.clock = pg.time.Clock()

    def update(self):
        self.screen.fill(pg.Color('white'))
        self.player.update()
        self.ball.update()
        
        # Check for collision and apply force based on mouse speed
        mouse_speed = self.player.get_mouse_speed()
        self.ball.hit_by_player(self.player.rect, mouse_speed)

        self.player.draw(self.screen)
        self.ball.draw(self.screen)

        pg.display.update()

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

async def main():
    game = Game()
    while True:
        game.check_events()
        game.update()
        game.clock.tick(60)
        await asyncio.sleep(0)

if __name__ == '__main__':
    asyncio.run(main())
