from pulsectl import Pulse


def set_application_volume(application: str, volume: float) -> float:
    with Pulse("set-application-volume") as pulse:
        sinks = pulse.sink_input_list()

        try:
            sink = next(
                sink for sink in sinks if application.lower() in sink.name.lower()
            )

            volume_struct = sink.volume
            previous_volume = volume_struct.value_flat
            volume_struct.value_flat = volume

            pulse.volume_set(sink, volume_struct)
            return previous_volume

        except StopIteration as e:
            raise ValueError(
                f"Application name `{application}` was not found in {sinks}"
            ) from e
