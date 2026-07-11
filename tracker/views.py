from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse
from datetime import date, datetime, timedelta
from .models import MealRate, MealLog, ExtraCharge, PaymentLog

def get_monthly_stats(start_date, end_date):
    """Calculate totals and outstanding balance for a date range."""
    meal_cost = MealLog.objects.filter(
        date__range=(start_date, end_date),
        status='Consumed'
    ).aggregate(total=Sum('cost_charged'))['total'] or 0

    extra_cost = ExtraCharge.objects.filter(
        date__range=(start_date, end_date)
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_paid = PaymentLog.objects.filter(
        date__range=(start_date, end_date)
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_accrued = meal_cost + extra_cost
    outstanding = total_accrued - total_paid

    return {
        'meal_cost': meal_cost,
        'extra_cost': extra_cost,
        'total_accrued': total_accrued,
        'total_paid': total_paid,
        'outstanding': outstanding
    }

@login_required
def dashboard(request):
    today = timezone.localtime().date()
    start_of_month = today.replace(day=1)
    
    # Calculate end of month
    if today.month == 12:
        end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # Monthly stats
    stats = get_monthly_stats(start_of_month, end_of_month)

    # Today's meals setup
    meal_rates = MealRate.objects.all()
    today_meals = []
    for rate in meal_rates:
        log = MealLog.objects.filter(date=today, meal_name=rate.meal_name).first()
        status = log.status if log else None
        today_meals.append({
            'meal_name': rate.meal_name,
            'rate': rate.rate,
            'status': status
        })

    # Recent 7 days activity
    past_days = []
    for i in range(7):
        d = today - timedelta(days=i)
        day_meals = []
        day_cost = 0
        for rate in meal_rates:
            log = MealLog.objects.filter(date=d, meal_name=rate.meal_name).first()
            status = log.status if log else 'Skipped'
            cost = log.cost_charged if (log and log.status == 'Consumed') else 0
            day_cost += cost
            day_meals.append({
                'name': rate.meal_name,
                'status': status,
                'char': rate.meal_name[0].upper()
            })
        past_days.append({
            'date': d,
            'is_today': d == today,
            'meals': day_meals,
            'cost': day_cost
        })

    context = {
        'today': today,
        'month_name': today.strftime('%B %Y'),
        'stats': stats,
        'today_meals': today_meals,
        'past_days': past_days,
        'has_rates': meal_rates.exists()
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def balance_summary(request):
    """HTMX endpoint to return the balance summary card HTML snippet."""
    today = timezone.localtime().date()
    start_of_month = today.replace(day=1)
    if today.month == 12:
        end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
    stats = get_monthly_stats(start_of_month, end_of_month)
    
    html = f"""
    <div class="card summary-card" id="balance-summary-card">
        <h2>Outstanding Balance</h2>
        <div class="summary-balance">₹{stats['outstanding']:.2f}</div>
        <div class="summary-details">
            <span>Accrued: ₹{stats['total_accrued']:.2f}</span>
            <span>Paid: ₹{stats['total_paid']:.2f}</span>
        </div>
    </div>
    """
    return HttpResponse(html)

@login_required
def toggle_meal(request):
    """HTMX endpoint to toggle a meal status."""
    if request.method != 'POST':
        return HttpResponse('Invalid Request', status=400)

    date_str = request.POST.get('date')
    meal_name = request.POST.get('meal_name')
    target_status = request.POST.get('status') # 'Consumed' or 'Skipped'

    try:
        log_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return HttpResponse('Invalid Date', status=400)

    # Get rate
    rate_obj = MealRate.objects.filter(meal_name=meal_name).first()
    rate_value = rate_obj.rate if rate_obj else 0

    # Get or create log
    log, created = MealLog.objects.get_or_create(
        date=log_date,
        meal_name=meal_name,
        defaults={'cost_charged': rate_value, 'status': target_status}
    )

    if not created:
        log.status = target_status
        # Update cost to active rate if they toggle it
        log.cost_charged = rate_value
        log.save()

    # Create HTML snippet for the updated toggle button
    is_consumed = log.status == 'Consumed'
    is_skipped = log.status == 'Skipped'

    html = f"""
    <div class="toggle-group" id="toggle-{meal_name}">
        <button type="button" 
                class="toggle-btn {'consumed' if is_consumed else 'neutral'}"
                hx-post="/toggle-meal/" 
                hx-vals='{{"date": "{date_str}", "meal_name": "{meal_name}", "status": "Consumed"}}'
                hx-target="#toggle-{meal_name}"
                hx-swap="outerHTML">
            Yes
        </button>
        <button type="button" 
                class="toggle-btn {'skipped' if is_skipped else 'neutral'}"
                hx-post="/toggle-meal/" 
                hx-vals='{{"date": "{date_str}", "meal_name": "{meal_name}", "status": "Skipped"}}'
                hx-target="#toggle-{meal_name}"
                hx-swap="outerHTML">
            No
        </button>
    </div>
    """
    response = HttpResponse(html)
    # Trigger reload of balance summary
    response['HX-Trigger'] = 'update-balance'
    return response

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        date_val = request.POST.get('date', timezone.localtime().date())

        if form_type == 'extra':
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            if description and amount:
                ExtraCharge.objects.create(
                    date=date_val,
                    description=description,
                    amount=amount
                )
        elif form_type == 'payment':
            amount = request.POST.get('amount')
            method = request.POST.get('method')
            if amount:
                PaymentLog.objects.create(
                    date=date_val,
                    amount=amount,
                    method=method
                )
        return redirect('dashboard')

    context = {
        'today': timezone.localtime().date().strftime('%Y-%m-%d')
    }
    return render(request, 'tracker/add_transaction.html', context)

@login_required
def settings_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_rates':
            # Loop through post data to update existing rates
            for key, val in request.POST.items():
                if key.startswith('rate_'):
                    rate_id = key.split('_')[1]
                    rate_obj = get_object_or_404(MealRate, id=rate_id)
                    rate_obj.rate = val
                    rate_obj.save()
        elif action == 'add_meal':
            name = request.POST.get('new_meal_name')
            rate = request.POST.get('new_meal_rate')
            if name and rate:
                MealRate.objects.create(meal_name=name.strip(), rate=rate)
        elif action == 'delete_meal':
            rate_id = request.POST.get('rate_id')
            if rate_id:
                MealRate.objects.filter(id=rate_id).delete()
        return redirect('settings')

    rates = MealRate.objects.all()
    return render(request, 'tracker/settings.html', {'rates': rates})

@login_required
def history_view(request):
    # Determine selected month and year
    today = timezone.localtime().date()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    start_date = date(selected_year, selected_month, 1)
    if selected_month == 12:
        end_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)

    # Get data
    meals = MealLog.objects.filter(date__range=(start_date, end_date)).order_by('date')
    extras = ExtraCharge.objects.filter(date__range=(start_date, end_date)).order_by('date')
    payments = PaymentLog.objects.filter(date__range=(start_date, end_date)).order_by('date')

    stats = get_monthly_stats(start_date, end_date)

    # Generate a copy-paste friendly text report
    month_name = start_date.strftime('%B %Y')
    summary_text = f"PG Food Bill Summary - {month_name}\n"
    summary_text += "=" * 32 + "\n"
    summary_text += f"Total Meals Cost:   ₹{stats['meal_cost']:.2f}\n"
    summary_text += f"Total Extra Cost:   ₹{stats['extra_cost']:.2f}\n"
    summary_text += f"Total Payments:     ₹{stats['total_paid']:.2f}\n"
    summary_text += "-" * 32 + "\n"
    summary_text += f"Outstanding Balance: ₹{stats['outstanding']:.2f}\n"
    summary_text += "=" * 32 + "\n"
    
    if meals.filter(status='Consumed').exists():
        summary_text += "\nConsumed Meals Breakdown:\n"
        # Summarize count per meal name
        meal_counts = {}
        for m in meals.filter(status='Consumed'):
            meal_counts[m.meal_name] = meal_counts.get(m.meal_name, 0) + 1
        for name, count in meal_counts.items():
            rate_item = MealRate.objects.filter(meal_name=name).first()
            rate_val = rate_item.rate if rate_item else 0
            summary_text += f"- {name}: {count} days @ ₹{rate_val:.2f} = ₹{count*rate_val:.2f}\n"
            
    if extras.exists():
        summary_text += "\nExtra Charges:\n"
        for ex in extras:
            summary_text += f"- {ex.date.strftime('%d %b')}: {ex.description} (₹{ex.amount:.2f})\n"

    # Year choices (past 2 years, current, and next year)
    years = range(today.year - 2, today.year + 2)
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    context = {
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': month_name,
        'meals': meals,
        'extras': extras,
        'payments': payments,
        'stats': stats,
        'summary_text': summary_text,
        'years': years,
        'months': months
    }
    return render(request, 'tracker/history.html', context)
