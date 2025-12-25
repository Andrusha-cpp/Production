from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.utils import timezone

from .forms import CandidateForm, RegistrationForm, ProfileForm, AdminUserForm, ContestForm
from .models import Candidate, Bet, Contest

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


def _get_current_contest():
    return Contest.objects.order_by("-ends_at").first()


def _apply_payouts(contest):
    if not contest or not contest.winner_id:
        return
    if contest.ends_at > timezone.now():
        return
    with transaction.atomic():
        bets = (
            Bet.objects.select_for_update()
            .filter(contest=contest, candidate=contest.winner, paid_out=False)
            .select_related("user")
        )
        if not bets.exists():
            return
        for bet in bets:
            payout = (bet.amount * bet.coefficient).quantize(Decimal("0.01"))
            bet.user.balance = bet.user.balance + payout
            bet.user.save(update_fields=["balance"])
            bet.paid_out = True
            bet.save(update_fields=["paid_out"])


def _calculate_coefficient(candidate, contest):
    """Calculate a simple dynamic coefficient based on the bet pool."""
    if not contest:
        return Decimal("1.10")
    pool_total = Bet.objects.filter(contest=contest).aggregate(total=Sum("amount")).get("total") or Decimal("0")
    candidate_total = (
        candidate.bets.filter(contest=contest).aggregate(total=Sum("amount")).get("total") or Decimal("0")
    )
    # Smoothing to reduce volatility and avoid huge odds for empty pools.
    smoothing = Decimal("200")
    smoothed_coeff = (pool_total + smoothing) / (candidate_total + smoothing)
    coeff = max(Decimal("1.10"), min(smoothed_coeff, Decimal("10.00")))
    return coeff.quantize(Decimal("0.01"))


def index(request):
    if not request.user.is_authenticated:
        return redirect("login")
    contest = _get_current_contest()
    contest_is_open = bool(contest and contest.ends_at > timezone.now())
    search_query = (request.GET.get("q") or "").strip()
    if contest:
        candidates_qs = contest.participants.all().order_by("id")
    else:
        candidates_qs = Candidate.objects.none()
    if search_query:
        candidates_qs = candidates_qs.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(patronymic__icontains=search_query)
            | Q(info__icontains=search_query)
            | Q(group__icontains=search_query)
        )
    paginator = Paginator(candidates_qs, 12)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)
    candidates = [_serialize_candidate(c) for c in page_obj.object_list]
    return render(
        request,
        "MainPage.html",
        {
            "candidates": candidates,
            "search_query": search_query,
            "page_obj": page_obj,
            "contest": contest,
            "contest_is_open": contest_is_open,
        },
    )


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
        .select_related("candidate", "contest")
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

    bet_results = []
    for bet in bets_qs[:5]:
        contest = bet.contest
        status = "Ожидает"
        payout = None
        if contest and contest.winner_id:
            if bet.candidate_id == contest.winner_id:
                status = "Выигрыш"
                payout = (bet.amount * bet.coefficient).quantize(Decimal("0.01"))
            else:
                status = "Проигрыш"
                payout = Decimal("0.00")
        bet_results.append({"bet": bet, "status": status, "payout": payout})

    context = {
        "user_obj": user,
        "bets": bet_results,
        "bets_count": bets_qs.count(),
        "total_amount": stats.get("total_amount") or Decimal("0"),
        "balance": user.balance,
        "last_bet": last_bet,
        "profile_form": profile_form,
        "password_form": password_form,
        "success_profile": success_profile,
        "success_password": success_password,
    }
    return render(request, "ProfilePage.html", context)



@login_required
def bet_view(request):
    bets_qs = Bet.objects.filter(user=request.user).select_related("candidate", "contest").order_by("-created_at")
    paginator = Paginator(bets_qs, 10)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)
    bet_items = []
    for bet in page_obj.object_list:
        status = "Ожидает"
        payout = None
        contest = bet.contest
        if contest and contest.winner_id:
            if bet.candidate_id == contest.winner_id:
                status = "Выигрыш"
                payout = (bet.amount * bet.coefficient).quantize(Decimal("0.01"))
            else:
                status = "Проигрыш"
                payout = Decimal("0.00")
        bet_items.append(
            {
                "id": bet.id,
                "candidate_id": bet.candidate_id,
                "candidate_name": f"{bet.candidate.last_name} {bet.candidate.first_name}",
                "amount": bet.amount,
                "coefficient": bet.coefficient,
                "created_at": bet.created_at,
                "status": status,
                "payout": payout,
            }
        )
    return render(request, "BetPage.html", {"bets": bet_items, "page_obj": page_obj})


@login_required
def candidate_list(request):
    candidates_qs = Candidate.objects.all().order_by("id")
    paginator = Paginator(candidates_qs, 12)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)
    return render(request, "candidates/list.html", {"page_obj": page_obj})


@login_required
def candidate_detail(request, pk):
    contest = _get_current_contest()
    if contest:
        candidate = get_object_or_404(Candidate, pk=pk, contests=contest)
    else:
        candidate = get_object_or_404(Candidate, pk=pk)
    error = None
    message = None
    amount_value = ""
    coefficient = _calculate_coefficient(candidate, contest)
    bet_limit = Decimal("1000")
    contest_is_open = bool(contest and contest.ends_at > timezone.now())

    if request.method == "POST":
        amount_value = (request.POST.get("amount") or "").strip()
        if not contest:
            error = "Конкурс пока не создан. Ставки недоступны."
        elif not contest_is_open:
            error = "Приём ставок завершён."
        elif not amount_value:
            error = "Введите сумму ставки."
        else:
            try:
                amount = Decimal(amount_value)
            except (InvalidOperation, ValueError):
                error = "Неверный формат суммы."
            else:
                if amount <= 0:
                    error = "Сумма должна быть больше 0."
                elif amount > bet_limit:
                    error = f"Сумма превышает допустимый лимит ({bet_limit} BYN)."
                else:
                    with transaction.atomic():
                        User = get_user_model()
                        user_locked = User.objects.select_for_update().get(pk=request.user.pk)
                        if user_locked.balance < amount:
                            error = "Недостаточно средств."
                        else:
                            coefficient = _calculate_coefficient(candidate, contest)
                            Bet.objects.create(
                                user=user_locked,
                                candidate=candidate,
                                contest=contest,
                                amount=amount,
                                coefficient=coefficient,
                            )
                            user_locked.balance = user_locked.balance - amount
                            user_locked.save(update_fields=["balance"])
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
            "bet_limit": bet_limit,
            "contest": contest,
            "contest_is_open": contest_is_open,
        },
    )


@login_required
def candidate_create(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
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
    if not request.user.is_staff:
        return HttpResponseForbidden()
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
    if not request.user.is_staff:
        return HttpResponseForbidden()
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == "POST":
        candidate.delete()
        return redirect("candidate-list")
    return render(
        request,
        "candidates/confirm_delete.html",
        {"candidate": candidate},
    )


@login_required
def user_list(request):
    if not request.user.is_staff:
        return redirect("home")
    User = get_user_model()
    users = User.objects.all().order_by("id")
    return render(request, "users/list.html", {"users": users})


@login_required
def user_create(request):
    if not request.user.is_staff:
        return redirect("home")
    if request.method == "POST":
        form = AdminUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("user-list")
    else:
        form = AdminUserForm()
    return render(request, "users/detail.html", {"form": form, "user_obj": None})


@login_required
def user_update(request, pk):
    if not request.user.is_staff:
        return redirect("home")
    User = get_user_model()
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = AdminUserForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            return redirect("user-list")
    else:
        form = AdminUserForm(instance=user_obj)
    return render(request, "users/detail.html", {"form": form, "user_obj": user_obj})


@login_required
def user_delete(request, pk):
    if not request.user.is_staff:
        return redirect("home")
    User = get_user_model()
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user_obj.delete()
        return redirect("user-list")
    return render(request, "users/confirm_delete.html", {"user_obj": user_obj})


@login_required
def contest_list(request):
    if not request.user.is_staff:
        return redirect("home")
    contests = Contest.objects.order_by("-ends_at")
    return render(request, "contests/list.html", {"contests": contests})


@login_required
def contest_create(request):
    if not request.user.is_staff:
        return redirect("home")
    if request.method == "POST":
        form = ContestForm(request.POST)
        if form.is_valid():
            contest = form.save()
            _apply_payouts(contest)
            return redirect("contest-list")
    else:
        form = ContestForm()
    return render(request, "contests/form.html", {"form": form, "title": "Новый конкурс"})


@login_required
def contest_update(request, pk):
    if not request.user.is_staff:
        return redirect("home")
    contest = get_object_or_404(Contest, pk=pk)
    if request.method == "POST":
        form = ContestForm(request.POST, instance=contest)
        if form.is_valid():
            contest = form.save()
            _apply_payouts(contest)
            return redirect("contest-list")
    else:
        form = ContestForm(instance=contest)
    return render(
        request,
        "contests/form.html",
        {"form": form, "title": f"Редактирование: {contest.name}"},
    )


@login_required
def contest_delete(request, pk):
    if not request.user.is_staff:
        return redirect("home")
    contest = get_object_or_404(Contest, pk=pk)
    if request.method == "POST":
        contest.delete()
        return redirect("contest-list")
    return render(request, "contests/confirm_delete.html", {"contest": contest})
