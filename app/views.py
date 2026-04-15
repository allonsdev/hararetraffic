import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.http import JsonResponse

from .models import (
    Vehicle, Trip, TrafficEvent, Alert,
    PerformanceMetric, LocationLog, Route, Node, Edge, SiteVisitLog
)


# ────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────

def _alert_count():
    return Alert.objects.filter(is_active=True).count()


def _base_ctx():
    """Common context available to every view."""
    return {'alert_count': _alert_count()}


# ────────────────────────────────────────────
# LANDING PAGE (public)
# ────────────────────────────────────────────

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html', {
        'total_vehicles': Vehicle.objects.count(),
        'active_trips': Trip.objects.filter(status='ongoing').count(),
    })


# ────────────────────────────────────────────
# AUTH
# ────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username', '').strip(),
            password=request.POST.get('password', ''),
        )
        if user:
            login(request, user)
            return redirect(request.POST.get('next') or 'home')
        error = 'Invalid username or password.'
    return render(request, 'login.html', {
        'error': error,
        'next': request.GET.get('next', ''),
        'total_vehicles': Vehicle.objects.count(),
        'active_trips': Trip.objects.filter(status='ongoing').count(),
        'form': type('F', (), {'username': type('F', (), {'value': lambda s: '', 'errors': []})()})(),
    })


def logout_view(request):
    logout(request)
    return redirect('login')


# ────────────────────────────────────────────
# HOME DASHBOARD
# ────────────────────────────────────────────

@login_required
def home(request):
    vehicles = Vehicle.objects.all()
    ctx = _base_ctx()
    ctx.update({
        'total_vehicles': vehicles.count(),
        'active_trips': Trip.objects.filter(status='ongoing').count(),
        'traffic_events': TrafficEvent.objects.filter(severity='high').count(),
        'vehicles': vehicles,
        'recent_alerts': Alert.objects.order_by('-created_at')[:6],
        'avg_speed': LocationLog.objects.aggregate(avg=Avg('speed'))['avg'] or 0,
        'metrics': PerformanceMetric.objects.order_by('-date').first(),
        'all_traffic': TrafficEvent.objects.order_by('-timestamp')[:8],
    })
    return render(request, 'index.html', ctx)


# ────────────────────────────────────────────
# LIVE MAP
# ────────────────────────────────────────────

@login_required
def map_view(request):
    vehicles = Vehicle.objects.all()
    traffic_events = TrafficEvent.objects.order_by('-timestamp')
    
    # Get ongoing trips to show active routes on map
    ongoing_trips = Trip.objects.filter(
        status='ongoing',
        vehicle__current_latitude__isnull=False,
        vehicle__current_longitude__isnull=False
    ).select_related('vehicle')[:20]  # Limit to 20 for performance
    
    ctx = _base_ctx()
    ctx.update({
        'vehicles': vehicles,
        'traffic_events': traffic_events,
        'ongoing_trips': ongoing_trips,
        'total_vehicles': vehicles.count(),
        'active_count': vehicles.filter(status='active').count(),
        'traffic_count': traffic_events.count(),
    })
    return render(request, 'map.html', ctx)
 

# ────────────────────────────────────────────
# ANALYTICS
# ────────────────────────────────────────────

@login_required
def analytics_view(request):
    all_metrics = PerformanceMetric.objects.order_by('date')

    # Prepare JSON for charts
    metrics_json = json.dumps([{
        'date': str(m.date),
        'avg_travel_time': m.avg_travel_time,
        'avg_response_time': m.avg_response_time,
        'avg_route_efficiency': m.avg_route_efficiency,
        'fleet_utilization': m.fleet_utilization,
        'idle_time': m.idle_time,
        'completed_trips': 0,  # extend if Trip aggregation added
        'active_vehicles': 0,
        'idle_vehicles': 0,
        'offline_vehicles': 0,
        'high_severity_events': 0,
        'avg_congestion_level': 1.0,
        'total_delay_hours': 0,
    } for m in all_metrics])

    # KPI aggregates
    total_trips = Trip.objects.count()
    avg_efficiency = all_metrics.aggregate(avg=Avg('avg_route_efficiency'))['avg'] or 0
    total_delay = 0
    avg_active = 0

    ctx = _base_ctx()
    ctx.update({
        'all_metrics': all_metrics.order_by('-date'),
        'metrics_json': metrics_json,
        'total_trips': total_trips,
        'avg_active': avg_active,
        'avg_efficiency': avg_efficiency,
        'total_delay': total_delay,
    })
    return render(request, 'analytics.html', ctx)


# ────────────────────────────────────────────
# FLEET
# ────────────────────────────────────────────

@login_required
def fleet_list(request):
    vehicles = Vehicle.objects.all().order_by('registration_number')
    ctx = _base_ctx()
    ctx.update({
        'vehicles': vehicles,
        'active_count': vehicles.filter(status='active').count(),
        'idle_count': vehicles.filter(status='idle').count(),
        'offline_count': vehicles.filter(status='offline').count(),
    })
    return render(request, 'fleet.html', ctx)


@login_required
def fleet_add(request):
    if request.method == 'POST':
        reg = request.POST.get('registration_number', '').strip()
        driver = request.POST.get('driver_name', '').strip()
        if reg and driver:
            lat = request.POST.get('current_latitude') or None
            lng = request.POST.get('current_longitude') or None
            Vehicle.objects.create(
                registration_number=reg,
                driver_name=driver,
                status=request.POST.get('status', 'idle'),
                speed=float(request.POST.get('speed') or 0),
                current_latitude=float(lat) if lat else None,
                current_longitude=float(lng) if lng else None,
            )
            messages.success(request, f'Vehicle {reg} added.')
        else:
            messages.error(request, 'Registration number and driver name are required.')
    return redirect('fleet_list')


@login_required
def fleet_edit(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    if request.method == 'POST':
        vehicle.registration_number = request.POST.get('registration_number', vehicle.registration_number).strip()
        vehicle.driver_name = request.POST.get('driver_name', vehicle.driver_name).strip()
        vehicle.status = request.POST.get('status', vehicle.status)
        vehicle.speed = float(request.POST.get('speed') or vehicle.speed)
        lat = request.POST.get('current_latitude')
        lng = request.POST.get('current_longitude')
        if lat: vehicle.current_latitude = float(lat)
        if lng: vehicle.current_longitude = float(lng)
        vehicle.save()
        messages.success(request, f'Vehicle {vehicle.registration_number} updated.')
    return redirect('fleet_list')


@login_required
def fleet_delete(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    if request.method == 'POST':
        reg = vehicle.registration_number
        vehicle.delete()
        messages.success(request, f'Vehicle {reg} deleted.')
    return redirect('fleet_list')


# ────────────────────────────────────────────
# TRIPS
# ────────────────────────────────────────────

@login_required
def trip_list(request):
    trips = Trip.objects.select_related('vehicle', 'route').order_by('-start_time')
    ctx = _base_ctx()
    ctx.update({
        'trips': trips,
        'vehicles': Vehicle.objects.filter(status__in=['active', 'idle']),
        'ongoing_count': trips.filter(status='ongoing').count(),
        'completed_count': trips.filter(status='completed').count(),
        'cancelled_count': trips.filter(status='cancelled').count(),
    })
    return render(request, 'trips.html', ctx)


@login_required
def trip_create(request):
    if request.method == 'POST':
        try:
            vehicle = get_object_or_404(Vehicle, pk=request.POST.get('vehicle'))
            Trip.objects.create(
                vehicle=vehicle,
                start_location=request.POST.get('start_location', '').strip(),
                destination=request.POST.get('destination', '').strip(),
                start_lat=float(request.POST.get('start_lat') or 0),
                start_lng=float(request.POST.get('start_lng') or 0),
                dest_lat=float(request.POST.get('dest_lat') or 0),
                dest_lng=float(request.POST.get('dest_lng') or 0),
                status='ongoing',
            )
            messages.success(request, 'Trip created.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('trip_list')


@login_required
def trip_complete(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    trip.status = 'completed'
    trip.end_time = timezone.now()
    trip.save()
    messages.success(request, 'Trip completed.')
    return redirect('trip_list')


@login_required
def trip_cancel(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    trip.status = 'cancelled'
    trip.end_time = timezone.now()
    trip.save()
    messages.success(request, 'Trip cancelled.')
    return redirect('trip_list')


# ────────────────────────────────────────────
# TRAFFIC EVENTS
# ────────────────────────────────────────────

@login_required
def traffic_list(request):
    events = TrafficEvent.objects.order_by('-timestamp')
    ctx = _base_ctx()
    ctx.update({
        'events': events,
        'high_count': events.filter(severity='high').count(),
        'medium_count': events.filter(severity='medium').count(),
        'low_count': events.filter(severity='low').count(),
    })
    return render(request, 'traffic.html', ctx)


@login_required
def traffic_create(request):
    if request.method == 'POST':
        TrafficEvent.objects.create(
            latitude=float(request.POST.get('latitude') or 0),
            longitude=float(request.POST.get('longitude') or 0),
            severity=request.POST.get('severity', 'low'),
            description=request.POST.get('description', '').strip(),
        )
        messages.success(request, 'Traffic event logged.')
    return redirect('traffic_list')


@login_required
def traffic_delete(request, event_id):
    event = get_object_or_404(TrafficEvent, pk=event_id)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Traffic event removed.')
    return redirect('traffic_list')


# ────────────────────────────────────────────
# ALERTS
# ────────────────────────────────────────────

@login_required
def alert_list(request):
    ctx = _base_ctx()
    ctx['all_alerts'] = Alert.objects.order_by('-created_at')
    return render(request, 'alerts.html', ctx)


@login_required
def alert_create(request):
    if request.method == 'POST':
        Alert.objects.create(
            message=request.POST.get('message', '').strip(),
            alert_type=request.POST.get('alert_type', 'system'),
            is_active=request.POST.get('is_active', 'true') == 'true',
        )
        messages.success(request, 'Alert created.')
    return redirect('alert_list')


@login_required
def alert_resolve(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)
    alert.is_active = False
    alert.save()
    messages.success(request, 'Alert resolved.')
    return redirect('alert_list')


# ────────────────────────────────────────────
# PERFORMANCE METRICS
# ────────────────────────────────────────────

@login_required
def metrics_view(request):
    all_metrics = PerformanceMetric.objects.order_by('-date')
    ctx = _base_ctx()
    ctx.update({'all_metrics': all_metrics, 'latest': all_metrics.first()})
    return render(request, 'metrics.html', ctx)


@login_required
def metrics_create(request):
    if request.method == 'POST':
        PerformanceMetric.objects.create(
            date=request.POST.get('date') or date.today(),
            avg_travel_time=float(request.POST.get('avg_travel_time') or 0),
            avg_response_time=float(request.POST.get('avg_response_time') or 0),
            avg_route_efficiency=float(request.POST.get('avg_route_efficiency') or 0),
            fleet_utilization=float(request.POST.get('fleet_utilization') or 0),
            idle_time=float(request.POST.get('idle_time') or 0),
        )
        messages.success(request, 'Metrics recorded.')
    return redirect('metrics_view')


# ────────────────────────────────────────────
# ADMIN DASHBOARD
# ────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    vehicles = Vehicle.objects.all()
    events = TrafficEvent.objects.all()
    ctx = _base_ctx()
    ctx.update({
        'total_vehicles': vehicles.count(),
        'active_trips': Trip.objects.filter(status='ongoing').count(),
        'total_users': User.objects.count(),
        'alerts': _alert_count(),
        'active_count': vehicles.filter(status='active').count(),
        'idle_count': vehicles.filter(status='idle').count(),
        'offline_count': vehicles.filter(status='offline').count(),
        'traffic_high': events.filter(severity='high').count(),
        'traffic_medium': events.filter(severity='medium').count(),
        'traffic_low': events.filter(severity='low').count(),
        'recent_alerts': Alert.objects.order_by('-created_at')[:8],
        'recent_logs': SiteVisitLog.objects.order_by('-timestamp')[:10],
        # For progress bars in template
        'fleet_status_rows': [
            ('Active', vehicles.filter(status='active').count(), '#4ade80'),
            ('Idle', vehicles.filter(status='idle').count(), '#fbbf24'),
            ('Offline', vehicles.filter(status='offline').count(), '#f87171'),
        ],
    })
    return render(request, 'admin_dashboard.html', ctx)


# ────────────────────────────────────────────
# SITE LOGS
# ────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def site_logs(request):
    logs = SiteVisitLog.objects.select_related('user').order_by('-timestamp')
    ctx = _base_ctx()
    ctx.update({
        'logs': logs[:200],
        'total_visits': logs.count(),
        'unique_paths': logs.values('path').distinct().count(),
    })
    return render(request, 'logs.html', ctx)


# ────────────────────────────────────────────
# JSON API ENDPOINTS
# ────────────────────────────────────────────

@login_required
def api_vehicles(request):
    data = [
        {
            'id': v.id, 'reg': v.registration_number, 'driver': v.driver_name,
            'status': v.status, 'lat': v.current_latitude, 'lng': v.current_longitude,
            'speed': v.speed, 'updated': v.last_updated.isoformat(),
        }
        for v in Vehicle.objects.all()
        if v.current_latitude and v.current_longitude
    ]
    return JsonResponse({'vehicles': data, 'count': len(data)})


@login_required
def api_alerts(request):
    data = list(Alert.objects.filter(is_active=True).values('id', 'message', 'alert_type', 'created_at'))
    return JsonResponse({'alerts': data, 'count': len(data)})


@login_required
def api_traffic(request):
    data = [
        {
            'id': e.id, 'latitude': e.latitude, 'longitude': e.longitude,
            'severity': e.severity, 'description': e.description,
            'timestamp': e.timestamp.isoformat(),
        }
        for e in TrafficEvent.objects.order_by('-timestamp')
    ]
    return JsonResponse({'events': data, 'count': len(data)})


@login_required
def api_metrics_historical(request):
    days = int(request.GET.get('days', 30))
    start_date = date.today() - timedelta(days=days)
    metrics = PerformanceMetric.objects.filter(date__gte=start_date).order_by('date')
    data = [
        {
            'date': str(m.date),
            'avg_travel_time': m.avg_travel_time,
            'avg_response_time': m.avg_response_time,
            'avg_route_efficiency': m.avg_route_efficiency,
            'fleet_utilization': m.fleet_utilization,
            'idle_time': m.idle_time,
            'completed_trips': 0,
            'active_vehicles': 0,
            'idle_vehicles': 0,
            'offline_vehicles': 0,
            'high_severity_events': 0,
            'avg_congestion_level': 1.0,
            'total_delay_hours': 0.0,
            'fuel_consumed': 0.0,
        }
        for m in metrics
    ]
    return JsonResponse({'metrics': data, 'period_days': days})