import pygame
import os
import time
import random
import asyncio

pygame.mixer.init()
pygame.font.init()

WIDTH,HEIGHT = 500,500
WIN = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Space Invaders Game")

#load images
RED_SHIP = pygame.image.load(os.path.join("assets","pixel_ship_red_small.png"))
GREEN_SHIP = pygame.image.load(os.path.join("assets","pixel_ship_green_small.png"))
BLUE_SHIP = pygame.image.load(os.path.join("assets","pixel_ship_blue_small.png"))

#lasers
RED_LASER = pygame.image.load(os.path.join("assets","pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets","pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets","pixel_laser_blue.png"))

#main player and laser
MAIN_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("assets","pixel_ship_yellow.png")),(WIDTH/9,HEIGHT/9))
MAIN_SHIP_LASER = pygame.image.load(os.path.join("assets","pixel_laser_yellow.png"))

#bg
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets","background-black.png")),(WIDTH,HEIGHT))


class Laser:
    def __init__(self,x,y,img) -> None:
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)
    
    def draw(self,window):
        window.blit(self.img,(self.x,self.y))
    
    def move(self,vel):
        self.y += vel

    def off_screen(self,height):
        return not(self.y <= height and self.y>=0)
    
    def collision(self, obj):
        return collide(obj, self)

class Ship:
    COOLDOWN = 30

    def __init__(self,x,y,health=100) -> None:
        self.x=x
        self.y=y
        self.health=health
        self.ship_img=None
        self.laser_img=None
        self.lasers=[]
        self.cooldown_counter=0
    
    def draw(self,window):
        WIN.blit(self.ship_img, (self.x,self.y))
        for laser in self.lasers:
            laser.draw(window)
    
    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)
                play_music(os.path.join("assets","laser-hit.wav"))

    def cooldown(self):
        if self.cooldown_counter >= self.COOLDOWN:
            self.cooldown_counter = 0
        elif self.cooldown_counter > 0:
            self.cooldown_counter += 1

    def shoot(self):
        if self.cooldown_counter == 0:
            laser = Laser(self.x,self.y,self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1
    
    def get_width(self):
        return self.ship_img.get_width()
    
    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100) -> None:
        super().__init__(x, y, health)
        self.ship_img = MAIN_SHIP
        self.laser_img = MAIN_SHIP_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.score = 0
    
    def shoot(self):
        if self.cooldown_counter == 0:
            laser = Laser(self.x-20,self.y,self.laser_img)
            self.lasers.append(laser)
            play_music(os.path.join("assets","shoot.wav"))
            self.cooldown_counter = 1

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)
                        play_music(os.path.join("assets","hit.wav"))
                        self.score += 1
                        

    def draw(self, window):
        super().draw(window)
        self.health_bar(window)
    
    def health_bar(self,window):
        pygame.draw.rect(window,(255,0,0),(self.x,self.y+self.ship_img.get_height()+10,self.ship_img.get_width(),10))
        pygame.draw.rect(window,(0,255,0),(self.x,self.y+self.ship_img.get_height()+10,self.ship_img.get_width()*(self.health/self.max_health),10))


class Enemy(Ship):
    COLOR_MAP = {
        "red" : (RED_SHIP,RED_LASER),
        "blue": (BLUE_SHIP,BLUE_LASER),
        "green": (GREEN_SHIP,GREEN_LASER)
    }

    def __init__(self, x, y,color, health=100) -> None:
        super().__init__(x, y, health)
        self.ship_img,self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)
    
    def shoot(self):
        if self.cooldown_counter == 0:
            laser = Laser(self.x-25,self.y,self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1

    def move(self,vel):
        self.y += vel

def collide(obj1 , obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask,(offset_x,offset_y)) != None

def play_music(music):
    pygame.mixer.music.load(music)
    pygame.mixer.music.play()
    if music == "shoot.wav":
        pygame.mixer.music.set_volume(0.1)

def wait():
    pygame.time.delay(5000)

def play():
    run = True
    FPS = 60
    level = 0
    lives = 3
    player_speed = 5
    main_font = pygame.font.SysFont("comicsans", 20)
    lost_font = pygame.font.SysFont("comicsans", 30)
    restore_font = pygame.font.SysFont("comicsans", 30)

    enemies = []
    NoOFEnemies = 5
    enemy_vel = 1
    laser_vel = 4

    lost = False
    lost_count = 0
    restore = False

    player = Player(300,300)

    clock = pygame.time.Clock()

    def redraw_window():
        WIN.blit(BG,(0,0))

        
        lives_label = main_font.render(f"Lives: {lives}",1,(255,255,255))
        level_label = main_font.render(f"Level: {level}",1,(255,255,255))
        score_label = main_font.render(f"Score: {player.score}",1,(255,255,255))


        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)
        if lost:
            lost_label = lost_font.render(f"You Lost!!",1,(255,255,255))
            WIN.blit(lost_label,(WIDTH/2-lost_label.get_width()/2,250))
            play_music(os.path.join("assets","lost sound.wav"))

        if restore:
            restore_label = restore_font.render("Wait!! Health is restoring...",1,(255,255,255))
            WIN.blit(restore_label,(WIDTH/2-restore_label.get_width()/2,250))
        
        WIN.blit(lives_label,(10,10))
        WIN.blit(level_label,(WIDTH-level_label.get_width()-10,10))
        WIN.blit(score_label,(WIDTH-score_label.get_width()-10,10+score_label.get_height()))

        pygame.display.update()


    while run:
        clock.tick(FPS)
        redraw_window()

        if player.health <= 0:
            if lives > 1:
                restore = True
                lives -= 1
                player.health = 100
            elif lives == 1:
                lost = True
                lost_count += 1
        else:
            restore = False

        if lost:
            if lost_count > FPS * 3:
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            NoOFEnemies += 5 
            for i in range(NoOFEnemies):
                enemy = Enemy(random.randrange(50,WIDTH-50),random.randrange(-1500,-100),random.choice(["red","blue","green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        
        keys = pygame.key.get_pressed()  
        if keys[pygame.K_LEFT] and player.x - player_speed > 0 :
            player.x -= player_speed
        if keys[pygame.K_RIGHT] and player.x + player_speed + player.get_width() < WIDTH:
            player.x += player_speed
        if keys[pygame.K_UP]  and player.y - player_speed > 0:
            player.y -= player_speed
        if keys[pygame.K_DOWN] and player.y + player_speed + player.get_height() + 15 < HEIGHT:
            player.y += player_speed
        if keys[pygame.K_SPACE] :
            player.shoot()

        
        for enemy in enemies:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(0, 4*60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 100
                play_music(os.path.join("assets","hit.wav"))
                enemies.remove(enemy)
                player.score += 1

            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)
            
        player.move_lasers(-laser_vel, enemies)

async def main():
    run = True
    noOfTimes = 0
    title_font = pygame.font.SysFont("comicsans",20)
    play_music(os.path.join("assets","pink-panther.mp3"))
    
    while run:
        pygame.display.update()
        WIN.blit(BG,(0,0))
        if noOfTimes == 0:
            title_label = title_font.render("Press the mouse to begin...", 1, (255,255,255))
            WIN.blit(title_label,(WIDTH/2 - title_label.get_width()/2,200))
        else:
            title_label = title_font.render("Wanna Play Again!",1,(255,255,255))
            extra_label = title_font.render("Press the mouse to begin...", 1, (255,255,255))
            WIN.blit(title_label,(WIDTH/2 - title_label.get_width()/2,200))
            WIN.blit(extra_label,(WIDTH/2 - title_label.get_width()/2-40,210+extra_label.get_height()))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONDOWN: 
                noOfTimes += 1
                pygame.mixer.music.pause()
                play()
    await asyncio.sleep(0)

asyncio.run(main())
                



