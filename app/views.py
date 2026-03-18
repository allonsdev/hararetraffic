from django.shortcuts import render
from django.db.models import Avg, Count
from .models import (
    Vehicle, Trip, TrafficEvent, Alert,
    PerformanceMetric, LocationLog
)

from django.db.models import Avg
from .models import PerformanceMetric, LocationLog, TrafficEvent, Trip

def home(request):
    vehicles = Vehicle.objects.all()

    trip_events = []
    for trip in Trip.objects.all():
        trip_events.append({
            "title": f"{trip.vehicle.registration_number}",
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

        # NEW ANALYTICS
        'avg_speed': LocationLog.objects.aggregate(avg=Avg('speed'))['avg'] or 0,
        'metrics': PerformanceMetric.objects.order_by('-date').first(),
        'trip_events': trip_events,
        'all_traffic': TrafficEvent.objects.all(),
    }

    return render(request, 'index.html', context)