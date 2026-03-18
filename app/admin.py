# admin.py
from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ExportMixin
from import_export.formats.base_formats import CSV, XLSX
from .models import (
    Vehicle, Driver, Trip, LocationLog,
    Node, Edge, Route,
    TrafficEvent, TrafficCondition,
    Alert, PerformanceMetric, SiteVisitLog
)

# ===============================
# 1. Vehicle Admin with Status Colors + Export
# ===============================
@admin.register(Vehicle)
class VehicleAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('registration_number', 'driver_name', 'status_colored', 'current_latitude', 'current_longitude', 'speed', 'last_updated')
    list_filter = ('status',)
    search_fields = ('registration_number', 'driver_name')
    ordering = ('registration_number',)
    formats = [CSV, XLSX]

    def status_colored(self, obj):
        color = {'active': 'green', 'idle': 'orange', 'offline': 'red'}.get(obj.status, 'black')
        return format_html('<b><span style="color: {};">{}</span></b>', color, obj.status)
    status_colored.short_description = 'Status'

# ===============================
# 2. Driver Admin + Export
# ===============================
@admin.register(Driver)
class DriverAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('name', 'phone', 'vehicle')
    search_fields = ('name', 'phone', 'vehicle__registration_number')
    formats = [CSV, XLSX]

# ===============================
# 3. Trip Admin with Status Colors + Export
# ===============================
@admin.register(Trip)
class TripAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('vehicle', 'start_location', 'destination', 'status_colored', 'start_time', 'end_time', 'route')
    list_filter = ('status', 'start_time')
    search_fields = ('vehicle__registration_number', 'start_location', 'destination')
    ordering = ('-start_time',)
    formats = [CSV, XLSX]

    def status_colored(self, obj):
        color = {'ongoing': 'blue', 'completed': 'green', 'cancelled': 'red'}.get(obj.status, 'black')
        return format_html('<b><span style="color:{};">{}</span></b>', color, obj.status)
    status_colored.short_description = 'Status'

# ===============================
# 4. LocationLog Admin + Export
# ===============================
@admin.register(LocationLog)
class LocationLogAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('vehicle', 'latitude', 'longitude', 'speed', 'timestamp')
    list_filter = ('vehicle', 'timestamp')
    search_fields = ('vehicle__registration_number',)
    formats = [CSV, XLSX]

# ===============================
# 5. Node Admin + Export
# ===============================
@admin.register(Node)
class NodeAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)
    formats = [CSV, XLSX]

# ===============================
# 6. Edge Admin with Travel Time Color + Export
# ===============================
@admin.register(Edge)
class EdgeAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('start_node', 'end_node', 'distance', 'base_travel_time', 'congestion_level_colored', 'current_travel_time_display')
    search_fields = ('start_node__name', 'end_node__name')
    formats = [CSV, XLSX]

    def congestion_level_colored(self, obj):
        color = 'green' if obj.congestion_level <= 1 else 'orange' if obj.congestion_level <= 2 else 'red'
        return format_html('<b><span style="color:{};">{:.1f}</span></b>', color, obj.congestion_level)
    congestion_level_colored.short_description = 'Congestion Level'

    def current_travel_time_display(self, obj):
        return f"{obj.current_travel_time():.1f} min"
    current_travel_time_display.short_description = 'Current Travel Time'

# ===============================
# 7. Route Admin + Export
# ===============================
@admin.register(Route)
class RouteAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('start_node', 'end_node', 'total_distance', 'estimated_time', 'created_at')
    search_fields = ('start_node__name', 'end_node__name')
    list_filter = ('created_at',)
    formats = [CSV, XLSX]

# ===============================
# 8. TrafficEvent Admin with Severity Colors + Export
# ===============================
@admin.register(TrafficEvent)
class TrafficEventAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('severity_colored', 'latitude', 'longitude', 'description', 'timestamp')
    list_filter = ('severity', 'timestamp')
    search_fields = ('description',)
    formats = [CSV, XLSX]

    def severity_colored(self, obj):
        color = {'low': 'green', 'medium': 'orange', 'high': 'red'}.get(obj.severity, 'black')
        return format_html('<b><span style="color:{};">{}</span></b>', color, obj.severity)
    severity_colored.short_description = 'Severity'

# ===============================
# 9. TrafficCondition Admin + Export
# ===============================
@admin.register(TrafficCondition)
class TrafficConditionAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('edge', 'average_speed', 'congestion_level_colored', 'updated_at')
    list_filter = ('updated_at',)
    formats = [CSV, XLSX]

    def congestion_level_colored(self, obj):
        color = 'green' if obj.congestion_level <= 1 else 'orange' if obj.congestion_level <= 2 else 'red'
        return format_html('<b><span style="color:{};">{:.1f}</span></b>', color, obj.congestion_level)
    congestion_level_colored.short_description = 'Congestion Level'

# ===============================
# 10. Alert Admin with Type Colors + Export
# ===============================
@admin.register(Alert)
class AlertAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('alert_type_colored', 'message', 'is_active', 'created_at')
    list_filter = ('alert_type', 'is_active')
    search_fields = ('message',)
    formats = [CSV, XLSX]

    def alert_type_colored(self, obj):
        color = {'traffic': 'orange', 'vehicle': 'blue', 'system': 'red'}.get(obj.alert_type, 'black')
        return format_html('<b><span style="color:{};">{}</span></b>', color, obj.alert_type)
    alert_type_colored.short_description = 'Type'

# ===============================
# 11. PerformanceMetric Admin + Export
# ===============================
@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('date', 'avg_travel_time', 'avg_response_time', 'avg_route_efficiency', 'fleet_utilization', 'idle_time')
    list_filter = ('date',)
    formats = [CSV, XLSX]

# ===============================
# 12. SiteVisitLog Admin + Export
# ===============================
@admin.register(SiteVisitLog)
class SiteVisitLogAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('user_display', 'path', 'method', 'ip_address', 'timestamp')
    list_filter = ('method', 'timestamp')
    search_fields = ('user__username', 'path', 'ip_address')
    formats = [CSV, XLSX]

    def user_display(self, obj):
        return obj.user.username if obj.user else 'Anonymous'
    user_display.short_description = 'User'