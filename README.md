

---

# Zero-Knowledge Allergen & Contamination Verification System

A cryptographic proof-of-concept for verifying commercial kitchen food safety and cross-contamination risks **without exposing proprietary business operations**.

By combining **IoT sensor networks**, **decay-and-transfer contamination modeling**, and **Zero-Knowledge Proofs (ZKPs)**, this system enables restaurants to prove an order is mathematically safe for a consumer’s specific allergy thresholds without revealing recipes, sensor readings, or operational layouts.

It aims to solve the problem of proving food safety for allergens to consumers without revealing a restaurant's proprietary recipes, kitchen layouts, or operational data.

---

## Architecture Overview

```
┌─────────────────┐       ┌────────────────────────┐       ┌────────────────────────┐
│   IoT Sensors   │ ───► │  Contamination Trace   │ ───► │    Risk Calculation    │
│  (Data Stream)  │       │   (Decay/Transfer)     │       │   (Threshold Check)    │
└────────┬────────┘       └────────────────────────┘       └───────────┬────────────┘
         │                                                             │
         ▼                                                             ▼
┌─────────────────┐                                        ┌────────────────────────┐
│ SHA-256 / ECDSA │                                        │    Groth16 ZK-Proof    │
│  (Commitments)  │                                        │  (256-Byte Attestation) │
└─────────────────┘                                        └───────────┬────────────┘
                                                                       │
                                                                       ▼
                                                           ┌────────────────────────┐
                                                           │ Consumer Verification  │
                                                           │   (PASS/FAIL Verdict)  │
                                                           └────────────────────────┘

```

---

## Core Components

* **IoT Sensor Simulation:** Simulates real-time, timestamped allergen readings (in PPM) across kitchen equipment.
* **Kitchen & Order Setup:** Models multi-station equipment topologies and scheduled order sequences.
* **Contamination Tracking Engine:** Calculates dynamic cross-contamination transfer and allergen decay across shared machinery.
* **Risk Calculation Engine:** Evaluates calculated residue against personalized consumer allergen sensitivity thresholds.
* **ZK Proof Generation:** Produces succinct, non-interactive cryptographic proofs for safe orders.
* **Proof Verification:** Allows external consumers to verify safety claims with zero knowledge of underlying data.
* **Lie Detection Engine:** Uses cryptographic commitments to detect retrospective sensor or log tampering.

---

## Key Data Structures

* `Verdict`: Enumerated result output (`PASS` or `FAIL`).
* `Allergen`: Represents a target food allergen profile.
* `Equipment`: Physical station/machinery node in the kitchen graph.
* `Order`: Scheduled item sequence tied to specific equipment stations.
* `IOTReading`: Timestamped allergen measurements (in PPM).
* `ConsumerProfile`: User-defined sensitivity thresholds per allergen.
* `ContaminationTrace`: Calculated allergen transfer history for an order.
* `ZKProof`: Cryptographic payload containing the Groth16 proof, signature, and root hash commitments.

---

## Cryptographic Stack

| Algorithm | Role | Purpose |
| --- | --- | --- |
| **SHA-256** | Data Commitments | Locks kitchen layout, order sequences, and IoT logs into immutable cryptographic roots. |
| **Groth16** | Zero-Knowledge Prover | Generates a 256-byte proof confirming `Calculated Risk < Threshold` without exposing inputs. |
| **ECDSA** | Digital Signatures | Authenticates that commitments originate from an authorized, registered restaurant node. |

---

## Execution Flow

```
STEP 1: Setup ──► STEP 2: IoT Data ──► STEP 3: Contamination ──► STEP 4: Risk Calculation
                                                                          │
STEP 7: Lie Detection ◄── STEP 6: Proof Verification ◄── STEP 5: ZK Generation ◄┘

```

1. **Setup:** Initialize kitchen stations, order queues, and cryptographic commitments.
2. **IoT Data Collection:** Capture real-time allergen concentration streams from physical nodes.
3. **Contamination Tracking:** Compute real-time cross-contamination propagation along equipment chains.
4. **Consumer Profile & Risk Calculation:** Evaluate order contamination against the user's personal threshold profile.
5. **Proof Generation:** If `Risk < Threshold`, compute a Groth16 ZK proof over private inputs.
6. **Proof Verification:** Validate the signature, proof payload, and state commitments publicly.
7. **Lie Detection Test:** Validate state roots to ensure no data was altered post-commitment.

---

## Demonstration Trace

```text
[STEP 1] SETUP KITCHEN & ORDERS
--------------------------------------------------------------------------------
✓ Kitchen: 4 equipment pieces
✓ Orders: 3 orders scheduled
✓ Kitchen commitment: d8b4c308ba8a40f6...
✓ Order commitment:   6a54f49ac37d3478...

[STEP 2] IoT DATA COLLECTION
--------------------------------------------------------------------------------
✓ IoT sensors collected: 10 readings
✓ IoT commitment: 7ea00a3181b85a13...
✓ Sample readings:
  - 11:00: 50.0 ppm peanuts
  - 11:01: 45.0 ppm peanuts
  - 11:02: 40.5 ppm peanuts

[STEP 3] CONTAMINATION TRACKING
--------------------------------------------------------------------------------
✓ Contamination traced for all orders:
  - order_001 (station_b): peanuts: 45.11 ppm
  - order_002 (station_b): peanuts: 40.80 ppm, fish: 18.05 ppm
  - order_003 (station_a): peanuts:  0.55 ppm, fish:  0.12 ppm

[STEP 4] RISK CALCULATION FOR CONSUMER
--------------------------------------------------------------------------------
✓ Consumer: alice_123
✓ Target order: order_003 (station_a)
✓ Risk score: 1.70 | Verdict: PASS
✓ Allergen breakdown:
  - peanuts: 0.55 / 1.0 ppm  ✓ SAFE
  - fish:    0.12 / 5.0 ppm  ✓ SAFE
  - sesame:  0.00 / 0.5 ppm  ✓ SAFE

[STEP 5] ZK PROOF GENERATION
--------------------------------------------------------------------------------
✓ Proof generated: 918ba13a5f1d3bbd
✓ Proof size: 256 bytes
✓ Risk score verified: 1.70 | Verdict: PASS
✓ Signature: a61e5525e5254b35bb3309217f74a2aa

[STEP 6] PROOF VERIFICATION
--------------------------------------------------------------------------------
✓ Proof verification:
  - Consumer match:   ✓
  - Verdict check:    ✓
  - Risk threshold:   ✓
  - Signature valid:  ✓

✓ FINAL RESULT: SAFE TO EAT ✓

[STEP 7] LIE DETECTION TEST
--------------------------------------------------------------------------------
✓ IoT data tampering detection: NOT TAMPERED ✓
✓ Forged data detection:         TAMPERING DETECTED ✓

```

---

## Data Visibility & Privacy Boundary(these are the security guarantees provided by us)

| Verified by Consumer (Public) | Hidden from Consumer (Private) |
| --- | --- |
| Cryptographic validity of the safety proof | Proprietary kitchen floorplan & routing |
| Allergen levels are within safe threshold boundaries | Exact recipe formulations & ingredients |
| Immutable lock on historical IoT sensor logs | Other customer orders and volume |
| Authenticated signature of the preparing facility | Raw IoT sensor readings & hardware IDs |
|  | Supply chain & ingredient vendor details |

---

## Security Guarantees

* **Anti-Tampering:** Restaurants cannot modify IoT logs or station orders retroactively after committing SHA-256 root hashes.
* **Soundness:** ZK proofs can **only** be generated when calculated allergen risk strictly satisfies the safety condition (`Risk < Threshold`).
* **Zero-Knowledge Privacy:** Public verifiers learn nothing about internal operations beyond the binary truth of the safety assertion.

## To run:
'''
1. initialise a git repository(git init)
2. git pull <this-repo-link>
3. python main.py
4. you can also use your own data to simulate
