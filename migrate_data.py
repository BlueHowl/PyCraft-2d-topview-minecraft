"""
Migration tool to convert legacy data formats to JSON.
"""

import os
import json
import shutil
from typing import Dict, List, Any
from game.data import DataManager


class DataMigrator:
    """Tool to migrate legacy data formats to new JSON structure."""
    
    def __init__(self, game_folder: str):
        self.game_folder = game_folder
        self.data_manager = DataManager(game_folder)
        self.data_path = os.path.join(game_folder, 'data')
        self.saves_path = os.path.join(game_folder, 'saves')
    
    def migrate_all(self, create_backups: bool = True) -> bool:
        """
        Migrate all data to new JSON format.
        
        Args:
            create_backups: Whether to create backups of original files
            
        Returns:
            True if migration successful, False otherwise
        """
        print("Starting data migration to JSON format...")
        
        success = True
        
        if create_backups:
            print("Creating backups...")
            self._create_backups()
        
        # Migrate configuration data
        print("Migrating configuration data...")
        if not self._migrate_config_data():
            success = False
        
        # Migrate save data
        print("Migrating save data...")
        if not self._migrate_save_data():
            success = False
        
        if success:
            print("Migration completed successfully!")
        else:
            print("Migration completed with some errors. Check the logs above.")
        
        return success
    
    def _create_backups(self):
        """Create backups of all original data files."""
        backup_folder = os.path.join(self.game_folder, 'data_backup')
        os.makedirs(backup_folder, exist_ok=True)
        
        # Backup data folder
        data_backup = os.path.join(backup_folder, 'data')
        if os.path.exists(self.data_path) and not os.path.exists(data_backup):
            shutil.copytree(self.data_path, data_backup)
            print(f"Created backup of data folder at {data_backup}")
        
        # Backup saves folder
        saves_backup = os.path.join(backup_folder, 'saves')
        if os.path.exists(self.saves_path) and not os.path.exists(saves_backup):
            shutil.copytree(self.saves_path, saves_backup)
            print(f"Created backup of saves folder at {saves_backup}")
    
    def _migrate_config_data(self) -> bool:
        """Migrate configuration files to JSON format."""
        success = True
        
        try:
            # Force loading of all config data - this will trigger migration
            # from legacy formats to JSON in the repositories
            self.data_manager.get_items()
            self.data_manager.get_crafting_recipes()
            self.data_manager.get_audio_mappings()
            
            print("✓ Configuration data migrated successfully")
            
        except Exception as e:
            print(f"✗ Error migrating configuration data: {e}")
            success = False
        
        return success
    
    def _migrate_save_data(self) -> bool:
        """Migrate all save files to JSON format."""
        if not os.path.exists(self.saves_path):
            print("No saves folder found, skipping save migration")
            return True
        
        success = True
        worlds = self.data_manager.list_worlds()
        
        for world_name in worlds:
            try:
                print(f"Migrating world: {world_name}")
                
                # Loading the game will automatically trigger migration
                # from legacy format to JSON if needed
                game_data = self.data_manager.load_game(world_name)
                
                if game_data:
                    print(f"✓ Successfully migrated world: {world_name}")
                else:
                    print(f"✗ Failed to migrate world: {world_name}")
                    success = False
                    
            except Exception as e:
                print(f"✗ Error migrating world {world_name}: {e}")
                success = False
        
        return success
    
    def verify_migration(self) -> bool:
        """Verify that migration was successful."""
        print("\nVerifying migration...")
        
        success = True
        
        # Check if JSON files were created
        expected_json_files = ['items.json', 'crafting.json', 'audio.json']
        for json_file in expected_json_files:
            json_path = os.path.join(self.data_path, json_file)
            if os.path.exists(json_path):
                print(f"✓ Found {json_file}")
            else:
                print(f"✗ Missing {json_file}")
                success = False
        
        # Check save files
        worlds = self.data_manager.list_worlds()
        for world_name in worlds:
            save_json_path = os.path.join(self.saves_path, world_name, 'save.json')
            if os.path.exists(save_json_path):
                print(f"✓ Found save.json for world: {world_name}")
            else:
                print(f"✗ Missing save.json for world: {world_name}")
                success = False
        
        return success
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """Generate a detailed migration report."""
        report = {
            'config_files': {},
            'save_files': {},
            'summary': {}
        }
        
        # Check config files
        config_files = ['items.json', 'crafting.json', 'audio.json', 'texCoords.txt']
        for config_file in config_files:
            file_path = os.path.join(self.data_path, config_file)
            report['config_files'][config_file] = {
                'exists': os.path.exists(file_path),
                'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
            }
        
        # Check save files
        worlds = self.data_manager.list_worlds()
        for world_name in worlds:
            world_path = os.path.join(self.saves_path, world_name)
            save_json = os.path.join(world_path, 'save.json')
            legacy_save = os.path.join(world_path, 'level.save')
            
            report['save_files'][world_name] = {
                'has_json': os.path.exists(save_json),
                'has_legacy': os.path.exists(legacy_save),
                'json_size': os.path.getsize(save_json) if os.path.exists(save_json) else 0,
                'legacy_size': os.path.getsize(legacy_save) if os.path.exists(legacy_save) else 0
            }
        
        # Generate summary
        total_worlds = len(worlds)
        migrated_worlds = sum(1 for world_data in report['save_files'].values() if world_data['has_json'])
        migrated_configs = sum(1 for config_data in report['config_files'].values() if config_data['exists'])
        
        report['summary'] = {
            'total_worlds': total_worlds,
            'migrated_worlds': migrated_worlds,
            'total_config_files': len(config_files),
            'migrated_config_files': migrated_configs,
            'migration_complete': migrated_worlds == total_worlds and migrated_configs >= 3
        }
        
        return report


def main():
    """Run the migration tool."""
    import sys
    
    if len(sys.argv) > 1:
        game_folder = sys.argv[1]
    else:
        # Use current directory as game folder
        game_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    migrator = DataMigrator(game_folder)
    
    print(f"Game folder: {game_folder}")
    print("=" * 50)
    
    # Run migration
    success = migrator.migrate_all(create_backups=True)
    
    # Verify migration
    if success:
        verification_success = migrator.verify_migration()
        if not verification_success:
            success = False
    
    # Generate report
    report = migrator.generate_migration_report()
    
    print("\n" + "=" * 50)
    print("MIGRATION REPORT")
    print("=" * 50)
    print(f"Total worlds: {report['summary']['total_worlds']}")
    print(f"Migrated worlds: {report['summary']['migrated_worlds']}")
    print(f"Config files migrated: {report['summary']['migrated_config_files']}/{report['summary']['total_config_files']}")
    print(f"Migration complete: {report['summary']['migration_complete']}")
    
    if success:
        print("\n🎉 Migration completed successfully!")
        return 0
    else:
        print("\n❌ Migration completed with errors.")
        return 1


if __name__ == "__main__":
    exit(main())
