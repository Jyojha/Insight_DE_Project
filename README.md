### Map My Route:
> Map my Route is a "Route Planner" for the city of San Francisco. If you want to go from point A to point B, this app will return the path that takes shortest time in going from A to B.The data pipeline is a low latency event based architecture.

### Technologies Used:
> Ingestion - Kafka(on cluster with 4 nodes)

> Stream Processing - Spark Streaming(on cluster with 1 Master and 3 Worker nodes)

> Database - Neo4j(on cluster with 3 nodes)

> Frontend - Django with Leaflet(same cluster as Neo4j)

### Code Description:
> src/feed_events.py -  receives the real-time data from the source and publishes the data to the Kafka brokers

> src/consumer.py - implements the stream processing and updates the edge weights into the database

> src/init_db.py - initializes the graph database with the processed street intersections and street segments

