import warnings
from typing import Any, Dict

from langchain_core.load import dumpd, load
from langchain_core.messages.base import BaseMessage


def serialize_token_data(token_data: Any) -> Dict[str, Any]:
    """Serialize token data that may contain LangChain objects."""
    try:
        # Try to serialize using LangChain's built-in serialization
        return dumpd(token_data)
    except Exception:
        # Fallback: handle individual components
        if isinstance(token_data, dict):
            serialized = {}
            for key, value in token_data.items():
                try:
                    serialized[key] = dumpd(value)
                except Exception:
                    # For non-serializable values, convert to string representation
                    if isinstance(value, BaseMessage):
                        serialized[key] = {
                            "type": "langchain_message_fallback",
                            "message_type": value.type,
                            "content": value.content,
                            "additional_kwargs": value.additional_kwargs,
                            "id": value.id,
                            "name": getattr(value, "name", None),
                        }
                    else:
                        serialized[key] = {"type": "fallback", "data": str(value)}
            return serialized
        else:
            # For non-dict objects, try to convert to string
            return {"type": "fallback", "data": str(token_data)}


def deserialize_token_data(data: Dict[str, Any]) -> Any:
    """Deserialize token data that may contain LangChain objects."""
    try:
        # Try LangChain's built-in deserialization
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*is in beta.*")
            return load(data)
    except Exception:
        # Fallback: handle individual components
        if isinstance(data, dict):
            deserialized = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    try:
                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", message=".*is in beta.*")
                            deserialized[key] = load(value)
                    except Exception:
                        # Check for fallback message format
                        if value.get("type") == "langchain_message_fallback":
                            # Reconstruct basic message info (will lose some functionality)
                            deserialized[key] = {
                                "type": value["message_type"],
                                "content": value["content"],
                                "additional_kwargs": value.get("additional_kwargs", {}),
                                "id": value.get("id"),
                                "name": value.get("name"),
                            }
                        elif value.get("type") == "fallback":
                            deserialized[key] = value["data"]
                        else:
                            deserialized[key] = value
                else:
                    deserialized[key] = value
            return deserialized
        else:
            return data


def ensure_json_serializable(obj: Any) -> Any:
    """Ensure an object is JSON serializable by converting problematic types."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {k: ensure_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]
    else:
        # Convert other types to string
        return str(obj)
