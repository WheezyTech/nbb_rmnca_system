from datetime import timedelta

from django.db.models import Count, Q

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from accounts.access import get_user_scope

from django.core.exceptions import ValidationError


from .services.transactions import (
    release_inventory,
    reserve_blood,
    release_reservation,
    issue_blood,
    return_blood,
    mark_transfused,
    discard_blood,
    request_transfer,
    approve_transfer,
    reject_transfer,
    dispatch_transfer,
    receive_transfer,
)

from .services.transfer_notifications import (
    transfer_requested_notification,
    transfer_approved_notification,
    transfer_dispatched_notification,
    transfer_received_notification,
)

from .services.transfers import (
    get_transfer_recommendations,
    get_transfer_opportunity,
    request_transfer_from_recommendation,
)

from facilities.models import Facility

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

from .serializers import (
    StorageLocationSerializer,
    InventoryRecordSerializer,
    BloodReservationSerializer,
    BloodIssueSerializer,
    BloodTransferSerializer,
    InventoryMovementSerializer,
    InventoryTraceabilitySerializer,
    BloodStockAlertSerializer,
    BloodRequestSerializer,
)

from .services.alerts import (
    get_stock_alert,
    generate_shortage_alerts,
    get_stock_alerts,
)

from .services.shortages import (
    get_zero_stock_by_facility,
    get_facility_shortage_ranking,
)

class InventoryScopedMixin:

    def scoped_queryset(self, queryset):

        user = self.request.user
        scope = get_user_scope(user)

        if scope == "national":
            return queryset

        if not user.facility_id:
            return queryset.none()

        return queryset.filter(
            facility_id=user.facility_id
        )


class StorageLocationViewSet(
    InventoryScopedMixin,
    viewsets.ModelViewSet,
):

    queryset = StorageLocation.objects.select_related(
        "facility"
    ).all()

    serializer_class = StorageLocationSerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "location_id",
        "name",
        "facility__name",
    ]

    def get_queryset(self):
        return self.scoped_queryset(
            super().get_queryset()
        )


class InventoryRecordViewSet(
    InventoryScopedMixin,
    viewsets.ReadOnlyModelViewSet,
):

    queryset = InventoryRecord.objects.select_related(
        "blood_unit",
        "facility",
        "storage_location",
    ).all()

    serializer_class = InventoryRecordSerializer
    permission_classes = [IsAuthenticated]

    search_fields = [
        "inventory_id",
        "blood_unit__unit_id",
        "blood_unit__barcode",
        "blood_unit__blood_group",
        "blood_unit__component_type",
    ]

    def get_queryset(self):
        return self.scoped_queryset(
            super().get_queryset()
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="release",
    )
    def release(self, request, pk=None):

        inventory = self.get_object()

        inventory = release_inventory(
            inventory_id=inventory.pk,
            released_by=request.user,
        )

        serializer = self.get_serializer(
            inventory
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="reserve",
    )
    def reserve(self, request, pk=None):

        inventory = self.get_object()
        user = request.user

        if not user.facility_id:
            return Response(
                {
                    "detail": (
                        "User is not assigned "
                        "to a facility."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        reservation = reserve_blood(
            inventory_id=inventory.pk,
            facility=user.facility,
            created_by=user,
            patient_reference=request.data.get(
                "patient_reference",
                "",
            ),
            blood_group=request.data.get(
                "blood_group",
                "",
            ),
            expires_at=request.data.get(
                "expires_at"
            ),
            notes=request.data.get(
                "notes",
                "",
            ),
        )

        return Response(
            {
                "reservation_id": (
                    reservation.reservation_id
                ),
                "inventory_id": (
                    reservation.inventory.inventory_id
                ),
                "status": reservation.status,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="issue",
    )
    def issue(self, request, pk=None):

        inventory = self.get_object()
        user = request.user

        if not user.facility_id:
            return Response(
                {
                    "detail": (
                        "User is not assigned "
                        "to a facility."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        issue_record = issue_blood(
            inventory_id=inventory.pk,
            facility=user.facility,
            issued_by=user,
            patient_reference=request.data.get(
                "patient_reference",
                "",
            ),
            clinical_reference=request.data.get(
                "clinical_reference",
                "",
            ),
            notes=request.data.get(
                "notes",
                "",
            ),
        )

        return Response(
            {
                "issue_id": issue_record.issue_id,
                "inventory_id": (
                    issue_record.inventory.inventory_id
                ),
                "status": issue_record.status,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="discard",
    )
    def discard(self, request, pk=None):

        inventory = self.get_object()

        discarded = discard_blood(
            inventory_id=inventory.pk,
            discarded_by=request.user,
            reason=request.data.get(
                "reason",
                "",
            ),
        )

        serializer = self.get_serializer(
            discarded
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="stock-summary",
    )
    def stock_summary(self, request):

        queryset = self.get_queryset().filter(
            status=InventoryRecord.Status.AVAILABLE
        )

        summary = queryset.values(
            "blood_unit__blood_group",
            "blood_unit__component_type",
        ).annotate(
            units=Count("id")
        ).order_by(
            "blood_unit__blood_group",
            "blood_unit__component_type",
        )

        data = [
            {
                "blood_group": item[
                    "blood_unit__blood_group"
                ],
                "component_type": item[
                    "blood_unit__component_type"
                ],
                "units": item["units"],
            }
            for item in summary
        ]

        return Response(data)

    @action(
        detail=False,
        methods=["get"],
        url_path="dashboard",
    )
    def dashboard(self, request):

        queryset = self.get_queryset()

        # Overall inventory counts
        total_units = queryset.count()

        available = queryset.filter(
            status=InventoryRecord.Status.AVAILABLE
        ).count()

        reserved = queryset.filter(
            status=InventoryRecord.Status.RESERVED
        ).count()

        issued = queryset.filter(
            status=InventoryRecord.Status.ISSUED
        ).count()

        transferred = queryset.filter(
            status=InventoryRecord.Status.TRANSFERRED
        ).count()

        expired = queryset.filter(
            status=InventoryRecord.Status.EXPIRED
        ).count()

        discarded = queryset.filter(
            status=InventoryRecord.Status.DISCARDED
        ).count()

        # Blood group/component breakdown
        stock_breakdown = (
            queryset
            .filter(
                status=InventoryRecord.Status.AVAILABLE
            )
            .values(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .annotate(
                units=Count("id")
            )
            .order_by(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
        )

        breakdown = [
            {
                "blood_group": item[
                    "blood_unit__blood_group"
                ],
                "component_type": item[
                    "blood_unit__component_type"
                ],
                "units": item["units"],
            }
            for item in stock_breakdown
        ]

        # Persistent alerts
        alert_queryset = BloodStockAlert.objects.select_related(
            "facility",
            "acknowledged_by",
            "resolved_by",
        )

        user = request.user
        scope = get_user_scope(user)

        if scope != "national":

            if not user.facility_id:
                alert_queryset = alert_queryset.none()

            else:
                alert_queryset = alert_queryset.filter(
                    facility_id=user.facility_id
                )

        open_alerts = alert_queryset.filter(
            status=BloodStockAlert.AlertStatus.OPEN
        ).count()

        acknowledged_alerts = alert_queryset.filter(
            status=BloodStockAlert.AlertStatus.ACKNOWLEDGED
        ).count()

        resolved_alerts = alert_queryset.filter(
            status=BloodStockAlert.AlertStatus.RESOLVED
        ).count()

        critical_alerts = alert_queryset.filter(
            alert_level=BloodStockAlert.AlertLevel.CRITICAL
        ).exclude(
            status=BloodStockAlert.AlertStatus.RESOLVED
        ).count()

        zero_stock_alerts = alert_queryset.filter(
            alert_level=BloodStockAlert.AlertLevel.ZERO_STOCK
        ).exclude(
            status=BloodStockAlert.AlertStatus.RESOLVED
        ).count()

        low_stock_alerts = alert_queryset.filter(
            alert_level=BloodStockAlert.AlertLevel.LOW
        ).exclude(
            status=BloodStockAlert.AlertStatus.RESOLVED
        ).count()

        data = {
            "inventory": {
                "total_units": total_units,
                "available": available,
                "reserved": reserved,
                "issued": issued,
                "transferred": transferred,
                "expired": expired,
                "discarded": discarded,
            },

            "alerts": {
                "open": open_alerts,
                "acknowledged": acknowledged_alerts,
                "resolved": resolved_alerts,
                "critical": critical_alerts,
                "zero_stock": zero_stock_alerts,
                "low_stock": low_stock_alerts,
            },

            "stock_breakdown": breakdown,
        }

        return Response(
            data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="facility-dashboard",
    )
    def facility_dashboard(self, request):

        user = request.user
        scope = get_user_scope(user)

        # -------------------------------------------------
        # FACILITY USERS
        # -------------------------------------------------
        if scope != "national":

            if not user.facility_id:
                return Response(
                    {
                        "detail": (
                            "User is not assigned "
                            "to a facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            facility = Facility.objects.get(
                pk=user.facility_id
            )

            queryset = InventoryRecord.objects.filter(
                facility=facility
            )

            alerts = BloodStockAlert.objects.filter(
                facility=facility
            )

            available = queryset.filter(
                status=InventoryRecord.Status.AVAILABLE
            ).count()

            reserved = queryset.filter(
                status=InventoryRecord.Status.RESERVED
            ).count()

            issued = queryset.filter(
                status=InventoryRecord.Status.ISSUED
            ).count()

            transferred = queryset.filter(
                status=InventoryRecord.Status.TRANSFERRED
            ).count()

            expired = queryset.filter(
                status=InventoryRecord.Status.EXPIRED
            ).count()

            discarded = queryset.filter(
                status=InventoryRecord.Status.DISCARDED
            ).count()

            breakdown = (
                queryset
                .filter(
                    status=InventoryRecord.Status.AVAILABLE
                )
                .values(
                    "blood_unit__blood_group",
                    "blood_unit__component_type",
                )
                .annotate(
                    units=Count("id")
                )
                .order_by(
                    "blood_unit__blood_group",
                    "blood_unit__component_type",
                )
            )

            stock_breakdown = [
                {
                    "blood_group": item[
                        "blood_unit__blood_group"
                    ],
                    "component_type": item[
                        "blood_unit__component_type"
                    ],
                    "units": item["units"],
                }
                for item in breakdown
            ]

            return Response(
                {
                    "scope": "facility",

                    "facility": {
                        "id": facility.id,
                        "name": facility.name,
                    },

                    "inventory": {
                        "total_units": queryset.count(),
                        "available": available,
                        "reserved": reserved,
                        "issued": issued,
                        "transferred": transferred,
                        "expired": expired,
                        "discarded": discarded,
                    },

                    "alerts": {
                        "open": alerts.filter(
                            status=BloodStockAlert.AlertStatus.OPEN
                        ).count(),

                        "acknowledged": alerts.filter(
                            status=BloodStockAlert.AlertStatus.ACKNOWLEDGED
                        ).count(),

                        "resolved": alerts.filter(
                            status=BloodStockAlert.AlertStatus.RESOLVED
                        ).count(),

                        "critical": alerts.filter(
                            alert_level=BloodStockAlert.AlertLevel.CRITICAL
                        ).exclude(
                            status=BloodStockAlert.AlertStatus.RESOLVED
                        ).count(),

                        "low": alerts.filter(
                            alert_level=BloodStockAlert.AlertLevel.LOW
                        ).exclude(
                            status=BloodStockAlert.AlertStatus.RESOLVED
                        ).count(),

                        "zero_stock": alerts.filter(
                            alert_level=BloodStockAlert.AlertLevel.ZERO_STOCK
                        ).exclude(
                            status=BloodStockAlert.AlertStatus.RESOLVED
                        ).count(),
                    },

                    "stock_breakdown": stock_breakdown,
                },

                status=status.HTTP_200_OK,
            )

        # -------------------------------------------------
        # NATIONAL DASHBOARD
        # -------------------------------------------------

        facilities = Facility.objects.all().order_by(
            "name"
        )

        facility_data = []

        for facility in facilities:

            queryset = InventoryRecord.objects.filter(
                facility=facility
            )

            alerts = BloodStockAlert.objects.filter(
                facility=facility
            )

            available = queryset.filter(
                status=InventoryRecord.Status.AVAILABLE
            ).count()

            reserved = queryset.filter(
                status=InventoryRecord.Status.RESERVED
            ).count()

            issued = queryset.filter(
                status=InventoryRecord.Status.ISSUED
            ).count()

            transferred = queryset.filter(
                status=InventoryRecord.Status.TRANSFERRED
            ).count()

            expired = queryset.filter(
                status=InventoryRecord.Status.EXPIRED
            ).count()

            discarded = queryset.filter(
                status=InventoryRecord.Status.DISCARDED
            ).count()

            critical = alerts.filter(
                alert_level=BloodStockAlert.AlertLevel.CRITICAL
            ).exclude(
                status=BloodStockAlert.AlertStatus.RESOLVED
            ).count()

            low = alerts.filter(
                alert_level=BloodStockAlert.AlertLevel.LOW
            ).exclude(
                status=BloodStockAlert.AlertStatus.RESOLVED
            ).count()

            zero_stock = alerts.filter(
                alert_level=BloodStockAlert.AlertLevel.ZERO_STOCK
            ).exclude(
                status=BloodStockAlert.AlertStatus.RESOLVED
            ).count()

            facility_data.append(
                {
                    "facility_id": facility.id,
                    "facility_name": facility.name,

                    "total_units": queryset.count(),
                    "available": available,
                    "reserved": reserved,
                    "issued": issued,
                    "transferred": transferred,
                    "expired": expired,
                    "discarded": discarded,

                    "critical_alerts": critical,
                    "low_stock_alerts": low,
                    "zero_stock_alerts": zero_stock,

                    "shortage_score": (
                        (zero_stock * 3)
                        + (critical * 2)
                        + low
                    ),
                }
            )

        # Highest shortage score first
        facility_data.sort(
            key=lambda item: (
                item["shortage_score"],
                -item["available"],
            ),
            reverse=True,
        )

        # National totals
        all_inventory = InventoryRecord.objects.all()

        all_alerts = BloodStockAlert.objects.all()

        national_summary = {
            "facilities": facilities.count(),

            "total_units": all_inventory.count(),

            "available": all_inventory.filter(
                status=InventoryRecord.Status.AVAILABLE
            ).count(),

            "reserved": all_inventory.filter(
                status=InventoryRecord.Status.RESERVED
            ).count(),

            "issued": all_inventory.filter(
                status=InventoryRecord.Status.ISSUED
            ).count(),

            "transferred": all_inventory.filter(
                status=InventoryRecord.Status.TRANSFERRED
            ).count(),

            "expired": all_inventory.filter(
                status=InventoryRecord.Status.EXPIRED
            ).count(),

            "discarded": all_inventory.filter(
                status=InventoryRecord.Status.DISCARDED
            ).count(),

            "open_alerts": all_alerts.filter(
                status=BloodStockAlert.AlertStatus.OPEN
            ).count(),

            "critical_alerts": all_alerts.filter(
                alert_level=BloodStockAlert.AlertLevel.CRITICAL
            ).exclude(
                status=BloodStockAlert.AlertStatus.RESOLVED
            ).count(),

            "low_stock_alerts": all_alerts.filter(
                alert_level=BloodStockAlert.AlertLevel.LOW
            ).exclude(
                status=BloodStockAlert.AlertStatus.RESOLVED
            ).count(),

            "zero_stock_alerts": all_alerts.filter(
                alert_level=BloodStockAlert.AlertLevel.ZERO_STOCK
            ).exclude(
                status=BloodStockAlert.AlertStatus.RESOLVED
            ).count(),
        }

        return Response(
            {
                "scope": "national",
                "summary": national_summary,
                "facility_ranking": facility_data,
            },

            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="national-dashboard",
    )
    def national_dashboard(self, request):

        user = request.user
        scope = get_user_scope(user)

        if scope != "national":
            return Response(
                {
                    "detail": (
                        "National inventory access "
                        "is restricted to national users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = self.get_queryset()

        # Overall stock
        total_units = queryset.count()

        available = queryset.filter(
            status=InventoryRecord.Status.AVAILABLE
        ).count()

        reserved = queryset.filter(
            status=InventoryRecord.Status.RESERVED
        ).count()

        issued = queryset.filter(
            status=InventoryRecord.Status.ISSUED
        ).count()

        transferred = queryset.filter(
            status=InventoryRecord.Status.TRANSFERRED
        ).count()

        transfused = queryset.filter(
            status=InventoryRecord.Status.TRANSFUSED
        ).count()

        expired = queryset.filter(
            status=InventoryRecord.Status.EXPIRED
        ).count()

        discarded = queryset.filter(
            status=InventoryRecord.Status.DISCARDED
        ).count()

        # Blood group breakdown
        blood_groups = (
            queryset
            .values("blood_unit__blood_group")
            .annotate(units=Count("id"))
            .order_by("blood_unit__blood_group")
        )

        blood_group_data = [
            {
                "blood_group": item[
                    "blood_unit__blood_group"
                ],
                "units": item["units"],
            }
            for item in blood_groups
        ]

        # Component breakdown
        components = (
            queryset
            .values("blood_unit__component_type")
            .annotate(units=Count("id"))
            .order_by("blood_unit__component_type")
        )

        component_data = [
            {
                "component_type": item[
                    "blood_unit__component_type"
                ],
                "units": item["units"],
            }
            for item in components
        ]

        # Facility breakdown
        facilities = (
            queryset
            .values(
                "facility_id",
                "facility__name",
            )
            .annotate(units=Count("id"))
            .order_by("facility__name")
        )

        facility_data = [
            {
                "facility_id": item["facility_id"],
                "facility": item["facility__name"],
                "units": item["units"],
            }
            for item in facilities
        ]

        return Response(
            {
                "summary": {
                    "total_units": total_units,
                    "available": available,
                    "reserved": reserved,
                    "issued": issued,
                    "transferred": transferred,
                    "transfused": transfused,
                    "expired": expired,
                    "discarded": discarded,
                },
                "blood_groups": blood_group_data,
                "components": component_data,
                "facilities": facility_data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="national-stock-matrix",
    )
    def national_stock_matrix(self, request):
        """
        National available blood stock matrix.

        Shows available blood units grouped by:
        - Facility
        - Blood group
        - Component type
        """

        user = request.user
        scope = get_user_scope(user)

        # National access only
        if scope != "national":
            return Response(
                {
                    "detail": (
                        "National inventory access "
                        "is restricted to national users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only AVAILABLE blood stock
        queryset = (
            InventoryRecord.objects
            .filter(
                status=InventoryRecord.Status.AVAILABLE
            )
            .values(
                "facility_id",
                "facility__name",
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .annotate(
                units=Count("id")
            )
            .order_by(
                "facility__name",
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
        )

        matrix = []

        for item in queryset:
            matrix.append(
                {
                    "facility_id": item["facility_id"],
                    "facility": item["facility__name"],
                    "blood_group": item[
                        "blood_unit__blood_group"
                    ],
                    "component_type": item[
                        "blood_unit__component_type"
                    ],
                    "units": item["units"],
                }
            )

        # National totals by blood group + component
        national_totals = (
            InventoryRecord.objects
            .filter(
                status=InventoryRecord.Status.AVAILABLE
            )
            .values(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .annotate(
                units=Count("id")
            )
            .order_by(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
        )

        totals = []

        for item in national_totals:
            totals.append(
                {
                    "blood_group": item[
                        "blood_unit__blood_group"
                    ],
                    "component_type": item[
                        "blood_unit__component_type"
                    ],
                    "units": item["units"],
                }
            )

        return Response(
            {
                "scope": "national",
                "matrix": matrix,
                "national_totals": totals,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="transfer-recommendations",
    )
    def transfer_recommendations(self, request):
        """
        Return ranked blood transfer recommendations.

        National users can see recommendations across
        all facilities.

        Facility users only see recommendations involving
        their own facility.
        """

        user = request.user
        scope = get_user_scope(user)

        recommendations = get_transfer_recommendations()

        # -------------------------------------------------
        # FACILITY SCOPE
        # -------------------------------------------------

        if scope != "national":

            if not user.facility_id:
                return Response(
                    {
                        "detail": (
                            "User is not assigned "
                            "to a facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            facility_id = user.facility_id

            recommendations = [
                item
                for item in recommendations
                if (
                    item["source_facility_id"]
                    == facility_id
                    or
                    item["destination_facility_id"]
                    == facility_id
                )
            ]

        return Response(
            {
                "count": len(recommendations),
                "recommendations": recommendations,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="transfer-opportunity",
    )
    def transfer_opportunity(self, request):
        """
        Return detailed information for one transfer opportunity.

        Required query parameters:

            source_facility_id
            destination_facility_id
            blood_group
            component_type
        """

        source_facility_id = request.query_params.get(
            "source_facility_id"
        )

        destination_facility_id = request.query_params.get(
            "destination_facility_id"
        )

        blood_group = request.query_params.get(
            "blood_group"
        )

        component_type = request.query_params.get(
            "component_type"
        )

        # -------------------------------------------------
        # VALIDATE PARAMETERS
        # -------------------------------------------------

        missing = []

        if not source_facility_id:
            missing.append("source_facility_id")

        if not destination_facility_id:
            missing.append("destination_facility_id")

        if not blood_group:
            missing.append("blood_group")

        if not component_type:
            missing.append("component_type")

        if missing:

            return Response(
                {
                    "detail": (
                        "Missing required parameters."
                    ),
                    "required": missing,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # CONVERT FACILITY IDS
        # -------------------------------------------------

        try:

            source_facility_id = int(
                source_facility_id
            )

            destination_facility_id = int(
                destination_facility_id
            )

        except (TypeError, ValueError):

            return Response(
                {
                    "detail": (
                        "Facility IDs must be valid integers."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # FACILITY SCOPE
        # -------------------------------------------------

        user = request.user
        scope = get_user_scope(user)

        if scope != "national":

            if not user.facility_id:

                return Response(
                    {
                        "detail": (
                            "User is not assigned "
                            "to a facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if (
                source_facility_id
                != user.facility_id
                and
                destination_facility_id
                != user.facility_id
            ):

                return Response(
                    {
                        "detail": (
                            "You can only view transfer "
                            "opportunities involving "
                            "your facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # -------------------------------------------------
        # SAME FACILITY PROTECTION
        # -------------------------------------------------

        if (
            source_facility_id
            == destination_facility_id
        ):

            return Response(
                {
                    "detail": (
                        "Source and destination facilities "
                        "must be different."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # CHECK FACILITIES EXIST
        # -------------------------------------------------

        source_facility = Facility.objects.filter(
            pk=source_facility_id
        ).first()

        destination_facility = Facility.objects.filter(
            pk=destination_facility_id
        ).first()

        if source_facility is None:

            return Response(
                {
                    "detail": (
                        "Source facility was not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if destination_facility is None:

            return Response(
                {
                    "detail": (
                        "Destination facility was not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------------------------------
        # GET OPPORTUNITY
        # -------------------------------------------------

        opportunity = get_transfer_opportunity(
            source_facility_id=source_facility_id,
            destination_facility_id=(
                destination_facility_id
            ),
            blood_group=blood_group,
            component_type=component_type,
        )

        if opportunity is None:

            return Response(
                {
                    "detail": (
                        "No active transfer opportunity "
                        "matches the supplied criteria."
                    ),

                    "source_facility": {
                        "id": source_facility.id,
                        "name": source_facility.name,
                    },

                    "destination_facility": {
                        "id": destination_facility.id,
                        "name": destination_facility.name,
                    },

                    "blood_group": blood_group,
                    "component_type": component_type,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------------------------------
        # DETAILED RESPONSE
        # -------------------------------------------------

        response_data = {
            "opportunity": opportunity,

            "source": {
                "facility_id": source_facility.id,
                "facility_name": source_facility.name,
                "available_units": (
                    opportunity[
                        "source_available_units"
                    ]
                ),
                "transferable_units": (
                    opportunity[
                        "source_transferable_units"
                    ]
                ),
            },

            "destination": {
                "facility_id": destination_facility.id,
                "facility_name": destination_facility.name,
                "available_units": (
                    opportunity[
                        "destination_available_units"
                    ]
                ),
            },

            "blood": {
                "blood_group": (
                    opportunity["blood_group"]
                ),
                "component_type": (
                    opportunity["component_type"]
                ),
            },

            "recommendation": {
                "recommended_units": (
                    opportunity[
                        "recommended_units"
                    ]
                ),
                "shortage_level": (
                    opportunity["shortage_level"]
                ),
                "priority": (
                    opportunity["priority"]
                ),
            },

            "action": {
                "can_request_transfer": True,
                "creates_transfer": False,
            },
        }

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="facility-comparison",
    )
    def facility_comparison(self, request):
        """
        National facility-by-facility stock comparison.

        Compares available blood stock across facilities
        and identifies shortage severity.
        """

        user = request.user
        scope = get_user_scope(user)

        # National access only
        if scope != "national":
            return Response(
                {
                    "detail": (
                        "National inventory access "
                        "is restricted to national users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # -------------------------------------------------
        # All blood group/component combinations
        # -------------------------------------------------

        combinations = (
            InventoryRecord.objects
            .values(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .distinct()
        )

        combinations = [
            (
                item["blood_unit__blood_group"],
                item["blood_unit__component_type"],
            )
            for item in combinations
        ]

        # -------------------------------------------------
        # Facilities
        # -------------------------------------------------

        facilities = Facility.objects.all().order_by(
            "name"
        )

        facility_data = []

        # -------------------------------------------------
        # Compare every facility
        # -------------------------------------------------

        for facility in facilities:

            available_queryset = (
                InventoryRecord.objects
                .filter(
                    facility=facility,
                    status=InventoryRecord.Status.AVAILABLE,
                )
            )

            # ---------------------------------------------
            # Stock by blood group/component
            # ---------------------------------------------

            stock = (
                available_queryset
                .values(
                    "blood_unit__blood_group",
                    "blood_unit__component_type",
                )
                .annotate(
                    units=Count("id")
                )
            )

            stock_map = {
                (
                    item["blood_unit__blood_group"],
                    item["blood_unit__component_type"],
                ): item["units"]
                for item in stock
            }

            # ---------------------------------------------
            # Shortage indicators
            # ---------------------------------------------

            zero_stock = 0
            critical = 0
            low = 0
            normal = 0

            stock_matrix = []

            for blood_group, component_type in combinations:

                units = stock_map.get(
                    (
                        blood_group,
                        component_type,
                    ),
                    0,
                )

                alert_level = get_stock_alert(
                    units
                )

                if alert_level == "ZERO_STOCK":
                    zero_stock += 1

                elif alert_level == "CRITICAL":
                    critical += 1

                elif alert_level == "LOW":
                    low += 1

                else:
                    normal += 1

                stock_matrix.append(
                    {
                        "blood_group": blood_group,
                        "component_type": component_type,
                        "units": units,
                        "alert_level": alert_level,
                    }
                )

            # ---------------------------------------------
            # Shortage score
            # ---------------------------------------------

            shortage_score = (
                (zero_stock * 3)
                + (critical * 2)
                + low
            )

            # ---------------------------------------------
            # Overall facility status
            # ---------------------------------------------

            if zero_stock > 0:
                shortage_status = "SEVERE"

            elif critical > 0:
                shortage_status = "CRITICAL"

            elif low > 0:
                shortage_status = "LOW"

            else:
                shortage_status = "NORMAL"

            # ---------------------------------------------
            # Facility totals
            # ---------------------------------------------

            total_available = available_queryset.count()

            total_inventory = (
                InventoryRecord.objects
                .filter(
                    facility=facility
                )
                .count()
            )

            # ---------------------------------------------
            # Persistent alerts
            # ---------------------------------------------

            alerts = BloodStockAlert.objects.filter(
                facility=facility
            )

            open_alerts = alerts.filter(
                status=BloodStockAlert.AlertStatus.OPEN
            ).count()

            active_critical_alerts = (
                alerts
                .filter(
                    alert_level=(
                        BloodStockAlert.AlertLevel.CRITICAL
                    )
                )
                .exclude(
                    status=(
                        BloodStockAlert.AlertStatus.RESOLVED
                    )
                )
                .count()
            )

            active_low_alerts = (
                alerts
                .filter(
                    alert_level=(
                        BloodStockAlert.AlertLevel.LOW
                    )
                )
                .exclude(
                    status=(
                        BloodStockAlert.AlertStatus.RESOLVED
                    )
                )
                .count()
            )

            active_zero_alerts = (
                alerts
                .filter(
                    alert_level=(
                        BloodStockAlert.AlertLevel.ZERO_STOCK
                    )
                )
                .exclude(
                    status=(
                        BloodStockAlert.AlertStatus.RESOLVED
                    )
                )
                .count()
            )

            facility_data.append(
                {
                    "facility_id": facility.id,
                    "facility_name": facility.name,

                    "total_inventory": total_inventory,
                    "total_available": total_available,

                    "stock_combinations": {
                        "total": len(combinations),
                        "normal": normal,
                        "low": low,
                        "critical": critical,
                        "zero_stock": zero_stock,
                    },

                    "alerts": {
                        "open": open_alerts,
                        "critical": active_critical_alerts,
                        "low": active_low_alerts,
                        "zero_stock": active_zero_alerts,
                    },

                    "shortage_score": shortage_score,
                    "shortage_status": shortage_status,

                    "stock_matrix": stock_matrix,
                }
            )

        # -------------------------------------------------
        # Rank facilities
        # -------------------------------------------------

        facility_data.sort(
            key=lambda item: (
                item["shortage_score"],
                -item["total_available"],
            ),
            reverse=True,
        )

        # Add ranking
        for index, facility in enumerate(
            facility_data,
            start=1,
        ):
            facility["rank"] = index

        # -------------------------------------------------
        # National summary
        # -------------------------------------------------

        total_facilities = len(facility_data)

        severe_facilities = sum(
            1
            for item in facility_data
            if item["shortage_status"] == "SEVERE"
        )

        critical_facilities = sum(
            1
            for item in facility_data
            if item["shortage_status"] == "CRITICAL"
        )

        low_facilities = sum(
            1
            for item in facility_data
            if item["shortage_status"] == "LOW"
        )

        normal_facilities = sum(
            1
            for item in facility_data
            if item["shortage_status"] == "NORMAL"
        )

        national_available = sum(
            item["total_available"]
            for item in facility_data
        )

        return Response(
            {
                "scope": "national",

                "summary": {
                    "facilities": total_facilities,
                    "national_available_units": (
                        national_available
                    ),

                    "severe_facilities": (
                        severe_facilities
                    ),

                    "critical_facilities": (
                        critical_facilities
                    ),

                    "low_stock_facilities": (
                        low_facilities
                    ),

                    "normal_facilities": (
                        normal_facilities
                    ),
                },

                "facility_comparison": facility_data,
            },

            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="transfer-opportunities",
    )
    def transfer_opportunities(self, request):

        user = request.user
        scope = get_user_scope(user)

        # -------------------------------------------------
        # NATIONAL ACCESS ONLY
        # -------------------------------------------------
        if scope != "national":
            return Response(
                {
                    "detail": (
                        "National transfer opportunity "
                        "access is restricted to national users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # -------------------------------------------------
        # GET ALL FACILITIES
        # -------------------------------------------------
        facilities = Facility.objects.all().order_by(
            "name"
        )

        # -------------------------------------------------
        # GET ALL BLOOD GROUP / COMPONENT COMBINATIONS
        # -------------------------------------------------
        combinations = (
            InventoryRecord.objects
            .values(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .distinct()
            .order_by(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
        )

        # -------------------------------------------------
        # STOCK DATA
        # -------------------------------------------------
        stock = (
            InventoryRecord.objects
            .filter(
                status=InventoryRecord.Status.AVAILABLE
            )
            .values(
                "facility_id",
                "facility__name",
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .annotate(
                units=Count("id")
            )
        )

        stock_map = {
            (
                item["facility_id"],
                item["blood_unit__blood_group"],
                item["blood_unit__component_type"],
            ): item["units"]
            for item in stock
        }

        # -------------------------------------------------
        # BUILD OPPORTUNITIES
        # -------------------------------------------------
        opportunities = []

        SURPLUS_THRESHOLD = 5
        CRITICAL_THRESHOLD = 2

        for combination in combinations:

            blood_group = combination[
                "blood_unit__blood_group"
            ]

            component_type = combination[
                "blood_unit__component_type"
            ]

            facility_stock = []

            for facility in facilities:

                units = stock_map.get(
                    (
                        facility.id,
                        blood_group,
                        component_type,
                    ),
                    0,
                )

                facility_stock.append(
                    {
                        "facility_id": facility.id,
                        "facility_name": facility.name,
                        "available_units": units,
                    }
                )

            # -------------------------------------------------
            # IDENTIFY SURPLUS FACILITIES
            # -------------------------------------------------
            surplus_facilities = [
                item
                for item in facility_stock
                if item["available_units"]
                > SURPLUS_THRESHOLD
            ]

            # -------------------------------------------------
            # IDENTIFY SHORTAGE FACILITIES
            # -------------------------------------------------
            shortage_facilities = [
                item
                for item in facility_stock
                if item["available_units"]
                <= SURPLUS_THRESHOLD
            ]

            # -------------------------------------------------
            # CREATE TRANSFER OPPORTUNITIES
            # -------------------------------------------------
            for destination in shortage_facilities:

                destination_units = destination[
                    "available_units"
                ]

                if destination_units == 0:
                    priority = "URGENT"

                elif destination_units <= CRITICAL_THRESHOLD:
                    priority = "HIGH"

                else:
                    priority = "NORMAL"

                for source in surplus_facilities:

                    source_units = source[
                        "available_units"
                    ]

                    # Keep at least the surplus threshold
                    # at the source facility.
                    transferable_units = (
                        source_units
                        - SURPLUS_THRESHOLD
                    )

                    if transferable_units <= 0:
                        continue

                    # Suggested quantity should restore
                    # destination stock to the surplus level.
                    required_units = (
                        SURPLUS_THRESHOLD
                        - destination_units
                    )

                    suggested_quantity = min(
                        transferable_units,
                        max(required_units, 1),
                    )

                    opportunities.append(
                        {
                            "blood_group": blood_group,
                            "component_type": component_type,

                            "source": {
                                "facility_id": (
                                    source["facility_id"]
                                ),
                                "facility_name": (
                                    source["facility_name"]
                                ),
                                "available_units": (
                                    source_units
                                ),
                            },

                            "destination": {
                                "facility_id": (
                                    destination[
                                        "facility_id"
                                    ]
                                ),
                                "facility_name": (
                                    destination[
                                        "facility_name"
                                    ]
                                ),
                                "available_units": (
                                    destination_units
                                ),
                            },

                            "suggested_quantity": (
                                suggested_quantity
                            ),

                            "priority": priority,
                        }
                    )

        # -------------------------------------------------
        # PRIORITY ORDER
        # -------------------------------------------------
        priority_order = {
            "URGENT": 0,
            "HIGH": 1,
            "NORMAL": 2,
        }

        opportunities.sort(
            key=lambda item: (
                priority_order.get(
                    item["priority"],
                    99,
                ),
                item["blood_group"],
                item["component_type"],
                item["destination"][
                    "facility_name"
                ],
                item["source"][
                    "facility_name"
                ],
            )
        )

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------
        summary = {
            "total_opportunities": len(
                opportunities
            ),

            "urgent": sum(
                1
                for item in opportunities
                if item["priority"] == "URGENT"
            ),

            "high": sum(
                1
                for item in opportunities
                if item["priority"] == "HIGH"
            ),

            "normal": sum(
                1
                for item in opportunities
                if item["priority"] == "NORMAL"
            ),
        }

        return Response(
            {
                "scope": "national",

                "summary": summary,

                "opportunities": opportunities,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="request-transfer-from-recommendation",
    )
    def request_transfer_from_recommendation(
        self,
        request,
    ):
        """
        Create transfer requests from a validated
        transfer recommendation.
        """

        user = request.user
        scope = get_user_scope(user)

        # -------------------------------------------------
        # REQUEST DATA
        # -------------------------------------------------

        source_facility_id = request.data.get(
            "source_facility_id"
        )

        destination_facility_id = request.data.get(
            "destination_facility_id"
        )

        blood_group = request.data.get(
            "blood_group"
        )

        component_type = request.data.get(
            "component_type"
        )

        requested_units = request.data.get(
            "requested_units"
        )

        reason = request.data.get(
            "reason",
            "",
        )

        notes = request.data.get(
            "notes",
            "",
        )

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        missing = []

        if not source_facility_id:
            missing.append(
                "source_facility_id"
            )

        if not destination_facility_id:
            missing.append(
                "destination_facility_id"
            )

        if not blood_group:
            missing.append(
                "blood_group"
            )

        if not component_type:
            missing.append(
                "component_type"
            )

        if requested_units in [
            None,
            "",
        ]:
            missing.append(
                "requested_units"
            )

        if missing:

            return Response(
                {
                    "detail": (
                        "Missing required fields."
                    ),
                    "required": missing,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # VALIDATE IDS
        # -------------------------------------------------

        try:

            source_facility_id = int(
                source_facility_id
            )

            destination_facility_id = int(
                destination_facility_id
            )

            requested_units = int(
                requested_units
            )

        except (
            TypeError,
            ValueError,
        ):

            return Response(
                {
                    "detail": (
                        "Facility IDs and requested_units "
                        "must be valid integers."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # SAME FACILITY PROTECTION
        # -------------------------------------------------

        if (
            source_facility_id
            == destination_facility_id
        ):

            return Response(
                {
                    "detail": (
                        "Source and destination facilities "
                        "must be different."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # FACILITY ACCESS CONTROL
        # -------------------------------------------------

        if scope != "national":

            if not user.facility_id:

                return Response(
                    {
                        "detail": (
                            "User is not assigned "
                            "to a facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if (
                source_facility_id
                != user.facility_id
            ):

                return Response(
                    {
                        "detail": (
                            "You can only request blood "
                            "from your own facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # -------------------------------------------------
        # CREATE REQUESTS
        # -------------------------------------------------

        try:

            transfers = (
                request_transfer_from_recommendation(
                    source_facility_id=(
                        source_facility_id
                    ),
                    destination_facility_id=(
                        destination_facility_id
                    ),
                    blood_group=blood_group,
                    component_type=component_type,
                    requested_units=requested_units,
                    requested_by=user,
                    reason=reason,
                    notes=notes,
                )
            )

        except ValidationError as exc:

            return Response(
                {
                    "detail": exc.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return Response(
            {
                "detail": (
                    "Transfer request created successfully."
                ),

                "count": len(transfers),

                "status": (
                    BloodTransfer.Status.REQUESTED
                ),

                "source_facility_id": (
                    source_facility_id
                ),

                "destination_facility_id": (
                    destination_facility_id
                ),

                "blood_group": blood_group,

                "component_type": component_type,

                "requested_units": requested_units,

                "transfers": [
                    {
                        "id": transfer.id,
                        "transfer_id": (
                            transfer.transfer_id
                        ),
                        "blood_unit_id": (
                            transfer.blood_unit_id
                        ),
                        "status": transfer.status,
                    }
                    for transfer in transfers
                ],
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="national-heatmap",
    )
    def national_heatmap(self, request):

        user = request.user
        scope = get_user_scope(user)

        # -------------------------------------------------
        # NATIONAL ACCESS ONLY
        # -------------------------------------------------
        if scope != "national":
            return Response(
                {
                    "detail": (
                        "National inventory access "
                        "is restricted to national users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # -------------------------------------------------
        # GET ALL FACILITIES
        # -------------------------------------------------
        facilities = (
            Facility.objects
            .all()
            .order_by("name")
        )

        # -------------------------------------------------
        # GET ALL BLOOD GROUP / COMPONENT COMBINATIONS
        # -------------------------------------------------
        combinations = (
            InventoryRecord.objects
            .values(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .distinct()
            .order_by(
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
        )

        combinations = [
            {
                "blood_group": item[
                    "blood_unit__blood_group"
                ],
                "component_type": item[
                    "blood_unit__component_type"
                ],
            }
            for item in combinations
        ]

        # -------------------------------------------------
        # AVAILABLE STOCK
        # -------------------------------------------------
        stock = (
            InventoryRecord.objects
            .filter(
                status=InventoryRecord.Status.AVAILABLE
            )
            .values(
                "facility_id",
                "blood_unit__blood_group",
                "blood_unit__component_type",
            )
            .annotate(
                units=Count("id")
            )
        )

        # -------------------------------------------------
        # CREATE FAST LOOKUP MAP
        # -------------------------------------------------
        stock_map = {
            (
                item["facility_id"],
                item["blood_unit__blood_group"],
                item["blood_unit__component_type"],
            ): item["units"]
            for item in stock
        }

        # -------------------------------------------------
        # BUILD HEATMAP
        # -------------------------------------------------
        heatmap = []

        for facility in facilities:

            facility_rows = []

            for combination in combinations:

                blood_group = combination["blood_group"]
                component_type = combination[
                    "component_type"
                ]

                units = stock_map.get(
                    (
                        facility.id,
                        blood_group,
                        component_type,
                    ),
                    0,
                )

                # -----------------------------------------
                # AVAILABILITY LEVEL
                # -----------------------------------------
                if units == 0:
                    availability = "ZERO"

                elif units <= 2:
                    availability = "CRITICAL"

                elif units <= 5:
                    availability = "LOW"

                else:
                    availability = "NORMAL"

                facility_rows.append(
                    {
                        "blood_group": blood_group,
                        "component_type": component_type,
                        "units": units,
                        "availability": availability,
                    }
                )

            heatmap.append(
                {
                    "facility_id": facility.id,
                    "facility_name": facility.name,
                    "stock": facility_rows,
                }
            )

        # -------------------------------------------------
        # NATIONAL TOTALS BY BLOOD GROUP / COMPONENT
        # -------------------------------------------------
        national_matrix = []

        for combination in combinations:

            blood_group = combination["blood_group"]
            component_type = combination[
                "component_type"
            ]

            total_units = sum(
                stock_map.get(
                    (
                        facility.id,
                        blood_group,
                        component_type,
                    ),
                    0,
                )
                for facility in facilities
            )

            if total_units == 0:
                availability = "ZERO"

            elif total_units <= 2:
                availability = "CRITICAL"

            elif total_units <= 5:
                availability = "LOW"

            else:
                availability = "NORMAL"

            national_matrix.append(
                {
                    "blood_group": blood_group,
                    "component_type": component_type,
                    "units": total_units,
                    "availability": availability,
                }
            )

        return Response(
            {
                "scope": "national",

                "thresholds": {
                    "zero": 0,
                    "critical": 2,
                    "low": 5,
                },

                "facilities": heatmap,

                "national_matrix": national_matrix,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="stock-alerts",
    )
    def stock_alerts(self, request):

        user = request.user
        scope = get_user_scope(user)

        low_threshold = request.query_params.get(
            "low_threshold",
            10,
        )

        critical_threshold = request.query_params.get(
            "critical_threshold",
            3,
        )

        try:
            low_threshold = int(low_threshold)
            critical_threshold = int(
                critical_threshold
            )

        except (TypeError, ValueError):
            return Response(
                {
                    "detail": (
                        "Thresholds must be "
                        "whole numbers."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if low_threshold < 0:
            return Response(
                {
                    "detail": (
                        "low_threshold cannot "
                        "be negative."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if critical_threshold < 0:
            return Response(
                {
                    "detail": (
                        "critical_threshold cannot "
                        "be negative."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if critical_threshold > low_threshold:
            return Response(
                {
                    "detail": (
                        "critical_threshold cannot "
                        "be greater than "
                        "low_threshold."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        facility = None

        if scope != "national":

            if not user.facility_id:
                return Response(
                    {
                        "detail": (
                            "User is not assigned "
                            "to a facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            facility = user.facility

        alerts = get_stock_alerts(
            low_threshold=low_threshold,
            critical_threshold=critical_threshold,
            facility=facility,
        )

        critical = [
            alert
            for alert in alerts
            if alert["severity"] == "CRITICAL"
        ]

        low = [
            alert
            for alert in alerts
            if alert["severity"] == "LOW"
        ]

        adequate = [
            alert
            for alert in alerts
            if alert["severity"] == "ADEQUATE"
        ]

        return Response(
            {
                "thresholds": {
                    "low": low_threshold,
                    "critical": critical_threshold,
                },
                "summary": {
                    "total_alerts": (
                        len(critical) + len(low)
                    ),
                    "critical": len(critical),
                    "low": len(low),
                    "adequate": len(adequate),
                },
                "alerts": alerts,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="traceability",
    )
    def traceability(self, request, pk=None):
        inventory = (
            self.get_queryset()
            .select_related(
                "blood_unit",
                "facility",
                "storage_location",
            )
            .prefetch_related(
                "movements__created_by",
                "movements__from_location",
                "movements__to_location",
                "reservations__created_by",
                "issues__issued_by",
            )
            .filter(pk=pk)
            .first()
        )

        if inventory is None:
            return Response(
                {"detail": "Inventory record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        blood_unit = inventory.blood_unit

        events = []

        # Inventory received event
        events.append({
            "event_type": "RECEIVED",
            "date": inventory.received_at,
            "facility": inventory.facility.name,
            "storage_location": inventory.storage_location.name,
            "user": None,
            "reason": "Blood unit received into inventory.",
        })

        # Inventory movement history
        for movement in inventory.movements.all().order_by("created_at"):
            events.append({
                "event_type": movement.movement_type,
                "date": movement.created_at,
                "facility": (
                    movement.to_location.facility.name
                    if movement.to_location
                    else (
                        movement.from_location.facility.name
                        if movement.from_location
                        else inventory.facility.name
                    )
                ),
                "storage_location": (
                    movement.to_location.name
                    if movement.to_location
                    else (
                        movement.from_location.name
                        if movement.from_location
                        else None
                    )
                ),
                "user": (
                    movement.created_by.get_full_name()
                    or movement.created_by.username
                    if movement.created_by
                    else None
                ),
                "reason": movement.reason,
            })

        # Reservation history
        for reservation in inventory.reservations.all().order_by(
            "reserved_at"
        ):
            events.append({
                "event_type": f"RESERVATION_{reservation.status}",
                "date": reservation.reserved_at,
                "facility": reservation.facility.name,
                "storage_location": inventory.storage_location.name,
                "user": (
                    reservation.created_by.get_full_name()
                    or reservation.created_by.username
                    if reservation.created_by
                    else None
                ),
                "reason": reservation.notes,
            })

        # Issue history
        for issue in inventory.issues.all().order_by("issued_at"):
            events.append({
                "event_type": f"ISSUE_{issue.status}",
                "date": issue.issued_at,
                "facility": issue.facility.name,
                "storage_location": inventory.storage_location.name,
                "user": (
                    issue.issued_by.get_full_name()
                    or issue.issued_by.username
                    if issue.issued_by
                    else None
                ),
                "reason": issue.notes,
                "patient_reference": issue.patient_reference,
                "clinical_reference": issue.clinical_reference,
            })

        # Sort complete timeline chronologically
        events.sort(
            key=lambda event: event["date"]
        )

        data = {
            "inventory_id": inventory.inventory_id,
            "unit_id": blood_unit.unit_id,
            "blood_group": blood_unit.blood_group,
            "component_type": blood_unit.component_type,
            "barcode": blood_unit.barcode,
            "current_facility": inventory.facility.name,
            "current_storage_location": inventory.storage_location.name,
            "current_status": inventory.status,
            "events": events,
        }

        serializer = InventoryTraceabilitySerializer(data)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class BloodReservationViewSet(
    InventoryScopedMixin,
    viewsets.ReadOnlyModelViewSet,
):

    queryset = BloodReservation.objects.select_related(
        "inventory",
        "facility",
        "created_by",
    ).all()

    serializer_class = BloodReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.scoped_queryset(
            super().get_queryset()
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="create",
    )
    def create_reservation(
        self,
        request,
    ):

        user = request.user

        if not user.facility_id:
            return Response(
                {
                    "detail": (
                        "User is not assigned "
                        "to a facility."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        inventory_id = request.data.get(
            "inventory"
        )

        if not inventory_id:
            return Response(
                {
                    "detail": (
                        "inventory is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation = reserve_blood(
            inventory_id=inventory_id,
            facility=user.facility,
            created_by=user,
            patient_reference=request.data.get(
                "patient_reference",
                "",
            ),
            blood_group=request.data.get(
                "blood_group",
                "",
            ),
            expires_at=request.data.get(
                "expires_at"
            ),
            notes=request.data.get(
                "notes",
                "",
            ),
        )

        return Response(
            {
                "reservation_id": (
                    reservation.reservation_id
                ),
                "status": reservation.status,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="release",
    )
    def release(self, request, pk=None):

        reservation = self.get_object()

        inventory = release_reservation(
            reservation_id=reservation.pk,
            released_by=request.user,
        )

        serializer = InventoryRecordSerializer(
            inventory
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class BloodIssueViewSet(
    InventoryScopedMixin,
    viewsets.ModelViewSet,
):

    queryset = BloodIssue.objects.select_related(
        "inventory",
        "inventory__blood_unit",
        "inventory__storage_location",
        "facility",
        "issued_by",
    ).all()

    serializer_class = BloodIssueSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "head",
        "options",
    ]

    def get_queryset(self):
        return self.scoped_queryset(
            super().get_queryset()
        )

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = request.user

        if not user.facility_id:
            from rest_framework.exceptions import (
                PermissionDenied
            )

            raise PermissionDenied(
                "User is not assigned to a facility."
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        issue = issue_blood(
            inventory_id=serializer.validated_data[
                "inventory"
            ].pk,
            facility=user.facility,
            issued_by=user,
            patient_reference=serializer.validated_data.get(
                "patient_reference",
                "",
            ),
            clinical_reference=serializer.validated_data.get(
                "clinical_reference",
                "",
            ),
            notes=serializer.validated_data.get(
                "notes",
                "",
            ),
        )

        output_serializer = self.get_serializer(
            issue
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="return",
    )
    def return_blood_unit(
        self,
        request,
        pk=None,
    ):

        issue = self.get_object()

        inventory = return_blood(
            issue_id=issue.pk,
            returned_by=request.user,
            reason=request.data.get(
                "reason",
                "",
            ),
        )

        serializer = InventoryRecordSerializer(
            inventory
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="transfuse",
    )
    def transfuse(
        self,
        request,
        pk=None,
    ):

        issue = self.get_object()

        result = mark_transfused(
            issue_id=issue.pk,
            recorded_by=request.user,
            notes=request.data.get(
                "notes",
                "",
            ),
        )

        serializer = self.get_serializer(
            result
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class BloodTransferViewSet(
    InventoryScopedMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = BloodTransfer.objects.select_related(
        "blood_unit",
        "from_facility",
        "to_facility",
        "requested_by",
        "approved_by",
        "rejected_by",
        "dispatched_by",
        "received_by",
    ).all()

    serializer_class = BloodTransferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        user = self.request.user
        scope = get_user_scope(user)

        if scope == "national":
            pass
        else:
            if not user.facility_id:
                return queryset.none()

            queryset = queryset.filter(
                Q(
                    from_facility_id=user.facility_id
                )
                |
                Q(
                    to_facility_id=user.facility_id
                )
            )

        params = self.request.query_params

        transfer_status = params.get("status")
        source = params.get("from_facility")
        destination = params.get("to_facility")
        blood_group = params.get("blood_group")
        component = params.get("component_type")

        if transfer_status:
            queryset = queryset.filter(
                status=transfer_status
            )

        if source:
            queryset = queryset.filter(
                from_facility_id=source
            )

        if destination:
            queryset = queryset.filter(
                to_facility_id=destination
            )

        if blood_group:
            queryset = queryset.filter(
                blood_unit__blood_group=blood_group
            )

        if component:
            queryset = queryset.filter(
                blood_unit__component_type=component
            )

        return queryset.order_by(
            "-requested_at"
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="dashboard",
    )
    def dashboard(self, request):

        queryset = self.get_queryset()

        now = timezone.now()

        requested = queryset.filter(
            status=BloodTransfer.Status.REQUESTED
        ).count()

        approved = queryset.filter(
            status=BloodTransfer.Status.APPROVED
        ).count()

        dispatched = queryset.filter(
            status=BloodTransfer.Status.DISPATCHED
        ).count()

        received = queryset.filter(
            status=BloodTransfer.Status.RECEIVED
        ).count()

        cancelled = queryset.filter(
            status=BloodTransfer.Status.CANCELLED
        ).count()

        aging_threshold = now - timedelta(hours=24)

        aging = queryset.filter(
            status__in=[
                BloodTransfer.Status.REQUESTED,
                BloodTransfer.Status.APPROVED,
                BloodTransfer.Status.DISPATCHED,
            ]
        ).filter(
            requested_at__lte=aging_threshold
        ).count()

        return Response(
            {
                "summary": {
                    "requested": requested,
                    "approved": approved,
                    "dispatched": dispatched,
                    "in_transit": dispatched,
                    "received": received,
                    "cancelled": cancelled,
                    "aging": aging,
                },
                "status_distribution": {
                    "requested": requested,
                    "approved": approved,
                    "dispatched": dispatched,
                    "received": received,
                    "cancelled": cancelled,
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="request",
    )
    def request_transfer_action(self, request):
        user = request.user

        if not user.facility_id:
            return Response(
                {
                    "detail": (
                        "User is not assigned "
                        "to a facility."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        inventory_id = request.data.get("inventory")

        destination_facility_id = request.data.get(
            "destination_facility"
        )

        if not inventory_id:
            return Response(
                {
                    "detail": "inventory is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not destination_facility_id:
            return Response(
                {
                    "detail": (
                        "destination_facility "
                        "is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            destination_facility = Facility.objects.get(
                pk=destination_facility_id
            )

            transfer = request_transfer(
                inventory_id=inventory_id,
                destination_facility=destination_facility,
                requested_by=user,
                reason=request.data.get(
                    "reason",
                    "",
                ),
                notes=request.data.get(
                    "notes",
                    "",
                ),
            )

        except Facility.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Destination facility "
                        "does not exist."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transfer_requested_notification(transfer)

        serializer = self.get_serializer(
            transfer
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
    )
    def approve(self, request, pk=None):

        transfer = self.get_object()

        user = request.user
        scope = get_user_scope(user)

        if scope != "national":
            return Response(
                {
                    "detail": (
                        "Only national users can approve "
                        "blood transfers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            transfer = approve_transfer(
                transfer_id=transfer.id,
                approved_by=user,
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc.detail)
                    if hasattr(exc, "detail")
                    else str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transfer_approved_notification(transfer)

        return Response(
            {
                "detail": "Transfer approved successfully.",
                "transfer_id": transfer.transfer_id,
                "status": transfer.status,
                "approved_by": user.id,
                "approved_at": transfer.approved_at,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
    )
    def reject(self, request, pk=None):

        transfer = self.get_object()

        user = request.user
        scope = get_user_scope(user)

        if scope != "national":
            return Response(
                {
                    "detail": (
                        "Only national users can reject "
                        "blood transfers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        reason = request.data.get(
            "reason",
            "",
        ).strip()

        if not reason:
            return Response(
                {
                    "detail": (
                        "A rejection reason is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transfer = reject_transfer(
                transfer_id=transfer.id,
                rejected_by=user,
                reason=reason,
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc.detail)
                    if hasattr(exc, "detail")
                    else str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transfer_dispatched_notification(transfer)

        return Response(
            {
                "detail": "Transfer rejected successfully.",
                "transfer_id": transfer.transfer_id,
                "status": transfer.status,
                "rejected_by": user.id,
                "rejected_at": transfer.rejected_at,
                "rejection_reason": (
                    transfer.rejection_reason
                ),
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="dispatch",
    )
    def dispatch(self, request, pk=None):

        transfer = self.get_object()

        user = request.user
        scope = get_user_scope(user)

        if scope != "national":
            return Response(
                {
                    "detail": (
                        "Only national users can dispatch "
                        "blood transfers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            transfer = dispatch_transfer(
                transfer_id=transfer.id,
                dispatched_by=user,
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": (
                        str(exc.detail)
                        if hasattr(exc, "detail")
                        else str(exc)
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Blood transfer dispatched successfully."
                ),
                "transfer_id": transfer.transfer_id,
                "status": transfer.status,
                "from_facility": (
                    transfer.from_facility.name
                ),
                "to_facility": (
                    transfer.to_facility.name
                ),
                "blood_group": (
                    transfer.blood_unit.blood_group
                ),
                "component_type": (
                    transfer.blood_unit.component_type
                ),
                "dispatched_at": transfer.dispatched_at,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="receive",
    )
    def receive(self, request, pk=None):

        storage_location_id = request.data.get(
            "storage_location"
        )

        if not storage_location_id:
            return Response(
                {
                    "detail": (
                        "storage_location "
                        "is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            storage_location = (
                StorageLocation.objects.get(
                    pk=storage_location_id
                )
            )

        except StorageLocation.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Storage location "
                        "does not exist."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            transfer = receive_transfer(
                transfer_id=pk,
                received_by=request.user,
                storage_location=storage_location,
            )

        except BloodTransfer.DoesNotExist:
            return Response(
                {
                    "detail": "Transfer not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transfer_received_notification(transfer)

        return Response(
            self.get_serializer(
                transfer
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="history",
    )
    def history(self, request, pk=None):

        transfer = self.get_object()

        inventory = (
            InventoryRecord.objects
            .select_related(
                "blood_unit",
                "facility",
                "storage_location",
            )
            .get(
                blood_unit=transfer.blood_unit
            )
        )

        movements = (
            InventoryMovement.objects
            .filter(inventory=inventory)
            .select_related(
                "created_by",
                "from_location",
                "to_location",
            )
            .order_by("created_at")
        )

        timeline = []

        timeline.append(
            {
                "event": "REQUESTED",
                "timestamp": transfer.requested_at,
                "user": (
                    transfer.requested_by.id
                    if transfer.requested_by
                    else None
                ),
            }
        )

        if transfer.approved_at:
            timeline.append(
                {
                    "event": "APPROVED",
                    "timestamp": transfer.approved_at,
                    "user": (
                        transfer.approved_by.id
                        if transfer.approved_by
                        else None
                    ),
                }
            )

        if transfer.rejected_at:
            timeline.append(
                {
                    "event": "REJECTED",
                    "timestamp": transfer.rejected_at,
                    "user": (
                        transfer.rejected_by.id
                        if transfer.rejected_by
                        else None
                    ),
                    "reason": transfer.rejection_reason,
                }
            )

        if transfer.dispatched_at:
            timeline.append(
                {
                    "event": "DISPATCHED",
                    "timestamp": transfer.dispatched_at,
                    "user": (
                        transfer.dispatched_by.id
                        if transfer.dispatched_by
                        else None
                    ),
                }
            )

        if transfer.received_at:
            timeline.append(
                {
                    "event": "RECEIVED",
                    "timestamp": transfer.received_at,
                    "user": (
                        transfer.received_by.id
                        if transfer.received_by
                        else None
                    ),
                }
            )

        return Response(
            {
                "transfer": {
                    "transfer_id": transfer.transfer_id,
                    "status": transfer.status,
                    "blood_unit": transfer.blood_unit.unit_id,
                    "blood_group": transfer.blood_unit.blood_group,
                    "component_type": (
                        transfer.blood_unit.component_type
                    ),
                    "from_facility": (
                        transfer.from_facility.name
                    ),
                    "to_facility": (
                        transfer.to_facility.name
                    ),
                },
                "timeline": timeline,
                "inventory_movements": [
                    {
                        "movement_type": movement.movement_type,
                        "reason": movement.reason,
                        "timestamp": movement.created_at,
                        "created_by": (
                            movement.created_by.id
                            if movement.created_by
                            else None
                        ),
                        "from_location": (
                            movement.from_location.name
                            if movement.from_location
                            else None
                        ),
                        "to_location": (
                            movement.to_location.name
                            if movement.to_location
                            else None
                        ),
                    }
                    for movement in movements
                ],
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="national-logistics",
    )
    def national_logistics(self, request):

        user = request.user

        if get_user_scope(user) != "national":
            return Response(
                {
                    "detail": (
                        "National logistics access "
                        "is restricted to national users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        transfers = self.get_queryset()

        now = timezone.now()

        requested = transfers.filter(
            status=BloodTransfer.Status.REQUESTED
        )

        approved = transfers.filter(
            status=BloodTransfer.Status.APPROVED
        )

        in_transit = transfers.filter(
            status=BloodTransfer.Status.DISPATCHED
        )

        received = transfers.filter(
            status=BloodTransfer.Status.RECEIVED
        )

        cancelled = transfers.filter(
            status=BloodTransfer.Status.CANCELLED
        )

        aging = transfers.filter(
            status__in=[
                BloodTransfer.Status.REQUESTED,
                BloodTransfer.Status.APPROVED,
                BloodTransfer.Status.DISPATCHED,
            ],
            requested_at__lte=(
                now - timedelta(hours=24)
            ),
        )

        return Response(
            {
                "summary": {
                    "total_transfers": transfers.count(),
                    "requested": requested.count(),
                    "approved": approved.count(),
                    "in_transit": in_transit.count(),
                    "received": received.count(),
                    "cancelled": cancelled.count(),
                    "aging": aging.count(),
                },
                "in_transit": [
                    {
                        "transfer_id": transfer.transfer_id,
                        "blood_unit": (
                            transfer.blood_unit.unit_id
                        ),
                        "blood_group": (
                            transfer.blood_unit.blood_group
                        ),
                        "component_type": (
                            transfer.blood_unit.component_type
                        ),
                        "from_facility": (
                            transfer.from_facility.name
                        ),
                        "to_facility": (
                            transfer.to_facility.name
                        ),
                        "dispatched_at": (
                            transfer.dispatched_at
                        ),
                    }
                    for transfer in in_transit
                ],
                "aging_transfers": [
                    {
                        "transfer_id": transfer.transfer_id,
                        "status": transfer.status,
                        "from_facility": (
                            transfer.from_facility.name
                        ),
                        "to_facility": (
                            transfer.to_facility.name
                        ),
                        "blood_group": (
                            transfer.blood_unit.blood_group
                        ),
                        "component_type": (
                            transfer.blood_unit.component_type
                        ),
                        "requested_at": (
                            transfer.requested_at
                        ),
                        "age_hours": round(
                            (
                                now -
                                transfer.requested_at
                            ).total_seconds()
                            / 3600,
                            1,
                        ),
                    }
                    for transfer in aging
                ],
            },
            status=status.HTTP_200_OK,
        )

class InventoryMovementViewSet(
    viewsets.ModelViewSet,
):

    queryset = InventoryMovement.objects.select_related(
        "inventory",
        "inventory__facility",
        "from_location",
        "to_location",
        "created_by",
    ).all()

    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        queryset = super().get_queryset()
        user = self.request.user
        scope = get_user_scope(user)

        if scope == "national":
            return queryset

        if not user.facility_id:
            return queryset.none()

        return queryset.filter(
            inventory__facility_id=user.facility_id
        )

    def perform_create(self, serializer):

        serializer.save(
            created_by=self.request.user
        )

class InventoryShortageViewSet(
    viewsets.ViewSet,
):
    """
    National inventory shortage and zero-stock APIs.
    """

    permission_classes = [IsAuthenticated]

    @action(
        detail=False,
        methods=["get"],
        url_path="zero-stock",
    )
    def zero_stock(self, request):
        """
        Return blood groups/components with
        zero available stock at each facility.
        """

        user = request.user
        scope = get_user_scope(user)

        data = get_zero_stock_by_facility()

        # Non-national users should only see
        # their own facility.
        if scope != "national":

            if not user.facility_id:
                return Response(
                    {
                        "detail": (
                            "User is not assigned "
                            "to a facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            data = [
                item
                for item in data
                if item["facility_id"]
                == user.facility_id
            ]

        return Response(
            data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="shortage-ranking",
    )
    def shortage_ranking(self, request):
        """
        Return facilities ranked according
        to blood-stock shortage severity.
        """

        user = request.user
        scope = get_user_scope(user)

        data = get_facility_shortage_ranking()

        # National users can see all facilities.
        if scope == "national":
            return Response(
                data,
                status=status.HTTP_200_OK,
            )

        # Facility users only see their own facility.
        if not user.facility_id:
            return Response(
                {
                    "detail": (
                        "User is not assigned "
                        "to a facility."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        data = [
            item
            for item in data
            if item["facility_id"]
            == user.facility_id
        ]

        return Response(
            data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="shortage-alerts",
    )
    def shortage_alerts(self, request):
        """
        Return automatically generated stock
        shortage alerts.
        """

        user = request.user
        scope = get_user_scope(user)

        alerts = generate_shortage_alerts()

        if scope != "national":

            if not user.facility_id:
                return Response(
                    {
                        "detail": (
                            "User is not assigned "
                            "to a facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            alerts = [
                alert
                for alert in alerts
                if alert["facility_id"]
                == user.facility_id
            ]

        return Response(
            alerts,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="alert-summary",
    )
    def alert_summary(self, request):
        """
        Return summary counts of shortage alerts.
        """

        user = request.user
        scope = get_user_scope(user)

        alerts = generate_shortage_alerts()

        if scope != "national":

            if not user.facility_id:
                return Response(
                    {
                        "detail": (
                            "User is not assigned "
                            "to a facility."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            alerts = [
                alert
                for alert in alerts
                if alert["facility_id"]
                == user.facility_id
            ]

        summary = {
            "total_alerts": len(alerts),

            "zero_stock": sum(
                1
                for alert in alerts
                if alert["alert_level"]
                == "ZERO_STOCK"
            ),

            "critical": sum(
                1
                for alert in alerts
                if alert["alert_level"]
                == "CRITICAL"
            ),

            "low": sum(
                1
                for alert in alerts
                if alert["alert_level"]
                == "LOW"
            ),
        }

        return Response(
            summary,
            status=status.HTTP_200_OK,
        )

class BloodStockAlertViewSet(
    InventoryScopedMixin,
    viewsets.ReadOnlyModelViewSet,
):

    queryset = (
        BloodStockAlert.objects
        .select_related(
            "facility",
            "acknowledged_by",
            "resolved_by",
        )
        .all()
        .order_by("-created_at")
    )

    serializer_class = BloodStockAlertSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        queryset = super().get_queryset()

        user = self.request.user
        scope = get_user_scope(user)

        if scope == "national":
            return queryset

        if not user.facility_id:
            return queryset.none()

        return queryset.filter(
            facility_id=user.facility_id
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="acknowledge",
    )
    def acknowledge(self, request, pk=None):

        alert = self.get_object()

        if (
            alert.status
            == BloodStockAlert.AlertStatus.RESOLVED
        ):
            return Response(
                {
                    "detail": (
                        "Resolved alerts cannot "
                        "be acknowledged."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        alert.status = (
            BloodStockAlert.AlertStatus.ACKNOWLEDGED
        )

        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user

        alert.save()

        return Response(
            self.get_serializer(alert).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="resolve",
    )
    def resolve(self, request, pk=None):

        alert = self.get_object()

        if (
            alert.status
            == BloodStockAlert.AlertStatus.RESOLVED
        ):
            return Response(
                {
                    "detail": (
                        "Alert is already resolved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        alert.status = (
            BloodStockAlert.AlertStatus.RESOLVED
        )

        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user

        alert.resolution_notes = request.data.get(
            "resolution_notes",
            "",
        )

        alert.save()

        return Response(
            self.get_serializer(alert).data,
            status=status.HTTP_200_OK,
        )

class BloodRequestViewSet(
    InventoryScopedMixin,
    viewsets.ModelViewSet,
):

    queryset = BloodRequest.objects.select_related(
        "facility",
        "requested_by",
        "reviewed_by",
    ).all()

    serializer_class = BloodRequestSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "head",
        "options",
    ]

    def get_queryset(self):

        queryset = self.scoped_queryset(
            super().get_queryset()
        )

        status_filter = self.request.query_params.get(
            "status"
        )

        priority = self.request.query_params.get(
            "priority"
        )

        blood_group = self.request.query_params.get(
            "blood_group"
        )

        component_type = self.request.query_params.get(
            "component_type"
        )

        facility = self.request.query_params.get(
            "facility"
        )

        if status_filter:
            queryset = queryset.filter(
                status=status_filter
            )

        if priority:
            queryset = queryset.filter(
                priority=priority
            )

        if blood_group:
            queryset = queryset.filter(
                blood_group__iexact=blood_group
            )

        if component_type:
            queryset = queryset.filter(
                component_type__iexact=component_type
            )

        if facility:
            queryset = queryset.filter(
                facility_id=facility
            )

        return queryset.order_by(
            "-created_at"
        )

    def perform_create(self, serializer):

        user = self.request.user

        if not user.facility_id:
            raise PermissionDenied(
                "User is not assigned to a facility."
            )

        serializer.save(
            facility=user.facility,
            requested_by=user,
            status=BloodRequest.Status.PENDING,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="review",
    )
    def review(
        self,
        request,
        pk=None,
    ):

        blood_request = self.get_object()

        if blood_request.status != (
            BloodRequest.Status.PENDING
        ):
            return Response(
                {
                    "detail": (
                        "Only pending blood requests "
                        "can be reviewed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        blood_request.status = (
            BloodRequest.Status.REVIEWED
        )

        blood_request.reviewed_by = request.user
        blood_request.reviewed_at = timezone.now()

        blood_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

        return Response(
            BloodRequestSerializer(
                blood_request
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="fulfillment",
    )
    def fulfillment(
        self,
        request,
        pk=None,
    ):

        from inventory.services.clinical import (
            get_request_fulfillment,
        )

        blood_request = self.get_object()

        result = get_request_fulfillment(
            blood_request
        )

        result["units"] = [
            {
                "inventory_id": (
                    inventory.inventory_id
                ),
                "unit_id": (
                    inventory.blood_unit.unit_id
                ),
                "blood_group": (
                    inventory.blood_unit.blood_group
                ),
                "component_type": (
                    inventory.blood_unit.component_type
                ),
                "expiry_date": (
                    inventory.blood_unit.expiry_date
                ),
                "storage_location": (
                    inventory.storage_location.name
                ),
            }
            for inventory in result["units"]
        ]

        return Response(
            result,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
    )
    def reject(
        self,
        request,
        pk=None,
    ):

        blood_request = self.get_object()

        if blood_request.status not in [
            BloodRequest.Status.PENDING,
            BloodRequest.Status.REVIEWED,
        ]:
            return Response(
                {
                    "detail": (
                        "This blood request "
                        "cannot be rejected."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get(
            "reason",
            "",
        )

        if not reason:
            return Response(
                {
                    "detail": (
                        "A rejection reason is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        blood_request.status = (
            BloodRequest.Status.REJECTED
        )

        blood_request.reviewed_by = request.user
        blood_request.reviewed_at = timezone.now()
        blood_request.notes = (
            f"{blood_request.notes}\n"
            f"Rejection reason: {reason}"
        ).strip()

        blood_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "notes",
                "updated_at",
            ]
        )

        return Response(
            BloodRequestSerializer(
                blood_request
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
    )
    def cancel(
        self,
        request,
        pk=None,
    ):

        blood_request = self.get_object()

        if blood_request.status in [
            BloodRequest.Status.FULFILLED,
            BloodRequest.Status.CANCELLED,
            BloodRequest.Status.REJECTED,
        ]:
            return Response(
                {
                    "detail": (
                        "This blood request "
                        "cannot be cancelled."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        blood_request.status = (
            BloodRequest.Status.CANCELLED
        )

        blood_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            BloodRequestSerializer(
                blood_request
            ).data,
            status=status.HTTP_200_OK,
        )