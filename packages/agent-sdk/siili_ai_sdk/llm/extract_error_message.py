import json


def extract_error_message(exception: Exception) -> str:
    """Extract a meaningful error message from various exception types."""
    error_str = str(exception)

    # Try to parse as JSON if it looks like a structured error
    if "Error code:" in error_str and "{" in error_str:
        try:
            # Extract JSON part from the error string
            json_start = error_str.find("{")
            json_part = error_str[json_start:]
            error_data = json.loads(json_part)

            # Handle Azure OpenAI content filter errors
            if "error" in error_data:
                error_info = error_data["error"]
                if error_info.get("code") == "content_filter":
                    return f"Content filtered: {error_info.get('message', 'Content policy violation')}"
                else:
                    return error_info.get("message", error_str)
        except (json.JSONDecodeError, KeyError):
            pass

    # Handle other common error patterns
    if "content management policy" in error_str.lower():
        return "Content was filtered due to content management policy"
    elif "rate limit" in error_str.lower():
        return "Rate limit exceeded"
    elif "authentication" in error_str.lower():
        return "Authentication failed"
    elif "quota" in error_str.lower():
        return "Quota exceeded"

    # Return the original error message if no specific pattern matches
    return error_str
