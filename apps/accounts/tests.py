import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

User = get_user_model()


# home page
@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["home", "about", "contact", "how_it_works"])
def test_public_pages(client, url_name):
    url = reverse(url_name)
    response = client.get(url)
    assert response.status_code == 200


# client login
@pytest.mark.django_db
def test_client_login_success(client):
    user = User.objects.create_user(
        email="client@example.com",
        password="pass1234",
        role="CLIENT",
        status="ACTIVE"
    )

    url = reverse("accounts:client_login")
    response = client.post(url, {
        "username": "client@example.com",
        "password": "pass1234"
    })

    assert response.status_code == 302
    assert response.url == reverse("client:dashboard")


@pytest.mark.django_db
def test_client_login_inactive(client):
    user = User.objects.create_user(
        email="client@example.com",
        password="pass1234",
        role="CLIENT",
        status="PENDING"
    )

    url = reverse("accounts:client_login")
    response = client.post(url, {
        "username": "client@example.com",
        "password": "pass1234"
    })

    assert response.status_code == 200
    assert b"not active" in response.content.lower()


@pytest.mark.django_db
def test_client_login_invalid_credentials(client):
    url = reverse("accounts:client_login")
    response = client.post(url, {
        "username": "wrong@example.com",
        "password": "wrongpass"
    })

    assert response.status_code == 200
    assert b"invalid credentials" in response.content.lower()


# client registration
@pytest.mark.django_db
@patch("apps.accounts.views.send_verification_email")
@patch("apps.accounts.views.generate_email_verification_token")  
@patch("apps.accounts.forms.ClientRegistrationForm.clean_gp_certificate")
def test_client_register_success(mock_gp, mock_token, mock_email, client):
    url = reverse("accounts:client_register")

    file = SimpleUploadedFile("gp.pdf", b"dummydata", content_type="application/pdf")
    mock_gp.return_value = file

    response = client.post(url, {
        "email": "newclient@example.com",
        "password1": "TestPass1!",
        "password2": "TestPass1!",
        "full_name": "Test User",
        "phone": "+447911123456",
        "terms_accepted": True,
        "gp_certificate": file,
    })

    assert response.status_code == 302, f"Expected redirect, got {response.status_code}. Form errors: {response.context.get('form').errors if hasattr(response, 'context') and response.context and 'form' in response.context else 'No form in context'}"
    assert response.url == reverse("accounts:client_register_confirmation")

    user = User.objects.get(email="newclient@example.com")
    assert user.gp_certificate is not None
    mock_token.assert_called_once()
    mock_email.assert_called_once()


@pytest.mark.django_db
def test_client_register_invalid(client):
    url = reverse("accounts:client_register")

    response = client.post(url, {
        "email": "bademail",
        "password1": "pass1234",
        "password2": "different"
    })

    assert response.status_code == 200
    assert User.objects.count() == 0


# client logout
@pytest.mark.django_db
def test_client_logout(client):
    user = User.objects.create_user(
        email="client@example.com",
        password="pass1234",
        role="CLIENT",
        status="ACTIVE"
    )

    client.force_login(user)
    url = reverse("accounts:client_logout")

    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse("accounts:client_login")


#volunteer login
@pytest.mark.django_db
def test_volunteer_login_success(client):
    user = User.objects.create_user(
        email="vol@example.com",
        password="pass1234",
        role="VOLUNTEER",
        status="ACTIVE"
    )

    url = reverse("accounts:volunteer_login")
    response = client.post(url, {
        "username": "vol@example.com",
        "password": "pass1234"
    })

    assert response.status_code == 302
    assert response.url == reverse("volunteer:dashboard")


@pytest.mark.django_db
def test_volunteer_login_invalid(client):
    url = reverse("accounts:volunteer_login")
    response = client.post(url, {
        "username": "wrong@example.com",
        "password": "wrongpass"
    })

    assert response.status_code == 200
    assert b"invalid credentials" in response.content.lower()


#register volunteer
@pytest.mark.django_db
@patch("apps.accounts.views.send_verification_email")
@patch("apps.accounts.views.generate_email_verification_token")
def test_volunteer_register_success(mock_token, mock_email, client):
    url = reverse("accounts:volunteer_register")

    response = client.post(url, {
        "email": "vol@example.com",
        "password1": "TestPass1!",
        "password2": "TestPass1!",
        "full_name": "Vol User",
        "phone": "+447911123456",
        "pvg_number": "1234567890123456",
        "terms_accepted": True,
    })

    assert response.status_code == 302, f"Expected redirect, got {response.status_code}. Form errors: {response.context.get('form').errors if hasattr(response, 'context') and response.context and 'form' in response.context else 'No form in context'}"
    assert response.url == reverse("accounts:volunteer_register_confirmation")

    user = User.objects.get(email="vol@example.com")
    mock_token.assert_called_once()
    mock_email.assert_called_once()


#email verification
@pytest.mark.django_db
@patch("apps.accounts.views.verify_email_token")
def test_verify_email_success(mock_verify, client):
    user = User.objects.create_user(
        email="client@example.com",
        password="pass1234",
        role="CLIENT",
        gp_certificate_verified=True,
        status="PENDING"
    )

    mock_verify.return_value = user

    url = reverse("accounts:verify_email", args=["sometoken"])
    response = client.get(url)

    user.refresh_from_db()
    assert user.status == "ACTIVE"
    assert response.status_code == 302
    assert response.url == reverse("home")

#token
@pytest.mark.django_db
@patch("apps.accounts.views.verify_email_token")
def test_verify_email_invalid(mock_verify, client):
    mock_verify.return_value = None

    url = reverse("accounts:verify_email", args=["badtoken"])
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("home")
