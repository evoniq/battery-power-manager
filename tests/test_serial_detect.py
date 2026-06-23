from ecoflow_tray.adapters.serial_detect import (
    SerialPortInfo,
    find_ecoflow_ports,
    list_serial_ports,
    pick_port,
)


ECOFLOW_VID = 0x3746
ECOFLOW_PID = 0xFFFF


def _ports():
    return [
        SerialPortInfo(device="COM3", description="Prolific USB-to-Serial", vid=0x067B, pid=0x2303),
        SerialPortInfo(device="COM7", description="USB Serial Device", vid=ECOFLOW_VID, pid=ECOFLOW_PID),
        SerialPortInfo(device="COM9", description="Other", vid=ECOFLOW_VID, pid=ECOFLOW_PID),
    ]


def test_find_ecoflow_ports_filters_by_vid_pid():
    found = find_ecoflow_ports(_ports(), ECOFLOW_VID, ECOFLOW_PID)
    assert [p.device for p in found] == ["COM7", "COM9"]


def test_pick_port_prefers_hint_when_match():
    p = pick_port(_ports(), ECOFLOW_VID, ECOFLOW_PID, hint="COM9")
    assert p is not None and p.device == "COM9"


def test_pick_port_falls_back_to_first_vid_pid_match():
    p = pick_port(_ports(), ECOFLOW_VID, ECOFLOW_PID, hint="COM42")
    assert p is not None and p.device == "COM7"


def test_pick_port_returns_none_when_no_match():
    only_prolific = [_ports()[0]]
    assert pick_port(only_prolific, ECOFLOW_VID, ECOFLOW_PID) is None


def test_list_serial_ports_safe_without_pyserial():
    # Whether or not pyserial is installed, this must return a list (possibly empty)
    # and never raise.
    result = list_serial_ports()
    assert isinstance(result, list)
