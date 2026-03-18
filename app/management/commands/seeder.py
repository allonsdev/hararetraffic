# management/commands/seed_data.py
from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import datetime, timedelta
from app.models import (
    Vehicle, Driver, Trip, LocationLog,
    Node, Edge, Route, TrafficEvent, TrafficCondition,
    Alert, PerformanceMetric
)

fake = Faker()

# Harare GPS boundaries
LAT_MIN = -17.9000
LAT_MAX = -17.7000
LNG_MIN = 30.9000
LNG_MAX = 31.1000

def random_lat():
    return round(random.uniform(LAT_MIN, LAT_MAX), 6)

def random_lng():
    return round(random.uniform(LNG_MIN, LNG_MAX), 6)

class Command(BaseCommand):
    help = "Seed 100+ records for smart transport system (Harare)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # -------------------------
        # 1. Vehicles & Drivers
        # -------------------------
        vehicles = []
        for _ in range(20):
            vehicle_status = random.choice(['active', 'idle', 'offline'])
            vehicle = Vehicle.objects.create(
                registration_number=f"ZIM-{fake.unique.bothify('???-####')}",
                driver_name=fake.name(),
                status=vehicle_status,
                current_latitude=random_lat(),
                current_longitude=random_lng(),
                speed=round(random.uniform(0, 60), 2),
                last_updated=datetime.now()
            )
            vehicles.append(vehicle)

        # -------------------------
        # 2. Trips
        # -------------------------
        for _ in range(30):
            vehicle = random.choice(vehicles)
            start_time = datetime.now() - timedelta(hours=random.randint(0, 5))
            end_time = start_time + timedelta(minutes=random.randint(15, 120))
            Trip.objects.create(
                vehicle=vehicle,
                start_location=fake.street_name(),
                destination=fake.street_name(),
                start_lat=random_lat(),
                start_lng=random_lng(),
                dest_lat=random_lat(),
                dest_lng=random_lng(),
                start_time=start_time,
                end_time=end_time,
                status=random.choice(['ongoing', 'completed', 'cancelled']),
                route=None
            )

        # -------------------------
        # 3. Location Logs
        # -------------------------
        for vehicle in vehicles:
            for _ in range(5):
                LocationLog.objects.create(
                    vehicle=vehicle,
                    latitude=random_lat(),
                    longitude=random_lng(),
                    speed=round(random.uniform(0, 60), 2),
                    timestamp=datetime.now() - timedelta(minutes=random.randint(0, 300))
                )

        # -------------------------
        # 4. Nodes & Edges
        # -------------------------
        nodes = [Node.objects.create(
            name=fake.street_name(),
            latitude=random_lat(),
            longitude=random_lng()
        ) for _ in range(20)]

        edges = []
        for _ in range(30):
            start, end = random.sample(nodes, 2)
            edges.append(Edge.objects.create(
                start_node=start,
                end_node=end,
                distance=round(random.uniform(1, 15), 2),
                base_travel_time=round(random.uniform(5, 30), 2),
                congestion_level=round(random.uniform(1, 3), 2)
            ))

        # -------------------------
        # 5. Routes
        # -------------------------
        for _ in range(20):
            start, end = random.sample(nodes, 2)
            Route.objects.create(
                start_node=start,
                end_node=end,
                total_distance=round(random.uniform(2, 25), 2),
                estimated_time=round(random.uniform(10, 60), 2),
                created_at=datetime.now()
            )

        # -------------------------
        # 6. Traffic Events
        # -------------------------
        for _ in range(15):
            TrafficEvent.objects.create(
                latitude=random_lat(),
                longitude=random_lng(),
                severity=random.choice(['low', 'medium', 'high']),
                description=fake.sentence(),
                timestamp=datetime.now() - timedelta(minutes=random.randint(0, 120))
            )

        # -------------------------
        # 7. Traffic Conditions
        # -------------------------
        for edge in edges:
            TrafficCondition.objects.create(
                edge=edge,
                average_speed=round(random.uniform(20, 60), 2),
                congestion_level=round(random.uniform(1, 3), 2),
                updated_at=datetime.now()
            )

        # -------------------------
        # 8. Alerts
        # -------------------------
        for _ in range(10):
            Alert.objects.create(
                message=fake.sentence(),
                alert_type=random.choice(['traffic', 'vehicle', 'system']),
                is_active=random.choice([True, False]),
                created_at=datetime.now() - timedelta(minutes=random.randint(0, 240))
            )

        # -------------------------
        # 9. Performance Metrics
        # -------------------------
        for _ in range(10):
            PerformanceMetric.objects.create(
                date=datetime.now().date() - timedelta(days=random.randint(0, 30)),
                avg_travel_time=round(random.uniform(15, 60), 2),
                avg_response_time=round(random.uniform(5, 20), 2),
                avg_route_efficiency=round(random.uniform(70, 100), 2),
                fleet_utilization=round(random.uniform(50, 100), 2),
                idle_time=round(random.uniform(5, 60), 2)
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded 100+ realistic records for Harare City Council'))