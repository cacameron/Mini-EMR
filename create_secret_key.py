import os
import secrets

env_path = ".env"
#loads .env
lines = []
if os.pathexists(env_path):
    with open(env_path, "r") as f:
        lines = f.readlines()

#checks if secret key already exists
existing_key = any(line.startswith("SECRET_KEY=") for line in lines)
if existing_key:
    print("SECRET_KEY already exists. No changes made to .env")
else:
    secret_key=secrets.token_hex(32)
    lines.append(f"SECRET_KEY={secret_key}\n")
    
    with open(env_path, "w") as f:
        f.writelines(lines)

    print(f"SECRET_KEY has been generated and added to {env_path}: {secret_key}")