import yaml 
import os
from typing import Dict, List, Any
from pathlib import Path
import logging

# set ip logging for production debugging

logger = logging.getLogger(__name__)

# creating a singleton config manager

class ConfigManager :
    """" Singleton pattern for configuration management.
    - Loads config once
    - Caches in memory
    - Validates on load
    - Provides factory methods for specific use cases
    """
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ConfigManager._config is None:
            ConfigManager._config = self._load_and_validate()
    
    @staticmethod
    def _get_config_path() -> Path:
        """Find config file path"""
        # Get app directory
        app_dir = Path(__file__).parent.parent
        config_path = app_dir / 'config' / 'canonical_schema.yml'
        return config_path


    # add avalidation logic 

    def _load_and_validate(self) -> Dict[str, Any]:
        """
            Load YAML config with comprehensive error handling.
    
            Returns: Loaded and validated configuration
            Raises: Specific exceptions with clear error messages
        """
        config_path =self._get_config_path()

        # ERROR LEVEL ! : FILE MISSING 

        if not config_path.exists():
            error_msg = f"""
                           ❌ CONFIG FILE NOT FOUND
                           Expected path: {config_path}
        
                           How to fix:
                           1. Make sure file exists
                           2. Check path is correct
                           3. Verify filename spelling
                           """
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # ERROR LEVEL ! : invalid yaml syntax 

        try :
            with open(config_path, 'r', encoding= 'utf-8') as file:
                config = yaml.safe_load(file)
            
            if config is None:
                raise ValueError("config file is empty")
        except yaml.YAMLError as e:
            error_msg = f"""
                        ❌ YAML SYNTAX ERROR
                        File: {config_path}
                        Error: {str(e)}
        
                        How to fix:
                        1. Check indentation (YAML is strict about spaces)
                        2. Check colons and dashes
                        3. Use online YAML validator
                        """                
            logger.error(error_msg)
            raise ValueError(error_msg) from e 
        
        # Error level ! : validate structure
        self._validate_config_structure(config)
        logger.info("Config loaded and validated successfully")
        return config

    def _validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate config structure and required fields"""
        required_fields = [
            "canonical_fields",
            "datatype_schema",
            "required_columns",
            "validation_rules"
        ]

        for section in required_fields :
            if section not in config :
                error_msg = f"""
                            ❌ CONFIG STRUCTURE ERROR
                            Missing section: {section}
    
                            How to fix:
                            1. Add missing section to config
                            2. Ensure correct indentation
                            3. Refer to documentation for required fields
                            """
                logger.error(error_msg)
                raise ValueError(error_msg)

#==========================================================================
# LAYER 2: FACTORY METHODS FOR SPECIFIC CONFIG SECTIONS
#==========================================================================

class ConfigManager(ConfigManager) :
    """ extended with factory methods for specific config sections """

    def get_field_mapping(self) -> Dict[str, List[str]]:
        """Get field mapping from config"""
        
        canonical_fields = self._config.get('canonical_fields', {})
        mapping = {}

        for field_name, field_config in canonical_fields.items():
            aliases = field_config.get('aliases', [])
            mapping[field_name] = aliases

        if not mapping :
            logger.warning("No field mapping found in config")    
        return mapping
    
    def get_datatype_schema(self) -> Dict[str, str]:
        """
        Get datatype enforcement schema.
        
        Returns: {
            'sales': 'float64',
            'date': 'datetime64[ns]',
            'quantity': 'int64',
            ...
        }
        """
         
        datatype_schema =  self._config.get('datatype_schema', {})

        if not datatype_schema :
            logger.warning("No datatype schema found in config")
        return datatype_schema
    
    def get_required_columns(self) -> List[str]:
        """
        Get list of REQUIRED columns (must exist in dataset).
        
        Returns: ['sales', 'date', 'product']
        """

        required_columns = self._config.get('required_columns', [])

        if not required_columns :
            logger.warning("No required columns defined in config")
        return required_columns
    
    def get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Get validation rules for each column.
        
        Returns: {
            'sales': {'min': 0, 'max': 1000000},
            'date': {'format': '%Y-%m-%d'},
            'quantity': {'min': 0}
        }
        """
        validation_rules = self._config.get('validation_rules', {})

        if not validation_rules :
            logger.warning("No validation rules defined in config")
        return validation_rules
    
    def get_canonical_schema(self, messy_column : str) -> str :
        """
        Find canonical field name for messy column name.
        
        Example: 'total revenue' → 'sales'
        
        Args: messy_column - Column name from user dataset
        Returns: Canonical field name
        Raises: ValueError if no mapping found
        
        """
        messy_column_layer = messy_column.lower().strip()
        mapping = self.get_field_mapping()

        # search trough all aliases 

        for canonical_field, aliases in mapping.items():
            if any(alias.lower().strip() == messy_column_layer for alias in aliases):
               logger.debug(f"✓ Mapped '{messy_column}' → '{canonical_field}'")
               return canonical_field 
            
        logger.warning(f"No mapping found for '{messy_column}'")
        raise ValueError(f"No mapping found for column: {messy_column}")
    

    def get_raw_config(self) -> Dict[str, Any]:
        """Get raw config dictionary (for debugging)"""
        return self._config.copy()

#==========================================================================
# LAYER 3: MODULE LEVEL FUNCTION FOR EASY ACCESS
#==========================================================================

#Global instance of ConfigManager

_config_manager = None

def initialize_config() -> None :
    """Initialize global config manager instance (call at app startup)"""
    global _config_manager

    if _config_manager is None :
        _config_manager = ConfigManager()
        logger.info("ConfigManager initialized")

def load_schema_config() -> Dict[str, Any] :
    """Module level function to load config (for backward compatibility)"""
    if _config_manager is None :
        initialize_config()
    return _config_manager.get_raw_config()

def get_field_mapping() -> Dict[str, List[str]]:
    """Module level function to get field mapping"""
    if _config_manager is None :
        initialize_config()
    return _config_manager.get_field_mapping()

def get_datatype_schema() -> Dict[str, str]:
    """Module level function to get datatype schema"""
    if _config_manager is None :
        initialize_config()
    return _config_manager.get_datatype_schema()

def get_required_columns() -> List[str]:
    """Module level function to get required columns"""
    if _config_manager is None :
        initialize_config()
    return _config_manager.get_required_columns()

def get_validation_rules() -> Dict[str, Dict[str, Any]]:
    """Module level function to get validation rules"""
    if _config_manager is None :
        initialize_config()
    return _config_manager.get_validation_rules()

def get_canonical_schema(messy_column : str) -> str :
    """Module level function to get canonical schema for a messy column"""
    if _config_manager is None :
        initialize_config()
    return _config_manager.get_canonical_schema(messy_column)