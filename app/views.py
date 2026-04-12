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


# ──────────────────────────────────────────────
# AUTH VIEWS
# ──────────────────────────────────────────────

def login_view(request):
    """
    Split-screen login: left = particles, right = form.
    """
    if request.user.is_authenticated:
        return redirect('home')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.POST.get('next') or 'home')
        error = "Invalid username or password."

    context = {
        'error': error,
        'next': request.GET.get('next', ''),
        'total_vehicles': Vehicle.objects.count(),
        'active_trips': Trip.objects.filter(status='ongoing').count(),
    }
    return render(request, 'login.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')


# ──────────────────────────────────────────────
# HOME DASHBOARD
# ──────────────────────────────────────────────

@login_required
def home(request):
    vehicles = Vehicle.objects.all()

    trip_events = []
    for trip in Trip.objects.select_related('vehicle').all():
        trip_events.append({
            "title": trip.vehicle.registration_number,
            "start": trip.start_time.isoformat(),
            "end": trip.end_time.isoformat() if trip.end_time else None,
        })

    context = {
        'total_vehicles': vehicles.count(),
        'active_trips': Trip.objects.filter(status='ongoing').count(),
        'traffic_events': TrafficEvent.objects.filter(severity='high').count(),
        'alerts': Alert.objects.filter(is_active=True).count(),

        'vehicles': vehicles,
        'recent_alerts': Alert.objects.order_by('-created_at')[:5],

        'avg_speed': LocationLog.objects.aggregate(avg=Avg('speed'))['avg'] or 0,
        'metrics': PerformanceMetric.objects.order_by('-date').first(),
        'trip_events': trip_events,
        'all_traffic': TrafficEvent.objects.all().order_by('-timestamp')[:10],
    }
    return render(request, 'index.html', context)


# ──────────────────────────────────────────────
# FLEET MANAGEMENT
# ──────────────────────────────────────────────

@login_required
def fleet_list(request):
    vehicles = Vehicle.objects.all().order_by('registration_number')
    context = {
        'vehicles': vehicles,
        'active_count': vehicles.filter(status='active').count(),
        'idle_count': vehicles.filter(status='idle').count(),
        'offline_count': vehicles.filter(status='offline').count(),
        'alerts': Alert.objects.filter(is_active=True).count(),
    }
    return render(request, 'fleet.html', context)


@login_required
def fleet_add(request):
    if request.method == 'POST':
        reg = request.POST.get('registration_number', '').strip()
        driver = request.POST.get('driver_name', '').strip()
        status = request.POST.get('status', 'idle')
        speed = float(request.POST.get('speed') or 0)
        lat = request.POST.get('current_latitude') or None
        lng = request.POST.get('current_longitude') or None

        if reg and driver:
            Vehicle.objects.create(
                registration_number=reg,
                driver_name=driver,
                status=status,
                speed=speed,
                current_latitude=float(lat) if lat else None,
                current_longitude=float(lng) if lng else None,
            )
            messages.success(request, f"Vehicle {reg} added successfully.")
        else:
            messages.error(request, "Registration number and driver name are required.")

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
        messages.success(request, f"Vehicle {vehicle.registration_number} updated.")
    return redirect('fleet_list')


@login_required
def fleet_delete(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    if request.method == 'POST':
        reg = vehicle.registration_number
        vehicle.delete()
        messages.success(request, f"Vehicle {reg} deleted.")
    return redirect('fleet_list')


# ──────────────────────────────────────────────
# TRIPS
# ──────────────────────────────────────────────

@login_required
def trip_list(request):
    trips = Trip.objects.select_related('vehicle', 'route').order_by('-start_time')
    context = {
        'trips': trips,
        'vehicles': Vehicle.objects.filter(status__in=['active', 'idle']),
        'alerts': Alert.objects.filter(is_active=True).count(),
        'ongoing_count': trips.filter(status='ongoing').count(),
        'completed_count': trips.filter(status='completed').count(),
        'cancelled_count': trips.filter(status='cancelled').count(),
    }
    return render(request, 'trips.html', context)


@login_required
def trip_create(request):
    if request.method == 'POST':
        try:
            vehicle_id = request.POST.get('vehicle')
            vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
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
            messages.success(request, "Trip created successfully.")
        except Exception as e:
            messages.error(request, f"Error creating trip: {e}")
    return redirect('trip_list')


@login_required
def trip_complete(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    trip.status = 'completed'
    trip.end_time = timezone.now()
    trip.save()
    messages.success(request, "Trip marked as completed.")
    return redirect('trip_list')


@login_required
def trip_cancel(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    trip.status = 'cancelled'
    trip.end_time = timezone.now()
    trip.save()
    messages.success(request, "Trip cancelled.")
    return redirect('trip_list')


# ──────────────────────────────────────────────
# TRAFFIC EVENTS
# ──────────────────────────────────────────────

@login_required
def traffic_list(request):
    events = TrafficEvent.objects.order_by('-timestamp')
    context = {
        'events': events,
        'high_count': events.filter(severity='high').count(),
        'medium_count': events.filter(severity='medium').count(),
        'low_count': events.filter(severity='low').count(),
        'alerts': Alert.objects.filter(is_active=True).count(),
    }
    return render(request, 'traffic.html', context)


@login_required
def traffic_create(request):
    if request.method == 'POST':
        TrafficEvent.objects.create(
            latitude=float(request.POST.get('latitude') or 0),
            longitude=float(request.POST.get('longitude') or 0),
            severity=request.POST.get('severity', 'low'),
            description=request.POST.get('description', '').strip(),
        )
        messages.success(request, "Traffic event logged.")
    return redirect('traffic_list')


@login_required
def traffic_delete(request, event_id):
    event = get_object_or_404(TrafficEvent, pk=event_id)
    if request.method == 'POST':
        event.delete()
        messages.success(request, "Traffic event removed.")
    return redirect('traffic_list')


# ──────────────────────────────────────────────
# ALERTS
# ──────────────────────────────────────────────

@login_required
def alert_list(request):
    context = {
        'all_alerts': Alert.objects.order_by('-created_at'),
        'alerts': Alert.objects.filter(is_active=True).count(),
    }
    return render(request, 'alerts.html', context)


@login_required
def alert_create(request):
    if request.method == 'POST':
        Alert.objects.create(
            message=request.POST.get('message', '').strip(),
            alert_type=request.POST.get('alert_type', 'system'),
            is_active=request.POST.get('is_active', 'true') == 'true',
        )
        messages.success(request, "Alert created.")
    return redirect('alert_list')


@login_required
def alert_resolve(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)
    alert.is_active = False
    alert.save()
    messages.success(request, "Alert resolved.")
    return redirect('alert_list')


# ──────────────────────────────────────────────
# PERFORMANCE METRICS
# ──────────────────────────────────────────────

@login_required
def metrics_view(request):
    all_metrics = PerformanceMetric.objects.order_by('-date')
    context = {
        'all_metrics': all_metrics,
        'latest': all_metrics.first(),
        'alerts': Alert.objects.filter(is_active=True).count(),
    }
    return render(request, 'metrics.html', context)


@login_required
def metrics_create(request):
    if request.method == 'POST':
        from datetime import date
        PerformanceMetric.objects.create(
            date=request.POST.get('date') or date.today(),
            avg_travel_time=float(request.POST.get('avg_travel_time') or 0),
            avg_response_time=float(request.POST.get('avg_response_time') or 0),
            avg_route_efficiency=float(request.POST.get('avg_route_efficiency') or 0),
            fleet_utilization=float(request.POST.get('fleet_utilization') or 0),
            idle_time=float(request.POST.get('idle_time') or 0),
        )
        messages.success(request, "Metrics recorded.")
    return redirect('metrics_view')


# ──────────────────────────────────────────────
# ADMIN DASHBOARD
# ──────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    vehicles = Vehicle.objects.all()
    events = TrafficEvent.objects.all()

    context = {
        'total_vehicles': vehicles.count(),
        'active_trips': Trip.objects.filter(status='ongoing').count(),
        'traffic_events': events.filter(severity='high').count(),
        'alerts': Alert.objects.filter(is_active=True).count(),
        'total_users': __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model().objects.count(),

        'active_count': vehicles.filter(status='active').count(),
        'idle_count': vehicles.filter(status='idle').count(),
        'offline_count': vehicles.filter(status='offline').count(),

        'traffic_high': events.filter(severity='high').count(),
        'traffic_medium': events.filter(severity='medium').count(),
        'traffic_low': events.filter(severity='low').count(),

        'recent_alerts': Alert.objects.order_by('-created_at')[:8],
        'recent_logs': SiteVisitLog.objects.order_by('-timestamp')[:10],
    }
    return render(request, 'admin_dashboard.html', context)


# ──────────────────────────────────────────────
# SITE VISIT LOGS
# ──────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def site_logs(request):
    logs = SiteVisitLog.objects.select_related('user').order_by('-timestamp')
    context = {
        'logs': logs[:200],
        'total_visits': logs.count(),
        'unique_paths': logs.values('path').distinct().count(),
        'alerts': Alert.objects.filter(is_active=True).count(),
    }
    return render(request, 'logs.html', context)


# ──────────────────────────────────────────────
# API ENDPOINTS (AJAX)
# ──────────────────────────────────────────────

@login_required
def api_vehicles(request):
    """Return all vehicle positions as JSON for live map updates."""
    data = []
    for v in Vehicle.objects.all():
        if v.current_latitude and v.current_longitude:
            data.append({
                'id': v.id,
                'reg': v.registration_number,
                'driver': v.driver_name,
                'status': v.status,
                'lat': v.current_latitude,
                'lng': v.current_longitude,
                'speed': v.speed,
                'updated': v.last_updated.isoformat(),
            })
    return JsonResponse({'vehicles': data})


@login_required
def api_alerts(request):
    """Return active alerts as JSON."""
    data = list(Alert.objects.filter(is_active=True).values(
        'id', 'message', 'alert_type', 'created_at'
    ))
    return JsonResponse({'alerts': data, 'count': len(data)})