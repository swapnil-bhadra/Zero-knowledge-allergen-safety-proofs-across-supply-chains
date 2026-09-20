import hashlib
import json
import time


# ============================================================================
# SHA-256 HASH FUNCTION
# ============================================================================

def calculate_sha256(input_str: str) -> str:
    """Create SHA-256 hash of the input string and return as hex string."""
    return hashlib.sha256(input_str.encode("utf-8")).hexdigest()


# ============================================================================
# SENSOR DATA COMMITMENT (Locking Data in Place)
# ============================================================================

def create_sensor_commitment(peanut_level, temperature, humidity):
    """Create a commitment (hash) of the current sensor data."""
    sensor_data = json.dumps({
        "timestamp": str(int(time.time() * 1000)),  # millis() equivalent
        "peanutPPM": peanut_level,
        "temperature": temperature,
        "humidity": humidity,
        "deviceID": "esp32_001",
    }, separators=(",", ":"))

    # Hash the data
    commitment = calculate_sha256(sensor_data)

    # Display commitment
    print("\n=== SENSOR DATA COMMITMENT ===")
    print(f"Data: {sensor_data}")
    print(f"Hash: {commitment}")
    print(f"Timestamp: {int(time.time() * 1000)}")
    print("Status: LOCKED (Cannot be changed)")

    # Upload commitment to cloud
    upload_commitment_to_cloud(commitment, sensor_data)

    return commitment


# ============================================================================
# PROOF GENERATION WITH HASHING
# ============================================================================

def generate_proof(peanut_level, risk_score, temperature, humidity):
    """Generate a proof with hash and verification hash."""
    proof_data = json.dumps({
        "type": "peanut_allergen_proof",
        "peanutLevel": peanut_level,
        "isSafe": peanut_level < 100,
        "riskScore": risk_score,
        "temperature": temperature,
        "humidity": humidity,
        "timestamp": int(time.time() * 1000),
    }, separators=(",", ":"))

    # Create proof hash
    proof_hash = calculate_sha256(proof_data)

    # Create verification hash (hash of hash)
    verification_hash = calculate_sha256(proof_hash)

    print("\n=== PROOF GENERATION ===")
    print(f"Proof Data: {proof_data}")
    print(f"Proof Hash: {proof_hash}")
    print(f"Verification Hash: {verification_hash}")

    # Store all three
    upload_proof_to_cloud(proof_data, proof_hash, verification_hash)

    return proof_data, proof_hash, verification_hash


# ============================================================================
# PROOF VERIFICATION WITH HASHING
# ============================================================================

def verify_proof(received_proof_data: str, received_proof_hash: str) -> bool:
    """Verify a proof by recalculating its hash and comparing."""
    calculated_hash = calculate_sha256(received_proof_data)
    is_valid = calculated_hash == received_proof_hash

    print("\n=== PROOF VERIFICATION ===")
    print(f"Received Data: {received_proof_data}")
    print(f"Received Hash: {received_proof_hash}")
    print(f"Calculated Hash: {calculated_hash}")
    print(f"Match: {'YES ✓' if is_valid else 'NO ✗'}")

    if not is_valid:
        print("TAMPERING DETECTED!")

    return is_valid


# ============================================================================
# HASH CHAIN (Multiple Commitments)
# ============================================================================

class HashChain:
    """Maintains a chain of hashes linking each record to the previous one."""

    def __init__(self):
        self.previous_hash = ""

    def create_hash_chain(self, peanut_level, temperature, humidity) -> str:
        """Create a new hash chained to the previous hash."""
        current_data = json.dumps({
            "peanut": peanut_level,
            "temp": temperature,
            "humidity": humidity,
        }, separators=(",", ":"))

        # Hash current data + previous hash (chain)
        chain_input = current_data + self.previous_hash
        current_hash = calculate_sha256(chain_input)

        print("\n=== HASH CHAIN ===")
        print(f"Current Data: {current_data}")
        print(f"Previous Hash: {self.previous_hash}")
        print(f"Chain Input: {chain_input}")
        print(f"Current Hash: {current_hash}")

        # Update for next iteration
        self.previous_hash = current_hash
        return current_hash


# ============================================================================
# CLOUD UPLOAD STUBS (implement as needed)
# ============================================================================

def upload_commitment_to_cloud(commitment: str, sensor_data: str):
    """Stub: upload commitment to cloud."""
    print(f"[cloud] Commitment uploaded: {commitment}")


def upload_proof_to_cloud(proof_data: str, proof_hash: str, verification_hash: str):
    """Stub: upload proof to cloud."""
    print(f"[cloud] Proof uploaded: {proof_hash}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Simulated sensor values
    peanut_level = 45.0
    temperature = 23.5
    humidity = 60.0
    risk_score = 0.2

    # 1. Create a sensor commitment
    create_sensor_commitment(peanut_level, temperature, humidity)

    # 2. Generate a proof
    proof_data, proof_hash, _ = generate_proof(
        peanut_level, risk_score, temperature, humidity
    )

    # 3. Verify the proof
    verify_proof(proof_data, proof_hash)

    # 4. Build a hash chain across multiple readings
    chain = HashChain()
    chain.create_hash_chain(peanut_level, temperature, humidity)
    chain.create_hash_chain(50.0, 24.0, 61.0)
    chain.create_hash_chain(55.0, 24.5, 62.0)