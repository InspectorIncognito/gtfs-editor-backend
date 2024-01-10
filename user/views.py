import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserLoginSerializer
from rest_framework.permissions import AllowAny


class UserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.context['user']

        user.session_token = uuid.uuid4()
        user.save()

        return Response({'session_token': user.session_token}, status=status.HTTP_200_OK)
