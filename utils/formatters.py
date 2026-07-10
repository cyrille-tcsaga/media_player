def format_duration(milliseconds: int) -> str:
    total_seconds = max(milliseconds, 0) // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"
