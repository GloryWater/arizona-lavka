"""
Security Configuration Validator for Arizona Lavka Marketplace

This script validates that all required security settings are properly configured
before starting the application.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add backend to path to import modules
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from utils.secrets_manager import validate_required_secrets, get_secret


def validate_security_configuration() -> Tuple[bool, Dict[str, str]]:
    """
    Validates that all required security configurations are present.
    
    Returns:
        Tuple of (is_valid, validation_results)
    """
    required_secrets = [
        'POSTGRES_PASSWORD',
        'JWT_SECRET_KEY',
        'CLOUDFLARE_TURNSTILE_SECRET_KEY',
        'GMAIL_APP_PASSWORD',
        'GMAIL_USERNAME',
        'CLOUDFLARE_TURNSTILE_SITE_KEY'
    ]
    
    validation_results = validate_required_secrets(required_secrets)
    
    # Additional checks
    additional_checks = {}
    
    # Check JWT secret length
    jwt_secret = get_secret('JWT_SECRET_KEY')
    if jwt_secret:
        additional_checks['JWT_SECRET_LENGTH'] = len(jwt_secret) >= 32
    else:
        additional_checks['JWT_SECRET_LENGTH'] = False
    
    # Check if running in production without proper secrets
    is_production = os.getenv('PRODUCTION', 'false').lower() == 'true'
    prod_secrets_available = all(validation_results.values())
    additional_checks['PRODUCTION_SECRETS'] = not is_production or prod_secrets_available
    
    # Combine all results
    all_valid = all(validation_results.values()) and all(additional_checks.values())
    
    full_results = {**validation_results, **additional_checks}
    
    return all_valid, full_results


def print_validation_report(is_valid: bool, results: Dict[str, str]):
    """Prints a formatted validation report."""
    print("=" * 60)
    print("VALIDATION REPORT FOR ARIZONA LAVKA MARKETPLACE SECURITY CONFIGURATION")
    print("=" * 60)
    
    print("\nRequired Secrets Status:")
    for key, value in results.items():
        if key in ['JWT_SECRET_LENGTH', 'PRODUCTION_SECRETS']:
            continue  # Skip additional checks for now
        status = "✅ OK" if value else "❌ MISSING"
        print(f"  {key:<30} {status}")
    
    print("\nAdditional Security Checks:")
    for key, value in results.items():
        if key not in ['JWT_SECRET_LENGTH', 'PRODUCTION_SECRETS']:
            continue  # Only show additional checks here
        status = "✅ OK" if value else "❌ FAILED"
        if key == 'JWT_SECRET_LENGTH':
            desc = "JWT secret length >= 32 chars"
        elif key == 'PRODUCTION_SECRETS':
            desc = "Proper secrets in production mode"
        else:
            desc = key
        print(f"  {desc:<30} {status}")
    
    print("\n" + "=" * 60)
    if is_valid:
        print("✅ ALL SECURITY CHECKS PASSED - Application can start safely")
    else:
        print("❌ SOME SECURITY CHECKS FAILED - Please fix before starting")
    print("=" * 60)


def main():
    """Main function to run the security validation."""
    print("🔍 Validating Arizona Lavka Marketplace security configuration...")
    
    is_valid, results = validate_security_configuration()
    
    print_validation_report(is_valid, results)
    
    if not is_valid:
        print("\n🚨 SECURITY VALIDATION FAILED!")
        print("Please ensure all required secrets are properly configured.")
        print("Refer to SECURITY_SETUP.md for instructions.")
        sys.exit(1)
    else:
        print("\n✅ Security validation passed successfully!")
        print("Application is ready to start with secure configuration.")


if __name__ == "__main__":
    main()