import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.volunteer.models import VolunteerProfile, VolunteerPreferences
from apps.volunteer.forms import VolunteerProfileForm, VolunteerPreferencesForm

User = get_user_model()

# Fixtures
@pytest.fixture
def volunteer_user(db):
    return User.objects.create_user(
        email='vol@test.com', password='testpass123',
        role='VOLUNTEER', full_name='John Smith',
        status='ACTIVE', is_email_verified=True,
    )

@pytest.fixture
def client_user(db):
    return User.objects.create_user(
        email='client@test.com', password='testpass123',
        role='CLIENT', full_name='Test Client', status='ACTIVE',
    )

@pytest.fixture
def profile(volunteer_user):
    return VolunteerProfile.objects.create(
        user=volunteer_user,
        forename='John', surname='Smith', gender='M',
        phone='07911123456',
        address_line1='10 Downing St', city='London', postcode='SW1A 2AA',
        date_of_birth=date(1990, 3, 15),
        emergency_contact_name='Jane Smith',
        emergency_contact_phone='07911654321',
        emergency_contact_relationship='Spouse',
        bio='I enjoy helping others.',
        skills_description='Cooking, driving.',
        profile_completed=True,
    )

@pytest.fixture
def preferences(profile):
    return VolunteerPreferences.objects.create(
        volunteer=profile,
        preferred_tasks=['SHOPPING', 'GARDENING'],
        preferred_days=['SAT', 'SUN'],
        preferred_times=['MORNING'],
        preferred_languages=['EN', 'FR'],
        can_work_with_pets=True,
        has_transportation=False,
    )

@pytest.fixture
def auth_client(client, volunteer_user):
    """Django test client logged in as a volunteer user."""
    client.force_login(volunteer_user)
    return client


VALID_PROFILE_POST = {
    'forename': 'John',
    'surname': 'Smith',
    'gender': 'M',
    'phone': '07911123456',
    'address_line1': '10 Downing St',
    'address_line2': '',
    'city': 'London',
    'postcode': 'SW1A 2AA',
    'date_of_birth': '1990-03-15',
    'emergency_contact_name': 'Jane Smith',
    'emergency_contact_phone': '07911654321',
    'emergency_contact_relationship': 'Spouse',
    'bio': 'I enjoy helping others.',
    'skills_description': 'Cooking, driving.',
}

VALID_PREFS_POST = {
    'preferred_tasks': ['SHOPPING', 'GARDENING'],
    'preferred_days': ['SAT', 'SUN'],
    'preferred_times': ['MORNING'],
    'preferred_languages': ['EN'],
    'preferred_gender': '',
    'can_work_with_pets': True,
    'availability_notes': '',
}



# Model — VolunteerProfile
@pytest.mark.django_db
class TestVolunteerProfileModel:

    def test_str(self, profile):
        assert str(profile) == 'John Smith'

    def test_full_name(self, profile):
        assert profile.full_name == 'John Smith'

    def test_age_exact_birthday_today(self, profile):
        today = date.today()
        profile.date_of_birth = date(today.year - 35, today.month, today.day)
        assert profile.age == 35

    def test_age_birthday_tomorrow(self, profile):
        today = date.today()
        tomorrow = date(today.year - 35, today.month, today.day) + timedelta(days=1)
        profile.date_of_birth = tomorrow
        assert profile.age == 34

    def test_profile_completed_default_false(self, db, volunteer_user):
        user2 = User.objects.create_user(
            email='v2@test.com', password='x', role='VOLUNTEER', full_name='V Two',
        )
        p = VolunteerProfile.objects.create(
            user=user2, forename='V', surname='Two', gender='F',
            address_line1='x', city='y', postcode='SW1A 1AA',
            date_of_birth=date(1992, 1, 1),
            emergency_contact_name='A B', emergency_contact_phone='07911000000',
            emergency_contact_relationship='Friend',
        )
        assert p.profile_completed is False

    def test_ordering_by_surname(self, db):
        u1 = User.objects.create_user(email='z@test.com', password='x', role='VOLUNTEER', full_name='Z')
        u2 = User.objects.create_user(email='a@test.com', password='x', role='VOLUNTEER', full_name='A')
        VolunteerProfile.objects.create(
            user=u1, forename='Zara', surname='Zimmer', gender='F',
            address_line1='x', city='y', postcode='SW1A 1AA',
            date_of_birth=date(1990, 1, 1),
            emergency_contact_name='EC One', emergency_contact_phone='07911000001',
            emergency_contact_relationship='Friend',
        )
        VolunteerProfile.objects.create(
            user=u2, forename='Adam', surname='Adams', gender='M',
            address_line1='x', city='y', postcode='SW1A 1AA',
            date_of_birth=date(1990, 1, 1),
            emergency_contact_name='EC Two', emergency_contact_phone='07911000002',
            emergency_contact_relationship='Friend',
        )
        profiles = list(VolunteerProfile.objects.filter(user__in=[u1, u2]))
        assert profiles[0].surname == 'Adams'
        assert profiles[1].surname == 'Zimmer'


# Model — VolunteerPreferences
@pytest.mark.django_db
class TestVolunteerPreferencesModel:

    def test_str(self, preferences):
        assert 'John Smith' in str(preferences)

    def test_get_preferred_tasks_display(self, preferences):
        result = preferences.get_preferred_tasks_display()
        assert 'Shopping assistance' in result
        assert 'Gardening' in result

    def test_get_preferred_days_display(self, preferences):
        result = preferences.get_preferred_days_display()
        assert 'Saturday' in result
        assert 'Sunday' in result

    def test_get_preferred_times_display(self, preferences):
        result = preferences.get_preferred_times_display()
        assert 'Morning (8:00 - 11:00)' in result

    def test_get_preferred_languages_display(self, preferences):
        result = preferences.get_preferred_languages_display()
        assert 'English' in result
        assert 'French' in result

    def test_get_preferred_gender_display_blank(self, preferences):
        preferences.preferred_gender = ''
        assert preferences.get_preferred_gender_display() == 'No preference'

    def test_get_preferred_gender_display_value(self, preferences):
        preferences.preferred_gender = 'F'
        assert preferences.get_preferred_gender_display() == 'Female'

    def test_can_work_with_pets_default_true(self, preferences):
        assert preferences.can_work_with_pets is True

    def test_has_transportation_default_false(self, preferences):
        assert preferences.has_transportation is False


# Form — VolunteerProfileForm
class TestVolunteerProfileForm:

    def _form(self, **overrides):
        return VolunteerProfileForm(data={**VALID_PROFILE_POST, **overrides})

    def test_valid_data(self):
        assert self._form().is_valid()

    # Forename
    def test_forename_too_short(self):
        form = self._form(forename='J')
        assert not form.is_valid()
        assert 'forename' in form.errors

    def test_forename_invalid_chars(self):
        form = self._form(forename='John99')
        assert not form.is_valid()
        assert 'forename' in form.errors

    def test_forename_title_cased(self):
        form = self._form(forename='john')
        assert form.is_valid()
        assert form.cleaned_data['forename'] == 'John'

    # Surname
    def test_surname_too_short(self):
        form = self._form(surname='S')
        assert not form.is_valid()
        assert 'surname' in form.errors

    def test_surname_title_cased(self):
        form = self._form(surname='smith')
        assert form.is_valid()
        assert form.cleaned_data['surname'] == 'Smith'

    # Phone
    @pytest.mark.parametrize('number', ['07911123456', '+447911123456', '07911 123456'])
    def test_phone_valid_uk(self, number):
        assert self._form(phone=number).is_valid()

    def test_phone_invalid(self):
        form = self._form(phone='99999')
        assert not form.is_valid()
        assert 'phone' in form.errors

    # Postcode
    @pytest.mark.parametrize('pc', ['SW1A 2AA', 'sw1a2aa', 'EC1A 1BB', 'W1A 0AX'])
    def test_postcode_valid(self, pc):
        assert self._form(postcode=pc).is_valid()

    def test_postcode_invalid(self):
        form = self._form(postcode='NOTAPC')
        assert not form.is_valid()
        assert 'postcode' in form.errors

    def test_postcode_uppercased(self):
        form = self._form(postcode='sw1a 2aa')
        assert form.is_valid()
        assert form.cleaned_data['postcode'] == 'SW1A 2AA'

    # Date of birth
    def test_dob_under_18_rejected(self):
        young = (date.today() - timedelta(days=17 * 365)).isoformat()
        form = self._form(date_of_birth=young)
        assert not form.is_valid()
        assert 'date_of_birth' in form.errors

    def test_dob_over_100_rejected(self):
        form = self._form(date_of_birth='1900-01-01')
        assert not form.is_valid()
        assert 'date_of_birth' in form.errors

    def test_dob_valid_adult(self):
        assert self._form(date_of_birth='1990-03-15').is_valid()

    # City
    def test_city_too_short(self):
        form = self._form(city='X')
        assert not form.is_valid()
        assert 'city' in form.errors

    def test_city_invalid_chars(self):
        form = self._form(city='London99')
        assert not form.is_valid()
        assert 'city' in form.errors

    # Emergency contact
    def test_emergency_contact_name_too_short(self):
        form = self._form(emergency_contact_name='X')
        assert not form.is_valid()
        assert 'emergency_contact_name' in form.errors

    def test_emergency_contact_phone_invalid(self):
        form = self._form(emergency_contact_phone='notaphone')
        assert not form.is_valid()
        assert 'emergency_contact_phone' in form.errors

    # Bio / skills_description — optional
    def test_bio_blank_allowed(self):
        assert self._form(bio='').is_valid()

    def test_skills_description_blank_allowed(self):
        assert self._form(skills_description='').is_valid()


# Form — VolunteerPreferencesForm

class TestVolunteerPreferencesForm:

    def _form(self, **overrides):
        return VolunteerPreferencesForm(data={**VALID_PREFS_POST, **overrides})

    def test_valid_data(self):
        assert self._form().is_valid()

    def test_no_tasks_invalid(self):
        assert not self._form(preferred_tasks=[]).is_valid()

    def test_no_days_invalid(self):
        assert not self._form(preferred_days=[]).is_valid()

    def test_no_times_invalid(self):
        assert not self._form(preferred_times=[]).is_valid()

    def test_preferred_gender_optional(self):
        assert self._form(preferred_gender='').is_valid()

    def test_can_work_with_pets_unchecked(self):
        data = {k: v for k, v in VALID_PREFS_POST.items() if k != 'can_work_with_pets'}
        assert VolunteerPreferencesForm(data=data).is_valid()

    def test_has_transportation_checked(self):
        assert self._form(has_transportation=True).is_valid()

    def test_availability_notes_blank_allowed(self):
        assert self._form(availability_notes='').is_valid()

# Views — access control
@pytest.mark.django_db
class TestVolunteerViewAccess:

    def test_dashboard_requires_login(self, client):
        resp = client.get(reverse('volunteer:dashboard'))
        assert resp.status_code in (301, 302)
        assert '/accounts/' in resp['Location']

    def test_create_profile_requires_login(self, client):
        resp = client.get(reverse('volunteer:create_profile'))
        assert resp.status_code in (301, 302)
        assert '/accounts/' in resp['Location']

    def test_edit_profile_requires_login(self, client):
        resp = client.get(reverse('volunteer:edit_profile'))
        assert resp.status_code in (301, 302)
        assert '/accounts/' in resp['Location']

    def test_client_cannot_access_dashboard(self, client, client_user):
        client.force_login(client_user)
        resp = client.get(reverse('volunteer:dashboard'))
        assert resp.status_code == 302
        assert resp['Location'] == reverse('home')

# Views — dashboard
@pytest.mark.django_db
class TestVolunteerDashboardView:

    def test_no_profile_redirects_to_create(self, auth_client):
        resp = auth_client.get(reverse('volunteer:dashboard'))
        assert resp.status_code == 302
        assert resp['Location'] == reverse('volunteer:create_profile')

    def test_with_profile_renders_200(self, auth_client, profile):
        resp = auth_client.get(reverse('volunteer:dashboard'))
        assert resp.status_code == 200
        assert 'volunteer/dashboard.html' in [t.name for t in resp.templates]

# Views — create profile
@pytest.mark.django_db
class TestVolunteerCreateProfileView:

    def test_get_renders_form(self, auth_client):
        resp = auth_client.get(reverse('volunteer:create_profile'))
        assert resp.status_code == 200
        assert 'volunteer/profile_form.html' in [t.name for t in resp.templates]

    def test_existing_profile_redirects_to_edit(self, auth_client, profile):
        resp = auth_client.get(reverse('volunteer:create_profile'))
        assert resp.status_code == 302
        assert resp['Location'] == reverse('volunteer:edit_profile')

    def test_valid_post_creates_profile(self, auth_client, volunteer_user):
        resp = auth_client.post(reverse('volunteer:create_profile'), VALID_PROFILE_POST)
        assert resp.status_code == 302
        assert resp['Location'] == reverse('volunteer:create_preferences')
        assert VolunteerProfile.objects.filter(user=volunteer_user).exists()

    def test_invalid_post_rerenders_form(self, auth_client, volunteer_user):
        data = {**VALID_PROFILE_POST, 'forename': 'X'}
        resp = auth_client.post(reverse('volunteer:create_profile'), data)
        assert resp.status_code == 200
        assert not VolunteerProfile.objects.filter(user=volunteer_user).exists()


# Views — edit profile
@pytest.mark.django_db
class TestVolunteerEditProfileView:

    def test_get_renders_form_with_instance(self, auth_client, profile):
        resp = auth_client.get(reverse('volunteer:edit_profile'))
        assert resp.status_code == 200
        assert b'John' in resp.content

    def test_valid_post_updates_profile(self, auth_client, profile):
        data = {**VALID_PROFILE_POST, 'forename': 'Updated'}
        resp = auth_client.post(reverse('volunteer:edit_profile'), data)
        assert resp.status_code == 302
        assert resp['Location'] == reverse('volunteer:dashboard')
        profile.refresh_from_db()
        assert profile.forename == 'Updated'

    def test_invalid_post_rerenders_form(self, auth_client, profile):
        data = {**VALID_PROFILE_POST, 'postcode': 'BADPC'}
        resp = auth_client.post(reverse('volunteer:edit_profile'), data)
        assert resp.status_code == 200


# Views — create preferences
@pytest.mark.django_db
class TestVolunteerCreatePreferencesView:

    def test_get_renders_form(self, auth_client, profile):
        resp = auth_client.get(reverse('volunteer:create_preferences'))
        assert resp.status_code == 200
        assert 'volunteer/preferences_form.html' in [t.name for t in resp.templates]

    def test_existing_prefs_redirects_to_edit(self, auth_client, preferences):
        resp = auth_client.get(reverse('volunteer:create_preferences'))
        assert resp.status_code == 302
        assert resp['Location'] == reverse('volunteer:edit_preferences')

    def test_valid_post_creates_prefs_and_marks_complete(self, auth_client, profile):
        profile.profile_completed = False
        profile.save()
        resp = auth_client.post(reverse('volunteer:create_preferences'), VALID_PREFS_POST)
        assert resp.status_code == 302
        assert resp['Location'] == reverse('volunteer:dashboard')
        assert VolunteerPreferences.objects.filter(volunteer=profile).exists()
        profile.refresh_from_db()
        assert profile.profile_completed is True

    def test_invalid_post_rerenders_form(self, auth_client, profile):
        data = {**VALID_PREFS_POST, 'preferred_tasks': []}
        resp = auth_client.post(reverse('volunteer:create_preferences'), data)
        assert resp.status_code == 200
        assert not VolunteerPreferences.objects.filter(volunteer=profile).exists()


# Views — edit preferences
@pytest.mark.django_db
class TestVolunteerEditPreferencesView:

    def test_get_renders_form(self, auth_client, preferences):
        resp = auth_client.get(reverse('volunteer:edit_preferences'))
        assert resp.status_code == 200

    def test_valid_post_updates_prefs(self, auth_client, preferences):
        data = {
            **VALID_PREFS_POST,
            'preferred_tasks': ['MEAL_PREP'],
            'preferred_days': ['FRI'],
            'preferred_times': ['AFTERNOON'],
        }
        resp = auth_client.post(reverse('volunteer:edit_preferences'), data)
        assert resp.status_code == 302
        assert resp['Location'] == reverse('volunteer:dashboard')
        preferences.refresh_from_db()
        assert 'MEAL_PREP' in preferences.preferred_tasks

    def test_view_profile_renders(self, auth_client, profile):
        resp = auth_client.get(reverse('volunteer:view_profile'))
        assert resp.status_code == 200
        assert 'volunteer/view_profile.html' in [t.name for t in resp.templates]
