TOKEN = 1000

def build_token():
    return str(TOKEN)

def is_token(message: str):
    return message.strip() == str(TOKEN)