from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect

from .forms import CandidateForm, RegistrationForm, ProfileForm
from .models import Candidate, Bet

def _serialize_candidate(candidate):
    try:
        photo_url = candidate.photo.url
    except (ValueError, AttributeError):
        photo_url = ""
    return {
        "id": candidate.id,
        "display_name": f"{candidate.last_name} {candidate.first_name}",
        "info": candidate.info,
        "photo_url": photo_url,
    }


def _calculate_coefficient(candidate):
    """Calculate a simple dynamic coefficient based on the bet pool."""
    pool_total = Bet.objects.aggregate(total=Sum("amount")).get("total") or Decimal("0")
    candidate_total = candidate.bets.aggregate(total=Sum("amount")).get("total") or Decimal("0")
    # Add a larger smoothing value to avoid huge spikes when there are few or no bets.
    smoothing = Decimal("1000")
    smoothed_coeff = (pool_total + smoothing) / (candidate_total + smoothing)
    coeff = max(Decimal("1.10"), min(smoothed_coeff, Decimal("10")))
    return coeff.quantize(Decimal("0.01"))


def index(request):
    if not request.user.is_authenticated:
        return redirect("login")
    candidates = [_serialize_candidate(c) for c in Candidate.objects.all().order_by("id")]
    return render(request, "MainPage.html", {"candidates": candidates})


def login_view(request):
    error = None
    email_value = ""

    if request.method == "POST":
        email_value = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        user = authenticate(request, email=email_value, password=password)
        if user:
            login(request, user)
            return redirect("bet")

        error = "Неверная почта или пароль."

    return render(request, "LoginPage.html", {"error": error, "email": email_value})


def register_view(request):
    error = None

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            password = form.cleaned_data["password"]
            User = get_user_model()
            if User.objects.filter(email=email).exists():
                error = "Пользователь с такой почтой уже существует."
            else:
                user = User.objects.create_user(
                    email=email,
                    username=email,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    course=form.cleaned_data.get("course"),
                    group=form.cleaned_data.get("group"),
                    password=password,
                )
                login(request, user)
                return redirect("bet")
    else:
        form = RegistrationForm()

    return render(
        request,
        "RegistrationPage.html",
        {"error": error, "form": form},
    )


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("home")


@login_required
def profile_view(request):
    user = request.user
    bets_qs = (
        Bet.objects.filter(user=user)
        .select_related("candidate")
        .order_by("-created_at")
    )
    stats = bets_qs.aggregate(total_amount=Sum("amount"))
    last_bet = bets_qs.first()
    success_profile = None
    success_password = None

    def _apply_bootstrap(form, labels_override=None):
        for name, field in form.fields.items():
            if labels_override and name in labels_override:
                field.label = labels_override[name]
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_classes + " form-control").strip()

    profile_form = ProfileForm(instance=user)
    password_form = PasswordChangeForm(user)
    password_labels = {
        "old_password": "Старый пароль",
        "new_password1": "Новый пароль",
        "new_password2": "Повторите пароль",
    }

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            profile_form = ProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                success_profile = "Данные профиля обновлены."
        elif action == "password":
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                success_password = "Пароль обновлён."

    _apply_bootstrap(profile_form)
    _apply_bootstrap(password_form, password_labels)

    context = {
        "user_obj": user,
        "bets": bets_qs[:5],
        "bets_count": bets_qs.count(),
        "total_amount": stats.get("total_amount") or Decimal("0"),
        "last_bet": last_bet,
        "profile_form": profile_form,
        "password_form": password_form,
        "success_profile": success_profile,
        "success_password": success_password,
    }
    return render(request, "ProfilePage.html", context)


@login_required
def bet_view(request):
    bets = (
        Bet.objects.filter(user=request.user)
        .select_related("candidate")
        .order_by("-created_at")
    )
    bet_items = []
    for bet in bets:
        bet_items.append(
            {
                "id": bet.id,
                "candidate_id": bet.candidate_id,
                "candidate_name": f"{bet.candidate.last_name} {bet.candidate.first_name}",
                "amount": bet.amount,
                "coefficient": bet.coefficient,
                "created_at": bet.created_at,
            }
        )
    return render(request, "BetPage.html", {"bets": bet_items})


@login_required
def candidate_list(request):
    candidates_qs = Candidate.objects.all().order_by("id")
    paginator = Paginator(candidates_qs, 12)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)
    return render(request, "candidates/list.html", {"page_obj": page_obj})


@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    error = None
    message = None
    amount_value = ""
    coefficient = _calculate_coefficient(candidate)

    if request.method == "POST":
        amount_value = (request.POST.get("amount") or "").strip()
        if not amount_value:
            error = "Введите сумму ставки."
        else:
            try:
                amount = Decimal(amount_value)
            except (InvalidOperation, ValueError):
                error = "Неверный формат суммы."
            else:
                if amount <= 0:
                    error = "Сумма должна быть больше 0."
                else:
                    coefficient = _calculate_coefficient(candidate)
                    Bet.objects.create(
                        user=request.user,
                        candidate=candidate,
                        amount=amount,
                        coefficient=coefficient,
                    )
                    message = "Ставка принята!"
                    amount_value = ""

    return render(
        request,
        "candidates/detail.html",
        {
            "candidate": candidate,
            "error": error,
            "message": message,
            "amount_value": amount_value,
            "coefficient": coefficient,
        },
    )


@login_required
def candidate_create(request):
    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("candidate-list")
    else:
        form = CandidateForm()
    return render(request, "candidates/form.html", {"form": form, "title": "Новая участница"})


@login_required
def candidate_update(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            return redirect("candidate-list")
    else:
        form = CandidateForm(instance=candidate)
    return render(
        request,
        "candidates/form.html",
        {"form": form, "title": f"Редактирование: {candidate.last_name} {candidate.first_name}"},
    )


@login_required
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == "POST":
        candidate.delete()
        return redirect("candidate-list")
    return render(
        request,
        "candidates/confirm_delete.html",
        {"candidate": candidate},
    )
