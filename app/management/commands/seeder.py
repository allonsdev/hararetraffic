# management/commands/seed_data.py
from django.core.management.base import BaseCommand
import random
from datetime import datetime, timedelta
from app.models import (
    Vehicle, Driver, Trip, LocationLog,
    Node, Edge, Route, TrafficEvent, TrafficCondition,
    Alert, PerformanceMetric, SiteVisitLog
)
from django.contrib.auth import get_user_model

User = get_user_model()

# Real Harare locations with actual GPS coordinates
HARARE_LOCATIONS = [
    {"name": "Harare CBD", "lat": -17.8292, "lng": 31.0522},
    {"name": "Robert Mugabe Road", "lat": -17.8315, "lng": 31.0455},
    {"name": "Samora Machel Avenue", "lat": -17.8252, "lng": 31.0500},
    {"name": "Julius Nyerere Way", "lat": -17.8220, "lng": 31.0450},
    {"name": "Second Street", "lat": -17.8290, "lng": 31.0490},
    {"name": "Borrowdale", "lat": -17.7830, "lng": 31.0658},
    {"name": "Avondale", "lat": -17.7950, "lng": 31.0380},
    {"name": "Mount Pleasant", "lat": -17.7840, "lng": 31.0550},
    {"name": "Eastlea", "lat": -17.8380, "lng": 31.0780},
    {"name": "Belgravia", "lat": -17.8150, "lng": 31.0610},
    {"name": "Newlands", "lat": -17.8055, "lng": 31.0335},
    {"name": "Highlands", "lat": -17.8480, "lng": 31.0220},
    {"name": "Mbare", "lat": -17.8660, "lng": 31.0430},
    {"name": "Highfield", "lat": -17.8770, "lng": 31.0140},
    {"name": "Glen Norah", "lat": -17.8890, "lng": 30.9980},
    {"name": "Glen View", "lat": -17.9050, "lng": 30.9730},
    {"name": "Chitungwiza Road", "lat": -17.8950, "lng": 31.0650},
    {"name": "Airport Road", "lat": -17.9000, "lng": 31.0900},
    {"name": "Arcadia", "lat": -17.8180, "lng": 31.0280},
    {"name": "Westgate", "lat": -17.8410, "lng": 30.9850},
    {"name": "Warren Park", "lat": -17.8320, "lng": 30.9770},
    {"name": "Marlborough", "lat": -17.8680, "lng": 30.9620},
    {"name": "Hatfield", "lat": -17.8130, "lng": 31.0740},
    {"name": "Msasa", "lat": -17.8050, "lng": 31.0950},
    {"name": "Graniteside", "lat": -17.8700, "lng": 31.0850},
]

# Zimbabwean names (mix of Shona and Ndebele)
ZIMBA_FIRST_NAMES = [
    "Tendai", "Tafadzwa", "Takudzwa", "Tinashe", "Tapiwa", "Tarirai", "Tatenda",
    "Blessing", "Fadzai", "Rumbidzai", "Tariro", "Ruvimbo", "Farai", "Chipo",
    "Simba", "Nhamo", "Tsitsi", "Nyasha", "Kudzai", "Panashe", "Munashe",
    "Nkosana", "Siphiwe", "Sibusiso", "Nhlanhla", "Thabo", "Nomsa", "Themba",
    "Nokuthula", "Lindiwe", "Zanele", "Precious", "Memory", "Charity", "Faith"
]

ZIMBA_LAST_NAMES = [
    "Moyo", "Ncube", "Dube", "Sibanda", "Ndlovu", "Nkomo", "Mpofu",
    "Mutasa", "Chiweshe", "Mlambo", "Nyathi", "Zulu", "Banda", "Phiri",
    "Gumede", "Khumalo", "Muzenda", "Zvobgo", "Mapfumo", "Chiwenga",
    "Mnangagwa", "Mujuru", "Mugabe", "Chitepo", "Nkala", "Zhou"
]

def random_zimba_name():
    return f"{random.choice(ZIMBA_FIRST_NAMES)} {random.choice(ZIMBA_LAST_NAMES)}"

def random_location():
    return random.choice(HARARE_LOCATIONS)

# Real traffic events that happen in Harare
REAL_TRAFFIC_EVENTS = [
    "Roadworks on Samora Machel - one lane closed",
    "Accident near Copa Cabana - traffic diverted",
    "Kombi rank causing congestion at Fourth Street",
    "ZESA maintenance causing delays on Enterprise Road",
    "Traffic lights not working at Parkade intersection",
    "Heavy traffic at Robert Mugabe roundabout",
    "Police roadblock on Chiremba Road",
    "Broken down haulage truck blocking Seke Road",
    "Flooding near Mukuvisi River bridge",
    "Market day congestion in Mbare Musika area",
    "Funeral procession causing delays on Simon Mazorodze",
    "Construction work on Borrowdale Road - expect delays",
    "Pothole damage on Harare Drive - vehicles slow",
    "Vendors occupying road at Rotten Row",
    "Bus accident at Machipisa Shopping Centre",
]

REAL_SYSTEM_ALERTS = [
    "Fleet vehicle ZW-4523-HB requires urgent maintenance",
    "Multiple vehicles reporting low fuel in Highfield zone",
    "GPS signal lost for 3 vehicles - last seen Chitungwiza",
    "Traffic congestion alert: CBD area experiencing heavy delays",
    "Driver overtime alert: T. Moyo exceeding shift hours",
    "Vehicle ZW-8821-ZH speeding detected on Airport Road",
    "Route optimization needed: current ETA +25 minutes",
    "Emergency services access blocked at Parirenyatwa Hospital",
    "Vehicle breakdown reported: ZW-3345-MR near Westgate",
    "Fuel theft alert: unusual consumption pattern detected",
]

class Command(BaseCommand):
    help = "Seed 100+ realistic records for Harare City Council Smart Transport System"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding realistic Zimbabwean data for Harare...")

        # -------------------------
        # 1. Vehicles & Drivers
        # -------------------------
        vehicles = []
        vehicle_types = ['Refuse Truck', 'Water Tanker', 'Ambulance', 'Fire Engine', 'Bus', 'Patrol Vehicle']
        
        for i in range(25):
            location = random_location()
            vehicle_status = random.choice(['active', 'active', 'active', 'idle', 'offline'])  # more active
            
            # Realistic ZW registration format
            reg_number = f"ZW-{random.randint(1000,9999)}-{random.choice(['HB','ZH','MR','AA'])}"
            
            vehicle = Vehicle.objects.create(
                registration_number=reg_number,
                driver_name=random_zimba_name(),
                status=vehicle_status,
                current_latitude=location['lat'] + random.uniform(-0.003, 0.003),
                current_longitude=location['lng'] + random.uniform(-0.003, 0.003),
                speed=round(random.uniform(0, 55) if vehicle_status == 'active' else 0, 2),
                last_updated=datetime.now() - timedelta(seconds=random.randint(0, 300))
            )
            vehicles.append(vehicle)
            self.stdout.write(f"  ✓ Created vehicle: {reg_number} - {vehicle.driver_name}")

        # -------------------------
        # 2. Real Harare Nodes
        # -------------------------
        nodes = []
        for loc in HARARE_LOCATIONS:
            node = Node.objects.create(
                name=loc['name'],
                latitude=loc['lat'],
                longitude=loc['lng']
            )
            nodes.append(node)
        self.stdout.write(f"  ✓ Created {len(nodes)} real Harare location nodes")

        # -------------------------
        # 3. Edges (Connections between locations)
        # -------------------------
        edges = []
        connected_pairs = [
            ("Harare CBD", "Robert Mugabe Road"),
            ("Harare CBD", "Samora Machel Avenue"),
            ("Robert Mugabe Road", "Julius Nyerere Way"),
            ("Samora Machel Avenue", "Second Street"),
            ("Borrowdale", "Mount Pleasant"),
            ("Avondale", "Newlands"),
            ("Mbare", "Chitungwiza Road"),
            ("Highfield", "Glen Norah"),
            ("Glen Norah", "Glen View"),
            ("Airport Road", "Msasa"),
            ("Harare CBD", "Eastlea"),
            ("Belgravia", "Highlands"),
            ("Westgate", "Warren Park"),
            ("Marlborough", "Graniteside"),
        ]
        
        for start_name, end_name in connected_pairs:
            start = next((n for n in nodes if n.name == start_name), None)
            end = next((n for n in nodes if n.name == end_name), None)
            if start and end:
                # Calculate approximate distance
                distance = round(random.uniform(2, 12), 2)
                edge = Edge.objects.create(
                    start_node=start,
                    end_node=end,
                    distance=distance,
                    base_travel_time=round(distance * random.uniform(3, 6), 2),
                    congestion_level=round(random.uniform(1.0, 2.5), 2)
                )
                edges.append(edge)
        self.stdout.write(f"  ✓ Created {len(edges)} road connections")

        # -------------------------
        # 4. Trips with real locations
        # -------------------------
        for _ in range(40):
            vehicle = random.choice(vehicles)
            start_loc = random_location()
            dest_loc = random_location()
            
            start_time = datetime.now() - timedelta(hours=random.randint(0, 8))
            is_ongoing = random.random() > 0.4
            
            Trip.objects.create(
                vehicle=vehicle,
                start_location=start_loc['name'],
                destination=dest_loc['name'],
                start_lat=start_loc['lat'],
                start_lng=start_loc['lng'],
                dest_lat=dest_loc['lat'],
                dest_lng=dest_loc['lng'],
                start_time=start_time,
                end_time=None if is_ongoing else start_time + timedelta(minutes=random.randint(20, 90)),
                status='ongoing' if is_ongoing else random.choice(['completed', 'cancelled']),
                route=None
            )
        self.stdout.write(f"  ✓ Created 40 trips with real Harare locations")

        # -------------------------
        # 5. Location Logs (tracking history)
        # -------------------------
        for vehicle in vehicles[:15]:  # Track 15 active vehicles
            for i in range(8):
                loc = random_location()
                LocationLog.objects.create(
                    vehicle=vehicle,
                    latitude=loc['lat'] + random.uniform(-0.002, 0.002),
                    longitude=loc['lng'] + random.uniform(-0.002, 0.002),
                    speed=round(random.uniform(15, 50), 2),
                    timestamp=datetime.now() - timedelta(minutes=i*5)
                )
        self.stdout.write(f"  ✓ Created location tracking history")

        # -------------------------
        # 6. Real Traffic Events
        # -------------------------
        for _ in range(20):
            loc = random_location()
            event_description = random.choice(REAL_TRAFFIC_EVENTS)
            
            TrafficEvent.objects.create(
                latitude=loc['lat'] + random.uniform(-0.001, 0.001),
                longitude=loc['lng'] + random.uniform(-0.001, 0.001),
                severity=random.choice(['low', 'low', 'medium', 'high']),
                description=event_description,
                timestamp=datetime.now() - timedelta(minutes=random.randint(5, 180))
            )
        self.stdout.write(f"  ✓ Created 20 realistic traffic events")

        # -------------------------
        # 7. Traffic Conditions
        # -------------------------
        for edge in edges:
            TrafficCondition.objects.create(
                edge=edge,
                average_speed=round(random.uniform(25, 55), 2),
                congestion_level=round(random.uniform(1.0, 2.8), 2),
                updated_at=datetime.now()
            )
        self.stdout.write(f"  ✓ Created traffic conditions for road segments")

        # -------------------------
        # 8. Real System Alerts
        # -------------------------
        for _ in range(15):
            Alert.objects.create(
                message=random.choice(REAL_SYSTEM_ALERTS),
                alert_type=random.choice(['traffic', 'vehicle', 'vehicle', 'system']),
                is_active=random.choice([True, True, True, False]),  # mostly active
                created_at=datetime.now() - timedelta(minutes=random.randint(10, 300))
            )
        self.stdout.write(f"  ✓ Created 15 realistic system alerts")

        # -------------------------
        # 9. Performance Metrics
        # -------------------------
        for i in range(30):
            PerformanceMetric.objects.create(
                date=datetime.now().date() - timedelta(days=i),
                avg_travel_time=round(random.uniform(18, 45), 2),
                avg_response_time=round(random.uniform(6, 15), 2),
                avg_route_efficiency=round(random.uniform(75, 95), 2),
                fleet_utilization=round(random.uniform(60, 90), 2),
                idle_time=round(random.uniform(8, 35), 2)
            )
        self.stdout.write(f"  ✓ Created 30 days of performance metrics")

        # -------------------------
        # 10. Site Visit Logs
        # -------------------------
        users = list(User.objects.all()[:3])
        paths = ['/map/', '/fleet/', '/analytics/', '/trips/', '/traffic/', '/alerts/', '/']
        
        for _ in range(50):
            SiteVisitLog.objects.create(
                user=random.choice(users) if users else None,
                path=random.choice(paths),
                full_path=random.choice(paths) + ('?filter=active' if random.random() > 0.7 else ''),
                method='GET',
                ip_address=f"41.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                referrer=random.choice(['', 'https://google.com', 'direct']),
                timestamp=datetime.now() - timedelta(minutes=random.randint(0, 1440))
            )
        self.stdout.write(f"  ✓ Created 50 site visit logs")

        # -------------------------
        # 11. Routes
        # -------------------------
        for _ in range(25):
            start, end = random.sample(nodes, 2)
            Route.objects.create(
                start_node=start,
                end_node=end,
                total_distance=round(random.uniform(3, 18), 2),
                estimated_time=round(random.uniform(12, 45), 2),
                created_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
        self.stdout.write(f"  ✓ Created 25 optimized routes")

        self.stdout.write(self.style.SUCCESS('\n✅ Successfully seeded 200+ realistic records for Harare City Council!'))
        self.stdout.write(self.style.SUCCESS('   • 25 vehicles with Zimbabwean drivers'))
        self.stdout.write(self.style.SUCCESS('   • 25 real Harare locations'))
        self.stdout.write(self.style.SUCCESS('   • 40 trips between actual places'))
        self.stdout.write(self.style.SUCCESS('   • 20 realistic traffic events'))
        self.stdout.write(self.style.SUCCESS('   • Live GPS tracking data'))