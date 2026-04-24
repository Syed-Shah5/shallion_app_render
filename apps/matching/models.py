from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Match(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUGGESTED', 'Client Sent Request'),
        ('ACCEPTED', 'Both Accepted'),
        ('REJECTED', 'Rejected'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
    ]

    client = models.ForeignKey(
        'client.ClientProfile',
        on_delete=models.CASCADE,
        related_name='matches_as_client',
    )
    volunteer = models.ForeignKey(
        'volunteer.VolunteerProfile',
        on_delete=models.CASCADE,
        related_name='matches_as_volunteer',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    compatibility_score = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    matching_notes = models.TextField(blank=True)

    client_accepted = models.BooleanField(default=False)
    client_accepted_at = models.DateTimeField(null=True, blank=True)

    volunteer_accepted = models.BooleanField(default=False)
    volunteer_accepted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'volunteer')
        ordering = ['-compatibility_score', '-created_at']

    def __str__(self):
        return f"{self.client.full_name} ↔ {self.volunteer.full_name}"

    # Client sends request (PENDING -> SUGGESTED)
    def send_request_to_volunteer(self):
        self.client_accepted = True
        self.client_accepted_at = timezone.now()
        self.status = 'SUGGESTED'
        self.save()

    # Volunteer accepts request (SUGGESTED -> ACCEPTED)
    def accept_by_volunteer(self):
        self.volunteer_accepted = True
        self.volunteer_accepted_at = timezone.now()
        self.status = 'ACCEPTED'
        self.save()

    # Either party rejects
    def reject(self):
        self.status = 'REJECTED'
        self.save()

    # Update match status based on client and volunteer acceptance
    def update_status(self):
        if self.client_accepted and self.volunteer_accepted:
            self.status = 'ACCEPTED'  # Both have accepted
        elif self.status == 'PENDING':
            pass  # Stay PENDING until client sends request
        elif self.status == 'SUGGESTED' and not self.volunteer_accepted:
            pass  # Stay SUGGESTED - waiting for volunteer response
