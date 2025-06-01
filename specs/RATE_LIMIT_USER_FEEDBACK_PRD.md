# Rate Limit User Feedback Implementation PRD

## Overview
This document outlines the implementation of user-friendly rate limiting feedback for the Podcast Digest Agent. The current rate limiting (10 requests per hour per IP) protects against abuse but provides poor user experience when limits are reached. This PRD defines enhancements to provide clear, actionable feedback to users.

## Problem Statement
Currently, when users hit the rate limit:
- They receive a generic "Error starting processing" message
- No indication that it's a temporary rate limit issue
- No information about when they can try again
- Users may think the service is broken rather than temporarily limited

## Goals
1. **Clear Communication**: Users immediately understand they've hit a rate limit
2. **Actionable Feedback**: Show exactly when they can make their next request
3. **Improved UX**: Differentiate rate limiting from actual errors
4. **Transparency**: Display remaining requests and reset times

## Technical Approach

### Backend Changes

#### 1. Enhanced Rate Limit Tracking
```python
# Modified request tracker structure
request_tracker = defaultdict(lambda: {
    'requests': [],  # List of request timestamps
    'first_request_time': None  # Track oldest request for reset calculation
})
```

#### 2. Improved check_rate_limit Function
```python
def check_rate_limit(request: Request, max_requests: int = 10, window_hours: int = 1):
    """Enhanced rate limiting with detailed feedback"""
    client_ip = request.client.host
    now = datetime.now()
    cutoff = now - timedelta(hours=window_hours)
    
    # Get client data
    client_data = request_tracker[client_ip]
    
    # Clean old requests
    client_data['requests'] = [
        req_time for req_time in client_data['requests'] 
        if req_time > cutoff
    ]
    
    # Calculate rate limit info
    requests_made = len(client_data['requests'])
    requests_remaining = max_requests - requests_made
    
    if requests_made >= max_requests:
        # Calculate when the oldest request expires
        oldest_request = min(client_data['requests'])
        reset_time = oldest_request + timedelta(hours=window_hours)
        seconds_until_reset = int((reset_time - now).total_seconds())
        
        # Return detailed error with retry information
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded. Max {max_requests} requests per {window_hours} hour(s)",
                "requests_made": requests_made,
                "requests_limit": max_requests,
                "retry_after_seconds": seconds_until_reset,
                "reset_time": reset_time.isoformat(),
                "window_hours": window_hours
            },
            headers={
                "Retry-After": str(seconds_until_reset),
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset_time.timestamp()))
            }
        )
    
    # Add current request
    client_data['requests'].append(now)
    
    # Return rate limit info in response headers
    return {
        "X-RateLimit-Limit": str(max_requests),
        "X-RateLimit-Remaining": str(requests_remaining - 1),
        "X-RateLimit-Window": f"{window_hours}h"
    }
```

#### 3. Apply Headers to Successful Responses
```python
@router.post("/process_youtube_url", response_model=ProcessUrlResponse, status_code=202)
async def process_youtube_url_endpoint(request: ProcessUrlRequest, req: Request, response: Response):
    rate_limit_headers = check_rate_limit(req)
    
    # Add rate limit headers to response
    for header, value in rate_limit_headers.items():
        response.headers[header] = value
    
    # ... rest of the function
```

### Frontend Changes

#### 1. Enhanced Error Handling in WorkflowContext
```typescript
// In WorkflowContext.tsx
.catch((error) => {
  console.error("[WORKFLOW] Error starting processing:", error);
  
  // Check if it's a rate limit error
  if (error.response?.status === 429) {
    const rateLimitData = error.response.data.detail;
    
    // Calculate human-readable time
    const minutesUntilReset = Math.ceil(rateLimitData.retry_after_seconds / 60);
    const resetTime = new Date(rateLimitData.reset_time);
    
    // Update state with rate limit info
    setWorkflowState((prevState) => {
      if (!prevState) return null;
      
      return {
        ...prevState,
        processingStatus: {
          ...prevState.processingStatus,
          status: "rate_limited",
        },
        rateLimitInfo: {
          retryAfterSeconds: rateLimitData.retry_after_seconds,
          resetTime: resetTime,
          requestsLimit: rateLimitData.requests_limit,
          message: `You've reached the limit of ${rateLimitData.requests_limit} requests per hour. You can try again in ${minutesUntilReset} minute${minutesUntilReset > 1 ? 's' : ''}.`
        },
        timeline: [
          ...prevState.timeline,
          {
            timestamp: new Date().toISOString(),
            event: "rate_limit_exceeded",
            message: `Rate limit reached. Try again at ${resetTime.toLocaleTimeString()}`,
          },
        ],
      };
    });
    
    // Show user-friendly toast
    toast.error(
      `Rate limit reached! You can make another request in ${minutesUntilReset} minute${minutesUntilReset > 1 ? 's' : ''}. 
      (Limit: ${rateLimitData.requests_limit} requests per hour)`,
      { duration: 10000 }
    );
  } else {
    // Handle other errors as before
    // ...
  }
  
  setIsProcessing(false);
});
```

#### 2. Rate Limit UI Component
Create `client/src/components/ui/RateLimitNotice.tsx`:
```typescript
interface RateLimitNoticeProps {
  resetTime: Date;
  requestsLimit: number;
}

export function RateLimitNotice({ resetTime, requestsLimit }: RateLimitNoticeProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>("");
  
  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();
      const diff = resetTime.getTime() - now.getTime();
      
      if (diff <= 0) {
        setTimeRemaining("Ready to retry!");
        return;
      }
      
      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeRemaining(`${minutes}:${seconds.toString().padStart(2, '0')}`);
    };
    
    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    
    return () => clearInterval(interval);
  }, [resetTime]);
  
  return (
    <div className="p-4 border border-warning bg-warning/10 rounded-lg">
      <h3 className="font-semibold text-warning mb-2">Rate Limit Reached</h3>
      <p className="text-sm mb-2">
        You've used all {requestsLimit} requests for this hour.
      </p>
      <div className="flex items-center gap-2">
        <Clock className="h-4 w-4" />
        <span className="font-mono text-lg">{timeRemaining}</span>
        <span className="text-sm text-muted-foreground">until next request</span>
      </div>
    </div>
  );
}
```

#### 3. Update HeroSection to Show Rate Limit Notice
```typescript
// In HeroSection.tsx
{processingStatus === "rate_limited" && workflowState?.rateLimitInfo && (
  <RateLimitNotice 
    resetTime={workflowState.rateLimitInfo.resetTime}
    requestsLimit={workflowState.rateLimitInfo.requestsLimit}
  />
)}
```

## Implementation Plan

### Phase 1: Backend Enhancement (1 hour)
1. Update rate limit tracking structure
2. Enhance `check_rate_limit` function with detailed feedback
3. Add response headers to all endpoints
4. Test rate limiting behavior

### Phase 2: Frontend Integration (2 hours)
1. Update error handling in WorkflowContext
2. Create RateLimitNotice component
3. Integrate rate limit UI into HeroSection
4. Add proper TypeScript types for rate limit data

### Phase 3: Testing & Polish (1 hour)
1. Test full rate limit flow
2. Verify countdown timer accuracy
3. Ensure proper error recovery
4. Add unit tests for new functionality

## Success Metrics
1. Users understand when rate limited (clear messaging)
2. Users know exactly when they can retry (countdown timer)
3. Reduced confusion and support requests
4. Improved user retention after hitting limits

## Future Enhancements
1. **Authenticated Users**: Higher limits for registered users
2. **Persistent Storage**: Use Redis to maintain limits across restarts
3. **Rate Limit Dashboard**: Show usage history and patterns
4. **Flexible Limits**: Different limits for different endpoints
5. **Grace Period**: Allow one extra request with warning

## Technical Considerations
1. **Time Zones**: All times in UTC internally, display in user's local time
2. **Clock Drift**: Handle slight time differences between client/server
3. **Performance**: Minimal overhead for rate limit checks
4. **Security**: Prevent rate limit bypass attempts

## Conclusion
This implementation provides a significantly improved user experience when rate limits are reached, turning a frustrating error into a clear, actionable notification with precise timing information.