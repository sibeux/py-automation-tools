"""
Buat password hash.
"""

import bcrypt

password = b"a"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())