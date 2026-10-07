from .models import SystemSettings


def get_system_settings():
    return SystemSettings.load()
