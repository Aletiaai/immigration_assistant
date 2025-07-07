# Path: hash_passwords.py (New and Improved Version)

from passlib.context import CryptContext
import getpass

# This is the recommended context for new applications
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

if __name__ == "__main__":
    print("--- Interactive User Password Hash Generator ---")
    
    try:
        username = input("Enter the new username: ").strip()
        if not username:
            print("Username cannot be empty. Exiting.")
        else:
            # Use getpass to hide password entry
            password = getpass.getpass("Enter the new password: ")
            
            hashed_password = get_password_hash(password)
            
            print("\n" + "="*40)
            print("COPY THE FOLLOWING LINE and add it inside the USERS dictionary")
            print("in your app/core/config.py file:")
            print("="*40 + "\n")
            # Print the exact line needed
            print(f"    '{username}': '{hashed_password}',")
            print("\n" + "="*40)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")