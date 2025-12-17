from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .forms import CandidateForm
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
    fullname_value = ""
    email_value = ""

    if request.method == "POST":
        fullname_value = (request.POST.get("fullname") or "").strip()
        email_value = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        if not fullname_value or not email_value or not password:
            error = "Заполните все поля."
        else:
            User = get_user_model()
            if User.objects.filter(email=email_value).exists():
                error = "Пользователь с такой почтой уже существует."
            else:
                parts = fullname_value.split()
                first_name = parts[0]
                last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

                user = User.objects.create_user(
                    email=email_value,
                    username=email_value,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )
                login(request, user)
                return redirect("bet")

    return render(
        request,
        "RegistrationPage.html",
        {"error": error, "fullname": fullname_value, "email": email_value},
    )


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("home")


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
                    Bet.objects.create(
                        user=request.user,
                        candidate=candidate,
                        amount=amount,
                        coefficient=Decimal("1"),
                    )
                    message = "Ставка принята!"
                    amount_value = ""

    return render(
        request,
        "candidates/detail.html",
        {"candidate": candidate, "error": error, "message": message, "amount_value": amount_value},
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
