"""
PyCraft 2D - Main Entry Point
A 2D Minecraft-like game built with Pygame.
"""
import sys
import traceback
from game.core.game import Game
from game.config.game_config import GameConfig
from game.utils.logger import log_info, log_error, log_exception


def main():
    """Main game entry point with comprehensive error handling."""
    game = None
    try:
        log_info("Starting PyCraft 2D...")
        log_info(f"Debug mode: {GameConfig.DEBUG_MODE}")
        
        # Create game instance
        game = Game()
        log_info("Game initialized successfully")
        
        # Main game loop
        while True:
            game.playing = False
            game.show_start_screen()
            game.show_go_screen()
            
    except KeyboardInterrupt:
        log_info("Game interrupted by user (Ctrl+C)")
    except Exception as e:
        log_exception(f"Critical error in main game loop: {e}")
        if GameConfig.DEBUG_MODE:
            # In debug mode, re-raise the exception to see full traceback
            raise
        else:
            # In release mode, try to show a user-friendly error message
            try:
                import pygame as pg
                if pg.get_init():
                    # If pygame is initialized, try to show error screen
                    show_error_screen(str(e))
            except:
                pass  # If we can't show error screen, just exit gracefully
    finally:
        # Cleanup
        if game:
            try:
                game.quit()
                log_info("Game cleanup completed")
            except:
                pass  # Ignore cleanup errors
        
        log_info("PyCraft 2D exiting")


def show_error_screen(error_message: str):
    """Show a simple error screen to the user."""
    try:
        import pygame as pg
        
        # Initialize pygame if not already done
        if not pg.get_init():
            pg.init()
        
        screen = pg.display.set_mode((800, 600))
        pg.display.set_caption("PyCraft 2D - Error")
        
        font = pg.font.Font(None, 36)
        small_font = pg.font.Font(None, 24)
        
        # Create error message
        error_text = font.render("An error occurred:", True, (255, 255, 255))
        error_detail = small_font.render(str(error_message)[:70], True, (255, 200, 200))
        instruction = small_font.render("Press any key to exit", True, (200, 200, 200))
        
        running = True
        clock = pg.time.Clock()
        
        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT or event.type == pg.KEYDOWN:
                    running = False
            
            screen.fill((40, 40, 40))
            screen.blit(error_text, (50, 200))
            screen.blit(error_detail, (50, 250))
            screen.blit(instruction, (50, 350))
            
            pg.display.flip()
            clock.tick(60)
        
        pg.quit()
    except:
        pass  # If we can't show the error screen, just exit


if __name__ == "__main__":
    main()
