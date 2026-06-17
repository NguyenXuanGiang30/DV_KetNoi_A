import unittest
import sys
from pathlib import Path

# Mock .env content for testing
MOCK_ENV_CONTENT = """# Smart Campus Config
AI_VISION_URL=http://ai-vision:8000
ACCESS_GATE_URL=http://access-gate:8000
NOTIFICATION_URL=http://notification:8000
AUTH_TOKEN=dev-token-2026
"""

class TestConfigureLan(unittest.TestCase):
    def setUp(self):
        self.temp_env = Path("scratch/temp_env.env")
        self.temp_env.write_text(MOCK_ENV_CONTENT, encoding="utf-8")

    def tearDown(self):
        if self.temp_env.exists():
            self.temp_env.unlink()

    def test_update_env_ip(self):
        # Test updating URLs in the env file content
        content = self.temp_env.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        updated_lines = []
        target_ip = "26.12.34.56"
        services = {
            "AI_VISION_URL": 8004,
            "ACCESS_GATE_URL": 8003,
            "NOTIFICATION_URL": 8007
        }
        
        for line in lines:
            updated = False
            for key, port in services.items():
                if line.startswith(f"{key}="):
                    updated_lines.append(f"{key}=http://{target_ip}:{port}")
                    updated = True
                    break
            if not updated:
                updated_lines.append(line)
                
        new_content = "\n".join(updated_lines) + "\n"
        self.temp_env.write_text(new_content, encoding="utf-8")
        
        # Verify changes
        verified_content = self.temp_env.read_text(encoding="utf-8")
        self.assertIn("AI_VISION_URL=http://26.12.34.56:8004", verified_content)
        self.assertIn("ACCESS_GATE_URL=http://26.12.34.56:8003", verified_content)
        self.assertIn("NOTIFICATION_URL=http://26.12.34.56:8007", verified_content)
        self.assertIn("AUTH_TOKEN=dev-token-2026", verified_content)

if __name__ == "__main__":
    unittest.main()
