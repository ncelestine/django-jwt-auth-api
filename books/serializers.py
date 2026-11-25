from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer for the Book model.
    The 'owner' field is read-only and shows the username.
    """
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Book
        fields = ["id", "title", "author", "description", "owner", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]
