import pygame
import neat
import time
import os
import random
pygame.font.init()

# size of the screen
WIN_WIDTH = 500
WIN_HEIGHT = 800

# loading the required images
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs" , 'bird1.png'))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs" , 'bird2.png'))) , pygame.transform.scale2x(pygame.image.load(os.path.join("imgs" , 'bird3.png'))) ]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs" , 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs" , 'base.png')))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs" , 'bg.png')))

GEN = 0

STAT_FONT = pygame.font.SysFont("comicsans" , 50)

class Bird():
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25 #how much it will tilt
    ROT_VEL = 20 #how much rotation on each frame
    ANIMATION_TIME = 5 #for flapping

    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0  # when did we last jumped....jump count basically
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5 #pygame considers the top left as 0,0 thus u need negative velocity to go up
        self.tick_count = 0
        self.height = self.y
    
    def move(self):
        self.tick_count += 1 
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2 # this basically creates an arc for our bird by creating the pixel dispacement for every single frame but this d changes as ticket_count keeps updating (+1)

        if d>=16:
            d = 16 # terminal velocity
        if d < 0:
            d -= 2 # just fine tuning for a better jump
        
        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    # for the flapping animation ; win -> window
    def draw(self , win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 +1:
            self.img = self.IMGS[0]
            self.img_count = 0 # resetting the img count

        if self.tilt <= -80:
            self.img = self.IMGS[1] # so that it doesnt flap while going down
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img , self.tilt) # rotating the image
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft  = (self.x , self.y)).center) 
        win.blit(rotated_image , new_rect.topleft) # using the center as the axis of rotation and not the default corner

    # for collision of our objects -> makes lists of all the pixels of two images and checks whether there is any overlapping of pixels to know whether a collision has occured
    def get_mask(self):
        return pygame.mask.from_surface(self.img)
    
class Pipe:
    GAP = 200
    VEL = 5

    def __init__ (self,x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0 

        #we only have one pipe image so we are flipping it to get the other half
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG , False , True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False # if it has passed
        self.set_height()

    # aligning the top pip according to the position of the bottom pipe
    def set_height(self):
        self.height = random.randrange(50,450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP
    
    #moving pipe based on velocity
    def move(self):
        self.x -= self.VEL

    def draw(self,win):
        win.blit(self.PIPE_TOP, (self.x , self.top))
        win.blit(self.PIPE_BOTTOM , (self.x , self.bottom))

    def collide(self,bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # offset is how far away the top left corners of the two images are from each other
        top_offset = (self.x-bird.x , self.top - round(bird.y))
        bottom_offset = (self.x - bird.x , self.bottom - round(bird.y))
    
        # point of collision -> none if no collision
        b_point = bird_mask.overlap(bottom_mask , bottom_offset)
        t_point = bird_mask.overlap(top_mask , top_offset)

        # if we collide or not
        if t_point or b_point:
            return True
        return False
    
class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG
    
    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH
    
    # moving two images; one starting at the left most end and the other just outside the bottom right end and both move left wiht the same velocity and then swtch plsces as soon as they are completely out of frame
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 +self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self , win):
        win.blit(self.IMG , (self.x1 , self.y))
        win.blit(self.IMG , (self.x2 , self.y))

def draw_window(win , birds , pipes , base , score , gen):
    win.blit(BG_IMG , (0,0))

    for pipe in pipes:
        pipe.draw(win)

    #using blit to shift the score so that it does not go out of the frame
    text = STAT_FONT.render("Score:" + str(score) , 1,(255,255,255))
    win.blit(text , (WIN_WIDTH - 10 - text.get_width() , 10))

    text = STAT_FONT.render("Gen:" + str(gen) , 1,(255,255,255))
    win.blit(text , (10 , 10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()

def main(genomes,config):
    global GEN
    GEN += 1
    nets = [] # for knowing which birds are controlled by which neural network
    ge = [] # to track the genomes to further alter it down the line
    birds = []

    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230,350))
        ge.append(genome)

    base = Base(730)
    pipes = [Pipe(600)]

    win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0
    run = True

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # we are setting a pipe index to know which the index of the pipe the nerual net is comparing with (for the distance between the bird and the pipe) in case there are 2 simultaneously on the screen
        pipe_ind = 0
        if len(birds)>0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break
            
        for x,bird in enumerate(birds):
            ge[x].fitness += 0.1
            bird.move()
            

            output = nets[x].activate((bird.y , abs(bird.y - pipes[pipe_ind].height) , abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        add_pipe = False

        #list for the pipes that are removed
        rem = []

        #bird.move()
        for pipe in pipes:
            for x , bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -=1 # its a penalty for birds that hit the pipe
                    #removing the birds and all its attributes
                    birds.pop(x) 
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            #if pipe is out of frame
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        # we can control the speed at which new pipes appear by changing the parameter given to the Pipe()
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5 # extra reward for passing a pipe
            pipes.append(Pipe(600))
        
        for r in rem:
            pipes.remove(r)
        
        # if bird hits the ground
        for x,bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x) 
                nets.pop(x)
                ge.pop(x)
                

        if score > 50:
            break

        base.move()
        draw_window(win, birds, pipes, base , score , GEN)



def run(config_path):
    config = neat.config.Config(neat.DefaultGenome , neat.DefaultReproduction , neat.DefaultSpeciesSet , neat.DefaultStagnation , config_path)
    # out population
    p = neat.Population(config)
    # our metrics
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # 50 is the number of generations i am running the ai for and main is our fitness function
    winner = p.run(main,50)



if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir , "config-feedforward.txt")
    run(config_path)
    