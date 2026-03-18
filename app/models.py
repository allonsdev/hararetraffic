from django.db import models

# Create your models here.
# models.py
# Django models for Real-Time Smart Transportation System
# Author: Allons Tafadzwa Mazani
# Purpose: Fleet tracking, traffic simulation, route optimization, real-time updates, and system evaluation

from django.db import models
from django.utils import timezone

# ===============================
# 1. Fleet & Tracking Models
# ===============================
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SiteVisitLog(models.Model):
    """
    Captures every page visit on the site.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(max_length=500)           # URL path visited
    full_path = models.CharField(max_length=500)      # Full URL with query string
    method = models.CharField(max_length=10)          # GET, POST, etc.
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)         # Browser / device info
    referrer = models.CharField(max_length=500, blank=True)  # Previous page
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user or 'Anonymous'} visited {self.path} at {self.timestamp}"

class Vehicle(models.Model):
    """
    Represents a municipal fleet vehicle.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('idle', 'Idle'),
        ('offline', 'Offline'),
    ]

    registration_number = models.CharField(max_length=50, unique=True)
    driver_name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='idle')

    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    speed = models.FloatField(default=0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['registration_number']
        verbose_name_plural = "Vehicles"

    def __str__(self):
        return f"{self.registration_number} ({self.status})"


class Driver(models.Model):
    """
    Represents a vehicle driver.
    """
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Trip(models.Model):
    """
    Represents a trip made by a vehicle from a start location to a destination.
    """
    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')

    start_location = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)

    start_lat = models.FloatField()
    start_lng = models.FloatField()
    dest_lat = models.FloatField()
    dest_lng = models.FloatField()

    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')

    route = models.ForeignKey('Route', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['vehicle', 'status']),
        ]

    def __str__(self):
        return f"{self.vehicle} - {self.start_location} to {self.destination}"


class LocationLog(models.Model):
    """
    Stores GPS location updates for vehicles (used for real-time tracking).
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='location_logs')

    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(default=0)

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vehicle', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.vehicle} @ {self.timestamp}"


# ===============================
# 2. Route Optimization Models
# ===============================

class Node(models.Model):
    """
    Represents an intersection or point in the road network.
    """
    name = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name or f"Node {self.id}"


class Edge(models.Model):
    """
    Represents a road segment connecting two nodes.
    Travel time can be dynamically updated based on traffic conditions.
    """
    start_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='edges_from')
    end_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='edges_to')

    distance = models.FloatField(help_text="Distance in kilometers")
    base_travel_time = models.FloatField(help_text="Base travel time in minutes")

    congestion_level = models.FloatField(default=1.0, help_text="Multiplier for congestion (1 = normal)")

    class Meta:
        verbose_name_plural = "Edges"
        indexes = [
            models.Index(fields=['start_node', 'end_node']),
        ]

    def current_travel_time(self):
        return self.base_travel_time * self.congestion_level

    def __str__(self):
        return f"{self.start_node} -> {self.end_node}"


class Route(models.Model):
    """
    Stores precomputed routes between nodes for trip optimization.
    """
    start_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='route_starts')
    end_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='route_ends')

    total_distance = models.FloatField()
    estimated_time = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Routes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Route {self.start_node} → {self.end_node}"


# ===============================
# 3. Traffic Models
# ===============================

class TrafficEvent(models.Model):
    """
    Represents traffic events such as accidents, roadworks, or congestion spots.
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    latitude = models.FloatField()
    longitude = models.FloatField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    description = models.TextField(blank=True)

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.severity} traffic at {self.latitude},{self.longitude}"


class TrafficCondition(models.Model):
    """
    Dynamic traffic condition per road segment.
    """
    edge = models.OneToOneField(Edge, on_delete=models.CASCADE, related_name='traffic_condition')

    average_speed = models.FloatField()
    congestion_level = models.FloatField(default=1.0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Traffic on {self.edge}"


# ===============================
# 4. Real-Time Alerts
# ===============================

class Alert(models.Model):
    """
    Alerts sent to the dashboard or system operators.
    """
    ALERT_TYPES = [
        ('traffic', 'Traffic'),
        ('vehicle', 'Vehicle'),
        ('system', 'System'),
    ]

    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message[:50]


# ===============================
# 5. System Evaluation Models
# ===============================

class PerformanceMetric(models.Model):
    """
    Stores metrics to evaluate system efficiency, e.g., travel time, response time, and fleet utilization.
    """
    date = models.DateField()

    avg_travel_time = models.FloatField(help_text="Average travel time in minutes")
    avg_response_time = models.FloatField(help_text="Average reroute/response time in minutes")
    avg_route_efficiency = models.FloatField(help_text="Route efficiency score (0-100)")

    fleet_utilization = models.FloatField(help_text="Percentage of fleet in active trips")
    idle_time = models.FloatField(help_text="Average idle time per vehicle in minutes")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Metrics for {self.date}"