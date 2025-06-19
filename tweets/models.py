from django.db import models
from django.conf import settings

# Modelo para las publicaciones (helicópteros)
class Post(models.Model):
    nombre = models.CharField(max_length=255)  # Nombre del post
    modelo_helicoptero = models.CharField(max_length=255)  # Modelo del helicóptero
    descripcion = models.TextField(blank=False)  # Descripción
    url = models.URLField(blank=True, null=True)  # Imagen (opcional)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.modelo_helicoptero}"


# Solo dos tipos de reacciones permitidas
REACTION_CHOICES = [
    ('like', 'Like'),
    ('dislike', 'Dislike')
]

# Modelo para reacciones a publicaciones
class Reaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='reactions', on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=7, choices=REACTION_CHOICES)

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type} to post {self.post.id}"


# Modelo para comentarios en publicaciones
class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} commented on post {self.post.id}"
