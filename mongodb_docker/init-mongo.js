db = db.getSiblingDB('auth_db');  // Cambia con il nome del tuo DB (da MONGO_URI_AUTH)
db.createUser({
  user: 'omnis_user',
  pwd: 'secure_password',  // Cambia con una password sicura
  roles: ['readWrite']
});

