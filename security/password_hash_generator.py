"""
Buat password hash.
"""

import bcrypt

password = b"testing_password123"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())