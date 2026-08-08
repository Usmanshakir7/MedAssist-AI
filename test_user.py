from database.user_model import create_user, login_user

# Register a user
success, message = create_user(
    "Usman shakir",
    "usman@example.com",
    "123456"
)

print(success)
print(message)

# Login
success, user = login_user(
    "usman@example.com",
    "123456"
)

print(success)

if success:
    print(user["full_name"])
    print(user["email"])