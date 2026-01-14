def test_register_valid(client):
    response = client.post(
        "/api/v1/users/register",
        json={"email": "user@example.com", "password": "some_password"},
    )
    assert response.status_code == 201


def test_register_user_already_exists(client):
    payload = {"email": "user@example.com", "password": "some_password"}
    client.post("/api/v1/users/register", json=payload)
    response = client.post("/api/v1/users/register", json=payload)
    assert response.status_code == 409


def test_register_user_validation_error(client):
    # invalid email format
    response = client.post(
        "/api/v1/users/register",
        json={"email": "imposter", "password": "valid_password"},
    )
    assert response.status_code == 400

    # invalid password (after strip)
    response = client.post(
        "/api/v1/users/register",
        json={"email": "user@example.com", "password": "       "},
    )
    assert response.status_code == 400

    # missing password
    response = client.post(
        "/api/v1/users/register",
        json={"email": "user@example.com"},
    )
    assert response.status_code == 400

    # missing email
    response = client.post(
        "/api/v1/users/register",
        json={"password": "valid_password"},
    )
    assert response.status_code == 400

    # invalid types
    response = client.post(
        "/api/v1/users/register",
        json={"email": 6, "password": 7},
    )
    assert response.status_code == 400


def test_register_internal_error_rolls_back(client, db_session, monkeypatch):
    from sqlalchemy import select

    from domain.user.user_model import User

    def boom(db, email, password):
        user = User(email=email, password_hash=b"hash")
        db.add(user)
        db.flush()
        raise Exception("boom")

    monkeypatch.setattr(
        "api.v1.auth.router.auth_service.add_user_and_token", boom
    )

    response = client.post(
        "/api/v1/users/register",
        json={"email": "user@example.com", "password": "some_password"},
    )
    assert response.status_code == 500

    saved_user = db_session.execute(
        select(User).where(User.email == "user@example.com")
    ).scalar_one_or_none()
    assert saved_user is None


def test_register_valid_returns_payload(client, db_session):
    response = client.post(
        "/api/v1/users/register",
        json={"email": "user@example.com", "password": "12345678"},
    )
    assert response.status_code == 201

    body = response.get_json()
    assert body["message"] == "OK"
    assert "data" in body

    data = body["data"]

    assert data["email_sent"] is True
    assert "created_user" in data

    user = data["created_user"]

    assert user["email"] == "user@example.com"
    assert user["role"] == "user"
    assert user["id"] is not None
