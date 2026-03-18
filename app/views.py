from django.shortcuts import render
from django.shortcuts import render
from .models import Vehicle, Trip, TrafficEvent, Alert

def home(request):
    vehicles = Vehicle.objects.all()
    context = {
        'total_vehicles': vehicles.count(),
        'active_trips': Trip.objects.filter(status='ongoing').count(),
        'traffic_events': TrafficEvent.objects.filter(severity='high').count(),
        'alerts': Alert.objects.filter(is_active=True).count(),
        'vehicles': vehicles,
        'recent_alerts': Alert.objects.order_by('-created_at')[:5],
    }
    return render(request, 'index.html', context)