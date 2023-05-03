import sys
import pygame
from random import choice, randint

from player import Player
from alien import Alien, Extra
from laser import Laser
import obstacle


class Game:
    def __init__(self) -> None:
        # Player setup
        player_sprite = Player(
            (screen_height / 2, screen_height), screen_width, 5)
        self.player = pygame.sprite.GroupSingle(player_sprite)
        self.game_over = False

        # health and score setup
        self.lives = 3
        self.live_surf = pygame.image.load(
            'graphics/player.png').convert_alpha()
        self.live_x_start_pos = screen_width - \
            (self.live_surf.get_size()[0] * 2 + 20)
        self.score = 0
        self.font = pygame.font.Font('font/Pixeled.ttf', 20)
        self.game_font = pygame.font.Font('font/Pixeled.ttf', 40)

        self.loose_surf = self.font.render('You loose', False, 'white')
        self.loose_rect = self.loose_surf.get_rect(
            center=(screen_width/2, screen_height/2))
        self.loose_surf.set_alpha(0)

        # Obstacle setup
        self.shape = obstacle.shape
        self.block_size = 6
        self.blocks = pygame.sprite.Group()
        self.obstacle_amount = 4
        self.obstacle_x_positions = [
            num * (screen_width/self.obstacle_amount) for num in range(self.obstacle_amount)]
        self.create_multiple_obstacles(
            *self.obstacle_x_positions, x_start=screen_width/15, y_start=480)

        # Alien setup
        self.aliens = pygame.sprite.Group()
        self.alien_setup(rows=6, cols=8)
        self.alien_direction = 1
        self.aliens_lasers = pygame.sprite.Group()

        # Extra setup
        self.extra = pygame.sprite.GroupSingle()
        self.extra_spawn_time = randint(400, 800)

        # Audio
        self.music = pygame.mixer.Sound('audio/music.wav')
        self.music.set_volume(0.1)
        self.music.play(loops=-1)

        self.destroy = pygame.mixer.Sound('audio/explosion.wav')
        self.destroy.set_volume(0.2)

        self.shot_sound = pygame.mixer.Sound('audio/laser.wav')
        self.shot_sound.set_volume(0.1)

    def create_obstacle(self, x_start, y_start, offset_x):
        for row_index, row in enumerate(self.shape):
            for col_index, col in enumerate(row):
                if col == 'x':
                    x = x_start + col_index * self.block_size + offset_x
                    y = y_start + row_index * self.block_size
                    block = obstacle.Block(
                        self.block_size, (241, 79, 80), x, y)
                    self.blocks.add(block)

    def create_multiple_obstacles(self, *offset, x_start, y_start):
        for offset_x in offset:
            self.create_obstacle(x_start, y_start, offset_x)

    def alien_setup(self, rows, cols, x_distance=60, y_distance=40, x_offset=70, y_offset=100):
        for row_index in range(rows):
            for col_index in range(cols):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset

                if row_index == 0:
                    alien_sprite = Alien('yellow', x, y)
                elif 1 <= row_index <= 2:
                    alien_sprite = Alien('green', x, y)
                else:
                    alien_sprite = Alien('red', x, y)
                self.aliens.add(alien_sprite)

    def alien_position_checker(self):
        all_aliens = self.aliens.sprites()
        for alien in all_aliens:
            if alien.rect.right >= screen_width:
                self.alien_direction = -1
                self.alien_move_down(2)
            elif alien.rect.left <= 0:
                self.alien_direction = 1
                self.alien_move_down(2)

    def alien_move_down(self, distance):
        if self.aliens:
            for alien in self.aliens.sprites():
                alien.rect.y += distance

    def alien_shoot(self):
        if self.aliens.sprites():
            random_alien = choice(self.aliens.sprites())
            laser_sprite = Laser(random_alien.rect.center, 6, screen_height)
            self.aliens_lasers.add(laser_sprite)
            self.shot_sound.play()

    def extra_alien_timer(self):
        self.extra_spawn_time -= 1
        if self.extra_spawn_time <= 0:
            self.extra.add(Extra(choice(['right', 'left']), screen_width))
            self.extra_spawn_time = randint(400, 800)

    def collision_checks(self):

        # player lasers
        if self.player.sprite.lasers:
            for laser in self.player.sprite.lasers:
                # obstacle collisions
                if pygame.sprite.spritecollide(laser, self.blocks, True):
                    laser.kill()

                # alien collisions
                alien_hit = pygame.sprite.spritecollide(
                    laser, self.aliens, True)
                if alien_hit:
                    laser.kill()
                    self.destroy.play()
                    for alien in alien_hit:
                        self.score += alien.value

                # extra collisions
                if pygame.sprite.spritecollide(laser, self.extra, True):
                    self.score += 500
                    laser.kill()
        # alien lasers
        if self.aliens_lasers:
            for laser in self.aliens_lasers:
                # obstacle collisions
                if pygame.sprite.spritecollide(laser, self.blocks, True):
                    laser.kill()
                # player collisions
                if pygame.sprite.spritecollide(laser, self.player, False):
                    laser.kill()
                    self.destroy.play()
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                        self.loose_surf.set_alpha(1000)
        # aliens
        if self.aliens:
            for alien in self.aliens:
                pygame.sprite.spritecollide(alien, self.blocks, True)

                if pygame.sprite.spritecollide(alien, self.player, False):
                    self.game_over = True
                    self.loose_surf.set_alpha(1000)

    def display_lives(self):
        for live in range(self.lives - 1):
            x = self.live_x_start_pos + \
                (live * (self.live_surf.get_size()[0] + 10))
            screen.blit(self.live_surf, (x, 8))

    def display_score(self):
        score_surf = self.font.render(f'score: {self.score}', False, 'white')
        score_rect = score_surf.get_rect(topleft=(10, -10))
        screen.blit(score_surf, score_rect)

    def victory_message(self):
        if not self.aliens.sprites():
            victory_surf = self.font.render('You won', False, 'white')
            victory_rect = victory_surf.get_rect(
                center=(screen_width/2, screen_height/2))
            screen.blit(victory_surf, victory_rect)
            self.game_end()

    def run(self):
        # update all sprite groups
        self.player.update()
        self.aliens_lasers.update()
        self.aliens.update(self.alien_direction)
        self.extra.update()

        self.collision_checks()
        self.alien_position_checker()
        self.extra_alien_timer()
        self.victory_message()

        # draw all sprite groups
        self.player.sprite.lasers.draw(screen)
        self.player.draw(screen)
        self.aliens.draw(screen)
        self.blocks.draw(screen)
        self.aliens_lasers.draw(screen)
        self.extra.draw(screen)
        self.display_lives()
        self.display_score()
        screen.blit(self.loose_surf, self.loose_rect)

    def game_end(self):
        self.game_over = True

    def start_screen(self):

        game_name_surf = self.game_font.render(
            'Space Invaders', False, 'white')
        game_name_rect = game_name_surf.get_rect(
            center=(screen_width/2, screen_height/3))
        start_surf = self.font.render('Press Enter to START', False, 'white')
        start_rect = start_surf.get_rect(
            center=(screen_width/2, screen_height/2))
        screen.blit(start_surf, start_rect)
        screen.blit(game_name_surf, game_name_rect)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            return True
        return False


class CRT:
    def __init__(self) -> None:
        self.tv = pygame.image.load('graphics/tv.png').convert_alpha()
        self.tv = pygame.transform.scale(
            self.tv, (screen_width, screen_height))

    def create_crt_lines(self):
        line_height = 3
        line_amount = int(screen_height / line_height)
        for line in range(line_amount):
            y_pos = line * line_height
            pygame.draw.line(self.tv, 'black', (0, y_pos),
                             (screen_width, y_pos), 1)

    def draw(self):
        self.tv.set_alpha(randint(75, 90))
        self.create_crt_lines()
        screen.blit(self.tv, (0, 0))


if __name__ == '__main__':
    pygame.init()
    screen_width = 600
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    game = Game()
    crt = CRT()

    start = False
    ALIENLASER = pygame.USEREVENT + 1
    pygame.time.set_timer(ALIENLASER, 800)
    while True:

        while not start:
            screen.fill((30, 30, 30))
            start = game.start_screen()
            crt.draw()
            if game.aliens_lasers:
                for laser in game.aliens_lasers:
                    laser.kill()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            pygame.display.flip()

        game.shot_sound.set_volume(0.1)

        if game.game_over:

            game.music.stop()
            pygame.time.wait(1500)

            game = Game()
            game.shot_sound.set_volume(0.0)

            start = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == ALIENLASER:
                game.alien_shoot()

        screen.fill((30, 30, 30))

        game.run()
        crt.draw()

        pygame.display.flip()
        clock.tick(60)
