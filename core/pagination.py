from .services import get_system_settings


def get_items_per_page():
    settings = get_system_settings()

    return max(
        1,
        min(
            settings.items_per_page,
            100,
        ),
    )
