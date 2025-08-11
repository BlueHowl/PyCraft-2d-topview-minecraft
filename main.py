"""
PyCraft 2D - Main Entry Point
A 2D Minecraft-like game built with Pygame.
"""
from game.core.game import Game


def main():
    """Main game entry point."""
    # Create game instance
    game = Game()
    
    # Main game loop
    while True:
        game.playing = False
        game.show_start_screen()
        game.show_go_screen()


if __name__ == "__main__":
    main()
