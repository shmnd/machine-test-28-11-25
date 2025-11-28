from rest_framework import serializers
from .models import Airport, Route

class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ['id', 'code', 'name']



class RouteSerializer(serializers.ModelSerializer):
    from_code = serializers.CharField(write_only=True)
    to_code = serializers.CharField(write_only=True)
    from_airport = AirportSerializer(read_only=True)
    to_airport = AirportSerializer(read_only=True)

    class Meta:
        model = Route
        fields = ['id', 'from_airport', 'to_airport', 'from_code', 'to_code', 'position', 'duration']

    def validate_position(self, position):
        if position not in (Route.LEFT, Route.RIGHT):
            raise serializers.ValidationError('Position must be left or right.')
        return position

    def validate_duration(self, duration):
        if duration <= 0:
            raise serializers.ValidationError('Duration must be a positive integer.')
        return duration

    def create(self, validated_data):
        from_code = validated_data.pop('from_code').strip().upper()
        to_code = validated_data.pop('to_code').strip().upper()
        from_airport, _ = Airport.objects.get_or_create(code=from_code)
        to_airport, _ = Airport.objects.get_or_create(code=to_code)
        # Use update_or_create to replace left/right child for a from_airport
        route, _ = Route.objects.update_or_create(
            from_airport=from_airport,
            position=validated_data['position'],
            defaults={'to_airport': to_airport, 'duration': validated_data['duration']},
        )
        return route



class NthNodeInputSerializer(serializers.Serializer):
    start_code = serializers.CharField()
    direction = serializers.ChoiceField(choices=[Route.LEFT, Route.RIGHT])
    n = serializers.IntegerField(min_value=1)

    



class ShortestPathInputSerializer(serializers.Serializer):
    source = serializers.CharField()
    target = serializers.CharField()
