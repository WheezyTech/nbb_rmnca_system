from django.contrib import admin
from .models import BloodRequest

from .models import (
    StorageLocation,
    InventoryRecord,
    BloodReservation,
    BloodIssue,
    BloodTransfer,
    InventoryMovement,
    BloodStockAlert,
)


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = (
        "location_id",
        "facility",
        "name",
        "storage_type",
        "temperature_min",
        "temperature_max",
        "is_active",
        "created_at",
    )
    list_filter = (
        "storage_type",
        "is_active",
        "facility",
    )
    search_fields = (
        "location_id",
        "name",
        "facility__name",
    )
    readonly_fields = (
        "location_id",
        "created_at",
    )
    ordering = (
        "facility__name",
        "name",
    )


@admin.register(InventoryRecord)
class InventoryRecordAdmin(admin.ModelAdmin):
    list_display = (
        "inventory_id",
        "blood_unit",
        "facility",
        "storage_location",
        "status",
        "received_at",
        "updated_at",
    )
    list_filter = (
        "status",
        "facility",
        "storage_location__storage_type",
    )
    search_fields = (
        "inventory_id",
        "blood_unit__unit_id",
        "blood_unit__barcode",
        "blood_unit__blood_group",
        "blood_unit__component_type",
    )
    readonly_fields = (
        "inventory_id",
        "blood_unit",
        "facility",
        "storage_location",
        "status",
        "received_at",
        "updated_at",
    )
    autocomplete_fields = (
        "blood_unit",
        "facility",
        "storage_location",
    )
    ordering = (
        "-received_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BloodReservation)
class BloodReservationAdmin(admin.ModelAdmin):
    list_display = (
        "reservation_id",
        "inventory",
        "facility",
        "patient_reference",
        "blood_group",
        "status",
        "reserved_at",
        "expires_at",
        "created_by",
    )
    list_filter = (
        "status",
        "blood_group",
        "facility",
    )
    search_fields = (
        "reservation_id",
        "inventory__inventory_id",
        "inventory__blood_unit__unit_id",
        "patient_reference",
        "blood_group",
    )
    readonly_fields = (
        "reservation_id",
        "inventory",
        "facility",
        "blood_group",
        "reserved_at",
        "status",
        "created_by",
    )
    autocomplete_fields = (
        "inventory",
        "facility",
        "created_by",
    )
    ordering = (
        "-reserved_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):

    list_display = (
        "request_id",
        "facility",
        "patient_reference",
        "blood_group",
        "component_type",
        "requested_units",
        "priority",
        "status",
        "requested_by",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "blood_group",
        "component_type",
        "facility",
    )

    search_fields = (
        "request_id",
        "patient_reference",
        "clinical_reference",
    )

    readonly_fields = (
        "request_id",
        "created_at",
        "updated_at",
        "reviewed_at",
    )

    ordering = (
        "-created_at",
    )


@admin.register(BloodIssue)
class BloodIssueAdmin(admin.ModelAdmin):
    list_display = (
        "issue_id",
        "inventory",
        "facility",
        "patient_reference",
        "clinical_reference",
        "status",
        "issued_at",
        "issued_by",
    )
    list_filter = (
        "status",
        "facility",
    )
    search_fields = (
        "issue_id",
        "inventory__inventory_id",
        "inventory__blood_unit__unit_id",
        "patient_reference",
        "clinical_reference",
    )
    readonly_fields = (
        "issue_id",
        "inventory",
        "facility",
        "patient_reference",
        "clinical_reference",
        "issued_at",
        "status",
        "issued_by",
    )
    autocomplete_fields = (
        "inventory",
        "facility",
        "issued_by",
    )
    ordering = (
        "-issued_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BloodTransfer)
class BloodTransferAdmin(admin.ModelAdmin):
    list_display = (
        "transfer_id",
        "blood_unit",
        "from_facility",
        "to_facility",
        "status",
        "requested_at",
        "dispatched_at",
        "received_at",
        "requested_by",
    )
    list_filter = (
        "status",
        "from_facility",
        "to_facility",
    )
    search_fields = (
        "transfer_id",
        "blood_unit__unit_id",
        "blood_unit__barcode",
        "from_facility__name",
        "to_facility__name",
    )
    readonly_fields = (
        "transfer_id",
        "blood_unit",
        "from_facility",
        "to_facility",
        "requested_at",
        "dispatched_at",
        "received_at",
        "status",
        "requested_by",
        "notes",
    )
    autocomplete_fields = (
        "blood_unit",
        "from_facility",
        "to_facility",
        "requested_by",
    )
    ordering = (
        "-requested_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        "movement_id",
        "inventory",
        "movement_type",
        "from_location",
        "to_location",
        "created_by",
        "created_at",
    )
    list_filter = (
        "movement_type",
        "from_location__facility",
        "to_location__facility",
    )
    search_fields = (
        "movement_id",
        "inventory__inventory_id",
        "inventory__blood_unit__unit_id",
        "reason",
    )
    readonly_fields = (
        "movement_id",
        "inventory",
        "movement_type",
        "from_location",
        "to_location",
        "reason",
        "created_by",
        "created_at",
    )
    autocomplete_fields = (
        "inventory",
        "from_location",
        "to_location",
        "created_by",
    )
    ordering = (
        "-created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(BloodStockAlert)
class BloodStockAlertAdmin(admin.ModelAdmin):

    list_display = (
        "alert_id",
        "facility",
        "blood_group",
        "component_type",
        "available_units",
        "alert_level",
        "status",
        "created_at",
        "acknowledged_at",
        "resolved_at",
    )

    list_filter = (
        "alert_level",
        "status",
        "facility",
        "blood_group",
        "component_type",
    )

    search_fields = (
        "alert_id",
        "facility__name",
        "blood_group",
        "component_type",
    )

    readonly_fields = (
        "alert_id",
        "created_at",
        "updated_at",
        "acknowledged_at",
        "acknowledged_by",
        "resolved_at",
        "resolved_by",
    )

    ordering = (
        "-created_at",
    )