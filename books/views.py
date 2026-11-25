from rest_framework import generics, permissions
from .models import Book
from .serializers import BookSerializer
from .permissions import IsOwnerOrReadOnly


class BookListCreateView(generics.ListCreateAPIView):
    """
    GET /books/   -> list all books (authenticated users only)
    POST /books/  -> create a new book (authenticated user becomes owner)
    """
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # All authenticated users can see all books
        return Book.objects.all()

    def perform_create(self, serializer):
        # Owner is always the current user
        serializer.save(owner=self.request.user)


class BookRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /books/<id>/      -> view single book
    PUT/PATCH /books/<id>/ -> update book (owner only)
    DELETE /books/<id>/    -> delete book (owner only)
    """
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Book.objects.all()
