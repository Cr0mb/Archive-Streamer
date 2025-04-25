import cv2
import pygame
import numpy as np
import subprocess
import threading
import os

if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')

print("Archive Streamer")
print("Made by Cr0mb \n")
video_url = input("Enter the archive.org video URL: ")

if "archive.org/details/" in video_url:
    video_url = video_url.replace("archive.org/details/", "archive.org/download/")

# Start ffplay in a separate thread to play the audio
def play_audio():
    subprocess.call([
        "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", video_url
    ])

# Start audio thread
audio_thread = threading.Thread(target=play_audio, daemon=True)
audio_thread.start()

cap = cv2.VideoCapture(video_url)
if not cap.isOpened():
    print("Error: Couldn't open video stream.")
    exit()

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS) or 60
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Streaming Video Player")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

fullscreen = False
windowed_size = (width, height)

button_text_fs = "⛶"
button_text_wd = "🗗"
button_width = 150
button_height = 30
button_padding = 10

progress_height = 10
progress_padding = 10
progress_color_bg = (50, 50, 50)
progress_color_fg = (255, 0, 0)

def draw_progress_bar(surface, current_frame):
    screen_width = screen.get_width()
    bar_top = screen.get_height() - progress_height - progress_padding
    bar_rect = pygame.Rect(0, bar_top, screen_width, progress_height)
    pygame.draw.rect(surface, progress_color_bg, bar_rect)

    if total_frames > 0:
        progress_ratio = current_frame / total_frames
        fg_width = int(screen_width * progress_ratio)
        pygame.draw.rect(surface, progress_color_fg, (0, bar_top, fg_width, progress_height))

    return bar_rect

running = True
while running:
    ret, frame = cap.read()
    if not ret:
        break

    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

    # Convert and transpose frame for Pygame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.transpose(frame, (1, 0, 2))
    frame_surface = pygame.surfarray.make_surface(frame)
    frame_surface = pygame.transform.scale(frame_surface, screen.get_size())
    screen.blit(frame_surface, (0, 0))

    button_rect = pygame.Rect(
        button_padding,
        screen.get_height() - button_height - progress_height - 2 * progress_padding,
        button_width,
        button_height
    )
    pygame.draw.rect(screen, (0, 0, 0), button_rect)
    pygame.draw.rect(screen, (200, 200, 200), button_rect, 2)

    button_text = button_text_fs if not fullscreen else button_text_wd
    text_surface = font.render(button_text, True, (255, 255, 255))
    screen.blit(text_surface, (
        button_rect.x + 10,
        button_rect.y + (button_height - text_surface.get_height()) // 2
    ))

    progress_bar_rect = draw_progress_bar(screen, current_frame)

    pygame.display.update()
    clock.tick(fps)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode(windowed_size)
            elif progress_bar_rect.collidepoint(event.pos):
                # Seek video based on click location
                click_x = event.pos[0]
                bar_width = progress_bar_rect.width
                target_ratio = click_x / bar_width
                target_frame = int(target_ratio * total_frames)
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

# Cleanup
cap.release()
pygame.quit()
