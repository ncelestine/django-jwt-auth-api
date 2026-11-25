from django.conf import settings
from django.db import models


class Book(models.Model):
    """
    Book in the catalog.

    - owner: user who created the book
    - title, author, description: basic book info
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="books",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author}"
