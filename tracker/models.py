from django.db import models

class MealRate(models.Model):
    meal_name = models.CharField(max_length=50, unique=True)
    rate = models.DecimalField(max_digits=6, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.meal_name} - {self.rate}"

class MealLog(models.Model):
    STATUS_CHOICES = [
        ('Consumed', 'Consumed'),
        ('Skipped', 'Skipped'),
    ]
    date = models.DateField()
    meal_name = models.CharField(max_length=50)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Skipped')
    cost_charged = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ('date', 'meal_name')

    def __str__(self):
        return f"{self.date} - {self.meal_name} ({self.status}) - {self.cost_charged}"

class ExtraCharge(models.Model):
    date = models.DateField()
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.date} - {self.description}: {self.amount}"

class PaymentLog(models.Model):
    date = models.DateField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.date} - Paid: {self.amount} via {self.method or 'Unknown'}"
