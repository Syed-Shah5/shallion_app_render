from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# Client profile model to store personal information 
class ClientProfile(models.Model):
       
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    forename = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=17)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    
    latitude = models.FloatField(null=True, blank=True, help_text="Latitude from postcode")
    longitude = models.FloatField(null=True, blank=True, help_text="Longitude from postcode")
    coordinates_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=17)
    emergency_contact_relationship = models.CharField(max_length=50)
    
    # Profile photo
    profile_photo = models.ImageField(upload_to='client_photos/', blank=True, null=True)
    
    # Additional info
    additional_notes = models.TextField(blank=True, help_text="Any additional information volunteers should know")
    profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['surname', 'forename']
    
    def __str__(self):
        return f"{self.forename} {self.surname}"
    
    @property
    def full_name(self):
        return f"{self.forename} {self.surname}"
    
    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

# Client preferences model to store matching criteria for volunteers
class ClientPreferences(models.Model):
    """Client's preferences for volunteer matching"""
    
    LANGUAGES = [
        ('EN', 'English'),
        ('ES', 'Spanish'),
        ('FR', 'French'),
        ('DE', 'German'),
        ('ZH', 'Chinese'),
        ('AR', 'Arabic'),
        ('HI', 'Hindi'),
        ('RU', 'Russian'),
        ('PT', 'Portuguese'),
        ('OTHER', 'Other'),
    ]
    
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    
    TIME_CHOICES = [
        ('MORNING', 'Morning (8:00 - 11:00)'),
        ('MIDDAY', 'Midday (11:00 - 14:00)'),
        ('AFTERNOON', 'Afternoon (14:00 - 17:00)'),
    ]
    
    TASK_CHOICES = [
        ('MEAL_PREP', 'Meal preparation'),
        ('SHOPPING', 'Shopping assistance'),
        ('HOUSEKEEPING', 'Housekeeping'),
        ('LAUNDRY', 'Laundry assistance'),
        ('GARDENING', 'Gardening'),
        ('PET_CARE', 'Pet care'),
        ('CHILD_CARE', 'Child care'),
        ('TRANSPORT', 'Transport assistance'),
        ('TECH', 'Technology assistance'),
        ('READING', 'Reading aloud'),
    ]
    
    client = models.OneToOneField(ClientProfile, on_delete=models.CASCADE, related_name='preferences')
    
    # Preferences
    preferred_gender = models.CharField(
        max_length=1, 
        choices=ClientProfile.GENDER_CHOICES, 
        blank=True,
        help_text="Preferred gender of volunteer (leave blank for no preference)"
    )
    
    preferred_languages = models.JSONField(
        default=list,
        help_text="List of preferred languages for communication"
    )
    
    preferred_days = models.JSONField(
        default=list,
        help_text="List of preferred days for visits"
    )
    
    preferred_times = models.JSONField(
        default=list,
        help_text="List of preferred time slots"
    )
    
    preferred_location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Preferred meeting location (if different from home address)"
    )
    
    preferred_tasks = models.JSONField(
        default=list,
        help_text="List of tasks client needs assistance with"
    )

    has_pets = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether the client has pets in their home"
    )
    
    # Availability
    availability_notes = models.TextField(
        blank=True,
        help_text="Any specific availability notes or restrictions"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Client preferences"
    
    def __str__(self):
        return f"Preferences for {self.client.full_name}"
    
    def get_preferred_tasks_display(self):
        task_dict = dict(self.TASK_CHOICES)
        return [task_dict.get(task, task) for task in self.preferred_tasks]
    
    def get_preferred_days_display(self):
        day_dict = dict(self.DAY_CHOICES)
        return [day_dict.get(day, day) for day in self.preferred_days]

    def get_preferred_times_display(self):
        time_dict = dict(self.TIME_CHOICES)
        return [time_dict.get(time, time) for time in self.preferred_times]

    def get_preferred_languages_display(self):
        lang_dict = dict(self.LANGUAGES)
        return [lang_dict.get(lang, lang) for lang in self.preferred_languages]

    def get_preferred_gender_display(self):
        if not self.preferred_gender:
            return "No preference"
        gender_dict = dict(ClientProfile.GENDER_CHOICES)
        return gender_dict.get(self.preferred_gender, self.preferred_gender)