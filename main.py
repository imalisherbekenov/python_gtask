import pygame, sys, random
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework

pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

# Screen
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("PyGame Arkanoid")

# Colors & Fonts
BG = pygame.Color("grey12")
brick_colors = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)]
title_font = pygame.font.Font(None, 70)
game_font = pygame.font.Font(None, 40)
msg_font = pygame.font.Font(None, 30)

# Sounds
try:
    bounce_sound = pygame.mixer.Sound("bounce.wav")
    brick_sound = pygame.mixer.Sound("brick_break.wav")
    game_over_sound = pygame.mixer.Sound("game_over.wav")
    laser_sound = pygame.mixer.Sound("laser.wav")
except pygame.error:

    class Dummy:
        def play(self):
            pass

    bounce_sound, brick_sound, game_over_sound, laser_sound = (
        Dummy(),
        Dummy(),
        Dummy(),
        Dummy(),
    )

# Levels
levels = [{"rows": 4, "cols": 10}, {"rows": 5, "cols": 10}, {"rows": 6, "cols": 10}]
current_level = 0


def create_brick_wall(level):
    cfg = levels[level]
    bricks = []
    rows, cols = cfg["rows"], cfg["cols"]
    bw, bh = W // cols - 10, 20
    pad = 5
    start_y = 50
    for r in range(rows):
        for c in range(cols):
            x = c * (bw + pad) + pad
            y = r * (bh + pad) + start_y
            color = brick_colors[r % len(brick_colors)]
            bricks.append(Brick(x, y, bw, bh, color))
    return bricks


# Game State
paddle = Paddle(W, H)
ball = Ball(W, H)
bricks = create_brick_wall(current_level)
power_ups = []
lasers = []
particles = []
fireworks = []
score = 0
lives = 3
display_msg = ""
msg_timer = 0
firework_timer = 0
muted = False
game_state = "title_screen"

# Main Loop
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_m:
                muted = not muted
            if e.key == pygame.K_SPACE:
                if game_state == "title_screen":
                    game_state = "playing"
                elif game_state in ["game_over", "you_win"]:
                    # reset all
                    paddle.reset()
                    ball.reset()
                    current_level = 0
                    bricks = create_brick_wall(current_level)
                    score = 0
                    lives = 3
                    power_ups.clear()
                    lasers.clear()
                    particles.clear()
                    fireworks.clear()
                    game_state = "title_screen"
                elif ball.is_glued:
                    ball.is_glued = False
            if e.key == pygame.K_f and paddle.has_laser:
                lasers.append(Laser(paddle.rect.centerx - 30, paddle.rect.top))
                lasers.append(Laser(paddle.rect.centerx + 30, paddle.rect.top))
                if not muted:
                    laser_sound.play()

    screen.fill(BG)

    if game_state == "title_screen":
        # Title
        surf = title_font.render("ARKANOID", True, (255, 255, 255))
        rect = surf.get_rect(center=(W / 2, H / 2 - 50))
        screen.blit(surf, rect)
        sub = game_font.render("Press SPACE to Start", True, (255, 255, 255))
        r2 = sub.get_rect(center=(W / 2, H / 2 + 20))
        screen.blit(sub, r2)

    elif game_state == "playing":
        paddle.update()
        keys = pygame.key.get_pressed()
        status, coll = ball.update(paddle, keys[pygame.K_SPACE])

        if status == "lost":
            lives -= 1
            if lives <= 0:
                game_state = "game_over"
                if not muted:
                    game_over_sound.play()
            else:
                ball.reset()
                paddle.reset()

        if coll in ["wall", "paddle"]:
            if not muted:
                bounce_sound.play()
            for _ in range(5):
                particles.append(
                    Particle(
                        ball.rect.centerx,
                        ball.rect.centery,
                        (255, 255, 0),
                        1,
                        3,
                        1,
                        3,
                        0,
                    )
                )

        for b in bricks[:]:
            if ball.rect.colliderect(b.rect):
                ball.speed_y *= -1
                for _ in range(15):
                    particles.append(
                        Particle(
                            b.rect.centerx, b.rect.centery, b.color, 1, 4, 1, 4, 0.05
                        )
                    )
                bricks.remove(b)
                score += 10
                if not muted:
                    brick_sound.play()
                if random.random() < 0.3:
                    pu_type = random.choice(list(PowerUp.PROPERTIES))
                    power_ups.append(PowerUp(b.rect.centerx, b.rect.centery, pu_type))
                break

        for pu in power_ups[:]:
            pu.update()
            if pu.rect.top > H:
                power_ups.remove(pu)
            elif paddle.rect.colliderect(pu.rect):
                display_msg = PowerUp.PROPERTIES[pu.type]["message"]
                msg_timer = 120
                if pu.type in ["grow", "laser", "glue"]:
                    paddle.activate_power_up(pu.type)
                else:
                    ball.activate_power_up(pu.type)
                power_ups.remove(pu)

        for lz in lasers[:]:
            lz.update()
            if lz.rect.bottom < 0:
                lasers.remove(lz)
            else:
                for b in bricks[:]:
                    if lz.rect.colliderect(b.rect):
                        for _ in range(10):
                            particles.append(
                                Particle(
                                    b.rect.centerx,
                                    b.rect.centery,
                                    b.color,
                                    1,
                                    3,
                                    1,
                                    3,
                                    0.05,
                                )
                            )
                        bricks.remove(b)
                        lasers.remove(lz)
                        score += 10
                        if not muted:
                            brick_sound.play()
                        break

        # Level progression
        if not bricks:
            current_level += 1
            if current_level < len(levels):
                bricks = create_brick_wall(current_level)
                ball.reset()
                paddle.reset()
            else:
                game_state = "you_win"

        # Draw game
        paddle.draw(screen)
        ball.draw(screen)
        for b in bricks:
            b.draw(screen)
        for pu in power_ups:
            pu.draw(screen)
        for lz in lasers:
            lz.draw(screen)

        # HUD
        score_s = game_font.render(f"Score: {score}", True, (255, 255, 255))
        lives_s = game_font.render(f"Lives: {lives}", True, (255, 255, 255))
        lvl_s = game_font.render(
            f"Level: {current_level+1}/{len(levels)}", True, (255, 255, 255)
        )
        screen.blit(score_s, (10, 10))
        screen.blit(lives_s, (W - 150, 10))
        screen.blit(lvl_s, (W // 2 - 60, 10))

    else:  # game over or win
        if game_state == "you_win":
            firework_timer -= 1
            if firework_timer <= 0:
                fireworks.append(Firework(W, H))
                firework_timer = random.randint(20, 50)
            for fw in fireworks[:]:
                fw.update()
                if fw.is_dead():
                    fireworks.remove(fw)
            for fw in fireworks:
                fw.draw(screen)

        msg = "YOU WIN!" if game_state == "you_win" else "GAME OVER"
        txt = game_font.render(msg, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=(W / 2, H / 2 - 20)))
        sub = game_font.render("Press SPACE to return to Title", True, (255, 255, 255))
        screen.blit(sub, sub.get_rect(center=(W / 2, H / 2 + 30)))

    # Messages
    if msg_timer > 0:
        msg_timer -= 1
        surf = msg_font.render(display_msg, True, (255, 255, 255))
        screen.blit(surf, surf.get_rect(midbottom=(W / 2, H - 50)))

    # Particles
    for p in particles[:]:
        p.update()
        if p.size <= 0:
            particles.remove(p)
    for p in particles:
        p.draw(screen)

    pygame.display.flip()
    clock.tick(60)
