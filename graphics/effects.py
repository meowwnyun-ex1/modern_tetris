#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Graphics Effects
------------------------------
คลาสและฟังก์ชันสำหรับเอฟเฟกต์พิเศษทางกราฟิก
"""

import random
import math

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame

        print("ใช้ pygame-ce แทน pygame")
    except ImportError:
        print("กรุณาติดตั้ง pygame หรือ pygame-ce")
        import sys

        sys.exit(1)
from pygame import gfxdraw


class Particle:
    """คลาสสำหรับอนุภาคในระบบอนุภาค"""

    def __init__(
        self,
        x,
        y,
        color,
        velocity=None,
        size=None,
        life_span=None,
        gravity=None,
        fade=True,
    ):
        """
        สร้างอนุภาคใหม่

        Args:
            x (float): ตำแหน่ง x เริ่มต้น
            y (float): ตำแหน่ง y เริ่มต้น
            color (tuple): สี RGB
            velocity (tuple, optional): ความเร็ว (vx, vy)
            size (int, optional): ขนาดของอนุภาค
            life_span (float, optional): อายุของอนุภาค (วินาที)
            gravity (float, optional): แรงโน้มถ่วง
            fade (bool, optional): ค่อยๆ จางหายไปหรือไม่
        """
        self.x = x
        self.y = y
        self.color = color

        # ตั้งค่าเริ่มต้นถ้าไม่มีการระบุ
        if velocity is None:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
        else:
            self.vx, self.vy = velocity

        self.size = size if size is not None else random.randint(1, 4)
        self.original_size = self.size
        self.life_span = (
            life_span if life_span is not None else random.uniform(0.5, 2.0)
        )
        self.gravity = gravity if gravity is not None else 0
        self.age = 0
        self.alive = True
        self.fade = fade

        # สำหรับเอฟเฟกต์เพิ่มเติม
        self.glow = random.random() < 0.3  # 30% โอกาสที่จะเรืองแสง
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-180, 180)  # องศาต่อวินาที

    def update(self, dt):
        """
        อัปเดตสถานะของอนุภาค

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)

        Returns:
            bool: True ถ้าอนุภาคยังมีชีวิตอยู่, False ถ้าหมดอายุ
        """
        # เพิ่มอายุ
        self.age += dt
        if self.age >= self.life_span:
            self.alive = False
            return False

        # คำนวณขนาดตามอายุ (ลดลงเมื่ออายุเพิ่มขึ้น)
        if self.fade:
            life_ratio = 1 - (self.age / self.life_span)
            self.size = self.original_size * life_ratio

        # อัปเดตตำแหน่ง
        self.x += self.vx * dt
        self.y += self.vy * dt

        # อัปเดตความเร็วตามแรงโน้มถ่วง
        self.vy += self.gravity * dt

        # เพิ่มความสุ่มเล็กน้อย
        self.vx += random.uniform(-10, 10) * dt
        self.vy += random.uniform(-10, 10) * dt

        # อัปเดตการหมุน
        self.rotation += self.rotation_speed * dt

        return True

    def render(self, surface):
        """
        วาดอนุภาคบนพื้นผิว

        Args:
            surface (pygame.Surface): พื้นผิวที่จะวาด
        """
        # คำนวณค่า alpha ตามอายุ
        alpha = int(255 * (1 - (self.age / self.life_span)))
        color_with_alpha = (*self.color, alpha)

        # วาดอนุภาคด้วยรูปแบบต่างๆ
        if self.size <= 1:
            # จุดเดียว
            pygame.gfxdraw.pixel(surface, int(self.x), int(self.y), color_with_alpha)
        elif self.glow:
            # วงกลมเรืองแสง
            radius = int(self.size)
            pygame.gfxdraw.filled_circle(
                surface, int(self.x), int(self.y), radius, color_with_alpha
            )

            # วาดวงแหวนรอบนอก
            if radius > 1:
                outer_color = (*self.color, alpha // 2)
                pygame.gfxdraw.circle(
                    surface, int(self.x), int(self.y), radius + 1, outer_color
                )
        else:
            # วงกลมปกติ
            pygame.gfxdraw.filled_circle(
                surface, int(self.x), int(self.y), int(self.size), color_with_alpha
            )


class ParticleSystem:
    """ระบบจัดการอนุภาค"""

    def __init__(self, max_particles=2000):
        """
        สร้างระบบอนุภาคใหม่

        Args:
            max_particles (int, optional): จำนวนอนุภาคสูงสุด
        """
        self.particles = []
        self.max_particles = max_particles

    def create_particle(
        self,
        x,
        y,
        color,
        velocity=None,
        size=None,
        life_span=None,
        gravity=None,
        fade=True,
    ):
        """
        สร้างอนุภาคใหม่และเพิ่มเข้าระบบ

        Args:
            x (float): ตำแหน่ง x เริ่มต้น
            y (float): ตำแหน่ง y เริ่มต้น
            color (tuple): สี RGB
            velocity (tuple, optional): ความเร็ว (vx, vy)
            size (int, optional): ขนาดของอนุภาค
            life_span (float, optional): อายุของอนุภาค (วินาที)
            gravity (float, optional): แรงโน้มถ่วง
            fade (bool, optional): ค่อยๆ จางหายไปหรือไม่
        """
        if len(self.particles) < self.max_particles:
            new_particle = Particle(
                x, y, color, velocity, size, life_span, gravity, fade
            )
            self.particles.append(new_particle)

    def create_particle_explosion(
        self, x, y, count, color=None, radius=50, life_span=None
    ):
        """
        สร้างระเบิดของอนุภาค (จำนวนมากพร้อมกันในรูปแบบวงกลม)

        Args:
            x (float): ตำแหน่ง x ศูนย์กลาง
            y (float): ตำแหน่ง y ศูนย์กลาง
            count (int): จำนวนอนุภาค
            color (tuple, optional): สี RGB (ถ้าไม่ระบุจะสุ่ม)
            radius (float, optional): รัศมีของระเบิด
            life_span (float, optional): อายุของอนุภาค (วินาที)
        """
        for _ in range(min(count, self.max_particles - len(self.particles))):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, radius)
            particle_x = x + math.cos(angle) * distance
            particle_y = y + math.sin(angle) * distance

            # สุ่มสีถ้าไม่ระบุ
            if color is None:
                particle_color = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
            else:
                # เพิ่มความแตกต่างเล็กน้อย
                r, g, b = color
                variance = 30
                particle_color = (
                    max(0, min(255, r + random.randint(-variance, variance))),
                    max(0, min(255, g + random.randint(-variance, variance))),
                    max(0, min(255, b + random.randint(-variance, variance))),
                )

            # คำนวณความเร็วจากศูนย์กลาง
            speed = random.uniform(10, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            self.create_particle(
                particle_x,
                particle_y,
                particle_color,
                velocity=(vx, vy),
                size=random.uniform(1, 4),
                life_span=life_span,
            )

    def update(self, dt):
        """
        อัปเดตสถานะของอนุภาคทั้งหมด

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)
        """
        # อัปเดตและลบอนุภาคที่หมดอายุ
        self.particles = [p for p in self.particles if p.update(dt)]

    def render(self, surface):
        """
        วาดอนุภาคทั้งหมดบนพื้นผิว

        Args:
            surface (pygame.Surface): พื้นผิวที่จะวาด
        """
        for particle in self.particles:
            particle.render(surface)


class BloomEffect:
    """คลาสสำหรับเอฟเฟกต์ Bloom (เรืองแสง)"""

    def __init__(self, threshold=128, blur_passes=2, intensity=0.8):
        """
        สร้างเอฟเฟกต์ Bloom

        Args:
            threshold (int): ค่าความสว่างเริ่มต้นสำหรับการเรืองแสง (0-255)
            blur_passes (int): จำนวนรอบของการเบลอ
            intensity (float): ความเข้มของเอฟเฟกต์
        """
        self.threshold = threshold
        self.blur_passes = blur_passes
        self.intensity = intensity

    def apply(self, surface):
        """
        ใช้เอฟเฟกต์ Bloom กับพื้นผิว

        Args:
            surface (pygame.Surface): พื้นผิวที่จะใช้เอฟเฟกต์

        Returns:
            pygame.Surface: พื้นผิวที่มีเอฟเฟกต์แล้ว
        """
        # สร้างสำเนาของพื้นผิวต้นฉบับ
        width, height = surface.get_size()
        bloom_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # สร้างพื้นผิวสำหรับส่วนที่สว่าง (กรองด้วย threshold)
        bright_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # ดึงพิกเซลที่สว่างกว่า threshold
        for y in range(height):
            for x in range(width):
                color = surface.get_at((x, y))
                brightness = (color.r + color.g + color.b) / 3
                if brightness > self.threshold:
                    # ปรับความสว่างให้มากขึ้น
                    bright_factor = min(255, brightness * 1.5)
                    bright_color = (
                        min(255, int(color.r * 1.5)),
                        min(255, int(color.g * 1.5)),
                        min(255, int(color.b * 1.5)),
                        color.a,
                    )
                    bright_surface.set_at((x, y), bright_color)

        # ทำการเบลอ
        blurred_surface = self._gaussian_blur(bright_surface, self.blur_passes)

        # รวมภาพต้นฉบับกับภาพที่เบลอแล้ว
        bloom_surface.blit(surface, (0, 0))
        bloom_surface.blit(blurred_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        return bloom_surface

    def _gaussian_blur(self, surface, passes):
        """
        ใช้เอฟเฟกต์ Gaussian Blur กับพื้นผิว

        Args:
            surface (pygame.Surface): พื้นผิวที่จะเบลอ
            passes (int): จำนวนรอบของการเบลอ

        Returns:
            pygame.Surface: พื้นผิวที่เบลอแล้ว
        """
        result = surface.copy()

        for _ in range(passes):
            # สร้างพื้นผิวชั่วคราว
            width, height = result.get_size()
            temp = pygame.Surface((width, height), pygame.SRCALPHA)

            # เบลอในแนวนอน
            horizontal_blur = pygame.Surface((width, height), pygame.SRCALPHA)
            for y in range(height):
                for x in range(width):
                    r, g, b, a = 0, 0, 0, 0
                    count = 0

                    # ใช้ kernel ขนาด 5x1
                    for i in range(-2, 3):
                        nx = x + i
                        if 0 <= nx < width:
                            color = result.get_at((nx, y))
                            r += color.r
                            g += color.g
                            b += color.b
                            a += color.a
                            count += 1

                    # คำนวณค่าเฉลี่ย
                    if count > 0:
                        horizontal_blur.set_at(
                            (x, y), (r // count, g // count, b // count, a // count)
                        )

            # เบลอในแนวตั้ง
            for y in range(height):
                for x in range(width):
                    r, g, b, a = 0, 0, 0, 0
                    count = 0

                    # ใช้ kernel ขนาด 1x5
                    for i in range(-2, 3):
                        ny = y + i
                        if 0 <= ny < height:
                            color = horizontal_blur.get_at((x, ny))
                            r += color.r
                            g += color.g
                            b += color.b
                            a += color.a
                            count += 1

                    # คำนวณค่าเฉลี่ย
                    if count > 0:
                        temp.set_at(
                            (x, y), (r // count, g // count, b // count, a // count)
                        )

            result = temp

        return result


class ShakeEffect:
    """คลาสสำหรับเอฟเฟกต์สั่น"""

    def __init__(self, duration=0.5, intensity=5):
        """
        สร้างเอฟเฟกต์สั่น

        Args:
            duration (float): ระยะเวลาของการสั่น (วินาที)
            intensity (float): ความแรงของการสั่น (พิกเซล)
        """
        self.duration = duration
        self.intensity = intensity
        self.timer = 0
        self.active = False
        self.offset_x = 0
        self.offset_y = 0

    def start(self, intensity=None, duration=None):
        """
        เริ่มเอฟเฟกต์สั่น

        Args:
            intensity (float, optional): ความแรงของการสั่น (พิกเซล)
            duration (float, optional): ระยะเวลาของการสั่น (วินาที)
        """
        self.active = True
        self.timer = 0

        if intensity is not None:
            self.intensity = intensity

        if duration is not None:
            self.duration = duration

    def update(self, dt):
        """
        อัปเดตสถานะของเอฟเฟกต์สั่น

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)

        Returns:
            tuple: (offset_x, offset_y) การเคลื่อนที่ของหน้าจอ
        """
        if self.active:
            self.timer += dt

            if self.timer >= self.duration:
                self.active = False
                self.offset_x = 0
                self.offset_y = 0
            else:
                # คำนวณความแรงตามเวลา (ลดลงเมื่อเวลาผ่านไป)
                progress = self.timer / self.duration
                current_intensity = self.intensity * (1 - progress)

                # สุ่มค่าการเคลื่อนที่
                self.offset_x = random.uniform(-current_intensity, current_intensity)
                self.offset_y = random.uniform(-current_intensity, current_intensity)

        return (self.offset_x, self.offset_y)
