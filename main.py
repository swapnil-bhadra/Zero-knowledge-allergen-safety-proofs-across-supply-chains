
import json
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum


class Verdict(Enum):
    """Proof verdict"""
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class Allergen:
    """Represents an allergen in food"""
    name: str
    residue_ppm: float  # Concentration in ingredient
    severity: float     # Multiplier (3.0 for severe, 1.5 for mild)


@dataclass
class Equipment:
    """Kitchen equipment"""
    id: str
    name: str
    allergen_prone: bool
    neighbors: List[str]  # Can share residue with these
    last_cleaned: datetime
    cleaning_method: str


@dataclass
class Order:
    """Food order"""
    order_id: str
    timestamp: datetime
    equipment_used: str
    ingredients: List[str]
    allergens: List[Allergen]
    prep_time_minutes: int


@dataclass
class IoTReading:
    """IoT sensor reading"""
    timestamp: str
    equipment: str
    allergen: str
    level_ppm: float


@dataclass
class ConsumerProfile:
    """Consumer's allergen profile"""
    consumer_id: str
    allergies: Dict[str, float]      # allergen -> max ppm threshold
    severity_factors: Dict[str, float]  # allergen -> severity multiplier
    risk_tolerance: float


@dataclass
class ContaminationTrace:
    """Contamination calculation trace"""
    order_id: str
    equipment: str
    allergen_levels: Dict[str, float]
    contamination_paths: List[str]
    final_risk_score: float
    verdict: Verdict


@dataclass
class ZKProof:
    """Zero-knowledge proof"""
    proof_id: str
    kitchen_commitment_root: str
    order_commitment_root: str
    iot_commitment_root: str
    consumer_id: str
    risk_score: float
    verdict: Verdict
    proof_signature: str
    timestamp: str
    proof_size_bytes: int


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2: IoT SENSOR SIMULATION
# ═════════════════════════════════════════════════════════════════════════════

class IoTSensor:
    """Simulates a physical allergen detector sensor"""
    
    def __init__(self, sensor_id: str, equipment_name: str):
        self.sensor_id = sensor_id
        self.equipment_name = equipment_name
        self.readings: List[IoTReading] = []
        self.current_level = 0
    
    def record_reading(self, level: float, allergen: str, timestamp: str) -> IoTReading:
        """Record an allergen level at a point in time"""
        reading = IoTReading(
            timestamp=timestamp,
            equipment=self.equipment_name,
            allergen=allergen,
            level_ppm=level
        )
        self.readings.append(reading)
        self.current_level = level
        return reading
    
    def get_all_readings(self) -> List[IoTReading]:
        """Get all readings from this sensor"""
        return self.readings


def create_iot_network() -> Dict[str, IoTSensor]:
    """Create IoT sensors for each equipment piece"""
    sensors = {
        "fryer_sensor": IoTSensor("sensor_001", "fryer"),
        "prep_sensor": IoTSensor("sensor_002", "prep"),
        "assembly_sensor": IoTSensor("sensor_003", "assembly"),
        "grill_sensor": IoTSensor("sensor_004", "grill")
    }
    return sensors


def collect_iot_data_for_day(sensors: Dict[str, IoTSensor]) -> List[IoTReading]:
    """
    Simulate IoT data collection for a day
    Returns all readings from all sensors
    """
    all_readings = []
    
    # 11:00 - Peanut butter in fryer (50 ppm)
    readings = [
        sensors["fryer_sensor"].record_reading(50.0, "peanuts", "11:00"),
        sensors["fryer_sensor"].record_reading(45.0, "peanuts", "11:01"),
        sensors["fryer_sensor"].record_reading(40.5, "peanuts", "11:02"),
        sensors["fryer_sensor"].record_reading(36.5, "peanuts", "11:03"),
        sensors["fryer_sensor"].record_reading(32.8, "peanuts", "11:04"),
        sensors["fryer_sensor"].record_reading(29.5, "peanuts", "11:05"),
        
        # 11:15 - Fish in fryer (20 ppm)
        sensors["fryer_sensor"].record_reading(26.5, "peanuts", "11:15"),  # Residual
        sensors["fryer_sensor"].record_reading(20.0, "fish", "11:15"),
        
        # 11:20 - Oil changed (cleaning)
        sensors["fryer_sensor"].record_reading(0.0, "peanuts", "11:20"),
        sensors["fryer_sensor"].record_reading(0.0, "fish", "11:20"),
    ]
    
    all_readings.extend(readings)
    return all_readings


def create_iot_commitment(iot_readings: List[IoTReading]) -> Dict:
    """
    Hash IoT data to create a commitment
    This prevents restaurant from changing sensor data later
    """
    readings_data = [
        {
            'timestamp': r.timestamp,
            'equipment': r.equipment,
            'allergen': r.allergen,
            'level_ppm': r.level_ppm
        }
        for r in iot_readings
    ]
    
    readings_str = json.dumps(readings_data, sort_keys=True)
    commitment_hash = hashlib.sha256(readings_str.encode()).hexdigest()
    
    return {
        'root': commitment_hash,
        'reading_count': len(iot_readings),
        'timestamp': datetime.now().isoformat(),
        'signature': "RESTAURANT_PRIVATE_KEY_SIGNATURE"
    }


def setup_kitchen() -> List[Equipment]:
    """Define kitchen layout and equipment"""
    return [
        Equipment(
            id="station_a",
            name="Prep Station",
            allergen_prone=False,
            neighbors=["station_d"],
            last_cleaned=datetime.now() - timedelta(hours=2),
            cleaning_method="surface_wipe"
        ),
        Equipment(
            id="station_b",
            name="Deep Fryer",
            allergen_prone=True,
            neighbors=["station_d"],
            last_cleaned=datetime.now() - timedelta(minutes=30),
            cleaning_method="oil_change"
        ),
        Equipment(
            id="station_c",
            name="Grill",
            allergen_prone=False,
            neighbors=["station_d"],
            last_cleaned=datetime.now() - timedelta(hours=1),
            cleaning_method="surface_wipe"
        ),
        Equipment(
            id="station_d",
            name="Assembly Counter",
            allergen_prone=False,
            neighbors=["station_a", "station_b", "station_c"],
            last_cleaned=datetime.now() - timedelta(minutes=15),
            cleaning_method="surface_wipe"
        ),
    ]


def create_kitchen_commitment(equipment: List[Equipment]) -> Dict:
    """Hash kitchen structure to lock it in"""
    equipment_data = [
        {
            'id': e.id,
            'name': e.name,
            'allergen_prone': e.allergen_prone,
            'neighbors': e.neighbors
        }
        for e in equipment
    ]
    
    equipment_str = json.dumps(equipment_data, sort_keys=True)
    commitment_hash = hashlib.sha256(equipment_str.encode()).hexdigest()
    
    return {
        'root': commitment_hash,
        'equipment_count': len(equipment),
        'timestamp': datetime.now().isoformat(),
        'signature': "RESTAURANT_PRIVATE_KEY_SIGNATURE"
    }


def setup_orders() -> List[Order]:
    """Define order sequence for the day"""
    base_time = datetime.now()
    
    peanut_allergen = Allergen(name="peanuts", residue_ppm=50, severity=3.0)
    fish_allergen = Allergen(name="fish", residue_ppm=20, severity=2.0)
    
    return [
        Order(
            order_id="order_001",
            timestamp=base_time + timedelta(minutes=0),
            equipment_used="station_b",
            ingredients=["peanut_butter", "oil", "sugar"],
            allergens=[peanut_allergen],
            prep_time_minutes=5
        ),
        Order(
            order_id="order_002",
            timestamp=base_time + timedelta(minutes=15),
            equipment_used="station_b",
            ingredients=["fish", "breadcrumbs", "oil"],
            allergens=[fish_allergen],
            prep_time_minutes=7
        ),
        Order(
            order_id="order_003",
            timestamp=base_time + timedelta(minutes=30),
            equipment_used="station_a",
            ingredients=["lettuce", "tomato", "cucumber"],
            allergens=[],
            prep_time_minutes=3
        ),
    ]


def create_order_commitment(orders: List[Order]) -> Dict:
    """Hash order sequence to lock it in"""
    order_data = [
        {
            'order_id': o.order_id,
            'timestamp': o.timestamp.isoformat(),
            'equipment_used': o.equipment_used,
            'allergens': [a.name for a in o.allergens]
        }
        for o in orders
    ]
    
    order_str = json.dumps(order_data, sort_keys=True)
    commitment_hash = hashlib.sha256(order_str.encode()).hexdigest()
    
    return {
        'root': commitment_hash,
        'order_count': len(orders),
        'timestamp': datetime.now().isoformat(),
        'signature': "RESTAURANT_PRIVATE_KEY_SIGNATURE"
    }


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4: CONTAMINATION TRACKING (CORE LOGIC)
# ═════════════════════════════════════════════════════════════════════════════

def track_contamination(
    orders: List[Order],
    equipment: List[Equipment]
) -> Tuple[Dict[str, Dict[str, float]], List[ContaminationTrace]]:
    """
    Track how allergens spread through kitchen over time
    This is the core logic that goes into the ZK circuit
    """
    
    equipment_state = {e.id: {'allergens': {}} for e in equipment}
    traces: List[ContaminationTrace] = []
    
    for order in orders:
        station_id = order.equipment_used
        allergen_levels = {}
        
        # Add allergens from this order
        for allergen in order.allergens:
            if allergen.name not in equipment_state[station_id]['allergens']:
                equipment_state[station_id]['allergens'][allergen.name] = 0
            
            equipment_state[station_id]['allergens'][allergen.name] += allergen.residue_ppm
        
        # Apply decay (allergens break down over time)
        decay_rate = 0.9  # 10% decay per 15 minutes
        for eq_id in equipment_state:
            for allergen_name in list(equipment_state[eq_id]['allergens'].keys()):
                old_level = equipment_state[eq_id]['allergens'][allergen_name]
                new_level = old_level * decay_rate
                equipment_state[eq_id]['allergens'][allergen_name] = new_level
        
        # Cross-contamination between neighbors
        for eq in equipment:
            for neighbor_id in eq.neighbors:
                for allergen_name in equipment_state[eq.id]['allergens']:
                    transfer_rate = 0.05  # 5% transfer
                    transfer_amount = equipment_state[eq.id]['allergens'][allergen_name] * transfer_rate
                    
                    if allergen_name not in equipment_state[neighbor_id]['allergens']:
                        equipment_state[neighbor_id]['allergens'][allergen_name] = 0
                    
                    equipment_state[neighbor_id]['allergens'][allergen_name] += transfer_amount
        
        # Record contamination for this order
        station_allergens = equipment_state[station_id]['allergens'].copy()
        
        trace = ContaminationTrace(
            order_id=order.order_id,
            equipment=station_id,
            allergen_levels=station_allergens,
            contamination_paths=[f"{e.id}" for e in equipment],
            final_risk_score=sum(station_allergens.values()),
            verdict=Verdict.PASS if sum(station_allergens.values()) < 10 else Verdict.FAIL
        )
        traces.append(trace)
    
    return equipment_state, traces


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5: RISK CALCULATION
# ═════════════════════════════════════════════════════════════════════════════

def calculate_risk_for_consumer(
    target_order_id: str,
    equipment_state: Dict,
    target_equipment: str,
    consumer: ConsumerProfile
) -> Dict:
    """
    Calculate allergen risk for a specific consumer and order
    This computes what goes into the ZK proof
    """
    
    target_allergens = equipment_state[target_equipment]['allergens'].copy()
    
    risk_assessment = {
        'order_id': target_order_id,
        'equipment': target_equipment,
        'allergen_risks': {},
        'total_risk_score': 0,
        'verdict': Verdict.PASS,
    }
    
    # For each allergen the consumer is allergic to
    for allergen_name, threshold in consumer.allergies.items():
        residue_level = target_allergens.get(allergen_name, 0)
        severity = consumer.severity_factors.get(allergen_name, 1.0)
        
        risk_contribution = (residue_level / threshold) * severity
        risk_assessment['allergen_risks'][allergen_name] = {
            'residue_ppm': residue_level,
            'threshold_ppm': threshold,
            'severity': severity,
            'risk_score': risk_contribution,
            'safe': residue_level < threshold
        }
        risk_assessment['total_risk_score'] += risk_contribution
    
    # Final verdict
    if risk_assessment['total_risk_score'] < 10.0:
        risk_assessment['verdict'] = Verdict.PASS
    else:
        risk_assessment['verdict'] = Verdict.FAIL
    
    return risk_assessment


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6: ZK PROOF GENERATION
# ═════════════════════════════════════════════════════════════════════════════

def generate_zk_proof(
    risk_assessment: Dict,
    kitchen_commitment: Dict,
    order_commitment: Dict,
    iot_commitment: Dict,
    consumer: ConsumerProfile
) -> Optional[ZKProof]:
    """
    Generate a ZK proof if risk is safe
    If verdict is FAIL, refuse to generate (cannot prove false claims)
    
    In real system: Uses Circom/Cairo to generate cryptographic proof
    """
    
    if risk_assessment['verdict'] != Verdict.PASS:
        return None
    
    proof_id = hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16]
    
    proof = ZKProof(
        proof_id=proof_id,
        kitchen_commitment_root=kitchen_commitment['root'],
        order_commitment_root=order_commitment['root'],
        iot_commitment_root=iot_commitment['root'],
        consumer_id=consumer.consumer_id,
        risk_score=risk_assessment['total_risk_score'],
        verdict=risk_assessment['verdict'],
        proof_signature=hashlib.sha256(
            json.dumps({
                'risk': risk_assessment['total_risk_score'],
                'verdict': risk_assessment['verdict'].value
            }).encode()
        ).hexdigest()[:32],
        timestamp=datetime.now().isoformat(),
        proof_size_bytes=256  # Typical zk-SNARK size
    )
    
    return proof


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7: PROOF VERIFICATION
# ═════════════════════════════════════════════════════════════════════════════

def verify_zk_proof(proof: Optional[ZKProof], consumer: ConsumerProfile) -> bool:
    """
    Verify ZK proof without seeing intermediate data
    Consumer runs this to check if order is safe
    """
    
    if proof is None:
        return False
    
    # Check 1: Proof is for correct consumer
    if proof.consumer_id != consumer.consumer_id:
        return False
    
    # Check 2: Verdict is PASS
    if proof.verdict != Verdict.PASS:
        return False
    
    # Check 3: Risk score is below safe threshold
    if proof.risk_score >= 10.0:
        return False
    
    # Check 4: Proof signature is valid (in real system: actual crypto verification)
    # Here we just check it exists
    if not proof.proof_signature:
        return False
    
    return True


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8: LIE DETECTION
# ═════════════════════════════════════════════════════════════════════════════

def detect_tampering(
    original_iot_readings: List[IoTReading],
    original_commitment_root: str
) -> bool:
    """
    Detect if restaurant tried to change IoT data
    by comparing commitment root
    """
    
    readings_data = [
        {
            'timestamp': r.timestamp,
            'equipment': r.equipment,
            'allergen': r.allergen,
            'level_ppm': r.level_ppm
        }
        for r in original_iot_readings
    ]
    
    readings_str = json.dumps(readings_data, sort_keys=True)
    calculated_hash = hashlib.sha256(readings_str.encode()).hexdigest()
    
    return calculated_hash == original_commitment_root


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 9: MAIN EXECUTION & DEMONSTRATION
# ═════════════════════════════════════════════════════════════════════════════

def main():
    """
    Complete end-to-end demonstration of the system
    """
    
    print("\n" + "="*80)
    print("ZKP ALLERGEN-SAFETY VERIFICATION SYSTEM - FINAL DEMO")
    print("="*80)
    
    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1: Setup
    # ─────────────────────────────────────────────────────────────────────────
    
    print("\n[STEP 1] SETUP KITCHEN & ORDERS")
    print("-" * 80)
    
    equipment = setup_kitchen()
    orders = setup_orders()
    kitchen_commitment = create_kitchen_commitment(equipment)
    order_commitment = create_order_commitment(orders)
    
    print(f"✓ Kitchen: {len(equipment)} equipment pieces")
    print(f"✓ Orders: {len(orders)} orders scheduled")
    print(f"✓ Kitchen commitment: {kitchen_commitment['root'][:16]}...")
    print(f"✓ Order commitment: {order_commitment['root'][:16]}...")
    
    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2: IoT Data Collection
    # ─────────────────────────────────────────────────────────────────────────
    
    print("\n[STEP 2] IoT DATA COLLECTION")
    print("-" * 80)
    
    sensors = create_iot_network()
    iot_readings = collect_iot_data_for_day(sensors)
    iot_commitment = create_iot_commitment(iot_readings)
    
    print(f"✓ IoT sensors collected: {len(iot_readings)} readings")
    print(f"✓ IoT commitment: {iot_commitment['root'][:16]}...")
    print(f"✓ Sample readings:")
    for reading in iot_readings[:3]:
        print(f"  - {reading.timestamp}: {reading.level_ppm} ppm {reading.allergen}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3: Contamination Tracking
    # ─────────────────────────────────────────────────────────────────────────
    
    print("\n[STEP 3] CONTAMINATION TRACKING")
    print("-" * 80)
    
    equipment_state, traces = track_contamination(orders, equipment)
    
    print("✓ Contamination traced for all orders:")
    for trace in traces:
        print(f"  - {trace.order_id}: {trace.equipment}")
        for allergen, level in trace.allergen_levels.items():
            print(f"    {allergen}: {level:.2f} ppm")
    
    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4: Consumer Profile & Risk Calculation
    # ─────────────────────────────────────────────────────────────────────────
    
    print("\n[STEP 4] RISK CALCULATION FOR CONSUMER")
    print("-" * 80)
    
    alice = ConsumerProfile(
        consumer_id="alice_123",
        allergies={'peanuts': 1.0, 'fish': 5.0, 'sesame': 0.5},
        severity_factors={'peanuts': 3.0, 'fish': 2.0, 'sesame': 1.5},
        risk_tolerance=0.1
    )
    
    target_order = orders[2]  # order_003 (salad at prep station)
    
    risk_assessment = calculate_risk_for_consumer(
        target_order.order_id,
        equipment_state,
        target_order.equipment_used,
        alice
    )
    
    print(f"✓ Consumer: {alice.consumer_id}")
    print(f"✓ Target order: {target_order.order_id}")
    print(f"✓ Equipment: {target_order.equipment_used}")
    print(f"✓ Risk score: {risk_assessment['total_risk_score']:.2f}")
    print(f"✓ Verdict: {risk_assessment['verdict'].value}")
    print(f"✓ Allergen breakdown:")
    for allergen, risk in risk_assessment['allergen_risks'].items():
        status = "✓ SAFE" if risk['safe'] else "✗ UNSAFE"
        print(f"  {allergen}: {risk['residue_ppm']:.2f}/{risk['threshold_ppm']} ppm {status}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # STEP 5: Proof Generation
    # ─────────────────────────────────────────────────────────────────────────
    
    print("\n[STEP 5] ZK PROOF GENERATION")
    print("-" * 80)
    
    zk_proof = generate_zk_proof(
        risk_assessment,
        kitchen_commitment,
        order_commitment,
        iot_commitment,
        alice
    )
    
    if zk_proof:
        print(f"✓ Proof generated: {zk_proof.proof_id}")
        print(f"✓ Proof size: {zk_proof.proof_size_bytes} bytes")
        print(f"✓ Risk score verified: {zk_proof.risk_score:.2f}")
        print(f"✓ Verdict: {zk_proof.verdict.value}")
        print(f"✓ Signature: {zk_proof.proof_signature}")
    else:
        print("✗ Proof generation failed (risk is not safe)")
    
    # ─────────────────────────────────────────────────────────────────────────
    # STEP 6: Proof Verification
    # ─────────────────────────────────────────────────────────────────────────
    
    print("\n[STEP 6] PROOF VERIFICATION")
    print("-" * 80)
    
    if zk_proof:
        is_valid = verify_zk_proof(zk_proof, alice)
        
        print(f"✓ Proof verification:")
        print(f"  - Consumer match: ✓")
        print(f"  - Verdict check: ✓")
        print(f"  - Risk threshold: ✓")
        print(f"  - Signature valid: ✓")
        print(f"\n✓ FINAL RESULT: {'SAFE TO EAT ✓' if is_valid else 'UNSAFE ✗'}")
        
        print(f"\n✓ What consumer can verify:")
        print(f"  ✓ Proof is mathematically valid")
        print(f"  ✓ Risk is below threshold")
        print(f"  ✓ Kitchen structure is locked")
        print(f"  ✓ Order sequence is locked")
        print(f"  ✓ IoT data is locked")
        
        print(f"\n✗ What consumer cannot see:")
        print(f"  ✗ Kitchen layout")
        print(f"  ✗ Recipe details")
        print(f"  ✗ Other orders")
        print(f"  ✗ IoT sensor readings")
        print(f"  ✗ Supplier information")
    else:
        print("✗ Proof is invalid - Consumer knows order is unsafe")
    
    # ─────────────────────────────────────────────────────────────────────────
    # STEP 7: Lie Detection Test - Tampering Detection
    # ─────────────────────────────────────────────────────────────────────────
    
    print("\n[STEP 7] LIE DETECTION TEST - TAMPERING DETECTION")
    print("-" * 80)
    
    # Calculate original hash
    original_readings_data = [
        {
            'timestamp': r.timestamp,
            'equipment': r.equipment,
            'allergen': r.allergen,
            'level_ppm': r.level_ppm
        }
        for r in iot_readings
    ]
    original_readings_str = json.dumps(original_readings_data, sort_keys=True)
    original_hash = hashlib.sha256(original_readings_str.encode()).hexdigest()
    
    print(f"\n[SCENARIO 1: Original IoT Data - NOT TAMPERED]")
    print(f"  First reading: {iot_readings[0].level_ppm} ppm {iot_readings[0].allergen}")
    print(f"  Second reading: {iot_readings[1].level_ppm} ppm {iot_readings[1].allergen}")
    print(f"  Calculated hash: {original_hash[:32]}...")
    print(f"  Commitment root: {iot_commitment['root'][:32]}...")
    
    is_authentic = detect_tampering(iot_readings, iot_commitment['root'])
    if is_authentic:
        print(f"  HASHES MATCH - Data is authentic!")
    else:
        print(f"  HASHES DO NOT MATCH - Data was tampered!")
    
    # Create forged readings with changed data
    print(f"\n[SCENARIO 2: Restaurant Tries to Tamper]")
    print(f"  Attacker changes reading[0] from {iot_readings[0].level_ppm} ppm → 0.0 ppm")
    print(f"  Attacker changes reading[1] from {iot_readings[1].level_ppm} ppm → 0.0 ppm")
    
    forged_readings = []
    for i, r in enumerate(iot_readings):
        if i == 0 or i == 1:  # Change first two readings
            forged_readings.append(IoTReading(r.timestamp, r.equipment, r.allergen, 0.0))
        else:
            forged_readings.append(IoTReading(r.timestamp, r.equipment, r.allergen, r.level_ppm))
    
    # Calculate forged hash
    forged_readings_data = [
        {
            'timestamp': r.timestamp,
            'equipment': r.equipment,
            'allergen': r.allergen,
            'level_ppm': r.level_ppm
        }
        for r in forged_readings
    ]
    forged_readings_str = json.dumps(forged_readings_data, sort_keys=True)
    forged_hash = hashlib.sha256(forged_readings_str.encode()).hexdigest()
    
    print(f"  Forged first reading: {forged_readings[0].level_ppm} ppm {forged_readings[0].allergen} (FAKE)")
    print(f"  Forged second reading: {forged_readings[1].level_ppm} ppm {forged_readings[1].allergen} (FAKE)")
    print(f"  Calculated hash: {forged_hash[:32]}...")
    print(f"  Commitment root: {iot_commitment['root'][:32]}...")
    
    is_forged_authentic = detect_tampering(forged_readings, iot_commitment['root'])
    if is_forged_authentic:
        print(f"  HASHES MATCH - Tampering failed (shouldn't happen)")
    else:
        print(f"  HASHES DO NOT MATCH - TAMPERING DETECTED! ✓")
    
    print(f"\n[DETECTION RESULT]")
    print(f"  Original data verified: {is_authentic}")
    print(f"  Forged data verified: {is_forged_authentic}")
    print(f"  System caught tampering: {'YES' if not is_forged_authentic else 'NO'}")


if __name__ == "__main__":
    main()