"""Windows master volume control via pycaw (Core Audio)."""
from __future__ import annotations

def _get_endpoint():
    from pycaw.pycaw import AudioUtilities
    device = AudioUtilities.GetSpeakers()
    return device.EndpointVolume

def set_volume(percent: int):
    percent = max(0, min(100, int(percent)))
    endpoint = _get_endpoint()
    endpoint.SetMasterVolumeLevelScalar(percent / 100.0, None)
    if percent > 0:
        endpoint.SetMute(0, None)
    return f"Ses yüzde {percent} olarak ayarlandı."

def set_mute(muted: bool):
    endpoint = _get_endpoint()
    endpoint.SetMute(1 if muted else 0, None)
    return "Ses kapatıldı." if muted else "Ses açıldı."
