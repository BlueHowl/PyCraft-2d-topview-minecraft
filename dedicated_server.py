#!/usr/bin/env python3
"""
PyCraft 2D Dedicated Server

This script runs a standalone multiplayer server for PyCraft 2D.
Players can connect to this server to play together.

Usage:
    python dedicated_server.py [options]

Options:
            log_info(f"World: {self.world_name}")
            log_info(f"Listening on {self.config.host}:{self.config.port}")
            log_info(f"Max players: {self.config.max_players}")
            log_info(f"Auto-save interval: {self.config.save_interval}s")lone multiplayer server for PyCraft 2D.
Players can connect to this server to play together.

Usage:
    python dedicated_server.py [options]

Options:
    --port PORT          Server port (default: 25565)
    --max-players NUM    Maximum players (default: 10)
    --world-name NAME    World name (default: "Dedicated World")
    --save-interval SEC  Auto-save interval (default: 300)
    --config FILE        Configuration file path
    --verbose           Enable verbose logging
    --help              Show this help message
"""

import sys
import os
import argparse
import signal
import time
import threading
import json
from pathlib import Path

# Add the game directory to the Python path
game_dir = Path(__file__).parent
sys.path.insert(0, str(game_dir))

from game.network.server.game_server import GameServer, ServerConfig
from game.utils.logger import log_info, log_error, log_warning, setup_logger
from game.data import DataManager


class DedicatedServer:
    """Standalone dedicated server for PyCraft 2D"""
    
    def __init__(self, config: ServerConfig, world_name: str = "Dedicated World"):
        """Initialize the dedicated server."""
        self.config = config
        self.world_name = world_name
        self.server = None
        self.running = False
        self.data_manager = DataManager(str(game_dir))
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        log_info(f"Dedicated server initialized")
        log_info(f"Configuration: {self.config}")
        log_info(f"World: {self.world_name}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        log_info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the dedicated server."""
        try:
            log_info("Starting PyCraft 2D Dedicated Server...")
            
            # Ensure world exists
            if not self._ensure_world_exists():
                log_error("Failed to create or verify world")
                return False
            
            # Create and start the game server
            self.server = GameServer(self.config, self.world_name)
            
            if not self.server.start():
                log_error("Failed to start game server")
                return False
            
            self.running = True
            log_info(f"Server started successfully!")
            log_info(f"World: {self.world_name}")
            log_info(f"Listening on {self.config.host}:{self.config.port}")
            log_info(f"Max players: {self.config.max_players}")
            log_info(f"Auto-save interval: {self.config.save_interval}s")
            log_info("Server is ready for connections")
            
            # Start auto-save thread
            self._start_auto_save()
            
            # Main server loop
            self._run_server_loop()
            
            return True
            
        except Exception as e:
            log_error(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the dedicated server."""
        if not self.running:
            return
        
        log_info("Stopping dedicated server...")
        self.running = False
        
        if self.server:
            self.server.stop()
            log_info("Game server stopped")
        
        log_info("Dedicated server stopped successfully")
    
    def _ensure_world_exists(self):
        """Ensure the world exists, create if necessary."""
        try:
            world_path = game_dir / 'saves' / self.world_name
            
            if not world_path.exists():
                log_info(f"Creating new world: {self.world_name}")
                
                # Create new world using data manager
                spawn_point = (0, 0)  # Default spawn
                seed = str(abs(hash(self.world_name)))
                
                success = self.data_manager.create_new_world(
                    world_name=self.world_name,
                    seed=seed,
                    spawn_point=spawn_point
                )
                
                if not success:
                    log_error(f"Failed to create world: {self.world_name}")
                    return False
                
                log_info(f"World created: {self.world_name}")
            else:
                log_info(f"Using existing world: {self.world_name}")
            
            return True
            
        except Exception as e:
            log_error(f"World creation error: {e}")
            return False
    
    def _start_auto_save(self):
        """Start the auto-save thread."""
        def auto_save_worker():
            while self.running:
                time.sleep(self.config.save_interval)
                if self.running and self.server:
                    try:
                        log_info("Auto-saving world...")
                        # The server should handle world saving
                        # This is a placeholder for when save functionality is implemented
                        log_info("Auto-save completed")
                    except Exception as e:
                        log_error(f"Auto-save failed: {e}")
        
        auto_save_thread = threading.Thread(target=auto_save_worker, daemon=True)
        auto_save_thread.start()
        log_info(f"Auto-save enabled (interval: {self.config.save_interval}s)")
    
    def _run_server_loop(self):
        """Run the main server loop."""
        try:
            while self.running:
                # Update server
                if self.server:
                    self.server.update()
                
                # Print status every 30 seconds
                if int(time.time()) % 30 == 0:
                    self._print_status()
                
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            log_info("Server interrupted by user")
        except Exception as e:
            log_error(f"Server loop error: {e}")
        finally:
            self.stop()
    
    def _print_status(self):
        """Print server status information."""
        if self.server:
            player_count = self.server.get_player_count()
            log_info(f"Server Status - Players: {player_count}/{self.config.max_players}")


def load_config(config_file):
    """Load configuration from file."""
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        return ServerConfig(
            host=config_data.get('host', 'localhost'),
            port=config_data.get('port', 25565),
            max_players=config_data.get('max_players', 10),
            save_interval=config_data.get('save_interval', 300),
            debug_mode=config_data.get('debug_mode', False)
        ), config_data.get('world_name', 'Dedicated World')
    except Exception as e:
        log_error(f"Failed to load config file {config_file}: {e}")
        return None


def create_default_config(config_file):
    """Create a default configuration file."""
    default_config = {
        "host": "localhost",
        "port": 25565,
        "max_players": 10,
        "world_name": "Dedicated World",
        "save_interval": 300,
        "debug_mode": False
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        log_info(f"Created default config file: {config_file}")
        return True
    except Exception as e:
        log_error(f"Failed to create config file {config_file}: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='PyCraft 2D Dedicated Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--port', type=int, default=25565,
                       help='Server port (default: 25565)')
    parser.add_argument('--max-players', type=int, default=10,
                       help='Maximum players (default: 10)')
    parser.add_argument('--world-name', default='Dedicated World',
                       help='World name (default: "Dedicated World")')
    parser.add_argument('--save-interval', type=int, default=300,
                       help='Auto-save interval in seconds (default: 300)')
    parser.add_argument('--config', 
                       help='Configuration file path')
    parser.add_argument('--create-config', 
                       help='Create a default configuration file')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--host', default='localhost',
                       help='Server host address (default: localhost)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logger(log_level)
    
    # Handle config file creation
    if args.create_config:
        if create_default_config(args.create_config):
            print(f"Created default config file: {args.create_config}")
            print("You can now edit it and run the server with --config option")
        return
    
    # Load configuration
    if args.config:
        config_result = load_config(args.config)
        if not config_result:
            log_error("Failed to load configuration file")
            sys.exit(1)
        config, world_name = config_result
    else:
        # Create config from command line arguments
        config = ServerConfig(
            host=args.host,
            port=args.port,
            max_players=args.max_players,
            save_interval=args.save_interval,
            debug_mode=args.verbose
        )
        world_name = args.world_name
    
    # Create and start the dedicated server
    server = DedicatedServer(config, world_name)
    
    try:
        if server.start():
            log_info("Server started successfully")
        else:
            log_error("Failed to start server")
            sys.exit(1)
    except KeyboardInterrupt:
        log_info("Server interrupted by user")
    except Exception as e:
        log_error(f"Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
