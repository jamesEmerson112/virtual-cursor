#!/usr/bin/env python3
"""
Validation script for .env configuration in the virtual cursor project.
Tests Emotiv API credentials, profile access, and headset connectivity.
"""

import os
import sys
import json
import time
import websocket
import ssl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EnvironmentValidator:
    def __init__(self):
        self.client_id = os.getenv("CLIENT_ID", "")
        self.client_secret = os.getenv("CLIENT_SECRET", "")
        self.profile_name = os.getenv("PROFILE_NAME", "")
        self.headset_id = os.getenv("HEADSET_ID", "")

        self.results = {
            "env_loaded": False,
            "cortex_service": False,
            "credentials_valid": False,
            "authorization": False,
            "headset_detection": False,
            "profile_management": False
        }

        self.ws = None
        self.auth_token = None
        self.request_id = 1

    def validate_environment_variables(self):
        """Check if all required environment variables are present."""
        print("🔍 Validating Environment Variables...")

        missing_vars = []
        if not self.client_id:
            missing_vars.append("CLIENT_ID")
        if not self.client_secret:
            missing_vars.append("CLIENT_SECRET")
        if not self.profile_name:
            missing_vars.append("PROFILE_NAME")

        if missing_vars:
            print(f"❌ Missing required variables: {', '.join(missing_vars)}")
            return False

        print(f"✅ CLIENT_ID: {self.client_id[:10]}...")
        print(f"✅ CLIENT_SECRET: {self.client_secret[:10]}...")
        print(f"✅ PROFILE_NAME: {self.profile_name}")
        print(f"✅ HEADSET_ID: {'(empty - will auto-detect)' if not self.headset_id else self.headset_id}")

        self.results["env_loaded"] = True
        return True

    def test_cortex_service_connectivity(self):
        """Test if Cortex service is running and accessible."""
        print("\n🔍 Testing Cortex Service Connectivity...")

        try:
            # Try to connect to Cortex WebSocket
            url = "wss://localhost:6868"
            self.ws = websocket.create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE}, timeout=5)
            print("✅ Successfully connected to Cortex service at localhost:6868")

            # Test basic API call - getCortexInfo
            info_request = {
                "jsonrpc": "2.0",
                "method": "getCortexInfo",
                "id": self.request_id
            }
            self.request_id += 1

            self.ws.send(json.dumps(info_request))
            response = json.loads(self.ws.recv())

            if "result" in response:
                print(f"✅ Cortex API Version: {response['result'].get('apiVersion', 'Unknown')}")
                print(f"✅ Server Version: {response['result'].get('serverVersion', 'Unknown')}")
                self.results["cortex_service"] = True
                return True
            else:
                print(f"❌ Unexpected response: {response}")
                return False

        except Exception as e:
            print(f"❌ Failed to connect to Cortex service: {e}")
            print("   Make sure EMOTIV Launcher is running and Cortex service is started")
            return False

    def test_credentials_and_authorization(self):
        """Test API credentials and authorization flow."""
        print("\n🔍 Testing API Credentials and Authorization...")

        if not self.ws:
            print("❌ No WebSocket connection available")
            return False

        try:
            # Test hasAccessRight
            access_request = {
                "jsonrpc": "2.0",
                "method": "hasAccessRight",
                "params": {
                    "clientId": self.client_id,
                    "clientSecret": self.client_secret
                },
                "id": self.request_id
            }
            self.request_id += 1

            self.ws.send(json.dumps(access_request))
            response = json.loads(self.ws.recv())

            if "error" in response:
                print(f"❌ Access right check failed: {response['error']['message']}")
                print("   Check if CLIENT_ID and CLIENT_SECRET are valid")
                return False

            access_granted = response["result"]["accessGranted"]
            print(f"✅ Access granted: {access_granted}")

            if not access_granted:
                print("⚠️  Access not granted - attempting to request access...")
                # Request access
                request_access = {
                    "jsonrpc": "2.0",
                    "method": "requestAccess",
                    "params": {
                        "clientId": self.client_id,
                        "clientSecret": self.client_secret
                    },
                    "id": self.request_id
                }
                self.request_id += 1

                self.ws.send(json.dumps(request_access))
                response = json.loads(self.ws.recv())

                if "error" in response:
                    print(f"❌ Request access failed: {response['error']['message']}")
                    return False

                print("✅ Access requested - may need manual approval in EMOTIV Launcher")

            # Attempt authorization
            auth_request = {
                "jsonrpc": "2.0",
                "method": "authorize",
                "params": {
                    "clientId": self.client_id,
                    "clientSecret": self.client_secret
                },
                "id": self.request_id
            }
            self.request_id += 1

            self.ws.send(json.dumps(auth_request))
            response = json.loads(self.ws.recv())

            if "error" in response:
                print(f"❌ Authorization failed: {response['error']['message']}")
                if response['error']['code'] == -32003:
                    print("   This usually means access needs to be granted in EMOTIV Launcher")
                return False

            self.auth_token = response["result"]["cortexToken"]
            print("✅ Authorization successful - cortexToken obtained")
            self.results["credentials_valid"] = True
            self.results["authorization"] = True
            return True

        except Exception as e:
            print(f"❌ Authorization test failed: {e}")
            return False

    def test_headset_detection(self):
        """Test headset detection and connection."""
        print("\n🔍 Testing Headset Detection...")

        if not self.auth_token:
            print("❌ No authorization token available")
            return False

        try:
            # Query headsets
            headset_request = {
                "jsonrpc": "2.0",
                "method": "queryHeadsets",
                "params": {},
                "id": self.request_id
            }
            self.request_id += 1

            self.ws.send(json.dumps(headset_request))
            response = json.loads(self.ws.recv())

            if "error" in response:
                print(f"❌ Headset query failed: {response['error']['message']}")
                return False

            headsets = response["result"]
            print(f"✅ Found {len(headsets)} headset(s)")

            if len(headsets) == 0:
                print("⚠️  No headsets detected")
                print("   Make sure your EMOTIV headset is turned on and paired")
                return False

            for i, headset in enumerate(headsets):
                print(f"   Headset {i+1}: {headset['id']}")
                print(f"     Status: {headset['status']}")
                print(f"     Connected by: {headset.get('connectedBy', 'N/A')}")
                if 'settings' in headset:
                    print(f"     Settings: {headset['settings']}")

            # Check if any headset is connected
            connected_headsets = [h for h in headsets if h['status'] == 'connected']
            if connected_headsets:
                print(f"✅ {len(connected_headsets)} headset(s) connected and ready")
                self.results["headset_detection"] = True
                return True
            else:
                print("⚠️  No headsets are currently connected")
                print("   You may need to connect your headset through EMOTIV Launcher")
                return False

        except Exception as e:
            print(f"❌ Headset detection test failed: {e}")
            return False

    def test_profile_management(self):
        """Test profile creation and management."""
        print("\n🔍 Testing Profile Management...")

        if not self.auth_token:
            print("❌ No authorization token available")
            return False

        try:
            # Query existing profiles
            profile_request = {
                "jsonrpc": "2.0",
                "method": "queryProfile",
                "params": {
                    "cortexToken": self.auth_token
                },
                "id": self.request_id
            }
            self.request_id += 1

            self.ws.send(json.dumps(profile_request))
            response = json.loads(self.ws.recv())

            if "error" in response:
                print(f"❌ Profile query failed: {response['error']['message']}")
                return False

            profiles = response["result"]
            profile_names = [p.get('name', 'Unknown') for p in profiles]
            print(f"✅ Found {len(profiles)} existing profile(s): {profile_names}")

            # Check if our target profile exists
            target_exists = self.profile_name in profile_names
            print(f"✅ Target profile '{self.profile_name}' exists: {target_exists}")

            if not target_exists:
                print(f"⚠️  Profile '{self.profile_name}' does not exist")
                print("   The application will attempt to create it when needed")

            self.results["profile_management"] = True
            return True

        except Exception as e:
            print(f"❌ Profile management test failed: {e}")
            return False

    def test_complete_integration(self):
        """Test if mouse_demo.py can initialize properly."""
        print("\n🔍 Testing Complete Integration...")

        try:
            # Import the cortex module to test if it initializes
            from cortex import Cortex

            print("✅ Cortex module imports successfully")

            # Try to create a Cortex instance (don't connect)
            cortex_instance = Cortex(self.client_id, self.client_secret, debug_mode=False)
            print("✅ Cortex instance creation successful")

            return True

        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            return False

    def cleanup(self):
        """Clean up WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass

    def run_full_validation(self):
        """Run complete validation suite."""
        print("=" * 60)
        print("🧪 EMOTIV Environment Validation Suite")
        print("=" * 60)

        try:
            # Step 1: Environment variables
            if not self.validate_environment_variables():
                return self.print_final_results()

            # Step 2: Cortex service connectivity
            if not self.test_cortex_service_connectivity():
                return self.print_final_results()

            # Step 3: Credentials and authorization
            if not self.test_credentials_and_authorization():
                return self.print_final_results()

            # Step 4: Headset detection
            self.test_headset_detection()  # Don't fail on this

            # Step 5: Profile management
            self.test_profile_management()  # Don't fail on this

            # Step 6: Integration test
            self.test_complete_integration()

        finally:
            self.cleanup()

        return self.print_final_results()

    def print_final_results(self):
        """Print final validation results and recommendations."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS")
        print("=" * 60)

        passed = sum(self.results.values())
        total = len(self.results)

        for test, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test.replace('_', ' ').title()}: {status}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed! Your .env configuration should work correctly.")
            return True
        else:
            print("\n⚠️  Some tests failed. Recommendations:")

            if not self.results["cortex_service"]:
                print("• Start EMOTIV Launcher and ensure Cortex service is running")

            if not self.results["credentials_valid"]:
                print("• Verify CLIENT_ID and CLIENT_SECRET are correct")
                print("• Check if the app needs approval in EMOTIV Launcher")

            if not self.results["headset_detection"]:
                print("• Turn on your EMOTIV headset")
                print("• Pair the headset through EMOTIV Launcher")
                print("• Ensure the headset is connected")

            if not self.results["profile_management"]:
                print("• Profile creation may be restricted")
                print("• Check permissions in EMOTIV Launcher")

            return False

def main():
    """Main function to run validation."""
    validator = EnvironmentValidator()
    success = validator.run_full_validation()

    print("\n" + "=" * 60)
    if success:
        print("🚀 Ready to run mouse_demo.py!")
    else:
        print("🔧 Please resolve the issues above before running mouse_demo.py")
    print("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
