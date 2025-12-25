from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('contest/', views.contest_view, name='contest'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('bet/', views.bet_view, name='bet'),
    path('candidates/', views.candidate_list, name='candidate-list'),
    path('candidates/new/', views.candidate_create, name='candidate-create'),
    path('candidates/<int:pk>/edit/', views.candidate_update, name='candidate-update'),
    path('candidates/<int:pk>/delete/', views.candidate_delete, name='candidate-delete'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate-detail'),
    path('users/', views.user_list, name='user-list'),
    path('users/new/', views.user_create, name='user-create'),
    path('users/<int:pk>/edit/', views.user_update, name='user-update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user-delete'),
    path('contests/', views.contest_list, name='contest-list'),
    path('contests/new/', views.contest_create, name='contest-create'),
    path('contests/<int:pk>/edit/', views.contest_update, name='contest-update'),
    path('contests/<int:pk>/delete/', views.contest_delete, name='contest-delete'),
]
