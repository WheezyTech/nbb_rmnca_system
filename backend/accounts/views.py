from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {
                "success": False,
                "message": "Username and password are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(
        username=username,
        password=password,
    )

    if user is None:
        return Response(
            {
                "success": False,
                "message": "Invalid username or password."
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {
                "success": False,
                "message": "This account is inactive."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "success": True,
            "message": "Login successful.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role,
                "facility": (
                    user.facility.name
                    if user.facility
                    else None
                ),
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user

    return Response(
        {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "facility": (
                {
                    "id": user.facility.id,
                    "name": user.facility.name,
                    "code": user.facility.facility_code,
                }
                if user.facility
                else None
            ),
        }
    )