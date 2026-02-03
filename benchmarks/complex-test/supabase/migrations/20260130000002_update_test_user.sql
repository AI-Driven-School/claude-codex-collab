-- Update test user password hash
UPDATE users
SET hashed_password = '$2b$12$veptxK5HvZd227ZvJYU.qeLtuxNqbK17kp3o0KLfic85dNDJLoX7W'
WHERE email = 'test@example.com';
