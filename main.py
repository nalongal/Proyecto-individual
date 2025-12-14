import pygame
from pygame.locals import * #importar constantes de Pygame
from OpenGL.GL import * #importar funciones OpenGL
from OpenGL.GLU import * #importar funciones GLU
import math
import os
import time #importar módulo time para manejo de tiempo

#Llamamos a la carpeta assets que contiene las texturas de los planetas
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

#Definimos la función para cargar texturas
def load_texture(filename):
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
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
#Definimos la función para dibujar esferas texturizadas
def draw_textured_sphere(tex, radius, slices=32, stacks=16):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    quad = gluNewQuadric()
    gluQuadricTexture(quad, True)
    gluSphere(quad, radius, slices, stacks)
    gluDeleteQuadric(quad)
    glDisable(GL_TEXTURE_2D)
#Definimos la función para dibujar anillos texturizados
def draw_ring(tex, inner_r, outer_r, slices=180):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(slices+1):
        t = i / float(slices)
        ang = 2.0 * math.pi * t
        x_in = inner_r * math.cos(ang); z_in = inner_r * math.sin(ang)
        x_out = outer_r * math.cos(ang); z_out = outer_r * math.sin(ang)
        glTexCoord2f(t, 0); glVertex3f(x_in, 0.0, z_in)
        glTexCoord2f(t, 1); glVertex3f(x_out, 0.0, z_out)
    glEnd()
    glDisable(GL_TEXTURE_2D) 
    glDisable(GL_BLEND)

# Planetas: (nombre, textura, radio, distancia al sol, periodo rotación (h), periodo órbita (d))
PLANETS = [
    ("Sun",     "2k_sun.jpg",             2.0,  0.0,    609.12,    1),
    ("Mercury", "2k_mercury.jpg",         0.06, 3.5,   1407.6,    88),
    ("Venus",   "2k_venus_surface.jpg",   0.15, 5.0,  -5832.5,   225),
    ("Earth",   "2k_earth_daymap.jpg",    0.16, 7.0,    23.93,   365),
    ("Mars",    "2k_mars.jpg",            0.09, 9.0,    24.6,    687),
    ("Jupiter", "2k_jupiter.jpg",         0.9,  12.5,    9.9,   4333),
    ("Saturn",  "2k_saturn.jpg",          0.75, 16.0,   10.7,  10759),
    ("Uranus",  "2k_uranus.jpg",          0.40, 19.0,  -17.2,  30687),
    ("Neptune", "2k_neptune.jpg",         0.39, 22.0,   16.1,  60190)
]
#Textura del anillo de Saturno
SATURN_RING = "2k_saturn_ring_alpha.png"

#Clase Cámara con funcionalidad de enfoque suave
def lerp(a, b, t):
    return a + (b - a) * t

# Clase Cámara con funcionalidad de enfoque suave
class Camera:
    def __init__(self):
        self.reset()
    # reinicia cámara a posición inicial
    def reset(self):
        self.distance = 40.0
        self.yaw = 0.0
        self.pitch = -20.0
        self.pan = [0.0, 0.0, 0.0]  #objetivo del lookAt (offset)
        #Para transición suave cuando enfocamos
        self.focusing = False
        self.focus_start = None
        self.focus_duration = 0.8
        self.focus_from = None
        self.focus_to = None
    # inicia enfoque suave hacia target_pos
    def start_focus(self, target_pos, desired_distance=5.0):
        """Inicia una transición suave para enfocar target_pos.
           desired_distance = distancia objetivo respecto al planeta (en unidades de escena).
        """
        cam_pos = self.get_position()  # posición actual de cámara
        # objetivo pan debe ser el punto al que mirar (target_pos)
        to_pan = list(target_pos)
        to_distance = max(1.5, desired_distance)
        # guardamos estado inicial y final
        self.focusing = True
        self.focus_start = time.time()
        self.focus_from = {
            "distance": self.distance,
            "yaw": self.yaw,
            "pitch": self.pitch,
            "pan": list(self.pan)
        }
        # calculamos yaw/pitch que sitúan la cámara a la distancia deseada mirando target_pos, pero para simplicidad mantendremos yaw/pitch actuales y solo moveremos pan+distance
        self.focus_to = {
            "distance": to_distance,
            "yaw": self.yaw,
            "pitch": self.pitch,
            "pan": to_pan
        }
    # actualiza cámara si está en modo enfoque
    def update_focus(self):
        if not self.focusing:
            return
        t = (time.time() - self.focus_start) / max(0.0001, self.focus_duration)
        if t >= 1.0:
            # terminar focus
            self.distance = self.focus_to["distance"]
            self.yaw = self.focus_to["yaw"]
            self.pitch = self.focus_to["pitch"]
            self.pan = list(self.focus_to["pan"])
            self.focusing = False
            return
        # interpolar suavemente
        self.distance = lerp(self.focus_from["distance"], self.focus_to["distance"], t)
        self.yaw = lerp(self.focus_from["yaw"], self.focus_to["yaw"], t)
        self.pitch = lerp(self.focus_from["pitch"], self.focus_to["pitch"], t)
        self.pan = [
            lerp(self.focus_from["pan"][i], self.focus_to["pan"][i], t) for i in range(3)
        ]
    # calcula posición actual de la cámara en función de yaw/pitch/distance/pan
    def get_position(self):
        rad_y = math.radians(self.yaw)
        rad_p = math.radians(self.pitch)
        x = self.pan[0] + self.distance * math.cos(rad_p) * math.sin(rad_y)
        y = self.pan[1] + self.distance * math.sin(rad_p)
        z = self.pan[2] + self.distance * math.cos(rad_p) * math.cos(rad_y)
        return [x, y, z]
    # aplica la transformación de la cámara
    def apply(self):
        self.update_focus()
        pos = self.get_position()
        gluLookAt(pos[0], pos[1], pos[2],
                  self.pan[0], self.pan[1], self.pan[2],
                  0.0, 1.0, 0.0)

#Definimos la función principal
def main():
    pygame.init()
    pygame.display.set_mode((1280, 720), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Sistema Solar - Teclado + Enfoque")
    clock = pygame.time.Clock()

    # configuración OpenGL básica
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1280/720, 0.1, 2000.0)
    glMatrixMode(GL_MODELVIEW)

    # cargar texturas
    textures = {}
    for name, filename, *_ in PLANETS:
        textures[name] = load_texture(filename)
    # carga anillo (si existe)
    ring_tex = None
    ring_path = os.path.join(ASSETS_DIR, SATURN_RING)
    if os.path.exists(ring_path):
        ring_tex = load_texture(SATURN_RING)

    # estado de planetas
    state = {p[0]: {"orbit": 0.0, "rot": 0.0} for p in PLANETS}

    camera = Camera()
    # configuración de escala de tiempo
    TIME_SCALE = 60.0  # acelera el movimiento orbital/rotacional para que se vea
    running = True

    # bucle principal
    while running:
        dt = clock.tick(60) / 1000.0
        scaled_dt = dt * TIME_SCALE

        # manejar eventos
        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False
            elif ev.type == KEYDOWN:
                if ev.key == K_ESCAPE:
                    running = False
                elif ev.key == K_r:
                    camera.reset()
                # teclas 1..9 para enfocar planetas
                elif K_1 <= ev.key <= K_9:
                    idx = ev.key - K_1  # 0-based
                    if idx < len(PLANETS):
                        # calcular posición actual del planeta idx
                        pname, _, pradius, pdist, _, _ = PLANETS[idx]
                        # Posición en su órbita:
                        ang = math.radians(state[pname]["orbit"])
                        px = math.cos(ang) * pdist
                        pz = math.sin(ang) * pdist
                        py = 0.0
                        # desired_distance: queremos acercarnos hasta ~2 radios del planeta (pero nunca menos)
                        desired = max(pradius * 2.5, 1.5)
                        camera.start_focus((px, py, pz), desired_distance=desired)

        # manejar entrada de teclado para controlar cámara
        keys = pygame.key.get_pressed()
        # Rotar cámara (izq/der/arr/abajo)
        if keys[K_LEFT]:
            camera.yaw -= 60.0 * dt
        if keys[K_RIGHT]:
            camera.yaw += 60.0 * dt
        if keys[K_UP]:
            camera.pitch += 40.0 * dt
            camera.pitch = max(-89.0, min(89.0, camera.pitch))
        if keys[K_DOWN]:
            camera.pitch -= 40.0 * dt
            camera.pitch = max(-89.0, min(89.0, camera.pitch))

        # Zoom in/out (+/-)
        if keys[K_EQUALS] or keys[K_PLUS]:
            camera.distance -= 30.0 * dt
            camera.distance = max(1.5, camera.distance)
        if keys[K_MINUS] or keys[K_UNDERSCORE]:
            camera.distance += 30.0 * dt

        # Panning (A/D/W/S para izquierda/derecha/adelante/atrás, Q/E para subir/bajar)
        pan_speed = 10.0 * dt * (camera.distance / 20.0)
        if keys[K_a]:
            camera.pan[0] -= pan_speed
        if keys[K_d]:
            camera.pan[0] += pan_speed
        if keys[K_w]:
            camera.pan[2] -= pan_speed
        if keys[K_s]:
            camera.pan[2] += pan_speed
        if keys[K_q]:
            camera.pan[1] += pan_speed   # subir
        if keys[K_e]:
            camera.pan[1] -= pan_speed   # bajar

        # actualizar estado planetas (órbita y rotación)
        for (name, _, radius, dist, rot_h, orb_d) in PLANETS:
            if orb_d > 0:
                orbital_deg_per_sec = 360.0 / (orb_d * 24.0 * 3600.0)
                state[name]["orbit"] += orbital_deg_per_sec * scaled_dt
            if rot_h != 0:
                rot_deg_per_sec = 360.0 / (abs(rot_h) * 3600.0)
                if rot_h < 0:
                    state[name]["rot"] -= rot_deg_per_sec * scaled_dt
                else:
                    state[name]["rot"] += rot_deg_per_sec * scaled_dt
            state[name]["orbit"] %= 360.0
            state[name]["rot"] %= 360.0

        # renderizar escena
        glClearColor(0.02, 0.02, 0.03, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        camera.apply()

        # sol (centro del sistema)
        glPushMatrix()
        glDisable(GL_LIGHTING)
        draw_textured_sphere(textures["Sun"], PLANETS[0][2], 40, 40)
        glEnable(GL_LIGHTING)
        glPopMatrix()

        # planetas
        for name, _, radius, dist, _, _ in PLANETS[1:]:
            ang = math.radians(state[name]["orbit"])
            x = math.cos(ang) * dist
            z = math.sin(ang) * dist
            glPushMatrix()
            glTranslatef(x, 0.0, z)
            glRotatef(state[name]["rot"], 0.0, 1.0, 0.0)
            draw_textured_sphere(textures[name], radius)
            glPopMatrix()

        # anillo Saturno 
        sat = next((p for p in PLANETS if p[0] == "Saturn"), None)
        if sat:
            _, _, srad, sdist, _, _ = sat
            s_ang = math.radians(state["Saturn"]["orbit"])
            sx = math.cos(s_ang) * sdist
            sz = math.sin(s_ang) * sdist
            glPushMatrix()
            glTranslatef(sx, 0.0, sz)
            glRotatef(20.0, 1.0, 0.0, 0.0)
            if ring_tex:
                draw_ring(ring_tex, srad * 1.2, srad * 3.0, slices=360)
            glPopMatrix()
        # intercambiar buffers (los buffers son dobles)
        pygame.display.flip()
    # salir
    pygame.quit()

# Ejecutar la función principal
if __name__ == "__main__":
    main()
