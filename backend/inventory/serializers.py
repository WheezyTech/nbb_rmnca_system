from rest_framework import serializers

from .models import (
    StorageLocation,
    InventoryRecord,
    BloodReservation,
    BloodIssue,
    BloodTransfer,
    InventoryMovement,
    BloodStockAlert,
    BloodRequest,
)


class StorageLocationSerializer(serializers.ModelSerializer):

    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    class Meta:
        model = StorageLocation
        fields = [
            "id",
            "location_id",
            "facility",
            "facility_name",
            "name",
            "storage_type",
            "temperature_min",
            "temperature_max",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "location_id",
            "created_at",
        ]


class InventoryRecordSerializer(serializers.ModelSerializer):

    unit_id = serializers.CharField(
        source="blood_unit.unit_id",
        read_only=True,
    )

    blood_group = serializers.CharField(
        source="blood_unit.blood_group",
        read_only=True,
    )

    component_type = serializers.CharField(
        source="blood_unit.component_type",
        read_only=True,
    )

    barcode = serializers.CharField(
        source="blood_unit.barcode",
        read_only=True,
    )

    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    storage_location_name = serializers.CharField(
        source="storage_location.name",
        read_only=True,
    )

    class Meta:
        model = InventoryRecord
        fields = [
            "id",
            "inventory_id",
            "blood_unit",
            "unit_id",
            "blood_group",
            "component_type",
            "barcode",
            "facility",
            "facility_name",
            "storage_location",
            "storage_location_name",
            "status",
            "received_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "inventory_id",
            "received_at",
            "updated_at",
        ]


class BloodReservationSerializer(serializers.ModelSerializer):

    inventory_unit = serializers.CharField(
        source="inventory.blood_unit.unit_id",
        read_only=True,
    )

    class Meta:
        model = BloodReservation
        fields = [
            "id",
            "reservation_id",
            "inventory",
            "inventory_unit",
            "facility",
            "patient_reference",
            "blood_group",
            "reserved_at",
            "expires_at",
            "status",
            "notes",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "reservation_id",
            "reserved_at",
        ]


class BloodIssueSerializer(serializers.ModelSerializer):

    unit_id = serializers.CharField(
        source="inventory.blood_unit.unit_id",
        read_only=True,
    )

    blood_group = serializers.CharField(
        source="inventory.blood_unit.blood_group",
        read_only=True,
    )

    component_type = serializers.CharField(
        source="inventory.blood_unit.component_type",
        read_only=True,
    )

    class Meta:
        model = BloodIssue
        fields = [
            "id",
            "issue_id",
            "inventory",
            "unit_id",
            "blood_group",
            "component_type",
            "facility",
            "patient_reference",
            "clinical_reference",
            "issued_at",
            "status",
            "issued_by",
            "notes",
        ]
        read_only_fields = [
            "id",
            "issue_id",
            "unit_id",
            "blood_group",
            "component_type",
            "facility",
            "issued_at",
            "status",
            "issued_by",
        ]


class BloodTransferSerializer(serializers.ModelSerializer):

    unit_id = serializers.CharField(
        source="blood_unit.unit_id",
        read_only=True,
    )

    from_facility_name = serializers.CharField(
        source="from_facility.name",
        read_only=True,
    )

    to_facility_name = serializers.CharField(
        source="to_facility.name",
        read_only=True,
    )

    class Meta:
        model = BloodTransfer
        fields = [
            "id",
            "transfer_id",
            "blood_unit",
            "unit_id",
            "from_facility",
            "from_facility_name",
            "to_facility",
            "to_facility_name",
            "requested_at",
            "dispatched_at",
            "received_at",
            "status",
            "requested_by",
            "notes",
        ]
        read_only_fields = [
            "id",
            "transfer_id",
            "requested_at",
        ]


class InventoryMovementSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = InventoryMovement
        fields = [
            "id",
            "movement_id",
            "inventory",
            "movement_type",
            "from_location",
            "to_location",
            "reason",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "movement_id",
            "created_at",
        ]

class InventoryTraceabilitySerializer(serializers.Serializer):
    inventory_id = serializers.CharField()
    unit_id = serializers.CharField()
    blood_group = serializers.CharField()
    component_type = serializers.CharField()
    barcode = serializers.CharField()
    current_facility = serializers.CharField()
    current_storage_location = serializers.CharField()
    current_status = serializers.CharField()
    events = serializers.ListField()

class BloodStockAlertSerializer(
    serializers.ModelSerializer
):

    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    acknowledged_by_name = serializers.SerializerMethodField()

    resolved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = BloodStockAlert

        fields = [
            "id",
            "alert_id",
            "facility",
            "facility_name",
            "blood_group",
            "component_type",
            "available_units",
            "alert_level",
            "status",
            "created_at",
            "updated_at",
            "acknowledged_at",
            "acknowledged_by",
            "acknowledged_by_name",
            "resolved_at",
            "resolved_by",
            "resolved_by_name",
            "resolution_notes",
        ]

        read_only_fields = [
            "id",
            "alert_id",
            "facility_name",
            "created_at",
            "updated_at",
            "acknowledged_at",
            "acknowledged_by",
            "acknowledged_by_name",
            "resolved_at",
            "resolved_by",
            "resolved_by_name",
        ]

    def get_acknowledged_by_name(self, obj):

        if not obj.acknowledged_by:
            return None

        return obj.acknowledged_by.get_full_name() or (
            obj.acknowledged_by.username
        )

    def get_resolved_by_name(self, obj):

        if not obj.resolved_by:
            return None

        return obj.resolved_by.get_full_name() or (
            obj.resolved_by.username
        )

class BloodRequestSerializer(serializers.ModelSerializer):

    facility_name = serializers.CharField(
        source="facility.name",
        read_only=True,
    )

    requested_by_name = serializers.SerializerMethodField()

    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = BloodRequest

        fields = [
            "id",
            "request_id",
            "facility",
            "facility_name",
            "patient_reference",
            "clinical_reference",
            "blood_group",
            "component_type",
            "requested_units",
            "priority",
            "clinical_indication",
            "required_by",
            "status",
            "requested_by",
            "requested_by_name",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "request_id",
            "facility",
            "facility_name",
            "requested_by",
            "requested_by_name",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]

    def get_requested_by_name(self, obj):

        return (
            obj.requested_by.get_full_name()
            or obj.requested_by.username
        )

    def get_reviewed_by_name(self, obj):

        if not obj.reviewed_by:
            return None

        return (
            obj.reviewed_by.get_full_name()
            or obj.reviewed_by.username
        )