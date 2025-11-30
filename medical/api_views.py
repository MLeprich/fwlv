"""
Medical API Views
REST API Endpunkte für IoT-Integration (Temperatursensoren)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Avg, Min, Max
from datetime import timedelta

from .models import TemperatureLog, MedicalBatch
from .serializers import TemperatureLogSerializer, TemperatureLogCreateSerializer

User = get_user_model()


class TemperatureLogViewSet(viewsets.ModelViewSet):
    """
    API ViewSet für Temperatur-Messungen

    Verwendet für IoT-Sensoren zur automatischen Datenübermittlung
    """
    queryset = TemperatureLog.objects.all().select_related('batch', 'location', 'measured_by')
    serializer_class = TemperatureLogSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filterset_fields = ['device_id', 'batch', 'location', 'is_within_range']
    ordering_fields = ['measured_at', 'temperature']
    ordering = ['-measured_at']

    def perform_create(self, serializer):
        """Setze measured_by auf den authentifizierten User (Sensor-Account)"""
        serializer.save(measured_by=self.request.user)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def temperature_log_bulk_create(request):
    """
    Bulk-Upload von Temperatur-Messungen

    POST /api/medical/temperature-logs/bulk/

    Body:
    {
        "measurements": [
            {
                "device_id": "sensor-01",
                "temperature": 5.2,
                "location_id": 123,
                "batch_number": "LOT-2024-001"
            },
            {
                "device_id": "sensor-02",
                "temperature": -18.5,
                "location_id": 124
            }
        ]
    }
    """
    measurements = request.data.get('measurements', [])

    if not measurements:
        return Response(
            {'error': 'Keine Messwerte übermittelt'},
            status=status.HTTP_400_BAD_REQUEST
        )

    created_logs = []
    errors = []

    for idx, measurement in enumerate(measurements):
        serializer = TemperatureLogCreateSerializer(data=measurement)

        if serializer.is_valid():
            # Erstelle TemperatureLog
            try:
                data = serializer.validated_data

                # Batch ermitteln (optional)
                batch = None
                batch_number = data.get('batch_number')
                if batch_number:
                    try:
                        batch = MedicalBatch.objects.get(batch_number=batch_number, is_active=True)
                    except MedicalBatch.DoesNotExist:
                        errors.append({
                            'index': idx,
                            'error': f"Charge '{batch_number}' nicht gefunden"
                        })
                        continue

                # Location ermitteln (optional)
                location = None
                location_id = data.get('location_id')
                if location_id:
                    from locations.models import Location
                    try:
                        location = Location.objects.get(id=location_id, is_active=True)
                    except Location.DoesNotExist:
                        errors.append({
                            'index': idx,
                            'error': f"Lagerort mit ID {location_id} nicht gefunden"
                        })
                        continue

                # Erstelle Log-Eintrag
                log = TemperatureLog.objects.create(
                    batch=batch,
                    temperature=data['temperature'],
                    device_id=data['device_id'],
                    location=location,
                    measured_by=request.user,
                    measured_at=data.get('measured_at', timezone.now())
                )

                # Prüfe Temperaturbereich
                if batch and batch.item:
                    storage_condition = batch.item.storage_condition
                    log.is_within_range = _check_temperature_range(
                        data['temperature'],
                        storage_condition
                    )
                    log.save()

                    # Setze cold_chain_break bei kritischer Abweichung
                    if not log.is_within_range:
                        if storage_condition == 'REFRIGERATED':
                            if data['temperature'] < 0 or data['temperature'] > 10:
                                batch.cold_chain_break = True
                                batch.save()

                created_logs.append({
                    'id': log.id,
                    'device_id': log.device_id,
                    'temperature': str(log.temperature),
                    'measured_at': log.measured_at.isoformat()
                })

            except Exception as e:
                errors.append({
                    'index': idx,
                    'error': str(e)
                })
        else:
            errors.append({
                'index': idx,
                'error': serializer.errors
            })

    return Response({
        'created': len(created_logs),
        'failed': len(errors),
        'logs': created_logs,
        'errors': errors
    }, status=status.HTTP_201_CREATED if created_logs else status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def temperature_stats(request):
    """
    Statistiken für Temperatur-Überwachung

    GET /api/medical/temperature-logs/stats/

    Query Parameters:
    - hours: Zeitraum in Stunden (default: 24)
    - device_id: Filter nach Gerät
    - location_id: Filter nach Lagerort
    """
    hours = int(request.query_params.get('hours', 24))
    device_id = request.query_params.get('device_id')
    location_id = request.query_params.get('location_id')

    since = timezone.now() - timedelta(hours=hours)

    queryset = TemperatureLog.objects.filter(measured_at__gte=since)

    if device_id:
        queryset = queryset.filter(device_id=device_id)

    if location_id:
        queryset = queryset.filter(location_id=location_id)

    stats = queryset.aggregate(
        avg_temperature=Avg('temperature'),
        min_temperature=Min('temperature'),
        max_temperature=Max('temperature'),
        total_measurements=queryset.count()
    )

    # Zähle Abweichungen
    warnings = queryset.filter(is_within_range=False).count()

    return Response({
        'period_hours': hours,
        'avg_temperature': stats['avg_temperature'],
        'min_temperature': stats['min_temperature'],
        'max_temperature': stats['max_temperature'],
        'total_measurements': stats['total_measurements'],
        'warnings': warnings,
        'ok_measurements': stats['total_measurements'] - warnings
    })


def _check_temperature_range(temperature, storage_condition):
    """Hilfsfunktion: Prüfe ob Temperatur im Sollbereich liegt"""
    if storage_condition == 'REFRIGERATED':  # 2-8°C
        return 2.0 <= temperature <= 8.0
    elif storage_condition == 'FROZEN':  # <= -15°C
        return temperature <= -15.0
    elif storage_condition == 'ROOM_TEMPERATURE':  # 15-25°C
        return 15.0 <= temperature <= 25.0
    else:
        return True
