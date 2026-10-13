import pygame
import numpy as np
import math
from pygame.locals import*
import pygame.midi

# pygame setup
bits = 16
running = True
pygame.mixer.pre_init(44100, -bits, 2)
pygame.init()
pygame.midi.init()
screen = pygame.display.set_mode((1000, 500))
pygame.display.set_caption("Lumaboard")
clock = pygame.time.Clock()
pygame.mixer.set_num_channels(100)

def interpolate(a, b, c):
    return b+(c*(a-b))

def tell_n_channels():
    n=0
    for i in channels:
        n+=i.get_busy()

def stop(i):
    global channels
    global sounds
    global playing

    if channels[i] != None:
        channels[i].stop()
    sounds[i].stop()

    channels[i] = None
    sounds[i].set_volume(1)

    playing[i] = 0  
    times[i] = -1

def make_sound(freq):
    duration = (1/freq)*100    # in seconds
    #freqency for the left speaker
    frequency_l = freq
    #frequency for the right speaker
    frequency_r = freq

    #this sounds totally different coming out of a laptop versus coming out of headphones

    sample_rate = 441*100

    n_samples = int(round(duration*sample_rate))

    #setup our numpy array to handle 16 bit ints, which is what we set our mixer to expect with "bits" up above
    buf = np.zeros((n_samples, 2), dtype = np.int16)
    max_sample = 2**(bits - 1) - 1

    for s in range(n_samples):
        t = float(s)/sample_rate    # time in seconds

        #grab the x-coordinate of the sine wave at a given time, while constraining the sample to what our mixer is set to with "bits"
        buf[s][0] = int(round((max_sample*0.25)*math.cos(math.pi*frequency_l*t))) *0.5    # left
        buf[s][1] = int(round((max_sample*0.25)*math.cos(math.pi*frequency_r*t)))   # right

    sound = pygame.sndarray.make_sound(buf)

    return sound

def bar(n, s):
    l = []
    while len(l) != n:
        l.append(s)
        s+=2
    return l

if __name__=="__main__":

    #keyboard
    keyboard = [[K_BACKQUOTE, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9, K_0, K_MINUS, K_EQUALS, K_BACKSPACE],
          [K_TAB, K_q, K_w, K_e, K_r, K_t, K_y, K_u, K_i, K_o, K_p, K_LEFTBRACKET, K_RIGHTBRACKET, K_BACKSLASH],
          [K_a, K_s, K_d, K_f, K_g, K_h, K_j, K_k, K_l, K_SEMICOLON, K_QUOTE, K_RETURN], 
          [K_LSHIFT, K_z, K_x, K_c, K_v, K_b, K_n, K_m, K_COMMA, K_PERIOD, K_SLASH, K_RSHIFT]]
    key_names = [
              'K_BACKQUOTE', 'K_1', 'K_2', 'K_3', 'K_4', 'K_5', 'K_6', 'K_7', 'K_8', 'K_9', 'K_0', 'K_MINUS', 'K_EQUALS', 'K_BACKSPACE',
              'K_TAB', 'K_q', 'K_w', 'K_e', 'K_r', 'K_t', 'K_y', 'K_u', 'K_i', 'K_o', 'K_p', 'K_LEFTBRACKET', 'K_RIGHTBRACKET', 'K_BACKSLASH',
              'K_a', 'K_s', 'K_d', 'K_f', 'K_g', 'K_h', 'K_j', 'K_k', 'K_l', 'K_SEMICOLON', 'K_QUOTE', 'K_RETURN', 
              'K_LSHIFT', 'K_z', 'K_x', 'K_c', 'K_v', 'K_b', 'K_n', 'K_m', 'K_COMMA', 'K_PERIOD', 'K_SLASH', 'K_RSHIFT']

    #constants
    freq             = 300              #frequency of note 0
    universal_length = len(key_names)   #number of keys
    rise             = [0, 1, 4, 3]     #note rise in each row
    visual_rise      = [0, 0.5, 2, 1.5] #note rise in each row on screen
    edo              = 12               #number of notes per octave

    #variables
    play_mask = []   #[bool]           of length universal_length, True if note is playing via playback, False if not
    keys      = []   #[int]            of length universal_length, shows keyboard in one array
    notes     = []   #[int]            of length universal_length, shows note number
    sounds    = []   #[pygame.Sound]   of length universal_length
    playing   = []   #[bool]           of length universal_length, True if note is playing, False if note if not
    times     = []   #[int]            of length universal_length, number of frames the note is playing
    channels  = []   #[pygame.Channel] of length universal_length
    recording = []   #[[int, int, int]], [[start_frame, end_frame, note_index]] list similar to midi. Tells what notes are playing from what frame to what frame
    time      = 0    #frame count of the program
    rise_time = 0.01 #time for note to fade into 100% volume linearly
    mode      = 1    # recording mode. 0 = none (not implemented yet), 1 = recording, 2 = playing.
    play_time = 0    #time when playback is on (mode is set to 2)
    loop_time = 0    #the number of frame in which the playback need to reset back to frame 0 (time = play_time = 0)
    s_press   = True #toggle bool

    #setup
    for i, array in enumerate(keyboard):
            keys += array
            notes += bar(len(array), rise[i])
            print(len(keys), len(notes))


    for i in range(len(keys)):
        note = notes[i]
        sounds.append(make_sound((2**(note/edo))*freq))
        playing.append(False)
        channels.append(None)
        times.append(-1)

    for i in range(100): #100 channels
        channels.append(pygame.mixer.Channel(i))

    print(f'devs: {pygame.midi.get_count()}')
    #midi_output = pygame.midi.Output(0)

    sustain = False
    s_press = False



    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.unicode == " ":
                    sustain = not sustain
                
        #controls
        all_pressed = pygame.key.get_pressed()
        #print(pygame.key.get_pressed())
        #print(all_pressed)
            

        if mode == 2:
            play_mask = [False] * universal_length
            for rec in recording:
                if rec[0] <= (time - play_time) <= rec[1]:
                    play_mask[rec[2]] = True

        if all_pressed[K_ESCAPE]:
            mode = 2
            play_time = time
            loop_time = max(recording, key=lambda x: x[1])[1] + 10
        
        if mode == 2:
            if (time - play_time) >= loop_time:
                time = play_time
            if (time - play_time) > loop_time:
                print('phew!')

        #print(mode, time-play_time, recording)

        #for i, e in enumerate(all_pressed):
            #window.blip

        if sustain:
            rise_time = 1
        else:
            rise_time = 0.01

        #print(len(keys), universal_length)
        for i, key in enumerate(keys):
            if all_pressed[key] or play_mask[i]:

                if s_press and (playing[i] == 2):
                    times[i] = 0
        
                
                if s_press and (playing[i] != 1):
                
                    playing[i] = 1

                
                    stop(i)

                    
                    for channel in channels:
                        if not channel.get_busy():

                            channel.play(sounds[i], loops=-1)
                            channels[i] = channel
                            playing[i] = 1
                            times[i] = 0

                            if mode == 1:
                                recording.append([time, -1, i])

                            break
                else:
                    pass
                    #sounds[i].set_volume(0)

                s_press=False

                
                

            else: #key is not being pressed
                times[i] = -1
                if playing[i] != 0:
                    if mode == 1:
                        for rec in recording:
                            if rec[1] == -1 and rec[2] == i:
                                rec[1] = time
                    
                    if sustain:
                        sounds[i].set_volume(sounds[i].get_volume()*0.9999999)
                        playing[i] = 2
                    else:
                        sounds[i].set_volume(0)

                    if sounds[i].get_volume() == 0:
                        stop(i)
                    
                        
                s_press=True

            if times[i] >= 0:
                times[i] += 1

            if times[i] > rise_time:
                pass
            else:
                sounds[i].set_volume(times[i] / rise_time)

        #midi

        '''       
        for i, sound in enumerate(sounds):
            if playing[i]:
                
                sound.set_volume(1)
            else:
                if sustain:
                    sound.set_volume(sound.get_volume()-0.01)
                else:
                    sound.set_volume(0)
        '''
        
        

        # fill the screen with a color to wipe away anything from last frame
        screen.fill([(100, 150, 255), (150, 200, 100)][sustain])

        count = 0
        for j, row in enumerate(keyboard):
            for i, cell in enumerate(row):
                i += visual_rise[j]
                default = [(255, 245, 235), (20, 10, 0)][notes[count]%12 in [1, 3, 6, 8, 10]]
                pygame.draw.rect(screen, [default, (255, 150, 200)][all_pressed[keys[count]] or play_mask[count]], (i*50, j*50, 45, 45))
                count+=1

        # RENDER YOUR GAME HERE

        # flip() the display to put your work on screen
        pygame.display.flip()

        #print(pygame.time.get_ticks())

        clock.tick(60)  # limits FPS to 60

        time += 1

    pygame.quit()

