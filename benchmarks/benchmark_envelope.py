"""
Benchmark: Per-Sample Loop vs. Vectorized NumPy Envelope Generation

This script compares the performance of two envelope implementations:
1. Original: Python per-sample loop (slow, Python bytecode per iteration)
2. Optimized: Vectorized NumPy envelope with preallocated buffer (fast, C-level loops)

Run with: python benchmark_envelope.py

Expected output: The vectorized version is typically 5–10x faster depending on CPU and buffer size.
"""

import numpy as np
import timeit
from typing import Tuple

# Audio configuration
SAMPLE_RATE = 44100
BUFFER_SIZE = 1024
ATTACK_TIME = 0.01  # 10 ms
RELEASE_TIME = 0.05  # 50 ms
MAX_VOLUME = 0.3


# ============================================================================
# Original Implementation: Per-Sample Python Loop
# ============================================================================

def envelope_per_sample_loop(
    frame_count: int,
    amplitude: float,
    target_amplitude: float,
    amplitude_increment: float
) -> Tuple[np.ndarray, float]:
    """
    Generate envelope using a Python per-sample loop.
    Returns: (envelope array, updated amplitude)
    """
    envelope = np.zeros(frame_count, dtype=np.float32)
    for i in range(frame_count):
        # Gradually move amplitude towards target_amplitude
        if amplitude < target_amplitude:
            # Attack phase: ramp amplitude UP
            amplitude += amplitude_increment
            if amplitude >= target_amplitude:
                amplitude = target_amplitude
        elif amplitude > target_amplitude:
            # Release phase: ramp amplitude DOWN
            amplitude -= amplitude_increment
            if amplitude <= target_amplitude:
                amplitude = target_amplitude
        
        # Store the current envelope value for this sample
        envelope[i] = amplitude
    
    return envelope, amplitude


# ============================================================================
# Optimized Implementation: Vectorized NumPy Envelope
# ============================================================================

def envelope_vectorized(
    frame_count: int,
    amplitude: float,
    target_amplitude: float,
    amplitude_increment: float,
    env_buffer: np.ndarray
) -> Tuple[np.ndarray, float]:
    """
    Generate envelope using vectorized NumPy operations.
    Uses a preallocated buffer to avoid per-call allocations.
    Returns: (envelope view, updated amplitude)
    """
    env = env_buffer[:frame_count]

    # If already at target or no increment defined, fill constant
    if amplitude == target_amplitude or amplitude_increment == 0:
        env.fill(amplitude)
    else:
        # Determine direction of ramp (+1 or -1)
        direction = 1.0 if target_amplitude > amplitude else -1.0
        # Compute how many samples are needed to reach the target
        if amplitude_increment > 0:
            samples_to_target = int(np.ceil(abs(target_amplitude - amplitude) / amplitude_increment))
        else:
            samples_to_target = 0

        if samples_to_target >= frame_count or samples_to_target <= 0:
            # Full buffer is part of the ramp
            inc = direction * amplitude_increment
            env[:] = (amplitude + inc * np.arange(frame_count, dtype=np.float32))
            # Clamp to avoid overshoot
            if direction > 0:
                np.clip(env, None, target_amplitude, out=env)
            else:
                np.clip(env, target_amplitude, None, out=env)
            amplitude = env[-1]
        else:
            # Part ramp, then constant at target
            n = samples_to_target
            inc = direction * amplitude_increment
            env[:n] = (amplitude + inc * np.arange(n, dtype=np.float32))
            env[n:frame_count] = target_amplitude
            amplitude = env[-1]

    return env, amplitude


# ============================================================================
# Benchmark Setup
# ============================================================================

def benchmark_implementations():
    """Run timing tests on both implementations."""
    
    print("=" * 70)
    print("Envelope Implementation Benchmark")
    print("=" * 70)
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"Buffer Size (frames): {BUFFER_SIZE}")
    print(f"Attack Time: {ATTACK_TIME*1000:.1f} ms")
    print(f"Release Time: {RELEASE_TIME*1000:.1f} ms")
    print()

    # Test cases: attack phase, sustain phase, release phase
    test_cases = [
        {
            "name": "Attack Phase (0.0 → 0.3)",
            "amplitude": 0.0,
            "target_amplitude": 0.3,
            "amplitude_increment": 0.3 / (ATTACK_TIME * SAMPLE_RATE),
        },
        {
            "name": "Sustain Phase (0.3 → 0.3)",
            "amplitude": 0.3,
            "target_amplitude": 0.3,
            "amplitude_increment": 0.0,
        },
        {
            "name": "Release Phase (0.3 → 0.0)",
            "amplitude": 0.3,
            "target_amplitude": 0.0,
            "amplitude_increment": 0.3 / (RELEASE_TIME * SAMPLE_RATE),
        },
    ]

    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print("-" * 70)

        # Setup
        amp = test["amplitude"]
        tgt_amp = test["target_amplitude"]
        inc = test["amplitude_increment"]

        # Preallocated buffer for vectorized version
        env_buffer = np.zeros(BUFFER_SIZE, dtype=np.float32)

        # ---- Per-Sample Loop Timing ----
        def per_sample():
            return envelope_per_sample_loop(BUFFER_SIZE, amp, tgt_amp, inc)

        time_per_sample = timeit.timeit(per_sample, number=10000)

        # ---- Vectorized Timing ----
        def vectorized():
            return envelope_vectorized(BUFFER_SIZE, amp, tgt_amp, inc, env_buffer)

        time_vectorized = timeit.timeit(vectorized, number=10000)

        # ---- Results ----
        speedup = time_per_sample / time_vectorized
        print(f"  Per-Sample Loop (10000 iterations):  {time_per_sample:.4f} s")
        print(f"  Vectorized NumPy (10000 iterations): {time_vectorized:.4f} s")
        print(f"  Speedup: {speedup:.2f}x faster")

        # Per-callback timing (in microseconds, assuming ~23 callbacks/sec at 44.1kHz, 1024 buffer)
        per_sample_us = (time_per_sample / 10000) * 1_000_000
        vectorized_us = (time_vectorized / 10000) * 1_000_000
        time_saved_us = per_sample_us - vectorized_us
        
        print(f"  Per-callback time (per-sample):  {per_sample_us:.2f} µs")
        print(f"  Per-callback time (vectorized):  {vectorized_us:.2f} µs")
        print(f"  Time saved per callback:         {time_saved_us:.2f} µs ({100*time_saved_us/per_sample_us:.1f}%)")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("""
The vectorized NumPy implementation is significantly faster because:
  1. NumPy operations run in optimized C loops (not Python bytecode).
  2. Preallocated buffers eliminate per-callback memory allocations.
  3. SIMD instructions on modern CPUs further accelerate vector operations.

For real-time audio at 44.1 kHz with 1024-sample buffers (~43 callbacks/sec),
the vectorized version saves microseconds per callback, reducing CPU load and
jitter — critical for low-latency responsive audio.

Performance gains are most noticeable on:
  - Longer buffers (higher frame_count).
  - Lower-power CPUs (where per-sample Python overhead is significant).
  - Multi-voice synths (where you call this many times per callback).
""")


if __name__ == "__main__":
    benchmark_implementations()
