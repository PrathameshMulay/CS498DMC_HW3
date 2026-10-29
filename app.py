import os
from flask import Flask, request, jsonify
from pymongo import MongoClient, ReadPreference, WriteConcern

app = Flask(__name__)

MONGO_URI = os.environ["MONGO_URI"]

client = MongoClient(MONGO_URI)
db = client["ev_db"]
vehicles = db["vehicles"]

# Fast write: acknowledged by the primary.
fast_collection = vehicles.with_options(
    write_concern=WriteConcern(w=1)
)

# Safe write: acknowledged after majority replication.
safe_collection = vehicles.with_options(
    write_concern=WriteConcern(w="majority")
)

# Explicit primary read preference.
primary_collection = vehicles.with_options(
    read_preference=ReadPreference.PRIMARY
)

# Prefer secondary, but fall back to primary if no secondary is available.
secondary_preferred_collection = vehicles.with_options(
    read_preference=ReadPreference.SECONDARY_PREFERRED
)


@app.route("/insert-fast", methods=["POST"])
def insert_fast():
    document = request.get_json()

    if not document:
        return jsonify({"error": "JSON document required"}), 400

    result = fast_collection.insert_one(document)

    return jsonify({"id": str(result.inserted_id)}), 201


@app.route("/insert-safe", methods=["POST"])
def insert_safe():
    document = request.get_json()

    if not document:
        return jsonify({"error": "JSON document required"}), 400

    result = safe_collection.insert_one(document)

    return jsonify({"id": str(result.inserted_id)}), 201


@app.route("/count-tesla-primary", methods=["GET"])
def count_tesla_primary():
    count = primary_collection.count_documents({"make": "TESLA"})

    return jsonify({"count": count}), 200


@app.route("/count-bmw-secondary", methods=["GET"])
def count_bmw_secondary():
    count = secondary_preferred_collection.count_documents({"make": "BMW"})

    return jsonify({"count": count}), 200


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
