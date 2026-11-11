import uuid

from django.db import models
from django.conf import settings


class Tenant(models.Model):

    class GSTStatus(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        UNREGISTERED = "UNREGISTERED", "Unregistered"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(max_length=150)

    slug = models.SlugField(unique=True)

    gst_status = models.CharField(
        max_length=20,
        choices=GSTStatus.choices,
        default=GSTStatus.UNREGISTERED
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TenantMembership(models.Model):

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        MANAGER = "MANAGER", "Manager"
        CASHIER = "CASHIER", "Cashier"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CASHIER
    )

    is_active = models.BooleanField(default=True)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "user"],
                name="unique_tenant_membership"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.tenant}"


class Store(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="stores"
    )

    name = models.CharField(max_length=150)

    address = models.TextField(blank=True)

    phone = models.CharField(max_length=15, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_store_name_per_tenant"
            )
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"