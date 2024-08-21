import os


class ApplicationNotFound(Exception):
    def __init__(self, application_name: str, applications_found: list[str]):
        super().__init__(
            f"Could not find any sound application named '{application_name}'. Available applications names are: {', '.join(applications_found)}."
        )


def set_application_volume_win(application: str, volume: float):
    from pycaw.pycaw import AudioUtilities

    sessions = [
        session for session in AudioUtilities.GetAllSessions() if session.Process
    ]

    try:
        session = next(
            session
            for session in sessions
            if application.lower() in session.Process.name().lower()
        )

        volume = session.SimpleAudioVolume
        min_vol, max_vol = volume.GetVolumeRange()
        volume_level = volume * (max_vol - min_vol) + min_vol
        volume.SetMasterVolumeLevel(volume_level, None)

    except StopIteration:
        applications_found = [session.Process.name() for session in sessions]
        raise ApplicationNotFound(application, applications_found) from None


def set_application_volume_posix(application: str, volume: float) -> float:
    from pulsectl import Pulse

    with Pulse("set-application-volume") as pulse:
        sinks = pulse.sink_input_list()

        try:
            sink = next(
                sink for sink in sinks if application.lower() in sink.name.lower()
            )

            volume_struct = sink.volume
            volume_struct.value_flat = volume
            pulse.volume_set(sink, volume_struct)

        except StopIteration:
            applications_found = [sink.name for sink in sinks]
            raise ApplicationNotFound(application, applications_found) from None


if os.name == "nt":
    set_application_volume = set_application_volume_posix
elif os.name == "posix":
    set_application_volume = set_application_volume_posix
else:
    msg = f"Unsupported operating system: '{os.name}'."
    raise ImportError(msg)
