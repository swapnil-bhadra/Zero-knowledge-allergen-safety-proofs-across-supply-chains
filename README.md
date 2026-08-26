COMPONENTS:
  1. IoT Sensor Simulation
  2. Kitchen & Order Setup
  3. Contamination Tracking (Core Logic)
  4. Risk Calculation
  5. ZK Proof Generation
  6. Proof Verification
  7. Lie Detection

STATUS: Production-ready simulation (actual ZK circuits would use Circom/Cairo)

Data Structures used:
1. class Verdict - to show final result as PASS or  FAIL
2. class Allergen - to represent an allergen in food
3. class Equipment - to show all equipment in the kitchen
4. class Order - a food order
5. class IOTReading - readings from the IOT Sensors
6. class ConsumerProfile - create a conumer profile for the user
7. class ContaminationTrace -  Contamination calculation trace
8. class ZKProof -  Zero-knowledge proof

Flow of control:

STEP 1: Setup
STEP 2: IoT Data Collection
STEP 3: Contamination Tracking
STEP 4: Consumer Profile & Risk Calculation
STEP 5: Proof Generation
STEP 6: Proof Verification
STEP 7: Lie Detection Test

Flow in Detail:
Step 1: IoT Data Collection

What: Sensors in kitchen automatically measure allergen levels
Why: Real-time, continuous, timestamped data
Example: Fryer sensor detects 50 ppm peanuts at 11:00

Step 2: Create Commitments (Lock In Data)

What: Hash all data (kitchen, orders, IoT readings)
Why: Restaurant can't change data after committing
Example: Kitchen commitment root = d8b4c308ba8a40f6...

Step 3: Contamination Tracking

What: Calculate how allergens spread through equipment
Why: Model real cross-contamination paths
Example: 50 ppm peanuts → decay → transfer → 0.55 ppm at prep

Step 4: Risk Calculation

What: Compare residue against consumer's thresholds
Why: Determine if order is safe
Example: 0.55 ppm < 1.0 ppm threshold = SAFE

Step 5: Proof Generation

What: Generate cryptographic proof if risk is safe
Why: Can't fake the proof (only safe orders get proofs)
Example: Proof ID = 119093fe0e5e8462

Step 6: Proof Verification

What: Consumer verifies proof without seeing data
Why: Math proves safety without transparency
Example: Alice scans QR code, gets SAFE ✓

Step 7: Lie Detection

What: Detect if restaurant changed IoT data
Why: Commitments prevent tampering
Example: Forged data detected ✓


Results from Demo1:

COMPONENTS VERIFIED:
  ✓ IoT data collection and commitment
  ✓ Kitchen layout and commitment
  ✓ Order sequence and commitment
  ✓ Contamination tracking algorithm
  ✓ Risk calculation for specific consumer
  ✓ ZK proof generation (if safe)
  ✓ Proof verification (without revealing data)
  ✓ Tampering detection

SECURITY PROPERTIES:
  ✓ Restaurant cannot change IoT data (commitment prevents it)
  ✓ Restaurant cannot hide orders (commitment prevents it)
  ✓ Restaurant cannot fake kitchen layout (commitment prevents it)
  ✓ Proof can only be generated if risk is truly safe
  ✓ Consumer never sees sensitive data
  ✓ Consumer can cryptographically verify safety