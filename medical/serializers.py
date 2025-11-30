"""
Medical Serializers
Serializers für die Medical API (IoT Integration)
"""

from rest_framework import serializers
from .models import TemperatureLog, MedicalBatch, MedicalItem
from locations.models import Location


class TemperatureLogSerializer(serializers.ModelSerializer):
    """Serializer für Temperatur-Messungen von IoT-Sensoren"""

    batch_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    location_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = TemperatureLog
        fields = [
            'id',
            'batch',
            'batch_number',
            'measured_at',
            'temperature',
            'is_within_range',
            'location',
            'location_id',
            'device_id',
        ]
        read_only_fields = ['id', 'measured_at', 'is_within_range']

    def validate_temperature(self, value):
        """Validiere Temperatur-Wert"""
        if value < -50 or value > 50:
            raise serializers.ValidationError("Temperatur muss zwischen -50°C und 50°C liegen.")
        return value

    def create(self, validated_data):
        """Erstelle Temperatur-Log-Eintrag"""
        # Batch aus batch_number ermitteln (optional)
        batch_number = validated_data.pop('batch_number', None)
        location_id = validated_data.pop('location_id', None)

        if batch_number:
            try:
                batch = MedicalBatch.objects.get(batch_number=batch_number, is_active=True)
                validated_data['batch'] = batch
            except MedicalBatch.DoesNotExist:
                raise serializers.ValidationError(f"Charge '{batch_number}' nicht gefunden.")

        if location_id:
            try:
                location = Location.objects.get(id=location_id, is_active=True)
                validated_data['location'] = location
            except Location.DoesNotExist:
                raise serializers.ValidationError(f"Lagerort mit ID {location_id} nicht gefunden.")

        # Prüfe ob Temperatur im Sollbereich liegt
        temperature = validated_data['temperature']
        batch = validated_data.get('batch')

        if batch and batch.item:
            storage_condition = batch.item.storage_condition
            is_within_range = self._check_temperature_range(temperature, storage_condition)
            validated_data['is_within_range'] = is_within_range

            # Setze cold_chain_break Flag bei kritischer Abweichung
            if not is_within_range:
                # Prüfe ob Abweichung kritisch ist (>2°C außerhalb)
                if storage_condition == 'REFRIGERATED':  # 2-8°C
                    if temperature < 0 or temperature > 10:
                        batch.cold_chain_break = True
                        batch.save()

        return super().create(validated_data)

    def _check_temperature_range(self, temperature, storage_condition):
        """Prüfe ob Temperatur im Sollbereich liegt"""
        if storage_condition == 'REFRIGERATED':  # 2-8°C
            return 2.0 <= temperature <= 8.0
        elif storage_condition == 'FROZEN':  # <= -15°C
            return temperature <= -15.0
        elif storage_condition == 'ROOM_TEMPERATURE':  # 15-25°C
            return 15.0 <= temperature <= 25.0
        else:
            return True  # Keine Anforderung


class TemperatureLogCreateSerializer(serializers.Serializer):
    """Vereinfachter Serializer für Bulk-Upload von Sensor-Daten"""

    device_id = serializers.CharField(max_length=100)
    temperature = serializers.DecimalField(max_digits=5, decimal_places=2)
    location_id = serializers.IntegerField(required=False, allow_null=True)
    batch_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    measured_at = serializers.DateTimeField(required=False)

    def validate_temperature(self, value):
        if value < -50 or value > 50:
            raise serializers.ValidationError("Temperatur muss zwischen -50°C und 50°C liegen.")
        return value
