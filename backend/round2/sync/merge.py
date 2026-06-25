def merge(log_a: dict, log_b: dict) -> dict:
    merged = {}
    all_keys = set(log_a.keys()).union(log_b.keys())
    
    for k in all_keys:
        if k in log_a and k in log_b:
            a = log_a[k]
            b = log_b[k]
            
            if a.lamport > b.lamport:
                merged[k] = a
            elif b.lamport > a.lamport:
                merged[k] = b
            else:
                if a.deleted and not b.deleted:
                    merged[k] = a
                elif b.deleted and not a.deleted:
                    merged[k] = b
                else:
                    # Use device_id for deterministic tie-breaking if perfectly concurrent
                    if a.device_id > b.device_id:
                        merged[k] = a
                    else:
                        merged[k] = b
        elif k in log_a:
            merged[k] = log_a[k]
        else:
            merged[k] = log_b[k]
            
    return merged
