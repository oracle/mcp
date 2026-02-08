# OCI Service Limits and Quota Policies MCP Server

A Python-based Model Context Protocol (MCP) server that provides **read-only access** to Oracle Cloud Infrastructure (OCI) service limits and quota policies. Query resource limits, quotas, and availability information across OCI services and regions using natural language.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Valid OCI configuration
- uv package manager (recommended) or Docker/Podman

### Install and Run
```bash
# Clone and navigate
cd /path/to/oci_limits_mcp_server

# Install dependencies
uv sync

# Run the server
uv run python oci_limits_mcp_server.py
```

## 🛠️ Available MCP Tools

The server provides 10 MCP tools for querying OCI limits and quotas:

### Service Limits Tools
1. **`list_supported_services()`** - List all OCI services with configurable limits
2. **`list_service_limits(service_name, compartment_name?, availability_domain?, limit_name?)`** - Get all limits for a service
3. **`get_service_limit(service_name, limit_name, compartment_name?, availability_domain?)`** - Get specific limit details
4. **`check_service_limits_by_region(service_name, region, compartment_name?)`** - Check limits in a specific region

### Quota Policy Tools
5. **`list_quota_policies(compartment_name?)`** - List all quota policies in a compartment
6. **`get_quota_policy(quota_name, compartment_name?)`** - Get detailed quota policy information

### Resource Discovery Tools
7. **`list_all_compartments()`** - List all compartments in your tenancy
8. **`list_availability_domains(compartment_name?)`** - List availability domains
9. **`get_resource_availability(service_name, resource_type, compartment_name?, availability_domain?)`** - Check resource availability

### Utility Tools
10. **`ping()`** - Health check endpoint

## 📋 Setup Methods

## Method 1: Using uv (Recommended)

### Install uv
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
pip install uv
```

### Setup and Run
```bash
# Navigate to the server directory
cd /Users/your-username/path/to/oracle_mcp/src/oci_limits_mcp_server

# Install dependencies
uv sync --dev

# Test the server
uv run python oci_limits_mcp_server.py --help

# Run with specific OCI profile
PROFILE_NAME=YOUR_PROFILE uv run python oci_limits_mcp_server.py

# Run tests
uv run python -m pytest test_oci_limits_mcp_server.py -v
```

## Method 2: Using Docker/Podman

### Build Container
```bash
# Navigate to server directory
cd /Users/your-username/path/to/oracle_mcp/src/oci_limits_mcp_server

# Build with Docker
docker build -t oci-limits-mcp:latest .

# Or build with Podman
podman build -t oci-limits-mcp:latest .
```

### Run Container
```bash
# Run without OCI config (will show warnings but work for testing)
podman run --rm -it oci-limits-mcp:latest

# Run with OCI config mounted
podman run --rm -it \
  -v ~/.oci:/home/oci/.oci:ro \
  -e PROFILE_NAME=YOUR_PROFILE \
  oci-limits-mcp:latest
```

## 🔧 OCI Configuration

### 1. Create OCI Config Directory
```bash
mkdir -p ~/.oci
chmod 700 ~/.oci
```

### 2. Create OCI Config File (`~/.oci/config`)
```ini
[DEFAULT]
user=ocid1.user.oc1..your_user_ocid
fingerprint=aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99:00:aa:bb:cc:dd
key_file=~/.oci/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..your_tenancy_ocid
region=us-ashburn-1

[DEV]
user=ocid1.user.oc1..your_dev_user_ocid
fingerprint=bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99:00:aa:bb:cc:dd:ee
key_file=~/.oci/oci_api_key_dev.pem
tenancy=ocid1.tenancy.oc1..your_dev_tenancy_ocid
region=us-phoenix-1
```

### 3. Set Key File Permissions
```bash
chmod 600 ~/.oci/oci_api_key.pem
```

### 4. Required OCI IAM Permissions
```
Allow group <your-group> to read limits in tenancy
Allow group <your-group> to read quotas in tenancy
Allow group <your-group> to read compartments in tenancy
Allow group <your-group> to read availability-domains in tenancy
```

## 🔌 Integration Methods

## Integration 1: VS Code with GitHub Copilot

### Setup Steps:
1. **Open VS Code Settings JSON:**
   - Press `Cmd+Shift+P` → "Preferences: Open User Settings (JSON)"

2. **Add MCP Configuration:**
```json
{
  "github.copilot.chat.mcp.servers": {
    "oci-limits": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/Users/your-username/path/to/oracle_mcp/src/oci_limits_mcp_server",
        "python",
        "oci_limits_mcp_server.py"
      ],
      "env": {
        "PROFILE_NAME": "DEFAULT"
      }
    }
  }
}
```

3. **Restart VS Code**

4. **Test with GitHub Copilot:**
   - Open Copilot Chat (`Cmd+Shift+P` → "GitHub Copilot: Open Chat")
   - Try: "What are my OCI compute limits in us-ashburn-1?"

## Integration 2: Claude Desktop

### Setup Steps:
1. **Create/Edit Claude Config:**
```bash
# Create config file
mkdir -p ~/Library/Application\ Support/Claude
```

2. **Add Configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "oci-limits": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/Users/your-username/path/to/oracle_mcp/src/oci_limits_mcp_server",
        "python",
        "oci_limits_mcp_server.py"
      ],
      "env": {
        "PROFILE_NAME": "DEFAULT"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Test in Claude:**
   - Ask: "Show me my OCI service limits"
   - Ask: "What quota policies do I have?"

## Integration 3: Cline Extension

### Setup Steps:
1. **Install Cline Extension:**
```bash
code --install-extension saoudrizwan.claude-dev
```

2. **The MCP config should already exist at:**
```
/Users/your-username/path/to/oracle_mcp/.vscode/mcp.json
```

3. **Test with Cline:**
   - Open Cline panel in VS Code
   - Ask: "Can you check my OCI compute limits?"
   - Ask: "What are my quota policies in the Dev compartment?"

## 📝 Testing

### Run the Test Suite
```bash
cd /Users/your-username/path/to/oracle_mcp/src/oci_limits_mcp_server

# Run all tests
uv run python -m pytest test_oci_limits_mcp_server.py -v

# Run with coverage
uv run python -m pytest test_oci_limits_mcp_server.py --cov=oci_limits_mcp_server
```

### Test Different Profiles
```bash
# Test with specific profile
PROFILE_NAME=DEV uv run python oci_limits_mcp_server.py

# Test import
uv run python -c "import oci_limits_mcp_server; print('Import successful')"
```

## 💬 Example Queries

### Service Limits Queries
- "What compute limits do I have in us-ashburn-1?"
- "Show me all block storage limits"
- "What's the maximum number of VCNs I can create?"
- "List all services that have configurable limits"

### Quota Policy Queries
- "Show me all quota policies in my tenancy"
- "What are the quota statements for my compute quota?"
- "Am I close to any quota limits in my Dev compartment?"

### Resource Availability Queries
- "What compute shapes are available in AD-1?"
- "Show me availability domains in us-phoenix-1"
- "Check resource availability for block storage"

## 📊 Example Responses

### Service Limits Response
```json
{
  "service": "compute",
  "total_limits": 15,
  "limits": [
    {
      "service_name": "compute",
      "name": "standard-a1-core-count", 
      "description": "Number of A1 cores",
      "value": 1000,
      "scope_type": "AD",
      "availability_domain": "Uocm:US-ASHBURN-AD-1",
      "compartment_name": "root"
    }
  ]
}
```

### Quota Policy Response
```json
{
  "id": "ocid1.quota.oc1..example",
  "name": "compute-quota",
  "description": "Quota for compute resources", 
  "compartment_name": "Dev",
  "lifecycle_state": "ACTIVE",
  "statements": [
    "set compute quota standard-a1-core-count to 500 in compartment Dev"
  ]
}
```

## 🔧 Troubleshooting

### Common Issues

#### "MCP Server Not Connecting"
- Verify file paths in configuration are absolute and correct
- Ensure `uv` is installed: `uv --version`
- Check OCI configuration: `uv run python -c "import oci; print('OCI SDK works')"`

#### "Profile Not Found"
- Check profile exists: `cat ~/.oci/config`
- Verify profile name spelling (case-sensitive)
- Test with: `PROFILE_NAME=YOUR_PROFILE uv run python oci_limits_mcp_server.py`

#### "Permission Errors"
- Check key file permissions: `ls -la ~/.oci/`
- Verify IAM permissions in OCI Console
- Test OCI CLI: `oci iam user get --user-id <your-user-ocid>`

### Debug Mode
```bash
# Enable debug logging
export MCP_DEBUG=1
export OCI_PYTHON_SDK_DEBUG=1
PROFILE_NAME=YOUR_PROFILE uv run python oci_limits_mcp_server.py
```

## 🔒 Security Notes

- **Read-only access**: Only performs read operations on OCI APIs
- **No credential storage**: Uses standard OCI SDK configuration
- **Stateless**: No data persistence or storage
- **Principle of least privilege**: Only requires read permissions

## 📜 License

Copyright (c) 2025, Oracle and/or its affiliates.  
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
