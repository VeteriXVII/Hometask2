import pygame
import sys
import random
import math
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework

pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PyGame Arkanoid")

BG_COLOR = pygame.Color('grey12')
BRICK_COLORS = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)]

title_font   = pygame.font.Font(None, 70)
game_font    = pygame.font.Font(None, 40)
message_font = pygame.font.Font(None, 30)

try:
    bounce_sound      = pygame.mixer.Sound('bounce.wav')
    brick_break_sound = pygame.mixer.Sound('brick_break.wav')
    game_over_sound   = pygame.mixer.Sound('game_over.wav')
    laser_sound       = pygame.mixer.Sound('laser.wav')
except pygame.error:
    class DummySound:
        def play(self): ...
    bounce_sound = brick_break_sound = game_over_sound = laser_sound = DummySound()

muted = False
def play_sound(snd):
    if not muted and hasattr(snd, "play"):
        snd.play()

paddle = Paddle(screen_width, screen_height)
ball   = Ball(screen_width, screen_height)

def create_brick_wall(level):
    bricks = []
    brick_rows    = 4 + level    
    brick_cols    = 8 + level
    brick_width   = 75
    brick_height  = 20
    brick_padding = 5
    wall_start_y  = 50
    for row in range(brick_rows):
        for col in range(brick_cols):
            x = col * (brick_width + brick_padding) + brick_padding
            y = row * (brick_height + brick_padding) + wall_start_y
            color = BRICK_COLORS[row % len(BRICK_COLORS)]
            bricks.append(Brick(x, y, brick_width, brick_height, color))
    return bricks

level      = 1
MAX_LEVEL  = 3
bricks     = create_brick_wall(level)
power_ups  = []
lasers     = []
particles  = []
fireworks  = []

game_state      = 'title_screen'
score           = 0
lives           = 3
display_message = ""
message_timer   = 0
firework_timer  = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:         
                muted = not muted

            if event.key == pygame.K_SPACE:
                if game_state == 'title_screen':
                    game_state = 'playing'
                elif game_state in ['game_over', 'you_win']:
                    level = 1
                    bricks = create_brick_wall(level)
                    score = 0; lives = 3
                    power_ups.clear(); lasers.clear(); particles.clear(); fireworks.clear()
                    paddle.reset(); ball.reset()
                    game_state = 'title_screen'
                elif ball.is_glued:
                    ball.is_glued = False

            if event.key == pygame.K_f and paddle.has_laser:
                lasers.append(Laser(paddle.rect.centerx - 30, paddle.rect.top))
                lasers.append(Laser(paddle.rect.centerx + 30, paddle.rect.top))
                play_sound(laser_sound)

    screen.fill(BG_COLOR)

    # Screen title
    if game_state == 'title_screen':
        title_surface = title_font.render("ARKANOID", True, (255, 255, 255))
        screen.blit(title_surface, title_surface.get_rect(center=(screen_width/2, screen_height/2 - 50)))

        start_surface = game_font.render("Press SPACE to Start", True, (255, 255, 255))
        screen.blit(start_surface, start_surface.get_rect(center=(screen_width/2, screen_height/2 + 20)))

    # Play state
    elif game_state == 'playing':
        paddle.update()
        keys = pygame.key.get_pressed()
        ball_status, collision_object = ball.update(paddle, keys[pygame.K_SPACE])

        if ball_status == 'lost':
            lives -= 1
            if lives <= 0:
                game_state = 'game_over'
                play_sound(game_over_sound)
            else:
                ball.reset(); paddle.reset()

        elif collision_object in ['wall', 'paddle']:
            play_sound(bounce_sound)
            for _ in range(5):
                particles.append(Particle(ball.rect.centerx, ball.rect.centery, (255, 255, 0), 1, 3, 1, 3, 0))

        # --- Brick collisions ---
        for brick in bricks[:]:
            if ball.rect.colliderect(brick.rect):
                ball.speed_y *= -1
                for _ in range(15):
                    particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 4, 1, 4, 0.05))
                bricks.remove(brick)
                score += 10
                play_sound(brick_break_sound)
                if random.random() < 0.3:
                    power_up_type = random.choice(
                        ['grow','laser','glue','slow','extralife','shrink','fast']
                    )
                    power_ups.append(PowerUp(brick.rect.centerx, brick.rect.centery, power_up_type))
                break

        # --- Power-ups ---
        for pu in power_ups[:]:
            pu.update()
            if pu.rect.top > screen_height:
                power_ups.remove(pu)
            elif paddle.rect.colliderect(pu.rect):
                display_message = pu.PROPERTIES[pu.type]['message']
                message_timer = 120
                if pu.type in ['grow','laser','glue','shrink']:
                    paddle.activate_power_up(pu.type)
                elif pu.type == 'slow':
                    ball.activate_power_up('slow')
                elif pu.type == 'fast':
                    ball.activate_power_up('fast')
                elif pu.type == 'extralife':
                    lives += 1
                power_ups.remove(pu)

        for laser in lasers[:]:
            laser.update()
            if laser.rect.bottom < 0:
                lasers.remove(laser)
            else:
                for brick in bricks[:]:
                    if laser.rect.colliderect(brick.rect):
                        for _ in range(10):
                            particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                        bricks.remove(brick)
                        lasers.remove(laser)
                        score += 10
                        play_sound(brick_break_sound)
                        break

        if not bricks:
            level += 1
            if level > MAX_LEVEL:
                game_state = 'you_win'
            else:
                bricks = create_brick_wall(level)
                paddle.reset(); ball.reset()

        paddle.draw(screen); ball.draw(screen)
        for brick in bricks: brick.draw(screen)
        for pu in power_ups: pu.draw(screen)
        for laser in lasers: laser.draw(screen)

        score_text = game_font.render(f"Score: {score}", True, (255,255,255))
        lives_text = game_font.render(f"Lives: {lives}", True, (255,255,255))
        level_text = game_font.render(f"Level: {level}", True, (255,255,255))
        mute_text  = game_font.render("🔇" if muted else "🔊", True, (255,255,255))

        screen.blit(score_text, (10,10))
        screen.blit(lives_text, (screen_width - lives_text.get_width() - 10, 10))
        screen.blit(level_text, (screen_width//2 - level_text.get_width()//2, 10))
        screen.blit(mute_text,  (screen_width//2 - mute_text.get_width()//2, 40))

    # Game over or win
    elif game_state in ['game_over','you_win']:
        if game_state == 'you_win':
            firework_timer -= 1
            if firework_timer <= 0:
                fireworks.append(Firework(screen_width, screen_height))
                firework_timer = random.randint(20, 50)
            for fw in fireworks[:]:
                fw.update()
                if fw.is_dead(): fireworks.remove(fw)
            for fw in fireworks: fw.draw(screen)

 
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150); overlay.fill((0,0,0))
        screen.blit(overlay, (0,0))

        big_font = pygame.font.Font(None, 80)
        msg = "You wun" if game_state == 'you_win' else "GAME OVER"
        screen.blit(big_font.render(msg, True, (255,0,0) if game_state=='game_over' else (0,255,0)),
                    big_font.render(msg, True, (0,0,0)).get_rect(center=(screen_width/2, screen_height/2 - 40)))

        screen.blit(game_font.render(f"Final score: {score}", True, (255,255,255)),
                    game_font.render("x", True, (0,0,0)).get_rect(center=(screen_width/2, screen_height/2 + 10)))

        restart_surface = game_font.render("Press SPACE to returne", True, (255,255,255))
        screen.blit(restart_surface, restart_surface.get_rect(center=(screen_width/2, screen_height/2 + 60)))

    if message_timer > 0:
        message_timer -= 1
        msg_surf = message_font.render(display_message, True, (255,255,255))
        screen.blit(msg_surf, msg_surf.get_rect(center=(screen_width/2, screen_height - 60)))

    for p in particles[:]:
        p.update()
        if p.size <= 0: particles.remove(p)
    for p in particles: p.draw(screen)

    pygame.display.flip()
    clock.tick(60)