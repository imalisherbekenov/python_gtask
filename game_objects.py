import pygame
import random
import math

# Initialize the font module for the power-up letters
pygame.font.init()
POWERUP_FONT = pygame.font.Font(None, 20)


class Paddle:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.original_width = 100
        self.height = 10
        self.speed = 7
        self.color = (200, 200, 200)

        self.width = self.original_width
        self.power_up_timers = {"grow": 0, "laser": 0, "glue": 0}
        self.has_laser = False
        self.has_glue = False

        self.rect = pygame.Rect(
            self.screen_width // 2 - self.width // 2,
            self.screen_height - 30,
            self.width,
            self.height,
        )

    def reset(self):
        self.rect.x = self.screen_width // 2 - self.original_width // 2
        self.width = self.original_width
        self.rect.width = self.width
        self.has_laser = False
        self.has_glue = False
        for pu in self.power_up_timers:
            self.power_up_timers[pu] = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width

        self._update_power_ups()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        # Optionally draw power-up indicators here

    def activate_power_up(self, type):
        duration = 600  # frames
        if type == "grow":
            if self.power_up_timers["grow"] <= 0:
                center = self.rect.centerx
                self.width = 150
                self.rect.width = self.width
                self.rect.centerx = center
            self.power_up_timers["grow"] = duration
        elif type == "laser":
            self.has_laser = True
            self.power_up_timers["laser"] = duration
        elif type == "glue":
            self.has_glue = True
            self.power_up_timers["glue"] = duration

    def _update_power_ups(self):
        # grow
        if self.power_up_timers["grow"] > 0:
            self.power_up_timers["grow"] -= 1
            if self.power_up_timers["grow"] <= 0:
                center = self.rect.centerx
                self.width = self.original_width
                self.rect.width = self.width
                self.rect.centerx = center
        # laser
        if self.power_up_timers["laser"] > 0:
            self.power_up_timers["laser"] -= 1
            if self.power_up_timers["laser"] <= 0:
                self.has_laser = False
        # glue
        if self.power_up_timers["glue"] > 0:
            self.power_up_timers["glue"] -= 1
            if self.power_up_timers["glue"] <= 0:
                self.has_glue = False


class Ball:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.radius = 10
        self.color = (200, 200, 200)
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self.is_glued = False
        self.is_slowed = False
        self.slow_timer = 0
        self.base_speed = 6
        self.reset()

    def reset(self):
        self.rect.center = (self.screen_width // 2, self.screen_height // 2)
        self.speed_x = self.base_speed * random.choice((1, -1))
        self.speed_y = -self.base_speed
        self.is_glued = False
        self.is_slowed = False
        self.slow_timer = 0

    def update(self, paddle, launch_ball=False):
        if self.is_glued:
            self.rect.centerx = paddle.rect.centerx
            self.rect.bottom = paddle.rect.top
            if launch_ball:
                self.is_glued = False
                self.speed_x = self.base_speed * random.choice((1, -1))
                self.speed_y = -self.base_speed
            return "playing", None

        if self.is_slowed:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.speed_x *= 2
                self.speed_y *= 2
                self.is_slowed = False

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        collision = None
        # wall collision
        if self.rect.top <= 0:
            self.speed_y *= -1
            collision = "wall"
        if self.rect.left <= 0 or self.rect.right >= self.screen_width:
            self.speed_x *= -1
            collision = "wall"
        # paddle collision
        if self.rect.colliderect(paddle.rect) and self.speed_y > 0:
            if paddle.has_glue:
                self.is_glued = True
            self.speed_y *= -1
            collision = "paddle"
        # bottom lost
        if self.rect.top > self.screen_height:
            return "lost", None

        return "playing", collision

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)

    def activate_power_up(self, type):
        if type == "slow" and not self.is_slowed:
            self.speed_x /= 2
            self.speed_y /= 2
            self.is_slowed = True
            self.slow_timer = 600


class Brick:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


class PowerUp:
    PROPERTIES = {
        "grow": {"color": (60, 60, 255), "char": "G", "message": "PADDLE GROW"},
        "laser": {"color": (255, 60, 60), "char": "L", "message": "LASER CANNONS"},
        "glue": {"color": (60, 255, 60), "char": "C", "message": "CATCH PADDLE"},
        "slow": {"color": (255, 165, 0), "char": "S", "message": "SLOW BALL"},
    }

    def __init__(self, x, y, type):
        self.width = 30
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.speed_y = 3
        self.type = type
        self.color = self.PROPERTIES[type]["color"]
        self.char = self.PROPERTIES[type]["char"]

    def update(self):
        self.rect.y += self.speed_y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text = POWERUP_FONT.render(self.char, True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=self.rect.center))


class Laser:
    def __init__(self, x, y):
        self.width = 5
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = (255, 255, 0)
        self.speed_y = -8

    def update(self):
        self.rect.y += self.speed_y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


# Visual Effects
class Particle:
    def __init__(self, x, y, color, min_s, max_s, min_sp, max_sp, gravity):
        self.x, self.y = x, y
        self.color = color
        self.size = random.randint(min_s, max_s)
        self.vx = random.uniform(min_sp, max_sp) * math.cos(random.uniform(0, 360))
        self.vy = random.uniform(min_sp, max_sp) * math.sin(random.uniform(0, 360))
        self.gravity = gravity

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.size -= 0.1

    def draw(self, screen):
        if self.size > 0:
            pygame.draw.circle(
                screen, self.color, (int(self.x), int(self.y)), int(self.size)
            )


class Firework:
    def __init__(self, w, h):
        self.screen_w, self.screen_h = w, h
        self.x = random.randint(0, w)
        self.y = h
        self.vy = -random.uniform(8, 12)
        self.explosion_y = random.uniform(h * 0.2, h * 0.5)
        self.exploded, self.particles = False, []

    def update(self):
        if not self.exploded:
            self.y += self.vy
            if self.y <= self.explosion_y:
                self.exploded = True
                color = (
                    random.randint(50, 255),
                    random.randint(50, 255),
                    random.randint(50, 255),
                )
                for _ in range(50):
                    self.particles.append(
                        Particle(self.x, self.y, color, 2, 4, 1, 4, 0.1)
                    )
        else:
            for p in self.particles[:]:
                p.update()
                if p.size <= 0:
                    self.particles.remove(p)

    def draw(self, screen):
        if not self.exploded:
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 3)
        else:
            for p in self.particles:
                p.draw(screen)

    def is_dead(self):
        return self.exploded and not self.particles
