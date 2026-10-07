from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
)
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from core.pagination import get_items_per_page

from .forms import (
    ProfileForm,
    UserCreateForm,
    UserUpdateForm,
    WebLoginForm,
    WebPasswordChangeForm,
)
from .models import User


def _is_administrator(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Administrator").exists()
    )


class WebLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = WebLoginForm
    redirect_authenticated_user = True


class WebLogoutView(LogoutView):
    pass


@login_required
def profile(request):
    profile_form = ProfileForm(instance=request.user)

    password_form = WebPasswordChangeForm(request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update-profile":
            profile_form = ProfileForm(
                request.POST,
                instance=request.user,
            )

            if profile_form.is_valid():
                profile_form.save()

                messages.success(
                    request,
                    "Profile updated successfully.",
                )

                return redirect("accounts_web:profile")

        elif action == "change-password":
            password_form = WebPasswordChangeForm(
                request.user,
                request.POST,
            )

            if password_form.is_valid():
                user = password_form.save()

                update_session_auth_hash(
                    request,
                    user,
                )

                messages.success(
                    request,
                    "Password changed successfully.",
                )

                return redirect("accounts_web:profile")

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
        },
    )


@login_required
def user_list(request):
    if not _is_administrator(request.user):
        raise PermissionDenied

    users = User.objects.prefetch_related("groups")

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "email",
    ).strip()

    direction = request.GET.get(
        "direction",
        "asc",
    ).strip()

    if search:
        users = users.filter(
            Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(groups__name__icontains=search)
        ).distinct()

    if status == "active":
        users = users.filter(is_active=True)

    if status == "inactive":
        users = users.filter(is_active=False)

    sort_fields = {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "status": "is_active",
        "last_login": "last_login",
    }

    sort_field = sort_fields.get(
        sort,
        "email",
    )

    if direction == "desc":
        order_by = f"-{sort_field}"
    else:
        direction = "asc"
        order_by = sort_field

    users = users.order_by(
        order_by,
        "id",
    )

    paginator = Paginator(
        users,
        get_items_per_page(),
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "selected_status": status,
        "sort": sort,
        "direction": direction,
    }

    template_name = "accounts/users/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "accounts/users/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
def user_create(request):
    if not _is_administrator(request.user):
        raise PermissionDenied

    if request.method == "POST":
        form = UserCreateForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("accounts_web:user-list")

    else:
        form = UserCreateForm(
            initial={
                "is_active": True,
            }
        )

    return render(
        request,
        "accounts/users/form.html",
        {
            "form": form,
            "page_title": "Add User",
            "page_subtitle": ("Create a user and assign an application role."),
            "submit_label": "Create User",
        },
    )


@login_required
def user_update(
    request,
    pk,
):
    if not _is_administrator(request.user):
        raise PermissionDenied

    user = get_object_or_404(
        User.objects.prefetch_related("groups"),
        pk=pk,
    )

    # A regular Administrator must not be able
    # to modify a Django superuser.
    if user.is_superuser and not request.user.is_superuser:
        raise PermissionDenied

    if request.method == "POST":
        form = UserUpdateForm(
            request.POST,
            instance=user,
        )

        if form.is_valid():
            # Prevent an administrator from locking
            # themselves out of the application.
            if user == request.user:
                if not form.cleaned_data["is_active"]:
                    form.add_error(
                        "is_active",
                        "You cannot deactivate your own account.",
                    )

                selected_role = form.cleaned_data["role"]

                if (
                    not request.user.is_superuser
                    and selected_role.name != "Administrator"
                ):
                    form.add_error(
                        "role",
                        "You cannot remove your own Administrator role.",
                    )

            if not form.errors:
                form.save()

                messages.success(
                    request,
                    "User updated successfully.",
                )

                return redirect("accounts_web:user-list")

    else:
        form = UserUpdateForm(instance=user)

    return render(
        request,
        "accounts/users/form.html",
        {
            "form": form,
            "managed_user": user,
            "page_title": "Edit User",
            "page_subtitle": (f"Update {user.email}."),
            "submit_label": "Save Changes",
        },
    )
