from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    database_hostname : str
    database_port : str
    database_name : str
    database_username : str
    database_password :str
    secret_key : str
    algorithm : str
    access_token_expire_minutes : int
    refresh_token_expire_days : int
    class Config:
        env_file = ".env"


setting = Setting()