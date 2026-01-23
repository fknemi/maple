from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from functools import wraps
import json
import jwt
import requests
from datetime import datetime, timedelta
from .models import SocialAccount


# ==============================================================================
# PAGE VIEWS
# ==============================================================================


@require_http_methods(["GET"])
def home(request):
    """Landing page"""
    return render(request, "home.html")


@require_http_methods(["GET"])
def dashboard(request):
    """Main dashboard view"""
    return render(request, "dashboard.html")


@require_http_methods(["GET"])
def habits(request):
    """Habits tracking page"""
    return render(request, "habits.html")


@require_http_methods(["GET"])
def tasks(request):
    """Tasks management page"""
    return render(request, "tasks.html")


@require_http_methods(["GET"])
def stats(request):
    """Statistics and analytics page"""
    return render(request, "stats.html")


@require_http_methods(["GET"])
def profile(request):
    """User profile page"""
    return render(request, "profile.html")


@require_http_methods(["GET"])
def account(request):
    """Account settings page"""
    return render(request, "account.html")


@require_http_methods(["GET"])
def login_page(request):
    """Login page"""
    return render(request, "login.html")


@require_http_methods(["GET"])
def register_page(request):
    """Registration page"""
    return render(request, "register.html")


# ==============================================================================
# AUTHENTICATION HELPERS
# ==============================================================================


def generate_jwt_token(user):
    """Create a JWT token for the given user. Token expires based on settings.JWT_EXPIRATION_DELTA"""
    payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "exp": datetime.utcnow() + settings.JWT_EXPIRATION_DELTA,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def user_to_dict(user):
    """Convert a User model instance to a clean dictionary"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }


def token_required(f):
    """Decorator to protect API endpoints with JWT authentication. Usage: @token_required above any view that needs auth"""

    @wraps(f)
    def decorated(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JsonResponse({"message": "Token is missing!"}, status=401)

        try:
            token = auth_header.split(" ")[1]
            data = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            request.user_data = data

            try:
                request.user = User.objects.get(id=data["user_id"])
            except User.DoesNotExist:
                return JsonResponse({"message": "User not found!"}, status=401)

        except IndexError:
            return JsonResponse({"message": "Token format invalid!"}, status=401)
        except jwt.ExpiredSignatureError:
            return JsonResponse({"message": "Token has expired!"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"message": "Token is invalid!"}, status=401)

        return f(request, *args, **kwargs)

    return decorated


# ==============================================================================
# USER REGISTRATION & LOGIN
# ==============================================================================


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Create a new user account. Expects: username, email, password in JSON body. Returns: JWT token and user data"""
    try:
        data = json.loads(request.body)
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            return JsonResponse(
                {"message": "Missing required fields: username, email, password"},
                status=400,
            )

        if User.objects.filter(username=username).exists():
            return JsonResponse({"message": "Username already exists"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"message": "Email already exists"}, status=400)

        user = User.objects.create(
            username=username, email=email, password=make_password(password)
        )

        token = generate_jwt_token(user)

        return JsonResponse(
            {
                "message": "User registered successfully",
                "token": token,
                "user": user_to_dict(user),
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """Login with email or username and password. Expects: email (can be username), password. Returns: JWT token and user data"""
    try:
        data = json.loads(request.body)
        identifier = data.get("email")
        password = data.get("password")

        if not identifier or not password:
            return JsonResponse({"message": "Missing credentials"}, status=400)

        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            return JsonResponse({"message": "Invalid credentials"}, status=401)

        if not check_password(password, user.password):
            return JsonResponse({"message": "Invalid credentials"}, status=401)

        token = generate_jwt_token(user)

        return JsonResponse(
            {
                "message": "Login successful",
                "token": token,
                "user": user_to_dict(user),
            },
            status=200,
        )

    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
    """Logout endpoint. Client should remove the token from storage"""
    return JsonResponse(
        {
            "message": "Logout successful. Please remove token from client.",
        },
        status=200,
    )


# ==============================================================================
# GITHUB OAUTH AUTHENTICATION
# ==============================================================================


@csrf_exempt
@require_http_methods(["GET"])
def github_login(request):
    """Start the GitHub OAuth flow. Returns the authorization URL to redirect users to"""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        f"scope=user:email"
    )
    return JsonResponse({"auth_url": github_auth_url})


@csrf_exempt
@require_http_methods(["GET"])
def github_callback(request):
    """Handle the callback from GitHub after user authorizes. Creates or logs in the user and redirects to the dashboard"""
    try:
        code = request.GET.get("code")

        if not code:
            return JsonResponse(
                {"message": "No authorization code provided"}, status=400
            )

        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return JsonResponse(
                {"message": "Failed to get access token from GitHub"}, status=400
            )

        user_response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

        github_user = user_response.json()
        github_id = str(github_user.get("id"))
        github_username = github_user.get("login")
        github_email = github_user.get("email")

        if not github_email:
            email_response = requests.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            emails = email_response.json()
            primary_email = next((e for e in emails if e.get("primary")), None)
            if primary_email:
                github_email = primary_email.get("email")

        try:
            social_account = SocialAccount.objects.get(
                provider="github", provider_user_id=github_id
            )
            user = social_account.user
            social_account.access_token = access_token
            social_account.save()

        except SocialAccount.DoesNotExist:
            if github_email:
                try:
                    user = User.objects.get(email=github_email)
                except User.DoesNotExist:
                    user = User.objects.create(
                        username=github_username,
                        email=github_email,
                    )
            else:
                user = User.objects.create(
                    username=github_username,
                    email=f"{github_username}@github.user",
                )

            SocialAccount.objects.create(
                user=user,
                provider="github",
                provider_user_id=github_id,
                access_token=access_token,
            )

        token = generate_jwt_token(user)
        frontend_url = f"{settings.FRONTEND_URL}/api/auth/callback?token={token}"
        return redirect(frontend_url)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)


@require_http_methods(["GET"])
def auth_success(request):
    """Handle the final step of OAuth flow. Sets the token as an HTTP-only cookie and redirects to dashboard"""
    token = request.GET.get("token")

    if not token:
        return JsonResponse({"message": "No token provided"}, status=400)

    response = redirect("/dashboard")

    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=3600 * 24 * 7,
    )

    return response


# ==============================================================================
# PROTECTED API ENDPOINTS
# ==============================================================================


@csrf_exempt
@require_http_methods(["GET"])
@token_required
def get_current_user(request):
    """Get the currently authenticated user's information. Requires valid JWT token in Authorization header"""
    return JsonResponse(
        {
            "user": user_to_dict(request.user),
        },
        status=200,
    )


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def protected_post(request):
    """Example of a protected POST endpoint. Can be used as a template for other authenticated endpoints"""
    try:
        data = json.loads(request.body)

        return JsonResponse(
            {
                "message": "Success",
                "data": data,
                "user": request.user_data,
            },
            status=200,
        )
    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON"}, status=400)
