from django.urls import path, include
from . import views

urlpatterns = [

    # ── PUBLIC ──
    path('landing/', views.landing, name='landing'),

    # ── AUTH ──
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ── MAIN DASHBOARD ──
    path('', views.home, name='home'),

    # ── LIVE MAP ──
    path('map/', views.map_view, name='map_view'),

    # ── ANALYTICS ──
    path('analytics/', views.analytics_view, name='analytics_view'),

    # ── FLEET ──
    path('fleet/',                         views.fleet_list,   name='fleet_list'),
    path('fleet/add/',                     views.fleet_add,    name='fleet_add'),
    path('fleet/edit/<int:vehicle_id>/',   views.fleet_edit,   name='fleet_edit'),
    path('fleet/delete/<int:vehicle_id>/', views.fleet_delete, name='fleet_delete'),

    # ── TRIPS ──
    path('trips/',                           views.trip_list,     name='trip_list'),
    path('trips/create/',                    views.trip_create,   name='trip_create'),
    path('trips/complete/<int:trip_id>/',    views.trip_complete, name='trip_complete'),
    path('trips/cancel/<int:trip_id>/',      views.trip_cancel,   name='trip_cancel'),

    # ── TRAFFIC ──
    path('traffic/',                          views.traffic_list,   name='traffic_list'),
    path('traffic/create/',                   views.traffic_create, name='traffic_create'),
    path('traffic/delete/<int:event_id>/',    views.traffic_delete, name='traffic_delete'),

    # ── ALERTS ──
    path('alerts/',                          views.alert_list,    name='alert_list'),
    path('alerts/create/',                   views.alert_create,  name='alert_create'),
    path('alerts/resolve/<int:alert_id>/',   views.alert_resolve, name='alert_resolve'),

    # ── METRICS ──
    path('metrics/',        views.metrics_view,   name='metrics_view'),
    path('metrics/create/', views.metrics_create, name='metrics_create'),

    # ── ADMIN ──
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # ── LOGS ──
    path('logs/', views.site_logs, name='site_logs'),

    # ── JSON API ──
    path('api/vehicles/',            views.api_vehicles,           name='api_vehicles'),
    path('api/alerts/',              views.api_alerts,             name='api_alerts'),
    path('api/traffic/',             views.api_traffic,            name='api_traffic'),
    path('api/metrics/historical/',  views.api_metrics_historical, name='api_metrics_historical'),
]