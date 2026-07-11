from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date
from decimal import Decimal
from .models import MealRate, MealLog, ExtraCharge, PaymentLog
from .views import get_monthly_stats

class PGTrackerTestCase(TestCase):
    def setUp(self):
        # Create user and client
        self.username = 'resident'
        self.password = 'testpass123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client = Client()
        self.client.login(username=self.username, password=self.password)

    def test_meal_rate_locking(self):
        """Test that updating a meal rate does not alter past logged costs."""
        # Configure Breakfast rate to 2.00
        rate = MealRate.objects.create(meal_name='Breakfast', rate=Decimal('2.00'))

        # Log Breakfast on July 10th
        date_1 = date(2026, 7, 10)
        log_1 = MealLog.objects.create(
            date=date_1,
            meal_name='Breakfast',
            status='Consumed',
            cost_charged=rate.rate
        )
        self.assertEqual(log_1.cost_charged, Decimal('2.00'))

        # Update Breakfast rate to 2.50
        rate.rate = Decimal('2.50')
        rate.save()

        # Log Breakfast on July 11th
        date_2 = date(2026, 7, 11)
        log_2 = MealLog.objects.create(
            date=date_2,
            meal_name='Breakfast',
            status='Consumed',
            cost_charged=rate.rate
        )
        self.assertEqual(log_2.cost_charged, Decimal('2.50'))

        # Re-fetch log_1 and check it is still 2.00 (rate-locked!)
        log_1.refresh_from_db()
        self.assertEqual(log_1.cost_charged, Decimal('2.00'))

    def test_outstanding_balance_calculation(self):
        """Test calculations: (Meals + Extras) - Payments = Dues."""
        # 1. Setup Rates
        r_breakfast = MealRate.objects.create(meal_name='Breakfast', rate=Decimal('2.00'))
        r_lunch = MealRate.objects.create(meal_name='Lunch', rate=Decimal('3.00'))

        # 2. Log Meals
        d1 = date(2026, 7, 1)
        d2 = date(2026, 7, 2)
        
        MealLog.objects.create(date=d1, meal_name='Breakfast', status='Consumed', cost_charged=r_breakfast.rate) # 2.00
        MealLog.objects.create(date=d1, meal_name='Lunch', status='Skipped', cost_charged=r_lunch.rate) # 0.00 (skipped)
        MealLog.objects.create(date=d2, meal_name='Breakfast', status='Consumed', cost_charged=r_breakfast.rate) # 2.00
        MealLog.objects.create(date=d2, meal_name='Lunch', status='Consumed', cost_charged=r_lunch.rate) # 3.00
        
        # Total meals cost = 2.00 + 2.00 + 3.00 = 7.00

        # 3. Log Extras
        ExtraCharge.objects.create(date=d1, description='Laundry', amount=Decimal('15.00'))
        ExtraCharge.objects.create(date=d2, description='Guest Meal', amount=Decimal('5.50'))
        # Total extras cost = 15.00 + 5.50 = 20.50

        # 4. Log Payments
        PaymentLog.objects.create(date=d2, amount=Decimal('10.00'), method='UPI')
        # Total paid = 10.00

        # 5. Run calculations
        stats = get_monthly_stats(date(2026, 7, 1), date(2026, 7, 31))

        # Expected totals
        # Accrued = 7.00 + 20.50 = 27.50
        # Outstanding = 27.50 - 10.00 = 17.50
        self.assertEqual(stats['meal_cost'], Decimal('7.00'))
        self.assertEqual(stats['extra_cost'], Decimal('20.50'))
        self.assertEqual(stats['total_accrued'], Decimal('27.50'))
        self.assertEqual(stats['total_paid'], Decimal('10.00'))
        self.assertEqual(stats['outstanding'], Decimal('17.50'))

    def test_dashboard_login_required(self):
        """Test that unauthenticated users are redirected to login."""
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
