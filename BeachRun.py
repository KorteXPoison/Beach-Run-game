import time
import pygame
from core.obj_reader import my_obj_reader
import numpy as np
import math
import pathlib
import sys
import random


from extras.text_texture import TextTexture
from geometry.custom import CustomGeometry
from light.directional import DirectionalLight
from light.ambient import AmbientLight
from extras.directional_light import DirectionalLightHelper
from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from extras.axes import AxesHelper
from extras.movement_rig import MovementRig
from extras.movement_rig2 import MovementRig2
from material.surface import SurfaceMaterial
from core_ext.texture import Texture
from material.texture import TextureMaterial
from geometry.rectangle import RectangleGeometry
from geometry.sphere import SphereGeometry
from material.phong import PhongMaterial
from material.lambert import LambertMaterial
from core_ext.object3d import Object3D


class Player3D(Mesh):
    def __init__(self, geometry, material):
        super().__init__(geometry, material)
        self.speed = 0.027 # Adjust the speed as needed
        self.gravity = 0.01  # Adjust the gravity force
        self.floor_limit = 3 # Set the limit of the floor
        self.max_speed = 0.027
        self.acceleration = 0.002
        self.deceleration = 0.001
        self._direction = np.array([0.0, 0.0, 0.0])
        self.is_jumping = False  # To track jumping state
        self.jump_speed = 0.13  # Adjust the jump speed as needed
        self.vertical_speed = 0.0  # Vertical speed due to jump or gravity

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, new_direction):
            if np.linalg.norm(new_direction) > 0:
                self._direction = new_direction / np.linalg.norm(new_direction)
            else:
                self._direction = new_direction

    def move(self, direction):
        if np.linalg.norm(direction) > 0:
            self.direction = direction
        self.speed = min(self.speed + self.acceleration, self.max_speed)
        movement = self.direction * self.speed
        self.translate(movement[0], 0, movement[2])

    def apply_gravity(self):
       if not self.is_jumping:  # Only apply gravity if not jumping
            if self.global_position[1] > self.floor_limit:
                self.translate(0, -self.gravity, 0)
            else:
                self.vertical_speed = 0.0  # Reset vertical speed when on the floor

    def jump(self):
        if not self.is_jumping and self.global_position[1] <= self.floor_limit + 0.1:
            self.is_jumping = True
            self.vertical_speed = self.jump_speed

    def jumpI(self):
        self.vertical_speed = self.jump_speed

    def update(self):
        if self.is_jumping:
            self.translate(0, self.vertical_speed, 0)
            self.vertical_speed -= self.gravity
            if self.global_position[1] <= self.floor_limit:
                self.is_jumping = False
                self.set_position([self.global_position[0], self.floor_limit, self.global_position[2]])
        self.apply_gravity()
        
        # Decelerate if no input is given
        if np.linalg.norm(self.direction) == 0:
            self.speed = max(self.speed - self.deceleration, 0)
        else:
            self.move(self.direction)

        if self.speed > 0:
            self.translate(self.direction[0] * self.speed, 0, self.direction[2] * self.speed)        
        # Limit position within bounds
        self.limit_position()

    def limit_position(self):
        if self.global_position[0] > 10:
            self.set_position([10, self.global_position[1], self.global_position[2]])
        if self.global_position[0] < -10:
            self.set_position([-10, self.global_position[1], self.global_position[2]])
        if self.global_position[2] < -65:
            self.set_position([self.global_position[0], self.global_position[1], -65])


    def get_position(self):
        return self.global_position


class Obstacle3D(Object3D):
    def __init__(self, geometry, material, position):
        super().__init__()
        self._mesh = Mesh(geometry, material)
        self.add(self._mesh)
        self.set_position(position)

    def translate(self, vector):
        current_position = self.local_position
        new_position = (
            current_position[0] + vector[0],
            current_position[1] + vector[1],
            current_position[2] + vector[2],
        )
        self.set_position(new_position)

    def get_position(self):
        return self.global_position


class Example(Base):

    def initialize(self):
        print("Initializing program...")
        self.game_state = "running"
        self.game_over_message = ""
        self.points = 0
        self.renderer = Renderer()
        self.scene = Scene()
        self.camera = Camera(aspect_ratio=16 / 9)
        self.camera.set_position([2, 3, 10])
        self.directional_light = DirectionalLight(color=[1, 1, 1], direction=[0, 1, 1])
        self.ambient_light = AmbientLight(color=[0.7, 0.7, 0.7])
        self.score = 0
        self.docks = []
        self.collect_hat_sound = pygame.mixer.Sound("sounds/collect-points.mp3")
        self.collision_sound = pygame.mixer.Sound("sounds/collision.mp3")
        self.waves_sound = pygame.mixer.Sound("sounds/soft-waves.mp3")
        sound_volume = 0.5
        self.waves_sound.set_volume(sound_volume)
        self.waves_sound.play(loops=-1)
        self.ball_bounce_sound = pygame.mixer.Sound("sounds/ball-bounce.wav")

        # Load object data
        obj_files = {
            "bucket": "bucket.obj",
            "ball": "bola.obj",
            "umbrella": "sombrinha.obj",
            "hat": "chapeu.obj",
            "boat": "boat.obj",
            "dock": "dock.obj",
            "pinheiro": "palm.obj",
            "flag": "flag.obj"
        }
        
        bucket_vertices, bucket_uvs = my_obj_reader(obj_files["bucket"])
        ball_vertices, ball_uvs = my_obj_reader(obj_files["ball"])
        umbrella_vertices, umbrella_uvs = my_obj_reader(obj_files["umbrella"])
        hat_vertices, hat_uvs = my_obj_reader(obj_files["hat"])
        boat_vertices, boat_uvs = my_obj_reader(obj_files["boat"])
        pinheiro_vertices, pinheiro_uvs = my_obj_reader(obj_files["pinheiro"])
        dock_vertices, dock_uvs = my_obj_reader(obj_files["dock"])
        flag_vertices, flag_uvs = my_obj_reader(obj_files["flag"])

        # Create geometries and materials
        bucket_geometry = CustomGeometry(bucket_vertices, bucket_uvs)
        ball_geometry = SphereGeometry(radius=0.3)
        umbrella_geometry = CustomGeometry(umbrella_vertices, umbrella_uvs)
        hat_geometry = CustomGeometry(hat_vertices, hat_uvs)
        boat_geometry = CustomGeometry(boat_vertices, boat_uvs)
        pinheiro_geometry = CustomGeometry(pinheiro_vertices, pinheiro_uvs)
        dock_geometry = CustomGeometry(dock_vertices, dock_uvs)
        flag_geometry = CustomGeometry(flag_vertices, flag_uvs)
        
        umbrella_texture = Texture(file_name="images/umb.jpg")
        blueumb = Texture(file_name="images/blueumb.jpg")
        hat_texture = Texture(file_name="images/hat.jpg")
        ball_texture = Texture(file_name="images/ball.jpg")
        bucketTexture = Texture(file_name="images/bucket.jpg")
        boat_texture = Texture(file_name="images/wood.jpg")
        pinheiro_texture = Texture(file_name="images/texturetest.jpg")
        dock_texture = Texture(file_name="images/wood.jpg")
        flag_texture = Texture(file_name="images/flag.jpg")
        material = LambertMaterial(
            texture=bucketTexture, number_of_light_sources=2
        )
        ball_mat = PhongMaterial(
            texture=ball_texture, number_of_light_sources=2,rotation_axis=True
        )
        blueumb_mat = PhongMaterial(
            texture=blueumb, number_of_light_sources=2
        )
        umb_mat = PhongMaterial(
            texture=umbrella_texture, number_of_light_sources=2
        )
        hat_mat = PhongMaterial(
            texture=hat_texture, number_of_light_sources=2
        )
        boat_mat = PhongMaterial(
            texture=boat_texture, number_of_light_sources=2
        )
        pinheiro_mat = PhongMaterial(
            texture=pinheiro_texture, number_of_light_sources=2
        )
        dock_mat = PhongMaterial(
            texture=dock_texture, number_of_light_sources=2
        )
        flag_mat = PhongMaterial(
            texture=flag_texture, number_of_light_sources=2
        )
        self.player = Player3D(ball_geometry, ball_mat)
        self.player.set_position([0, 3, 62])  # Set initial position
        self.player.scale(2)
        self.scene.add(self.player)

        #Create meshes
        hat = Mesh(hat_geometry, hat_mat)
        umb = Mesh(umbrella_geometry, umb_mat)
        self.boat = Mesh(boat_geometry, boat_mat)
        self.boat1 = Mesh(boat_geometry, boat_mat)
        pinheiro = Mesh(pinheiro_geometry, pinheiro_mat)
        pinheiro.set_position([-10,0,5])
        pinheiro.scale(0.01)
        pinheiro.rotate_x(-math.pi/2)
        dock = Mesh(dock_geometry, dock_mat)
        flag = Mesh(flag_geometry, flag_mat)
        flag.scale(0.95)
        flag.set_position([0, 5, -65])
        self.scene.add(flag)
        pinheiro.set_position([-4,3,-2])
        pinheiro.scale(0.5)
        hat.set_position([0, 0.7, 3])
        umb.set_position([2, 2, 6])
        self.boat.set_position([-20, 1, -30])
        self.boat1.set_position([18, 1, -30])
        self.boat.rotate_y(math.pi/2)
        self.boat1.rotate_y(math.pi/2)
        dock.set_position([0, 2, -30])
        dock.scale(5)
        umb.scale(3)

        self.rig = MovementRig()
        self.rig2 = MovementRig2()

        #self.scene.add(hat)
        #self.scene.add(umb)
        self.scene.add(self.boat)
        self.scene.add(self.boat1)
        self.scene.add(dock)
        self.docks.append(dock)  # Add dock to the list for collision detection
        self.rig2.add(self.camera)
        self.rig2.set_position([0, 1, 4])
        self.scene.add(self.rig2)

        dock_positions = [[0, 2, 30], [0, 2, 54], [0, 2, -54]]
        for pos in dock_positions:
            new_dock = Mesh(dock_geometry, dock_mat)
            new_dock.set_position(pos)
            new_dock.scale(5)
            self.docks.append(new_dock)
            self.scene.add(new_dock)

        self.scene.add(self.directional_light)
        self.scene.add(self.ambient_light)

        self.obstacles = []
        self.hats = []
        self.umbrellas_between_dock = []
        for i in range(20):  # Add multiple obstacles
            obstacle = Obstacle3D(
                bucket_geometry,
                LambertMaterial(texture=bucketTexture, number_of_light_sources=2),
                [random.uniform(-4.1, 4.1), 2.5, -i*2.4-12],
            )
            obstacle.scale(0.4)
            self.obstacles.append(obstacle)
            self.scene.add(obstacle)
        for i in range(15):  # Add multiple obstacles
            obstacle = Obstacle3D(
                bucket_geometry,
                LambertMaterial(texture=bucketTexture, number_of_light_sources=2),
                [random.uniform(-4.1, 4.1), 2.5, i*2.4+12],
            )
            obstacle.scale(0.4)
            self.obstacles.append(obstacle)
            self.scene.add(obstacle)
        for i in range(20):  # Add multiple obstacles
            hat = Obstacle3D(
                hat_geometry,
                LambertMaterial(texture=hat_texture, number_of_light_sources=2),
                [random.uniform(-4.1, 4.1), random.uniform(2.5, 4), -i*2.4-12],
            )
            hat.scale(2)
            self.hats.append(hat)
            self.scene.add(hat)
        for i in range(15):  # Add multiple obstacles
            hat = Obstacle3D(
                hat_geometry,
                LambertMaterial(texture=hat_texture, number_of_light_sources=2),
                [random.uniform(-4.1, 4.1), random.uniform(2.5, 4), i*2.4+12],
            )
            hat.scale(2)
            self.hats.append(hat)
            self.scene.add(hat)
        fixed_x_positions = [0, -1.75, 0, 1.75, 3.5]
        selected_positions = []
        for i in range(5):  # Add multiple obstacles
            x_position = random.choice(fixed_x_positions)
            umbrella = Obstacle3D(
                umbrella_geometry,
                LambertMaterial(texture=blueumb, number_of_light_sources=2),
                [x_position, 1.5, i*4-7],
            )
            fixed_x_positions.remove(x_position)
            selected_positions.append(x_position)
            umbrella.scale(2)
            self.umbrellas_between_dock.append(umbrella)
            self.scene.add(umbrella)
        for i in range(5):  # Add multiple obstacles
            x_position = selected_positions[i]
            hat = Obstacle3D(
                hat_geometry,
                LambertMaterial(texture=hat_texture, number_of_light_sources=2),
                [x_position, 5, i*4-7],
            )
            hat.scale(2)
            self.hats.append(hat)
            self.scene.add(hat)
        for i in range(30):  # Adjust the number of trees as needed
            palm_tree = Mesh(pinheiro_geometry, pinheiro_mat)
            if (i%2 == 0):
                palm_tree.set_position([
                    random.uniform(-60, -8),  # x coordinate
                    0,                       # y coordinate (fixed)
                    random.uniform(0, 45)    # z coordinate
                ])
            else:
                palm_tree.set_position([
                    random.uniform(8, 60),  # x coordinate
                    0,                       # y coordinate (fixed)
                    random.uniform(0, 45)    # z coordinate
                ])
            palm_tree.scale(0.01)  # Adjust the scale if needed
            palm_tree.rotate_x(-math.pi/2)
            self.scene.add(palm_tree)

        for i in range(30):  # Adjust the number of trees as needed
            umbrella = Mesh(umbrella_geometry, umb_mat)
            if (i%2 == 0):
                umbrella.set_position([
                    random.uniform(-60, -8),  # x coordinate
                    0.8,                       # y coordinate (fixed)
                    random.uniform(0, 45)    # z coordinate
                ])
            else:
                umbrella.set_position([
                    random.uniform(8, 60),  # x coordinate
                    0.8,                       # y coordinate (fixed)
                    random.uniform(0, 45)    # z coordinate
                ])
            umbrella.scale(3)
            self.scene.add(umbrella)

        directional_light_helper = DirectionalLightHelper(
            self.directional_light
        )
        self.directional_light.set_position([0, 40, 10])
        self.directional_light.add(directional_light_helper)

        sky_geometry = SphereGeometry(radius=100)
        sky_material = PhongMaterial(
            texture=Texture(file_name="images/sky.png"),
            number_of_light_sources=2,
        )
        sky = Mesh(sky_geometry, sky_material)
        self.scene.add(sky)

        grass_geometry = RectangleGeometry(width=200, height=200)
        grass_material = PhongMaterial(
            texture=Texture(file_name="images/aisandsea.jpg"),
            number_of_light_sources=2,
            rotation_axis=True,
            rotation_speed=0.3
        )
        self.grass = Mesh(grass_geometry, grass_material)
        self.grass.rotate_x(-math.pi / 2)
        self.scene.add(self.grass)
        self.create_score_label()
        self.start_time = time.time()

    def create_score_label(self):
        self.score_text_texture = TextTexture(
            text=f"Score: {self.score}",
            system_font_name="Arial Bold",
            font_size=40,
            font_color=[255, 255, 255],
            transparent=True,
            image_width=256,
            image_height=128,
            align_horizontal=0.5,
            align_vertical=0.5
        )

        self.score_label_material = TextureMaterial(self.score_text_texture)
        self.score_label_geometry = RectangleGeometry(width=2, height=1)
        self.score_label = Mesh(self.score_label_geometry, self.score_label_material) 
        self.score_label.scale(3)
        self.scene.add(self.score_label)

    def update_score_label(self):
        self.score_text_texture.update_text(f"Score: {self.score}")

    def update(self):
        if self.game_state == "running":
            self.player.move(np.array([0.0, 0.0, -1.0]))
            self.player.apply_gravity()
            self.player.update()
            current_time = time.time() - self.start_time  # Calculate elapsed time
            self.player.material.uniform_dict["time"].data = current_time  # Update the time uniform
            self.grass.material.uniform_dict["time"].data = current_time*0.5
            self.boat.translate(0, 0, 0.2*math.sin(self.time))
            self.boat1.translate(0, 0, -0.2*math.sin(self.time))

            player_position = self.player.global_position
            self.camera.set_position(
                [player_position[0], player_position[1] + 3, player_position[2] + 7]
            )
            self.score_label.set_position(
                [player_position[0] + 5, player_position[1] + 8, player_position[2] + 2]
            )
            keys = pygame.key.get_pressed()
            direction = np.array([0.0, 0.0, 0.0])

            # Modify direction based on key presses
            if keys[pygame.K_SPACE]:
                self.player.jump() # Jump
            if keys[pygame.K_a]:
                direction += np.array([-1.5, 0.0, 0.0])  # Move left
            if keys[pygame.K_d]:
                direction += np.array([1.5, 0.0, 0.0])  # Move right

            #self.player.direction = direction  # Set player's direction
            self.player.direction = direction

            self.player.update()

            self.update_score_label()

            self.rig.update(self.input, self.delta_time)
            self.rig2.update(self.input, self.delta_time)
            self.directional_light.set_direction(
                [0, math.sin(0.1 * self.time), 1]
            )
            # Check for collisions
            for obstacle in self.obstacles:
                obstacle_pos = obstacle.global_position
                if np.linalg.norm(
                    np.array(player_position) - np.array(obstacle_pos)
                ) < 1.0:  # Adjust collision threshold
                    pygame.mixer.Sound.play(self.collision_sound)
                    print("Game Over!")
                    time.sleep(0.2)
                    self.game_state = "game_over"
                    self.game_over_message = "Game Over!"
                    return
            
            for hat in self.hats:
                hat_pos = hat.global_position
                if np.linalg.norm(
                    np.array(player_position) - np.array(hat_pos)
                ) < 1.0: 
                    self.score += 1
                    self.scene.remove(hat)  # Remove hat from the scene
                    self.hats.remove(hat)  # Remove hat from the list
                    print(f"Hat collected! Current score: {self.score}")
                    pygame.mixer.Sound.play(self.collect_hat_sound)
            
            for umbrella in self.umbrellas_between_dock:
                umbrella_pos = umbrella.global_position
                if np.linalg.norm(
                    np.array(player_position) - np.array(umbrella_pos)
                ) < 2:
                    pygame.mixer.Sound.play(self.ball_bounce_sound)
                    self.player.is_jumping = False 
                    self.player.jumpI()
            # Check for collisions with the dock
            on_dock = False
            for dock in self.docks:
                dock_pos = dock.global_position
                if np.linalg.norm(
                    np.array(player_position[0]) - np.array(dock_pos[0])
                ) < 5.8 and (player_position[2] < -12 or player_position[2] > 12):  # Adjust collision threshold as needed
                    on_dock = True
                    break

            if not on_dock:
                self.player.is_jumping = True
                self.player.floor_limit = 0.5
                self.player.gravity=0.005
                self.max_speed = 0.01
                self.speed = 0.01
            else:
                self.player.gravity=0.01
                self.player.floor_limit = 3
                self.max_speed=0.02
                self.speed=0.02
            # Check if player reaches Z=5 and touches sea
            if player_position[1] < 1:
                print("Game Over! Player can't touch the sand or the sea")
                self.game_state = "game_over"
                self.game_over_message = "Game Over!"
                return
            if player_position[2] <= -65:
                print("Total score: ", self.score )
                self.game_state = "game_over"
                self.game_over_message = f"Total Score: {self.score}"
                return

            self.renderer.render(self.scene, self.camera)
        elif self.game_state == "game_over":
            self.display_game_over_screen(self.game_over_message)


    def display_game_over_screen(self, message):
        screen_width, screen_height = get_screen_size()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 74)
        text = font.render(message, True, (255, 255, 255))
        self.screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 4))

        small_font = pygame.font.Font(None, 50)
        try_again_text = small_font.render("Try Again", True, (0, 255, 0))
        exit_text = small_font.render("Exit", True, (255, 0, 0))
        try_again_rect = try_again_text.get_rect(center=(screen_width // 2, screen_height // 2))
        exit_rect = exit_text.get_rect(center=(screen_width // 2, screen_height // 2 + 100))

        self.screen.blit(try_again_text, try_again_rect)
        self.screen.blit(exit_text, exit_rect)

        pygame.display.flip()

        while self.game_state == "game_over":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if try_again_rect.collidepoint(event.pos):
                        self.game_state = "running"
                        Example(screen_size=[screen_width, screen_height]).run()  # Restart the game
                    elif exit_rect.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

def get_screen_size():
    pygame.init()
    screen_info = pygame.display.Info()
    return screen_info.current_w, screen_info.current_h

# Instantiate this class and run the program
screen_width, screen_height = get_screen_size()
Example(screen_size=[screen_width, screen_height]).run()