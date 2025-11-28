from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.

class Airport(models.Model):
    code = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True,null=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code

class Route(models.Model):
    LEFT = 'left'
    RIGHT = 'right'
    POSITION_CHOICES = [(LEFT, 'Left'), (RIGHT, 'Right')]

    from_airport = models.ForeignKey(Airport, related_name='outgoing_routes', on_delete=models.CASCADE)
    to_airport = models.ForeignKey( Airport, related_name='incoming_routes', on_delete=models.CASCADE)
    position = models.CharField(max_length=5, choices=POSITION_CHOICES)
    duration = models.PositiveIntegerField(help_text='Duration/distance (int)', db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['from_airport', 'position'], name='unique_from_position')
        ]
        indexes = [
            models.Index(fields=['from_airport', 'position']),
            models.Index(fields=['duration']),
        ]


    """clean() method is used for custom model validation before saving the object to the database."""
    def clean(self):
        if self.from_airport_id == self.to_airport_id:
            raise ValidationError("Route cannot be from and to the same airport.")

    def __str__(self):
        return f"{self.from_airport.code} -{self.position}-> {self.to_airport.code} ({self.duration})"
