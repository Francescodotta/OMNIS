import security
import pymongo
 #create fake user
def create_admin_user(app):
    user_data= {}
    username= "username"
    password= "password"
    role= "admin"
    email = "admin@gmail.com"
    password= security.hash_password(password)
    role= security.encrypt_data(role)
    email = security.encrypt_data(email)
    nome = security.encrypt_data("admin")
    cognome = security.encrypt_data("admin")
    posizione = security.encrypt_data("professor")
    affiliazione = security.encrypt_data("università di napoli")
    laboratorio = security.encrypt_data("laboratorio di proteomica")
    tier = security.encrypt_data("tier 1")
    app.mongo.db.users.insert_one({"username": username, "password": password, "role": role, "email": email, "progressive_id": 0, "nome": nome, "cognome": cognome, "posizione": posizione, "affiliazione": affiliazione, "laboratorio": laboratorio, "tier": tier})
    return "admin create successfully"



def test_login(app, client):
    # First create the test user
    # create_admin_user(app)
    
    # Then attempt login with correct endpoint
    # Attempt login
    login_data = {
        "username": "username",
        "password": "password"
    }
    
    response = client.post("/api/login", 
                         json=login_data,
                         content_type='application/json')
    
    # Print response for debugging
    print(f"Response Status: {response.status_code}")
    print(f"Response Data: {response.data}")
    
    assert response.status_code == 200 or response.status_code == 201
    # Verify response contains expected data
    assert "access_token" in response.json
    
    
def test_user_registration(app, client):
    
    # Login to get access token
    login_data = {
        "username": "username",
        "password": "password"
    }
    response = client.post(
        "/api/login", 
        json=login_data,
        content_type='application/json'
    )
    assert response.status_code in (200, 201)
    access_token = response.json.get("access_token")
    print(f"Access token: {access_token} (type: {type(access_token)})")
    assert isinstance(access_token, str) and access_token  # Ensure token is a non-empty string

    user_registration_data = {
        "username": "eva",
        "nome": "eva",
        "cognome": "copola",
        "affiliazione": "università di napoli",
        "role": "guest",
        "posizione": "ricercatore",
        "laboratorio": "laboratorio di proteomica",
        "tier": "tier 1",
        "password": "password123",
        "email": "fra@gmail.com"
    }

    reg_response = client.post(
        "/api/register",
        json=user_registration_data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )

    print(f"Registration Status: {reg_response.status_code}")
    print(f"Registration Data: {reg_response.json}")

    assert reg_response.status_code == 201  # or your expected status code
    
    # delete request to delete the user
    delete_response = client.delete(
        "/api/user/eva",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    print(f"Delete Status: {delete_response.status_code}")
    print(f"Delete Data: {delete_response.json}")
    
    assert delete_response.status_code == 200  # or your expected status code