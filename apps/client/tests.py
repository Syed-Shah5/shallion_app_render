import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.client.models import ClientProfile, ClientPreferences
from apps.client.forms import ClientProfileForm, ClientPreferencesForm

User = get_user_model()

# Fixtures
@pytest.fixture
def client_user(db):
    return User.objects.create_user(
        email='client@test.com', password='testpass123',
        role='CLIENT', full_name='Test Client',
        status='ACTIVE', is_email_verified=True,
    )

@pytest.fixture
def volunteer_user(db):
    return User.objects.create_user(
        email='vol@test.com', password='testpass123',
        role='VOLUNTEER', full_name='Vol User', status='ACTIVE',
    )

@pytest.fixture
def profile(client_user):
    return ClientProfile.objects.create(
        user=client_user,
        forename='Jane', surname='Doe', gender='F',
        phone='07911123456',
        address_line1='1 Test St', city='London', postcode='SW1A 1AA',
        date_of_birth=date(1985, 6, 15),
        emergency_contact_name='John Doe',
        emergency_contact_phone='07911654321',
        emergency_contact_relationship='Spouse',
        profile_completed=True,
    )

@pytest.fixture
def preferences(profile):
    return ClientPreferences.objects.create(
        client=profile,
        preferred_tasks=['SHOPPING', 'MEAL_PREP'],
        preferred_days=['MON', 'WED'],
        preferred_times=['MORNING'],
        preferred_languages=['EN'],
    )

@pytest.fixture
def auth_client(client, client_user):
    """Django test client logged in as a client user."""
    client.force_login(client_user)
    return client

VALID_PROFILE_POST = {
    'forename': 'Jane',
    'surname': 'Doe',
    'gender': 'F',
    'phone': '07911123456',
    'address_line1': '1 Test St',
    'address_line2': '',
    'city': 'London',
    'postcode': 'SW1A 1AA',
    'date_of_birth': '1985-06-15',
    'emergency_contact_name': 'John Doe',
    'emergency_contact_phone': '07911654321',
    'emergency_contact_relationship': 'Spouse',
    'additional_notes': '',
}

VALID_PREFS_POST = {
    'preferred_tasks': ['SHOPPING', 'MEAL_PREP'],
    'preferred_days': ['MON', 'WED'],
    'preferred_times': ['MORNING'],
    'preferred_languages': ['EN'],
    'preferred_gender': '',
    'preferred_location': '',
    'availability_notes': '',
}

# Model — ClientProfile
@pytest.mark.django_db
class TestClientProfileModel:

    def test_str(self, profile):
        assert str(profile) == 'Jane Doe'

    def test_full_name(self, profile):
        assert profile.full_name == 'Jane Doe'

    def test_age_exact_birthday_today(self, profile):
        today = date.today()
        profile.date_of_birth = date(today.year - 40, today.month, today.day)
        assert profile.age == 40

    def test_age_birthday_tomorrow(self, profile):
        today = date.today()
        tomorrow = date(today.year - 40, today.month, today.day) + timedelta(days=1)
        profile.date_of_birth = tomorrow
        assert profile.age == 39

    def test_profile_completed_default_false(self, db, client_user):
        # Create a second user to avoid unique constraint
        user2 = User.objects.create_user(
            email='c2@test.com', password='x', role='CLIENT', full_name='X',
        )
        p = ClientProfile.objects.create(
            user=user2, forename='A', surname='B', gender='M',
            address_line1='x', city='y', postcode='SW1A 1AA',
            date_of_birth=date(1990, 1, 1),
            emergency_contact_name='X', emergency_contact_phone='07911000000',
            emergency_contact_relationship='Friend',
        )
        assert p.profile_completed is False


# Model — ClientPreferences
@pytest.mark.django_db
class TestClientPreferencesModel:

    def test_str(self, preferences):
        assert 'Jane Doe' in str(preferences)

    def test_get_preferred_tasks_display(self, preferences):
        result = preferences.get_preferred_tasks_display()
        assert 'Shopping assistance' in result
        assert 'Meal preparation' in result

    def test_get_preferred_days_display(self, preferences):
        result = preferences.get_preferred_days_display()
        assert 'Monday' in result
        assert 'Wednesday' in result

    def test_get_preferred_times_display(self, preferences):
        result = preferences.get_preferred_times_display()
        assert 'Morning (8:00 - 11:00)' in result

    def test_get_preferred_languages_display(self, preferences):
        result = preferences.get_preferred_languages_display()
        assert 'English' in result

    def test_get_preferred_gender_display_blank(self, preferences):
        preferences.preferred_gender = ''
        assert preferences.get_preferred_gender_display() == 'No preference'

    def test_get_preferred_gender_display_value(self, preferences):
        preferences.preferred_gender = 'F'
        assert preferences.get_preferred_gender_display() == 'Female'


# Form — ClientProfileForm
class TestClientProfileForm:

    def _form(self, **overrides):
        return ClientProfileForm(data={**VALID_PROFILE_POST, **overrides})

    def test_valid_data(self):
        assert self._form().is_valid()

    # Forename
    def test_forename_too_short(self):
        form = self._form(forename='A')
        assert not form.is_valid()
        assert 'forename' in form.errors

    def test_forename_invalid_chars(self):
        form = self._form(forename='Jane123')
        assert not form.is_valid()
        assert 'forename' in form.errors

    def test_forename_title_cased(self):
        form = self._form(forename='jane')
        assert form.is_valid()
        assert form.cleaned_data['forename'] == 'Jane'

    # Surname
    def test_surname_too_short(self):
        form = self._form(surname='D')
        assert not form.is_valid()
        assert 'surname' in form.errors

    def test_surname_title_cased(self):
        form = self._form(surname='doe')
        assert form.is_valid()
        assert form.cleaned_data['surname'] == 'Doe'

    # Phone
    @pytest.mark.parametrize('number', ['07911123456', '+447911123456', '07911 123456'])
    def test_phone_valid_uk(self, number):
        assert self._form(phone=number).is_valid()

    def test_phone_invalid(self):
        form = self._form(phone='1234')
        assert not form.is_valid()
        assert 'phone' in form.errors

    # Postcode
    @pytest.mark.parametrize('pc', ['SW1A 1AA', 'sw1a1aa', 'EC1A 1BB', 'W1A 0AX'])
    def test_postcode_valid(self, pc):
        assert self._form(postcode=pc).is_valid()

    def test_postcode_invalid(self):
        form = self._form(postcode='INVALID')
        assert not form.is_valid()
        assert 'postcode' in form.errors

    def test_postcode_uppercased(self):
        form = self._form(postcode='sw1a 1aa')
        assert form.is_valid()
        assert form.cleaned_data['postcode'] == 'SW1A 1AA'

    # Date of birth
    def test_dob_under_18_rejected(self):
        young = (date.today() - timedelta(days=17 * 365)).isoformat()
        form = self._form(date_of_birth=young)
        assert not form.is_valid()
        assert 'date_of_birth' in form.errors

    def test_dob_over_120_rejected(self):
        form = self._form(date_of_birth='1800-01-01')
        assert not form.is_valid()
        assert 'date_of_birth' in form.errors

    def test_dob_valid_adult(self):
        assert self._form(date_of_birth='1985-06-15').is_valid()

    # City
    def test_city_too_short(self):
        form = self._form(city='X')
        assert not form.is_valid()
        assert 'city' in form.errors

    def test_city_invalid_chars(self):
        form = self._form(city='London123')
        assert not form.is_valid()
        assert 'city' in form.errors

    # Emergency contact
    def test_emergency_contact_name_too_short(self):
        form = self._form(emergency_contact_name='X')
        assert not form.is_valid()
        assert 'emergency_contact_name' in form.errors

    def test_emergency_contact_phone_invalid(self):
        form = self._form(emergency_contact_phone='abc')
        assert not form.is_valid()
        assert 'emergency_contact_phone' in form.errors


# Form — ClientPreferencesForm
class TestClientPreferencesForm:

    def _form(self, **overrides):
        return ClientPreferencesForm(data={**VALID_PREFS_POST, **overrides})

    def test_valid_data(self):
        assert self._form().is_valid()

    def test_no_tasks_invalid(self):
        assert not self._form(preferred_tasks=[]).is_valid()

    def test_no_days_invalid(self):
        assert not self._form(preferred_days=[]).is_valid()

    def test_no_times_invalid(self):
        assert not self._form(preferred_times=[]).is_valid()

    def test_optional_fields_blank_allowed(self):
        form = self._form(preferred_gender='', preferred_location='', availability_notes='')
        assert form.is_valid()



# Views — access control
@pytest.mark.django_db
class TestClientViewAccess:

    def test_dashboard_requires_login(self, client):
        resp = client.get(reverse('client:dashboard'))
        assert resp.status_code in (301, 302)
        assert '/accounts/' in resp['Location']

    def test_create_profile_requires_login(self, client):
        resp = client.get(reverse('client:create_profile'))
        assert resp.status_code in (301, 302)
        assert '/accounts/' in resp['Location']

    def test_edit_profile_requires_login(self, client):
        resp = client.get(reverse('client:edit_profile'))
        assert resp.status_code in (301, 302)
        assert '/accounts/' in resp['Location']

    def test_volunteer_cannot_access_dashboard(self, client, volunteer_user):
        client.force_login(volunteer_user)
        resp = client.get(reverse('client:dashboard'))
        assert resp.status_code == 302
        assert resp['Location'] == reverse('home')


# Views — dashboard
@pytest.mark.django_db
class TestClientDashboardView:

    def test_no_profile_redirects_to_create(self, auth_client):
        resp = auth_client.get(reverse('client:dashboard'))
        assert resp.status_code == 302
        assert resp['Location'] == reverse('client:create_profile')

    def test_with_profile_renders_200(self, auth_client, profile):
        resp = auth_client.get(reverse('client:dashboard'))
        assert resp.status_code == 200
        assert 'client/dashboard.html' in [t.name for t in resp.templates]

# Views — create profile
@pytest.mark.django_db
class TestClientCreateProfileView:

    def test_get_renders_form(self, auth_client):
        resp = auth_client.get(reverse('client:create_profile'))
        assert resp.status_code == 200
        assert 'client/profile_form.html' in [t.name for t in resp.templates]

    def test_existing_profile_redirects_to_edit(self, auth_client, profile):
        resp = auth_client.get(reverse('client:create_profile'))
        assert resp.status_code == 302
        assert resp['Location'] == reverse('client:edit_profile')

    def test_valid_post_creates_profile(self, auth_client, client_user):
        resp = auth_client.post(reverse('client:create_profile'), VALID_PROFILE_POST)
        assert resp.status_code == 302
        assert resp['Location'] == reverse('client:create_preferences')
        assert ClientProfile.objects.filter(user=client_user).exists()

    def test_invalid_post_rerenders_form(self, auth_client, client_user):
        data = {**VALID_PROFILE_POST, 'forename': 'X'}
        resp = auth_client.post(reverse('client:create_profile'), data)
        assert resp.status_code == 200
        assert not ClientProfile.objects.filter(user=client_user).exists()

# Views — edit profile
@pytest.mark.django_db
class TestClientEditProfileView:

    def test_get_renders_form_with_instance(self, auth_client, profile):
        resp = auth_client.get(reverse('client:edit_profile'))
        assert resp.status_code == 200
        assert b'Jane' in resp.content

    def test_valid_post_updates_profile(self, auth_client, profile):
        data = {**VALID_PROFILE_POST, 'forename': 'Updated'}
        resp = auth_client.post(reverse('client:edit_profile'), data)
        assert resp.status_code == 302
        assert resp['Location'] == reverse('client:dashboard')
        profile.refresh_from_db()
        assert profile.forename == 'Updated'

    def test_invalid_post_rerenders_form(self, auth_client, profile):
        data = {**VALID_PROFILE_POST, 'postcode': 'BADCODE'}
        resp = auth_client.post(reverse('client:edit_profile'), data)
        assert resp.status_code == 200



# Views — create preferences
@pytest.mark.django_db
class TestClientCreatePreferencesView:

    def test_get_renders_form(self, auth_client, profile):
        resp = auth_client.get(reverse('client:create_preferences'))
        assert resp.status_code == 200
        assert 'client/preferences_form.html' in [t.name for t in resp.templates]

    def test_existing_prefs_redirects_to_edit(self, auth_client, preferences):
        resp = auth_client.get(reverse('client:create_preferences'))
        assert resp.status_code == 302
        assert resp['Location'] == reverse('client:edit_preferences')

    def test_valid_post_creates_prefs_and_marks_complete(self, auth_client, profile):
        profile.profile_completed = False
        profile.save()
        resp = auth_client.post(reverse('client:create_preferences'), VALID_PREFS_POST)
        assert resp.status_code == 302
        assert resp['Location'] == reverse('client:dashboard')
        assert ClientPreferences.objects.filter(client=profile).exists()
        profile.refresh_from_db()
        assert profile.profile_completed is True

    def test_invalid_post_rerenders_form(self, auth_client, profile):
        data = {**VALID_PREFS_POST, 'preferred_tasks': []}
        resp = auth_client.post(reverse('client:create_preferences'), data)
        assert resp.status_code == 200
        assert not ClientPreferences.objects.filter(client=profile).exists()


# Views — edit preferences
@pytest.mark.django_db
class TestClientEditPreferencesView:

    def test_get_renders_form(self, auth_client, preferences):
        resp = auth_client.get(reverse('client:edit_preferences'))
        assert resp.status_code == 200

    def test_valid_post_updates_prefs(self, auth_client, preferences):
        data = {
            **VALID_PREFS_POST,
            'preferred_tasks': ['GARDENING'],
            'preferred_days': ['FRI'],
            'preferred_times': ['AFTERNOON'],
        }
        resp = auth_client.post(reverse('client:edit_preferences'), data)
        assert resp.status_code == 302
        assert resp['Location'] == reverse('client:dashboard')
        preferences.refresh_from_db()
        assert 'GARDENING' in preferences.preferred_tasks

    def test_view_profile_renders(self, auth_client, profile):
        resp = auth_client.get(reverse('client:view_profile'))
        assert resp.status_code == 200
        assert 'client/view_profile.html' in [t.name for t in resp.templates]