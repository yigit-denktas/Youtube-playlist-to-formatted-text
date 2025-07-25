"""
Secure configuration management with encrypted storage.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING, List
import logging

# Use centralized dependency management
from .dependencies import safe_import, is_available

# Import optional dependencies using the centralized system
keyring, KEYRING_AVAILABLE = safe_import("keyring", "keyring")
Fernet, CRYPTOGRAPHY_AVAILABLE = safe_import("cryptography.fernet", "cryptography")


class SecureConfigManager:
    """Secure configuration management with encrypted storage."""
    
    SERVICE_NAME = "YouTubeTranscriptExtractor"
    CONFIG_FILE = Path.home() / ".yte_config.enc"
    
    def __init__(self, service_name: Optional[str] = None, username: str = "default_user"):
        """Initialize secure configuration manager.
        
        Args:
            service_name: Optional service name for keyring storage
            username: Username for keyring storage
        """
        self.service_name = service_name or self.SERVICE_NAME
        self.username = username
        self.logger = logging.getLogger(__name__)
        self._cipher: Optional[Any] = None
        
        if not KEYRING_AVAILABLE:
            self.logger.warning("Keyring package not available. API keys will not be stored securely.")
            return
        
        if CRYPTOGRAPHY_AVAILABLE:
            try:
                self._cipher = self._get_or_create_cipher()
            except Exception as e:
                self.logger.warning(f"Could not initialize encryption: {e}. Using keyring only.")
        else:
            self.logger.warning("Cryptography package not available. Config files will not be encrypted.")
    
    def _get_or_create_cipher(self) -> Optional[Any]:
        """Get or create encryption key."""
        if not KEYRING_AVAILABLE or not CRYPTOGRAPHY_AVAILABLE:
            return None
            
        try:
            if keyring is None or Fernet is None:
                return None
                
            key = keyring.get_password(self.service_name, "encryption_key")
            if not key:
                key = Fernet.generate_key().decode()
                keyring.set_password(self.service_name, "encryption_key", key)
            return Fernet(key.encode())
        except Exception as e:
            self.logger.error(f"Failed to create cipher: {e}")
            return None
    
    def store_api_key(self, key_name: str, key_value: str) -> bool:
        """Store API key securely using keyring.
        
        Args:
            key_name: Name/identifier for the API key
            key_value: The actual API key value
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not KEYRING_AVAILABLE or keyring is None:
            self.logger.error("Keyring not available. Cannot store API key securely.")
            return False
            
        try:
            full_key_name = self._generate_key_name(key_name)
            keyring.set_password(self.service_name, full_key_name, key_value)
            self.logger.info(f"Successfully stored API key: {key_name}")
            self._update_stored_keys_list(key_name, 'add')
            return True
        except Exception as e:
            self.logger.error(f"Failed to store API key {key_name}: {e}")
            return False
    
    def get_api_key(self, key_name: str) -> Optional[str]:
        """Retrieve API key securely from keyring.
        
        Args:
            key_name: Name/identifier for the API key
            
        Returns:
            API key value or None if not found/error
        """
        if not KEYRING_AVAILABLE or keyring is None:
            self.logger.warning("Keyring not available. Cannot retrieve API key securely.")
            return None
            
        try:
            full_key_name = self._generate_key_name(key_name)
            key = keyring.get_password(self.service_name, full_key_name)
            if key:
                self.logger.debug(f"Successfully retrieved API key: {key_name}")
            return key
        except Exception as e:
            self.logger.error(f"Failed to retrieve API key {key_name}: {e}")
            return None
    
    def delete_api_key(self, key_name: str) -> bool:
        """Delete API key from secure storage.
        
        Args:
            key_name: Name/identifier for the API key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not KEYRING_AVAILABLE or keyring is None:
            self.logger.error("Keyring not available. Cannot delete API key.")
            return False
            
        try:
            full_key_name = self._generate_key_name(key_name)
            keyring.delete_password(self.service_name, full_key_name)
            self.logger.info(f"Successfully deleted API key: {key_name}")
            self._update_stored_keys_list(key_name, 'remove')
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete API key {key_name}: {e}")
            return False
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save encrypted configuration to file.
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self._cipher or not CRYPTOGRAPHY_AVAILABLE or Fernet is None:
                # Fallback to plain JSON if encryption not available
                self.logger.warning("Encryption not available, saving as plain JSON")
                config_file = self.CONFIG_FILE.with_suffix('.json')
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                return True
            
            json_str = json.dumps(config, indent=2)
            encrypted = self._cipher.encrypt(json_str.encode())
            
            # Ensure directory exists
            self.CONFIG_FILE.parent.mkdir(exist_ok=True)
            self.CONFIG_FILE.write_bytes(encrypted)
            
            self.logger.info(f"Configuration saved to {self.CONFIG_FILE}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """Load encrypted configuration from file.
        
        Returns:
            Configuration dictionary or empty dict if not found/error
        """
        try:
            # Try encrypted file first
            if self.CONFIG_FILE.exists() and self._cipher and CRYPTOGRAPHY_AVAILABLE:
                encrypted_data = self.CONFIG_FILE.read_bytes()
                decrypted = self._cipher.decrypt(encrypted_data)
                config = json.loads(decrypted.decode())
                self.logger.info(f"Configuration loaded from {self.CONFIG_FILE}")
                return config
            
            # Fallback to plain JSON
            json_file = self.CONFIG_FILE.with_suffix('.json')
            if json_file.exists():
                with open(json_file, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Configuration loaded from {json_file}")
                return config
            
            self.logger.info("No configuration file found, returning empty config")
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def migrate_from_env(self, env_file: str = ".env") -> bool:
        """Migrate API keys from .env file to secure storage.
        
        Args:
            env_file: Path to the .env file
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            if not os.path.exists(env_file):
                self.logger.info("No .env file found, nothing to migrate")
                return True
            
            if not KEYRING_AVAILABLE or keyring is None:
                self.logger.warning("Keyring not available. Cannot migrate API keys to secure storage.")
                return False
            
            # Read .env file
            api_keys_migrated = 0
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('API_KEY=') and '=' in line:
                        key_value = line.split('=', 1)[1].strip().strip('"\'')
                        if key_value and key_value != 'your_api_key_here':
                            if self.store_api_key("gemini_api_key", key_value):
                                api_keys_migrated += 1
                                self.logger.info("Migrated Gemini API key from .env")
            
            if api_keys_migrated > 0:
                self.logger.info(f"Successfully migrated {api_keys_migrated} API key(s)")
                
                # Optionally create a backup and comment out the key
                try:
                    with open(env_file, 'r') as f:
                        lines = f.readlines()
                    
                    with open(env_file, 'w') as f:
                        for line in lines:
                            if line.strip().startswith('API_KEY='):
                                f.write(f"# Migrated to secure storage: {line}")
                            else:
                                f.write(line)
                    
                    self.logger.info(f"Commented out API_KEY in {env_file}")
                except Exception as e:
                    self.logger.warning(f"Could not update .env file: {e}")
                
                return True
            else:
                self.logger.info("No API keys found in .env file to migrate")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to migrate from .env: {e}")
            return False
    
    def list_stored_keys(self) -> List[str]:
        """List all stored API key names.
        
        Returns:
            List of API key names stored in keyring
        """
        try:
            # Try to get credentials from keyring backend first
            if KEYRING_AVAILABLE:
                try:
                    backend = keyring.get_keyring()
                    if hasattr(backend, 'get_all_credentials'):
                        credentials = backend.get_all_credentials()
                        keys = []
                        for cred in credentials:
                            if cred.service == self.service_name and cred.username.startswith(f"{self.username}_"):
                                # Extract the key name from username
                                key_name = self._extract_credential_name(cred.username)
                                if key_name:  # Only add if extraction was successful
                                    keys.append(key_name)
                        return keys
                except Exception as e:
                    self.logger.debug(f"Could not list from keyring backend: {e}")
            
            # Fallback to config file
            config = self.load_config()
            return config.get('stored_keys', [])
        except Exception as e:
            self.logger.error(f"Failed to list stored keys: {e}")
            return []
    
    def _update_stored_keys_list(self, key_name: str, action: str = 'add') -> None:
        """Update the list of stored keys in config.
        
        Args:
            key_name: Name of the API key
            action: 'add' or 'remove'
        """
        try:
            config = self.load_config()
            stored_keys = set(config.get('stored_keys', []))
            
            if action == 'add':
                stored_keys.add(key_name)
            elif action == 'remove':
                stored_keys.discard(key_name)
            
            config['stored_keys'] = list(stored_keys)
            self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"Failed to update stored keys list: {e}")
    
    def is_setup_required(self) -> bool:
        """Check if initial setup is required.
        
        Returns:
            True if setup is needed, False if already configured
        """
        # Check if we have any stored API keys
        gemini_key = self.get_api_key("gemini_api_key")
        return gemini_key is None or gemini_key.strip() == ""
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get security status information.
        
        Returns:
            Dictionary with security status details
        """
        return {
            "keyring_available": KEYRING_AVAILABLE,
            "encryption_available": CRYPTOGRAPHY_AVAILABLE,
            "secure_storage_enabled": KEYRING_AVAILABLE and CRYPTOGRAPHY_AVAILABLE,
            "stored_keys_count": len(self.list_stored_keys()),
            "setup_required": self.is_setup_required()
        }

    # Additional methods expected by tests
    def store_credential(self, key_name: str, key_value: str) -> bool:
        """Store credential securely - alias for store_api_key."""
        return self.store_api_key(key_name, key_value)

    def retrieve_credential(self, key_name: str) -> Optional[str]:
        """Retrieve credential securely - alias for get_api_key."""
        return self.get_api_key(key_name)

    def delete_credential(self, key_name: str) -> bool:
        """Delete credential - alias for delete_api_key."""
        return self.delete_api_key(key_name)

    def list_stored_credentials(self) -> List[str]:
        """List stored credentials - alias for list_stored_keys."""
        return self.list_stored_keys()

    def credential_exists(self, key_name: str) -> bool:
        """Check if credential exists."""
        credential = self.get_api_key(key_name)
        return credential is not None and credential.strip() != ""

    def update_credential(self, key_name: str, key_value: str) -> bool:
        """Update an existing credential."""
        if self.credential_exists(key_name):
            return self.store_api_key(key_name, key_value)
        return False

    def _generate_key_name(self, base_name: str) -> str:
        """Generate a key name for storage."""
        return f"{self.username}_{base_name}"

    def _extract_credential_name(self, key_name: str) -> Optional[str]:
        """Extract credential name from storage key."""
        prefix = f"{self.username}_"
        if key_name.startswith(prefix):
            return key_name[len(prefix):]
        return None

    def validate_keyring_availability(self) -> bool:
        """Validate if keyring is available."""
        if not KEYRING_AVAILABLE or keyring is None:
            return False
        
        try:
            # Try to actually get the keyring backend
            backend = keyring.get_keyring()
            return backend is not None
        except Exception:
            return False

    def get_keyring_backend_info(self) -> Dict[str, Any]:
        """Get keyring backend information."""
        if not KEYRING_AVAILABLE or keyring is None:
            return {"available": False, "backend": None}
        
        try:
            backend = keyring.get_keyring()
            info = {
                "available": True,
                "backend": str(type(backend).__name__),
                "backend_module": str(type(backend).__module__)
            }
            
            # Add priority if available
            if hasattr(backend, 'priority'):
                info["priority"] = backend.priority
                
            return info
        except Exception as e:
            return {}

    def bulk_store_credentials(self, credentials: Dict[str, str]) -> Dict[str, bool]:
        """Store multiple credentials at once."""
        results = {}
        for key_name, key_value in credentials.items():
            results[key_name] = self.store_api_key(key_name, key_value)
        return results

    def bulk_retrieve_credentials(self, key_names: List[str]) -> Dict[str, Optional[str]]:
        """Retrieve multiple credentials at once."""
        results = {}
        for key_name in key_names:
            results[key_name] = self.get_api_key(key_name)
        return results

    def clear_all_credentials(self) -> int:
        """Clear all stored credentials.
        
        Returns:
            Number of credentials cleared
        """
        try:
            stored_keys = self.list_stored_keys()
            success_count = 0
            for key_name in stored_keys:
                if self.delete_api_key(key_name):
                    success_count += 1
            
            return success_count
        except Exception as e:
            self.logger.error(f"Failed to clear all credentials: {e}")
            return 0


class SecureMigrationHelper:
    """Helper class for migrating from old configuration methods."""
    
    def __init__(self, secure_manager: SecureConfigManager):
        """Initialize migration helper.
        
        Args:
            secure_manager: SecureConfigManager instance
        """
        self.secure_manager = secure_manager
        self.logger = logging.getLogger(__name__)
    
    def migrate_from_plaintext(self, old_config_file: str) -> bool:
        """Migrate from plaintext configuration file.
        
        Args:
            old_config_file: Path to old configuration file
            
        Returns:
            True if migration successful
        """
        try:
            if not os.path.exists(old_config_file):
                return True
            
            with open(old_config_file, 'r') as f:
                old_config = json.load(f)
            
            migrated_count = 0
            
            # Migrate API keys
            if 'api_key' in old_config:
                if self.secure_manager.store_api_key("gemini_api_key", old_config['api_key']):
                    migrated_count += 1
                    del old_config['api_key']  # Remove from plaintext
            
            # Save remaining non-sensitive config
            if old_config:  # If there's still non-sensitive config left
                self.secure_manager.save_config(old_config)
            
            # Backup old file
            backup_file = f"{old_config_file}.migrated"
            os.rename(old_config_file, backup_file)
            
            self.logger.info(f"Migrated {migrated_count} sensitive items. Old config backed up to {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return False
    
    def create_migration_report(self) -> Dict[str, Any]:
        """Create a report of the migration process.
        
        Returns:
            Migration report dictionary
        """
        report = {
            "migration_date": str(Path.cwd()),
            "secure_storage_available": True,
            "encrypted_config_available": CRYPTOGRAPHY_AVAILABLE,
            "stored_keys": self.secure_manager.list_stored_keys(),
            "setup_required": self.secure_manager.is_setup_required()
        }
        
        return report
