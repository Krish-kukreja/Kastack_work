# Intent Classifier Comparison

We evaluated two intent classifiers on a hand-written, held-out test set of 50 novel queries (including 10 Out-Of-Distribution/Gibberish inputs). Both models use an identical `LinearSVC` with Platt scaling (`CalibratedClassifierCV`).

| Model | Accuracy | Macro-F1 | OOD Detect | Head Size | Total Runtime Footprint | Mean Latency | p95 Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TF-IDF** | 0.8000 | 0.7952 | 0.9000 | 1.1875 MB | **1.1875 MB** | **4.59 ms** | **5.91 ms** |
| **MiniLM** | **0.8600** | **0.8627** | **0.9200** | **0.0786 MB** | ~90.08 MB | 21.00 ms | 41.93 ms |

### The Tradeoff Takeaway
While the MiniLM embedding model achieves higher semantic accuracy (86% vs 80%) and slightly better OOD/gibberish detection, it does so at the massive cost of an ~80x larger memory footprint and a ~5x slower inference latency. For the specific parameters of this challenge, the constraint was to ship a lightweight, zero-dependency model strictly under 50 MB. Therefore, TF-IDF decisively wins for this constraint, packing highly competitive performance into an ultra-fast, 1.18 MB standalone package.
