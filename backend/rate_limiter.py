"""
Canvas API Rate Limiter
Enforces Canvas API rate limits (3000 requests per hour)

Built for: FacultyFlow v2.0
Based on: Canvas API rate limit documentation
"""

import time
from typing import List


class RateLimiter:
    """
    Rate limiter for Canvas API requests
    Canvas allows 3000 requests per hour per access token
    """

    def __init__(self, max_requests: int = 3000, window: int = 3600):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed in the time window
            window: Time window in seconds (default: 3600 = 1 hour)
        """
        self.max_requests = max_requests
        self.window = window
        self.requests: List[float] = []

    def wait_if_needed(self):
        """
        Check if rate limit is exceeded and wait if necessary
        Call this before making each Canvas API request
        """
        now = time.time()

        # Remove requests outside the current window
        self.requests = [r for r in self.requests if r > now - self.window]

        # If we've hit the limit, wait until the oldest request expires
        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            sleep_time = oldest_request + self.window - now

            if sleep_time > 0:
                print(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

                # Clean up again after sleeping
                now = time.time()
                self.requests = [r for r in self.requests if r > now - self.window]

        # Record this request
        self.requests.append(now)

    def get_remaining_requests(self) -> int:
        """
        Get number of requests remaining in current window

        Returns:
            int: Number of requests available before hitting limit
        """
        now = time.time()
        self.requests = [r for r in self.requests if r > now - self.window]
        return self.max_requests - len(self.requests)

    def reset(self):
        """
        Reset the rate limiter (clear all recorded requests)
        """
        self.requests = []
