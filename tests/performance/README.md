# MAAPS Performance Testing Suite

Comprehensive performance testing, benchmarking, and profiling for MAAPS.

## Overview

This suite includes:
- **Load Testing** - API endpoint load and stress testing with Locust
- **Benchmarking** - Core operation performance benchmarks
- **Stress Testing** - System behavior under extreme conditions
- **Profiling** - CPU and memory profiling analysis

## Installation

```bash
# Install performance testing dependencies
pip install -r requirements-performance.txt
```

## Quick Start

### 1. Benchmarking

Measure performance of core operations:

```bash
python tests/performance/benchmark.py
```

**Output:**
- Execution time statistics (avg, p50, p95, p99)
- Throughput (operations/second)
- Resource usage (CPU, memory)
- Results saved to `benchmark_results.json`

**Example Results:**
```
Audio Enhancement (1s)    Average: 45.23ms    95th: 52.10ms    Ops/sec: 22.11
Generate Melody (2s)      Average: 123.45ms   95th: 145.20ms   Ops/sec: 8.10
Extract Metadata          Average: 234.56ms   95th: 267.89ms   Ops/sec: 4.26
```

### 2. Load Testing

Test API endpoints under concurrent load:

```bash
# Start MAAPS API server first
cd api
uvicorn main:app --host 0.0.0.0 --port 8000

# In another terminal, run load test
locust -f tests/performance/load_test.py --host=http://localhost:8000
```

**Web UI:** Open `http://localhost:8089`

**Headless Mode:**
```bash
locust -f tests/performance/load_test.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --csv=results/load_test
```

**Parameters:**
- `--users`: Number of concurrent users (e.g., 50, 100, 200)
- `--spawn-rate`: Users spawned per second (e.g., 5, 10)
- `--run-time`: Test duration (e.g., 3m, 5m, 10m)
- `--csv`: Save results to CSV files

**Output:**
- Requests per second
- Response time percentiles (50th, 95th, 99th)
- Success/failure rates
- Per-endpoint statistics

### 3. Stress Testing

Test system under extreme conditions:

```bash
python tests/performance/stress_test.py
```

**Tests:**
- **Concurrent Load**: 5-10 workers, 50-100 tasks
- **Memory Stress**: Sustained high memory usage (30s)
- **Sustained Load**: Continuous operations (60s)

**Monitors:**
- Task success/failure rates
- Throughput under load
- Resource utilization
- System stability

### 4. Profiling

Identify performance bottlenecks:

```bash
python tests/performance/profile_analysis.py
```

**Generates:**
- CPU profile files (`*.prof`)
- Memory allocation reports
- Performance hotspot analysis
- Optimization recommendations

**View Profiles:**
```bash
# Interactive viewer
python -m pstats tests/performance/audio_enhancement_profile.prof

# In pstats:
sort cumulative  # Sort by cumulative time
stats 20         # Show top 20 functions
callers func     # Show callers of function
callees func     # Show callees of function
```

**Visual Profiling:**
```bash
pip install snakeviz
snakeviz tests/performance/audio_enhancement_profile.prof
```

## Test Scenarios

### Load Test Scenarios

#### Light Load (Development)
```bash
locust -f tests/performance/load_test.py \
  --host=http://localhost:8000 \
  --users 10 \
  --spawn-rate 2 \
  --run-time 2m \
  --headless
```

#### Medium Load (Staging)
```bash
locust -f tests/performance/load_test.py \
  --host=http://staging.example.com \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --csv=results/staging_load_test
```

#### High Load (Production Capacity)
```bash
locust -f tests/performance/load_test.py \
  --host=http://production.example.com \
  --users 200 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless \
  --csv=results/production_load_test
```

#### Spike Test (Burst Traffic)
```bash
locust -f tests/performance/load_test.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 50 \
  --run-time 3m \
  --headless
```

### User Classes

**MAAPSUser**: Normal user behavior
- 50% health checks
- 30% audio enhancement
- 10% music generation
- 10% metadata extraction

**HighLoadUser**: Intensive operations
- Batch processing (3 files)
- Large audio files (5 seconds)
- Complex workflows

## Performance Metrics

### Response Time Targets

| Operation | Target (p95) | Max (p99) |
|-----------|--------------|-----------|
| Health Check | < 50ms | < 100ms |
| Audio Enhancement (1s) | < 100ms | < 200ms |
| Audio Enhancement (5s) | < 500ms | < 1s |
| Music Generation (2s) | < 200ms | < 400ms |
| Metadata Extraction | < 300ms | < 600ms |
| Workflow Execution | < 1s | < 2s |
| Batch Processing (3 files) | < 3s | < 5s |

### Throughput Targets

| System Load | Target RPS | Success Rate |
|-------------|------------|--------------|
| Light (10 users) | > 50 | > 99% |
| Medium (50 users) | > 200 | > 98% |
| High (100 users) | > 300 | > 95% |
| Peak (200 users) | > 400 | > 90% |

### Resource Limits

| Resource | Soft Limit | Hard Limit |
|----------|------------|------------|
| CPU per pod | 2 cores | 4 cores |
| Memory per pod | 4GB | 8GB |
| Concurrent workflows | 50 | 100 |
| Queue size | 50,000 | 100,000 |

## Continuous Performance Testing

### CI/CD Integration

Add to `.github/workflows/ci-cd.yml`:

```yaml
performance-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-performance.txt

    - name: Run benchmarks
      run: python tests/performance/benchmark.py

    - name: Compare results
      run: |
        python scripts/compare_benchmarks.py \
          tests/performance/benchmark_results.json \
          baseline/benchmark_baseline.json

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: tests/performance/*.json
```

### Scheduled Testing

Run weekly performance tests:

```yaml
on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM
```

## Interpreting Results

### Benchmark Results

**Performance Tiers:**
- **Excellent**: < 100ms (real-time capable)
- **Good**: 100-500ms (responsive)
- **Acceptable**: 500-1000ms (usable)
- **Slow**: > 1000ms (needs optimization)

**Regression Detection:**
Compare current results to baseline:
```bash
python scripts/compare_benchmarks.py \
  tests/performance/benchmark_results.json \
  baseline/benchmark_baseline.json
```

Investigate if:
- Response time increased > 20%
- Throughput decreased > 15%
- Memory usage increased > 30%

### Load Test Results

**Good Indicators:**
- Response time p95 < target
- Success rate > 95%
- Requests/sec meets target
- No error spikes

**Warning Signs:**
- Response time p99 > 2x target
- Success rate < 90%
- Error rate > 5%
- Memory/CPU near limits

**Critical Issues:**
- Success rate < 80%
- Error rate > 10%
- Response time p99 > 10x target
- System crashes or hangs

### Profiling Results

**Look for:**
1. **Hot Functions**: High cumulative time
2. **Frequent Calls**: High call count
3. **Memory Leaks**: Growing memory usage
4. **I/O Bottlenecks**: Time spent waiting

**Optimization Targets:**
- Functions with > 5% total time
- Loops with > 1000 iterations
- Allocations > 100MB
- Wait time > 50ms

## Optimization Strategies

### Code Optimization

1. **Cache expensive computations**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=128)
   def expensive_computation(param):
       # ...
   ```

2. **Use vectorization**
   ```python
   # Slow
   result = [process(x) for x in data]

   # Fast
   result = np.vectorize(process)(data)
   ```

3. **Parallel processing**
   ```python
   from concurrent.futures import ThreadPoolExecutor

   with ThreadPoolExecutor(max_workers=4) as executor:
       results = executor.map(process, data)
   ```

### System Optimization

1. **Increase worker threads**
   ```bash
   MAX_WORKER_THREADS=16
   ```

2. **Tune message bus**
   ```bash
   MESSAGE_BUS_MAX_QUEUE_SIZE=100000
   MESSAGE_BUS_DISPATCHER_THREADS=12
   ```

3. **Enable caching**
   ```bash
   CACHE_MAX_SIZE_MB=4000
   ENABLE_RESULT_CACHING=true
   ```

4. **Resource limits**
   ```yaml
   resources:
     requests:
       cpu: "4"
       memory: "8Gi"
     limits:
       cpu: "8"
       memory: "16Gi"
   ```

## Troubleshooting

### High Response Times

1. Check CPU usage: `kubectl top pods`
2. Review profiling data for bottlenecks
3. Enable caching for frequent operations
4. Increase worker threads
5. Scale horizontally (add pods)

### Memory Issues

1. Check for memory leaks in profiling
2. Reduce cache size if needed
3. Limit concurrent workflows
4. Increase memory limits
5. Review audio buffer management

### Low Throughput

1. Increase worker threads
2. Scale horizontally
3. Enable load balancing
4. Optimize database queries
5. Use async processing

### Failed Tests

1. Check logs: `kubectl logs -f deployment/maaps`
2. Review error messages in results
3. Verify system health
4. Check resource limits
5. Review network connectivity

## Best Practices

1. **Baseline First**: Establish performance baseline before changes
2. **Test Regularly**: Run benchmarks on every major change
3. **Monitor Trends**: Track performance over time
4. **Set Alerts**: Alert on regression > 20%
5. **Test Realistic Scenarios**: Use production-like data
6. **Isolate Tests**: Run performance tests in isolated environment
7. **Document Results**: Keep history of performance metrics
8. **Optimize Incrementally**: Fix biggest bottlenecks first

## Results Archive

Store results for comparison:

```
tests/performance/
├── results/
│   ├── 2025-01-15_benchmark.json
│   ├── 2025-01-15_load_test.csv
│   └── ...
└── baseline/
    ├── benchmark_baseline.json
    └── load_test_baseline.csv
```

## Support

For performance issues:
1. Review profiling results
2. Check system logs
3. Compare to baseline metrics
4. Consult PERFORMANCE_REPORT.md
5. Open GitHub issue with results

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [Python Profiling Guide](https://docs.python.org/3/library/profile.html)
- [Memory Profiler](https://pypi.org/project/memory-profiler/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html)
