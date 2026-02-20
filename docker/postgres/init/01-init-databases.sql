-- Initialize databases for Nexum and Bastion

-- Create users
CREATE USER nexum WITH ENCRYPTED PASSWORD 'nexum_password';
CREATE USER bastion WITH ENCRYPTED PASSWORD 'bastion_password';

-- Create databases
CREATE DATABASE nexum OWNER nexum;
CREATE DATABASE bastion OWNER bastion;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE nexum TO nexum;
GRANT ALL PRIVILEGES ON DATABASE bastion TO bastion;

-- Connect to nexum database and set up schema
\c nexum;
GRANT ALL ON SCHEMA public TO nexum;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nexum;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nexum;

-- Connect to bastion database and set up schema
\c bastion;
GRANT ALL ON SCHEMA public TO bastion;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bastion;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bastion;