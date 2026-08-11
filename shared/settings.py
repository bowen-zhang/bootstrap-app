import os


class Settings:
    @property
    def is_dev(self) -> bool:
        return os.environ.get("DEV", "") != ""


settings = Settings()