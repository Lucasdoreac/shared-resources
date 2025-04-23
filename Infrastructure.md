# Infrastructure
We use Docker to deploy a local Redis server for caching, aiming to accelerate response times and thereby improve the overall user experience.

## Why use ![Redis Cache](https://img.shields.io/badge/Redis%20Cache-%23D82C20.svg?logo=redis&logoColor=white)?

- **High performance:** 
by operating entirely in memory, it delivers responses in microseconds, significantly speeding up access to frequently used data.

- **Flexible data models:**
supports lists, hashes, sorted sets, and more, enabling implementations ranging from simple caching to counters, queues, and geolocation.

- **Automatic expiration:**
with per-key TTL, you set expiration times and ensure outdated information is removed effortlessly.

- **Optional persistence:**
combine speed with safety by enabling snapshots (RDB) or append‑only files (AOF) to write data to disk.

- **Scalability and high availability:**
with Sentinel for failover and Cluster for data partitioning, Redis scales reliably with your system.

- **Easy to use with Docker:**
the official lightweight image and Compose configuration make setup instant and reproducible in any environment.

## Why use ![Docker](https://img.shields.io/badge/Docker-%230db7ed.svg?logo=docker&logoColor=white)?

- **Reproducibility:** Identical environment on every machine, eliminating “it works on my machine” issues.

- **Isolation:** Prevents version and dependency conflicts on the host OS.
  
- **Declarative Configuration:** Everything defined in `docker-compose.yml`—version, persistence, healthchecks, and restart policies.
  
- **Clean Teardown:** `docker compose down -v` removes all resources without leaving residues.

- **CI/CD Friendly:** Automatically brings up Redis in your pipelines for integrated testing.
  
- **Network Portability:** Services communicate by container name, without relying on fixed IPs.
  
- **Security:** Containers are isolated with resource and network policies.  

## How to Use

1. Install Docker Desktop (if you haven’t already).  
2. Open a terminal in this directory.  
3. Run the following command to start Redis in detached mode:

   ```bash
   docker compose up -d

## Want to Verify?
If you want to monitor Redis, run the following command from Git Bash in the directory where your project is running:
   ```bash
   winpty docker exec -it redis-local redis-cli monitor
   ```
Example output:

![image](https://github.com/user-attachments/assets/dcb579a7-53da-4ca6-bdf5-e061ba601938)

This stream shows only the call(the exact command sent to redis server) it does not include the reply.Use it to verify that your aplication is ussing the expected commands 

