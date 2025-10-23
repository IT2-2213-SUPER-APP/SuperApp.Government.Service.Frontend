from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from .models import Profile
from .serializers import RegisterSerializer, UserSerializer, ProfileSerializer


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.

    Allows any user (authenticated or not) to create a new user account.
    Uses the RegisterSerializer to validate and create the user.
    """
    serializer_class = RegisterSerializer
    # Allow any user to access this endpoint for registration purposes.
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Custom create method to return the created user's data upon success.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Return the data of the newly created user using the UserSerializer
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "User Created Successfully. Now perform Login to get your token.",
        })


class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing user profiles.

    A user can only view and edit their own profile.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should only return the profile of the currently authenticated user.
        """
        return Profile.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Retrieves the profile for the current user. We override this to ensure
        a user can only ever access their own profile from this endpoint.
        """
        # The queryset is already filtered for the current user,
        # so we can just get the first object.
        obj = self.get_queryset().first()
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_update(self, serializer):
        """
        Ensure the profile being updated belongs to the request user.
        """
        serializer.save(user=self.request.user)
