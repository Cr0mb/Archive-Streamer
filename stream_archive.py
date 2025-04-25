import cv2
import pygame
import numpy as np
import subprocess
import threading
import os
import time

def clear_terminal():
    """Clear the terminal screen."""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def play_audio(video_url, start_event):
    """Play audio in a separate thread using ffplay."""
    try:
        # Start the audio playback
        process = subprocess.Popen([
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", video_url
        ])
        # Give audio a bit of time to buffer before signaling
        time.sleep(0.5)  # Buffer for 0.5 seconds
        # Notify that the audio has started
        start_event.set()
        process.wait()  # Wait for audio to finish before exiting the thread
    except FileNotFoundError:
        print("Error: ffplay is not installed or not found in the system path.")
        exit()

def setup_pygame(width, height):
    """Initialize Pygame screen and font."""
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Streaming Video Player")
    font = pygame.font.SysFont("Arial", 20)
    return screen, font

def draw_progress_bar(surface, current_frame, total_frames, screen_width):
    """Draw the progress bar at the bottom of the screen."""
    progress_height = 10
    progress_padding = 10
    progress_color_bg = (50, 50, 50)
    progress_color_fg = (255, 0, 0)

    bar_top = surface.get_height() - progress_height - progress_padding
    bar_rect = pygame.Rect(0, bar_top, screen_width, progress_height)
    pygame.draw.rect(surface, progress_color_bg, bar_rect)

    if total_frames > 0:
        progress_ratio = current_frame / total_frames
        fg_width = int(screen_width * progress_ratio)
        pygame.draw.rect(surface, progress_color_fg, (0, bar_top, fg_width, progress_height))

    return bar_rect

def main():
    clear_terminal()
    
    print("Archive Streamer")
    print("Made by Cr0mb \n")
    
    video_url = input("Enter the archive.org video URL: ")
    
    if "archive.org/details/" in video_url:
        video_url = video_url.replace("archive.org/details/", "archive.org/download/")

    # Create an event to sync audio and video start
    audio_thread_event = threading.Event()
    audio_thread = threading.Thread(target=play_audio, args=(video_url, audio_thread_event), daemon=True)
    audio_thread.start()

    cap = cv2.VideoCapture(video_url)
    if not cap.isOpened():
        print("Error: Couldn't open video stream.")
        exit()

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 120
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    screen, font = setup_pygame(width, height)

    fullscreen = False
    windowed_size = (width, height)

    button_text_fs = "⛶"
    button_text_wd = "🗗"
    button_width = 150
    button_height = 30
    button_padding = 10

    running = True
    while running:
        # Wait for the audio to start
        audio_thread_event.wait()

        ret, frame = cap.read()
        if not ret:
            break

        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        # Convert frame for Pygame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.transpose(frame, (1, 0, 2))
        frame_surface = pygame.surfarray.make_surface(frame)
        frame_surface = pygame.transform.scale(frame_surface, screen.get_size())
        screen.blit(frame_surface, (0, 0))

        button_rect = pygame.Rect(
            button_padding,
            screen.get_height() - button_height - 10,
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

        progress_bar_rect = draw_progress_bar(screen, current_frame, total_frames, screen.get_width())

        pygame.display.update()
        pygame.time.Clock().tick(fps)

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
                    click_x = event.pos[0]
                    bar_width = progress_bar_rect.width
                    target_ratio = click_x / bar_width
                    target_frame = int(target_ratio * total_frames)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()
