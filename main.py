import pygame #Para gráficos y manejo de ventanas
from pygame.locals import * #Para eventos y configuración
from OpenGL.GL import * #Para gráficos 3D
from OpenGL.GLU import * 
import math
import os
import time #Para funciones de tiempo y animaciones

#Utilizar la carpeta 'assets' para cargar texturas
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

#Función para cargar texturas desde archivos
def load_texture(filename):
    path = os.path.join(ASSETS_DIR, filename)
    surf = pygame.image.load(path).convert_alpha()
    w, h = surf.get_size()
    data = pygame.image.tostring(surf, "RGBA", True)

    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return tid

#Función para dibujar una esfera texturizada
def draw_textured_sphere(tex, radius, slices=32, stacks=16):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    quad = gluNewQuadric()
    gluQuadricTexture(quad, True)
    gluSphere(quad, radius, slices, stacks)
    gluDeleteQuadric(quad)
    glDisable(GL_TEXTURE_2D)

# Función para dibujar un anillo texturizado
def draw_ring(tex, inner_r, outer_r, slices=180):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    glBegin(GL_TRIANGLE_STRIP)
    # Dibujamos el anillo usando un TRIANGLE_STRIP
    for i in range(slices + 1):
        t = i / slices
        ang = 2 * math.pi * t
        glTexCoord2f(t, 0)
        glVertex3f(math.cos(ang) * inner_r, 0, math.sin(ang) * inner_r)
        glTexCoord2f(t, 1)
        glVertex3f(math.cos(ang) * outer_r, 0, math.sin(ang) * outer_r)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)

# Función para dibujar la órbita de un planeta
def draw_orbit(radius, segments=180):
    glDisable(GL_LIGHTING)
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_LINE_LOOP)
    # Dibujamos un círculo en el plano XZ
    for i in range(segments):
        ang = 2 * math.pi * i / segments
        glVertex3f(math.cos(ang) * radius, 0, math.sin(ang) * radius)
    glEnd()
    glEnable(GL_LIGHTING)

#Definición de planetas con sus propiedades y texturas
PLANETS = [
    ("Sun", "2k_sun.jpg", 2.0, 0.0, 609.12, 1),
    ("Mercury", "2k_mercury.jpg", 0.06, 3.5, 1407.6, 88),
    ("Venus", "2k_venus_surface.jpg", 0.15, 5.0, -5832.5, 225),
    ("Earth", "2k_earth_daymap.jpg", 0.16, 7.0, 23.93, 365),
    ("Mars", "2k_mars.jpg", 0.09, 9.0, 24.6, 687),
    ("Jupiter", "2k_jupiter.jpg", 0.9, 12.5, 9.9, 4333),
    ("Saturn", "2k_saturn.jpg", 0.75, 16.0, 10.7, 10759),
    ("Uranus", "2k_uranus.jpg", 0.40, 19.0, -17.2, 30687),
    ("Neptune", "2k_neptune.jpg", 0.39, 22.0, 16.1, 60190)
]
# Definición de la inclinación axial de los planetas
AXIAL_TILT = {
    "Mercury": 0.03,
    "Venus": 177.4,
    "Earth": 23.44,
    "Mars": 25.19,
    "Jupiter": 3.13,
    "Saturn": 26.73,
    "Uranus": 97.77,
    "Neptune": 28.32
}
# Textura del anillo de Saturno
SATURN_RING = "2k_saturn_ring_alpha.png"


#Definición de la clase Cámara para manejar vistas y animaciones
def lerp(a, b, t):
    return a + (b - a) * t

#Creamos una clase Cámara para manejar la vista y animaciones
class Camera:
    def __init__(self):
        self.reset()
    # Método para reiniciar la cámara a su estado inicial
    def reset(self):
        self.distance = 40.0
        self.yaw = 0.0
        self.pitch = -20.0
        self.pan = [0.0, 0.0, 0.0]
        self.focusing = False
        self.focus_start = None
        self.focus_duration = 0.8
        self.focus_from = None
        self.focus_to = None
    # Método para iniciar el enfoque hacia una posición objetivo
    def start_focus(self, target_pos, desired_distance=5.0):
        self.focusing = True
        self.focus_start = time.time()
        self.focus_from = {
            "distance": self.distance,
            "yaw": self.yaw,
            "pitch": self.pitch,
            "pan": list(self.pan)
        }
        self.focus_to = {
            "distance": max(1.5, desired_distance),
            "yaw": self.yaw,
            "pitch": self.pitch,
            "pan": list(target_pos)
        }
    # Método para actualizar la posición de la cámara durante el enfoque
    def update_focus(self): 
        if not self.focusing:
            return
        t = (time.time() - self.focus_start) / self.focus_duration
        if t >= 1: 
            self.distance = self.focus_to["distance"]
            self.pan = self.focus_to["pan"]
            self.focusing = False
            return
        self.distance = lerp(self.focus_from["distance"], self.focus_to["distance"], t)
        self.pan = [
            lerp(self.focus_from["pan"][i], self.focus_to["pan"][i], t)
            for i in range(3)
        ]
    # Método para calcular la posición actual de la cámara
    def get_position(self):
        ry = math.radians(self.yaw)
        rp = math.radians(self.pitch)
        return [
            self.pan[0] + self.distance * math.cos(rp) * math.sin(ry),
            self.pan[1] + self.distance * math.sin(rp),
            self.pan[2] + self.distance * math.cos(rp) * math.cos(ry)
        ]
    # Método para aplicar la transformación de la cámara en OpenGL
    def apply(self):
        self.update_focus()
        pos = self.get_position()
        gluLookAt(*pos, *self.pan, 0, 1, 0)

#Definimos la función principal del programa que se encarga de la inicialización y el bucle principal
def main():
    pygame.init()
    pygame.display.set_mode((1280, 720), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Sistema Solar – TODO INTEGRADO")

    # Configuración de OpenGL
    clock = pygame.time.Clock()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    # Configuración de la luz
    glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 0, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.05, 0.05, 0.05, 1))

    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 1280 / 720, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    
    # Carga de texturas
    textures = {p[0]: load_texture(p[1]) for p in PLANETS}
    ring_tex = load_texture(SATURN_RING)

    # Estado inicial de los planetas
    state = {p[0]: {"orbit": 0.0, "rot": 0.0} for p in PLANETS}

    camera = Camera()
    TIME_SCALE = 3600.0  # 1s = 1h real

    # Bucle principal
    running = True
    while running:
        dt = clock.tick(60) / 1000
        sim_dt = dt * TIME_SCALE

        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                running = False
            elif e.type == KEYDOWN and K_1 <= e.key <= K_9:
                idx = e.key - K_1
                name, _, r, d, _, _ = PLANETS[idx]
                ang = math.radians(state[name]["orbit"])
                camera.start_focus(
                    (math.cos(ang) * d, 0, math.sin(ang) * d),
                    max(r * 3, 1.5)
                )

        # Manejo de entrada para controlar la cámara
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            camera.yaw -= 60 * dt
        if keys[K_RIGHT]:
            camera.yaw += 60 * dt
        if keys[K_UP]:
            camera.pitch += 40 * dt
        if keys[K_DOWN]:
            camera.pitch -= 40 * dt

        # Limitamos el pitch para evitar giros incómodos
        if keys[K_EQUALS] or keys[K_PLUS]:
            camera.distance = max(1.5, camera.distance - 30 * dt)
        if keys[K_MINUS] or keys[K_UNDERSCORE]:
            camera.distance += 30 * dt
        # Movimiento de paneo con WASD y QE
        pan_speed = 10 * dt * (camera.distance / 20)
        if keys[K_a]:
            camera.pan[0] -= pan_speed
        if keys[K_d]:
            camera.pan[0] += pan_speed
        if keys[K_w]:
            camera.pan[2] -= pan_speed
        if keys[K_s]:
            camera.pan[2] += pan_speed
        if keys[K_q]:
            camera.pan[1] += pan_speed
        if keys[K_e]:
            camera.pan[1] -= pan_speed

       #Definimos la rotación y órbita de cada planeta
        for name, _, _, _, rot_h, orb_d in PLANETS:
            if rot_h != 0:
                deg = 360 / (abs(rot_h) * 3600)
                state[name]["rot"] += deg * sim_dt * (-1 if rot_h < 0 else 1)
            if orb_d > 0:
                state[name]["orbit"] += 360 / (orb_d * 86400) * sim_dt

        # Renderizado de la escena
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        camera.apply()

        # Dibujamos las órbitas de los planetas
        for _, _, _, dist, _, _ in PLANETS[1:]:
            draw_orbit(dist)

        glDisable(GL_LIGHTING)
        draw_textured_sphere(textures["Sun"], 2.0, 40, 40)
        glEnable(GL_LIGHTING)

        # Dibujamos los planetas
        for name, _, r, d, _, _ in PLANETS[1:]:
            ang = math.radians(state[name]["orbit"])
            glPushMatrix()
            glTranslatef(math.cos(ang) * d, 0, math.sin(ang) * d)
            glRotatef(AXIAL_TILT.get(name, 0), 0, 0, 1)
            glRotatef(state[name]["rot"], 0, 1, 0)
            draw_textured_sphere(textures[name], r)
            glPopMatrix()

        # Dibujamos el anillo de Saturno
        ang = math.radians(state["Saturn"]["orbit"])
        glPushMatrix()
        glTranslatef(math.cos(ang) * 16, 0, math.sin(ang) * 16)
        glRotatef(26.73, 0, 0, 1)
        draw_ring(ring_tex, 0.9, 2.5, 360)
        glPopMatrix()

        pygame.display.flip()
    
    # Limpiamos y cerramos Pygame
    pygame.quit()

# Ejecutamos la función principal si el script es ejecutado directamente
if __name__ == "__main__":
    main()
