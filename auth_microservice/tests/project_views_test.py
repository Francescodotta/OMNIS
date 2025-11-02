def test_login(app, client):
    # First create the test user
    #create_admin_user(app)
    
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


def test_create_project_views(app, client):
    
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
    assert isinstance(access_token, str) and access_token  

    # Project views creation request
    create_project_views_data = {
        "name": "deio",
        "description": "anadlytersis",
        "field": "tanscriptomdterics"
        }

    views_response = client.post(
        "/api/project",
        json=create_project_views_data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
            }
    )

    print(f"Creation project views Status: {views_response.status_code}")
    print(f"Creation project views Data: {views_response.json}")
   
    assert views_response.status_code == 201
    progressive_id = views_response.json.get("progressive_id")
    print(f"Project created: {views_response.json}")

    # delete request to delete the user
    delete_response = client.delete(
        f"/api/project/{progressive_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    print(f"Delete Status: {delete_response.status_code}")
    print(f"Delete Data: {delete_response.json}")
    
    assert delete_response.status_code == 200  # or your expected status code