"""
Tests for the secure_config module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from youtube_transcript_extractor.src.utils.secure_config import SecureConfigManager


@pytest.mark.unit
class TestSecureConfigManager:
    """Tests for SecureConfigManager class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = SecureConfigManager(service_name="test_service")
    
    def test_init(self):
        """Test SecureConfigManager initialization."""
        assert self.manager.service_name == "test_service"
        assert self.manager.username == "default_user"
    
    def test_init_with_custom_username(self):
        """Test initialization with custom username."""
        manager = SecureConfigManager(service_name="test", username="custom_user")
        assert manager.username == "custom_user"
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_store_credential_success(self, mock_keyring):
        """Test successful credential storage."""
        mock_keyring.set_password.return_value = None
        
        result = self.manager.store_credential("api_key", "test_secret_key")
        
        assert result is True
        mock_keyring.set_password.assert_called_once_with(
            "test_service", 
            "default_user_api_key", 
            "test_secret_key"
        )
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_store_credential_failure(self, mock_keyring):
        """Test credential storage failure."""
        mock_keyring.set_password.side_effect = Exception("Keyring error")
        
        result = self.manager.store_credential("api_key", "test_secret_key")
        
        assert result is False
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_retrieve_credential_success(self, mock_keyring):
        """Test successful credential retrieval."""
        mock_keyring.get_password.return_value = "retrieved_secret"
        
        result = self.manager.retrieve_credential("api_key")
        
        assert result == "retrieved_secret"
        mock_keyring.get_password.assert_called_once_with(
            "test_service",
            "default_user_api_key"
        )
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_retrieve_credential_not_found(self, mock_keyring):
        """Test credential retrieval when not found."""
        mock_keyring.get_password.return_value = None
        
        result = self.manager.retrieve_credential("api_key")
        
        assert result is None
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_retrieve_credential_failure(self, mock_keyring):
        """Test credential retrieval failure."""
        mock_keyring.get_password.side_effect = Exception("Keyring error")
        
        result = self.manager.retrieve_credential("api_key")
        
        assert result is None
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_delete_credential_success(self, mock_keyring):
        """Test successful credential deletion."""
        mock_keyring.delete_password.return_value = None
        
        result = self.manager.delete_credential("api_key")
        
        assert result is True
        mock_keyring.delete_password.assert_called_once_with(
            "test_service",
            "default_user_api_key"
        )
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_delete_credential_not_found(self, mock_keyring):
        """Test credential deletion when not found."""
        from keyring.errors import PasswordDeleteError
        mock_keyring.delete_password.side_effect = PasswordDeleteError("Not found")
        
        result = self.manager.delete_credential("api_key")
        
        assert result is False
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_delete_credential_failure(self, mock_keyring):
        """Test credential deletion failure."""
        mock_keyring.delete_password.side_effect = Exception("Keyring error")
        
        result = self.manager.delete_credential("api_key")
        
        assert result is False
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_list_stored_credentials_success(self, mock_keyring):
        """Test listing stored credentials."""
        # Mock the credential listing functionality
        mock_credentials = [
            Mock(service="test_service", username="default_user_api_key"),
            Mock(service="test_service", username="default_user_db_password"),
            Mock(service="other_service", username="other_user_key"),
        ]
        
        # Mock the keyring backend
        mock_backend = Mock()
        mock_backend.get_all_credentials.return_value = mock_credentials
        mock_keyring.get_keyring.return_value = mock_backend
        
        result = self.manager.list_stored_credentials()
        
        expected = ["api_key", "db_password"]
        assert result == expected
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_list_stored_credentials_no_backend_support(self, mock_keyring):
        """Test listing credentials when backend doesn't support it."""
        mock_keyring.get_keyring.return_value = Mock(spec=[])  # No get_all_credentials
        
        # Mock load_config to return empty config to avoid fallback
        with patch.object(self.manager, 'load_config', return_value={}):
            result = self.manager.list_stored_credentials()
            assert result == []
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_list_stored_credentials_failure(self, mock_keyring):
        """Test listing credentials failure."""
        mock_keyring.get_keyring.side_effect = Exception("Backend error")
        
        # Mock load_config to return empty config to avoid fallback
        with patch.object(self.manager, 'load_config', return_value={}):
            result = self.manager.list_stored_credentials()
            assert result == []
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_credential_exists_true(self, mock_keyring):
        """Test checking if credential exists (true case)."""
        mock_keyring.get_password.return_value = "some_value"
        
        result = self.manager.credential_exists("api_key")
        
        assert result is True
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_credential_exists_false(self, mock_keyring):
        """Test checking if credential exists (false case)."""
        mock_keyring.get_password.return_value = None
        
        result = self.manager.credential_exists("api_key")
        
        assert result is False
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_update_credential_success(self, mock_keyring):
        """Test successful credential update."""
        mock_keyring.get_password.return_value = "old_value"  # Exists
        mock_keyring.set_password.return_value = None
        
        result = self.manager.update_credential("api_key", "new_value")
        
        assert result is True
        mock_keyring.set_password.assert_called_once_with(
            "test_service",
            "default_user_api_key",
            "new_value"
        )
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_update_credential_not_exists(self, mock_keyring):
        """Test updating credential that doesn't exist."""
        mock_keyring.get_password.return_value = None  # Doesn't exist
        
        result = self.manager.update_credential("api_key", "new_value")
        
        assert result is False
        mock_keyring.set_password.assert_not_called()
    
    def test_generate_key_name(self):
        """Test key name generation."""
        key_name = self.manager._generate_key_name("api_key")
        assert key_name == "default_user_api_key"
        
        key_name = self.manager._generate_key_name("database_password")
        assert key_name == "default_user_database_password"
    
    def test_extract_credential_name(self):
        """Test extracting credential name from key."""
        cred_name = self.manager._extract_credential_name("default_user_api_key")
        assert cred_name == "api_key"
        
        cred_name = self.manager._extract_credential_name("default_user_database_password")
        assert cred_name == "database_password"
        
        # Test with wrong prefix
        cred_name = self.manager._extract_credential_name("other_user_api_key")
        assert cred_name is None
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_validate_keyring_availability_available(self, mock_keyring):
        """Test keyring availability check when available."""
        mock_keyring.get_keyring.return_value = Mock()
        
        result = self.manager.validate_keyring_availability()
        
        assert result is True
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_validate_keyring_availability_unavailable(self, mock_keyring):
        """Test keyring availability check when unavailable."""
        mock_keyring.get_keyring.side_effect = Exception("No backend available")
        
        result = self.manager.validate_keyring_availability()
        
        assert result is False
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_get_keyring_backend_info(self, mock_keyring):
        """Test getting keyring backend information."""
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "WinVaultKeyring"
        mock_backend.priority = 5
        mock_keyring.get_keyring.return_value = mock_backend
        
        result = self.manager.get_keyring_backend_info()
        
        assert "backend" in result
        assert "priority" in result
        assert result["backend"] == "WinVaultKeyring"
        assert result["priority"] == 5
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_get_keyring_backend_info_failure(self, mock_keyring):
        """Test getting keyring backend info failure."""
        mock_keyring.get_keyring.side_effect = Exception("Backend error")
        
        result = self.manager.get_keyring_backend_info()
        
        assert result == {}
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_bulk_store_credentials_success(self, mock_keyring):
        """Test bulk credential storage."""
        mock_keyring.set_password.return_value = None
        
        credentials = {
            "api_key": "secret_key_value",
            "db_password": "secret_db_password",
            "auth_token": "secret_token"
        }
        
        results = self.manager.bulk_store_credentials(credentials)
        
        assert len(results) == 3
        assert all(results.values())  # All should be True
        assert mock_keyring.set_password.call_count == 3
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_bulk_store_credentials_partial_failure(self, mock_keyring):
        """Test bulk credential storage with partial failure."""
        # Mock to fail on second call
        mock_keyring.set_password.side_effect = [None, Exception("Error"), None]
        
        credentials = {
            "api_key": "secret_key_value",
            "db_password": "secret_db_password",
            "auth_token": "secret_token"
        }
        
        results = self.manager.bulk_store_credentials(credentials)
        
        assert len(results) == 3
        assert results["api_key"] is True
        assert results["db_password"] is False
        assert results["auth_token"] is True
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_bulk_retrieve_credentials_success(self, mock_keyring):
        """Test bulk credential retrieval."""
        mock_keyring.get_password.side_effect = [
            "secret_key_value",
            "secret_db_password",
            None  # Not found
        ]
        
        credential_names = ["api_key", "db_password", "missing_key"]
        
        results = self.manager.bulk_retrieve_credentials(credential_names)
        
        assert len(results) == 3
        assert results["api_key"] == "secret_key_value"
        assert results["db_password"] == "secret_db_password"
        assert results["missing_key"] is None
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_clear_all_credentials_success(self, mock_keyring):
        """Test clearing all credentials."""
        # Mock listing credentials
        mock_credentials = [
            Mock(service="test_service", username="default_user_api_key"),
            Mock(service="test_service", username="default_user_db_password"),
        ]
        
        mock_backend = Mock()
        mock_backend.get_all_credentials.return_value = mock_credentials
        mock_keyring.get_keyring.return_value = mock_backend
        mock_keyring.delete_password.return_value = None
        
        result = self.manager.clear_all_credentials()
        
        assert result == 2  # Two credentials cleared
        assert mock_keyring.delete_password.call_count == 2
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_clear_all_credentials_no_credentials(self, mock_keyring):
        """Test clearing credentials when none exist."""
        mock_backend = Mock()
        mock_backend.get_all_credentials.return_value = []
        mock_keyring.get_keyring.return_value = mock_backend
        
        result = self.manager.clear_all_credentials()
        
        assert result == 0
        mock_keyring.delete_password.assert_not_called()


@pytest.mark.integration
class TestSecureConfigManagerIntegration:
    """Integration tests for SecureConfigManager."""
    
    @patch('youtube_transcript_extractor.src.utils.secure_config.keyring')
    def test_full_credential_lifecycle(self, mock_keyring):
        """Test complete credential lifecycle: store, retrieve, update, delete."""
        manager = SecureConfigManager("test_integration")
        
        # Mock keyring responses
        stored_value = None
        
        def mock_set_password(service, username, password):
            nonlocal stored_value
            stored_value = password
        
        def mock_get_password(service, username):
            return stored_value
        
        def mock_delete_password(service, username):
            nonlocal stored_value
            if stored_value is None:
                from keyring.errors import PasswordDeleteError
                raise PasswordDeleteError("Not found")
            stored_value = None
        
        mock_keyring.set_password.side_effect = mock_set_password
        mock_keyring.get_password.side_effect = mock_get_password
        mock_keyring.delete_password.side_effect = mock_delete_password
        
        # Test storage
        assert manager.store_credential("test_key", "test_value") is True
        
        # Test retrieval
        assert manager.retrieve_credential("test_key") == "test_value"
        
        # Test existence check
        assert manager.credential_exists("test_key") is True
        
        # Test update
        assert manager.update_credential("test_key", "updated_value") is True
        assert manager.retrieve_credential("test_key") == "updated_value"
        
        # Test deletion
        assert manager.delete_credential("test_key") is True
        assert manager.retrieve_credential("test_key") is None
        assert manager.credential_exists("test_key") is False
    
    def test_multiple_managers_isolation(self):
        """Test that multiple managers with different service names are isolated."""
        manager1 = SecureConfigManager("service1")
        manager2 = SecureConfigManager("service2")
        
        # Key names should be different
        key1 = manager1._generate_key_name("api_key")
        key2 = manager2._generate_key_name("api_key")
        
        assert key1 == "default_user_api_key"
        assert key2 == "default_user_api_key"
        
        # But service names should be different
        assert manager1.service_name != manager2.service_name


if __name__ == '__main__':
    pytest.main([__file__])
