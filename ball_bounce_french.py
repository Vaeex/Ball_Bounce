import pygame
import pygame.gfxdraw
import math
import random

# =============================================================================
# ⚙️ Paramètres du jeu (Settings)
# =============================================================================
settings = {
    # 🎯 Moteur Physique
    'gravity': 0.05,                 # Intensité de la gravité appliquée à la balle (px/frame²)
    'ball_elasticity': 1.0,          # Facteur d'élasticité (1.0 = rebond parfait, <1 = perte d'énergie)

    # 🔵 Cercles (Niveaux)
    'num_circles': 25,               # Nombre total de cercles
    'base_radius': 45,               # Rayon du premier cercle (le plus petit)
    'radius_increment': 100,         # Distance entre chaque cercle
    'radius_increment_factor': 0.1,  # Facteur multiplicatif pour espacer progressivement les cercles
    'circle_thickness': 5,           # Épaisseur de chaque anneau (px)
    'circle_rotation_speed': 0.005, # Vitesse de rotation des cercles (rad/frame)
    'circle_rotation_speed_offset': 0.00025, # Variation de vitesse entre chaque cercle
    'hole_size': 0.5,               # Taille du trou dans un cercle (en radians, 0.35 ≈ 20°)
    'base_hole_angle': 1.5,          # Angle initial du trou (en radians)

    # 🎨 Options de couleur pour les cercles
    'circle_color_mode': 'gradient',  # Mode de couleur : "alternating" (alternance) ou "gradient" (dégradé)
    'circle_colors': [(255, 187, 0), (255, 0, 0)],  # Liste des couleurs utilisées

    # ⚪ Balle
    'ball_speed': 2.5,                 # Vitesse initiale de la balle (px/frame)
    'ball_radius': 5,                # Rayon de la balle (px)
    'ball_color': (255, 255, 255),       # Couleur de la balle

    # 🌠 Trainée de la balle
    'ball_trail_length': 8,         # Longueur de la trainée (nombre de positions stockées)
    'ball_trail_width': 5,           # Largeur de la trainée (px)
    'ball_trail_color': (220, 220, 220), # Couleur de la trainée

    # ✨ Particules (Effets de destruction des cercles)
    'particle_count': 150,            # Nombre de particules générées lors de la destruction d'un cercle
    'particle_min_size': 1,          # Taille minimale des particules
    'particle_max_size': 1,          # Taille maximale des particules
    'particle_min_lifetime': 35,     # Durée de vie minimale des particules (frames)
    'particle_max_lifetime': 50,     # Durée de vie maximale des particules (frames)
    'particle_speed_min': -1,        # Vitesse minimale des particules
    'particle_speed_max': 1,         # Vitesse maximale des particules

    # 🖥️ Affichage
    'background_color': (0, 0, 0),   # Couleur du fond de l'écran
    'arc_resolution': 50,            # Résolution des arcs (nombre de points pour un rendu lisse)
}


# =============================================================================
# Initialisation de Pygame
# =============================================================================
pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Ball - Game")
clock = pygame.time.Clock()


# =============================================================================
# Fonctions utilitaires
# =============================================================================
def normalize_angle(angle):
    """Ramène un angle dans [0, 2π)."""
    return angle % (2 * math.pi)

def is_angle_in_range(angle, start, end):
    """
    Retourne True si 'angle' se trouve dans l'intervalle [start, end] (en gérant le passage par 0).
    """
    if start > end:
        return angle >= start or angle <= end
    else:
        return start <= angle <= end

def draw_ring_arc(surface, center, r, thickness, start_angle, end_angle, color, num_points=100):
    """
    Dessine un segment d'anneau (ring) : la portion d'un cercle d'épaisseur 'thickness'
    comprise entre 'start_angle' et 'end_angle'.
    Pour cela, on calcule la polyligne de l'arc extérieur et celle de l'arc intérieur,
    puis on les relie en un polygone rempli (avec antialiasing).
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
    Retourne la couleur du cercle d'indice i, en fonction du mode choisi dans settings.
      - "alternating" : utilise la liste de couleurs de manière cyclique
      - "gradient"    : interpole linéairement entre la première et la deuxième couleur de la liste
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
# Classe Particle : Particule pour l'effet de désintégration
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
# Classe Circle : Cercle tournant avec un trou (dessiné en segments lisses)
# =============================================================================
class Circle:
    def __init__(self, x, y, r, hole_angle, hole_size, color, thickness, rotation_speed):
        self.x = x
        self.y = y
        self.r = r
        self.hole_angle = hole_angle      # Angle de base du trou
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


# =============================================================================
# Classe Ball : La balle qui rebondit, subit la gravité et laisse une trainée
# =============================================================================
class Ball:
    def __init__(self, x, y, r, color):
        self.pos = [x, y]
        self.r = r
        self.color = color
        self.vel = [0, 0]
        self.trail = []  # Positions précédentes pour la trainée

    def update(self):
        self.vel[1] += settings['gravity']
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.trail.append(tuple(self.pos))
        if len(self.trail) > settings['ball_trail_length']:
            self.trail.pop(0)

    def draw(self, surface):
        if len(self.trail) > 1:
            for i, pos in enumerate(self.trail):
                alpha = int(255 * (i+1) / len(self.trail))
                color_with_alpha = settings['ball_trail_color'] + (alpha,)
                trail_radius = settings['ball_trail_width']
                trail_surf = pygame.Surface((trail_radius*2, trail_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, color_with_alpha, (trail_radius, trail_radius), trail_radius)
                surface.blit(trail_surf, (pos[0]-trail_radius, pos[1]-trail_radius))
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.r)

    def check_collision(self, circle):
        dx = self.pos[0] - circle.x
        dy = self.pos[1] - circle.y
        d = math.hypot(dx, dy)
        collision_radius = circle.r - circle.thickness / 2
        if d + self.r > collision_radius:
            angle_ball = normalize_angle(math.atan2(dy, dx))
            effective_hole_angle = normalize_angle(circle.hole_angle + circle.rotation)
            gap_start = normalize_angle(effective_hole_angle - circle.hole_size / 2)
            gap_end = normalize_angle(effective_hole_angle + circle.hole_size / 2)
            if is_angle_in_range(angle_ball, gap_start, gap_end):
                return "escape"  # La balle passe par le trou
            else:
                normal = [math.cos(angle_ball), math.sin(angle_ball)]
                dot = self.vel[0]*normal[0] + self.vel[1]*normal[1]
                self.vel[0] -= 2 * dot * normal[0]
                self.vel[1] -= 2 * dot * normal[1]
                self.vel[0] *= settings['ball_elasticity']
                self.vel[1] *= settings['ball_elasticity']
                overlap = (d + self.r) - collision_radius
                self.pos[0] -= normal[0] * overlap
                self.pos[1] -= normal[1] * overlap
        return None


# =============================================================================
# Générateur de particules pour l'effet de désintégration d'un cercle
# =============================================================================
def generate_particles_from_circle(circle):
    for i in range(settings['particle_count']):
        angle = random.uniform(0, 2*math.pi)
        x = circle.x + circle.r * math.cos(angle)
        y = circle.y + circle.r * math.sin(angle)
        speed = random.uniform(1, 3)
        vx = math.cos(angle) * speed + random.uniform(-0.5, 0.5)
        vy = math.sin(angle) * speed + random.uniform(-0.5, 0.5)
        p = Particle(x, y, circle.color)
        p.vel = [vx, vy]
        particles.append(p)


# =============================================================================
# Création des cercles (niveaux)
# =============================================================================
circles = []
radius = settings['base_radius']
total_circles = settings['num_circles']
for i in range(total_circles):
    center_x = width // 2
    center_y = height // 2
    hole_angle = settings['base_hole_angle']
    # Utilisation de la fonction pour déterminer la couleur selon le mode choisi
    circle_color = get_circle_color(i, total_circles)
    rotation_speed = settings['circle_rotation_speed'] + i * settings['circle_rotation_speed_offset']
    circles.append(Circle(center_x, center_y, radius, hole_angle, settings['hole_size'],
                          circle_color, settings['circle_thickness'], rotation_speed))
    radius += settings['radius_increment'] * settings['radius_increment_factor']


# =============================================================================
# Création de la balle
# =============================================================================
ball_start_x = width // 2 + random.uniform(-50, 50)
ball_start_y = height // 2 + random.uniform(-50, 50)
ball = Ball(ball_start_x, ball_start_y, settings['ball_radius'], settings['ball_color'])
angle = random.uniform(0, 2*math.pi)
ball.vel = [math.cos(angle)*settings['ball_speed'], math.sin(angle)*settings['ball_speed']]


# =============================================================================
# Boucle principale
# =============================================================================
running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    ball.update()
    for p in particles:
        p.update()
    particles = [p for p in particles if p.lifetime > 0]

    if circles:
        result = ball.check_collision(circles[0])
        if result == "escape":
            generate_particles_from_circle(circles[0])
            for c in circles:
                c.rotation_speed = -c.rotation_speed
            circles.pop(0)

    for circle in circles:
        circle.update()

    screen.fill(settings['background_color'])
    for circle in reversed(circles):
        circle.draw(screen)
    ball.draw(screen)
    for p in particles:
        p.draw(screen)

    pygame.display.flip()

pygame.quit()
