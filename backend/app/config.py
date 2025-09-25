import os
class Settings:
    POSTGRES_DB=os.getenv('POSTGRES_DB','mlagrico')
    POSTGRES_USER=os.getenv('POSTGRES_USER','ml_user')
    POSTGRES_PASSWORD=os.getenv('POSTGRES_PASSWORD','ml_pass')
    DB_HOST=os.getenv('DB_HOST','db')
    DB_PORT=int(os.getenv('DB_PORT','5432'))
    REDIS_HOST=os.getenv('REDIS_HOST','redis')
    REDIS_PORT=int(os.getenv('REDIS_PORT','6379'))
    MAIN_API_BASE=os.getenv('MAIN_API_BASE','http://sistema-principal.local/api')
    API_KEY=os.getenv('API_KEY','dev-local-key')
settings=Settings()
