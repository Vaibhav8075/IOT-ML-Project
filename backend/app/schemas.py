from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TelemetryIn(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    zone_id: str = Field(min_length=1, max_length=64)
    timestamp: datetime
    temperature_c: float
    humidity_pct: float
    pm25: float
    co_adc: float
    flame_channels: list[int] = Field(min_length=5, max_length=5)
    pir_motion: int = Field(ge=0, le=1)
    ldr_raw: float
    ldr_flicker: float

    @field_validator("humidity_pct")
    @classmethod
    def validate_humidity(cls, value):
        if value < 0 or value > 100:
            raise ValueError("humidity_pct must be between 0 and 100")
        return value

    @field_validator("flame_channels")
    @classmethod
    def validate_flame_channels(cls, value):
        if any(channel not in (0, 1) for channel in value):
            raise ValueError("flame_channels must contain only 0 or 1")
        return value


class TelemetryOut(BaseModel):
    id: int
    device_id: str
    zone_id: str
    timestamp: str
    temperature_c: float
    humidity_pct: float
    pm25: float
    co_adc: float
    flame_channels: list[int]
    pir_motion: int
    ldr_raw: float
    ldr_flicker: float
    predicted_label: str
    confidence: float


class ZoneStatusOut(BaseModel):
    zone_id: str
    device_id: str
    timestamp: str
    predicted_label: str
    confidence: float
    temperature_c: float
    humidity_pct: float
    pm25: float
    co_adc: float
