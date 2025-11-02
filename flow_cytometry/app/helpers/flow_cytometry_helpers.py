from app.utils.security import encrypt_data, decrypt_data
import os
from dotenv import load_dotenv

load_dotenv()

def encrypt_flow_cytometry_data(flow_data):
    """
    Encrypts sensitive flow cytometry data before storing it in the database
    
    Args:
        flow_data (dict): Dictionary containing flow cytometry data
    
    Returns:
        dict: Dictionary with encrypted sensitive data
    """
    try:
        # Fields to encrypt
        sensitive_fields = ['filename', 'description', 'file_path', 'workspace', 'timepoint']
        
        # Create a new dictionary with encrypted data
        encrypted_data = flow_data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                # Convert to string if not already
                value = str(encrypted_data[field])
                # Encrypt the value using the security utility
                encrypted_value = encrypt_data(value)
                # Store the encrypted value as string
                encrypted_data[field] = encrypted_value.decode()
        
        return encrypted_data
    
    except Exception as e:
        print(f"Error encrypting flow cytometry data: {str(e)}")
        raise Exception("Failed to encrypt flow cytometry data")

def decrypt_flow_cytometry_data(encrypted_data):
    """
    Decrypts flow cytometry data for frontend display
    
    Args:
        encrypted_data (dict): Dictionary containing encrypted flow cytometry data
    
    Returns:
        dict: Dictionary with decrypted data
    """
    try:
        # Fields to decrypt
        sensitive_fields = ['filename', 'description', 'file_path', 'workspace', 'timepoint']
        
        # Create a new dictionary with decrypted data
        decrypted_data = encrypted_data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                # Decode the encrypted value
                encrypted_value = decrypted_data[field].encode()
                # Decrypt the value using the security utility
                decrypted_value = decrypt_data(encrypted_value)
                # Store the decrypted value
                decrypted_data[field] = decrypted_value
        
        return decrypted_data
    
    except Exception as e:
        print(f"Error decrypting flow cytometry data: {str(e)}")
        raise Exception("Failed to decrypt flow cytometry data")

# Utility function to check if data is already encrypted
def is_encrypted(data):
    """
    Checks if the given data is already encrypted
    
    Args:
        data (str): Data to check
    
    Returns:
        bool: True if data appears to be encrypted, False otherwise
    """
    try:
        if not isinstance(data, str):
            return False
        
        # Try to decode as base64
        decoded = base64.b64decode(data)
        # Check if it has the Fernet version byte
        return len(decoded) >= 32 and decoded[0] == 128
    except:
        return False




