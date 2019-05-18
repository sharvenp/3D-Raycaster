
import pygame as pg
import math
import time
from PIL import Image

rad = math.radians
deg = math.degrees

class Player():

    """
    Player Class
    Controls Position, Movement and Rotation of player
    """

    def __init__(self, x, y):
        
        self.x = x
        self.y = y

        self.movement_speed = 2
        self.angular_speed = 7.5

        self.curr_dx = 0
        self.curr_dy = 0
        self.angle = 0

    def move(self, h, v):

        self.x = round(self.x + h)
        self.y = round(self.y + v)

    def rotate(self, rot):
        
        self.angle += rot
        self.angle %= 360

class Renderer:

    """
    3D Renderer Class
    Handles all display stuff
    """

    def __init__(self, height, fov_angle, fov_radius, scale=1):

        self.FRAME_RATE = 60

        self.WIDTH = round(math.sqrt(2) * fov_radius * (1 - (math.cos(rad(fov_angle)))))
        self.HEIGHT = height
        self.WALL_SCALING = self.HEIGHT//2
        self.TOP_DOWN_SCALE = scale

        self.FLOOR_COLOR = (30, 30, 30)
        self.CEILING_COLOR = (70, 0, 0)
        self.WALL_COLOR = (255, 255, 255)
        self.PLAYER_COLOR = (255, 0, 0)
        self.RAYCAST_LINE_COLOR = (102, 0, 166)

        self.level_map = []

        self.fov_angle = fov_angle
        self.fov_radius = fov_radius
        self.raycast_step = fov_angle/(90)

        print("Loading Map...")
        im = Image.open('data/map.png')
        pix = im.load()

        for col in range(im.size[0]):
            a = []
            for row in range(im.size[1]):
                if pix[row, col] == (255, 255, 255, 255):
                    a.append(1)
                else:
                    a.append(0)
            self.level_map.append(a)
        print("Map Loaded.")

        self.level_height = len(self.level_map)
        self.level_width = len(self.level_map[0])

    def get_distance(self, x0, y0, x1, y1):

        return math.sqrt(((x1 - x0)**2) + ((y1 - y0)**2))

    def get_blocks(self, x0, y0, x1, y1):
        
        # Bresenham's line algorithm

        blocks = []

        s = abs(x1 - x0) < abs(y1 - y0)
        if s:
            x0, y0 = y0, x0
            x1, y1 = y1, x1

        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0

        dx = x1 - x0
        dy = abs(y1 - y0)
        e = 0
        ystep = 0
        if y1 != y0:
            ystep = (y1 - y0)//abs(y1 - y0)
        y = y0
        
        for x in range(x0, x1): 
            if s: 
                blocks.append((y, x));
            else:
                blocks.append((x, y));

            e += dy;
            if dx <= 2*e:
                y += ystep
                e -= dx

        return blocks

    def cast_ray(self, x, y, angle):
    
        # Append all blocks that are not on a wall

        dx = math.cos(rad(angle)) * self.fov_radius
        dy = math.sin(rad(angle)) * self.fov_radius

        blocks = self.get_blocks(x, y, round(x + dx), round(y + dy))

        new_blocks = []

        if blocks[0] != (x, y):
            blocks = blocks[::-1]

        for block in blocks:

            c, r = block

            if c >= self.level_width or r >= self.level_height or r < 0 or c < 0:
                break

            if self.level_map[r][c] != 0 and (x, y) != (c, r):
                new_blocks.append(block)
                break

            new_blocks.append(block)
            
        return new_blocks

    def run(self):

        pg.init()
        
        screen = pg.display.set_mode((self.WIDTH, self.HEIGHT))    
        pg.display.set_caption('Raycasting')
        clock = pg.time.Clock()
                
        x, y = self.level_width//2, self.level_height//2
        player = Player(x, y)
        self.level_map[y][x] = 2

        view = False
        
        while True:

            screen.fill((0, 0, 0))    

            e = pg.event.poll()
            if e.type == pg.QUIT:
                return
            keys = pg.key.get_pressed()
            if keys[pg.K_ESCAPE] or keys[pg.K_SLASH]:
                return
                
            # View Switch
            if keys[pg.K_1]:
                view = False
                screen = pg.display.set_mode((self.WIDTH, self.HEIGHT))
                pg.display.set_caption('Raycasting 3D Rendering')
            elif keys[pg.K_2]:
                view = True
                screen = pg.display.set_mode((self.level_width * self.TOP_DOWN_SCALE, self.level_height * self.TOP_DOWN_SCALE))    
                pg.display.set_caption('Raycast 2D FOV')

            # Rotate Player
            rot = (int(keys[pg.K_d]) - int(keys[pg.K_a])) * player.angular_speed
            player.rotate(rot)
            
            # Move Player
            movement = int(keys[pg.K_w]) - int(keys[pg.K_s])
            h = math.cos(rad(abs(player.angle))) * player.movement_speed * movement
            v = math.sin(rad(abs(player.angle))) * player.movement_speed * movement
            valid_x = round(player.x + h)
            valid_y = round(player.y + v)
            if 0 <= valid_x <= self.level_width - 1 and 0 <= valid_y <= self.level_height - 1 and self.level_map[valid_y][valid_x] == 0:
                self.level_map[player.y][player.x] = 0
                self.level_map[valid_y][valid_x] = 2
                player.move(h, v)

            if not view: # Raycast 3D View    

                # Draw Floor and Ceiling
                pg.draw.rect(screen, self.CEILING_COLOR, (0, 0, self.WIDTH, self.HEIGHT//2))
                pg.draw.rect(screen, self.FLOOR_COLOR, (0, self.HEIGHT//2, self.WIDTH, self.HEIGHT//2))

                # Render 3D
                i = 0
                phi = (player.angle + self.fov_angle//2) % 360
                # rect_width = self.fov_radius * math.sin(rad(self.raycast_step))
                rect_width = self.WIDTH // (self.fov_angle//self.raycast_step)
                
                while phi != (player.angle - self.fov_angle//2) % 360:
                    hit = self.cast_ray(player.x, player.y, phi)[-1]
                    d = self.get_distance(player.x, player.y, hit[0], hit[1])
                    if d:
                        p = d * math.cos(rad(phi))
                        wall_height = (self.WALL_SCALING / p)

                        if wall_height > self.WALL_SCALING:
                            wall_height = self.WALL_SCALING
                        elif wall_height < 0:
                            wall_height = 0

                        brightness = 1 - (p / self.fov_radius)
                        
                        if brightness > 1:
                            brightness = 1

                        c = (round(self.WALL_COLOR[0] * brightness), round(self.WALL_COLOR[1] * brightness), round(self.WALL_COLOR[2] * brightness))
                        pg.draw.rect(screen, c, (rect_width * i, (self.HEIGHT - wall_height)//2, rect_width, wall_height))

                    i += 1
                    phi -= self.raycast_step
                    phi %= 360

            else: # Top Down View
                

                # Draw Raycast Lines
                phi = (player.angle + self.fov_angle//2) % 360
                while phi != (player.angle - self.fov_angle//2) % 360:

                    blocks = self.cast_ray(player.x, player.y, phi)
                    for block in blocks:
                        pg.draw.rect(screen, self.RAYCAST_LINE_COLOR, (block[0]*self.TOP_DOWN_SCALE, block[1]*self.TOP_DOWN_SCALE, self.TOP_DOWN_SCALE, self.TOP_DOWN_SCALE))

                    phi -= self.raycast_step
                    phi %= 360

                # Draw Map
                for row in range(len(self.level_map)):
                    for col in range(len(self.level_map[row])):
                        if self.level_map[row][col] == 1:
                            pg.draw.rect(screen, self.WALL_COLOR, (col*self.TOP_DOWN_SCALE, row*self.TOP_DOWN_SCALE, self.TOP_DOWN_SCALE, self.TOP_DOWN_SCALE))
                        elif self.level_map[row][col] == 2:
                            pg.draw.circle(screen, self.PLAYER_COLOR, (col*self.TOP_DOWN_SCALE, row*self.TOP_DOWN_SCALE), 2*self.TOP_DOWN_SCALE)
            
            clock.tick(self.FRAME_RATE)
            pg.display.flip() 


def main():
    
    r = Renderer(500, 90, 500, 3)
    r.run()


if __name__ == "__main__":
    main()
    