def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * quantile)
    return sorted_values[index]


def estimate_cost(answer: str) -> float:
    estimated_tokens = max(len(answer.split()), 1)
    return round(estimated_tokens / 1000 * 0.00015, 8)
