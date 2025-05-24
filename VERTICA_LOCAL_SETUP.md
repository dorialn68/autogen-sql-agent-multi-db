# 🐘 Vertica Community Edition - Local Setup Guide

## Quick Docker Setup (Recommended for Testing)

### 1. Prerequisites
- **Docker Desktop** installed and running
- **8GB+ RAM** recommended
- **5GB+ disk space** available

### 2. Pull and Run Vertica Community Edition
```bash
# Pull the official Vertica CE container
docker pull opentext/vertica-ce:latest

# Run Vertica with persistent data
docker run -d \
  --name vertica-ce \
  -p 5433:5433 \
  -p 5444:5444 \
  -e VERTICA_DB_NAME=testdb \
  -e VERTICA_DB_PASSWORD=password123 \
  -v vertica-data:/home/dbadmin/docker \
  opentext/vertica-ce:latest

# Check if container is running
docker ps
```

### 3. Verify Vertica is Running
```bash
# Check container logs
docker logs vertica-ce

# Connect to the container
docker exec -it vertica-ce /bin/bash

# Inside container, connect to database
vsql -U dbadmin -d testdb -h localhost -p 5433
```

### 4. Test Basic Vertica Operations
```sql
-- Check Vertica version
SELECT version();

-- List databases
\l

-- Create a test table
CREATE TABLE customers (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(50),
    country VARCHAR(50)
);

-- Insert sample data
INSERT INTO customers VALUES 
(1, 'John Doe', 'john@example.com', 'New York', 'USA'),
(2, 'Jane Smith', 'jane@example.com', 'London', 'UK'),
(3, 'Carlos Rodriguez', 'carlos@example.com', 'Madrid', 'Spain'),
(4, 'Liu Wei', 'liu@example.com', 'Beijing', 'China'),
(5, 'Priya Patel', 'priya@example.com', 'Mumbai', 'India');

-- Query the data
SELECT * FROM customers;
SELECT country, COUNT(*) FROM customers GROUP BY country;
```

## Alternative: Vertica CE VM Download

### 1. Download from Official Site
- Visit: https://www.vertica.com/download/vertica/community-edition/
- Download **Vertica Community Edition VM**
- Import into VMware/VirtualBox

### 2. Default Credentials
- **Username**: `dbadmin`
- **Password**: `dbadmin` 
- **Database**: `VMart`
- **Port**: `5433`

## Testing with Our Multi-Database System

### 1. Connection Details for AutoGen System
```json
{
  "name": "Local_Vertica_CE",
  "db_type": "vertica", 
  "connection_type": "remote",
  "database": "testdb",
  "schema": "public",
  "host": "localhost",
  "port": 5433,
  "username": "dbadmin",
  "password": "password123"
}
```

### 2. Test Queries for Validation
```sql
-- Complex analytical query
SELECT 
    country,
    COUNT(*) as customer_count,
    AVG(LENGTH(name)) as avg_name_length
FROM customers 
GROUP BY country 
ORDER BY customer_count DESC;

-- Cross-customer analysis (similar to your original request)
SELECT 
    c1.name as customer1,
    c2.name as customer2,
    c1.country as shared_country
FROM customers c1
JOIN customers c2 ON c1.country = c2.country AND c1.id != c2.id
ORDER BY c1.country;
```

## 🔧 Troubleshooting

### Docker Issues
```bash
# If container fails to start
docker logs vertica-ce

# Reset everything
docker stop vertica-ce
docker rm vertica-ce
docker volume rm vertica-data

# Try with more memory
docker run -d --name vertica-ce -p 5433:5433 \
  --memory=4g --memory-swap=8g \
  opentext/vertica-ce:latest
```

### Connection Issues
- **Port 5433 busy**: Change to `-p 5434:5433`
- **Memory issues**: Increase Docker memory limit to 4GB+
- **Slow startup**: Vertica CE can take 2-5 minutes to fully initialize

## 🎯 Integration with AutoGen System

Once Vertica is running, we'll:
1. ✅ Add Vertica config to `database_configs.json`
2. ✅ Test connection through our system 
3. ✅ Validate complex queries work
4. ✅ Test database switching in web interface
5. ✅ Verify AutoGen generates correct Vertica SQL

## Next Steps
1. Start Docker container
2. Verify Vertica is accessible
3. Add configuration to our system
4. Test multi-database switching
5. Validate complex analytical queries 