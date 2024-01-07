import bcrypt

password_input = '1234'
passwd = b'{password_input}'


#
# salt = bcrypt.gensalt()
# hashed = bcrypt.hashpw(passwd, salt)
#
# print(salt)
# print(hashed)
# hash = b'$2b$12$.Ws6sUe3meIkrAqDPoMcjOfHzSf5fYhKrhIn73Y6gVl.sgM.8hw42'
# if bcrypt.checkpw(passwd, hash):
#     print(bcrypt.checkpw(passwd, hash))
# else:
#     print("does not match")

def check_password(input_password, user_password):
    # Assuming input_password is the password entered by a user
    input_password_bytes = input_password.encode('utf-8')  # Convert the input password to bytes
    stored_password_bytes = user_password.encode('utf-8')  # Convert the stored password to bytes

    return bcrypt.checkpw(input_password_bytes, stored_password_bytes)


print(check_password('2024', '$2b$12$UZmcMtog4EgUYs72MhsGSelIsXTgwsDyjv8guBI4DxxbYvzBQjIru'))
