import pygame
import pygame.gfxdraw
import math
import random

# =============================================================================
# ⚙️ Game Settings
# =============================================================================
settings = {
    # 🎯 Physics Engine
    'gravity': 0.05,                 # Gravity intensity applied to the ball (px/frame²)
    'ball_elasticity': 1.0,          # Elasticity factor (1.0 = perfect bounce, <1 = energy loss)

    # 🔵 Circles (Levels)
    'num_circles': 25,               # Total number of circles
    'base_radius': 45,               # Radius of the first (smallest) circle
    'radius_increment': 100,         # Distance between each circle
    'radius_increment_factor': 0.1,  # Multiplicative factor for progressive spacing
    'circle_thickness': 5,           # Thickness of each ring (px)
    'circle_rotation_speed': 0.005,  # Rotation speed of circles (rad/frame)
    'circle_rotation_speed_offset': 0.00025,  # Speed variation between circles
    'hole_size': 0.5,                # Size of the hole in a circle (in radians, 0.35 ≈ 20°)
    'base_hole_angle': 1.5,          # Initial hole angle (in radians)

    # 🎨 Circle color options
    'circle_color_mode': 'gradient',  # Color mode: "alternating" (switching) or "gradient" (smooth transition)
    'circle_colors': [(255, 187, 0), (255, 0, 0)],  # List of colors used

    # ⚪ Ball
    'ball_speed': 2.5,               # Initial speed of the ball (px/frame)
    'ball_radius': 5,                # Ball radius (px)
    'ball_color': (255, 255, 255),    # Ball color

    # 🌠 Ball trail
    'ball_trail_length': 8,           # Trail length (number of stored positions)
    'ball_trail_width': 5,            # Trail width (px)
    'ball_trail_color': (220, 220, 220),  # Trail color

    # ✨ Particles (Circle destruction effects)
    'particle_count': 150,            # Number of particles generated when a circle is destroyed
    'particle_min_size': 1,           # Minimum particle size
    'particle_max_size': 1,           # Maximum particle size
    'particle_min_lifetime': 35,      # Minimum particle lifetime (frames)
    'particle_max_lifetime': 50,      # Maximum particle lifetime (frames)
    'particle_speed_min': -1,         # Minimum particle speed
    'particle_speed_max': 1,          # Maximum particle speed

    # 🖥️ Display
    'background_color': (0, 0, 0),    # Background color
    'arc_resolution': 50,             # Arc resolution (number of points for smooth rendering)
}

# =============================================================================
# Initialize Pygame
# =============================================================================
pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Ball - Game")
clock = pygame.time.Clock()

# =============================================================================
# Utility Functions
# =============================================================================
def normalize_angle(angle):
    """Brings an angle into the range [0, 2π)."""
    return angle % (2 * math.pi)

def is_angle_in_range(angle, start, end):
    """
    Returns True if 'angle' is within the interval [start, end] (handling wrap-around at 0).
    """
    if start > end:
        return angle >= start or angle <= end
    else:
        return start <= angle <= end

def draw_ring_arc(surface, center, r, thickness, start_angle, end_angle, color, num_points=100):
    """
    Draws a ring segment: a portion of a circle with thickness 'thickness'
    between 'start_angle' and 'end_angle'.
    This is done by calculating the polyline of the outer and inner arcs,
    then connecting them into a filled polygon (with anti-aliasing).
    """
    outer_r = r + thickness / 2
    inner_r = r - thickness / 2
    outer_points = []
    inner_points = []
    
    for i in range(num_points + 1):
        angle = start_angle + (end_angle - start_angle) * i / num_points
        x = center[0] + outer_r * math.cos(angle)
        y = center[1] + outer_r * math.sin(angle)
        outer_points.append((int(x), int(y)))
    
    for i in range(num_points + 1):
        angle = end_angle - (end_angle - start_angle) * i / num_points
        x = center[0] + inner_r * math.cos(angle)
        y = center[1] + inner_r * math.sin(angle)
        inner_points.append((int(x), int(y)))
    
    points = outer_points + inner_points
    pygame.gfxdraw.filled_polygon(surface, points, color)
    pygame.gfxdraw.aapolygon(surface, points, color)

def get_circle_color(i, total):
    """
    Returns the color of the circle at index i, based on the chosen mode in settings.
      - "alternating": uses the color list cyclically
      - "gradient": linearly interpolates between the first and second colors in the list
    """
    mode = settings.get("circle_color_mode", "alternating")
    colors = settings.get("circle_colors", [(255, 0, 0), (255, 255, 255)])
    if mode == "alternating":
        return colors[i % len(colors)]
    elif mode == "gradient":
        if len(colors) < 2:
            return colors[0]
        t = i / (total - 1) if total > 1 else 0
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * t)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * t)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * t)
        return (r, g, b)
    else:
        return colors[0]

# =============================================================================
# Particle Class: Particles for circle destruction effects
# =============================================================================
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = random.randint(settings['particle_min_lifetime'], settings['particle_max_lifetime'])
        self.size = random.randint(settings['particle_min_size'], settings['particle_max_size'])
        self.vel = [
            random.uniform(settings['particle_speed_min'], settings['particle_speed_max']),
            random.uniform(settings['particle_speed_min'], settings['particle_speed_max'])
        ]
        
    def update(self):
        self.x += self.vel[0]
        self.y += self.vel[1]
        self.lifetime -= 1
        
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

particles = []

# =============================================================================
# Circle Class: Rotating circle with a hole (drawn with smooth segments)
# =============================================================================
class Circle:
    def __init__(self, x, y, r, hole_angle, hole_size, color, thickness, rotation_speed):
        self.x = x
        self.y = y
        self.r = r
        self.hole_angle = hole_angle
        self.hole_size = hole_size
        self.color = color
        self.thickness = thickness
        self.rotation_speed = rotation_speed
        self.rotation = 0.0

    def update(self):
        self.rotation = normalize_angle(self.rotation + self.rotation_speed)

    def draw(self, surface):
        center = (self.x, self.y)
        effective_hole_angle = normalize_angle(self.hole_angle + self.rotation)
        gap_start = normalize_angle(effective_hole_angle - self.hole_size / 2)
        gap_end = normalize_angle(effective_hole_angle + self.hole_size / 2)
        
        if gap_start < gap_end:
            draw_ring_arc(surface, center, self.r, self.thickness, gap_end, 2*math.pi, self.color, settings['arc_resolution'])
            draw_ring_arc(surface, center, self.r, self.thickness, 0, gap_start, self.color, settings['arc_resolution'])
        else:
            draw_ring_arc(surface, center, self.r, self.thickness, gap_end, gap_start, self.color, settings['arc_resolution'])
