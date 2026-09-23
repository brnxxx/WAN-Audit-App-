import unittest
from unittest.mock import patch

from app.schemas import DeviceCreate, DeviceUpdate, InterfaceCreate
from app.services.gns3_service import (
    GNS3ServiceError,
    _infer_device_type,
    _infer_status,
    _match_site_or_backbone,
    execute_router_command,
    ping_host,
)


class FakeEntity:
    def __init__(self, entity_id: int, name: str):
        self.id = entity_id
        self.name = name


class CoreBehaviorTests(unittest.TestCase):
    def test_gns3_mapping_is_case_and_separator_insensitive(self):
        site_id, backbone_id = _match_site_or_backbone(
            "RTR_SITE-Paris_01",
            [FakeEntity(7, "Site Paris")],
            [FakeEntity(9, "CORE")],
        )
        self.assertEqual(site_id, 7)
        self.assertIsNone(backbone_id)

    def test_gns3_type_and_status_mapping(self):
        self.assertEqual(_infer_device_type("dynamips", "EDGE-01"), "router")
        self.assertEqual(_infer_device_type("qemu", "Main Firewall"), "firewall")
        self.assertEqual(_infer_status("started"), "online")
        self.assertEqual(_infer_status("unexpected"), "unknown")

    def test_device_creation_requires_exactly_one_location(self):
        with self.assertRaises(ValueError):
            DeviceCreate(name="r1", device_type="router")
        with self.assertRaises(ValueError):
            DeviceCreate(name="r1", device_type="router", site_id=1, backbone_id=2)

    def test_device_update_can_clear_location_but_not_duplicate_it(self):
        self.assertIsNone(DeviceUpdate(name="r1", device_type="router").site_id)
        with self.assertRaises(ValueError):
            DeviceUpdate(name="r1", device_type="router", site_id=1, backbone_id=2)

    def test_interface_status_is_validated(self):
        with self.assertRaises(ValueError):
            InterfaceCreate(device_id=1, name="eth0", status="broken")

    @patch("app.services.gns3_service.subprocess.run")
    def test_ping_returns_structured_metrics(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = (
            "4 packets transmitted, 4 received, 0% packet loss\n"
            "rtt min/avg/max/mdev = 1.200/4.500/9.800/1.000 ms\n"
        )
        run.return_value.stderr = ""
        result = ping_host("192.0.2.1", 4)
        self.assertTrue(result["reachable"])
        self.assertEqual(result["packets_received"], 4)
        self.assertEqual(result["packet_loss_percent"], 0)
        self.assertEqual(result["latency_avg_ms"], 4.5)

    @patch("app.services.gns3_service.ConnectHandler")
    @patch("app.services.gns3_service.get_project_node")
    def test_ping_from_gns3_node_uses_console_and_parses_cisco_output(self, get_node, connect):
        get_node.return_value = {
            "name": "R1",
            "console_host": "127.0.0.1",
            "console": 5001,
        }
        connection = connect.return_value
        connection.send_command_timing.return_value = (
            "Success rate is 100 percent (4/4), round-trip min/avg/max = 1/4/9 ms"
        )
        result = ping_host("10.0.0.2", 4, "project-1", "node-1")
        connect.assert_called_once()
        connection.send_command_timing.assert_called_once_with(
            "ping 10.0.0.2 repeat 4", read_timeout=15
        )
        self.assertEqual(result["source"], "R1")
        self.assertEqual(result["packets_received"], 4)
        self.assertEqual(result["latency_avg_ms"], 4.0)

    @patch("app.services.gns3_service._run_from_node")
    @patch("app.services.gns3_service.get_project_node")
    def test_router_command_requires_allowed_cisco_read_only_command(self, get_node, run_node):
        get_node.return_value = {"name": "R1", "node_type": "dynamips"}
        run_node.return_value = ("GigabitEthernet0/0 is up", "R1")
        result = execute_router_command("project-1", "node-1", "show ip interface brief")
        run_node.assert_called_once_with("project-1", "node-1", "show ip interface brief")
        self.assertEqual(result["source"], "R1")
        with self.assertRaises(GNS3ServiceError):
            execute_router_command("project-1", "node-1", "configure terminal")


if __name__ == "__main__":
    unittest.main()
