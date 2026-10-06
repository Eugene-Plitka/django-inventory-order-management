ROLE_NAMES = (
    "Administrator",
    "Sales Manager",
    "Purchasing Manager",
    "Warehouse Employee",
)


def user_role(request):
    user = request.user

    if not user.is_authenticated:
        return {
            "current_user_role": None,
        }

    if user.is_superuser:
        return {
            "current_user_role": "Administrator",
        }

    role = (
        user.groups.filter(name__in=ROLE_NAMES)
        .values_list(
            "name",
            flat=True,
        )
        .first()
    )

    return {
        "current_user_role": role,
    }
