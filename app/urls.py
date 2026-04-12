from django.urls import path
from . import views

urlpatterns = [

    # ── AUTH ──
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),

    # ── MAIN DASHBOARD ──
    path('',         views.home,         name='home'),

    # ── FLEET ──
    path('fleet/',                        views.fleet_list,   name='fleet_list'),
    path('fleet/add/',                    views.fleet_add,    name='fleet_add'),
    path('fleet/edit/<int:vehicle_id>/',  views.fleet_edit,   name='fleet_edit'),
    path('fleet/delete/<int:vehicle_id>/',views.fleet_delete, name='fleet_delete'),

    # ── TRIPS ──
    path('trips/',                          views.trip_list,     name='trip_list'),
    path('trips/create/',                   views.trip_create,   name='trip_create'),
    path('trips/complete/<int:trip_id>/',   views.trip_complete, name='trip_complete'),
    path('trips/cancel/<int:trip_id>/',     views.trip_cancel,   name='trip_cancel'),

    # ── TRAFFIC ──
    path('traffic/',                         views.traffic_list,   name='traffic_list'),
    path('traffic/create/',                  views.traffic_create, name='traffic_create'),
    path('traffic/delete/<int:event_id>/',   views.traffic_delete, name='traffic_delete'),

    # ── ALERTS ──
    path('alerts/',                         views.alert_list,    name='alert_list'),
    path('alerts/create/',                  views.alert_create,  name='alert_create'),
    path('alerts/resolve/<int:alert_id>/',  views.alert_resolve, name='alert_resolve'),

    # ── METRICS ──
    path('metrics/',         views.metrics_view,   name='metrics_view'),
    path('metrics/create/',  views.metrics_create, name='metrics_create'),

    # ── ADMIN DASHBOARD ──
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # ── SITE LOGS ──
    path('logs/', views.site_logs, name='site_logs'),

    # ── API / AJAX ──
    path('api/vehicles/', views.api_vehicles, name='api_vehicles'),
    path('api/alerts/',   views.api_alerts,   name='api_alerts'),
]