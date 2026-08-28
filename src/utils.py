from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def hashing(password): # for database
    return password_hash.hash(password)