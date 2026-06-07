ERROR_MARKERS = (
    "shutdown",
    "adc out of range",
    "lost communication",
    "timer too close",
    "error",
    "failed",
)

WARNING_MARKERS = (
    "warning",
    "warn",
    "deprecated",
)

CLASSIFICATION_MARKERS = (
    ("adc out of range", "adc"),
    ("thermal", "thermal"),
    ("heater", "heater"),
    ("mcu", "mcu"),
    ("canbus", "canbus"),
    (" can ", "canbus"),
    ("probe", "probe"),
    ("endstop", "endstop"),
    ("serial", "serial"),
    ("timer too close", "timer"),
    ("firmware_restart", "firmware_restart"),
    ("restart", "firmware_restart"),
    ("shutdown", "shutdown"),
    ("disconnected", "disconnect"),
    ("lost communication", "disconnect"),
    ("ready", "reconnect"),
)


def classify_message(message: str) -> str:
    normalized = f" {message.lower()} "
    for marker, classification in CLASSIFICATION_MARKERS:
        if marker in normalized:
            return classification
    return "normal"


def level_for_message(message: str, classification: str) -> str:
    normalized = message.lower()
    if classification in {"shutdown", "disconnect", "adc", "thermal", "heater", "mcu", "timer"}:
        return "error"
    if any(marker in normalized for marker in ERROR_MARKERS):
        return "error"
    if any(marker in normalized for marker in WARNING_MARKERS):
        return "warning"
    return "info"
