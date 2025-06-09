#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Fixed Graphics Effects
-----------------------------------
Complete particle system with all missing methods
"""

import random
import math

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame
        print("Using pygame-ce instead of pygame")
    except ImportError:
        print("Please install pygame or pygame-ce")
        import sys
        sys.exit(1)

from pygame import gfxdraw


class Particle:
    """Enhanced particle class"""

    def __init__(self, x, y, color, velocity=None, size=None, life_span=None, gravity=None, fade=True):
        self.x = float(x)
        self.y = float(y)
        self.color = color

        # Set velocity
        if velocity is None:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
        else:
            self.vx, self.vy = velocity

        # Set properties
        self.size = size if size is not None else random.randint(1, 4)
        self.original_size = self.size
        self.life_span = life_span if life_span is not None else random.uniform(0.5, 2.0)
        self.gravity = gravity if gravity is not None else 0
        self.age = 0
        self.alive = True
        self.fade = fade

        # Extra properties
        self.glow = random.random() < 0.3
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-180, 180)

    def update(self, dt):
        """Update particle state"""
        self.age += dt
        if self.age >= self.life_span:
            self.alive = False
            return False

        # Update size based on age
        if self.fade:
            life_ratio = 1 - (self.age / self.life_span)
            self.size = max(0.1, self.original_size * life_ratio)

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Apply gravity
        self.vy += self.gravity * dt

        # Add slight randomness
        self.vx += random.uniform(-10, 10) * dt
        self.vy += random.uniform(-10, 10) * dt

        # Update rotation
        self.rotation += self.rotation_speed * dt

        return True

    def render(self, surface):
        """Render particle with proper alpha blending"""
        try:
            # Calculate alpha based on age
            alpha = int(255 * (1 - (self.age / self.life_span)))
            if alpha <= 0:
                return

            # Create color with alpha
            if len(self.color) == 3:
                color_with_alpha = (*self.color, alpha)
            else:
                color_with_alpha = (*self.color[:3], min(alpha, self.color[3]))

            # Get integer coordinates
            x, y = int(self.x), int(self.y)
            size = int(self.size)

            # Skip if too small or off screen
            if size < 1 or x < -size or y < -size or x > surface.get_width() + size or y > surface.get_height() + size:
                return

            if size == 1:
                # Single pixel
                try:
                    surface.set_at((x, y), self.color)
                except:
                    pass
            elif self.glow and size > 2:
                # Glowing particle
                try:
                    pygame.draw.circle(surface, self.color, (x, y), size)
                    # Outer glow
                    if size > 1:
                        outer_color = (*self.color, alpha // 2)
                        pygame.draw.circle(surface, outer_color, (x, y), size + 1, 1)
                except:
                    pass
            else:
                # Regular particle
                try:
                    pygame.draw.circle(surface, self.color, (x, y), size)
                except:
                    pass

        except Exception:
            pass  # Silently ignore rendering errors


class ParticleSystem:
    """Complete particle system implementation"""

    def __init__(self, max_particles=2000):
        self.particles = []
        self.max_particles = max_particles

    def create_particle(self, x, y, color, velocity=None, size=None, life_span=None, gravity=None, fade=True):
        """Create and add a new particle"""
        if len(self.particles) < self.max_particles:
            particle = Particle(x, y, color, velocity, size, life_span, gravity, fade)
            self.particles.append(particle)

    def create_particle_explosion(self, x, y, count, color=None, radius=50, life_span=None):
        """Create explosion of particles"""
        for _ in range(min(count, self.max_particles - len(self.particles))):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, radius)
            particle_x = x + math.cos(angle) * distance
            particle_y = y + math.sin(angle) * distance

            # Random color if not specified
            if color is None:
                particle_color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )
            else:
                # Add variance to color
                r, g, b = color[:3]
                variance = 30
                particle_color = (
                    max(0, min(255, r + random.randint(-variance, variance))),
                    max(0, min(255, g + random.randint(-variance, variance))),
                    max(0, min(255, b + random.randint(-variance, variance)))
                )

            # Calculate velocity
            speed = random.uniform(10, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            self.create_particle(
                particle_x, particle_y, particle_color,
                velocity=(vx, vy),
                size=random.uniform(1, 4),
                life_span=life_span
            )

    def create_firework(self, x, y, color=None):
        """Create firework effect"""
        main_color = color or (
            random.randint(100, 255),
            random.randint(100, 255), 
            random.randint(100, 255)
        )
        
        # Main explosion
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            particle_color = (
                max(50, main_color[0] + random.randint(-50, 50)),
                max(50, main_color[1] + random.randint(-50, 50)),
                max(50, main_color[2] + random.randint(-50, 50))
            )
            
            self.create_particle(
                x, y, particle_color,
                velocity=(vx, vy),
                size=random.uniform(2, 6),
                life_span=random.uniform(1.0, 3.0),
                gravity=50,
                fade=True
            )

    def update(self, dt):
        """Update all particles"""
        # Update particles and remove dead ones
        self.particles = [p for p in self.particles if p.update(dt)]

    def render(self, surface):
        """Render all particles"""
        for particle in self.particles:
            particle.render(surface)

    def clear(self):
        """Remove all particles"""
        self.particles.clear()

    def get_count(self):
        """Get current particle count"""
        return len(self.particles)


class BloomEffect:
    """Simple bloom effect implementation"""

    def __init__(self, threshold=128, blur_passes=2, intensity=0.8):
        self.threshold = threshold
        self.blur_passes = blur_passes
        self.intensity = intensity

    def apply(self, surface):
        """Apply bloom effect to surface"""
        try:
            width, height = surface.get_size()
            
            # Create bloom surface
            bloom_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            bright_surface = pygame.Surface((width, height), pygame.SRCALPHA)

            # Extract bright pixels
            for y in range(0, height, 2):  # Sample every other pixel for performance
                for x in range(0, width, 2):
                    try:
                        color = surface.get_at((x, y))
                        brightness = (color.r + color.g + color.b) / 3
                        if brightness > self.threshold:
                            bright_factor = min(255, brightness * 1.2)
                            bright_color = (
                                min(255, int(color.r * 1.2)),
                                min(255, int(color.g * 1.2)),
                                min(255, int(color.b * 1.2)),
                                color.a if len(color) > 3 else 255
                            )
                            bright_surface.set_at((x, y), bright_color)
                    except:
                        continue

            # Simple blur by scaling down and up
            try:
                # Scale down
                small_surface = pygame.transform.scale(bright_surface, (width // 4, height // 4))
                # Scale back up (creates blur effect)
                blurred_surface = pygame.transform.scale(small_surface, (width, height))
                
                # Combine original with bloom
                bloom_surface.blit(surface, (0, 0))
                bloom_surface.blit(blurred_surface, (0, 0), special_flags=pygame.BLEND_ADD)
                
                return bloom_surface
            except:
                return surface

        except Exception:
            return surface


class ShakeEffect:
    """Screen shake effect"""

    def __init__(self, duration=0.5, intensity=5):
        self.duration = duration
        self.intensity = intensity
        self.timer = 0
        self.active = False
        self.offset_x = 0
        self.offset_y = 0

    def start(self, intensity=None, duration=None):
        """Start shake effect"""
        self.active = True
        self.timer = 0
        if intensity is not None:
            self.intensity = intensity
        if duration is not None:
            self.duration = duration

    def update(self, dt):
        """Update shake effect"""
        if self.active:
            self.timer += dt
            if self.timer >= self.duration:
                self.active = False
                self.offset_x = 0
                self.offset_y = 0
            else:
                progress = self.timer / self.duration
                current_intensity = self.intensity * (1 - progress)
                self.offset_x = random.uniform(-current_intensity, current_intensity)
                self.offset_y = random.uniform(-current_intensity, current_intensity)

        return (self.offset_x, self.offset_y)

    def is_active(self):
        """Check if shake is active"""
        return self.active