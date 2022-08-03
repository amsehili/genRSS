import subprocess

try:
    import mutagen

    _MUTAGEN = True
except ImportError:
    _MUTAGEN = False


def _run_command(args):
    """Helper function to run un external program.

    Args:
        args (list): List of arguments. The 1st argument should be program name.

    Returns:
        output (str): Program output.
    """
    try:
        output = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except FileNotFoundError:
        return None
    if output.returncode != 0:
        return None
    return output.stdout.decode("utf-8").strip()


def get_duration_mutagen(filename):
    """Get file duration in seconds using mutagen. If mutagen is not installed
    or media file is not valid, return None.

    Args:
        filename (str): Path to a file.

    Returns:
        duration (int): File duration in seconds or None.
    """
    if _MUTAGEN:
        try:
            file = mutagen.File(filename)
        except mutagen.mp3.HeaderNotFoundError:
            return None
        if file is not None:
            return round(file.info.length)
    return None


def get_duration_sox(filename):
    """Get file duration in seconds using sox. If sox is not installed or media
    file is not valid, return None.

    Args:
        filename (str): Path to a file.

    Returns:
        duration (int): File duration in seconds or None if no duration could
            be exracted.
    """
    duration_str = _run_command(["soxi", "-D", filename])
    if duration_str is not None:
        try:
            return round(float(duration_str))
        except ValueError:
            return None


def get_duration_ffprobe(filename):
    """Get file duration in seconds using ffprobe. If ffprobe is not installed
    or media file is not valid, return None.

    Args:
        filename (str): Path to a file.

    Returns:
        duration (int): File duration in seconds or None if no duration could be
            exracted.
    """
    duration_str = _run_command(
        [
            "ffprobe",
            "-i",
            filename,
            "-show_entries",
            "format=duration",
            "-v",
            "quiet",
            "-of",
            "csv=p=0",
        ]
    )
    if duration_str is not None:
        try:
            return round(float(duration_str))
        except ValueError:
            return None
