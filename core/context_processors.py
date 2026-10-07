from .services import get_system_settings


def system_settings(request):
    return {
        "system_settings": get_system_settings(),
    }
