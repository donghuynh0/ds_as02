# Coffeehouse Face Recognition System

## Setup

### 1. Database

**MongoDB**
```bash
cd docker/mongo
docker compose up -d
```

**MinIO**
```bash
cd docker/minio
docker compose up -d
```

### 2. Environment Configuration

Create `.env` file in `configs/` directory:

```bash
touch configs/.env
```

Update with your docker compose values:

```env
# MongoDB
MONGO_URI=mongodb://<MONGO_INITDB_ROOT_USERNAME>:<MONGO_INITDB_ROOT_PASSWORD>@<ip>:27017/?authSource=admin
MONGO_DB=<database_name>

# MinIO
MINIO_ENDPOINT=<ip>:9000
MINIO_ACCESS_KEY=<MINIO_ROOT_USER>
MINIO_SECRET_KEY=<MINIO_ROOT_PASSWORD>
MINIO_BUCKET=<bucket_name>
```

### 3. Virtual Environment

```bash
# Create
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

### 4. Insert Menu Data

```bash
mongosh < insert_menu.js
```

## Run

```bash
python3 app.py
```

**Access:**
- Client: http://localhost:5001/client
- Staff: http://localhost:5001/staff