#!/usr/bin/env python
"""
RoboOS Simple Game: Robot Arena
A simple CLI game where you control a robot to dodge obstacles.
Created for RoboOS by Eslam Ibrahim © 2026
"""

import os
import time
import random
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class RobotArena:
    def __init__(self, width=20, height=10):
        self.width = width
        self.height = height
        self.robot_pos = width // 2
        self.score = 0
        self.game_over = False
        self.obstacles = [] # List of [row, col]

    def spawn_obstacle(self):
        if random.random() < 0.3:
            self.obstacles.append([0, random.randint(0, self.width - 1)])

    def update(self):
        new_obstacles = []
        for obs in self.obstacles:
            obs[0] += 1 # Move down
            if obs[0] == self.height - 1 and obs[1] == self.robot_pos:
                self.game_over = True
            if obs[0] < self.height:
                new_obstacles.append(obs)
        self.obstacles = new_obstacles
        self.score += 1
        self.spawn_obstacle()

    def draw(self):
        clear_screen()
        print(f"╔{'═' * self.width}╗")
        for r in range(self.height):
            line = "║"
            for c in range(self.width):
                char = " "
                if r == self.height - 1 and c == self.robot_pos:
                    char = "🤖" if os.name != 'nt' else "R"
                else:
                    for obs in self.obstacles:
                        if obs[0] == r and obs[1] == c:
                            char = "🔥" if os.name != 'nt' else "*"
                line += char
            print(line + "║")
        print(f"╚{'═' * self.width}╝")
        print(f"Score: {self.score} | Player: Eslam Ibrahim")
        print("Use 'a' to move Left, 'd' to move Right, 'q' to Quit")

def play_game():
    game = RobotArena()
    print("Welcome to Robot Arena!")
    print("Developed by Eslam Ibrahim © 2026")
    time.sleep(2)
    
    import msvcrt # Windows only for non-blocking input
    
    while not game.game_over:
        game.draw()
        
        # Simple input handling
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 'a' and game.robot_pos > 0:
                game.robot_pos -= 1
            elif key == 'd' and game.robot_pos < game.width - 1:
                game.robot_pos += 1
            elif key == 'q':
                break
        
        game.update()
        time.sleep(0.1)

    print(f"\n🎮 GAME OVER! Final Score: {game.score}")
    print("Keep learning with RoboOS!")

if __name__ == "__main__":
    try:
        play_game()
    except KeyboardInterrupt:
        print("\nGame exited.")
