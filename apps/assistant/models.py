from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    field = models.ForeignKey("farms.Field", on_delete=models.CASCADE, related_name="chat")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # user | assistant
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
