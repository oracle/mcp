#!/usr/bin/env python3
"""
Lens API Tool Handlers Module

Contains all individual handler functions for lens API MCP tool operations.
"""

import base64
import json
import logging
import sys
import os
from typing import Sequence, Dict, Any, Optional
from mcp.types import TextContent

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import make_request

# Module-level logger
logger = logging.getLogger("lens-mcp.tool_handlers")

# Ensure this logger inherits the correct log level from environment
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level))
logger.debug(f"🐛 Tool handler logger initialized with level: {log_level}")


async def handle_list_instances(arguments: dict) -> Sequence[TextContent]:
    """Handle list_instances tool call."""
    logger.debug("🏢 Executing list_instances operation")
    
    try:
        logger.info("📡 Making HTTP request to list instances...")
        response = make_request('GET', '/instances/')
        response.raise_for_status()
        
        instances_data = response.json()
        result_text = f"Found {len(instances_data)} instances:\n" + json.dumps(instances_data, indent=2)
        
        logger.info(f"✅ HTTP request successful - Found {len(instances_data)} instances")
        logger.debug(f"📤 Returning response (length: {len(result_text)} chars)")
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"❌ Error in list_instances: {str(e)}")
        return [TextContent(type="text", text=f"Error listing instances: {str(e)}")]

async def handle_get_latest_health_check(arguments: dict) -> Sequence[TextContent]:
    """Handle get_latest_health_check tool call."""
    instance_id = arguments["instance_id"]
    
    logger.debug(f"🩺 Executing get_latest_health_check for instance {instance_id}")
    
    try:
        endpoint = f'/instances/{instance_id}/active-health-check/'
        
        logger.info(f"📡 Making HTTP request to get latest health check for instance {instance_id}...")
        response = make_request('GET', endpoint)
        response.raise_for_status()
        
        health_check_data = response.json()
        
        if not health_check_data:
            result_text = f"No active health checks found for instance {instance_id}"
        else:
            # Extract only the state from the health check data
            state = health_check_data.get('state', 'unknown')
            result_text = f"Latest health check state for instance {instance_id}: {state}"
        
        logger.info(f"✅ Latest health check state retrieved successfully for instance {instance_id}")
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"❌ Error getting latest health check: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                return [TextContent(type="text", text=f"Error getting latest health check: {error_detail}")]
            except:
                return [TextContent(type="text", text=f"Error getting latest health check: {e.response.text}")]
        return [TextContent(type="text", text=f"Error getting latest health check: {str(e)}")]


async def handle_create_health_check(arguments: dict) -> Sequence[TextContent]:
    """Handle create_health_check tool call."""
    instance_id = arguments["instance_id"]
    health_check_type = arguments.get("type", "single_node")
    
    logger.debug(f"🆕 Executing create_health_check for instance {instance_id} with type {health_check_type}")
    
    try:
        endpoint = f'/instances/{instance_id}/active-health-check/'
        payload = {"type": health_check_type}
        
        logger.info(f"📡 Making HTTP request to create health check for instance {instance_id}...")
        response = make_request('POST', endpoint, json=payload)
        response.raise_for_status()
        
        logger.info(f"✅ Health check created successfully for instance {instance_id}")
        return [TextContent(
            type="text",
            text=f"Health check of type {health_check_type} created successfully for instance {instance_id}"
        )]
        
    except Exception as e:
        logger.error(f"❌ Error creating health check: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                return [TextContent(type="text", text=f"Error creating health check: {error_detail}")]
            except:
                return [TextContent(type="text", text=f"Error creating health check: {e.response.text}")]
        return [TextContent(type="text", text=f"Error creating health check: {str(e)}")]


async def handle_get_instance_log(arguments: dict) -> Sequence[TextContent]:
    """Handle get_instance_log tool call."""
    instance_id = arguments["instance_id"]
    
    logger.debug(f"📋 Executing get_instance_log for instance {instance_id}")
    
    try:
        endpoint = f'/instances/{instance_id}/active-health-check/'
        
        logger.info(f"📡 Making HTTP request to get log for instance {instance_id}...")
        response = make_request('GET', endpoint)
        response.raise_for_status()
        
        health_check_data = response.json()
        
        if not health_check_data:
            return [TextContent(type="text", text=f"No active health check found for instance {instance_id}")]
        
        # Process the latest health check and decode any base64 logs
        decoded_logs = []
        
        decoded_logs.append(f"=== Latest Health Check ===")
        decoded_logs.append(f"ID: {health_check_data.get('uuid', 'N/A')}")
        decoded_logs.append(f"State: {health_check_data.get('state', 'N/A')}")
        decoded_logs.append(f"Type: {health_check_data.get('type', 'N/A')}")
        decoded_logs.append(f"Created: {health_check_data.get('created_at', 'N/A')}")
        
        # Check for base64 encoded logs 
        log_found = False
        if 'log' in health_check_data and health_check_data['log']:
            try:
                decoded_text = base64.b64decode(health_check_data['log']).decode('utf-8')
                
                # Split into lines and get the last 100 lines
                log_lines = decoded_text.splitlines()
                if len(log_lines) > 100:
                    log_lines = log_lines[-100:]
                    decoded_logs.append(f"\n--- Decoded log (last 100 lines of {len(decoded_text.splitlines())} total) ---")
                else:
                    decoded_logs.append(f"\n--- Decoded log (all {len(log_lines)} lines) ---")
                
                decoded_logs.append('\n'.join(log_lines))
                log_found = True
            except Exception as decode_error:
                decoded_logs.append(f"\n--- Raw {'log'} (failed to decode) ---")
                decoded_logs.append(str(health_check_data['log']))
                logger.warning(f"Failed to decode {'log'}: {str(decode_error)}")
                log_found = True

        if not log_found:
            decoded_logs.append("\n--- No log data found ---")
        
        result_text = f"Retrieved and decoded latest log for instance {instance_id}:\n\n" + "\n".join(decoded_logs)
        
        logger.info(f"✅ Instance log retrieved and decoded successfully for instance {instance_id}")
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"❌ Error getting instance logs: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                return [TextContent(type="text", text=f"Error getting instance logs: {error_detail}")]
            except:
                return [TextContent(type="text", text=f"Error getting instance logs: {e.response.text}")]
        return [TextContent(type="text", text=f"Error getting instance logs: {str(e)}")]


async def handle_get_monitoring_ring_health_status(arguments: dict) -> Sequence[TextContent]:
    """Handle get_monitoring_ring_health_status tool call."""
    monitoring_ring_id = arguments["monitoring_ring_id"]
    
    logger.debug(f"🔍 Executing get_monitoring_ring_health_status for monitoring ring {monitoring_ring_id}")
    
    try:
        # Step 1: Get monitoring ring details
        logger.info(f"📡 Getting monitoring ring details for {monitoring_ring_id}...")
        ring_endpoint = f'/monitoring-rings/{monitoring_ring_id}/'
        ring_response = make_request('GET', ring_endpoint)
        ring_response.raise_for_status()
        
        ring_data = ring_response.json()
        ring_name = ring_data.get('name', 'Unknown')
        instances = ring_data.get('instances', [])
        
        # Log what was retrieved from monitoring ring API
        logger.info(f"📊 Retrieved monitoring ring data: name='{ring_name}', instances_count={len(instances)}")
        logger.debug(f"🔍 Ring data keys: {list(ring_data.keys())}")
        
        # Log detailed instan
        if instances:
            instance_sample = instances[0] if instances else {}
            logger.debug(f"🔍 Sample instance keys: {list(instance_sample.keys()) if instance_sample else 'No instances'}")
        
        if not instances:
            return [TextContent(type="text", text=f"No instances found in monitoring ring '{ring_name}' ({monitoring_ring_id})")]
        
        logger.info(f"✅ Found {len(instances)} instances in monitoring ring '{ring_name}'")
        
        # Step 2: Collect health status for each instance
        health_results = []
        failed_instances = []
        
        for instance in instances:
            instance_id = instance.get('instance_id')
            instance_name = instance.get('display_name', instance_id)
            
            logger.debug(f"🩺 Checking health for instance {instance_name} ({instance_id})")
            
            instance_result = {
                'instance_id': instance_id,
                'instance_name': instance_name,
                'region': instance.get('region_name', 'Unknown'),
                'shape': instance.get('shape', 'Unknown'),
                'active_health_check': None,
                'passive_health_check': None,
                'overall_status': 'unknown'
            }
            
            # Get active health check
            try:
                active_endpoint = f'/instances/{instance_id}/active-health-check/'
                active_response = make_request('GET', active_endpoint)
                active_response.raise_for_status()
                
                active_data = active_response.json()
                
                # Log what was retrieved from active health check API
                logger.debug(f"🩺 Active health check data for {instance_name}: {active_data}")
                if active_data:
                    logger.info(f"📋 Active health check retrieved for {instance_name}: state={active_data.get('state')}, type={active_data.get('type')}")
                    instance_result['active_health_check'] = {
                        'state': active_data.get('state', 'unknown'),
                        'type': active_data.get('type', 'unknown'),
                        'created_at': active_data.get('created_at', 'unknown'),
                        'uuid': active_data.get('uuid', 'unknown')
                    }
                else:
                    logger.info(f"📋 No active health check data found for {instance_name}")
                    instance_result['active_health_check'] = {'state': 'no_check', 'message': 'No active health check found'}
                    
            except Exception as active_e:
                logger.warning(f"⚠️  Failed to get active health check for {instance_name}: {active_e}")
                instance_result['active_health_check'] = {'state': 'error', 'message': str(active_e)}
            
            # Get passive health check from lens API
            try:
                passive_endpoint = f'/instances/{instance_id}/passive-health-check/'
                passive_response = make_request('GET', passive_endpoint)
                passive_response.raise_for_status()
                
                passive_data = passive_response.json()
                passive_health = passive_data.get('passive_health_check', {})
                failure_recommendation = passive_data.get('failure_recommendation')
                
                # Log what was retrieved from passive health check API
                logger.debug(f"🔍 Passive health check data for {instance_name}: {passive_data}")
                logger.info(f"📊 Passive health check retrieved for {instance_name}: status={passive_health.get('status')}, has_failure_recommendation={bool(failure_recommendation)}")
                if failure_recommendation:
                    logger.debug(f"⚠️  Failure recommendation for {instance_name}: {failure_recommendation}")
                
                # Structure the passive health check result
                passive_result = {
                    'status': passive_health.get('status', 'unknown'),
                    'failure_recommendation': failure_recommendation
                }
                
                # Add issue description if available from failure recommendation
                if failure_recommendation and failure_recommendation.get('issue'):
                    passive_result['issue'] = failure_recommendation['issue']
                
                instance_result['passive_health_check'] = passive_result
                
            except Exception as passive_e:
                logger.warning(f"⚠️  Failed to get passive health check for {instance_name}: {passive_e}")
                instance_result['passive_health_check'] = {'status': 'error', 'message': str(passive_e)}
            
            # Determine overall status
            active_state = instance_result['active_health_check'].get('state', 'unknown') if instance_result['active_health_check'] else 'unknown'
            passive_status = instance_result['passive_health_check'].get('status', 'unknown') if instance_result['passive_health_check'] else 'unknown'
            
            # Logic to determine if instance is failed
            # Active Health Check States: scheduled, running, failed, completed, disabled
            is_failed = False
            if active_state == 'failed':
                is_failed = True
            elif passive_status == 'fail':
                is_failed = True
            elif active_state == 'disabled':
                # Health checks are disabled for this instance
                instance_result['overall_status'] = 'disabled'
            elif active_state == 'completed' and passive_status == 'pass':
                instance_result['overall_status'] = 'healthy'
            elif active_state == 'completed' and passive_status in ['unknown', 'error', 'unavailable']:
                # Active check completed but no passive data - still consider healthy if active passed
                instance_result['overall_status'] = 'healthy'
            elif active_state in ['scheduled', 'running']:
                instance_result['overall_status'] = 'checking'
            else:
                instance_result['overall_status'] = 'degraded'
            
            if is_failed:
                instance_result['overall_status'] = 'failed'
                failed_instances.append(instance_result)
            
            health_results.append(instance_result)
        
        # Step 4: Generate comprehensive report
        report_lines = []
        report_lines.append(f"=== Health Status Report for Monitoring Ring ===")
        report_lines.append(f"Ring Name: {ring_name}")
        report_lines.append(f"Ring ID: {monitoring_ring_id}")
        report_lines.append(f"Total Instances: {len(instances)}")
        report_lines.append(f"Failed Instances: {len(failed_instances)}")
        report_lines.append("")
        
        # Summary by status
        status_counts = {}
        for result in health_results:
            status = result['overall_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        report_lines.append("=== Status Summary ===")
        for status, count in sorted(status_counts.items()):
            emoji = {
                'healthy': '✅',
                'failed': '❌',
                'degraded': '⚠️',
                'checking': '🔄',
                'no_data': '❓',
                'disabled': '🚫',
                'unknown': '❔'
            }.get(status, '📊')
            report_lines.append(f"{emoji} {status.upper()}: {count} instances")
        report_lines.append("")
        
        # Failed instances detail
        if failed_instances:
            report_lines.append("=== FAILED INSTANCES DETAILS ===")
            for failed in failed_instances:
                report_lines.append(f"❌ {failed['instance_name']} ({failed['instance_id']})")
                report_lines.append(f"   Region: {failed['region']}")
                report_lines.append(f"   Shape: {failed['shape']}")
                
                if failed['active_health_check']:
                    ahc = failed['active_health_check']
                    report_lines.append(f"   Active Health Check: {ahc.get('state', 'unknown')} ({ahc.get('type', 'unknown')})")
                
                if failed['passive_health_check']:
                    phc = failed['passive_health_check']
                    status_line = f"   Passive Health Check: {phc.get('status', 'unknown')}"
                    if 'issue' in phc and phc['issue']:
                        status_line += f" - {phc['issue']}"
                    report_lines.append(status_line)
                    
                    # Add failure recommendation details if available
                    if phc.get('failure_recommendation'):
                        fr = phc['failure_recommendation']
                        if fr.get('suggestion'):
                            report_lines.append(f"     Suggestion: {fr['suggestion']}")
                        if fr.get('fault_code'):
                            report_lines.append(f"     Fault Code: {fr['fault_code']}")
                
                report_lines.append("")
        
        # All instances detail
        report_lines.append("=== ALL INSTANCES STATUS ===")
        for result in health_results:
            status_emoji = {
                'healthy': '✅',
                'failed': '❌',
                'degraded': '⚠️',
                'checking': '🔄',
                'no_data': '❓',
                'disabled': '🚫',
                'unknown': '❔'
            }.get(result['overall_status'], '📊')
            
            report_lines.append(f"{status_emoji} {result['instance_name']} ({result['instance_id']})")
            report_lines.append(f"   Overall Status: {result['overall_status'].upper()}")
            
            if result['active_health_check']:
                ahc = result['active_health_check']
                report_lines.append(f"   Active: {ahc.get('state', 'unknown')} ({ahc.get('type', 'unknown')})")
            
            if result['passive_health_check']:
                phc = result['passive_health_check']
                passive_line = f"   Passive: {phc.get('status', 'unknown')}"
                if 'issue' in phc and phc['issue']:
                    passive_line += f" - {phc['issue']}"
                report_lines.append(passive_line)
            
            report_lines.append("")
        
        result_text = "\n".join(report_lines)
        logger.info(f"✅ Health status report generated for monitoring ring '{ring_name}' - {len(failed_instances)} failed instances found")
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"❌ Error getting monitoring ring health status: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                return [TextContent(type="text", text=f"Error getting monitoring ring health status: {error_detail}")]
            except:
                return [TextContent(type="text", text=f"Error getting monitoring ring health status: {e.response.text}")]
        return [TextContent(type="text", text=f"Error getting monitoring ring health status: {str(e)}")]


