Below are some events that can be filtered on using a `where` clause with the log search functionality. 

Examples to search for logs regarding a launch instance event:

`| where type = 'com.oraclecloud.computeapi.launchinstance.begin'`
`| where type = 'com.oraclecloud.computeapi.launchinstance.end'`

Do NOT attempt to filter on event types using a wildcard (*) operator.

| Event Description | Event ID |
|-------------------|----------|
| Database Tools Identity - Refresh Identity Credential End | com.oraclecloud.dbtoolsserviceapi.refreshdatabasetoolsidentitycredential.end |
| Database Tools Identity - Refresh Identity Credential Begin | com.oraclecloud.dbtoolsserviceapi.refreshdatabasetoolsidentitycredential.begin |
| Database Tools Identity - Change Compartment End | com.oraclecloud.dbtoolsserviceapi.changedatabasetoolsidentitycompartment.end |
| Database Tools Identity - Create Begin | com.oraclecloud.dbtoolsserviceapi.createdatabasetoolsidentity.begin |
| Database Tools Identity - Delete End | com.oraclecloud.dbtoolsserviceapi.deletedatabasetoolsidentity.end |
| Database Tools Identity - Delete Begin | com.oraclecloud.dbtoolsserviceapi.deletedatabasetoolsidentity.begin |
| Database Tools Identity - Update Begin | com.oraclecloud.dbtoolsserviceapi.updatedatabasetoolsidentity.begin |
| Database Tools Identity - Create End | com.oraclecloud.dbtoolsserviceapi.createdatabasetoolsidentity.end |
| Database Tools Identity - Change Compartment Begin | com.oraclecloud.dbtoolsserviceapi.changedatabasetoolsidentitycompartment.begin |
| Database Tools Identity - Update End | com.oraclecloud.dbtoolsserviceapi.updatedatabasetoolsidentity.end |
| Attribute Set Update - Begin | com.oraclecloud.datasafe.updateattributeset.begin |
| Attribute Set Delete - End | com.oraclecloud.datasafe.deleteattributeset.end |
| Attribute Set Create - Begin | com.oraclecloud.datasafe.createattributeset.begin |
| Attribute Set Create - End | com.oraclecloud.datasafe.createattributeset.end |
| Attribute Set Delete - Begin | com.oraclecloud.datasafe.deleteattributeset.begin |
| Attribute Set Update - End | com.oraclecloud.datasafe.updateattributeset.end |
| DeleteKnowledgeBase - end | com.oraclecloud.adm.deleteknowledgebase.end |
| UpdateKnowledgeBase - begin | com.oraclecloud.adm.updateknowledgebase.begin |
| DeleteKnowledgeBase - begin | com.oraclecloud.adm.deleteknowledgebase.begin |
| CreateKnowledgeBase - end | com.oraclecloud.adm.createknowledgebase.end |
| CreateKnowledgeBase - begin | com.oraclecloud.adm.createknowledgebase.begin |
| VulnerabilityAudit - Create | com.oraclecloud.adm.createvulnerabilityaudit |
| VulnerabilityAudit - Delete | com.oraclecloud.adm.deletevulnerabilityaudit |
| UpdateKnowledgeBase - end | com.oraclecloud.adm.updateknowledgebase.end |
| VulnerabilityAudit - Update | com.oraclecloud.adm.updatevulnerabilityaudit |
| External Database Connector - Update End | com.oraclecloud.databaseservice.updateexternaldatabaseconnector.end |
| Autonomous Database - Update End | com.oraclecloud.databaseservice.updateautonomousdatabase.end |
| Cloud Exadata Infrastructure - Change Compartment End | com.oraclecloud.databaseservice.changecloudexadatainfrastructurecompartment.end |
| External Database Connector - Create End | com.oraclecloud.databaseservice.createexternaldatabaseconnector.end |
| DB System - Create End | com.oraclecloud.databaseservice.launchdbsystem.end |
| Autonomous Database - Change Compartment Begin | com.oraclecloud.databaseservice.changeautonomousdatabasecompartment.begin |
| Autonomous Database - Disable Dataguard Begin | com.oraclecloud.databaseservice.disableautonomousdataguard.begin |
| Autonomous Database - Enable Dataguard Begin | com.oraclecloud.databaseservice.enableautonomousdataguard.begin |
| Autonomous Database - Manual Fail Over Begin | com.oraclecloud.databaseservice.failoverautonomousdatabase.begin |
| Autonomous Database - Switch Over Begin | com.oraclecloud.databaseservice.switchoverautonomousdatabase.begin |
| Autonomous Database - Disconnect Refreshable Clone from Source Database Begin | com.oraclecloud.databaseservice.disconnectrefreshableautonomousdatabaseclonefromsource.begin |
| ML Application Instance - Change compartment End | com.oraclecloud.datascience.changemlapplicationinstancecompartment.end |
| External Non-Container Database - Disable Database Management Service End | com.oraclecloud.databaseservice.disabledatabasemanagementserviceforexternalnoncontainerdatabase.end |
| DB System - Create Begin | com.oraclecloud.databaseservice.launchdbsystem.begin |
| External Container Database - Scan Pluggable Databases End | com.oraclecloud.databaseservice.scanexternalcontainerdatabasepluggabledatabases.end |
| ML Application Implementation Version - Update | com.oraclecloud.datascience.updatemlapplicationimplementationversion |
| Autonomous Database - Terminate End | com.oraclecloud.databaseservice.deleteautonomousdatabase.end |
| External Non-Container Database - Change Compartment End | com.oraclecloud.databaseservice.changeexternalnoncontainerdatabasecompartment.end |
| Autonomous Database - Update Compute Model Begin | com.oraclecloud.databaseservice.updateautonomousdatabasecomputemodel.begin |
| External Database Connector - Check Status Begin | com.oraclecloud.databaseservice.checkexternaldatabaseconnectorconnectionstatus.begin |
| Autonomous Container Database - Terminate Begin | com.oraclecloud.databaseservice.terminateautonomouscontainerdatabase.begin |
| Cloud Exadata Infrastructure - Create Begin | com.oraclecloud.databaseservice.createcloudexadatainfrastructure.begin |
| Cloud VM Cluster - Create End | com.oraclecloud.databaseservice.createcloudvmcluster.end |
| Cloud VM Cluster - Terminate Virtual Machine Begin | com.oraclecloud.databaseservice.cloudvmclusterterminatevirtualmachine.begin |
| Cloud Exadata Infrastructure - Add Storage Capacity End | com.oraclecloud.databaseservice.addstoragecapacitycloudexadatainfrastructure.end |
| External Non-Container Database - Enable Database Management Service Begin | com.oraclecloud.databaseservice.enabledatabasemanagementserviceforexternalnoncontainerdatabase.begin |
| External Pluggable Database - Delete End | com.oraclecloud.databaseservice.deleteexternalpluggabledatabase.end |
| Data Guard Association - Create End | com.oraclecloud.databaseservice.createdataguardassociation.end |
| Cloud Exadata Infrastructure - DB Server Maintenance End | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancedbserver.end |
| External Pluggable Database - Disable Database Management Service Begin | com.oraclecloud.databaseservice.disabledatabasemanagementserviceforexternalpluggabledatabase.begin |
| ML Application Implementation - Update End | com.oraclecloud.datascience.updatemlapplicationimplementation.end |
| Pluggable Database - Remote Clone Begin | com.oraclecloud.databaseservice.pluggabledatabase.remoteclone.begin |
| External Container Database - Delete Begin | com.oraclecloud.databaseservice.deleteexternalcontainerdatabase.begin |
| Cloud Exadata Infrastructure - Maintenance Rescheduled | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancerescheduled |
| Application Virtual IP (VIP) - Create Begin | com.oraclecloud.databaseservice.createapplicationvip.begin |
| Autonomous Database - Disable Dataguard End | com.oraclecloud.databaseservice.disableautonomousdataguard.end |
| Autonomous Database - Enable Dataguard End | com.oraclecloud.databaseservice.enableautonomousdataguard.end |
| Autonomous Database - Manual Fail Over End | com.oraclecloud.databaseservice.failoverautonomousdatabase.end |
| Autonomous Database - Switch Over End | com.oraclecloud.databaseservice.switchoverautonomousdatabase.end |
| Data Guard Association - Failover End | com.oraclecloud.databaseservice.failoverdataguardassociation.end |
| Autonomous Database - Disconnect Refreshable Clone from Source Database End | com.oraclecloud.databaseservice.disconnectrefreshableautonomousdatabaseclonefromsource.end |
| External Non-Container Database - Enable Database Management Service End | com.oraclecloud.databaseservice.enabledatabasemanagementserviceforexternalnoncontainerdatabase.end |
| Cloud VM Cluster - Delete Begin | com.oraclecloud.databaseservice.deletecloudvmcluster.begin |
| Autonomous Database - Free Database Automatically Stopped | com.oraclecloud.databaseservice.freeautonomousdatabasestopped |
| Cloud Exadata Infrastructure - Delete End | com.oraclecloud.databaseservice.deletecloudexadatainfrastructure.end |
| DB System - Change Compartment End | com.oraclecloud.databaseservice.changedbsystemcompartment.end |
| External Container Database - Change Compartment Begin | com.oraclecloud.databaseservice.changeexternalcontainerdatabasecompartment.begin |
| DB System - Change Compartment Begin | com.oraclecloud.databaseservice.changedbsystemcompartment.begin |
| Autonomous Database - Automatic Backup Begin | com.oraclecloud.databaseservice.automaticbackupautonomousdatabase.begin |
| External Container Database - Change Compartment End | com.oraclecloud.databaseservice.changeexternalcontainerdatabasecompartment.end |
| Cloud Exadata Infrastructure - VM Maintenance Begin | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancevm.begin |
| ML Application Instance - Trigger Begin | com.oraclecloud.datascience.triggermlapplicationinstanceflow.begin |
| Database - Create Backup End | com.oraclecloud.databaseservice.backupdatabase.end |
| ML Application Instance - Trigger End | com.oraclecloud.datascience.triggermlapplicationinstanceflow.end |
| Cloud Exadata Infrastructure - Storage Server Maintenance Begin | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancestorageservers.begin |
| ML Application Instance View - Create | com.oraclecloud.datascience.createmlapplicationinstanceview |
| ML Application - Change compartment | com.oraclecloud.datascience.changemlapplicationcompartment |
| External Pluggable Database - Change Compartment End | com.oraclecloud.databaseservice.changeexternalpluggabledatabasecompartment.end |
| Cloud Exadata Infrastructure - Maintenance Custom Action Time Out End | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancecustomactiontime.end |
| Autonomous Database - Automatic Backup End | com.oraclecloud.databaseservice.automaticbackupautonomousdatabase.end |
| ML Application Implementation - Change compartment Begin | com.oraclecloud.datascience.changemlapplicationimplementationcompartment.begin |
| External Container Database - Disable Database Management Service End | com.oraclecloud.databaseservice.disabledatabasemanagementserviceforexternalcontainerdatabase.end |
| External Database Connector - Check Status End | com.oraclecloud.databaseservice.checkexternaldatabaseconnectorconnectionstatus.end |
| ML Application Instance View - Recover Begin | com.oraclecloud.datascience.recovermlapplicationinstanceview.begin |
| External Pluggable Database - Update Begin | com.oraclecloud.databaseservice.updateexternalpluggabledatabase.begin |
| External Pluggable Database - Delete Begin | com.oraclecloud.databaseservice.deleteexternalpluggabledatabase.begin |
| Application Virtual IP (VIP) - Delete End | com.oraclecloud.databaseservice.deleteapplicationvip.end |
| ML Application Instance - Delete Begin | com.oraclecloud.datascience.deletemlapplicationinstance.begin |
| External Non-Container Database - Create | com.oraclecloud.databaseservice.createexternalnoncontainerdatabase |
| DB System - Update IORM Begin | com.oraclecloud.databaseservice.updateiormconfig.begin |
| ML Application Instance - Create Begin | com.oraclecloud.datascience.createmlapplicationinstance.begin |
| Cloud VM Cluster - Change Compartment End | com.oraclecloud.databaseservice.changecloudvmclustercompartment.end |
| Cloud Exadata Infrastructure - Information Events | com.oraclecloud.databaseservice.exadatainfrastructure.information |
| Job - Delete Begin | com.oraclecloud.datascience.deletejob.begin |
| GGS Deployment - Updating | com.oraclecloud.goldengate.stateupdating |
| Cloud Guard - Announcements | com.oraclecloud.cloudguard.announcements |
| Artifact Repository - Create | com.oraclecloud.artifacts.createrepository |
| GGS Deployment - Create Deployment Backup End | com.oraclecloud.goldengate.createdeploymentbackup.end |
| Container Image - Read Manifest | com.oraclecloud.artifacts.readdockerrepositorymanifest |
| Artifact Repository - List | com.oraclecloud.artifacts.listrepositories |
| SQL Firewall Allowed SQL Bulk Delete - End | com.oraclecloud.datasafe.bulkdeletesqlfirewallallowedsqls.end |
| Security Assessment Refresh - Begin | com.oraclecloud.datasafe.refreshsecurityassessment.begin |
| Tag Namespace - Create | com.oraclecloud.taggingcontrolplane.createtagnamespace |
| Security Assessment Compare - End | com.oraclecloud.datasafe.comparesecurityassessment.end |
| Audit Trail Start - End | com.oraclecloud.datasafe.startaudittrail.end |
| Generic Artifact - List | com.oraclecloud.artifacts.listgenericartifacts |
| Job - Delete End | com.oraclecloud.datascience.deletejob.end |
| Container Repository - Change Compartment | com.oraclecloud.artifacts.changecontainerrepositorycompartment |
| Generic Artifact - Get By Path | com.oraclecloud.artifacts.getgenericartifactbypath |
| Generic Artifact - Get | com.oraclecloud.artifacts.getgenericartifact |
| Tag Definition - Update | com.oraclecloud.taggingcontrolplane.updatetagdefinition |
| VMware Solution - Get Work Request | com.oraclecloud.vmwaresolution.getworkrequest |
| GGS Deployment - Restore Deployment End | com.oraclecloud.goldengate.restoredeployment.end |
| Container Repository - Update (Legacy) | com.oraclecloud.artifacts.updatedockerrepositorymetadata |
| User Assessment Report Download | com.oraclecloud.datasafe.downloaduserassessmentreport |
| Container Repository - Upload Layer | com.oraclecloud.artifacts.uploaddockerlayer |
| SQL Firewall Allowed SQL Bulk Create - End | com.oraclecloud.datasafe.bulkcreatesqlfirewallallowedsqls.end |
| GGS Deployment - Create Deployment Backup Begin | com.oraclecloud.goldengate.createdeploymentbackup.begin |
| Generic Artifact - Download | com.oraclecloud.artifacts.getgenericartifactcontent |
| Container Image - Delete | com.oraclecloud.artifacts.deletecontainerimage |
| GGS Deployment - Deleted | com.oraclecloud.goldengate.statedeleted |
| Autonomous Container Database - Automatic Failover | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.autofailover |
| Autonomous Container Database - Automatic Reinstate | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.autoreinstate |
| GGS Deployment - Update Deployment Backup Begin | com.oraclecloud.goldengate.updatedeploymentbackup.begin |
| Audit Trail Start - Begin | com.oraclecloud.datasafe.startaudittrail.begin |
| GGS Deployment - Delete Database Registration End | com.oraclecloud.goldengate.deletedatabaseregistration.end |
| Security Assessment Create - End | com.oraclecloud.datasafe.createsecurityassessment.end |
| Autonomous Cloud VM Cluster - Warning | com.oraclecloud.databaseservice.autonomous.cloudautonomousvmcluster.warning |
| Container Repository - Update | com.oraclecloud.artifacts.updatecontainerrepository |
| Tag Namespace - Change Compartment | com.oraclecloud.taggingcontrolplane.changetagnamespacecompartment |
| Job Run - Succeeded | com.oraclecloud.datascience.succeededjobrun |
| VMware Solution - List Supported VMware Software Versions | com.oraclecloud.vmwaresolution.listsupportedvmwaresoftwareversions |
| Container Repository - Delete (Legacy) | com.oraclecloud.artifacts.deletedockerrepository |
| Audit Trail Resume - Begin | com.oraclecloud.datasafe.resumeaudittrail.begin |
| GGS Deployment - Update Deployment Begin | com.oraclecloud.goldengate.updatedeployment.begin |
| VMware Solution - List Work Request Logs | com.oraclecloud.vmwaresolution.listworkrequestlogs |
| DB Node - Warning | com.oraclecloud.databaseservice.dbnode.warning |
| GGS Deployment - Creating | com.oraclecloud.goldengate.statecreating |
| Security Assessment Refresh - End | com.oraclecloud.datasafe.refreshsecurityassessment.end |
| Retention Policy - Create | com.oraclecloud.artifacts.createimageretentionpolicy |
| Container Repository - Delete Layer | com.oraclecloud.artifacts.deletedockerlayer |
| Container Image - Delete | com.oraclecloud.artifacts.deletedockerimage |
| Artifact Repository - Delete | com.oraclecloud.artifacts.deleterepository |
| VMware Solution - Delete SDDC End | com.oraclecloud.vmwaresolution.deletesddc.end |
| GGS Deployment - Delete Deployment Begin | com.oraclecloud.goldengate.deletedeployment.begin |
| VMware Solution - Get ESXi Host | com.oraclecloud.vmwaresolution.getesxihost |
| Generic Artifact - Upload By Path | com.oraclecloud.artifacts.putgenericartifactcontentbypath |
| User Assessment Baseline Unset - End | com.oraclecloud.datasafe.unsetuserassessmentbaseline.end |
| GGS Deployment - Inactive | com.oraclecloud.goldengate.stateinactive |
| VMware Solution - List SDDCs | com.oraclecloud.vmwaresolution.listesxihosts |
| Generic Artifact - Delete By Path | com.oraclecloud.artifacts.deletegenericartifactbypath |
| Job Run - Failed | com.oraclecloud.datascience.failedjobrun |
| Audit Trail Resume - End | com.oraclecloud.datasafe.resumeaudittrail.end |
| VMware Solution - Update SDDC | com.oraclecloud.vmwaresolution.updatesddc |
| GGS Deployment - Stop Deployment End | com.oraclecloud.goldengate.stopdeployment.end |
| Anomaly Detection - private endpoint move end | com.oraclecloud.aiservice.changeaiprivateendpointcompartment.end |
| GGS Deployment - Update Database Registration End | com.oraclecloud.goldengate.updatedatabaseregistration.end |
| Container Repository - Delete Contents (Legacy) | com.oraclecloud.artifacts.deletedockerrepositorycontents |
| Security Assessment Baseline Set - Begin | com.oraclecloud.datasafe.setsecurityassessmentbaseline.begin |
| Retention Policy - Update | com.oraclecloud.artifacts.updateimageretentionpolicy |
| GGS Deployment - Delete Deployment End | com.oraclecloud.goldengate.deletedeployment.end |
| VMware Solution - Delete ESXi Host End | com.oraclecloud.vmwaresolution.deleteesxihost.end |
| Tag Definition - Delete | com.oraclecloud.taggingcontrolplane.deletetagdefinition.end |
| GGS Deployment - Create Database Registration End | com.oraclecloud.goldengate.createdatabaseregistration.end |
| GGS Deployment - Create Deployment End | com.oraclecloud.goldengate.createdeployment.end |
| Container Image Signature - Delete | com.oraclecloud.artifacts.deletecontainerimagesignature |
| Generic Artifact - Update | com.oraclecloud.artifacts.updategenericartifact |
| Tag Namespace - Update | com.oraclecloud.taggingcontrolplane.updatetagnamespace |
| GGS Deployment - Update Database Registration Begin | com.oraclecloud.goldengate.updatedatabaseregistration.begin |
| User Assessment Compare - End | com.oraclecloud.datasafe.compareuserassessment.end |
| VMware Solution - Downgrade HCX Begin | com.oraclecloud.vmwaresolution.downgradehcx.begin |
| VMware Solution - List Work Request Errors | com.oraclecloud.vmwaresolution.listworkrequesterrors |
| Artifact Repository - Change Compartment | com.oraclecloud.artifacts.changerepositorycompartment |
| User Assessment Refresh - End | com.oraclecloud.datasafe.refreshuserassessment.end |
| Job Run - Create Begin | com.oraclecloud.datascience.createjobrun.begin |
| GGS Deployment - Start Deployment Begin | com.oraclecloud.goldengate.startdeployment.begin |
| VMware Solution - Get SDDC | com.oraclecloud.vmwaresolution.getsddc |
| Job - Create | com.oraclecloud.datascience.createjob |
| Security Assessment Create - Begin | com.oraclecloud.datasafe.createsecurityassessment.begin |
| GGS Deployment - Deleting | com.oraclecloud.goldengate.statedeleting |
| Security Assessment Report Download | com.oraclecloud.datasafe.downloadsecurityassessmentreport |
| Container Repository - Remove Version (Legacy) | com.oraclecloud.artifacts.removedockertag |
| VMware Solution - List Work Requests | com.oraclecloud.vmwaresolution.listworkrequests |
| User Assessment Create - End | com.oraclecloud.datasafe.createuserassessment.end |
| Generic Artifact - Update By Path | com.oraclecloud.artifacts.updategenericartifactbypath |
| Tag Namespace - Cascade Delete | com.oraclecloud.taggingcontrolplane.cascadedeletetagnamespace.begin |
| Tag Definition - Create | com.oraclecloud.taggingcontrolplane.createtagdefinition |
| Cloud Guard - Status | com.oraclecloud.cloudguard.status |
| VMware Solution - Upgrade HCX End | com.oraclecloud.vmwaresolution.upgradehcx.end |
| VMware Solution - Delete SDDC Begin | com.oraclecloud.vmwaresolution.deletesddc.begin |
| VMware Solution - Update ESXi Host | com.oraclecloud.vmwaresolution.updateesxihost |
| User Assessment Compare - Begin | com.oraclecloud.datasafe.compareuserassessment.begin |
| Anomaly Detection - private endpoint create end | com.oraclecloud.aiservice.createaiprivateendpoint.end |
| Security Assessment Drift From Baseline | com.oraclecloud.datasafe.securityassessmentdriftfrombaseline |
| Container Image - List | com.oraclecloud.artifacts.listcontainerimages |
| GGS Deployment - Stop Deployment Begin | com.oraclecloud.goldengate.stopdeployment.begin |
| Job Run - Timeout | com.oraclecloud.datascience.timeoutjobrun |
| Container Configuration - Update | com.oraclecloud.artifacts.updatecontainerconfiguration |
| Security Assessment Baseline Unset - Begin | com.oraclecloud.datasafe.unsetsecurityassessmentbaseline.begin |
| Anomaly Detection - private endpoint delete begin | com.oraclecloud.aiservice.deleteaiprivateendpoint.begin |
| Generic Artifact - Delete | com.oraclecloud.artifacts.deletegenericartifact |
| Security Assessment Report Generate - Begin | com.oraclecloud.datasafe.generatesecurityassessmentreport.begin |
| Tag Default - Create | com.oraclecloud.taggingcontrolplane.createtagdefault |
| User Assessment Report Generate - Begin | com.oraclecloud.datasafe.generateuserassessmentreport.begin |
| Container Repository - List | com.oraclecloud.artifacts.listcontainerrepositories |
| VMware Solution - Create SDDC End | com.oraclecloud.vmwaresolution.createsddc.end |
| Retention Policy - Delete | com.oraclecloud.artifacts.deleteimageretentionpolicy |
| User Assessment Refresh - Begin | com.oraclecloud.datasafe.refreshuserassessment.begin |
| Autonomous Cloud VM Cluster - Create Begin | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.create.begin |
| SQL Firewall Allowed SQL Bulk Delete - Begin | com.oraclecloud.datasafe.bulkdeletesqlfirewallallowedsqls.begin |
| GGS Deployment - Update Deployment End | com.oraclecloud.goldengate.updatedeployment.end |
| Job - Update | com.oraclecloud.datascience.updatejob |
| VMware Solution - List SDDCs | com.oraclecloud.vmwaresolution.listsddcs |
| Container Repository - Create | com.oraclecloud.artifacts.createcontainerrepository |
| Tag Default - Delete | com.oraclecloud.taggingcontrolplane.deletetagdefault |
| GGS Deployment - Needs Attention | com.oraclecloud.goldengate.stateneedsattention |
| Tag Definition - Delete | com.oraclecloud.taggingcontrolplane.deletetagdefinition.begin |
| Job Run - Delete | com.oraclecloud.datascience.deletejobrun |
| Container Image Signature - List | com.oraclecloud.artifacts.listcontainerimagesignatures |
| GGS Deployment - Create Database Registration Begin | com.oraclecloud.goldengate.createdatabaseregistration.begin |
| User Assessment Create - Begin | com.oraclecloud.datasafe.createuserassessment.begin |
| User Assessment Report Generate - End | com.oraclecloud.datasafe.generateuserassessmentreport.end |
| Autonomous Cloud VM Cluster - Create End | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.create.end |
| VMware Solution - Upgrade HCX Begin | com.oraclecloud.vmwaresolution.upgradehcx.begin |
| User Assessment Drift From Baseline | com.oraclecloud.datasafe.userassessmentdriftfrombaseline |
| Container Repository - Read Metadata | com.oraclecloud.artifacts.readdockerrepositorymetadata |
| User Assessment Baseline Set - Begin | com.oraclecloud.datasafe.setuserassessmentbaseline.begin |
| User Assessment Baseline Unset - Begin | com.oraclecloud.datasafe.unsetuserassessmentbaseline.begin |
| Job Run - Cancel Begin | com.oraclecloud.datascience.canceljobrun.begin |
| Container Repository - Pull Layer | com.oraclecloud.artifacts.pulldockerlayer |
| Tag Namespace - Cascade Delete | com.oraclecloud.taggingcontrolplane.cascadedeletetagnamespace.end |
| Container Image - Restore | com.oraclecloud.artifacts.restorecontainerimage |
| GGS Deployment - Start Deployment End | com.oraclecloud.goldengate.startdeployment.end |
| Job Run - Cancel End | com.oraclecloud.datascience.canceljobrun.end |
| GGS Deployment - Create Deployment Begin | com.oraclecloud.goldengate.createdeployment.begin |
| Anomaly Detection - private endpoint move begin | com.oraclecloud.aiservice.changeaiprivateendpointcompartment.begin |
| SQL Firewall Allowed SQL Bulk Create - Begin | com.oraclecloud.datasafe.bulkcreatesqlfirewallallowedsqls.begin |
| Anomaly Detection - private endpoint create begin | com.oraclecloud.aiservice.createaiprivateendpoint.begin |
| SQL Firewall Allowed SQL Delete - Begin | com.oraclecloud.datasafe.deletesqlfirewallallowedsql.begin |
| Container Repository - Delete | com.oraclecloud.artifacts.deletecontainerrepository |
| GGS Deployment - Delete Database Registration Begin | com.oraclecloud.goldengate.deletedatabaseregistration.begin |
| Job Run - Create End | com.oraclecloud.datascience.createjobrun.end |
| Anomaly Detection - private endpoint delete end | com.oraclecloud.aiservice.deleteaiprivateendpoint.end |
| Tag Default - Update | com.oraclecloud.taggingcontrolplane.updatetagdefault |
| Security Assessment Baseline Unset - End | com.oraclecloud.datasafe.unsetsecurityassessmentbaseline.end |
| GGS Deployment - Failed | com.oraclecloud.goldengate.statefailed |
| Container Repository - Get | com.oraclecloud.artifacts.getcontainerrepository |
| SQL Firewall Allowed SQL Delete - End | com.oraclecloud.datasafe.deletesqlfirewallallowedsql.end |
| VMware Solution - List Supported Skus | com.oraclecloud.vmwaresolution.listsupportedskus |
| GGS Deployment - Update Deployment Backup End | com.oraclecloud.goldengate.updatedeploymentbackup.end |
| Artifact Repository - Update | com.oraclecloud.artifacts.updaterepository |
| Container Image Signature - Upload | com.oraclecloud.artifacts.uploadcontainerimagesignature |
| Security Assessment Report Generate - End | com.oraclecloud.datasafe.generatesecurityassessmentreport.end |
| VMware Solution - Downgrade HCX End | com.oraclecloud.vmwaresolution.downgradehcx.end |
| Audit Trail Stop - Begin | com.oraclecloud.datasafe.stopaudittrail.begin |
| Job Run - Update | com.oraclecloud.datascience.updatejobrun |
| GGS Deployment - Delete Deployment Backup Begin | com.oraclecloud.goldengate.deletedeploymentbackup.begin |
| Generic Artifact - Download By Path | com.oraclecloud.artifacts.getgenericartifactcontentbypath |
| GGS Deployment - Delete Deployment Backup End | com.oraclecloud.goldengate.deletedeploymentbackup.end |
| VMware Solution - Refresh HCX Licenses Status End | com.oraclecloud.vmwaresolution.refreshhcxlicensestatus.end |
| Custom Property - Update | com.oraclecloud.datacatalog.object.customproperty.update |
| Security Assessment Baseline Set - End | com.oraclecloud.datasafe.setsecurityassessmentbaseline.end |
| VMware Solution - Refresh HCX Licenses Status Begin | com.oraclecloud.vmwaresolution.refreshhcxlicensestatus.begin |
| VMware Solution - Delete ESXi Host Begin | com.oraclecloud.vmwaresolution.deleteesxihost.begin |
| User Assessment Baseline Set - End | com.oraclecloud.datasafe.setuserassessmentbaseline.end |
| Container Image - Upload | com.oraclecloud.artifacts.uploaddockerimage |
| Autonomous Cloud VM Cluster - Critical | com.oraclecloud.databaseservice.autonomous.cloudautonomousvmcluster.critical |
| GGS Deployment - Restore Deployment Begin | com.oraclecloud.goldengate.restoredeployment.begin |
| GGS Deployment - Active | com.oraclecloud.goldengate.stateactive |
| Container Image - Remove Version | com.oraclecloud.artifacts.removecontainerversion |
| Cloud VM Cluster - Warning | com.oraclecloud.databaseservice.cloudvmcluster.warning |
| Exadb VM Cluster - Warning | com.oraclecloud.databaseservice.exadbvmcluster.warning |
| VM Cluster - Terminate Virtual Machine Begin | com.oraclecloud.databaseservice.vmclusterterminatevirtualmachine.begin |
| Autonomous Container Database - Failover Begin | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.failover.begin |
| Exadata Infrastructure - Custom action time Begin | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecustomactiontime.begin |
| Exadata Infrastructure - Storage server maintenance End | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancestorageservers.end |
| Instance - Stop Instance Begin | com.oraclecloud.analytics.stopanalyticsinstance.begin |
| Project - Delete Begin | com.oraclecloud.datascience.deleteproject.begin |
| External MySQL DB System - Deregister End | com.oraclecloud.databasemanagement.externalmysqlresource.dbsystem.deregister.end |
| UpdateAsset | com.oraclecloud.cloudbridge.updateasset |
| Autonomous Data Guard Association - Switchover End | com.oraclecloud.databaseservice.switchoverautonomousdataguardassociation.end |
| Event - Create Kernel Crash Event | com.oraclecloud.osmh.createevent.kernelcrash |
| Delete Global Accelerator Routing Policy Begin | com.oraclecloud.gax.public.api.deleteroutingpolicy.begin |
| Work Request - Update Software Source End | com.oraclecloud.osmh.updatesoftwaresource.end |
| Update Volume Backup Policy | com.oraclecloud.blockvolumes.updatevolumebackuppolicy |
| Distributed Database - Patch Begin | com.oraclecloud.globaldb.patchdistributeddatabase.begin |
| Private Service Access - Update End | com.oraclecloud.privateserviceaccess.updateprivateserviceaccess.end |
| Internet Gateway - Create | com.oraclecloud.virtualnetwork.createinternetgateway |
| Model Deployment - Activate Begin | com.oraclecloud.datascience.activatemodeldeployment.begin |
| Work Request - Reboot Begin | com.oraclecloud.osmh.reboot.begin |
| Security Policy Deploy - End | com.oraclecloud.datasafe.deploysecuritypolicydeployment.end |
| VirtualServiceRouteTable - Create Begin | com.oraclecloud.servicemesh.createvirtualserviceroutetable.begin |
| NAT Gateway - Create | com.oraclecloud.natgateway.createnatgateway |
| Fusion Environment - Create Begin | com.oraclecloud.fusionapps.createfusionenvironment.begin |
| LicenseManager - Create ProductLicense | com.oraclecloud.licensemanager.createproductlicense |
| Public IP - Update | com.oraclecloud.virtualnetwork.updatepublicip |
| Delete Export Set | com.oraclecloud.filestorage.deleteexportset |
| Job - Update | com.oraclecloud.oracleresourcemanager.updatejob |
| SQL Firewall Collection Update - End | com.oraclecloud.datasafe.updatesqlcollection.end |
| Work Request - Install Windows Updates End | com.oraclecloud.osmh.installwindowsupdates.end |
| BDS Instance - Configure Install OS Patch Begin | com.oraclecloud.bds.cp.installospatch.begin |
| Autonomous VM Cluster - Terminate Begin | com.oraclecloud.databaseservice.deleteautonomousvmcluster.begin |
| Data Store - Delete Begin | com.oraclecloud.dataexchange.deletedatastore.begin |
| Node - Stop Begin | com.oraclecloud.zerolatency.stopzerolatencynode.begin |
| Deregister Target Database - End | com.oraclecloud.datasafe.deregisterdatasafetarget.end |
| Rotate Pluggable Database Key - Begin | com.oraclecloud.databaseservice.rotatepluggabledatabasekey.begin |
| Price List Item - Create | com.oraclecloud.subscriptionpricingservice.createpricelistitem |
| Update Stack - End | com.oraclecloud.dataintelligencefoundation.updatestack.end |
| Instance - Start Instance End | com.oraclecloud.analytics.startanalyticsinstance.end |
| Create Export | com.oraclecloud.filestorage.createexport |
| Stack - Change Compartment End | com.oraclecloud.oracleresourcemanager.changestackcompartment.end |
| Ingest Time Rule - Delete | com.oraclecloud.logginganalytics.deleteingesttimerule |
| BDS Instance - List Autoscale Configuration(s) | com.oraclecloud.bds.autoscale.cp.listautoscaleconfiguration |
| Authentication Policy - Update | com.oraclecloud.identitycontrolplane.updateauthenticationpolicy |
| Tenancy Attachment - Create End | com.oraclecloud.resourceanalytics.createtenancyattachment.end |
| Create Global Accelerator Listener Begin | com.oraclecloud.gax.public.api.createlistener.begin |
| GGS Pipeline - Failed | com.oraclecloud.goldengate.pipeline.statefailed |
| FsuDiscovery - Create Begin | com.oraclecloud.fsu.createfsudiscovery.begin |
| DR Protection Group - Disassociate End | com.oraclecloud.disasterrecovery.disassociatedrprotectiongroup.end |
| Cluster - Update Begin | com.oraclecloud.clustersapi.updatecluster.begin |
| Deployment - Delete Begin | com.oraclecloud.apigateway.deletedeployment.begin |
| Table - Alter Begin | com.oraclecloud.nosql.altertable.begin |
| Autonomous Cloud VM Cluster - Terminate End | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.terminate.end |
| Managed Instance - Stage Update | com.oraclecloud.osmh.stageupdate |
| Resource Schedule - Update Begin | com.oraclecloud.resourcescheduler.updateschedule.begin |
| Delete Inventory Begin | com.oraclecloud.cloudbridge.deleteinventory.begin |
| Source Event Types - Remove | com.oraclecloud.logginganalytics.removesourceeventtypes |
| Managed Instance Group - Detach Managed Instance | com.oraclecloud.osms.detachmanagedinstancefrommanagedinstancegroup |
| Service Instance - Create Begin | com.oraclecloud.zerolatency.createzerolatency.begin |
| MySQL - Update HeatWave Cluster Begin | com.oraclecloud.mysqlaas.updateheatwavecluster.begin |
| Change Boot Volume Compartment Begin | com.oraclecloud.blockvolumes.changebootvolumecompartment.begin |
| VM Cluster Network - Validate Begin | com.oraclecloud.databaseservice.validatevmclusternetwork.begin |
| Package - Update | com.oraclecloud.datatransferservice.updatetransferpackage |
| Instance - Terminate Begin | com.oraclecloud.computeapi.terminateinstance.begin |
| Update Global Accelerator End | com.oraclecloud.gax.public.api.updateglobalaccelerator.end |
| Cache Database - Unload Begin | com.oraclecloud.zerolatency.unloadzerolatencydatabase.begin |
| Security Policy Delete - End | com.oraclecloud.datasafe.deletesecuritypolicy.end |
| Instance - Launch End | com.oraclecloud.computeapi.launchinstance.end |
| DR Plan Execution - Ignore Begin | com.oraclecloud.disasterrecovery.ignoredrplanexecution.begin |
| Event - Create Update Ksplice Kernel Event | com.oraclecloud.osmh.createevent.kspliceupdate.updateksplicekernel |
| Service Instance - Roll Back Patch Begin | com.oraclecloud.zerolatency.rollbackpatchzerolatency.begin |
| Network Address List - Change Compartment End | com.oraclecloud.waf.changenetworkaddresslistcompartment.end |
| Db Node Snapshot - Mount end | com.oraclecloud.databaseservice.mountdbnodesnapshot.end |
| Idp Group Mapping - Create | com.oraclecloud.identitycontrolplane.addidpgroupmapping |
| Notebook Session - Create End | com.oraclecloud.datascience.createnotebooksession.end |
| Dynamic Group - Create | com.oraclecloud.identitycontrolplane.createdynamicgroup |
| VirtualService - Delete End | com.oraclecloud.servicemesh.deletevirtualservice.end |
| DB Home - Terminate Begin | com.oraclecloud.databaseservice.deletedbhome.begin |
| Work Request - Set Management Station Config Begin | com.oraclecloud.osmh.setmanagementstationconfig.begin |
| Distributed Autonomous Database - Change Compartment Begin | com.oraclecloud.globaldb.changedistributedautonomousdatabasecompartment.begin |
| Work Request - Update Security End | com.oraclecloud.osmh.updatesecurity.end |
| Instance Pool - Soft Reset Action End | com.oraclecloud.computemanagement.softresetinstancepool.end |
| Instance Pool - Soft Stop Action End | com.oraclecloud.computemanagement.softstopinstancepool.end |
| DeleteProject - end | com.oraclecloud.devopsproject.deleteproject.end |
| Update Volume Kms Key End | com.oraclecloud.blockvolumes.updatevolumekmskey.end |
| Container Instance - Maintenance Begin | com.oraclecloud.containerinstances.maintenance.begin |
| Exascale Database Storage Vault - Change Compartment Begin | com.oraclecloud.databaseservice.changeexascaledbstoragevaultcompartment.begin |
| Db Node Snapshot - Delete end | com.oraclecloud.databaseservice.deletedbnodesnapshot.end |
| Rotate On-Prem Connector - End | com.oraclecloud.datasafe.updateonpremconnectorwallet.end |
| IngressGateway - Update Begin | com.oraclecloud.servicemesh.updateingressgateway.begin |
| Peer - Delete Peer End | com.oraclecloud.blockchain.deletepeer.end |
| Source - Update Begin | com.oraclecloud.applicationmigration.updatesource.begin |
| Tenancy Attachment - Delete Begin | com.oraclecloud.resourceanalytics.deletetenancyattachment.begin |
| Event - Delete Report | com.oraclecloud.osmh.event.deletereport |
| Work Request - List Snaps Begin | com.oraclecloud.osmh.listsnaps.begin |
| Bastion - Change Bastion Compartment | com.oraclecloud.bastion.changebastioncompartment |
| BDS Lake Configuration Instance - Deactivate Lake Configuration Begin | com.oraclecloud.bds.cp.deactivatebdslakeconfiguration.begin |
| Connection Update End | com.oraclecloud.odms.updateconnection.end |
| MySQL - Delete Channel End | com.oraclecloud.mysqlaas.deletechannel.end |
| Oce Instance - Change Compartment Begin | com.oraclecloud.oce.changeoceinstancecompartment.begin |
| Federated User - Create | com.oraclecloud.identitycontrolplane.createfederateduser |
| VM Cluster - Patch End | com.oraclecloud.databaseservice.patchvmcluster.end |
| Connection - Update End | com.oraclecloud.devopsbuild.updateconnection.end |
| Database - Warning | com.oraclecloud.databaseservice.database.warning |
| Batch Job Pool - Create | com.oraclecloud.batch.createbatchjobpool |
| ChangeAssetCompartment | com.oraclecloud.cloudbridge.changeassetcompartment |
| User Capabilities - Update | com.oraclecloud.identitycontrolplane.updateusercapabilities |
| DB Node - Instance Reboot Migrated | com.oraclecloud.databaseservice.dbnodeinstancerebootmigrated |
| Managed Database - Critical | com.oraclecloud.databasemanagement.manageddatabase.critical |
| Asset - Delete End | com.oraclecloud.dataexchange.deleteasset.end |
| Batch Job Pool - Change Compartment End | com.oraclecloud.batch.changebatchjobpoolcompartment.end |
| Cloud Exadata Infrastructure - Granular Maintenance Duration Exceeded Without Enforced Duration | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancedurationexceedednotenforced |
| Data Guard Create Standby Database - Create End | com.oraclecloud.databaseservice.createstandbydatabase.end |
| OCI Cache Cluster - Update Begin | com.oraclecloud.redisservice.updaterediscluster.begin |
| Oce Instance - Create Begin | com.oraclecloud.oce.createoceinstance.begin |
| Warning - Suppress | com.oraclecloud.logginganalytics.suppresswarning |
| Mirror Repository - End | com.oraclecloud.devopscoderepo.mirrorrepository.end |
| LicenseManager - Delete ProductLicense | com.oraclecloud.licensemanager.deleteproductlicense |
| Node - Start End | com.oraclecloud.zerolatency.startzerolatencynode.end |
| SQL Firewall Collection Stop - End | com.oraclecloud.datasafe.stopsqlcollection.end |
| User Assessment Password Expiry Date | com.oraclecloud.datasafe.userassessmentpasswordexpirydate |
| DR Plan - Update Begin | com.oraclecloud.disasterrecovery.updatedrplan.begin |
| Public IP - Delete | com.oraclecloud.virtualnetwork.deletepublicip |
| ZPR Policy - Create Begin | com.oraclecloud.zpr.createzprpolicy.begin |
| ZPR Configuration - Create Begin | com.oraclecloud.zpr.createconfiguration.begin |
| ZPR Configuration - Create End | com.oraclecloud.zpr.createconfiguration.end |
| ZPR Policy - List | com.oraclecloud.zpr.listzprpolicies |
| ZPR Policy - Create End | com.oraclecloud.zpr.createzprpolicy.end |
| ZPR Policy - Get | com.oraclecloud.zpr.getzprpolicy |
| ZPR Configuration - Get | com.oraclecloud.zpr.getconfiguration |
| Recovery Service Subnet - Create Begin | com.oraclecloud.autonomousrecoveryservice.createrecoveryservicesubnet.begin |
| Object Storage Link Sync Job - Stop Import Job | com.oraclecloud.lustrefilestorage.stopimportfromobject |
| Get Protected Database Configuration Begin | com.oraclecloud.autonomousrecoveryservice.fetchprotecteddatabaseconfiguration.begin |
| Stream Packaging Config - Create | com.oraclecloud.mediaservices.createstreampackagingconfig |
| Process Automation Instance - Change Compartment Begin | com.oraclecloud.processautomation.changeopainstancecompartment.begin |
| Delete Feature flag | com.oraclecloud.appconfiguration.deletefeatureflag |
| VirtualService - Create Begin | com.oraclecloud.servicemesh.createvirtualservice.begin |
| Federated Interactive Login | com.oraclecloud.identitysignon.federatedinteractivelogin |
| Application Data Platform - PodDb Restore Point Delete End | com.oraclecloud.applicationdataplatform.deletepoddbrestorepoint.end |
| Process Automation Instance - Create Begin | com.oraclecloud.processautomation.createopainstance.begin |
| BDS Lake Configuration Instance - Update Lake Configuration End | com.oraclecloud.bds.cp.updatebdslakeconfiguration.end |
| Oce Instance - Delete End | com.oraclecloud.oce.deleteoceinstance.end |
| Fusion Environment - Maintenance Scheduled | com.oraclecloud.fusionappsinternal.fusionenvironmentmaintenancescheduled |
| Security Policy Create - End | com.oraclecloud.datasafe.createsecuritypolicy.end |
| Topic - Update | com.oraclecloud.notification.updatetopic |
| LicenseManager - Update License Record | com.oraclecloud.licensemanager.updatelicenserecord |
| VMware Solution - Get Cluster | com.oraclecloud.vmwaresolution.getcluster |
| KeyVersion - Cancel Deletion Begin | com.oraclecloud.keymanagementservice.cancelkeyversiondeletion.begin |
| Notebook Session - Delete End | com.oraclecloud.datascience.deletenotebooksession.end |
| Global Autonomous Database - Start End | com.oraclecloud.globaldb.startshardeddatabase.end |
| Distributed Autonomous Database - Fetch Cloud Autonomous VM Clusters | com.oraclecloud.globaldb.fetchdistributedautonomousdatabasevmclusters |
| Autonomous Database - Update Open Mode Begin | com.oraclecloud.databaseservice.updateautonomousdatabaseopenmode.begin |
| Global Autonomous Database - Delete End | com.oraclecloud.globaldb.deleteshardeddatabase.end |
| Exadb VM Cluster - Terminate Virtual Machine Begin | com.oraclecloud.databaseservice.exadbvmclusterterminatevirtualmachine.begin |
| Stream Cell Deployment - Delete | com.oraclecloud.mediaservices.deletestreamcelldeployment |
| Job - Update | com.oraclecloud.datatransferservice.updatetransferjob |
| Add Stack - End | com.oraclecloud.dataintelligencefoundation.addstack.end |
| AccessPolicy - Update End | com.oraclecloud.servicemesh.updateaccesspolicy.end |
| Cache Database - Start Cache Agent End | com.oraclecloud.zerolatency.startcacheagent.end |
| Container Instance - Delete Container Instance End | com.oraclecloud.containerinstances.deletecontainerinstance.end |
| Masking Policy Create - End | com.oraclecloud.datasafe.createmaskingpolicy.end |
| Price List - Update | com.oraclecloud.subscriptionpricingservice.updatepricelist |
| Change Volume Backup Compartment | com.oraclecloud.blockvolumes.changevolumebackupcompartment |
| API - Update Begin | com.oraclecloud.apigateway.updateapi.begin |
| Container Instance - Maintenance End | com.oraclecloud.containerinstances.maintenance.end |
| Idp Group Mapping - Update | com.oraclecloud.identitycontrolplane.updateidpgroupmapping |
| Batch Context - Update End | com.oraclecloud.batch.updatebatchcontext.end |
| Work Request - Sync Agent Config End | com.oraclecloud.osmh.syncagentconfig.end |
| DR Plan - Create Begin | com.oraclecloud.disasterrecovery.createdrplan |
| EM Bridge - Delete | com.oraclecloud.logginganalytics.deleteembridge |
| Autonomous Container Database - Convert To Physical Standby End | com.oraclecloud.databaseservice.autonomous.container.database.physical.standby.conversion.end |
| Autonomous VM Cluster - Maintenance Begin | com.oraclecloud.databaseservice.autonomousvmclustermaintenance.begin |
| TriggeredAlert - Reset | com.oraclecloud.budgets.resettriggeredalert |
| MySQL - Create Channel End | com.oraclecloud.mysqlaas.createchannel.end |
| Work Request - Sync Management Station Mirror Begin | com.oraclecloud.osmh.syncmanagementstationmirror.begin |
| Instance - Live Migration End | com.oraclecloud.computeapi.livemigrate.end |
| DHCP Options - Delete | com.oraclecloud.virtualnetwork.deletedhcpoptions |
| Autonomous VM Cluster - Update Begin | com.oraclecloud.databaseservice.updateautonomousvmcluster.begin |
| Exadb VM Cluster - Delete End | com.oraclecloud.databaseservice.deleteexadbvmcluster.end |
| Change File System Compartment | com.oraclecloud.filestorage.changefilesystemcompartment |
| Stack - Change Compartment Begin | com.oraclecloud.oracleresourcemanager.changestackcompartment.begin |
| BDS Instance - Delete Resource Principal Configuration Begin | com.oraclecloud.bds.cp.deleteresourceprincipalconfiguration.begin |
| Node - Disable Administrator Shell Access Begin | com.oraclecloud.zerolatency.disableadminshellaccess.begin |
| DR Plan Execution - CreateStopDrillPreCheck Begin | com.oraclecloud.disasterrecovery.createstopdrillprecheckdrplanexecution |
| Update Address List | com.oraclecloud.waf.updateaddresslist |
| Grant - Create | com.oraclecloud.identitycontrolplane.creategrant |
| Autoscaling Configuration - Update | com.oraclecloud.autoscaling.updateautoscalingconfiguration |
| Media Workflow Job - Move Compartment | com.oraclecloud.mediaservices.changemediaworkflowjobcompartment |
| Service Instance - Configure End | com.oraclecloud.zerolatency.configurezerolatency.end |
| Oneoff Patch - Download Begin | com.oraclecloud.databaseservice.downloadoneoffpatch.begin |
| Database Security Config Refresh - End | com.oraclecloud.datasafe.refreshdatabasesecurityconfig.end |
| Oce Instance - Create End | com.oraclecloud.oce.createoceinstance.end |
| Autonomous Data Guard Association - Reinstate End | com.oraclecloud.databaseservice.reinstateautonomousdataguardassociation.end |
| Migration - Update Begin | com.oraclecloud.applicationmigration.updatemigration.begin |
| FsuCollection - Delete End | com.oraclecloud.fsu.deletecollection.end |
| Private Service Access - Delete End | com.oraclecloud.privateserviceaccess.deleteprivateserviceaccess.end |
| Work Request - Switch Module Stream Begin | com.oraclecloud.osmh.switchmodulestream.begin |
| Source - Create Begin | com.oraclecloud.applicationmigration.createsource.begin |
| Work Request - Install Bug Fix Windows Updates Begin | com.oraclecloud.osmh.installbugfixwindowsupdates.begin |
| Exadb VM Cluster - Delete Begin | com.oraclecloud.databaseservice.deleteexadbvmcluster.begin |
| OMA - Create Access Request End | com.oraclecloud.lockbox.createaccessrequest.end |
| MySQL - Generate HeatWave Cluster Memory Estimate Begin | com.oraclecloud.mysqlaas.generateheatwaveclustermemoryestimate.begin |
| Mesh - Update End | com.oraclecloud.servicemesh.updatemesh.end |
| Cache Database - Health Check | com.oraclecloud.zerolatency.healthcheckzerolatencydatabase |
| Media Workflow Job - Update | com.oraclecloud.mediaservices.updatemediaworkflowjob |
| DR Plan Execution - Delete Begin | com.oraclecloud.disasterrecovery.deletedrplanexecution.begin |
| Autonomous Container Database - Switchover Begin | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.switchover.begin |
| Autonomous Container Database - Information | com.oraclecloud.databaseservice.autonomous.container.database.information |
| Pluggable Database - Inplace Restore End | com.oraclecloud.databaseservice.pluggabledatabase.inplacerestore.end |
| Autonomous Container Database - Maintenance Scheduled | com.oraclecloud.databaseservice.autonomous.container.database.maintenance.scheduled |
| Instance - Scale Instance End | com.oraclecloud.blockchain.scaleplatforminstance.end |
| Autonomous Database - Long-term Backup Will Expire In 24 Hours | com.oraclecloud.databaseservice.autonomous.database.backup.longtermbackupexpiresinaday.reminder |
| Pipeline Run - Delete Begin | com.oraclecloud.datascience.deletepipelinerun.begin |
| Event - Create Lifecycle Promotion Event | com.oraclecloud.osmh.createevent.softwaresource.lifecyclepromotion |
| Audit Profile Retention Update - End | com.oraclecloud.datasafe.changeretention.end |
| Volume - Detach Begin | com.oraclecloud.computeapi.detachvolume.begin |
| Fleet - Delete Begin | com.oraclecloud.javamanagementservice.deletefleet.begin |
| ContainerScanTarget - Create End | com.oraclecloud.vulnerabilityscanning.createcontainerscantarget.end |
| DR Protection Group - Create Begin | com.oraclecloud.disasterrecovery.createdrprotectiongroup |
| Notebook Session - Deactivate Begin | com.oraclecloud.datascience.deactivatenotebooksession.begin |
| Forecasting - Create Data Asset | com.oraclecloud.aiserviceforecast.createdataasset |
| Forecasting - Create Forecast Begin | com.oraclecloud.aiserviceforecast.createforecast.begin |
| Forecasting - Create Forecast End | com.oraclecloud.aiserviceforecast.createforecast.end |
| Forecasting - Create Project | com.oraclecloud.aiserviceforecast.createproject |
| Language - Create Project | com.oraclecloud.aiservicelanguage.createproject |
| Masking Columns Patch - Begin | com.oraclecloud.datasafe.patchmaskingcolumns.begin |
| IngressGateway - Change Compartment Begin | com.oraclecloud.servicemesh.changeingressgatewaycompartment.begin |
| Index - Drop End | com.oraclecloud.nosql.dropindex.end |
| Report Generate - Begin | com.oraclecloud.datasafe.generatereport.begin |
| Database - Critical | com.oraclecloud.databaseservice.database.critical |
| Cache Database - Update End | com.oraclecloud.zerolatency.updatezerolatencydatabase.end |
| Work Request - Validate Software Source Begin | com.oraclecloud.osmh.validatesoftwaresource.begin |
| Public IP - Create | com.oraclecloud.virtualnetwork.createpublicip |
| Environment - Update Begin | com.oraclecloud.ohaaas.updateenvironment.begin |
| Network Security Group - Create | com.oraclecloud.virtualnetwork.createnetworksecuritygroup |
| BDS Instance - Create Nodes Backups End | com.oraclecloud.bds.cp.backupnodes.end |
| Connection Delete Begin | com.oraclecloud.odms.deleteconnection.begin |
| Work Request - Install Other Windows Updates Begin | com.oraclecloud.osmh.installotherwindowsupdates.begin |
| Backup Destination - Update | com.oraclecloud.databaseservice.updatebackupdestination |
| Cache Database - Stop Replication Agent Begin | com.oraclecloud.zerolatency.stopreplicationagent.begin |
| Harvest - End | com.oraclecloud.datacatalog.harvestjob.end |
| Internet Gateway - Delete | com.oraclecloud.virtualnetwork.deleteinternetgateway |
| SQL Firewall Collection Delete - Begin | com.oraclecloud.datasafe.deletesqlcollection.begin |
| Batch Job Pool - Stop | com.oraclecloud.batch.stopbatchjobpool |
| Security Policy Auto Create | com.oraclecloud.datasafe.autocreatesecuritypolicy |
| SMTP Credential - Create | com.oraclecloud.identitycontrolplane.createsmtpcredential |
| Lookup - Register | com.oraclecloud.logginganalytics.registerlookup |
| Update Custom Protection Rule | com.oraclecloud.waf.updatecustomprotectionrule |
| Job State Change | com.oraclecloud.odms.jobstatechange |
| Network Address List - Change Compartment Begin | com.oraclecloud.waf.changenetworkaddresslistcompartment.begin |
| DR Plan Execution - Retry Begin | com.oraclecloud.disasterrecovery.retrydrplanexecution.begin |
| Connection Create End | com.oraclecloud.odms.createconnection.end |
| Desktop Pool - Create | com.oraclecloud.ocidesktopservice.createdesktoppool |
| My Recovery Email - Update | com.oraclecloud.identitycontrolplane.updatemyrecoveryemail |
| Security Policy Deployment Update - End | com.oraclecloud.datasafe.updatesecuritypolicydeployment.end |
| Instance Pool - Detach Load Balancer Begin | com.oraclecloud.computemanagement.detachloadbalancer.begin |
| Batch Context - Create Begin | com.oraclecloud.batch.createbatchcontext.begin |
| BDS Instance - Refresh Resource Principal Begin | com.oraclecloud.bds.cp.refreshresourceprincipal.begin |
| VirtualDeployment - Delete End | com.oraclecloud.servicemesh.deletevirtualdeployment.end |
| OMA - Handle Access Request Begin | com.oraclecloud.lockbox.handleaccessrequest.begin |
| DeployArtifact - Update Begin | com.oraclecloud.devopsdeploy.updatedeployartifact.begin |
| Mirror Repository - Begin | com.oraclecloud.devopscoderepo.mirrorrepository.begin |
| Autonomous Database - Create End | com.oraclecloud.databaseservice.autonomous.database.instance.create.end |
| Data Store - Create End | com.oraclecloud.dataexchange.createdatastore.end |
| Exadb VM Cluster - Update End | com.oraclecloud.databaseservice.updateexadbvmcluster.end |
| Route Table - Create | com.oraclecloud.virtualnetwork.createroutetable |
| Assetsource - Delete Begin | com.oraclecloud.cloudbridge.deleteassetsource.begin |
| Exadata Infrastructure - Connectivity Status | com.oraclecloud.databaseservice.exadatainfrastructureconnectstatus |
| Node - Start Begin | com.oraclecloud.zerolatency.startzerolatencynode.begin |
| DR Plan Execution - CreateFailoverPreCheck Begin | com.oraclecloud.disasterrecovery.createfailoverprecheckdrplanexecution |
| DataRefresh - Estimate | com.oraclecloud.analyticswarehouse.pipeline.datarefresh.estimate |
| SQL Firewall Collection Create - Begin | com.oraclecloud.datasafe.createsqlcollection.begin |
| DR Plan Execution - Ignore End | com.oraclecloud.disasterrecovery.ignoredrplanexecution.end |
| Job - Create | com.oraclecloud.datatransferservice.addtransferjob |
| Distributed Database - Configure GSMs Begin | com.oraclecloud.globaldb.configuredistributeddatabasegsms.begin |
| Imaging - Delete | com.oraclecloud.computeimagingapi.deleteimage |
| Scheduled Job - Create | com.oraclecloud.osms.createscheduledjob |
| Appliance Export Job - Create | com.oraclecloud.datatransferservice.addapplianceexportjob |
| Exascale Database Storage Vault - Change Compartment End | com.oraclecloud.databaseservice.changeexascaledbstoragevaultcompartment.end |
| Database - Automatic Backup End | com.oraclecloud.databaseservice.automaticbackupdatabase.end |
| WebLogic Domain - Update | com.oraclecloud.weblogicmanagement.updatewlsdomain |
| Desktop Pool - Change Compartment | com.oraclecloud.ocidesktopservice.changedesktoppoolcompartment |
| Managed Instance - Scan Begin | com.oraclecloud.weblogicmanagement.scanmanagedinstance.begin |
| Create Boot Volume Backup Begin | com.oraclecloud.blockvolumes.createbootvolumebackup.begin |
| Lookup Properties - Update | com.oraclecloud.logginganalytics.updatelookup |
| Backup Destination - Create | com.oraclecloud.databaseservice.createbackupdestination |
| Group - Delete | com.oraclecloud.identitycontrolplane.deletegroup |
| Create Iot Domain - Begin | com.oraclecloud.iot.createiotdomain.begin |
| Assetsource - Create Begin | com.oraclecloud.cloudbridge.createassetsource.begin |
| Global Autonomous Database - Configure Sharding End | com.oraclecloud.globaldb.configuresharding.end |
| Assign Operator Control - Delete | com.oraclecloud.operatorcontrol.deleteoperatorcontrolassignment |
| DFI Cluster: Create Begin | com.oraclecloud.dataflowinteractive.createinteractivecluster.begin |
| DeployEnvironment - Delete End | com.oraclecloud.devopsdeploy.deletedeployenvironment.end |
| Model Deployment - Deactivate Begin | com.oraclecloud.datascience.deactivatemodeldeployment.begin |
| Managed Instance - Get Windows Update Details | com.oraclecloud.osmh.getwindowsupdatedetails |
| Update Waas Policy End | com.oraclecloud.waf.updatewaaspolicy.end |
| Managed Database - Warning | com.oraclecloud.databasemanagement.manageddatabase.warning |
| Event - Create Kernel Oops Event | com.oraclecloud.osmh.createevent.kerneloops |
| Sensitive Data Model Delete - Begin | com.oraclecloud.datasafe.deletesensitivedatamodel.begin |
| VirtualServiceRouteTable - Delete Begin | com.oraclecloud.servicemesh.deletevirtualserviceroutetable.begin |
| Bastion - Create Session End | com.oraclecloud.bastion.createsession.end |
| Auto Approve - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.autoapprovedelegatedresourceaccessrequest |
| Unified Audit Policy Bulk Create - Begin | com.oraclecloud.datasafe.bulkcreateunifiedauditpolicy.begin |
| Fusion Environment Family - Change Compartment Begin | com.oraclecloud.fusionapps.changefusionenvironmentfamilycompartment.begin |
| Autonomous Database - Restore End | com.oraclecloud.databaseservice.autonomous.database.restore.end |
| Language - Create Model Endpoint End | com.oraclecloud.aiservicelanguage.createmodelendpoint.end |
| BDS Api Key Instance - Create Api Key End | com.oraclecloud.bds.cp.createbdsapikey.end |
| Work Request - Sync Agent Config Begin | com.oraclecloud.osmh.syncagentconfig.begin |
| Exadb VM Cluster - Change Compartment Begin | com.oraclecloud.databaseservice.changeexadbvmclustercompartment.begin |
| BDS Instance - AutoscaleRun - Add Node | com.oraclecloud.bds.autoscale.cp.autoscalerunaddnode |
| VMware Solution - Inplace Upgrade ESXi Host End | com.oraclecloud.vmwaresolution.inplaceupgrade.end |
| Resource Schedule - Delete | com.oraclecloud.resourcescheduler.deleteschedule |
| Fusion Environment Family - Update Begin | com.oraclecloud.fusionapps.updatefusionenvironmentfamily.begin |
| Update Boot Volume Kms Key Begin | com.oraclecloud.blockvolumes.updatebootvolumekmskey.begin |
| Resource Analytics Instance - Delete End | com.oraclecloud.resourceanalytics.deleteresourceanalyticsinstance.end |
| Visual Builder Studio - Delete Instance - begin | com.oraclecloud.vbstudioinst.deletevbsinstance.begin |
| Fleet - Delete End | com.oraclecloud.javamanagementservice.deletefleet.end |
| Portfolio - Get | com.oraclecloud.atat.getportfolio |
| Connection - Delete End | com.oraclecloud.devopsbuild.deleteconnection.end |
| NAT Gateway - Delete | com.oraclecloud.natgateway.deletenatgateway |
| FsuAction - Apply Success | com.oraclecloud.fsu.fsuaction.apply.success |
| Integration Instance - Stop End | com.oraclecloud.integration.stopintegrationinstance.end |
| Database - Change Database Key Store Type End | com.oraclecloud.databaseservice.changedatabasekeystoretype.end |
| Run Job - End | com.oraclecloud.datalake.createjobrun.end |
| Run Job - Begin | com.oraclecloud.datalake.createjobrun.begin |
| Work Request - Register Managed Instance Begin | com.oraclecloud.osmh.registermanagedinstance.begin |
| Desktop - Start | com.oraclecloud.ocidesktopservice.startdesktop |
| Database - Move End | com.oraclecloud.databaseservice.movedatabase.end |
| Distributed Autonomous Database - Validate Network Begin | com.oraclecloud.globaldb.validatedistributedautonomousdatabasenetwork.begin |
| Work Request - Update Management Station Software End | com.oraclecloud.osmh.updatemanagementstationsoftware.end |
| Associations - Upsert | com.oraclecloud.logginganalytics.upsertassociations |
| MySQL - Resume Channel End | com.oraclecloud.mysqlaas.resumechannel.end |
| Node - Move | com.oraclecloud.oraclerovingedgeinfrastructure.movenode |
| Budget - Delete | com.oraclecloud.budgets.deletebudget |
| Execute Task - Begin | com.oraclecloud.dataintegration.createtaskrun.begin |
| Stream Cell Assignment Group - Create | com.oraclecloud.mediaservices.createstreamcellassignmentgroup |
| Event - Create Install Packages Event | com.oraclecloud.osmh.createevent.softwareupdate.installpackages |
| Asset - Delete Begin | com.oraclecloud.dataexchange.deleteasset.begin |
| MeshIngressGatewayRouteTable - Delete End | com.oraclecloud.servicemesh.deleteingressgatewayroutetable.end |
| Table - Drop Replica Begin | com.oraclecloud.nosql.dropreplica.begin |
| Audit Profile Delete - End | com.oraclecloud.datasafe.deleteauditprofile.end |
| Operator Logout - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.serviceprovideroperatorlogout |
| Managed Instance - Validate Software Source | com.oraclecloud.osmh.validatesoftwaresource |
| Update Global Accelerator Routing Policy Begin | com.oraclecloud.gax.public.api.updateroutingpolicy.begin |
| Imaging - Export Begin | com.oraclecloud.computeapi.exportimage.begin |
| Managed Instance - Install Other Windows Updates | com.oraclecloud.osmh.installotherwindowsupdates |
| Resource Categories - Remove | com.oraclecloud.logginganalytics.removeresourcecategories |
| Sensitive Data Model Referential Relation Delete - Begin | com.oraclecloud.datasafe.deletereferentialrelation.begin |
| VM Cluster - Terminate Virtual Machine End | com.oraclecloud.databaseservice.vmclusterterminatevirtualmachine.end |
| VM Cluster - Update End | com.oraclecloud.databaseservice.updatevmcluster.end |
| Delete Iot DomainGroup - Begin | com.oraclecloud.iot.deleteiotdomaingroup.begin |
| Bastion - Delete Bastion End | com.oraclecloud.bastion.deletebastion.end |
| ContainerScanRecipe - Create | com.oraclecloud.vulnerabilityscanning.createcontianerscanrecipe |
| Job State Waiting | com.oraclecloud.odms.jobstatewaiting |
| Distributed Database - Prevalidate | com.oraclecloud.globaldb.prevalidatedistributeddatabase |
| Web Application Firewall - Change Compartment End | com.oraclecloud.waf.changewebappfirewallcompartment.end |
| Global Autonomous Database - Fetch Shardable Cloud Autonomous VM Clusters | com.oraclecloud.globaldb.fetchshardablecloudautonomousvmclusters |
| User - Create | com.oraclecloud.identitycontrolplane.createuser |
| Delegated Authentication - Initiate Activation | com.oraclecloud.identitycontrolplane.initiatedelegatedauthenticationactivation |
| Sensitive Data Detected | com.oraclecloud.dataprotection.sensitivedatadetected |
| Global Database Private Endpoint - Delete Begin | com.oraclecloud.globaldb.deleteprivateendpoint.begin |
| Visual Builder Studio - Create Instance - end | com.oraclecloud.vbstudioinst.createvbsinstance.end |
| DeleteAsset | com.oraclecloud.cloudbridge.deleteasset |
| BDS Instance - AutoscaleRun - Scale Up | com.oraclecloud.bds.autoscale.cp.autoscaleup |
| Security Policy Deployment Update - Begin | com.oraclecloud.datasafe.updatesecuritypolicydeployment.begin |
| Event - Create Update Software Source Event | com.oraclecloud.osmh.createevent.softwaresource.updatesoftwaresource |
| Update Caching Rules End | com.oraclecloud.waf.updatecachingrules.end |
| Language - Delete Project | com.oraclecloud.aiservicelanguage.deleteproject |
| Forecasting - Delete Forecast | com.oraclecloud.aiserviceforecast.deleteforecast |
| Forecasting - Delete Data Asset | com.oraclecloud.aiserviceforecast.deletedataasset |
| Forecasting - Delete Project | com.oraclecloud.aiserviceforecast.deleteproject |
| Work Request - Install All Security Windows Updates Begin | com.oraclecloud.osmh.installsecuritywindowsupdates.begin |
| Batch Job - Cancel End | com.oraclecloud.batch.cancelbatchjob.end |
| Work Request - Update All Packages End | com.oraclecloud.osmh.updateallpackages.end |
| Create On-Prem Connector - Begin | com.oraclecloud.datasafe.createonpremconnector.begin |
| Database Tools Private Endpoint - Change Compartment End | com.oraclecloud.dbtoolsserviceapi.changedatabasetoolsprivateendpointcompartment.end |
| External MySQL DB System - Disable Database Management Begin | com.oraclecloud.databasemanagement.externalmysqlresource.dbsystem.disablemgmt.begin |
| Update Feature flag | com.oraclecloud.appconfiguration.updatefeatureflag |
| BDS Instance - Delete Nodes Backups Begin | com.oraclecloud.bds.cp.deletenodesbackups.begin |
| Application Bundle - Create End | com.oraclecloud.ohaaas.createapplicationbundle.end |
| Work Request - Sync Metadata Begin | com.oraclecloud.osmh.syncmetadata.begin |
| Autonomous Data Guard Association - Failover End | com.oraclecloud.databaseservice.failoverautonomousdataguardassociation.end |
| SMTP Credential - Update | com.oraclecloud.identitycontrolplane.updatesmtpcredential |
| HostPortScanResult - ChangeCompartment | com.oraclecloud.vulnerabilityscanning.changehostportscanresultcompartment |
| Work Request - Cancel | com.oraclecloud.privateserviceaccess.cancelpsaworkrequest |
| FsuCycle - Delete Begin | com.oraclecloud.fsu.deletefsucycle.begin |
| Update Iot Domain - Begin | com.oraclecloud.iot.updateiotdomain.begin |
| AccessPolicy - Delete Begin | com.oraclecloud.servicemesh.deleteaccesspolicy.begin |
| Change Password | com.oraclecloud.identitysignon.changepassword |
| VNIC - Detach End | com.oraclecloud.computeapi.detachvnic.end |
| VNIC - Detach Begin | com.oraclecloud.computeapi.detachvnic.begin |
| Group - Create | com.oraclecloud.identitycontrolplane.creategroup |
| VirtualDeployment - Create Begin | com.oraclecloud.servicemesh.createvirtualdeployment.begin |
| VMware Solution - Inplace Upgrade ESXi Host Begin | com.oraclecloud.vmwaresolution.inplaceupgrade.begin |
| Appliance - Create | com.oraclecloud.datatransferservice.addtransferappliance |
| Data Store - Create Begin | com.oraclecloud.dataexchange.createdatastore.begin |
| Pluggable Database - Relocate Begin | com.oraclecloud.databaseservice.pluggabledatabase.relocate.begin |
| Identity Provider Group - Create | com.oraclecloud.identitycontrolplane.createidentityprovidergroup |
| Costs by Clin - Get | com.oraclecloud.atat.getclincost |
| Distributed Database Private Endpoint - Delete Begin | com.oraclecloud.globaldb.deletedistributeddatabaseprivateendpoint.begin |
| ContainerScanTarget - Update End | com.oraclecloud.vulnerabilityscanning.updatecontainerscantarget.end |
| Key - Create Begin | com.oraclecloud.keymanagementservice.createkey.begin |
| VLAN - Update | com.oraclecloud.virtualnetwork.updatevlan |
| MeshIngressGatewayRouteTable - Delete Begin | com.oraclecloud.servicemesh.deleteingressgatewayroutetable.begin |
| DR Plan Execution - CreateFailover End | com.oraclecloud.disasterrecovery.createfailoverdrplanexecution.end |
| Database - Information | com.oraclecloud.databaseservice.database.information |
| Application Data Platform - PodDb Delete End | com.oraclecloud.applicationdataplatform.deletepoddb.end |
| Pluggable database - Enable Database Management Service End | com.oraclecloud.databaseservice.enablepdbmanagement.end |
| MeshIngressGatewayRouteTable - Create Begin | com.oraclecloud.servicemesh.createingressgatewayroutetable.begin |
| Recovery Service Subnet - Delete Begin | com.oraclecloud.autonomousrecoveryservice.deleterecoveryservicesubnet.begin |
| Distributed Database Private Endpoint - Create Begin | com.oraclecloud.globaldb.createdistributeddatabaseprivateendpoint.begin |
| Event - Scheduled Job Status Change | com.oraclecloud.osmh.event.scheduledjob |
| Bastion - Create Session Begin | com.oraclecloud.bastion.createsession.begin |
| DeployPipeline - Create End | com.oraclecloud.devopsdeploy.createdeploypipeline.end |
| FsuAction - Create End | com.oraclecloud.fsu.createaction.end |
| PathAnalyzerTest - Create | com.oraclecloud.vnconfigadvisor.createpathanalyzertest |
| Volume - Attach End | com.oraclecloud.computeapi.attachvolume.end |
| Lustre File System - Change Compartment Begin | com.oraclecloud.lustrefilestorage.changelustrefilesystemcompartment.begin |
| Distributed Database - Generate Wallet | com.oraclecloud.globaldb.generatedistributeddatabasewallet |
| VM Cluster Network - Network Validation File Download | com.oraclecloud.databaseservice.downloadvmclusternetworkconfigfile |
| Change Volume Compartment End | com.oraclecloud.blockvolumes.changevolumecompartment.end |
| Instance - Scale Instance Up or Down End | com.oraclecloud.analytics.scaleanalyticsinstance.end |
| DR Plan - Create End | com.oraclecloud.disasterrecovery.createdrplan.end |
| Work Request - Update Packages End | com.oraclecloud.osmh.updatepackages.end |
| BDS Instance - Update Replace Configuration End | com.oraclecloud.bds.cp.updatereplaceconfig.end |
| Protection Policy - Create End | com.oraclecloud.autonomousrecoveryservice.createprotectionpolicy.end |
| Swift Password - Delete | com.oraclecloud.identitycontrolplane.deleteswiftpassword |
| UpdateProject - end | com.oraclecloud.devopsproject.updateproject.begin |
| Distributed Database - Download GSM Certificate Signing Request | com.oraclecloud.globaldb.downloaddistributeddatabasegsmcertificatesigningrequest |
| External Pluggable Database - Enable Stack Monitoring Service End | com.oraclecloud.databaseservice.enablestackmonitoringforexternalpluggabledatabase.end |
| Distributed Database - Change Compartment End | com.oraclecloud.globaldb.changedistributeddatabasecompartment.end |
| GGS Pipeline - Stop Pipeline Begin | com.oraclecloud.goldengate.stoppipeline.begin |
| Assetsource - Refresh Begin | com.oraclecloud.cloudbridge.refreshassetsource.begin |
| Cache Database - Create End | com.oraclecloud.zerolatency.createzerolatencydatabase.end |
| Sensitive Discovery Job Create - End | com.oraclecloud.datasafe.creatediscoveryjob.end |
| Stream Cell Assignment Group - Update | com.oraclecloud.mediaservices.updatestreamcellassignmentgroup |
| Support Account - Unlink | com.oraclecloud.identitycontrolplane.unlinksupportaccount |
| Approve Delegated Resource Access Request - End | com.oraclecloud.delegateaccesscontrol.approvedelegatedresourceaccessrequest.end |
| Distributed Database - Validate Network End | com.oraclecloud.globaldb.validatedistributeddatabasenetwork.end |
| Web Application Acceleration - Change Compartment End | com.oraclecloud.waa.changewebappaccelerationcompartment.end |
| Device - Delete | com.oraclecloud.datatransferservice.deletetransferdevice |
| DB Node - Update | com.oraclecloud.databaseservice.updatedbnode |
| DB Node - Update Begin | com.oraclecloud.databaseservice.dbnodeaction.begin |
| Autonomous Cloud VM Cluster - Information | com.oraclecloud.databaseservice.autonomous.cloudautonomousvmcluster.information |
| VMware Solution - List Supported Commitments | com.oraclecloud.vmwaresolution.listsupportedcommitments |
| Cache Database - Load Begin | com.oraclecloud.zerolatency.loadzerolatencydatabase.begin |
| Lookup - Delete | com.oraclecloud.logginganalytics.deletelookup |
| Data Lake - Create End | com.oraclecloud.datalake.createdatalake.end |
| BDS Instance - Delete Replace Configuration End | com.oraclecloud.bds.cp.deletereplaceconfig.end |
| Key - Enable Begin | com.oraclecloud.keymanagementservice.enablekey.begin |
| VirtualService - Delete Begin | com.oraclecloud.servicemesh.deletevirtualservice.begin |
| Event - Create Remove Packages Event | com.oraclecloud.osmh.createevent.softwareupdate.removepackages |
| Autonomous VM Cluster - Critical | com.oraclecloud.databaseservice.autonomous.vmcluster.critical |
| Cache Database - Delete Diagnostics End | com.oraclecloud.zerolatency.deletezerolatencydatabasediagnostics.end |
| GGS Pipeline - Running | com.oraclecloud.goldengate.pipeline.staterunning |
| DeployEnvironment - Create End | com.oraclecloud.devopsdeploy.createdeployenvironment.end |
| Oce Instance - Delete Begin | com.oraclecloud.oce.deleteoceinstance.begin |
| IngressGateway - Update End | com.oraclecloud.servicemesh.updateingressgateway.end |
| Event - Create Reboot Started Event | com.oraclecloud.osmh.createevent.reboot.rebootstarted |
| OCI Cache Cluster - Delete Begin | com.oraclecloud.redisservice.deleterediscluster.begin |
| BDS Instance - AutoscaleRun - Remove Node | com.oraclecloud.bds.autoscale.cp.autoscalerunremovenode |
| Sensitive Type Create - Begin | com.oraclecloud.datasafe.createsensitivetype.begin |
| External Non-Container Database - Enable Stack Monitoring Service Begin | com.oraclecloud.databaseservice.enablestackmonitoringforexternalnoncontainerdatabase.begin |
| Oracle managed database software update awaiting user action | com.oraclecloud.databaseservice.managedsoftwareupdateawaitinguseraction |
| Recovery Service Subnet - Create End | com.oraclecloud.autonomousrecoveryservice.createrecoveryservicesubnet.end |
| Job Abort End | com.oraclecloud.odms.abortjob.end |
| Container Instance - Delete Container Instance Begin | com.oraclecloud.containerinstances.deletecontainerinstance.begin |
| Connection - Create Begin | com.oraclecloud.devopsbuild.createconnection.begin |
| Exadb VM Cluster - Audit | com.oraclecloud.databaseservice.exadbvmcluster.audit |
| ContainerScanTarget - Update Begin | com.oraclecloud.vulnerabilityscanning.updatecontainerscantarget.begin |
| Instance Configuration - Create | com.oraclecloud.computemanagement.createinstanceconfiguration |
| DB System - Upgrade End | com.oraclecloud.databaseservice.upgradedbsystem.end |
| Instance Pool - Update Begin | com.oraclecloud.computemanagement.updateinstancepool.begin |
| ContainerScanTarget - ChangeCompartment | com.oraclecloud.vulnerabilityscanning.changecontainerscantargetcompartment |
| BDS Instance - Add Block Storage End | com.oraclecloud.bds.cp.addblockstorage.end |
| Waf Policy - Delete End | com.oraclecloud.waf.deletewebappfirewallpolicy.end |
| Update Boot Volume Kms Key End | com.oraclecloud.blockvolumes.updatebootvolumekmskey.end |
| Create Iot DomainGroup - Begin | com.oraclecloud.iot.createiotdomaingroup.begin |
| GGS Pipeline - Stop Pipeline End | com.oraclecloud.goldengate.stoppipeline.end |
| Log Group - Delete | com.oraclecloud.logginganalytics.deleteloganalyticsloggroup |
| Backup - Delete Begin | com.oraclecloud.postgresql.deletebackup.begin |
| DR Protection Group - UpdateRole End | com.oraclecloud.disasterrecovery.updatedrprotectiongrouprole.end |
| FsuAction - Delete Begin | com.oraclecloud.fsu.deletefsuaction.begin |
| ContainerScanTarget - Delete End | com.oraclecloud.vulnerabilityscanning.deletecontainerscantarget.end |
| Volume - Attach Begin | com.oraclecloud.computeapi.attachvolume.begin |
| Backup - Delete End | com.oraclecloud.postgresql.deletebackup.end |
| Assetsource - Update Begin | com.oraclecloud.cloudbridge.updateassetsource.begin |
| Network Source - Update | com.oraclecloud.identitycontrolplane.updatenetworksource |
| Package - Create | com.oraclecloud.datatransferservice.addtransferpackage |
| Appliance Export Job - Delete | com.oraclecloud.datatransferservice.deleteapplianceexportjob |
| BuildPipeline - Create Begin | com.oraclecloud.devopsbuild.createbuildpipeline.begin |
| Delegated Authentication User - Create | com.oraclecloud.identitycontrolplane.createdelegatedauthenticationuser |
| Revoke Delegated Resource Access Request - Begin | com.oraclecloud.delegateaccesscontrol.revokedelegatedresourceaccessrequest.begin |
| Application - Create | com.oraclecloud.dataflow.createapplication |
| Imaging - Update | com.oraclecloud.computeimagingapi.updateimage |
| Pipeline - Delete End | com.oraclecloud.datascience.deletepipeline.end |
| Access Request - Closed | com.oraclecloud.operatorcontrol.closedaccessrequest |
| Detection Rule - Delete | com.oraclecloud.logginganalytics.deletescheduledtask |
| Group - Update | com.oraclecloud.identitycontrolplane.updategroup |
| ContianerScanRecipe - Delete | com.oraclecloud.vulnerabilityscanning.deletecontainerscanrecipe |
| Instance - Delete Instance Begin | com.oraclecloud.blockchain.deleteplatforminstance.begin |
| Data Lake - Create Begin | com.oraclecloud.datalake.createdatalake.begin |
| DR Plan Execution - Cancel Begin | com.oraclecloud.disasterrecovery.canceldrplanexecution.begin |
| Instance - Action Begin | com.oraclecloud.computeapi.instanceaction.begin |
| Application Data Platform - PodDb Restore Point Create End | com.oraclecloud.applicationdataplatform.createpoddbrestorepoint.end |
| Identity Provider - Delete | com.oraclecloud.identitycontrolplane.deleteidentityprovider |
| Audit Policy Provision - End | com.oraclecloud.datasafe.provisionauditpolicy.end |
| Update Boot Volume Begin | com.oraclecloud.blockvolumes.updatebootvolume.begin |
| Data Guard Failover - Begin | com.oraclecloud.databaseservice.dataguardfailover.begin |
| NodePool - Delete Begin | com.oraclecloud.clustersapi.deletenodepool.begin |
| Masking Job - End | com.oraclecloud.datasafe.maskdata.end |
| Visual Builder Studio - Update Instance - end | com.oraclecloud.vbstudioinst.updatevbsinstance.end |
| Batch Job Pool - Start | com.oraclecloud.batch.startbatchjobpool |
| Instance - Preemption Action | com.oraclecloud.computeapi.instancepreemptionaction |
| Mesh - Delete Begin | com.oraclecloud.servicemesh.deletemesh.begin |
| Interactive Login | com.oraclecloud.identitysignon.interactivelogin |
| GGS Deployment - Upgrade Maintenance Scheduled | com.oraclecloud.goldengate.upgrademaintenanceschedule |
| Work Request - Switch Module Stream End | com.oraclecloud.osmh.switchmodulestream.end |
| LicenseManager - Delete LicenseRecord | com.oraclecloud.licensemanager.deletelicenserecord |
| DR Protection Group - Create End | com.oraclecloud.disasterrecovery.createdrprotectiongroup.end |
| Distributed Autonomous Database - Upload Signed Certificate And Generate Wallet End | com.oraclecloud.globaldb.uploaddistributedautonomousdatabasesignedcertificateandgeneratewallet.end |
| Imaging - Create Begin | com.oraclecloud.computeapi.createimage.begin |
| Batch Task Environment - Change Compartment End | com.oraclecloud.batch.changebatchtaskenvironmentcompartment.end |
| Autonomous Cloud VM Cluster - Terminate Begin | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.terminate.begin |
| Oracle managed database software update scheduled | com.oraclecloud.databaseservice.managedsoftwareupdatescheduled |
| Masking Policy Delete - Begin | com.oraclecloud.datasafe.deletemaskingpolicy.begin |
| Distributed Database - Stop End | com.oraclecloud.globaldb.stopdistributeddatabase.end |
| FsuCollection - Create Begin | com.oraclecloud.fsu.createfsucollection.begin |
| Service Instance - Delete End | com.oraclecloud.zerolatency.deletezerolatency.end |
| Table - Drop Replica End | com.oraclecloud.nosql.dropreplica.end |
| Distributed Autonomous Database - Patch End | com.oraclecloud.globaldb.patchdistributedautonomousdatabase.end |
| App Configuration Change compartment - End | com.oraclecloud.appconfiguration.changecompartment.end |
| Autonomous VM Cluster - Warning | com.oraclecloud.databaseservice.autonomous.vmcluster.warning |
| Cluster - Move | com.oraclecloud.oraclerovingedgeinfrastructure.movecluster |
| Trigger - Create End | com.oraclecloud.devopsbuild.createtrigger.end |
| Delete Http Redirect Begin | com.oraclecloud.waf.deletehttpredirect.begin |
| Exascale Database Storage Vault - Update Begin | com.oraclecloud.databaseservice.updateexascaledbstoragevault.begin |
| Start Workspace - End | com.oraclecloud.dataintegration.startdisworkspace.end |
| Tenancy Attachment - Delete End | com.oraclecloud.resourceanalytics.deletetenancyattachment.end |
| Update Volume Group Backup | com.oraclecloud.blockvolumes.updatevolumegroupbackup |
| Distributed Database - Update | com.oraclecloud.globaldb.updatedistributeddatabase |
| Purge Cache End | com.oraclecloud.waf.purgecache.end |
| Masking Library Format Delete | com.oraclecloud.datasafe.deletelibrarymaskingformat |
| SubmitHistoricalMetrics | com.oraclecloud.cloudbridge.submithistoricalmetrics |
| PathAnalysis - Async Begin | com.oraclecloud.vnconfigadvisor.getpathanalysis.begin |
| SQL Firewall Collection Delete - End | com.oraclecloud.datasafe.deletesqlcollection.end |
| DFI Cluster: Delete Begin | com.oraclecloud.dataflowinteractive.deleteinteractivecluster.begin |
| Pipeline Run - Delete End | com.oraclecloud.datascience.deletepipelinerun.end |
| Service Provider Interaction Response | com.oraclecloud.delegateaccesscontrol.serviceprovideroperatorinteractionresponse |
| ExaCompute VmInstance - Migrate Begin | com.oraclecloud.exacompute.migratevminstance.begin |
| ExaCompute VmInstance - Migrate End | com.oraclecloud.exacompute.migratevminstance.end |
| DB Home - Create Begin | com.oraclecloud.databaseservice.createdbhome.begin |
| Maintenance Schedule - Create Begin | com.oraclecloud.exacompute.createexacomputemaintenanceschedule.begin |
| Maintenance Schedule - Create End | com.oraclecloud.exacompute.createexacomputemaintenanceschedule.end |
| Maintenance Schedule - Safe Reboot Migration Begin | com.oraclecloud.exacompute.saferebootmigrationstart.begin |
| Maintenance Schedule - Safe Reboot Migration End | com.oraclecloud.exacompute.saferebootmigrationstart.end |
| Maintenance Schedule - Maintenance Window Begin | com.oraclecloud.exacompute.maintenancewindowstart.begin |
| Maintenance Schedule - Maintenance Window End | com.oraclecloud.exacompute.maintenancewindowstart.end |
| Maintenance Schedule - Delete Begin | com.oraclecloud.exacompute.deleteexacomputemaintenanceschedule.begin |
| Maintenance Schedule - Delete End | com.oraclecloud.exacompute.deleteexacomputemaintenanceschedule.end |
| Maintenance Schedule - Update Begin | com.oraclecloud.exacompute.updateexacomputemaintenanceschedule.begin |
| Maintenance Schedule - Update End | com.oraclecloud.exacompute.updateexacomputemaintenanceschedule.end |
| ExaCompute VmAction - Restart Begin | com.oraclecloud.exacompute.exacomputevmactionrestart.begin |
| ExaCompute VmAction - Restart End | com.oraclecloud.exacompute.exacomputevmactionrestart.end |
| ExaCompute VmAction - Start Begin | com.oraclecloud.exacompute.exacomputevmactionstart.begin |
| ExaCompute VmCluster - Create End | com.oraclecloud.exacompute.createexacomputevmcluster.end |
| ExaCompute VmCluster - Add Vminstances Begin | com.oraclecloud.exacompute.addvminstances.begin |
| ExaCompute VmCluster - Add Vminstances End | com.oraclecloud.exacompute.addvminstances.end |
| ExaCompute VmAction - Start End | com.oraclecloud.exacompute.exacomputevmactionstart.end |
| ExaCompute VmCluster - Delete Begin | com.oraclecloud.exacompute.deleteexacomputevmcluster.begin |
| ExaCompute VmAction - Stop Begin | com.oraclecloud.exacompute.exacomputevmactionstop.begin |
| ExaCompute VmCluster - Create Begin | com.oraclecloud.exacompute.createexacomputevmcluster.begin |
| ExaCompute VmAction - Stop End | com.oraclecloud.exacompute.exacomputevmactionstop.end |
| ExaCompute VmCluster - Delete End | com.oraclecloud.exacompute.deleteexacomputevmcluster.end |
| ExaCompute - Create Bonding Begin | com.oraclecloud.exacompute.createexacomputebonding.begin |
| ExaCompute - Create Bonding End | com.oraclecloud.exacompute.createexacomputebonding.end |
| ExaComputeNode - Evacuate Begin | com.oraclecloud.exacompute.evacuatenode.begin |
| ExaComputeNode - Evacuate End | com.oraclecloud.exacompute.evacuatenode.end |
| ExaCompute Instance - Migrate Begin | com.oraclecloud.exacompute.migrateinstance.begin |
| ExaCompute Instance - Migrate End | com.oraclecloud.exacompute.migrateinstance.end |
| ExaCompute - Delete Bonding Begin | com.oraclecloud.exacompute.deleteexacomputebonding.begin |
| ExaCompute - Delete Bonding End | com.oraclecloud.exacompute.deleteexacomputebonding.end |
| Create Stack - Begin | com.oraclecloud.dataintelligencefoundation.createstack.begin |
| Table - Alter End | com.oraclecloud.nosql.altertable.end |
| Database Tools Private Endpoint - Create End | com.oraclecloud.dbtoolsserviceapi.createdatabasetoolsprivateendpoint.end |
| Web Application Acceleration Policy - Change Compartment Begin | com.oraclecloud.waa.changewebappaccelerationpolicycompartment.begin |
| SQL Firewall Policy Delete - End | com.oraclecloud.datasafe.deletesqlfirewallpolicy.end |
| Protection Policy - Change Compartment End | com.oraclecloud.autonomousrecoveryservice.changeprotectionpolicycompartment.end |
| Create Waas Policy Begin | com.oraclecloud.waf.createwaaspolicy.begin |
| Vault - Schedule Deletion Begin | com.oraclecloud.keymanagementservice.schedulevaultdeletion.begin |
| External MySQL DB System - Register | com.oraclecloud.databasemanagement.externalmysqlresource.dbsystem.register |
| Connection - Update Begin | com.oraclecloud.devopsbuild.updateconnection.begin |
| Application Bundle - Create Begin | com.oraclecloud.ohaaas.createapplicationbundle.begin |
| Network Address List - Delete Begin | com.oraclecloud.waf.deletenetworkaddresslist.begin |
| SQL Firewall Collection Stop - Begin | com.oraclecloud.datasafe.stopsqlcollection.begin |
| Application Data Platform - PodDb Backup Begin | com.oraclecloud.applicationdataplatform.createpoddbbackup.begin |
| Autoscaling Configuration - Create | com.oraclecloud.autoscaling.createautoscalingconfiguration |
| Unified Audit Policy Create - End | com.oraclecloud.datasafe.createunifiedauditpolicy.end |
| DB Home - Patch Begin | com.oraclecloud.databaseservice.patchdbhome.begin |
| Notebook Session - Activate Begin | com.oraclecloud.datascience.activatenotebooksession.begin |
| RevCycleEnvironment - Create End | com.oraclecloud.ircscontrolplaneapi.createrevcycleenvironment.end |
| Web Application Firewall - Update End | com.oraclecloud.waf.updatewebappfirewall.end |
| Create Address List | com.oraclecloud.waf.createaddresslist |
| Fusion Environment Family - Create End | com.oraclecloud.fusionapps.createfusionenvironmentfamily.end |
| Auth Token - Create | com.oraclecloud.identitycontrolplane.createauthtoken |
| WebLogic Domain - Delete | com.oraclecloud.weblogicmanagement.deletewlsdomain |
| MySQL - Reset Channel Begin | com.oraclecloud.mysqlaas.resetchannel.begin |
| Web Application Acceleration Policy - Update End | com.oraclecloud.waa.updatewebappaccelerationpolicy.end |
| Private Service Access - Change Compartment End | com.oraclecloud.privateserviceaccess.changeprivateserviceaccesscompartment.end |
| BDS Instance - Configure Remove Kafka Begin | com.oraclecloud.bds.cp.removekafka.begin |
| BDS Instance - Create Resource Principal Configuration End | com.oraclecloud.bds.cp.createresourceprincipalconfiguration.end |
| Sensitive Data Model Delete - End | com.oraclecloud.datasafe.deletesensitivedatamodel.end |
| Route Table - Delete | com.oraclecloud.virtualnetwork.deleteroutetable |
| VM Cluster Network - Update End | com.oraclecloud.databaseservice.updatevmclusternetwork.end |
| Pluggable Database - Convert to Regular Begin | com.oraclecloud.databaseservice.pluggabledatabase.converttoregular.begin |
| Work Request - Install Module Profiles End | com.oraclecloud.osmh.installmoduleprofiles.end |
| Table - Drop End | com.oraclecloud.nosql.droptable.end |
| FsuCollection - Delete Begin | com.oraclecloud.fsu.deletefsucollection.begin |
| Delete Mount Target | com.oraclecloud.filestorage.deletemounttarget |
| Oracle managed DB Home deletion started | com.oraclecloud.databaseservice.oraclemanageddbhomedeletionstarted |
| Detection Rule - Resume | com.oraclecloud.logginganalytics.resumescheduledtask |
| Kafka Config - Create | com.oraclecloud.rawfkaapiprod.createkafkaclusterconfig |
| DFI Cluster: Get Cluster | com.oraclecloud.dataflowinteractive.getinteractivecluster |
| Autonomous Container Database - Critical | com.oraclecloud.databaseservice.autonomous.container.database.critical |
| Cache Database - Delete Begin | com.oraclecloud.zerolatency.deletezerolatencydatabase.begin |
| Autonomous Container Database - Convert To Physical Standby Begin | com.oraclecloud.databaseservice.autonomous.container.database.physical.standby.conversion.begin |
| Key - Cancel Deletion Begin | com.oraclecloud.keymanagementservice.cancelkeydeletion.begin |
| Vault - Restore Begin | com.oraclecloud.keymanagementservice.restorevault.begin |
| Autonomous Database - Update Permission Level Begin | com.oraclecloud.databaseservice.updateautonomousdatabasepermissionlevel.begin |
| Exascale Database Storage Vault - Delete Begin | com.oraclecloud.databaseservice.deleteexascaledbstoragevault.begin |
| BDS Metastore Configuration Instance - Activate Metastore Configuration End | com.oraclecloud.bds.cp.activatebdsmetastoreconfiguration.end |
| Model - Update | com.oraclecloud.datascience.updatemodel |
| Autonomous Cloud VM Cluster - maintenance begin | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.maintenance.begin |
| Oracle managed software update staging started | com.oraclecloud.databaseservice.oraclemanageddbhomestagestarted |
| Event - Disable Module Streams Event | com.oraclecloud.osmh.createevent.softwaresource.disablemodulestreams |
| Create Stack - End | com.oraclecloud.dataintelligencefoundation.createstack.end |
| App Configuration Import - End | com.oraclecloud.appconfiguration.importappconfiguration.end |
| Autonomous Cloud VM Cluster - maintenance scheduled | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.maintenance.scheduled |
| App Configuration Delete - End | com.oraclecloud.appconfiguration.deleteappconfiguration.end |
| Instance - Create Instance End | com.oraclecloud.blockchain.createplatforminstance.end |
| Instance - Start Instance Begin | com.oraclecloud.blockchain.startplatforminstance.begin |
| Deployment - Create End | com.oraclecloud.apigateway.createdeployment.end |
| MySQL - Stop DB System End | com.oraclecloud.mysqlaas.stopdbsystem.end |
| Create Repository - Begin | com.oraclecloud.devopscoderepo.createrepository.begin |
| Instance Configuration - Launch Begin | com.oraclecloud.computemanagement.launchinstanceconfiguration.begin |
| Distributed Database Private Endpoint - Delete End | com.oraclecloud.globaldb.deletedistributeddatabaseprivateendpoint.end |
| Service Instance - Roll Back Patch End | com.oraclecloud.zerolatency.rollbackpatchzerolatency.end |
| Upload Warning - Delete | com.oraclecloud.logginganalytics.deleteuploadwarning |
| Key - Enable End | com.oraclecloud.keymanagementservice.enablekey.end |
| Oracle managed database software update disabled | com.oraclecloud.databaseservice.managedsoftwareupdatedisabled |
| BDS Instance - AutoscaleRun - Scale In | com.oraclecloud.bds.autoscale.cp.autoscalein |
| Service Gateway - Update | com.oraclecloud.servicegateway.updateservicegateway |
| Network Address List - Delete End | com.oraclecloud.waf.deletenetworkaddresslist.end |
| Gateway - Create Begin | com.oraclecloud.apigateway.creategateway.begin |
| Container Instance - Restart Container Instance Begin | com.oraclecloud.containerinstances.restartcontainerinstance.begin |
| Instance - Delete End | com.oraclecloud.omh.deleteomhinstance.end |
| Detection Rule - Pause | com.oraclecloud.logginganalytics.pausescheduledtask |
| Batch Context - Start | com.oraclecloud.batch.startbatchcontext |
| Service Instance - Start Server End | com.oraclecloud.zerolatency.starttimestenserver.end |
| Extend - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.extenddelegatedresourceaccessrequest |
| DR Plan Execution - Cancel End | com.oraclecloud.disasterrecovery.canceldrplanexecution.end |
| Create Boot Volume Begin | com.oraclecloud.blockvolumes.createbootvolume.begin |
| Masking Library Format Create - End | com.oraclecloud.datasafe.createlibrarymaskingformat.end |
| Update Global Accelerator BackendSet End | com.oraclecloud.gax.public.api.updatebackendset.end |
| GGS Deployment - Deployment Recovery Workflow Begin | com.oraclecloud.goldengate.deploymentrecovery.begin |
| Global Autonomous Database - Generate GSM Certificate Signing Request End | com.oraclecloud.globaldb.generategsmcertificatesigningrequest.end |
| DeleteProject - begin | com.oraclecloud.devopsproject.deleteproject.begin |
| Security Policy Report Delete - End | com.oraclecloud.datasafe.deletesecuritypolicyreport.end |
| Fusion Environment Family - Delete End | com.oraclecloud.fusionapps.deletefusionenvironmentfamily.end |
| Service Instance - Update Begin | com.oraclecloud.zerolatency.updatezerolatency.begin |
| Autonomous Data Guard Association - Critical | com.oraclecloud.databaseservice.autonomous.container.database.dataguardassociation.critical |
| IngressGateway - Create Begin | com.oraclecloud.servicemesh.createingressgateway.begin |
| Event - Create Update Other Event | com.oraclecloud.osmh.createevent.softwareupdate.updateother |
| MySQL - Copy Backup Begin | com.oraclecloud.mysqlaas.copybackup.begin |
| User - Update | com.oraclecloud.identitycontrolplane.updateuser |
| Event - Create Update Bugfix Event | com.oraclecloud.osmh.createevent.softwareupdate.updatebugfix |
| Update Export | com.oraclecloud.filestorage.updateexport |
| Language - Detect Dominant Language | com.oraclecloud.aiservicelanguage.detectdominantlanguage |
| DR Protection Group - Delete Begin | com.oraclecloud.disasterrecovery.deletedrprotectiongroup.begin |
| Recovery Service Subnet - Update Begin | com.oraclecloud.autonomousrecoveryservice.updaterecoveryservicesubnet.begin |
| Add Operator - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.adddelegatedresourceaccessrequestoperator |
| Portfolio - Delete | com.oraclecloud.atat.deleteportfolio |
| MySQL - Create Backup End | com.oraclecloud.mysqlaas.createbackup.end |
| KeyVersion - Schedule Deletion End | com.oraclecloud.keymanagementservice.schedulekeyversiondeletion.end |
| MySQL - Create Backup Begin | com.oraclecloud.mysqlaas.createbackup.begin |
| ContainerScanRecipes - Update End | com.oraclecloud.vulnerabilityscanning.updatecontainerscanrecipe.end |
| Job Update Begin | com.oraclecloud.odms.updatejob.begin |
| Appliance - Delete | com.oraclecloud.datatransferservice.deletetransferappliance |
| BDS Instance - Delete NodeBackup Configuration | com.oraclecloud.bds.cp.deletenodebackupconfig |
| Work Request - Collect Metadata Begin | com.oraclecloud.osmh.collectmetadata.begin |
| Token Request | com.oraclecloud.identitysignon.tokenrequest |
| Global Autonomous Database - Download GSM Certificate Signing Request | com.oraclecloud.globaldb.downloadgsmcertificatesigningrequest |
| VNIC - Update | com.oraclecloud.virtualnetwork.updatevnic |
| Oracle managed DB Home deletion completed | com.oraclecloud.databaseservice.oraclemanageddbhomedeletioncompleted |
| MySQL - Delete DB System End | com.oraclecloud.mysqlaas.deletedbsystem.end |
| Container Instance - Restart Container Instance End | com.oraclecloud.containerinstances.restartcontainerinstance.end |
| Run - Begin | com.oraclecloud.dataflow.createrun.begin |
| Phase Begin | com.oraclecloud.odms.beginphase |
| DataPipeline | com.oraclecloud.analyticswarehouse.data.pipeline |
| Topic - Create | com.oraclecloud.notification.createtopic |
| Delete Volume End | com.oraclecloud.blockvolumes.deletevolume.end |
| Upload Log Events File | com.oraclecloud.logginganalytics.uploadlogeventsfile |
| Audit Profile Create - Begin | com.oraclecloud.datasafe.createauditprofile.begin |
| OSN - Create OSN End | com.oraclecloud.blockchain.createosn.end |
| Language - Update Model End | com.oraclecloud.aiservicelanguage.updatemodel.end |
| Oracle managed DB Home deletion failed | com.oraclecloud.databaseservice.oraclemanageddbhomedeletionfailed |
| Distributed Database Private Endpoint - Change Compartment End | com.oraclecloud.globaldb.changedistributeddatabaseprivateendpointcompartment.end |
| Autonomous Database - Upgrade Database Version End | com.oraclecloud.databaseservice.upgradeautonomousdatabasedbversion.end |
| Autonomous Database - Restore Begin | com.oraclecloud.databaseservice.autonomous.database.restore.begin |
| Application Data Platform - PodDb Restore Point Delete Begin | com.oraclecloud.applicationdataplatform.deletepoddbrestorepoint.begin |
| External MySQL Connector - Create | com.oraclecloud.databasemanagement.externalmysqlresource.connector.create |
| Fusion Environment - Update End | com.oraclecloud.fusionapps.updatefusionenvironment.end |
| Database - Change Database Key Store Type Begin | com.oraclecloud.databaseservice.changedatabasekeystoretype.begin |
| Capacity Reservation - Change compartment | com.oraclecloud.computeapi.changecomputecapacityreservationcompartment |
| Imaging - Add Shape Compatibility | com.oraclecloud.computeimagingapi.removeimageshapecompatibility |
| Update Workspace - End | com.oraclecloud.dataintegration.updateworkspace.end |
| Recovery Email - Verify | com.oraclecloud.identitycontrolplane.verifyrecoveryemail |
| BDS Instance - Create Autoscale Configuration | com.oraclecloud.bds.autoscale.cp.createautoscaleconfiguration |
| Database Software Image - Create Begin | com.oraclecloud.databaseservice.createdatabasesoftwareimage.begin |
| Autonomous Database - Update Permission Level End | com.oraclecloud.databaseservice.updateautonomousdatabasepermissionlevel.end |
| Database - Modify DbManagement End | com.oraclecloud.databaseservice.modifydbmanagement.end |
| Service Instance - Health Check | com.oraclecloud.zerolatency.healthcheckzerolatency |
| Gateway - Change Compartment Begin | com.oraclecloud.apigateway.changegatewaycompartment.begin |
| DR Plan Execution - Resume Begin | com.oraclecloud.disasterrecovery.resumedrplanexecution.begin |
| Pipeline - Update | com.oraclecloud.datascience.updatepipeline |
| SQL Firewall Policy Update - End | com.oraclecloud.datasafe.updatesqlfirewallpolicy.end |
| Database - Update Begin | com.oraclecloud.postgresql.updatedbsystem.begin |
| Job Update End | com.oraclecloud.odms.updatejob.end |
| FsuCycle - Create Begin | com.oraclecloud.fsu.createfsucycle.begin |
| Gateway - Update End | com.oraclecloud.apigateway.updategateway.end |
| Process Automation Instance - Create End | com.oraclecloud.processautomation.createopainstance.end |
| Harvest - Begin | com.oraclecloud.datacatalog.harvestjob.begin |
| Delete Delegation Subscription - End | com.oraclecloud.delegateaccesscontrol.deletedelegationsubscription.end |
| Web Application Firewall - Change Compartment Begin | com.oraclecloud.waf.changewebappfirewallcompartment.begin |
| Work Request - Switch Snap Channel Begin | com.oraclecloud.osmh.switchsnapchannel.begin |
| VNIC - Attach End | com.oraclecloud.computeapi.attachvnic.end |
| Change Delegation Control Compartment - Begin | com.oraclecloud.delegateaccesscontrol.changedelegationcontrolcompartment.begin |
| Operator - Login | com.oraclecloud.operatorcontrol.operatorlogin |
| Connection Delete End | com.oraclecloud.odms.deleteconnection.end |
| BDS Instance - Refresh Resource Principal End | com.oraclecloud.bds.cp.refreshresourceprincipal.end |
| Migration - Change Compartment | com.oraclecloud.applicationmigration.changemigrationcompartment |
| Managed Instance - Install Package | com.oraclecloud.osms.installpackageonmanagedinstance |
| ILOM Fault | com.oraclecloud.hardwarefault.ilomfault |
| Log Group - Create | com.oraclecloud.logginganalytics.createloganalyticsloggroup |
| Network Security Group - Delete | com.oraclecloud.virtualnetwork.deletenetworksecuritygroup |
| Delete Target Database - End | com.oraclecloud.datasafe.deletetargetdatabase.end |
| Autonomous Data Guard Association - Reinstate Begin | com.oraclecloud.databaseservice.reinstateautonomousdataguardassociation.begin |
| Stream Distribution Channel - Update | com.oraclecloud.mediaservices.updatestreamdistributionchannel |
| Skip Policy-based Snapshot Creation | com.oraclecloud.filestorage.skippolicybasedsnapshotcreation |
| WebLogic Domain - Change Compartment | com.oraclecloud.weblogicmanagement.changewlsdomaincompartment |
| Autonomous Database - Warning | com.oraclecloud.databaseservice.autonomous.database.warning |
| Autonomous VM Cluster - Change Compartment | com.oraclecloud.databaseservice.changeautonomousvmclustercompartment |
| Create Volume Backup Policy | com.oraclecloud.blockvolumes.createvolumebackuppolicy |
| Copy Volume Backup Begin | com.oraclecloud.blockvolumes.copyvolumebackup.begin |
| Event - Change Compartment | com.oraclecloud.osmh.changeeventcompartment |
| ODA Instance - Change Compartment Begin | com.oraclecloud.digitalassistant.changeodacompartment.end |
| Sensitive Type Update - End | com.oraclecloud.datasafe.updatesensitivetype.end |
| Distributed Database Private Endpoint - Update | com.oraclecloud.globaldb.updatedistributeddatabaseprivateendpoint |
| MySQL - Resume Channel Begin | com.oraclecloud.mysqlaas.resumechannel.begin |
| Alert UpdateAll - End | com.oraclecloud.datasafe.alertsupdate.end |
| ODA Instance - Activate Customer Encryption Key Begin | com.oraclecloud.digitalassistant.activatecustomerencryptionkey.begin |
| Managed Instance Group - Update | com.oraclecloud.osms.updatemanagedinstancegroup |
| Pricing Rule - Delete | com.oraclecloud.subscriptionpricingservice.deletepricingrule |
| Delete Stack - End | com.oraclecloud.dataintelligencefoundation.deletestack.end |
| Security List - Create | com.oraclecloud.virtualnetwork.createsecuritylist |
| BDS Instance - Create Replace Configuration End | com.oraclecloud.bds.cp.createreplaceconfig.end |
| API - Update End | com.oraclecloud.apigateway.updateapi.end |
| Application - Update | com.oraclecloud.functions.updateapplication |
| Fusion Environment Family - Terminate Begin | com.oraclecloud.fusionapps.terminatefusionenvironmentfamily.begin |
| Work Request - Remove Snaps End | com.oraclecloud.osmh.removesnaps.end |
| Fusion Environment - Delete Begin | com.oraclecloud.fusionapps.deletefusionenvironment.begin |
| DR Plan Execution - Update Begin | com.oraclecloud.disasterrecovery.updatedrplanexecution.begin |
| HostScanTargets - Update | com.oraclecloud.vulnerabilityscanning.updatehostscantarget.begin |
| External Container Database - Enable Stack Monitoring Service Begin | com.oraclecloud.databaseservice.enablestackmonitoringforexternalcontainerdatabase.begin |
| Compartments - Create Compartment | com.oraclecloud.compartments.createcompartment |
| Tenancy Attachment - Update End | com.oraclecloud.resourceanalytics.updatetenancyattachment.end |
| Work Request - Register Managed Instance End | com.oraclecloud.osmh.registermanagedinstance.end |
| AccessPolicy - Change Compartment Begin | com.oraclecloud.servicemesh.changeaccesspolicycompartment.begin |
| GGS Pipeline - Needs Attention | com.oraclecloud.goldengate.pipeline.stateneedsattention |
| Portfolio - Update | com.oraclecloud.atat.patchportfolio |
| MySQL - Copy Backup End | com.oraclecloud.mysqlaas.copybackup.end |
| Sensitive Discovery Job Create - Begin | com.oraclecloud.datasafe.creatediscoveryjob.begin |
| Create Target Database - Begin | com.oraclecloud.datasafe.createtargetdatabase.begin |
| Delete Global Accelerator Routing Policy End | com.oraclecloud.gax.public.api.deleteroutingpolicy.end |
| SQL Firewall Policy Update - Begin | com.oraclecloud.datasafe.updatesqlfirewallpolicy.begin |
| Service Instance - Stop Server End | com.oraclecloud.zerolatency.stoptimestenserver.end |
| Swift Password - Create | com.oraclecloud.identitycontrolplane.createswiftpassword |
| Update Global Accelerator Listener Begin | com.oraclecloud.gax.public.api.updatelistener.begin |
| Autonomous Container Database - Failover End | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.failover.end |
| Autonomous Container Database - Add Standby Begin | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.createstandby.begin |
| Autonomous Container Database - Convert To Snapshot Standby Begin | com.oraclecloud.databaseservice.autonomous.container.database.snapshot.standby.conversion.begin |
| Autonomous Container Database - Reinstate Begin | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.reinstate.begin |
| Scheduled Job - Execute Scheduled Job Canceled | com.oraclecloud.osmh.executescheduledjob.canceled |
| BuildPipeline - Update Begin | com.oraclecloud.devopsbuild.updatebuildpipeline.begin |
| VM Cluster - Create End | com.oraclecloud.databaseservice.createvmcluster.end |
| Trigger - Delete End | com.oraclecloud.devopsbuild.deletetrigger.end |
| Migration Evaluate Begin | com.oraclecloud.odms.evaluatemigration.begin |
| Instance - Delete Instance | com.oraclecloud.analytics.deleteanalyticsinstance |
| Exascale Database Storage Vault - Delete End | com.oraclecloud.databaseservice.deleteexascaledbstoragevault.end |
| AI Data Platform - Update Begin | com.oraclecloud.aidataplatform.updateaidataplatform.begin |
| DFI Cluster: Stop Begin | com.oraclecloud.dataflowinteractive.stopinteractivecluster.begin |
| External Container Database - Enable Stack Monitoring Service End | com.oraclecloud.databaseservice.enablestackmonitoringforexternalcontainerdatabase.end |
| Cache Database - Close End | com.oraclecloud.zerolatency.closezerolatencydatabase.end |
| Refresh Data Guard Health Status - End | com.oraclecloud.databaseservice.dataguardrefreshhealthstatus.end |
| Data Guard Switchover - End | com.oraclecloud.databaseservice.dataguardswitchover.end |
| Internet Gateway - Change Compartment | com.oraclecloud.virtualnetwork.changeinternetgatewaycompartment |
| Desktop Pool - Delete | com.oraclecloud.ocidesktopservice.deletedesktoppool |
| Deployment - Change Compartment Begin | com.oraclecloud.apigateway.changedeploymentcompartment.begin |
| Global Autonomous Database - Update | com.oraclecloud.globaldb.updateshardeddatabase |
| Cluster - Create | com.oraclecloud.oraclerovingedgeinfrastructure.createcluster |
| MySQL - Restart HeatWave Cluster Begin | com.oraclecloud.mysqlaas.restartheatwavecluster.begin |
| Gateway - Change Compartment End | com.oraclecloud.apigateway.changegatewaycompartment.end |
| Managed Instance - List Snaps | com.oraclecloud.osmh.listsnaps |
| Work Request - Update Security Begin | com.oraclecloud.osmh.updatesecurity.begin |
| Instance Pool - Start Action End | com.oraclecloud.computemanagement.startinstancepool.end |
| VMware Solution - Create ESXi Host Begin | com.oraclecloud.vmwaresolution.createesxihost.begin |
| DR Plan Execution - CreateStopDrill End | com.oraclecloud.disasterrecovery.createstopdrilldrplanexecution.end |
| DeployArtifact - Create Begin | com.oraclecloud.devopsdeploy.createdeployartifact.begin |
| Project - Update | com.oraclecloud.datascience.updateproject |
| Index - Create Begin | com.oraclecloud.nosql.createindex.begin |
| BDS Instance - Configure Enable ODH Service Certificate End | com.oraclecloud.bds.cp.enableodhservicecertificate.end |
| Kafka Cluster - Create End | com.oraclecloud.rawfkaapiprod.createkafkacluster.end |
| Work Request - Remove Content End | com.oraclecloud.osmh.removecontent.end |
| VirtualService - Update Begin | com.oraclecloud.servicemesh.updatevirtualservice.begin |
| Exadata Infrastructure - Update End | com.oraclecloud.databaseservice.updateexadatainfrastructure.end |
| Delete Alert Policy - Begin | com.oraclecloud.datasafe.deletealertpolicy.begin |
| Job Resume End | com.oraclecloud.odms.resumejob.end |
| VirtualService - Create End | com.oraclecloud.servicemesh.createvirtualservice.end |
| Tenancy Attachment - Update Begin | com.oraclecloud.resourceanalytics.updatetenancyattachment.begin |
| Change Compartment NetworkFirewall | com.oraclecloud.networkfirewallservice.changenetworkfirewallcompartment |
| Resource Categories - Update | com.oraclecloud.logginganalytics.updateresourcecategories |
| Provisioning Status - Get | com.oraclecloud.atat.getprovisioningstatus |
| Sensitive Data Model Update - End | com.oraclecloud.datasafe.updatesensitivedatamodel.end |
| User - Deactivate | com.oraclecloud.identitycontrolplane.deactivateuser |
| Management Agent - New Version Available | com.oraclecloud.managementagent.agentimagenewversionavailable |
| WebLogic Domain - Restore Begin | com.oraclecloud.weblogicmanagement.restorewlsdomain.begin |
| Cache Database - Unload End | com.oraclecloud.zerolatency.unloadzerolatencydatabase.end |
| Instance - Change Compartment End | com.oraclecloud.computeapi.changeinstancecompartment.end |
| Exascale Database Storage Vault - Update End | com.oraclecloud.databaseservice.updateexascaledbstoragevault.end |
| Instance Pool - Terminate Begin | com.oraclecloud.computemanagement.terminateinstancepool.begin |
| Database - Rotate Database Key End | com.oraclecloud.databaseservice.rotatedatabasekey.end |
| DR Protection Group - Associate End | com.oraclecloud.disasterrecovery.associatedrprotectiongroup.end |
| Autonomous Database - Information | com.oraclecloud.databaseservice.autonomous.database.information |
| VM Cluster Network - Create Begin | com.oraclecloud.databaseservice.createvmclusternetwork.begin |
| Security Policy Report Create - End | com.oraclecloud.datasafe.createsecuritypolicyreport.end |
| WebLogic Domain - Stop Begin | com.oraclecloud.weblogicmanagement.stopwlsdomain.begin |
| Start Workspace - Begin | com.oraclecloud.dataintegration.startworkspace.begin |
| Entity - Delete | com.oraclecloud.logginganalytics.deleteentity |
| Container Instance - Change Compartment End | com.oraclecloud.containerinstances.changecontainerinstancecompartment.end |
| Dynamic Group - Update | com.oraclecloud.identitycontrolplane.updatedynamicgroup |
| External Container Database - Disable Stack Monitoring Service Begin | com.oraclecloud.databaseservice.disablestackmonitoringforexternalcontainerdatabase.begin |
| Autonomous Cloud VM Cluster - maintenance reminder | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.maintenance.reminder |
| DeployStage - Update Begin | com.oraclecloud.devopsdeploy.updatedeploystage.begin |
| Managed Instance - Register | com.oraclecloud.osmh.registermanagedinstance |
| Change Volume Compartment Begin | com.oraclecloud.blockvolumes.changevolumecompartment.begin |
| Oce Instance - Update End | com.oraclecloud.oce.updateoceinstance.end |
| Cache Database - Configure Cache Begin | com.oraclecloud.zerolatency.configurecache.begin |
| SQL Firewall Policy Delete - Begin | com.oraclecloud.datasafe.deletesqlfirewallpolicy.begin |
| Discovery Schedule - Create | com.oraclecloud.cloudbridge.creatediscoveryschedule |
| FsuAction - Delete End | com.oraclecloud.fsu.deleteaction.end |
| Instance - Schedule Maintenance | com.oraclecloud.computeapi.schedulemaintenance |
| Access Request - Revoke | com.oraclecloud.operatorcontrol.revokeaccessrequest |
| Verify MFA Token | com.oraclecloud.identitysignon.verifymfatoken |
| Migration Delete Begin | com.oraclecloud.odms.deletemigration.begin |
| Set Unprocessed Data Bucket | com.oraclecloud.logginganalytics.setunprocesseddatabucket |
| Update Volume Begin | com.oraclecloud.blockvolumes.updatevolume.begin |
| Autonomous Database - Long-term Backup Will Expire In 90 Days | com.oraclecloud.databaseservice.autonomous.database.backup.longtermbackupexpiresinthreemonths.reminder |
| VM Cluster Network - Create End | com.oraclecloud.databaseservice.createvmclusternetwork.end |
| Desktop Pool - Start | com.oraclecloud.ocidesktopservice.startdesktoppool |
| Delete Volume Group | com.oraclecloud.blockvolumes.deletevolumegroup |
| Sensitive Data Model Referential Relation Create - Begin | com.oraclecloud.datasafe.createreferentialrelation.begin |
| KeyVersion - Schedule Deletion Begin | com.oraclecloud.keymanagementservice.schedulekeyversiondeletion.begin |
| Assign Operator Control - Create | com.oraclecloud.operatorcontrol.createoperatorcontrolassignment |
| Key - Restore Begin | com.oraclecloud.keymanagementservice.restorekey.begin |
| Imaging - Export End | com.oraclecloud.computeapi.exportimage.end |
| VirtualServiceRouteTable - Update Begin | com.oraclecloud.servicemesh.updatevirtualserviceroutetable.begin |
| Cache Database - Generate Diagnostics Begin | com.oraclecloud.zerolatency.generatezerolatencydatabasediagnostics.begin |
| OMA - Create Access Request Begin | com.oraclecloud.lockbox.createaccessrequest.begin |
| Distributed Autonomous Database - Update | com.oraclecloud.globaldb.updatedistributedautonomousdatabase |
| Unified Audit Policy Definition Delete - End | com.oraclecloud.datasafe.deleteunifiedauditpolicydefinition.end |
| IngressGateway - Create End | com.oraclecloud.servicemesh.createingressgateway.end |
| DB Home - Terminate End | com.oraclecloud.databaseservice.deletedbhome.end |
| Database Tools Private Endpoint - Update End | com.oraclecloud.dbtoolsserviceapi.updatedatabasetoolsprivateendpoint.end |
| Entitlement - Update | com.oraclecloud.datatransferservice.updatetransferapplianceentitlement |
| Instance Pool - Start Action Begin | com.oraclecloud.computemanagement.startinstancepool.begin |
| Cloud Exadata Infrastructure - Granular Maintenance Duration Unplanned Windows Created | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenanceunplannedwindowscreated |
| Process Automation Instance - Change Compartment End | com.oraclecloud.processautomation.changeopainstancecompartment.end |
| Instance Pool - Terminate End | com.oraclecloud.computemanagement.terminateinstancepool.end |
| Vault - Cancel Deletion Begin | com.oraclecloud.keymanagementservice.cancelvaultdeletion.begin |
| Delete Stack - Begin | com.oraclecloud.dataintelligencefoundation.deletestack.begin |
| Network Security Group Security Rules - Update Security Rules | com.oraclecloud.virtualnetwork.updatenetworksecuritygroupsecurityrules |
| Managed Instance - Update Vulnerability | com.oraclecloud.osmh.updatevulnerability |
| Oneoff Patch - Delete Begin | com.oraclecloud.databaseservice.deleteoneoffpatch.begin |
| DB Node Console History - Delete End | com.oraclecloud.databaseservice.deletedbnodeconsolehistory.end |
| DB Node Console Connection - Delete End | com.oraclecloud.databaseservice.deletedbnodeconsoleconnection.end |
| DB Node Console Connection - Create Begin | com.oraclecloud.databaseservice.createdbnodeconsoleconnection.begin |
| DB Node Console History - Create Begin | com.oraclecloud.databaseservice.createdbnodeconsolehistory.begin |
| VM Cluster Network - Add DB Server Network Begin | com.oraclecloud.databaseservice.adddbservervmclusternetwork.begin |
| VM Cluster Network - Remove DB Server Network Begin | com.oraclecloud.databaseservice.removedbservervmclusternetwork.begin |
| DB Node Console History - Delete Begin | com.oraclecloud.databaseservice.deletedbnodeconsolehistory.begin |
| DB Node Console Connection - Delete Begin | com.oraclecloud.databaseservice.deletedbnodeconsoleconnection.begin |
| VM Cluster Network - Terminate Begin | com.oraclecloud.databaseservice.deletevmclusternetwork.begin |
| DB Node Console History - Create End | com.oraclecloud.databaseservice.createdbnodeconsolehistory.end |
| DB Node Console Connection - Create End | com.oraclecloud.databaseservice.createdbnodeconsoleconnection.end |
| Batch Task Profile - Create | com.oraclecloud.batch.createbatchtaskprofile |
| GGS Pipeline - Start Pipeline Begin | com.oraclecloud.goldengate.startpipeline.begin |
| DB Node - Information | com.oraclecloud.databaseservice.dbnode.information |
| Notebook Session - Delete Begin | com.oraclecloud.datascience.deletenotebooksession.begin |
| DB Node Console History - Update | com.oraclecloud.databaseservice.updatedbnodeconsolehistory |
| DB Node Console Connection - Update | com.oraclecloud.databaseservice.updatedbnodeconsoleconnection |
| DB Node Console History - Get Content | com.oraclecloud.databaseservice.getdbnodeconsolehistorycontent |
| Batch Job - Cancel Begin | com.oraclecloud.batch.cancelbatchjob.begin |
| Language - Update Model Endpoint | com.oraclecloud.aiservicelanguage.updatemodelendpoint |
| HostPortScanResult - Delete | com.oraclecloud.vulnerabilityscanning.deletehostportscanresult |
| Model - Deactivate | com.oraclecloud.datascience.deactivatemodel |
| Migration Evaluate End | com.oraclecloud.odms.evaluatemigration.end |
| Waf Policy - Update Begin | com.oraclecloud.waf.updatewebappfirewallpolicy.begin |
| Event - Sysadmin Event | com.oraclecloud.osmh.event.sysadmin |
| SQL Firewall Collection Start - Begin | com.oraclecloud.datasafe.startsqlcollection.begin |
| GGS Deployment - Deployment Recovery Workflow End | com.oraclecloud.goldengate.deploymentrecovery.end |
| Managed Instance - Install Snaps | com.oraclecloud.osmh.installsnaps |
| Integration Instance - Change Compartment Begin | com.oraclecloud.integration.changeintegrationcompartment.begin |
| Source - Change Compartment | com.oraclecloud.applicationmigration.changesourcecompartment |
| Resource Schedule - Deactivate | com.oraclecloud.resourcescheduler.deactivateschedule |
| Kafka Config - Update | com.oraclecloud.rawfkaapiprod.updatekafkaclusterconfig |
| Object - Update | com.oraclecloud.objectstorage.updateobject |
| Phase End | com.oraclecloud.odms.endphase |
| Security Policy Delete - Begin | com.oraclecloud.datasafe.deletesecuritypolicy.begin |
| Vault - Create Begin | com.oraclecloud.keymanagementservice.createvault.begin |
| Boot Volume - Detach Begin | com.oraclecloud.computeapi.detachbootvolume.begin |
| DeployEnvironment - Create Begin | com.oraclecloud.devopsdeploy.createdeployenvironment.begin |
| Delete Delegation Subscription - Begin | com.oraclecloud.delegateaccesscontrol.deletedelegationsubscription.begin |
| Waf Policy - Change Compartment Begin | com.oraclecloud.waf.changewebappfirewallpolicycompartment.begin |
| Batch Job Pool - Change Compartment Begin | com.oraclecloud.batch.changebatchjobpoolcompartment.begin |
| Software Source - Create | com.oraclecloud.osms.createsoftwaresource |
| Create Custom Protection Rule | com.oraclecloud.waf.createcustomprotectionrule |
| BDS Instance - Restart Node End | com.oraclecloud.bds.cp.restartbdsnode.end |
| SQL Firewall Policy Generate - End | com.oraclecloud.datasafe.generatesqlfirewallpolicy.end |
| Network Address List - Update Begin | com.oraclecloud.waf.updatenetworkaddresslist.begin |
| Create Global Accelerator Routing Policy End | com.oraclecloud.gax.public.api.createroutingpolicy.end |
| Source Event Types - Enable | com.oraclecloud.logginganalytics.enablesourceeventtypes |
| ODA Instance - Delete Begin | com.oraclecloud.digitalassistant.deleteodainstance.begin |
| Integration Instance - Update Begin | com.oraclecloud.integration.updateintegrationinstance.begin |
| OMA - Change Approval Template Compartment | com.oraclecloud.lockbox.changeapprovaltemplatecompartment |
| Cluster - Create Begin | com.oraclecloud.clustersapi.createcluster.begin |
| Language - Detect Key Phrases | com.oraclecloud.aiservicelanguage.detectlanguagekeyphrases |
| BDS Api Key Instance - Delete Api Key End | com.oraclecloud.bds.cp.deletebdsapikey.end |
| BDS Instance - Configure Enable ODH Service Certificate Begin | com.oraclecloud.bds.cp.enableodhservicecertificate.begin |
| Access Request - Approve | com.oraclecloud.operatorcontrol.approveaccessrequest |
| Network Security Group Security Rules - Add Security Rules | com.oraclecloud.virtualnetwork.addnetworksecuritygroupsecurityrules |
| HostCisBenchmarkScanResult - Delete | com.oraclecloud.vulnerabilityscanning.deletehostcisbenchmarkscanresult |
| Unified Audit Policy Definition Delete - Begin | com.oraclecloud.datasafe.deleteunifiedauditpolicydefinition.begin |
| Create On-Prem Connector - End | com.oraclecloud.datasafe.createonpremconnector.end |
| Work Request - Update Enhancement Begin | com.oraclecloud.osmh.updateenhancement.begin |
| Create Global Accelerator Hostname Begin | com.oraclecloud.gax.public.api.createhostname.begin |
| Instance - Scale Instance Up or Down Begin | com.oraclecloud.analytics.scaleanalyticsinstance.begin |
| Data Store - Update End | com.oraclecloud.dataexchange.updatedatastore.end |
| Protection Policy - Update End | com.oraclecloud.autonomousrecoveryservice.updateprotectionpolicy.end |
| Autonomous Database - AccessControl Lists Update Begin | com.oraclecloud.databaseservice.updateautonomousdatabaseacl.begin |
| Reject Policy-based Snapshot Creation | com.oraclecloud.filestorage.rejectpolicybasedsnapshotcreation |
| Integration Instance - Start Begin | com.oraclecloud.integration.startintegrationinstance.begin |
| AccessPolicy - Delete End | com.oraclecloud.servicemesh.deleteaccesspolicy.end |
| Instance - Infrastructure Failure | com.oraclecloud.computeapi.instancefailed |
| DRG - Delete | com.oraclecloud.virtualnetwork.deletedrg |
| WebLogic Domain - Scan End | com.oraclecloud.weblogicmanagement.scanwlsdomain.end |
| WebLogic Domain - Uninstall Latest Patches Begin | com.oraclecloud.weblogicmanagement.uninstalllatestpatchesfromwlsdomain.begin |
| BDS Instance - Configure Install Software Updates Begin | com.oraclecloud.bds.cp.installsoftwareupdates.begin |
| Autonomous VM Cluster - Maintenance Reminder | com.oraclecloud.databaseservice.autonomousvmclustermaintenance.reminder |
| Configure - Enable Begin | com.oraclecloud.datasafe.enabledatasafeservice.begin |
| Object - Delete | com.oraclecloud.objectstorage.deleteobject |
| Audit Trail Update - End | com.oraclecloud.datasafe.updateaudittrail.end |
| Job Abort Begin | com.oraclecloud.odms.abortjob.begin |
| Distributed Database - Create End | com.oraclecloud.globaldb.createdistributeddatabase.end |
| Private Service Access - Delete Begin | com.oraclecloud.privateserviceaccess.deleteprivateserviceaccess.begin |
| RevCycleEnvironment - Update End | com.oraclecloud.ircscontrolplaneapi.updaterevcycleenvironment.end |
| Autonomous Database - Create Backup End | com.oraclecloud.databaseservice.autonomous.database.backup.end |
| BDS Instance - Terminate End | com.oraclecloud.bds.cp.terminateinstance.end |
| VMware Solution - Cancel Downgrade HCX End | com.oraclecloud.vmwaresolution.canceldowngradehcx.end |
| Security Policy Configuration Update - Begin | com.oraclecloud.datasafe.updatesecuritypolicyconfig.begin |
| Audit Profile Create - End | com.oraclecloud.datasafe.createauditprofile.end |
| Instance - Create Begin | com.oraclecloud.omh.createomhinstance.begin |
| Security List - Delete | com.oraclecloud.virtualnetwork.deletesecuritylist |
| Cloud VM Cluster - Information | com.oraclecloud.databaseservice.cloudvmcluster.information |
| Distributed Autonomous Database - Stop Begin | com.oraclecloud.globaldb.stopdistributedautonomousdatabase.begin |
| Database - Enable DbManagement End | com.oraclecloud.databaseservice.enabledbmanagement.end |
| Media Workflow Configuration - Delete | com.oraclecloud.mediaservices.deletemediaworkflowconfiguration |
| Peer - Create Peer End | com.oraclecloud.blockchain.createpeer.end |
| Delete NetworkFirewallPolicy Begin | com.oraclecloud.networkfirewallservice.deletenetworkfirewallpolicy.begin |
| Speech - Create Transcription Job | com.oraclecloud.aiservicespeech.createtranscriptionjob |
| Source - Update End | com.oraclecloud.applicationmigration.updatesource.end |
| Database Software Image - Move End | com.oraclecloud.databaseservice.movedatabasesoftwareimage.end |
| Ingest Time Rule - Create | com.oraclecloud.logginganalytics.createingesttimerule |
| Instance - Change Compartment | com.oraclecloud.analytics.changeanalyticsinstancecompartment |
| Database - Restore Begin | com.oraclecloud.databaseservice.restoredatabase.begin |
| OCI Cache Cluster - Create Begin | com.oraclecloud.redisservice.createrediscluster.begin |
| BDS Instance - Configure Install ODH Patch End | com.oraclecloud.bds.cp.installodhpatch.end |
| Batch Job - Create Begin | com.oraclecloud.batch.createbatchjob.begin |
| Capacity Reservation - Create reservation begin | com.oraclecloud.computeapi.createcomputecapacityreservation.begin |
| Work Request - Unregister Managed Instance End | com.oraclecloud.osmh.unregistermanagedinstance.end |
| Create Volume Begin | com.oraclecloud.blockvolumes.createvolume.begin |
| Application - Update | com.oraclecloud.dataflow.updateapplication |
| Event - Create Sync Agent Config Event | com.oraclecloud.osmh.createevent.agent.syncagentconfig |
| Delete Iot Domain - Begin | com.oraclecloud.iot.deleteiotdomain.begin |
| Deployment - Update Begin | com.oraclecloud.apigateway.updatedeployment.begin |
| Migration State Change | com.oraclecloud.odms.statechangemigration |
| Update Volume Backup | com.oraclecloud.blockvolumes.updatevolumebackup |
| Update Global Accelerator Hostname End | com.oraclecloud.gax.public.api.updatehostname.end |
| BDS Instance - Disable Cloud SQL Begin | com.oraclecloud.bds.cp.removecloudsql.begin |
| DR Protection Group - ChangeCompartment Begin | com.oraclecloud.disasterrecovery.changedrprotectiongroupcompartment.begin |
| Autonomous Container Database - Restore End | com.oraclecloud.databaseservice.autonomous.container.database.restore.end |
| Log Group - Change Compartment | com.oraclecloud.logginganalytics.changeloganalyticsloggroupcompartment |
| Detection Rule - Change Compartment | com.oraclecloud.logginganalytics.changescheduledtaskcompartment |
| Update Volume | com.oraclecloud.blockvolumes.updatevolume |
| ODA Instance - Create End | com.oraclecloud.digitalassistant.createodainstance.end |
| Cluster - Update | com.oraclecloud.oraclerovingedgeinfrastructure.updatecluster |
| Event - Create Update Management Station Config Event | com.oraclecloud.osmh.createevent.managementstation.updatemanagementstationconfig |
| Application Data Platform - PodDb Restore Point Flashback End | com.oraclecloud.applicationdataplatform.flashbackpoddbrestorepoint.end |
| VMware Solution - Create Cluster Begin | com.oraclecloud.vmwaresolution.createcluster.begin |
| BDS Metastore Configuration Instance - Create Metastore Configuration Begin | com.oraclecloud.bds.cp.createbdsmetastoreconfiguration.begin |
| Distributed Database - Start End | com.oraclecloud.globaldb.startdistributeddatabase.end |
| OMA - Handle Access Request End | com.oraclecloud.lockbox.handleaccessrequest.end |
| Web Application Acceleration - Purge Cache End | com.oraclecloud.waa.purgewebappaccelerationcache.end |
| Work Request - Unregister Managed Instance Begin | com.oraclecloud.osmh.unregistermanagedinstance.begin |
| Event - Create Sysadmin Succeeded Event | com.oraclecloud.osmh.createevent.sysadmin.succeeded |
| Integration Instance - Change Compartment End | com.oraclecloud.integration.changeintegrationcompartment.end |
| DR Protection Group - Update Begin | com.oraclecloud.disasterrecovery.updatedrprotectiongroup.begin |
| VM Cluster Network - Update Begin | com.oraclecloud.databaseservice.updatevmclusternetwork.begin |
| Media Workflow Configuration - Update | com.oraclecloud.mediaservices.updatemediaworkflowconfiguration |
| Delete Global Accelerator Ruleset End | com.oraclecloud.gax.public.api.deleteruleset.end |
| Subnet - Create | com.oraclecloud.virtualnetwork.createsubnet |
| HostScanRecipe - Delete | com.oraclecloud.vulnerabilityscanning.deletehostscanrecipe |
| Managed Instance - Scan End | com.oraclecloud.weblogicmanagement.scanmanagedinstance.end |
| Web Application Acceleration Policy - Delete Begin | com.oraclecloud.waa.deletewebappaccelerationpolicy.begin |
| App Configuration Update - End | com.oraclecloud.appconfiguration.updateappconfiguration.end |
| BDS Instance - Configure Add Kafka End | com.oraclecloud.bds.cp.addkafka.end |
| On-Prem Connector State Change | com.oraclecloud.datasafe.statechangeonpremconnector |
| MySQL - Restart DB System End | com.oraclecloud.mysqlaas.restartdbsystem.end |
| Project - Create | com.oraclecloud.datascience.createproject |
| Batch Job - Update End | com.oraclecloud.batch.updatebatchjob.end |
| Batch Job - Pause Begin | com.oraclecloud.batch.pausebatchjob.begin |
| Work Request - Remove Packages End | com.oraclecloud.osmh.removepackages.end |
| CreateProject - end | com.oraclecloud.devopsproject.createproject.end |
| Service Instance - Stop Begin | com.oraclecloud.zerolatency.stopzerolatency.begin |
| Automatic Key Rotation - Begin | com.oraclecloud.keymanagementservice.autokeyrotate.begin |
| Masking Columns Patch - End | com.oraclecloud.datasafe.patchmaskingcolumns.end |
| Oracle managed database software update completed | com.oraclecloud.databaseservice.managedsoftwareupdatecompleted |
| Exadb VM Cluster - Create End | com.oraclecloud.databaseservice.createexadbvmcluster.end |
| Speech - Update Transcription Job | com.oraclecloud.aiservicespeech.updatetranscriptionjob |
| Task Order - Remove from portfolio | com.oraclecloud.atat.deletetaskorder |
| Update Iot Domain - End | com.oraclecloud.iot.updateiotdomain.end |
| Data Exchange - Create Begin | com.oraclecloud.dataexchange.createdataexchange.begin |
| Batch Job - Update Begin | com.oraclecloud.batch.updatebatchjob.begin |
| ChangeAssetTags | com.oraclecloud.cloudbridge.changeassettags |
| Pluggable database - Disable Database Management Service Begin | com.oraclecloud.databaseservice.disablepdbmanagement.begin |
| Distributed Autonomous Database - Generate Wallet | com.oraclecloud.globaldb.generatedistributedautonomousdatabasewallet |
| BDS Instance - Configure Install Software Updates End | com.oraclecloud.bds.cp.installsoftwareupdates.end |
| FsuDiscovery - Delete End | com.oraclecloud.fsu.deletediscovery.end |
| App Configuration Change compartment - Begin | com.oraclecloud.appconfiguration.changecompartment.begin |
| Sensitive Data Model Referential Relation Create - End | com.oraclecloud.datasafe.createreferentialrelation.end |
| DR Plan Execution - CreateSwitchoverPreCheck End | com.oraclecloud.disasterrecovery.createswitchoverprecheckdrplanexecution.end |
| Scheduled Job - Update | com.oraclecloud.osms.updatescheduledjob |
| RevCycleEnvironment - Delete Begin | com.oraclecloud.ircscontrolplaneapi.deleterevcycleenvironment.begin |
| Work Request - Install Snaps End | com.oraclecloud.osmh.installsnaps.end |
| Backup Destination - Terminate | com.oraclecloud.databaseservice.deletebackupdestination |
| AI Data Platform - Delete End | com.oraclecloud.aidataplatform.deleteaidataplatform.end |
| VirtualDeployment - Change Compartment Begin | com.oraclecloud.servicemesh.changevirtualdeploymentcompartment.begin |
| Managed Instance - Install Windows Security Updates | com.oraclecloud.osmh.installsecuritywindowsupdates |
| Container Instance - Stop Container Instance Begin | com.oraclecloud.containerinstances.stopcontainerinstance.begin |
| Event - Create Exploit Attempt Event | com.oraclecloud.osmh.createevent.exploitattempt |
| Migration Start Begin | com.oraclecloud.odms.startmigration.begin |
| BDS Instance - Remove Autoscale Configuration | com.oraclecloud.bds.autoscale.cp.removeautoscaleconfiguration |
| BDS Metastore Configuration Instance - Create Metastore Configuration End | com.oraclecloud.bds.cp.createbdsmetastoreconfiguration.end |
| Global Database Private Endpoint - Change Compartment Begin | com.oraclecloud.globaldb.changeprivateendpointcompartment.begin |
| Vault - Restore End | com.oraclecloud.keymanagementservice.restorevault.end |
| Instance - Update | com.oraclecloud.omh.updateomhinstance |
| Purge Cache Begin | com.oraclecloud.waf.purgecache.begin |
| Delete Workspace - Begin | com.oraclecloud.dataintegration.deleteworkspace.begin |
| Source - Upsert | com.oraclecloud.logginganalytics.upsertsource |
| BuildPipelineStage - Delete End | com.oraclecloud.devopsbuild.deletebuildpipelinestage.end |
| Managed Instance - Unregister | com.oraclecloud.osmh.unregistermanagedinstance |
| Instance - Scale Instance Begin | com.oraclecloud.blockchain.scaleplatforminstance.begin |
| Table - Change Compartment Begin | com.oraclecloud.nosql.changecompartment.begin |
| Service Gateway - Detach Service | com.oraclecloud.servicegateway.detachserviceid |
| Data Lake - Update Begin | com.oraclecloud.datalake.updatedatalake.begin |
| Exadata Infrastructure - Update Begin | com.oraclecloud.databaseservice.updateexadatainfrastructure.begin |
| Connection Create Begin | com.oraclecloud.odms.createconnection.begin |
| Distributed Autonomous Database - Stop End | com.oraclecloud.globaldb.stopdistributedautonomousdatabase.end |
| Scheduled Job - Execute Scheduled Job Succeeded | com.oraclecloud.osmh.executescheduledjob.succeeded |
| Distributed Database - Upload Signed Certificate And Generate Wallet End | com.oraclecloud.globaldb.uploaddistributeddatabasesignedcertificateandgeneratewallet.end |
| VMware Solution - Change SDDC Compartment | com.oraclecloud.vmwaresolution.changesddccompartment |
| Autonomous Database - Backup Update - Begin | com.oraclecloud.databaseservice.autonomous.database.backup.updateautonomousdatabasebackup.begin |
| Key Store - Change Compartment | com.oraclecloud.databaseservice.changekeystorecompartment |
| Instance - Create End | com.oraclecloud.omh.createomhinstance.end |
| Work Request - Install Bug Fix Windows Updates End | com.oraclecloud.osmh.installbugfixwindowsupdates.end |
| Node - Delete | com.oraclecloud.oraclerovingedgeinfrastructure.deletenode |
| DR Plan Execution - CreateStartDrillPreCheck Begin | com.oraclecloud.disasterrecovery.createstartdrillprecheckdrplanexecution |
| HostScanTarget - Create | com.oraclecloud.vulnerabilityscanning.createhostscantarget.end |
| Security Policy Report Create - Begin | com.oraclecloud.datasafe.createsecuritypolicyreport.begin |
| Waf Policy - Update End | com.oraclecloud.waf.updatewebappfirewallpolicy.end |
| ContainerScanTarget - Create Begin | com.oraclecloud.vulnerabilityscanning.createcontainerscantarget.begin |
| Pipeline Run - Update | com.oraclecloud.datascience.updatepipelinerun |
| Model Deployment - Create Begin | com.oraclecloud.datascience.createmodeldeployment.begin |
| Managed Instance - Detach Parent Software Source | com.oraclecloud.osms.detachparentsoftwaresourcefrommanagedinstance |
| Work Request - Update Management Station Software Begin | com.oraclecloud.osmh.updatemanagementstationsoftware.begin |
| Connection Update Begin | com.oraclecloud.odms.updateconnection.begin |
| Create Feature flag | com.oraclecloud.appconfiguration.createfeatureflag |
| Global Autonomous Database - Generate Wallet | com.oraclecloud.globaldb.generatewallet |
| Update Alert Policy - Begin | com.oraclecloud.datasafe.updatealertpolicy.begin |
| Service Instance - Configure Begin | com.oraclecloud.zerolatency.configurezerolatency.begin |
| CreateProject - begin | com.oraclecloud.devopsproject.createproject.begin |
| BuildPipelineStage - Update End | com.oraclecloud.devopsbuild.updatebuildpipelinestage.end |
| Work Request - Enable Module Streams End | com.oraclecloud.osmh.enablemodulestreams.end |
| Bucket - Delete | com.oraclecloud.objectstorage.deletebucket |
| Create Certificate | com.oraclecloud.waf.createcertificate |
| Migration - Migrate Application End | com.oraclecloud.applicationmigration.migrateapplication.end |
| Autonomous Container Database - Create End | com.oraclecloud.databaseservice.autonomous.container.database.instance.create.end |
| MFA TOTP Device - Activate | com.oraclecloud.identitycontrolplane.activatemfatotpdevice |
| GGS Pipeline - Updating | com.oraclecloud.goldengate.pipeline.stateupdating |
| Web Application Acceleration - Purge Cache Begin | com.oraclecloud.waa.purgewebappaccelerationcache.begin |
| Event - Create Sync Management Station Config Event | com.oraclecloud.osmh.createevent.managementstation.syncmanagementstationconfig |
| Autonomous Cloud VM Cluster - Change Compartment End | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.changecompartment.end |
| Object Storage Link - Change Compartment | com.oraclecloud.lustrefilestorage.changeobjectstoragelinkcompartment |
| Integration Instance - Delete End | com.oraclecloud.integration.deleteintegrationinstance.end |
| Database Tools Connection - Update End | com.oraclecloud.dbtoolsserviceapi.updatedatabasetoolsconnection.end |
| Trigger - Create Begin | com.oraclecloud.devopsbuild.createtrigger.begin |
| Web Application Acceleration - Change Compartment Begin | com.oraclecloud.waa.changewebappaccelerationcompartment.begin |
| Entitlement - Update | com.oraclecloud.oraclerovingedgeinfrastructure.updateentitlement |
| Exadb VM Cluster - Change Compartment End | com.oraclecloud.databaseservice.changeexadbvmclustercompartment.end |
| Model Deployment - Create End | com.oraclecloud.datascience.createmodeldeployment.end |
| Register Target Database - End | com.oraclecloud.datasafe.registerdatasafetarget.end |
| Warning - Unsuppress | com.oraclecloud.logginganalytics.unsuppresswarning |
| Exadata Infrastructure - Create Begin | com.oraclecloud.databaseservice.createexadatainfrastructure.begin |
| Protected Database - Create Begin | com.oraclecloud.autonomousrecoveryservice.createprotecteddatabase.begin |
| Pluggable database - Modify Database Management Service Begin | com.oraclecloud.databaseservice.modifypdbmanagement.begin |
| Local Peering Gateway - Change Compartment | com.oraclecloud.virtualnetwork.changelocalpeeringgatewaycompartment |
| BDS Instance - Delete Replace Configuration Begin | com.oraclecloud.bds.cp.deletereplaceconfig.begin |
| Web Application Firewall - Delete End | com.oraclecloud.waf.deletewebappfirewall.end |
| Batch Job - Create End | com.oraclecloud.batch.createbatchjob.end |
| App Configuration Create - End | com.oraclecloud.appconfiguration.createappconfiguration.end |
| App Configuration Import - Begin | com.oraclecloud.appconfiguration.importappconfiguration.begin |
| Compartments - Move Compartment | com.oraclecloud.compartments.movecompartment |
| External MySQL Connector - Delete End | com.oraclecloud.databasemanagement.externalmysqlresource.connector.delete.end |
| Environment - Update End | com.oraclecloud.ohaaas.updateenvironment.end |
| AppRelease | com.oraclecloud.analyticswarehouse.app.release |
| Autonomous VM Cluster - Create Begin | com.oraclecloud.databaseservice.createautonomousvmcluster.begin |
| Autonomous VM Cluster - Maintenance Scheduled | com.oraclecloud.databaseservice.autonomousvmclustermaintenance.scheduled |
| Cache Database - Load End | com.oraclecloud.zerolatency.loadzerolatencydatabase.end |
| Event - Create Remove Module Profile Event | com.oraclecloud.osmh.createevent.softwaresource.removemoduleprofile |
| Service Instance - Delete Begin | com.oraclecloud.zerolatency.deletezerolatency.begin |
| Language - Detect Entities | com.oraclecloud.aiservicelanguage.detectlanguageentities |
| Batch Context - Delete Begin | com.oraclecloud.batch.deletebatchcontext.begin |
| ODA Instance - Create Begin | com.oraclecloud.digitalassistant.createodainstance.begin |
| Portfolio - Create end | com.oraclecloud.atat.addportfolio.end |
| Job - Delete | com.oraclecloud.datatransferservice.deletetransferjob |
| Gateway - Delete Begin | com.oraclecloud.apigateway.deletegateway.begin |
| Update Delegation Subscription - Begin | com.oraclecloud.delegateaccesscontrol.updatedelegationsubscription.begin |
| MySQL - Generate HeatWave Cluster Memory Estimate End | com.oraclecloud.mysqlaas.generateheatwaveclustermemoryestimate.end |
| Ingest Time Rule - Disable | com.oraclecloud.logginganalytics.disableingesttimerule |
| Instance - Create End | com.oraclecloud.apiplatform.createapiplatforminstance.end |
| Autonomous Database - Update DB Tools End | com.oraclecloud.databaseservice.updateautonomousdatabasetools.end |
| SQL Firewall Collection Start - End | com.oraclecloud.datasafe.startsqlcollection.end |
| Delete Global Accelerator Begin | com.oraclecloud.gax.public.api.deleteglobalaccelerator.begin |
| PathAnalysis - Async End | com.oraclecloud.vnconfigadvisor.getpathanalysis.end |
| Source - Delete Begin | com.oraclecloud.applicationmigration.deletesource.begin |
| Fusion Environment - Maintenance End | com.oraclecloud.fusionappsinternal.fusionenvironmentmaintenance.end |
| Query Service - Delete Project Begin | com.oraclecloud.queryservice.deleteproject.begin |
| Query Service - Delete Project End | com.oraclecloud.queryservice.deleteproject.end |
| Query Service - Update Project | com.oraclecloud.queryservice.updateproject |
| Query Service - Change Project Compartment End  | com.oraclecloud.queryservice.changeprojectcompartment.end |
| Query Service - Create Project Begin | com.oraclecloud.queryservice.createproject.begin |
| Query Service - Create Project End | com.oraclecloud.queryservice.createproject.end |
| Query Service - Change Project Compartment Begin | com.oraclecloud.queryservice.changeprojectcompartment.begin |
| MFA TOTP Device - Delete | com.oraclecloud.identitycontrolplane.deletemfatotpdevice |
| Oneoff Patch - Delete End | com.oraclecloud.databaseservice.deleteoneoffpatch.end |
| Web Application Acceleration Policy - Create End | com.oraclecloud.waa.createwebappaccelerationpolicy.end |
| Managed Instance - Sync Metadata | com.oraclecloud.osmh.syncmetadata |
| Source Event Types - Disable | com.oraclecloud.logginganalytics.disablesourceeventtypes |
| FsuDiscovery - Create End | com.oraclecloud.fsu.creatediscovery.end |
| Managed Instance - Remove Snaps | com.oraclecloud.osmh.removesnaps |
| Dismissed - Problem | com.oraclecloud.cloudguard.problemdismissed |
| Sensitive Data Model Create - End | com.oraclecloud.datasafe.createsensitivedatamodel.end |
| GGS Pipeline - Delete Pipeline End | com.oraclecloud.goldengate.deletepipeline.end |
| Cache Database - Stop Cache Agent End | com.oraclecloud.zerolatency.stopcacheagent.end |
| BDS Instance - Create End | com.oraclecloud.bds.cp.createinstance.end |
| Update Volume End | com.oraclecloud.blockvolumes.updatevolume.end |
| Distributed Autonomous Database - Download GSM Certificate Signing Request | com.oraclecloud.globaldb.downloaddistributedautonomousdatabasegsmcertificatesigningrequest |
| Instance - Update Instance Begin | com.oraclecloud.blockchain.updateplatforminstance.begin |
| Database - Move Begin | com.oraclecloud.databaseservice.movedatabase.begin |
| HostScanTargets - Update | com.oraclecloud.vulnerabilityscanning.updatehostscantarget.end |
| Sensitive Data Model Create - Begin | com.oraclecloud.datasafe.createsensitivedatamodel.begin |
| Exadata Infrastructure - Maintenance Rescheduled With Reason | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancerescheduledwithreason |
| BDS Metastore Configuration Instance - Activate Metastore Configuration Begin | com.oraclecloud.bds.cp.activatebdsmetastoreconfiguration.begin |
| Cluster Network - Create End | com.oraclecloud.computemanagement.createclusternetwork.end |
| Managed Instance - Detach Child Software Source | com.oraclecloud.osms.detachchildsoftwaresourcefrommanagedinstance |
| Delete Alert Policy - End | com.oraclecloud.datasafe.deletealertpolicy.end |
| Fusion Environment - Refresh End | com.oraclecloud.fusionapps.fusionenvironmentrefresh.end |
| HTTP Monitor - Create | com.oraclecloud.healthchecks.createhttpmonitor |
| Integration Instance - Create Begin | com.oraclecloud.integration.createintegrationinstance.begin |
| Recovery Service Subnet - Delete End | com.oraclecloud.autonomousrecoveryservice.deleterecoveryservicesubnet.end |
| Instance - Stop Instance End | com.oraclecloud.blockchain.stopplatforminstance.end |
| Work Request - Import Content Begin | com.oraclecloud.osmh.importcontent.begin |
| Create Inventory Begin | com.oraclecloud.cloudbridge.createinventory.begin |
| Create Iot Domain - End | com.oraclecloud.iot.createiotdomain.end |
| Security Policy Configuration Update - End | com.oraclecloud.datasafe.updatesecuritypolicyconfig.end |
| Delete Certificate | com.oraclecloud.waf.deletecertificate |
| Migration - Migrate Application Begin | com.oraclecloud.applicationmigration.migrateapplication.begin |
| Protected Database - Change Billing Compartment Begin | com.oraclecloud.autonomousrecoveryservice.changeprotecteddatabasebillingcompartment.begin |
| User UI Password - Update | com.oraclecloud.identityprovisioning.updateuseruipassword |
| Data Store - Update Begin | com.oraclecloud.dataexchange.updatedatastore.begin |
| Key Store - Terminate | com.oraclecloud.databaseservice.deletekeystore |
| Key Store - Create | com.oraclecloud.databaseservice.createkeystore |
| Cancel Cascade Delete Project - begin | com.oraclecloud.devopsproject.cancelscheduledcascadingprojectdeletion.begin |
| Deployment - Create | com.oraclecloud.devopsdeploy.createdeployment |
| Stream Packaging Config - Delete | com.oraclecloud.mediaservices.deletestreampackagingconfig |
| Language - Create Project End | com.oraclecloud.aiservicelanguage.createproject.end |
| Model - Activate | com.oraclecloud.datascience.activatemodel |
| Work Request - Install Snaps Begin | com.oraclecloud.osmh.installsnaps.begin |
| Asset - Create Begin | com.oraclecloud.dataexchange.createasset.begin |
| Backup Destination - Change Compartment | com.oraclecloud.databaseservice.changebackupdestinationcompartment |
| Node - Update | com.oraclecloud.oraclerovingedgeinfrastructure.updatenode |
| ZPR Policy - Delete Begin | com.oraclecloud.zpr.deletezprpolicy.begin |
| ZPR Configuration - Delete Begin | com.oraclecloud.zpr.deleteconfiguration.begin |
| ZPR Configuration - Delete End | com.oraclecloud.zpr.deleteconfiguration.end |
| ZPR Policy - Delete End | com.oraclecloud.zpr.deletezprpolicy.end |
| Object Storage Link Sync Job - Start Export Job | com.oraclecloud.lustrefilestorage.startexporttoobject |
| Event - Create Update All Packages Event | com.oraclecloud.osmh.createevent.softwareupdate.updateallpackages |
| Migration Clone End | com.oraclecloud.odms.clonemigration.end |
| VirtualDeployment - Change Compartment End | com.oraclecloud.servicemesh.changevirtualdeploymentcompartment.end |
| OSN - Delete OSN Begin | com.oraclecloud.blockchain.deleteosn.begin |
| Service Instance - Patch End | com.oraclecloud.zerolatency.applypatchzerolatency.end |
| Autonomous Container Database - Convert To Snapshot Standby End | com.oraclecloud.databaseservice.autonomous.container.database.snapshot.standby.conversion.end |
| LicenseManager - Create LicenseRecord | com.oraclecloud.licensemanager.createlicenserecord |
| Application - Delete | com.oraclecloud.dataflow.deleteapplication |
| Local Peering Gateway - Create | com.oraclecloud.virtualnetwork.createlocalpeeringgateway |
| SQL Firewall Collection Logs Purge - End | com.oraclecloud.datasafe.purgesqlcollectionlogs.end |
| Scheduled Job - Change Compartment | com.oraclecloud.osms.changescheduledjobcompartment |
| AI Data Platform - Delete Begin | com.oraclecloud.aidataplatform.deleteaidataplatform.begin |
| Object - Create | com.oraclecloud.objectstorage.createobject |
| Distributed Database - Add GDSCTL Node Begin | com.oraclecloud.globaldb.adddistributeddatabasegdscontrolnode.begin |
| Cache Database - Open End | com.oraclecloud.zerolatency.openzerolatencydatabase.end |
| HostScanTarget - Create | com.oraclecloud.vulnerabilityscanning.createhostscantarget.begin |
| Autonomous Container Database - Create Backup End | com.oraclecloud.databaseservice.autonomous.container.database.backup.end |
| Exascale Database Storage Vault - Create Begin | com.oraclecloud.databaseservice.createexascaledbstoragevault.begin |
| Product - Create | com.oraclecloud.subscriptionpricingservice.createproduct |
| Distributed Database Private Endpoint - Change Compartment Begin | com.oraclecloud.globaldb.changedistributeddatabaseprivateendpointcompartment.begin |
| Cache Database - Create Begin | com.oraclecloud.zerolatency.createzerolatencydatabase.begin |
| Global Autonomous Database - Delete Begin | com.oraclecloud.globaldb.deleteshardeddatabase.begin |
| Network Security Group - Update | com.oraclecloud.virtualnetwork.updatenetworksecuritygroup |
| Entitlement - Move | com.oraclecloud.oraclerovingedgeinfrastructure.moveentitlement |
| Create Delegation Control - End | com.oraclecloud.delegateaccesscontrol.createdelegationcontrol.end |
| Sensitive Type Create - End | com.oraclecloud.datasafe.createsensitivetype.end |
| Vault - Schedule Deletion End | com.oraclecloud.keymanagementservice.schedulevaultdeletion.end |
| CreateAsset | com.oraclecloud.cloudbridge.createasset |
| Fleet - Create Begin | com.oraclecloud.javamanagementservice.createfleet.begin |
| Work Request - Disable Module Streams Begin | com.oraclecloud.osmh.disablemodulestreams.begin |
| Database Tools Private Endpoint - Create Begin | com.oraclecloud.dbtoolsserviceapi.createdatabasetoolsprivateendpoint.begin |
| Database Security Config Refresh - Begin | com.oraclecloud.datasafe.refreshdatabasesecurityconfig.begin |
| Auth Token - Delete | com.oraclecloud.identitycontrolplane.deleteauthtoken |
| Media Workflow Job - Delete end | com.oraclecloud.mediaservices.deletemediaworkflowjob.end |
| Create Target Database - End | com.oraclecloud.datasafe.createtargetdatabase.end |
| MySQL - Create Configuration | com.oraclecloud.mysqlaas.createconfiguration |
| Copy Volume Backup End | com.oraclecloud.blockvolumes.copyvolumebackup.end |
| Delete Boot Volume Kms Key Begin | com.oraclecloud.blockvolumes.deletebootvolumekmskey.begin |
| Instance Pool - Reset Action End | com.oraclecloud.computemanagement.resetinstancepool.end |
| Managed Instance - Remove Content | com.oraclecloud.osmh.removecontent |
| DR Protection Group - Delete End | com.oraclecloud.disasterrecovery.deletedrprotectiongroup.end |
| Instance Pool - Pre Termination End | com.oraclecloud.computemanagement.instancepoolpreterminationaction.end |
| Delete Volume Group Backup Begin | com.oraclecloud.blockvolumes.deletevolumegroupbackup.begin |
| DR Plan - Delete End | com.oraclecloud.disasterrecovery.deletedrplan.end |
| Idp SCIM Client - Reset | com.oraclecloud.identitycontrolplane.resetidpscimclient |
| VMware Solution - Create Cluster End | com.oraclecloud.vmwaresolution.createcluster.end |
| Capacity Reservation - Delete reservation begin | com.oraclecloud.computeapi.deletecomputecapacityreservation.begin |
| Event - Create Reboot Succeeded After Timeout Event | com.oraclecloud.osmh.createevent.reboot.rebootsucceededaftertimeout |
| Create Volume Group End | com.oraclecloud.blockvolumes.createvolumegroup.end |
| Access Request Shared Operator - Create | com.oraclecloud.operatorcontrol.addsharedoperator |
| VMware Solution - Retrieve Password | com.oraclecloud.vmwaresolution.retrievepassword |
| Model Deployment - Delete Begin | com.oraclecloud.datascience.deletemodeldeployment.begin |
| VMware Solution - List Clusters | com.oraclecloud.vmwaresolution.listclusters |
| Unified Audit Policy Definition Update - End | com.oraclecloud.datasafe.updateunifiedauditpolicydefinition.end |
| Work Request - Update Ksplice Kernel Begin | com.oraclecloud.osmh.updateksplicekernel.begin |
| Resource Schedule - Activate | com.oraclecloud.resourcescheduler.activateschedule |
| Managed Instance Group - Attach Managed Instance | com.oraclecloud.osms.attachmanagedinstancetomanagedinstancegroup |
| Kafka Cluster - Update Begin | com.oraclecloud.rawfkaapiprod.updatekafkacluster.begin |
| Work Request - Install Windows Updates Begin | com.oraclecloud.osmh.installwindowsupdates.begin |
| Instance - Create Instance | com.oraclecloud.analytics.createanalyticsinstance |
| Managed Instance - Install Windows Bug Fix Updates | com.oraclecloud.osmh.installbugfixwindowsupdates |
| BuildPipeline - Create End | com.oraclecloud.devopsbuild.createbuildpipeline.end |
| DR Plan Execution - CreateFailoverPreCheck End | com.oraclecloud.disasterrecovery.createfailoverprecheckdrplanexecution.end |
| Distributed Database - Validate Network Begin | com.oraclecloud.globaldb.validatedistributeddatabasenetwork.begin |
| MySQL - Delete HeatWave Cluster End | com.oraclecloud.mysqlaas.deleteheatwavecluster.end |
| DeployArtifact - Delete End | com.oraclecloud.devopsdeploy.deletedeployartifact.end |
| Fusion Environment - Change Compartment End | com.oraclecloud.fusionapps.changefusionenvironmentcompartment.end |
| Distributed Database - Change Compartment Begin | com.oraclecloud.globaldb.changedistributeddatabasecompartment.begin |
| Global Autonomous Database - Prevalidate | com.oraclecloud.globaldb.prevalidateshardeddatabase |
| Console History - Update | com.oraclecloud.computeapi.updateconsolehistory |
| Work Request - Update Other End | com.oraclecloud.osmh.updateother.end |
| Node - Disable Administrator Shell Access End | com.oraclecloud.zerolatency.disableadminshellaccess.end |
| Managed Instance - Remove Package | com.oraclecloud.osms.removepackagefrommanagedinstance |
| Logical Entities - Change | com.oraclecloud.datacatalog.changedlogicalentities |
| Subnet - Update | com.oraclecloud.virtualnetwork.updatesubnet |
| Key Store - Update | com.oraclecloud.databaseservice.updatekeystore |
| Operator Control - Delete | com.oraclecloud.operatorcontrol.deleteoperatorcontrol |
| Database Security Config Update - Begin | com.oraclecloud.datasafe.updatedatabasesecurityconfig.begin |
| VM Cluster - Terminate Begin | com.oraclecloud.databaseservice.deletevmcluster.begin |
| Service Provider Interaction Request | com.oraclecloud.delegateaccesscontrol.serviceproviderinteractionrequest |
| Global Database Private Endpoint - Update | com.oraclecloud.globaldb.updateprivateendpoint |
| Parser - Delete | com.oraclecloud.logginganalytics.deleteparser |
| Database Tools Connection - Create End | com.oraclecloud.dbtoolsserviceapi.createdatabasetoolsconnection.end |
| OCI Cache Cluster - Update End | com.oraclecloud.redisservice.updaterediscluster.end |
| VirtualServiceRouteTable - Change Compartment End | com.oraclecloud.servicemesh.changevirtualserviceroutetablecompartment.end |
| Desktop Pool - Update | com.oraclecloud.ocidesktopservice.updatedesktoppool |
| Work Request - Set Software Sources End | com.oraclecloud.osmh.setsoftwaresources.end |
| Cluster Network - Terminate End | com.oraclecloud.computemanagement.terminateclusternetwork.end |
| Run - End | com.oraclecloud.dataflow.createrun.end |
| Service Instance - Change Compartment End | com.oraclecloud.zerolatency.changezerolatencycompartment.end |
| SQL Firewall Collection Insights Refresh - Begin | com.oraclecloud.datasafe.refreshsqlcollectionloginsights.begin |
| EM Bridge - Create | com.oraclecloud.logginganalytics.createembridge |
| Work Request - Sync Management Station Mirror End | com.oraclecloud.osmh.syncmanagementstationmirror.end |
| DB Node - Reboot Migration Maintenance Scheduled | com.oraclecloud.databaseservice.dbnoderebootmigrationmaintenancescheduled |
| NodePool - Delete End | com.oraclecloud.clustersapi.deletenodepool.end |
| Vault - Create End | com.oraclecloud.keymanagementservice.createvault.end |
| Gateway - Create End | com.oraclecloud.apigateway.creategateway.end |
| MFA TOTP Device - Create | com.oraclecloud.identitycontrolplane.createmfatotpdevice |
| Work Request - Update Bug Fix Begin | com.oraclecloud.osmh.updatebugfix.begin |
| Cache Database - Initiate Checkpoint Begin | com.oraclecloud.zerolatency.checkpointzerolatencydatabase.begin |
| Discovery Schedule - Change compartment | com.oraclecloud.cloudbridge.changediscoveryschedulecompartment |
| GGS Pipeline - Deleted | com.oraclecloud.goldengate.pipeline.statedeleted |
| Peer - Update Peer End | com.oraclecloud.blockchain.updatepeer.end |
| Bastion - Create Bastion Begin | com.oraclecloud.bastion.createbastion.begin |
| Visual Builder Studio - Create Instance - begin | com.oraclecloud.vbstudioinst.createvbsinstance.begin |
| DFI Cluster: List Clusters | com.oraclecloud.dataflowinteractive.listinteractiveclusters |
| Autonomous Database - AccessControl Lists Update End | com.oraclecloud.databaseservice.updateautonomousdatabaseacl.end |
| Asset - Update Begin | com.oraclecloud.dataexchange.updateasset.begin |
| Assetsource - Refresh End | com.oraclecloud.cloudbridge.refreshassetsource.end |
| Delete NetworkFirewallPolicy End | com.oraclecloud.networkfirewallservice.deletenetworkfirewallpolicy.end |
| Instance Maintenance Event - Begin | com.oraclecloud.computeapi.instancemaintenance.begin |
| Autonomous Container Database -  Rotate Encryption Key Begin | com.oraclecloud.databaseservice.rotateautonomouscontainerdatabaseencryptionkey.begin |
| Event - Create Switch Module Stream Event | com.oraclecloud.osmh.createevent.softwaresource.switchmodulestream |
| Password - Create or Reset | com.oraclecloud.identitycontrolplane.createorresetpassword |
| Private Service Access - Update Begin | com.oraclecloud.privateserviceaccess.updateprivateserviceaccess.begin |
| Work Request - List Windows Update Begin | com.oraclecloud.osmh.listwindowsupdate.begin |
| Forecasting - Change Data Asset Compartment | com.oraclecloud.aiserviceforecast.changedataassetcompartment |
| Forecasting - Change Project Compartment | com.oraclecloud.aiserviceforecast.changeprojectcompartment |
| Forecasting - Change Forecast Compartment | com.oraclecloud.aiserviceforecast.changeforecastcompartment |
| Service Gateway - Change Compartment | com.oraclecloud.servicegateway.changeservicegatewaycompartment |
| Network Source - Delete | com.oraclecloud.identitycontrolplane.deletenetworksource |
| Work Request - Create Software Source End | com.oraclecloud.osmh.createsoftwaresource.end |
| Pipeline - Create | com.oraclecloud.datascience.createpipeline |
| NodePool - Create End | com.oraclecloud.clustersapi.createnodepool.end |
| Masking Column Delete | com.oraclecloud.datasafe.deletemaskingcolumn |
| Global Autonomous Database - Configure GSMs End | com.oraclecloud.globaldb.configureshardeddatabasegsms.end |
| Capacity Reservation - Delete reservation end | com.oraclecloud.computeapi.deletecomputecapacityreservation.end |
| Sensitive Type Delete | com.oraclecloud.datasafe.deletesensitivetype |
| Container Instance - Stop Container Instance End | com.oraclecloud.containerinstances.stopcontainerinstance.end |
| Process Automation Instance - Delete End | com.oraclecloud.processautomation.deleteopainstance.end |
| Work Request - Stage Update End | com.oraclecloud.osmh.stageupdate.end |
| Route Table - Change Compartment | com.oraclecloud.virtualnetwork.changeroutetablecompartment |
| Delete Target Database - Begin | com.oraclecloud.datasafe.deletetargetdatabase.begin |
| Web Application Acceleration - Create Begin | com.oraclecloud.waa.createwebappacceleration.begin |
| Oneoff Patch - Create End | com.oraclecloud.databaseservice.createoneoffpatch.end |
| Throttled Expired Snapshot Deletion | com.oraclecloud.filestorage.throttledexpiredsnapshotdeletion |
| Cloud Exadata Infrastructure - Critical Events | com.oraclecloud.databaseservice.exadatainfrastructure.critical |
| Deploy Artifacts - Begin | com.oraclecloud.dataintelligencefoundation.deployartifacts.begin |
| Autonomous Container Database - Update Begin | com.oraclecloud.databaseservice.autonomous.container.database.instance.update.begin |
| Application - Update Begin | com.oraclecloud.ohaaas.updateapplication.begin |
| Instance - Stop Instance End | com.oraclecloud.analytics.stopanalyticsinstance.end |
| Work Request - Validate Software Source End | com.oraclecloud.osmh.validatesoftwaresource.end |
| Node - Create | com.oraclecloud.oraclerovingedgeinfrastructure.createnode |
| Global Database Private Endpoint - Create End | com.oraclecloud.globaldb.createprivateendpoint.end |
| HTTP Receive Pack | com.oraclecloud.devopscoderepo.httpreceivepack |
| Topic - Delete | com.oraclecloud.notification.deletetopic |
| Object Storage Link - Create | com.oraclecloud.lustrefilestorage.createobjectstoragelink |
| Portfolio Cost - Get | com.oraclecloud.atat.getportfoliocost |
| Service Instance - Patch Begin | com.oraclecloud.zerolatency.applypatchzerolatency.begin |
| Package - Update | com.oraclecloud.datatransferservice.attachdevicestotransferpackage |
| Delete Custom Protection Rule | com.oraclecloud.waf.deletecustomprotectionrule |
| Internet Gateway - Update | com.oraclecloud.virtualnetwork.updateinternetgateway |
| MeshIngressGatewayRouteTable - Update End | com.oraclecloud.servicemesh.updateingressgatewayroutetable.end |
| WebLogic Domain - Install Latest Patches End | com.oraclecloud.weblogicmanagement.installlatestpatchesonwlsdomain.end |
| Access Request - Create | com.oraclecloud.operatorcontrol.createaccessrequest |
| Create Alert Policy - End | com.oraclecloud.datasafe.createalertpolicy.end |
| Managed Instance - Reboot | com.oraclecloud.osmh.reboot |
| Create Global Accelerator Begin | com.oraclecloud.gax.public.api.createglobalaccelerator.begin |
| BDS Instance - Update Resource Principal Configuration | com.oraclecloud.bds.cp.updateresourceprincipalconfiguration |
| Detection Rule - Update | com.oraclecloud.logginganalytics.updatescheduledtask |
| Anomaly Detection - Model training begin | com.oraclecloud.aiservice.trainmodel.begin |
| Masking Library Format Update - End | com.oraclecloud.datasafe.updatelibrarymaskingformat.end |
| DeployStage - Update End | com.oraclecloud.devopsdeploy.updatedeploystage.end |
| Customer Secret Key - Update | com.oraclecloud.identitycontrolplane.updatecustomersecretkey |
| BDS Instance - Get Autoscale Configuration(s) | com.oraclecloud.bds.cp.getautoscaleconfiguration |
| Report Schedule - Begin | com.oraclecloud.datasafe.schedulereport.begin |
| BDS Instance - Configure Remove Kafka End | com.oraclecloud.bds.cp.removekafka.end |
| Create Volume Group Backup Begin | com.oraclecloud.blockvolumes.createvolumegroupbackup.begin |
| Event - Software Source Updated | com.oraclecloud.osmh.event.softwaresourceupdated |
| Media Workflow - Move Compartment | com.oraclecloud.mediaservices.changemediaworkflowcompartment |
| Object Storage Link - Update | com.oraclecloud.lustrefilestorage.updateobjectstoragelink |
| Cache Database - Stop Cache Agent Begin | com.oraclecloud.zerolatency.stopcacheagent.begin |
| Entitlement - Create | com.oraclecloud.oraclerovingedgeinfrastructure.createentitlement |
| Create Global Accelerator Hostname End | com.oraclecloud.gax.public.api.createhostname.end |
| Idp User - Delete | com.oraclecloud.identitycontrolplane.deleteidpuser |
| Database - Update Begin | com.oraclecloud.databaseservice.updatedatabase.begin |
| Create Pull Request - Begin | com.oraclecloud.devopscoderepo.createpullrequest.begin |
| Data Exchange - Update End | com.oraclecloud.dataexchange.updatedataexchange.end |
| Oracle managed datbase software update readiness check successful | com.oraclecloud.databaseservice.managedsoftwareupdatereadinesschecksuccessful |
| Bastion - Update Bastion Begin | com.oraclecloud.bastion.updatebastion.begin |
| Throttled Policy-based Snapshot Creation | com.oraclecloud.filestorage.throttledpolicybasedsnapshotcreation |
| API - Change Compartment End | com.oraclecloud.apigateway.changeapicompartment.end |
| MySQL - Upgrade DB System - Update Crash Recovery End | com.oraclecloud.mysqlaas.updatecrashrecoveryforupgrade.end |
| RevCycleEnvironment - Delete End | com.oraclecloud.ircscontrolplaneapi.deleterevcycleenvironment.end |
| BDS Instance - Delete Resource Principal Configuration End | com.oraclecloud.bds.cp.deleteresourceprincipalconfiguration.end |
| Security List - Update | com.oraclecloud.virtualnetwork.updatesecuritylist |
| TriggeredAlert - Delete | com.oraclecloud.budgets.deletetriggeredalert |
| Model - Create | com.oraclecloud.datascience.createmodel |
| FsuCycle - Success | com.oraclecloud.fsu.fsucycle.success |
| Delete Export | com.oraclecloud.filestorage.deleteexport |
| Stack - Delete | com.oraclecloud.oracleresourcemanager.deletestack |
| Create Volume Group | com.oraclecloud.blockvolumes.createvolumegroup |
| WebLogic Domain - Start Begin | com.oraclecloud.weblogicmanagement.startwlsdomain.begin |
| RevCycleEnvironmentGroup - Create End | com.oraclecloud.ircscontrolplaneapi.createrevcycleenvironmentgroup.end |
| DR Plan Execution - CreateStartDrill End | com.oraclecloud.disasterrecovery.createstartdrilldrplanexecution.end |
| Source - Create End | com.oraclecloud.applicationmigration.createsource.end |
| Key - Schedule Deletion Begin | com.oraclecloud.keymanagementservice.schedulekeydeletion.begin |
| Global Database Private Endpoint - Delete End | com.oraclecloud.globaldb.deleteprivateendpoint.end |
| Distributed Autonomous Database - Delete Begin | com.oraclecloud.globaldb.deletedistributedautonomousdatabase.begin |
| Pipeline Run - Create Begin | com.oraclecloud.datascience.createpipelinerun.begin |
| DFI Cluster: Update End | com.oraclecloud.dataflowinteractive.updateinteractivecluster.end |
| Work Request - Collect Metadata End | com.oraclecloud.osmh.collectmetadata.end |
| Autonomous Cloud VM Cluster - Change Compartment Begin | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.changecompartment.begin |
| Rotate On-Prem Connector - Begin | com.oraclecloud.datasafe.updateonpremconnectorwallet.begin |
| AlertRule - Create | com.oraclecloud.budgets.createalertrule |
| Fusion Environment Family - Delete Begin | com.oraclecloud.fusionapps.deletefusionenvironmentfamily.begin |
| Data Exchange - Delete Begin | com.oraclecloud.dataexchange.deletedataexchange.begin |
| NodePool - Create Begin | com.oraclecloud.clustersapi.createnodepool.begin |
| Security Policy Deployment Create - Begin | com.oraclecloud.datasafe.createsecuritypolicydeployment.begin |
| Instance Pool - Detach Load Balancer End | com.oraclecloud.computemanagement.detachloadbalancer.end |
| Database Software Image - Delete Begin | com.oraclecloud.databaseservice.deletedatabasesoftwareimage.begin |
| Parser - Upsert | com.oraclecloud.logginganalytics.upsertparser |
| Create Volume Backup Begin | com.oraclecloud.blockvolumes.createvolumebackup.begin |
| DR Plan Execution - CreateFailover Begin | com.oraclecloud.disasterrecovery.createfailoverdrplanexecution |
| Cache Database - Delete Diagnostics Begin | com.oraclecloud.zerolatency.deletezerolatencydatabasediagnostics.begin |
| Vault - Change Compartment Begin | com.oraclecloud.keymanagementservice.changevaultcompartment.begin |
| Autoscaling Configuration - Delete | com.oraclecloud.autoscaling.deleteautoscalingconfiguration |
| Service Instance - Stop Server Begin | com.oraclecloud.zerolatency.stoptimestenserver.begin |
| Upload Log File | com.oraclecloud.logginganalytics.uploadlogfile |
| Media Workflow - Delete | com.oraclecloud.mediaservices.deletemediaworkflow |
| Protected Database - Update Begin | com.oraclecloud.autonomousrecoveryservice.updateprotecteddatabase.begin |
| Batch Context - Create End | com.oraclecloud.batch.createbatchcontext.end |
| Table - Create Begin | com.oraclecloud.nosql.createtable.begin |
| Language - Delete Project End | com.oraclecloud.aiservicelanguage.deleteproject.end |
| Speech - Completed Transcription Job | com.oraclecloud.aiservicespeech.completedtranscriptionjob |
| Distributed Autonomous Database - Prevalidate | com.oraclecloud.globaldb.prevalidatedistributedautonomousdatabase |
| Kafka Cluster - Delete End | com.oraclecloud.rawfkaapiprod.deletekafkacluster.end |
| Fusion Environment - Update Begin | com.oraclecloud.fusionapps.updatefusionenvironment.begin |
| Delete Inventory End | com.oraclecloud.cloudbridge.deleteinventory.end |
| Application Data Platform - PodDb Create from Backup End | com.oraclecloud.applicationdataplatform.poddbcreatefrombackup.end |
| Masking Job - Begin | com.oraclecloud.datasafe.maskdata.begin |
| Update Http Redirect Begin | com.oraclecloud.waf.updatehttpredirect.begin |
| Batch Job Pool - Delete | com.oraclecloud.batch.deletebatchjobpool |
| Delete Waas Policy End | com.oraclecloud.waf.deletewaaspolicy.end |
| Mesh - Create End | com.oraclecloud.servicemesh.createmesh.end |
| Db Node Snapshot - Create Begin | com.oraclecloud.databaseservice.createdbnodesnapshot.begin |
| Asset - Update End | com.oraclecloud.dataexchange.updateasset.end |
| AccessPolicy - Create Begin | com.oraclecloud.servicemesh.createaccesspolicy.begin |
| Database - Terminate End | com.oraclecloud.databaseservice.deletedatabase.end |
| External MySQL Connector - Delete Begin | com.oraclecloud.databasemanagement.externalmysqlresource.connector.delete.begin |
| BDS Instance - Configure Disable ODH Service Certificate Begin | com.oraclecloud.bds.cp.disableodhservicecertificate.begin |
| HostAgentScanResult - ChangeCompartment | com.oraclecloud.vulnerabilityscanning.changehostagentscanresultcompartment |
| Masking Library Format Update - Begin | com.oraclecloud.datasafe.updatelibrarymaskingformat.begin |
| Change Custom Protection Rule Compartment | com.oraclecloud.waf.changecustomprotectionrulecompartment |
| DB Node - Update End | com.oraclecloud.databaseservice.dbnodeaction.end |
| Local Peering Gateway - Delete | com.oraclecloud.virtualnetwork.deletelocalpeeringgateway |
| Container Instance - Update Container End | com.oraclecloud.containerinstances.updatecontainer.end |
| SQL Firewall Policy Generate - Begin | com.oraclecloud.datasafe.generatesqlfirewallpolicy.begin |
| Audit Events Post Retention Purge | com.oraclecloud.datasafe.purgeretention |
| Batch Task Environment - Update | com.oraclecloud.batch.updatebatchtaskenvironment |
| Update Waas Policy Custom Protection Rules End | com.oraclecloud.waf.updatewaaspolicycustomprotectionrules.end |
| Data Guard Create Standby Database - Create Begin | com.oraclecloud.databaseservice.createstandbydatabase.begin |
| Create Global Accelerator Routing Policy Begin | com.oraclecloud.gax.public.api.createroutingpolicy.begin |
| Migration Delete End | com.oraclecloud.odms.deletemigration.end |
| Idp Group - Add User To | com.oraclecloud.identitycontrolplane.addusertoidpgroup |
| Service Instance - Stop End | com.oraclecloud.zerolatency.stopzerolatency.end |
| DB Home - Create End | com.oraclecloud.databaseservice.createdbhome.end |
| Bastion - Delete Session Begin | com.oraclecloud.bastion.deletesession.begin |
| VCN - Update | com.oraclecloud.virtualnetwork.updatevcn |
| GGS Pipeline - Create Pipeline End | com.oraclecloud.goldengate.createpipeline.end |
| HostVulnerabilityCsv - Export | com.oraclecloud.vulnerabilityscanning.exporthostvulnerabilitycsv |
| WebLogic Domain - Restore End | com.oraclecloud.weblogicmanagement.restorewlsdomain.end |
| BDS Instance - Update Autoscale Configuration | com.oraclecloud.bds.autoscale.cp.updateautoscaleconfiguration |
| Access Request - Extend | com.oraclecloud.operatorcontrol.extendaccessrequest |
| Job Delete Begin | com.oraclecloud.odms.deletejob.begin |
| OCI Cache Cluster - Change Compartment End | com.oraclecloud.redisservice.changeredisclustercompartment.end |
| VCN - Delete | com.oraclecloud.virtualnetwork.deletevcn |
| Service Gateway - Attach Service | com.oraclecloud.servicegateway.attachserviceid |
| Instance Pool - Soft Reset Action Begin | com.oraclecloud.computemanagement.softresetinstancepool.begin |
| Instance Pool - Soft Stop Action Begin | com.oraclecloud.computemanagement.softstopinstancepool.begin |
| RevCycleEnvironment - Update Begin | com.oraclecloud.ircscontrolplaneapi.updaterevcycleenvironment.begin |
| Autonomous Container Database - Convert To Physical Standby Reminder | com.oraclecloud.dbaas.autonomous.container.database.automatic.conversion.to.physical.standby.reminder |
| Scheduled Job - Delete | com.oraclecloud.osms.deletescheduledjob |
| Work Request - Remove Module Profiles End | com.oraclecloud.osmh.removemoduleprofiles.end |
| Imaging - Add Shape Compatibility | com.oraclecloud.computeimagingapi.addimageshapecompatibility |
| Autonomous Database - Backup Update - End | com.oraclecloud.databaseservice.autonomous.database.backup.updateautonomousdatabasebackup.end |
| Console History - Capture End | com.oraclecloud.computeapi.captureconsolehistory.end |
| Pricing Rule - Update | com.oraclecloud.subscriptionpricingservice.updatepricingrule |
| Customer Secret Key - Create | com.oraclecloud.identitycontrolplane.createcustomersecretkey |
| Software Source - Delete | com.oraclecloud.osms.deletesoftwaresource |
| BDS Metastore Configuration Instance - Update Metastore Configuration Begin | com.oraclecloud.bds.cp.updatebdsmetastoreconfiguration.begin |
| Update Global Accelerator Routing Policy End | com.oraclecloud.gax.public.api.updateroutingpolicy.end |
| BDS Instance - Replace Node Begin | com.oraclecloud.bds.cp.replacenode.begin |
| Create Volume Backup Policy Assignment | com.oraclecloud.blockvolumes.createvolumebackuppolicyassignment |
| Report Schedule - End | com.oraclecloud.datasafe.schedulereport.end |
| BDS Instance - Update NodeBackup Configuration | com.oraclecloud.bds.cp.updatenodebackupconfig |
| Container Instance - Start Container Instance Begin | com.oraclecloud.containerinstances.startcontainerinstance.begin |
| Global Autonomous Database - Validate Network Begin | com.oraclecloud.globaldb.validatenetwork.begin |
| Create Workspace - End | com.oraclecloud.dataintegration.createdisworkspace.end |
| MySQL - Delete Configuration | com.oraclecloud.mysqlaas.deleteconfiguration |
| VirtualServiceRouteTable - Create End | com.oraclecloud.servicemesh.createvirtualserviceroutetable.end |
| Update Delegation Subscription - End | com.oraclecloud.delegateaccesscontrol.updatedelegationsubscription.end |
| Autonomous VM Cluster - Create End | com.oraclecloud.databaseservice.createautonomousvmcluster.end |
| Work Request - Install Enhancement Windows Updates Begin | com.oraclecloud.osmh.installenhancementwindowsupdates.begin |
| Instance Pool - Reset Action Begin | com.oraclecloud.computemanagement.resetinstancepool.begin |
| Public IP - Change Compartment | com.oraclecloud.virtualnetwork.changepublicipcompartment |
| App Configuration Delete - Begin | com.oraclecloud.appconfiguration.deleteappconfiguration.begin |
| Managed Instance Group - Delete | com.oraclecloud.osms.deletemanagedinstancegroup |
| List Workspace | com.oraclecloud.dataintegration.listworkspace |
| Key - Restore End | com.oraclecloud.keymanagementservice.restorekey.end |
| Create Repository - End | com.oraclecloud.devopscoderepo.createrepository.end |
| Event - Kernel Crash | com.oraclecloud.osmh.event.kernelcrash |
| Oracle managed database software update started | com.oraclecloud.databaseservice.managedsoftwareupdatestarted |
| Fusion Environment - Terminate Begin | com.oraclecloud.fusionapps.terminatefusionenvironment.begin |
| MySQL - Update Backup | com.oraclecloud.mysqlaas.updatebackup |
| VM Cluster - Audit | com.oraclecloud.databaseservice.vmcluster.audit |
| Instance Maintenance Event - End | com.oraclecloud.computeapi.instancemaintenance.end |
| Migration - Create Begin | com.oraclecloud.applicationmigration.createmigration.begin |
| Event - Create Install Module Profiles Event | com.oraclecloud.osmh.createevent.softwaresource.installmoduleprofile |
| Configure - Enable End | com.oraclecloud.datasafe.enabledatasafeservice.end |
| DRG Attachment - Delete | com.oraclecloud.virtualnetwork.deletedrgattachment |
| Event - Ksplice Exploit | com.oraclecloud.osmh.event.kspliceexploit |
| Data Guard Update Config - End | com.oraclecloud.databaseservice.updatedataguardconfig.end |
| Create NetworkFirewall Begin | com.oraclecloud.networkfirewallservice.createnetworkfirewall.begin |
| Managed Instance Group - Create | com.oraclecloud.osms.createmanagedinstancegroup |
| Execute Delegated Resource Access Request Command | com.oraclecloud.delegateaccesscontrol.executedelegatedresourceaccessrequestcommand |
| Fusion Environment Family  - Change Compartment End | com.oraclecloud.fusionapps.changefusionenvironmentfamilycompartment.end |
| Database Security Config Update - End | com.oraclecloud.datasafe.updatedatabasesecurityconfig.end |
| Lustre File System - Create End | com.oraclecloud.lustrefilestorage.createlustrefilesystem.end |
| Application Data Platform - PodDb Create End | com.oraclecloud.applicationdataplatform.createpoddb.end |
| Table - Add Replica End | com.oraclecloud.nosql.addreplica.end |
| Capacity Reservation - Create reservation end | com.oraclecloud.computeapi.createcomputecapacityreservation.end |
| Instance Pool - Create End | com.oraclecloud.computemanagement.createinstancepool.end |
| MySQL - Delete HeatWave Cluster Begin | com.oraclecloud.mysqlaas.deleteheatwavecluster.begin |
| BDS Lake Configuration Instance - Activate Lake Configuration Begin | com.oraclecloud.bds.cp.activatebdslakeconfiguration.begin |
| Auto Association - Disable | com.oraclecloud.logginganalytics.disableautoassociation |
| Create File System | com.oraclecloud.filestorage.createfilesystem |
| Job - Create Begin | com.oraclecloud.oracleresourcemanager.createjob.begin |
| DFI Cluster: Start End | com.oraclecloud.dataflowinteractive.startinteractivecluster.end |
| Unified Audit Policy Delete - Begin | com.oraclecloud.datasafe.deleteunifiedauditpolicy.begin |
| Report Generate - End | com.oraclecloud.datasafe.generatereport.end |
| Stop Workspace - Begin | com.oraclecloud.dataintegration.stopworkspace.begin |
| OMA - Delete Approval Template | com.oraclecloud.lockbox.deleteapprovaltemplate |
| Security Policy Update - End | com.oraclecloud.datasafe.updatesecuritypolicy.end |
| Autonomous Database - Update Open Mode End | com.oraclecloud.databaseservice.updateautonomousdatabaseopenmode.end |
| Managed Instance - Attach Parent Software Source | com.oraclecloud.osms.attachparentsoftwaresourcetomanagedinstance |
| Protected Database - Change Compartment Begin | com.oraclecloud.autonomousrecoveryservice.changeprotecteddatabasecompartment.begin |
| HostScanTarget - Delete | com.oraclecloud.vulnerabilityscanning.deletehostscantarget.begin |
| Sensitive Column Create - Begin | com.oraclecloud.datasafe.createsensitivecolumn.begin |
| Compute Host - Conformance Change | com.oraclecloud.computeapi.statechangehostconformance |
| Cache Database - Update Begin | com.oraclecloud.zerolatency.updatezerolatencydatabase.begin |
| DeployEnvironment - Update End | com.oraclecloud.devopsdeploy.updatedeployenvironment.end |
| Global Autonomous Database - Patch End | com.oraclecloud.globaldb.patchshardeddatabase.end |
| Event - Create Set Management Station Healthy State Event | com.oraclecloud.osmh.createevent.managementstation.setmanagementstationhealthstate.healthy |
| Assetsource - Create End | com.oraclecloud.cloudbridge.createassetsource.end |
| MySQL - Stop HeatWave Cluster End | com.oraclecloud.mysqlaas.stopheatwavecluster.end |
| Integration Instance - Update End | com.oraclecloud.integration.updateintegrationinstance.end |
| VM Cluster - Add Virtual Machine Begin | com.oraclecloud.databaseservice.vmclusteraddvirtualmachine.begin |
| VM Cluster - Update Begin | com.oraclecloud.databaseservice.updatevmcluster.begin |
| Peer - Update Peer Begin | com.oraclecloud.blockchain.updatepeer.begin |
| Peer - Delete Peer Begin | com.oraclecloud.blockchain.deletepeer.begin |
| Fleet - Change Compartment End | com.oraclecloud.javamanagementservice.changefleetcompartment.end |
| BuildRun - Create | com.oraclecloud.devopsbuild.createbuildrun |
| Work Request - Install All Windows Updates Begin | com.oraclecloud.osmh.installallwindowsupdates.begin |
| Exadb VM Cluster - Create Begin | com.oraclecloud.databaseservice.createexadbvmcluster.begin |
| Work Request - Stage Update Begin | com.oraclecloud.osmh.stageupdate.begin |
| Function - Delete | com.oraclecloud.functions.deletefunction |
| OCI Cache Cluster - Create End | com.oraclecloud.redisservice.createrediscluster.end |
| Create Global Accelerator Listener End | com.oraclecloud.gax.public.api.createlistener.end |
| Autonomous Container Database - Restore Begin | com.oraclecloud.databaseservice.autonomous.container.database.restore.begin |
| DR Plan Execution - Resume End | com.oraclecloud.disasterrecovery.resumedrplanexecution.end |
| Pluggable database - Modify Database Management Service End | com.oraclecloud.databaseservice.modifypdbmanagement.end |
| BDS Metastore Configuration Instance - Update Metastore Configuration End | com.oraclecloud.bds.cp.updatebdsmetastoreconfiguration.end |
| Web Application Acceleration - Update End | com.oraclecloud.waa.updatewebappacceleration.end |
| SSH Receive Pack | com.oraclecloud.devopscoderepo.sshreceivepack |
| VM Cluster - Create Begin | com.oraclecloud.databaseservice.createvmcluster.begin |
| DR Plan Execution - CreateStopDrill Begin | com.oraclecloud.disasterrecovery.createstopdrilldrplanexecution |
| GGS Deployment - Storage Utilization | com.oraclecloud.goldengate.storageutilization |
| Event - Create Reboot Failed Event | com.oraclecloud.osmh.createevent.reboot.rebootfailed |
| Fusion Environment - Maintenance Begin | com.oraclecloud.fusionappsinternal.fusionenvironmentmaintenance.begin |
| Key - Backup End | com.oraclecloud.keymanagementservice.backupkey.end |
| Migration - Update End | com.oraclecloud.applicationmigration.updatemigration.end |
| Create - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.createdelegatedresourceaccessrequest |
| Application - Delete | com.oraclecloud.functions.deleteapplication |
| Distributed Database - Generate GSM Certificate Signing Request End | com.oraclecloud.globaldb.generatedistributeddatabasegsmcertificatesigningrequest.end |
| FsuAction - Critical | com.oraclecloud.fsu.fsuaction.critical |
| Network Address List - Update End | com.oraclecloud.waf.updatenetworkaddresslist.end |
| Event - Rerun Accepted | com.oraclecloud.osmh.event.rerunaccepted |
| Stream Cell Assignment Group - Delete | com.oraclecloud.mediaservices.deletestreamcellassignmentgroup |
| MySQL - Update DB System End | com.oraclecloud.mysqlaas.updatedbsystem.end |
| Recovery Service Subnet - Change Compartment End | com.oraclecloud.autonomousrecoveryservice.changerecoveryservicesubnetcompartment.end |
| Create Global Accelerator Ruleset End | com.oraclecloud.gax.public.api.createruleset.end |
| Create Volume End | com.oraclecloud.blockvolumes.createvolume.end |
| Delete Repository - Begin | com.oraclecloud.devopscoderepo.deleterepository.begin |
| Instance - Change Compartment | com.oraclecloud.omh.changeomhinstancecompartment |
| OAuth Client Credential - Update | com.oraclecloud.identitycontrolplane.updateoauthclientcredential |
| WebLogic Domain - Stop End | com.oraclecloud.weblogicmanagement.stopwlsdomain.end |
| Resource Analytics Instance - Update Begin | com.oraclecloud.resourceanalytics.updateresourceanalyticsinstance.begin |
| Api Key - Upload | com.oraclecloud.identitycontrolplane.uploadapikey |
| Media Workflow Job - Create begin | com.oraclecloud.mediaservices.mediaworkflowjob.begin |
| Autonomous Container Database - Rotate Encryption Key End | com.oraclecloud.databaseservice.rotateautonomouscontainerdatabaseencryptionkey.end |
| Data Guard Reinstate - End | com.oraclecloud.databaseservice.dataguardreinstate.end |
| NodePool - Update Begin | com.oraclecloud.clustersapi.updatenodepool.begin |
| Process Automation Instance - Update End | com.oraclecloud.processautomation.updateopainstance.end |
| MySQL - Restart DB System Begin | com.oraclecloud.mysqlaas.restartdbsystem.begin |
| DB Node - Critical | com.oraclecloud.databaseservice.dbnode.critical |
| Work Request - Remove Snaps Begin | com.oraclecloud.osmh.removesnaps.begin |
| Bastion - Delete Session End | com.oraclecloud.bastion.deletesession.end |
| GGS Pipeline - Update Pipeline End | com.oraclecloud.goldengate.updatepipeline.end |
| VM Cluster - Add Virtual Machine End | com.oraclecloud.databaseservice.vmclusteraddvirtualmachine.end |
| Event - Create Update Security Event | com.oraclecloud.osmh.createevent.softwareupdate.updatesecurity |
| Resource Analytics Instance - Create End | com.oraclecloud.resourceanalytics.createresourceanalyticsinstance.end |
| Field - Upsert | com.oraclecloud.logginganalytics.upsertfield |
| Distributed Database - Configure Sharding Begin | com.oraclecloud.globaldb.configuredistributeddatabasesharding.begin |
| Global Autonomous Database - Change Compartment End | com.oraclecloud.globaldb.changeshardeddatabasecompartment.end |
| Approve Delegated Resource Access Request - Begin | com.oraclecloud.delegateaccesscontrol.approvedelegatedresourceaccessrequest.begin |
| Language - Update Project | com.oraclecloud.aiservicelanguage.updateproject |
| Forecasting - Update Data Asset | com.oraclecloud.aiserviceforecast.updatedataasset |
| Forecasting - Update Forecast | com.oraclecloud.aiserviceforecast.updateforecast |
| Forecasting - Update Project | com.oraclecloud.aiserviceforecast.updateproject |
| Resource Schedule - Create Begin | com.oraclecloud.resourcescheduler.createschedule.begin |
| HostScanTarget - Delete | com.oraclecloud.vulnerabilityscanning.deletehostscantarget.end |
| Alert Generation Throttled | com.oraclecloud.datasafe.throttlealertgeneration |
| Portfolio - Create begin | com.oraclecloud.atat.addportfolio.begin |
| Cache Database - Start Replication Agent Begin | com.oraclecloud.zerolatency.startreplicationagent.begin |
| Software Source - Add Package | com.oraclecloud.osms.addpackagestosoftwaresource |
| Distributed Autonomous Database - Delete End | com.oraclecloud.globaldb.deletedistributedautonomousdatabase.end |
| Web Application Firewall - Create Begin | com.oraclecloud.waf.createwebappfirewall.begin |
| Delete Volume Begin | com.oraclecloud.blockvolumes.deletevolume.begin |
| Audit Trail Update - Begin | com.oraclecloud.datasafe.updateaudittrail.begin |
| Database Tools Connection - Update Begin | com.oraclecloud.dbtoolsserviceapi.updatedatabasetoolsconnection.begin |
| Security Policy Deployment Delete - Begin | com.oraclecloud.datasafe.deletesecuritypolicydeployment.begin |
| BDS Lake Configuration Instance - Test Lake Configuration Begin | com.oraclecloud.bds.cp.testbdslakeconfiguration.begin |
| LicenseManager - Update ProductLicense | com.oraclecloud.licensemanager.updateproductlicense |
| DR Plan Execution - CreateStartDrillPreCheck End | com.oraclecloud.disasterrecovery.createstartdrillprecheckdrplanexecution.end |
| Distributed Database - Delete Begin | com.oraclecloud.globaldb.deletedistributeddatabase.begin |
| Migration - Create End | com.oraclecloud.applicationmigration.createmigration.end |
| Database - Delete Begin | com.oraclecloud.postgresql.deletedbsystem.begin |
| Change Volume Group Backup Compartment | com.oraclecloud.blockvolumes.changevolumegroupbackupcompartment |
| Update Global Accelerator Ruleset Begin | com.oraclecloud.gax.public.api.updateruleset.begin |
| MySQL - Delete Channel Begin | com.oraclecloud.mysqlaas.deletechannel.begin |
| WebLogic Domain - Restart Begin | com.oraclecloud.weblogicmanagement.restartwlsdomain.begin |
| Instance Console Connection - Update | com.oraclecloud.computeapi.updateinstanceconsoleconnection |
| Bucket - Update | com.oraclecloud.objectstorage.updatebucket |
| Delete On-Prem Connector - Begin | com.oraclecloud.datasafe.deleteonpremconnector.begin |
| Update Delegation Control - Begin | com.oraclecloud.delegateaccesscontrol.updatedelegationcontrol.begin |
| AlertRule - Update | com.oraclecloud.budgets.updatealertrule |
| FsuJob - Critical | com.oraclecloud.fsu.fsujob.critical |
| Audit Policy Provision - Begin | com.oraclecloud.datasafe.provisionauditpolicy.begin |
| Instance - Update | com.oraclecloud.apiplatform.updateapiplatforminstance |
| Waf Policy - Create End | com.oraclecloud.waf.createwebappfirewallpolicy.end |
| Oneoff Patch - Download End | com.oraclecloud.databaseservice.downloadoneoffpatch.end |
| Application - Create | com.oraclecloud.functions.createapplication |
| Create Iot DomainGroup - End | com.oraclecloud.iot.createiotdomaingroup.end |
| OMA - Change Resource Settings Compartment | com.oraclecloud.lockbox.changelockboxcompartment |
| Managed Instance - Collect Metadata | com.oraclecloud.osmh.collectmetadata |
| Lookup Data - Append | com.oraclecloud.logginganalytics.appendlookupdata |
| Protected Database - Update End | com.oraclecloud.autonomousrecoveryservice.updateprotecteddatabase.end |
| Event - Create Set Management Station Unhealthy State Event | com.oraclecloud.osmh.createevent.managementstation.setmanagementstationhealthstate.unhealthy |
| Web Application Acceleration - Update Begin | com.oraclecloud.waa.updatewebappacceleration.begin |
| DeployArtifact - Delete Begin | com.oraclecloud.devopsdeploy.deletedeployartifact.begin |
| AccessPolicy - Create End | com.oraclecloud.servicemesh.createaccesspolicy.end |
| Route Table - Update | com.oraclecloud.virtualnetwork.updateroutetable |
| Security Policy Deployment Cleanup | com.oraclecloud.datasafe.cleanupsecuritypolicydeployment |
| VMware Solution - Cancel Downgrade HCX Begin | com.oraclecloud.vmwaresolution.canceldowngradehcx.begin |
| Migration Create Begin | com.oraclecloud.odms.createmigration.begin |
| MySQL - Add HeatWave Cluster Begin | com.oraclecloud.mysqlaas.addheatwavecluster.begin |
| MySQL - Add HeatWave Cluster End | com.oraclecloud.mysqlaas.addheatwavecluster.end |
| DRG - Update | com.oraclecloud.virtualnetwork.updatedrg |
| Instance Configuration - Delete | com.oraclecloud.computemanagement.deleteinstanceconfiguration |
| BDS Api Key Instance - Delete Api Key Begin | com.oraclecloud.bds.cp.deletebdsapikey.begin |
| BundleAutoUpdate | com.oraclecloud.analyticswarehouse.data.bundles |
| GGS Pipeline - Update Pipeline Begin | com.oraclecloud.goldengate.updatepipeline.begin |
| Batch Context - Update Begin | com.oraclecloud.batch.updatebatchcontext.begin |
| Oce Instance - Update Begin | com.oraclecloud.oce.updateoceinstance.begin |
| HostScanRecipe - Create | com.oraclecloud.vulnerabilityscanning.createhostscanrecipe |
| Event - Delete | com.oraclecloud.osmh.deleteevent |
| VCN - Create | com.oraclecloud.virtualnetwork.createvcn |
| Instance - Delete End | com.oraclecloud.apiplatform.deleteapiplatforminstance.end |
| Event - Create Agent List Packages Event | com.oraclecloud.osmh.createevent.agent.listpackages |
| Cluster Network - Create Begin | com.oraclecloud.computemanagement.createclusternetwork.begin |
| Table - Change Compartment End | com.oraclecloud.nosql.changecompartment.end |
| Bucket - Create | com.oraclecloud.objectstorage.createbucket |
| NodePool - Update End | com.oraclecloud.clustersapi.updatenodepool.end |
| BDS Instance - Replace Node End | com.oraclecloud.bds.cp.replacenode.end |
| Change Boot Volume Backup Compartment | com.oraclecloud.blockvolumes.changebootvolumebackupcompartment |
| Autonomous Cloud VM Cluster - Update End | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.update.end |
| Instance - Update Instance | com.oraclecloud.analytics.updateanalyticsinstance |
| Database - Rotate Database Key Begin | com.oraclecloud.databaseservice.rotatedatabasekey.begin |
| Expired - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.expireddelegatedresourceaccessrequest |
| Fusion Environment Family - Create Begin | com.oraclecloud.fusionapps.createfusionenvironmentfamily.begin |
| Management Agent - Deletion Pending | com.oraclecloud.managementagent.upcomingagentdeletion |
| Sensitive Data Model Update - Begin | com.oraclecloud.datasafe.updatesensitivedatamodel.begin |
| Database Security Config Create - Begin | com.oraclecloud.datasafe.createdatabasesecurityconfig.begin |
| Masking Policy Update - Begin | com.oraclecloud.datasafe.updatemaskingpolicy.begin |
| Batch Task Profile - Delete | com.oraclecloud.batch.deletebatchtaskprofile |
| Autonomous Database - Create Begin | com.oraclecloud.databaseservice.autonomous.database.instance.create.begin |
| Create Boot Volume Backup End | com.oraclecloud.blockvolumes.createbootvolumebackup.end |
| Stop Workspace - End | com.oraclecloud.dataintegration.stopdisworkspace.end |
| Data Lake - Delete Begin | com.oraclecloud.datalake.deletedatalake.begin |
| Update Boot Volume End | com.oraclecloud.blockvolumes.updatebootvolume.end |
| Stream Cell Deployment - Create | com.oraclecloud.mediaservices.createstreamcelldeployment |
| Pluggable database - Disable Database Management Service End | com.oraclecloud.databaseservice.disablepdbmanagement.end |
| Migration Start End | com.oraclecloud.odms.startmigration.end |
| Resource Analytics Instance - Create Begin | com.oraclecloud.resourceanalytics.createresourceanalyticsinstance.begin |
| Security Policy Cleanup | com.oraclecloud.datasafe.cleanupsecuritypolicy |
| Language - Delete Model Endpoint End | com.oraclecloud.aiservicelanguage.deletemodelendpoint.end |
| Autoscaling Configuration - Scaling Action | com.oraclecloud.autoscaling.scalingaction |
| Autonomous Container Database - Create Begin | com.oraclecloud.databaseservice.autonomous.container.database.instance.create.begin |
| Distributed Autonomous Database - Patch Begin | com.oraclecloud.globaldb.patchdistributedautonomousdatabase.begin |
| Ping Monitor - Create | com.oraclecloud.healthchecks.createpingmonitor |
| Boot Volume - Attach Begin | com.oraclecloud.computeapi.attachbootvolume.begin |
| Auto Association - Enable | com.oraclecloud.logginganalytics.enableautoassociation |
| Db Node Snapshot - Unmount end | com.oraclecloud.databaseservice.unmountdbnodesnapshot.end |
| Instance Pool - Attach Load Balancer End | com.oraclecloud.computemanagement.attachloadbalancer.end |
| Software Source - Change Compartment | com.oraclecloud.osms.changesoftwaresourcecompartment |
| Batch Job Pool - Update Begin | com.oraclecloud.batch.updatebatchjobpool.begin |
| External Pluggable Database - Disable Stack Monitoring Service End | com.oraclecloud.databaseservice.disablestackmonitoringforexternalpluggabledatabase.end |
| BDS Instance - Get Resource Principal Configuration | com.oraclecloud.bds.cp.getresourceprincipalconfiguration |
| Bastion - Update Bastion End | com.oraclecloud.bastion.updatebastion.end |
| Imaging - Create End | com.oraclecloud.computeapi.createimage.end |
| Object Storage Link - Delete End | com.oraclecloud.lustrefilestorage.deleteobjectstoragelink.end |
| API - Delete Begin | com.oraclecloud.apigateway.deleteapi.begin |
| BDS Lake Configuration Instance - Test Lake Configuration End | com.oraclecloud.bds.cp.testbdslakeconfiguration.end |
| Change Protection Mode End | com.oraclecloud.databaseservice.changeprotectionmode.end |
| Delete Volume Backup End | com.oraclecloud.blockvolumes.deletevolumebackup.end |
| Global Database Private Endpoint - Change Compartment End | com.oraclecloud.globaldb.changeprivateendpointcompartment.end |
| Web Application Acceleration - Delete End | com.oraclecloud.waa.deletewebappacceleration.end |
| VMware Solution - Update Cluster | com.oraclecloud.vmwaresolution.updatecluster |
| Audit Profile Delete - Begin | com.oraclecloud.datasafe.deleteauditprofile.begin |
| Autonomous VM Cluster - Terminate End | com.oraclecloud.databaseservice.deleteautonomousvmcluster.end |
| OSN - Update OSN End | com.oraclecloud.blockchain.updateosn.end |
| Data Guard Reinstate - Begin | com.oraclecloud.databaseservice.dataguardreinstate.begin |
| Object Storage Link - Delete Begin | com.oraclecloud.lustrefilestorage.deleteobjectstoragelink.begin |
| Delete Volume Kms Key Begin | com.oraclecloud.blockvolumes.deletevolumekmskey.begin |
| DB System - Information | com.oraclecloud.databaseservice.dbsystem.information |
| Web Application Firewall - Create End | com.oraclecloud.waf.createwebappfirewall.end |
| Backup - Create Begin | com.oraclecloud.postgresql.createbackup.begin |
| Source - Delete End | com.oraclecloud.applicationmigration.deletesource.end |
| BDS Instance - Configure Cloud SQL Begin | com.oraclecloud.bds.cp.addcloudsql.begin |
| Cluster - Create End | com.oraclecloud.clustersapi.createcluster.end |
| DRG - Create | com.oraclecloud.virtualnetwork.createdrg |
| Execute Task - End | com.oraclecloud.dataintegration.createtaskrun.end |
| HostScanRecipe - ChangeCompartment | com.oraclecloud.vulnerabilityscanning.changehostscanrecipecompartment |
| Object Storage Link Sync Job - Start Import Job | com.oraclecloud.lustrefilestorage.startimportfromobject |
| Autonomous Container Database - Create Backup Begin | com.oraclecloud.databaseservice.autonomous.container.database.backup.begin |
| Instance - Change Compartment | com.oraclecloud.blockchain.changeplatformcompartment |
| Delete Boot Volume Begin | com.oraclecloud.blockvolumes.deletebootvolume.begin |
| Bastion - Delete Bastion Begin | com.oraclecloud.bastion.deletebastion.begin |
| Instance - Change Compartment Begin | com.oraclecloud.computeapi.changeinstancecompartment.begin |
| Container Instance - Change Compartment Begin | com.oraclecloud.containerinstances.changecontainerinstancecompartment.begin |
| Table - Create End | com.oraclecloud.nosql.createtable.end |
| VLAN - Delete | com.oraclecloud.virtualnetwork.deletevlan |
| Db Node Snapshot - Unmount Begin | com.oraclecloud.databaseservice.unmountdbnodesnapshot.begin |
| Job State Failed | com.oraclecloud.odms.jobstatefailed |
| DB Home - Patch End | com.oraclecloud.databaseservice.patchdbhome.end |
| Instance - Delete Begin | com.oraclecloud.apiplatform.deleteapiplatforminstance.begin |
| Object Collection Rule - Create | com.oraclecloud.logginganalytics.createloganalyticsobjectcollectionrule |
| BDS Instance - Create Resource Principal Configuration Begin | com.oraclecloud.bds.cp.createresourceprincipalconfiguration.begin |
| Waf Policy - Change Compartment End | com.oraclecloud.waf.changewebappfirewallpolicycompartment.end |
| Managed Instance - Install Package Update | com.oraclecloud.osms.installpackageupdateonmanagedinstance |
| Subscription Pricing Config - Create | com.oraclecloud.subscriptionpricingservice.createsubscriptionpricingconfig |
| MySQL - Reset Channel End | com.oraclecloud.mysqlaas.resetchannel.end |
| Private Service Access - Create Begin | com.oraclecloud.privateserviceaccess.createprivateserviceaccess.begin |
| WebLogic Domain - Create Agreement Record | com.oraclecloud.weblogicmanagement.createagreementrecord |
| Lustre File System - Update Begin | com.oraclecloud.lustrefilestorage.updatelustrefilesystem.begin |
| DHCP Options - Update | com.oraclecloud.virtualnetwork.updatedhcpoptions |
| Cache Database - Configure Begin | com.oraclecloud.zerolatency.configurezerolatencydatabase.begin |
| Dynamic Group - Delete | com.oraclecloud.identitycontrolplane.deletedynamicgroup |
| Work Request - Update All Packages Begin | com.oraclecloud.osmh.updateallpackages.begin |
| Data Store - Delete End | com.oraclecloud.dataexchange.deletedatastore.end |
| Container Instance - Create Container Instance Begin | com.oraclecloud.containerinstances.createcontainerinstance.begin |
| DeployPipeline - Delete Begin | com.oraclecloud.devopsdeploy.deletedeploypipeline.begin |
| HostScanRecipes - Update | com.oraclecloud.vulnerabilityscanning.updatehostscanrecipe.end |
| VirtualServiceRouteTable - Delete End | com.oraclecloud.servicemesh.deletevirtualserviceroutetable.end |
| VirtualService - Change Compartment Begin | com.oraclecloud.servicemesh.changevirtualservicecompartment.begin |
| Database Security Config Cleanup | com.oraclecloud.datasafe.cleanupdatabasesecurityconfig |
| Update Protection Rules End | com.oraclecloud.waf.updateprotectionrules.end |
| Security Policy Deployment Auto Create | com.oraclecloud.datasafe.autocreatesecuritypolicydeployment |
| User - Activate | com.oraclecloud.identitycontrolplane.activateuser |
| Cache Database - Start Cache Agent Begin | com.oraclecloud.zerolatency.startcacheagent.begin |
| Application - Change Compartment | com.oraclecloud.functions.changeapplicationcompartment |
| Distributed Database Private Endpoint - Create End | com.oraclecloud.globaldb.createdistributeddatabaseprivateendpoint.end |
| OSN - Delete OSN End | com.oraclecloud.blockchain.deleteosn.end |
| Instance - Start Instance Begin | com.oraclecloud.analytics.startanalyticsinstance.begin |
| Database - Disable DbManagement End | com.oraclecloud.databaseservice.disabledbmanagement.end |
| BDS Instance - Create Replace Configuration Begin | com.oraclecloud.bds.cp.createreplaceconfig.begin |
| Operator Control - Update | com.oraclecloud.operatorcontrol.updateoperatorcontrol |
| Backup - Create End | com.oraclecloud.postgresql.createbackup.end |
| Batch Job - Lifecycle State Change | com.oraclecloud.batch.updatebatchjobstate |
| Update NetworkFirewall End | com.oraclecloud.networkfirewallservice.updatenetworkfirewall.end |
| HostAgentScanResult - Delete | com.oraclecloud.vulnerabilityscanning.deletehostagentscanresult |
| API - Change Compartment Begin | com.oraclecloud.apigateway.changeapicompartment.begin |
| Register Target Database - Begin | com.oraclecloud.datasafe.registerdatasafetarget.begin |
| Oracle managed software update staging failed | com.oraclecloud.databaseservice.oraclemanageddbhomestagefailed |
| DeployStage - Create End | com.oraclecloud.devopsdeploy.createdeploystage.end |
| SQL Firewall Collection Insights Refresh - End | com.oraclecloud.datasafe.refreshsqlcollectionloginsights.end |
| Container Instance - Start Container Instance End | com.oraclecloud.containerinstances.startcontainerinstance.end |
| Exascale Database Storage Vault - Autoscale | com.oraclecloud.databaseservice.autoscaleexascaledbstoragevault |
| Container Instance - Update Container Instance End | com.oraclecloud.containerinstances.updatecontainerinstance.end |
| Private IP - Update | com.oraclecloud.virtualnetwork.updateprivateip |
| Exadata Infrastructure - Delete Begin | com.oraclecloud.databaseservice.deleteexadatainfrastructure.begin |
| Create Snapshot | com.oraclecloud.filestorage.createsnapshot |
| Stack - Create | com.oraclecloud.oracleresourcemanager.createstack |
| Access Request - Expired | com.oraclecloud.operatorcontrol.expiredaccessrequest |
| Customer Secret Key - Delete | com.oraclecloud.identitycontrolplane.deletecustomersecretkey |
| External MySQL DB System - Deregister Begin | com.oraclecloud.databasemanagement.externalmysqlresource.dbsystem.deregister.begin |
| ContainerScanResult - ChangeCompartment | com.oraclecloud.vulnerabilityscanning.changecontaineragentscanresultcompartment |
| AccessPolicy - Change Compartment End | com.oraclecloud.servicemesh.changeaccesspolicycompartment.end |
| Create Inventory End | com.oraclecloud.cloudbridge.createinventory.end |
| Instance - Action End | com.oraclecloud.computeapi.instanceaction.end |
| BDS Instance - Autoscale - No Action | com.oraclecloud.bds.autoscale.cp.autoscalenoaction |
| Delete Global Accelerator Ruleset Begin | com.oraclecloud.gax.public.api.deleteruleset.begin |
| Database - Update End | com.oraclecloud.postgresql.updatedbsystem.end |
| Model Deployment - Update End | com.oraclecloud.datascience.updatemodeldeployment.end |
| Work Request - Enable Module Streams Begin | com.oraclecloud.osmh.enablemodulestreams.begin |
| Tenancy Attachment - Create Begin | com.oraclecloud.resourceanalytics.createtenancyattachment.begin |
| Update Protection Rules Begin | com.oraclecloud.waf.updateprotectionrules.begin |
| DB System - Upgrade Begin | com.oraclecloud.databaseservice.upgradedbsystem.begin |
| MySQL - Start HeatWave Cluster Begin | com.oraclecloud.mysqlaas.startheatwavecluster.begin |
| Delete Private Endpoint - Begin | com.oraclecloud.datasafe.deletedatasafeprivateendpoint.begin |
| Change Address List Compartment | com.oraclecloud.waf.changeaddresslistcompartment |
| GGS Deployment - Upgrade Available | com.oraclecloud.goldengate.upgradenewversion |
| Application Data Platform - PodDb Patch End | com.oraclecloud.applicationdataplatform.createpoddbpatch.end |
| Update Stack - Begin | com.oraclecloud.dataintelligencefoundation.updatestack.begin |
| Create Global Accelerator Ruleset Begin | com.oraclecloud.gax.public.api.createruleset.begin |
| BuildRun - Delete | com.oraclecloud.devopsbuild.deletebuildrun |
| Update Waas Policy Custom Protection Rules Begin | com.oraclecloud.waf.updatewaaspolicycustomprotectionrules.begin |
| Visual Builder Studio - Update Instance - begin | com.oraclecloud.vbstudioinst.updatevbsinstance.begin |
| Security Policy Configuration Create - End | com.oraclecloud.datasafe.createsecuritypolicyconfig.end |
| Object Collection Rule - Move Compartment | com.oraclecloud.logginganalytics.changeloganalyticsobjectcollectionrulecompartment |
| Key - Disable Begin | com.oraclecloud.keymanagementservice.disablekey.begin |
| Subscription - Resend Confirmation | com.oraclecloud.notification.resendsubscriptionconfirmation |
| Fusion Environment - Delete End | com.oraclecloud.fusionapps.deletefusionenvironment.end |
| Stream Distribution Channel - Delete | com.oraclecloud.mediaservices.deletestreamdistributionchannel |
| Integration Instance - Start End | com.oraclecloud.integration.startintegrationinstance.end |
| BDS Instance - Create Begin | com.oraclecloud.bds.cp.createinstance.begin |
| Device - Update | com.oraclecloud.datatransferservice.updatetransferdevice |
| Entity - Create | com.oraclecloud.logginganalytics.createentity |
| Trigger - Delete Begin | com.oraclecloud.devopsbuild.deletetrigger.begin |
| Event - Create Update Enhancement Event | com.oraclecloud.osmh.createevent.softwareupdate.updateenhancement |
| Copy Boot Volume Backup Begin | com.oraclecloud.blockvolumes.copybootvolumebackup.begin |
| Security Policy Deployment Create - End | com.oraclecloud.datasafe.createsecuritypolicydeployment.end |
| Delete File System | com.oraclecloud.filestorage.deletefilesystem |
| Stack - Update | com.oraclecloud.oracleresourcemanager.updatestack |
| Operator - Logout | com.oraclecloud.operatorcontrol.operatorlogout |
| Batch Task Environment - Change Compartment Begin | com.oraclecloud.batch.changebatchtaskenvironmentcompartment.begin |
| BDS Instance - Add Worker Node Begin | com.oraclecloud.bds.cp.addnode.begin |
| Detected - Sighting | com.oraclecloud.cloudguard.sightingdetected |
| VM Cluster Network - Validate End | com.oraclecloud.databaseservice.validatevmclusternetwork.end |
| Deploy Artifacts - End | com.oraclecloud.dataintelligencefoundation.deployartifacts.end |
| Create Pull Request - End | com.oraclecloud.devopscoderepo.createpullrequest.end |
| Create Pull Request Comment - End | com.oraclecloud.devopscoderepo.createpullrequestcomment.end |
| Decline Pull Request - End | com.oraclecloud.devopscoderepo.declinepullrequest.end |
| Merge Pull Request - End | com.oraclecloud.devopscoderepo.mergepullrequest.end |
| Patch Pull Request - End | com.oraclecloud.devopscoderepo.patchpullrequest.end |
| Reopen Pull Request - End | com.oraclecloud.devopscoderepo.reopenpullrequest.end |
| Review Pull Request - End | com.oraclecloud.devopscoderepo.reviewpullrequest.end |
| Update Project Repository Settings - End | com.oraclecloud.devopscoderepo.updateprojectrepositorysettings.end |
| Update Repository Settings - End | com.oraclecloud.devopscoderepo.updaterepositorysettings.end |
| Create Private Endpoint - Begin | com.oraclecloud.datasafe.createdatasafeprivateendpoint.begin |
| Table - Drop Begin | com.oraclecloud.nosql.droptable.begin |
| Anomaly Detection - Model training end | com.oraclecloud.aiservice.trainmodel.end |
| Oracle managed database software update enabled | com.oraclecloud.databaseservice.managedsoftwareupdateenabled |
| Batch Context - Change Compartment End | com.oraclecloud.batch.changebatchcontextcompartment.end |
| Table - Add Replica Begin | com.oraclecloud.nosql.addreplica.begin |
| Report Schedule Delete - Begin | com.oraclecloud.datasafe.removeschedulereport.begin |
| FsuAction - Create Begin | com.oraclecloud.fsu.createfsuaction.begin |
| Event - Create Report | com.oraclecloud.osmh.event.createreport |
| Security Policy Report Update - Begin | com.oraclecloud.datasafe.refreshsecuritypolicyreport.begin |
| Cluster - Delete Begin | com.oraclecloud.clustersapi.deletecluster.begin |
| Delete Waas Policy Begin | com.oraclecloud.waf.deletewaaspolicy.begin |
| Index - Create End | com.oraclecloud.nosql.createindex.end |
| Reject Delegated Resource Access Request - Begin | com.oraclecloud.delegateaccesscontrol.rejectdelegatedresourceaccessrequest.begin |
| Managed Instance - Switch Snap Channel | com.oraclecloud.osmh.switchsnapchannel |
| Managed Instance - Attach Child Software Source | com.oraclecloud.osms.attachchildsoftwaresourcetomanagedinstance |
| Pipeline Run - Failed | com.oraclecloud.datascience.failedpipelinerun |
| Operator Login - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.serviceprovideroperatorlogin |
| Distributed Autonomous Database - Configure GSMs Begin | com.oraclecloud.globaldb.configuredistributedautonomousdatabasegsms.begin |
| Security Policy Deployment Delete - End | com.oraclecloud.datasafe.deletesecuritypolicydeployment.end |
| DB System - Critical | com.oraclecloud.databaseservice.dbsystem.critical |
| BDS Instance - Configure Renew ODH Service Certificate End | com.oraclecloud.bds.cp.renewodhservicecertificate.end |
| BDS Metastore Configuration Instance - Delete Metastore Configuration | com.oraclecloud.bds.cp.deletebdsmetastoreconfiguration |
| Work Request - List Packages End | com.oraclecloud.osmh.listpackages.end |
| Subscription - Move | com.oraclecloud.notification.movesubscription |
| Management Agent - Upgraded | com.oraclecloud.managementagent.agentupgraded |
| Application - Update End | com.oraclecloud.ohaaas.updateapplication.end |
| OMA - Create Approval Template | com.oraclecloud.lockbox.createapprovaltemplate |
| IngressGateway - Delete End | com.oraclecloud.servicemesh.deleteingressgateway.end |
| Distributed Database - Upload Signed Certificate And Generate Wallet Begin | com.oraclecloud.globaldb.uploaddistributeddatabasesignedcertificateandgeneratewallet.begin |
| Revoke Delegated Resource Access Request - End | com.oraclecloud.delegateaccesscontrol.revokedelegatedresourceaccessrequest.end |
| Distributed Database - Delete End | com.oraclecloud.globaldb.deletedistributeddatabase.end |
| Update Alert Policy Rule - End | com.oraclecloud.datasafe.updatealertpolicyrule.end |
| Web Application Acceleration - Delete Begin | com.oraclecloud.waa.deletewebappacceleration.begin |
| Update NetworkFirewallPolicy | com.oraclecloud.networkfirewallservice.updatenetworkfirewallpolicy |
| GGS Pipeline - Create Pipeline Begin | com.oraclecloud.goldengate.createpipeline.begin |
| Resource Schedule - Update End | com.oraclecloud.resourcescheduler.updateschedule.end |
| Stream Cdn Config - Create | com.oraclecloud.mediaservices.createstreamcdnconfig |
| Update Volume Group | com.oraclecloud.blockvolumes.updatevolumegroup |
| Work Request - Disable Module Streams End | com.oraclecloud.osmh.disablemodulestreams.end |
| Batch Job - Change Compartment Begin | com.oraclecloud.batch.changebatchjobcompartment.begin |
| HostAgentScanResult - Export | com.oraclecloud.vulnerabilityscanning.exporthostagentscanresultcsv |
| DHCP Options - Create | com.oraclecloud.virtualnetwork.createdhcpoptions |
| Policy - Delete | com.oraclecloud.identitycontrolplane.deletepolicy |
| Instance - Launch Begin | com.oraclecloud.computeapi.launchinstance.begin |
| Compute Host - State Change | com.oraclecloud.computeapi.statechangecomputehosts |
| Compute Host - Create | com.oraclecloud.computeapi.createcomputehosts |
| Compute Host - Terminate | com.oraclecloud.computeapi.deletecomputehosts |
| MeshIngressGatewayRouteTable - Update Begin | com.oraclecloud.servicemesh.updateingressgatewayroutetable.begin |
| Create Workspace - Begin | com.oraclecloud.dataintegration.createworkspace.begin |
| API - Delete end | com.oraclecloud.apigateway.deleteapi.end |
| Autonomous Container Database - Warning | com.oraclecloud.databaseservice.autonomous.container.database.warning |
| Managed Database - Information | com.oraclecloud.databasemanagement.manageddatabase.information |
| Database Tools Private Endpoint - Delete End | com.oraclecloud.dbtoolsserviceapi.deletedatabasetoolsprivateendpoint.end |
| MFA TOTP Device - Generate Seed | com.oraclecloud.identitycontrolplane.generatetotpseed |
| Masking Library Format Create - Begin | com.oraclecloud.datasafe.createlibrarymaskingformat.begin |
| WebLogic Domain - Scan Begin | com.oraclecloud.weblogicmanagement.scanwlsdomain.begin |
| BDS Instance - Configure Disable ODH Service Certificate End | com.oraclecloud.bds.cp.disableodhservicecertificate.end |
| Create Private Endpoint - End | com.oraclecloud.datasafe.createdatasafeprivateendpoint.end |
| Policy - Update | com.oraclecloud.identitycontrolplane.updatepolicy |
| Work Request - Update Packages Begin | com.oraclecloud.osmh.updatepackages.begin |
| Global Autonomous Database - Change Compartment Begin | com.oraclecloud.globaldb.changeshardeddatabasecompartment.begin |
| External MySQL DB System - Update | com.oraclecloud.databasemanagement.externalmysqlresource.dbsystem.update |
| MySQL - Automatic Recovery End | com.oraclecloud.mysqlaas.automaticrecovery.end |
| MySQL - Create DB System End | com.oraclecloud.mysqlaas.createdbsystem.end |
| DR Plan Execution - CreateStartDrill Begin | com.oraclecloud.disasterrecovery.createstartdrilldrplanexecution |
| Application Data Platform - PodDb Restore Point Flashback Begin | com.oraclecloud.applicationdataplatform.flashbackpoddbrestorepoint.begin |
| Event - Create Set Management Station Config Event | com.oraclecloud.osmh.createevent.managementstation.setmanagementstationconfig |
| Fusion Environment - Terminate End | com.oraclecloud.fusionapps.terminatefusionenvironment.end |
| Global Autonomous Database - Start Begin | com.oraclecloud.globaldb.startshardeddatabase.begin |
| Work Request - Create Software Source Begin | com.oraclecloud.osmh.createsoftwaresource.begin |
| BDS Instance - Autoscale - Error | com.oraclecloud.bds.autoscale.cp.autoscaleerror |
| Package - Delete | com.oraclecloud.datatransferservice.deletetransferpackage |
| Update Alert Policy - End | com.oraclecloud.datasafe.updatealertpolicy.end |
| Event - Create Enable Module Streams Event | com.oraclecloud.osmh.createevent.softwaresource.enablemodulestreams |
| AI Data Platform - Update End | com.oraclecloud.aidataplatform.updateaidataplatform.end |
| PathAnalyzerTest - Update | com.oraclecloud.vnconfigadvisor.updatepathanalyzertest |
| Update Boot Volume Backup | com.oraclecloud.blockvolumes.updatebootvolumebackup |
| Autonomous VM Cluster - Update End | com.oraclecloud.databaseservice.updateautonomousvmcluster.end |
| Database Tools Connection - Delete Begin | com.oraclecloud.dbtoolsserviceapi.deletedatabasetoolsconnection.begin |
| Mesh - Update Begin | com.oraclecloud.servicemesh.updatemesh.begin |
| Assign Operator Control - Update | com.oraclecloud.operatorcontrol.updateoperatorcontrolassignment |
| Namespace - Offboard | com.oraclecloud.logginganalytics.offboardnamespace |
| BuildPipeline - Update End | com.oraclecloud.devopsbuild.updatebuildpipeline.end |
| Update Global Accelerator Begin | com.oraclecloud.gax.public.api.updateglobalaccelerator.begin |
| Database Tools Connection - Change Compartment Begin | com.oraclecloud.dbtoolsserviceapi.changedatabasetoolsconnectioncompartment.begin |
| Instance - Update Instance End | com.oraclecloud.blockchain.updateplatforminstance.end |
| Network Address List - Create Begin | com.oraclecloud.waf.createnetworkaddresslist.begin |
| Audit Archive Retrieval Delete - End | com.oraclecloud.datasafe.deleteauditarchiveretrieval.end |
| Audit Profile Update - Begin | com.oraclecloud.datasafe.updateauditprofile.begin |
| Distributed Autonomous Database - Validate Network End | com.oraclecloud.globaldb.validatedistributedautonomousdatabasenetwork.end |
| Rotate Pluggable Database Key - End | com.oraclecloud.databaseservice.rotatepluggabledatabasekey.end |
| BDS Instance - Configure Renew ODH Service Certificate Begin | com.oraclecloud.bds.cp.renewodhservicecertificate.begin |
| Lustre File System - Update End | com.oraclecloud.lustrefilestorage.updatelustrefilesystem.end |
| Language - Delete Model | com.oraclecloud.aiservicelanguage.deletemodel |
| Schedule Cascade Delete Project - begin | com.oraclecloud.devopsproject.schedulecascadingprojectdeletion.begin |
| Database - Create End | com.oraclecloud.databaseservice.createdatabase.end |
| Application Data Platform - PodDb Create from Backup Begin | com.oraclecloud.applicationdataplatform.poddbcreatefrombackup.begin |
| Audit Trail Stop - End | com.oraclecloud.datasafe.stopaudittrail.end |
| BuildPipeline - Delete End | com.oraclecloud.devopsbuild.deletebuildpipeline.end |
| Operator Control - Create | com.oraclecloud.operatorcontrol.createoperatorcontrol |
| Cache Database - Configure End | com.oraclecloud.zerolatency.configurezerolatencydatabase.end |
| Oracle managed database software update rescheduled | com.oraclecloud.databaseservice.managedsoftwareupdaterescheduled |
| Fleet - Create End | com.oraclecloud.javamanagementservice.createfleet.end |
| Instance - Terminate End | com.oraclecloud.computeapi.terminateinstance.end |
| Database - Create Begin | com.oraclecloud.postgresql.createdbsystem.begin |
| Trigger - Update Begin | com.oraclecloud.devopsbuild.updatetrigger.begin |
| WebLogic Domain - Create | com.oraclecloud.weblogicmanagement.createwlsdomain |
| Oce Instance - Change Compartment End | com.oraclecloud.oce.changeoceinstancecompartment.end |
| Mesh - Create Begin | com.oraclecloud.servicemesh.createmesh.begin |
| BDS Lake Configuration Instance - Delete Lake Configuration End | com.oraclecloud.bds.cp.deletebdslakeconfiguration.end |
| Media Workflow Configuration - Move Compartment | com.oraclecloud.mediaservices.changemediaworkflowconfigurationcompartment |
| VirtualDeployment - Update End | com.oraclecloud.servicemesh.updatevirtualdeployment.end |
| DR Plan Execution - CreateSwitchover End | com.oraclecloud.disasterrecovery.createswitchoverdrplanexecution.end |
| Database Tools Connection - Delete End | com.oraclecloud.dbtoolsserviceapi.deletedatabasetoolsconnection.end |
| Container Instance - Update Container Begin | com.oraclecloud.containerinstances.updatecontainer.begin |
| Db Node Snapshot - Delete Begin | com.oraclecloud.databaseservice.deletedbnodesnapshot.begin |
| Database - Restore End | com.oraclecloud.databaseservice.restoredatabase.end |
| KeyVersion - Cancel Deletion End | com.oraclecloud.keymanagementservice.cancelkeyversiondeletion.end |
| Resource Analytics Instance - Update End | com.oraclecloud.resourceanalytics.updateresourceanalyticsinstance.end |
| Vault - Cancel Deletion End | com.oraclecloud.keymanagementservice.cancelvaultdeletion.end |
| Container Instance - Update Container Instance Begin | com.oraclecloud.containerinstances.updatecontainerinstance.begin |
| Work Request - Update Ksplice Userspace End | com.oraclecloud.osmh.updatekspliceuserspace.end |
| Service Instance - Start End | com.oraclecloud.zerolatency.startzerolatency.end |
| Task Order - Add to portfolio | com.oraclecloud.atat.addtaskorder |
| Create Volume Group Backup End | com.oraclecloud.blockvolumes.createvolumegroupbackup.end |
| Migration Update Begin | com.oraclecloud.odms.updatemigration.begin |
| Exadata Infrastructure - Granular Maintenance Execution Window Canceled | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecancelexecutionwindow |
| Swift Password - Update | com.oraclecloud.identitycontrolplane.updateswiftpassword |
| Unified Audit Policy Bulk Create - End | com.oraclecloud.datasafe.bulkcreateunifiedauditpolicy.end |
| FsuDiscovery - Delete Begin | com.oraclecloud.fsu.deletefsudiscovery.begin |
| Pluggable Database - Convert to Regular End | com.oraclecloud.databaseservice.pluggabledatabase.converttoregular.end |
| Database - Automatic Backup Begin | com.oraclecloud.databaseservice.automaticbackupdatabase.begin |
| Media Workflow Configuration - Create | com.oraclecloud.mediaservices.createmediaworkflowconfiguration |
| Protected Database - Change Compartment End | com.oraclecloud.autonomousrecoveryservice.changeprotecteddatabasecompartment.end |
| Recovery Service Subnet - Update End | com.oraclecloud.autonomousrecoveryservice.updaterecoveryservicesubnet.end |
| FsuCollection - Create End | com.oraclecloud.fsu.createcollection.end |
| BDS Lake Configuration Instance - Create Lake Configuration End | com.oraclecloud.bds.cp.createbdslakeconfiguration.end |
| VirtualServiceRouteTable - Change Compartment Begin | com.oraclecloud.servicemesh.changevirtualserviceroutetablecompartment.begin |
| Work Request - Update Vulnerability End | com.oraclecloud.osmh.updatevulnerability.end |
| Delete Volume Backup Begin | com.oraclecloud.blockvolumes.deletevolumebackup.begin |
| Stream Cdn Config - Update | com.oraclecloud.mediaservices.updatestreamcdnconfig |
| BDS Instance - Create Nodes Backups Begin | com.oraclecloud.bds.cp.backupnodes.begin |
| Move Workspace - Begin | com.oraclecloud.dataintegration.moveworkspace.begin |
| Unified Audit Policy Update - Begin | com.oraclecloud.datasafe.updateunifiedauditpolicy.begin |
| Service Gateway - Create | com.oraclecloud.servicegateway.createservicegateway |
| OAuth Client Credential - Delete | com.oraclecloud.identitycontrolplane.deleteoauthclientcredential |
| DB Node - Reboot Migration Maintenance Completed | com.oraclecloud.databaseservice.dbnoderebootmigrationmaintenancecompleted |
| Alert Policy Target Association Patch - Begin | com.oraclecloud.datasafe.patchtargetalertpolicyassociation.begin |
| Object Collection Rule - Update | com.oraclecloud.logginganalytics.updateloganalyticsobjectcollectionrule |
| Local Peering Gateway - Delete End | com.oraclecloud.virtualnetwork.deletelocalpeeringgateway.end |
| Work Request - Set Management Station Config End | com.oraclecloud.osmh.setmanagementstationconfig.end |
| Autonomous Container Database - Maintenance Begin | com.oraclecloud.databaseservice.autonomous.container.database.maintenance.begin |
| Distributed Database - Fetch VM Clusters | com.oraclecloud.globaldb.fetchdistributeddatabasevmclusters |
| Instance Configuration - Launch End | com.oraclecloud.computemanagement.launchinstanceconfiguration.end |
| Upload - Delete | com.oraclecloud.logginganalytics.deleteupload |
| Event - Kernel Oops | com.oraclecloud.osmh.event.kerneloops |
| HTTP Monitor - Update | com.oraclecloud.healthchecks.updatehttpmonitor |
| DRG Attachment - Update | com.oraclecloud.virtualnetwork.updatedrgattachment |
| MySQL - Restart HeatWave Cluster End | com.oraclecloud.mysqlaas.restartheatwavecluster.end |
| Stream Packaging Config - Update | com.oraclecloud.mediaservices.updatestreampackagingconfig |
| Batch Task Environment - Delete | com.oraclecloud.batch.deletebatchtaskenvironment |
| Subscription - Update | com.oraclecloud.notification.updatesubscription |
| Trigger - Update End | com.oraclecloud.devopsbuild.updatetrigger.end |
| Project - Delete End | com.oraclecloud.datascience.deleteproject.end |
| Connection - Delete Begin | com.oraclecloud.devopsbuild.deleteconnection.begin |
| Instance Pool - Change Compartment | com.oraclecloud.computemanagement.changeinstancepoolcompartment |
| ODA Instance - Update Customer Encryption Key End | com.oraclecloud.digitalassistant.updatecustomerencryptionkey.end |
| Create Http Redirect Begin | com.oraclecloud.waf.createhttpredirect.begin |
| Work Request - Cancel | com.oraclecloud.ohaaas.cancelworkrequest |
| Security Assessment Finding Risk Update - Begin | com.oraclecloud.datasafe.updatefinding.begin |
| Stream Cell Deployment - Update | com.oraclecloud.mediaservices.updatestreamcelldeployment |
| Create NetworkFirewallPolicy | com.oraclecloud.networkfirewallservice.createnetworkfirewallpolicy |
| Service Gateway - Delete Begin | com.oraclecloud.servicegateway.deleteservicegateway.begin |
| Work Request - Remove Module Profiles Begin | com.oraclecloud.osmh.removemoduleprofiles.begin |
| Batch Task Profile - Change Compartment End | com.oraclecloud.batch.changebatchtaskprofilecompartment.end |
| Delete On-Prem Connector - End | com.oraclecloud.datasafe.deleteonpremconnector.end |
| WebLogic Domain - Uninstall Latest Patches End | com.oraclecloud.weblogicmanagement.uninstalllatestpatchesfromwlsdomain.end |
| ODA Instance - Update Customer Encryption Key Begin | com.oraclecloud.digitalassistant.updatecustomerencryptionkey.begin |
| Pipeline - Delete Begin | com.oraclecloud.datascience.deletepipeline.begin |
| DR Protection Group - Update End | com.oraclecloud.disasterrecovery.updatedrprotectiongroup.end |
| External MySQL DB System - Enable Database Management End | com.oraclecloud.databasemanagement.externalmysqlresource.dbsystem.enablemgmt.end |
| Work Request - Install Other Windows Updates End | com.oraclecloud.osmh.installotherwindowsupdates.end |
| Local Peering Gateway - Update | com.oraclecloud.virtualnetwork.updatelocalpeeringgateway |
| DR Plan Execution - Pause Begin | com.oraclecloud.disasterrecovery.pausedrplanexecution.begin |
| Ingest Time Rule - Change Compartment | com.oraclecloud.logginganalytics.changeingesttimerulecompartment |
| Batch Task - Lifecycle State Change | com.oraclecloud.batch.updatebatchjobtaskstate |
| Update File System | com.oraclecloud.filestorage.updatefilesystem |
| Audit Archive Retrieval Create - End | com.oraclecloud.datasafe.createauditarchiveretrieval.end |
| BDS Instance - Configure Install ODH Patch Begin | com.oraclecloud.bds.cp.installodhpatch.begin |
| Instance Pool - Pre Termination Fail | com.oraclecloud.computemanagement.instancepoolpreterminationactionfail.end |
| Exadata Infrastructure ��� Granular Maintenance Scheduling Plan Needs Attention | com.oraclecloud.databaseservice.exadatainfrastructuremaintenanceschedulingplanneedsattention |
| Node - Enable Administrator Shell Access End | com.oraclecloud.zerolatency.enableadminshellaccess.end |
| Key - Change Compartment End | com.oraclecloud.keymanagementservice.changekeycompartment.end |
| LicenseManager - Update Configuration | com.oraclecloud.licensemanager.updateconfiguration |
| DR Protection Group - ChangeCompartment End | com.oraclecloud.disasterrecovery.changedrprotectiongroupcompartment.end |
| MySQL - Delete Backup End | com.oraclecloud.mysqlaas.deletebackup.end |
| Delete Volume Group Backup End | com.oraclecloud.blockvolumes.deletevolumegroupbackup.end |
| Delete Global Accelerator Listener Begin | com.oraclecloud.gax.public.api.deletelistener.begin |
| Instance Maintenance Event - Scheduled | com.oraclecloud.computeapi.instancemaintenance |
| Language - Delete Model End | com.oraclecloud.aiservicelanguage.deletemodel.end |
| Desktop - Delete | com.oraclecloud.ocidesktopservice.deletedesktop |
| FsuCycle - Create End | com.oraclecloud.fsu.createcycle.end |
| External Non-Container Database - Disable Stack Monitoring Service Begin | com.oraclecloud.databaseservice.disablestackmonitoringforexternalnoncontainerdatabase.begin |
| Change Certificate Compartment | com.oraclecloud.waf.changecertificatecompartment |
| Object Collection Rule - Delete | com.oraclecloud.logginganalytics.deleteloganalyticsobjectcollectionrule |
| Create Boot Volume End | com.oraclecloud.blockvolumes.createbootvolume.end |
| Exadata Infrastructure - Activate End | com.oraclecloud.databaseservice.activateexadatainfrastructure.end |
| Exadata Infrastructure - Configure Exascale End | com.oraclecloud.databaseservice.configureexascaleexadatainfrastructure.end |
| Exadata Infrastructure - Add Storage Capacity End | com.oraclecloud.databaseservice.addstoragecapacityexadatainfrastructure.end |
| Autonomous Cloud VM Cluster - maintenance end | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.maintenance.end |
| Cache Database - Configure Cache End | com.oraclecloud.zerolatency.configurecache.end |
| Pluggable Database - Relocate End | com.oraclecloud.databaseservice.pluggabledatabase.relocate.end |
| DR Plan Execution - CreateSwitchover Begin | com.oraclecloud.disasterrecovery.createswitchoverdrplanexecution |
| Anomaly Detection - Anomalies detected | com.oraclecloud.aiservice.anomaliesdetected |
| Cluster Network - Change Compartment | com.oraclecloud.computemanagement.changeclusternetworkcompartment |
| DFI Cluster: Start Begin | com.oraclecloud.dataflowinteractive.startinteractivecluster.begin |
| Assetsource - Change Compartment | com.oraclecloud.cloudbridge.changeassetsourcecompartment |
| Ping Monitor - Delete | com.oraclecloud.healthchecks.deletepingmonitor |
| Global Autonomous Database - Generate GSM Certificate Signing Request Begin | com.oraclecloud.globaldb.generategsmcertificatesigningrequest.begin |
| DR Protection Group - UpdateRole Begin | com.oraclecloud.disasterrecovery.updatedrprotectiongrouprole.begin |
| Cloud VM Cluster - Audit | com.oraclecloud.databaseservice.cloudvmcluster.audit |
| Cloud Exadata Infrastructure - Granular Maintenance Execution Window Canceled | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancecancelexecutionwindow |
| Exadata Infrastructure - Granular Maintenance Duration Exceeded Without Enforced Duration | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancedurationexceedednotenforced |
| Idp Group - Remove User From | com.oraclecloud.identitycontrolplane.removeuserfromidpgroup |
| Pipeline Run - Create End | com.oraclecloud.datascience.createpipelinerun.end |
| WebLogic Domain - Start End | com.oraclecloud.weblogicmanagement.startwlsdomain.end |
| Report Schedule Delete - End | com.oraclecloud.datasafe.removeschedulereport.end |
| Private IP - Delete | com.oraclecloud.virtualnetwork.deleteprivateip |
| Field - Delete | com.oraclecloud.logginganalytics.deletefield |
| Database - Terminate Begin | com.oraclecloud.databaseservice.deletedatabase.begin |
| Deployment - Update End | com.oraclecloud.apigateway.updatedeployment.end |
| Global Autonomous Database - Stop Begin | com.oraclecloud.globaldb.stopshardeddatabase.begin |
| Protection Policy - Change Compartment Begin | com.oraclecloud.autonomousrecoveryservice.changeprotectionpolicycompartment.begin |
| Migration Clone Begin | com.oraclecloud.odms.clonemigration.begin |
| Protected Database - Change Billing Compartment End | com.oraclecloud.autonomousrecoveryservice.changeprotecteddatabasebillingcompartment.end |
| Cache Database - Close Begin | com.oraclecloud.zerolatency.closezerolatencydatabase.begin |
| Associations - Delete | com.oraclecloud.logginganalytics.deleteassociations |
| Key - Schedule Deletion End | com.oraclecloud.keymanagementservice.schedulekeydeletion.end |
| Update Property | com.oraclecloud.appconfiguration.updateproperty |
| Database Tools Private Endpoint - Delete Begin | com.oraclecloud.dbtoolsserviceapi.deletedatabasetoolsprivateendpoint.begin |
| DFI Cluster: Stop End | com.oraclecloud.dataflowinteractive.stopinteractivecluster.end |
| VMware Solution - Create ESXi Host End | com.oraclecloud.vmwaresolution.createesxihost.end |
| Event - Create Set Software Source Event | com.oraclecloud.osmh.createevent.softwaresource.setsoftwaresources |
| Detected - Problem | com.oraclecloud.cloudguard.problemdetected |
| Cluster - Delete | com.oraclecloud.oraclerovingedgeinfrastructure.deletecluster |
| Subscription - Get Unsubscription | com.oraclecloud.notification.getunsubscription |
| VNIC - Attach Begin | com.oraclecloud.computeapi.attachvnic.begin |
| Data Exchange - Create End | com.oraclecloud.dataexchange.createdataexchange.end |
| Distributed Database - Patch End | com.oraclecloud.globaldb.patchdistributeddatabase.end |
| Identity Provider - Create | com.oraclecloud.identitycontrolplane.createidentityprovider |
| PathAnalyzerTest - Change Compartment | com.oraclecloud.vnconfigadvisor.changepathanalyzertestcompartment |
| SQL Firewall Policy Auto Create | com.oraclecloud.datasafe.autocreatesqlfirewallpolicy |
| TriggeredAlert - Create | com.oraclecloud.budgets.createtriggeredalert |
| Distributed Database - Stop Begin | com.oraclecloud.globaldb.stopdistributeddatabase.begin |
| Instance Configuration - Change Compartment | com.oraclecloud.computemanagement.changeinstanceconfigurationcompartment |
| Integration Instance - Stop Begin | com.oraclecloud.integration.stopintegrationinstance.begin |
| Resource Analytics Instance - Delete Begin | com.oraclecloud.resourceanalytics.deleteresourceanalyticsinstance.begin |
| NAT Gateway - Update | com.oraclecloud.natgateway.updatenatgateway |
| Instance Console Connection - Create End | com.oraclecloud.computeapi.createinstanceconsoleconnection.end |
| DeployArtifact - Update End | com.oraclecloud.devopsdeploy.updatedeployartifact.end |
| Security Policy Configuration Delete - Begin | com.oraclecloud.datasafe.deletesecuritypolicyconfig.begin |
| DeployPipeline - Update Begin | com.oraclecloud.devopsdeploy.updatedeploypipeline.begin |
| API - Create End | com.oraclecloud.apigateway.createapi.end |
| Batch Job - Change Compartment End | com.oraclecloud.batch.changebatchjobcompartment.end |
| Authorization Code Request | com.oraclecloud.identitysignon.authcoderequest |
| Oracle managed software update staging completed | com.oraclecloud.databaseservice.oraclemanageddbhomestagecompleted |
| Migration Create End | com.oraclecloud.odms.createmigration.end |
| BDS Instance - Disable Cloud SQL End | com.oraclecloud.bds.cp.removecloudsql.end |
| Instance Console Connection - Delete End | com.oraclecloud.computeapi.deleteinstanceconsoleconnection.end |
| Idp Group Mapping - Delete | com.oraclecloud.identitycontrolplane.removeidpgroupmapping |
| Change Http Redirect Compartment | com.oraclecloud.waf.changehttpredirectcompartment |
| Global Autonomous Database - Configure GSMs Begin | com.oraclecloud.globaldb.configureshardeddatabasegsms.begin |
| Distributed Autonomous Database - Generate GSM Certificate Signing Request End | com.oraclecloud.globaldb.generatedistributedautonomousdatabasegsmcertificatesigningrequest.end |
| Web Application Firewall - Update Begin | com.oraclecloud.waf.updatewebappfirewall.begin |
| Notebook Session - Deactivate End | com.oraclecloud.datascience.deactivatenotebooksession.end |
| Event - Create Set Management Station Unavailable State Event | com.oraclecloud.osmh.createevent.managementstation.setmanagementstationhealthstate.unavailable |
| Update Waas Policy Begin | com.oraclecloud.waf.updatewaaspolicy.begin |
| Data Lake - Update End | com.oraclecloud.datalake.updatedatalake.end |
| Exadata Infrastructure - IB Switch maintenance Begin | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancenetworkswitches.begin |
| Exadata Infrastructure - Custom action time End | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecustomactiontime.end |
| Exadata Infrastructure - IB Switch maintenance End | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancenetworkswitches.end |
| Exadata Infrastructure - Activate Begin | com.oraclecloud.databaseservice.activateexadatainfrastructure.begin |
| Exadata Infrastructure - Add Storage Capacity Begin | com.oraclecloud.databaseservice.addstoragecapacityexadatainfrastructure.begin |
| Exadata Infrastructure - Configure Exascale Begin | com.oraclecloud.databaseservice.configureexascaleexadatainfrastructure.begin |
| Instance - Update | com.oraclecloud.computeapi.updateinstance |
| Cloud Exadata Infrastructure ��� Granular Maintenance Scheduling Plan Needs Attention | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenanceschedulingplanneedsattention |
| MySQL - Upgrade DB System End | com.oraclecloud.mysqlaas.upgradedbsystem.end |
| Delete Alert Policy Rule - Begin | com.oraclecloud.datasafe.deletealertpolicyrule.begin |
| Autonomous Container Database - Maintenance End | com.oraclecloud.databaseservice.autonomous.container.database.maintenance.end |
| Batch Job Pool - Update End | com.oraclecloud.batch.updatebatchjobpool.end |
| Exadata Infrastructure - Storage server maintenance Begin | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancestorageservers.begin |
| MySQL - Upgrade DB System Begin | com.oraclecloud.mysqlaas.upgradedbsystem.begin |
| Exadata Infrastructure - Granular Maintenance Duration Unplanned Windows Created | com.oraclecloud.databaseservice.exaccinfrastructuremaintenanceunplannedwindowscreated |
| SQL Firewall Collection Cleanup | com.oraclecloud.datasafe.cleanupsqlcollection |
| Upload Log File - Delete | com.oraclecloud.logginganalytics.deleteuploadfile |
| VMware Solution - Delete Cluster Begin | com.oraclecloud.vmwaresolution.deletecluster.begin |
| External MySQL Connector - Update End | com.oraclecloud.databasemanagement.externalmysqlresource.connector.update.end |
| ODA Instance - Activate Customer Encryption Key End | com.oraclecloud.digitalassistant.activatecustomerencryptionkey.end |
| Console History - Capture Begin | com.oraclecloud.computeapi.captureconsolehistory.begin |
| Distributed Database - Start Begin | com.oraclecloud.globaldb.startdistributeddatabase.begin |
| Service Gateway - Delete End | com.oraclecloud.servicegateway.deleteservicegateway.end |
| Fusion Environment - Change Compartment Begin | com.oraclecloud.fusionapps.changefusionenvironmentcompartment.begin |
| Protection Policy - Delete Begin | com.oraclecloud.autonomousrecoveryservice.deleteprotectionpolicy.begin |
| IngressGateway - Change Compartment End | com.oraclecloud.servicemesh.changeingressgatewaycompartment.end |
| UpdateInventory | com.oraclecloud.cloudbridge.updateinventory |
| WebLogic Domain - Restart End | com.oraclecloud.weblogicmanagement.restartwlsdomain.end |
| Distributed Autonomous Database - Change Compartment End | com.oraclecloud.globaldb.changedistributedautonomousdatabasecompartment.end |
| HTTP Monitor - Delete | com.oraclecloud.healthchecks.deletehttpmonitor |
| Notebook Session - Update | com.oraclecloud.datascience.updatenotebooksession |
| Change Mount Target Compartment | com.oraclecloud.filestorage.changemounttargetcompartment |
| Job - Cancel | com.oraclecloud.oracleresourcemanager.canceljob |
| IngressGateway - Delete Begin | com.oraclecloud.servicemesh.deleteingressgateway.begin |
| Delete Volume Backup Policy | com.oraclecloud.blockvolumes.deletevolumebackuppolicy |
| Database Security Config Create - End | com.oraclecloud.datasafe.createdatabasesecurityconfig.end |
| Database - Create Begin | com.oraclecloud.databaseservice.createdatabase.begin |
| Event - Create Agent Upload Content Event | com.oraclecloud.osmh.createevent.agent.uploadcontent |
| DB System - Audit | com.oraclecloud.databaseservice.dbsystem.audit |
| Oneoff Patch - Create Begin | com.oraclecloud.databaseservice.createoneoffpatch.begin |
| HostScanRecipes - Update | com.oraclecloud.vulnerabilityscanning.updatehostscanrecipe.begin |
| Delete Alert Policy Rule - End | com.oraclecloud.datasafe.deletealertpolicyrule.end |
| Pluggable Database - Refresh Begin | com.oraclecloud.databaseservice.pluggabledatabase.refresh.begin |
| Global Database Private Endpoint - Create Begin | com.oraclecloud.globaldb.createprivateendpoint.begin |
| Private IP - Create | com.oraclecloud.virtualnetwork.createprivateip |
| Get Workspace | com.oraclecloud.dataintegration.getworkspace |
| Job Delete End | com.oraclecloud.odms.deletejob.end |
| Migration Update End | com.oraclecloud.odms.updatemigration.end |
| Api Key - Delete | com.oraclecloud.identitycontrolplane.deleteapikey |
| Web Application Acceleration Policy - Delete End | com.oraclecloud.waa.deletewebappaccelerationpolicy.end |
| Autonomous Database - Create Backup Begin | com.oraclecloud.databaseservice.autonomous.database.backup.begin |
| Audit Archive Retrieval Create - Begin | com.oraclecloud.datasafe.createauditarchiveretrieval.begin |
| Delete Boot Volume End | com.oraclecloud.blockvolumes.deletebootvolume.end |
| Grant - Delete | com.oraclecloud.identitycontrolplane.deletegrant |
| Sensitive Column Create - End | com.oraclecloud.datasafe.createsensitivecolumn.end |
| Appliance - Update | com.oraclecloud.datatransferservice.updatetransferappliance |
| Distributed Database - Create Begin | com.oraclecloud.globaldb.createdistributeddatabase.begin |
| DeployStage - Create Begin | com.oraclecloud.devopsdeploy.createdeploystage.begin |
| Data Guard Failover - End | com.oraclecloud.databaseservice.dataguardfailover.end |
| KeyVersion - Create Begin | com.oraclecloud.keymanagementservice.createkeyversion.begin |
| DR Plan - Delete Begin | com.oraclecloud.disasterrecovery.deletedrplan |
| BDS Instance - Add Block Storage Begin | com.oraclecloud.bds.cp.addblockstorage.begin |
| DFI Cluster: Update Begin | com.oraclecloud.dataflowinteractive.updateinteractivecluster.begin |
| Delete Boot Volume Backup Begin | com.oraclecloud.blockvolumes.deletebootvolumebackup.begin |
| Deployment - Delete End | com.oraclecloud.apigateway.deletedeployment.end |
| Event - Update Report | com.oraclecloud.osmh.event.updatereport |
| Database - Enable DbManagement Begin | com.oraclecloud.databaseservice.enabledbmanagement.begin |
| Cache Database - Initiate Checkpoint End | com.oraclecloud.zerolatency.checkpointzerolatencydatabase.end |
| Key - Create End | com.oraclecloud.keymanagementservice.createkey.end |
| DeployPipeline - Update End | com.oraclecloud.devopsdeploy.updatedeploypipeline.end |
| Application Data Platform - PodDb Restore Point Create Begin | com.oraclecloud.applicationdataplatform.createpoddbrestorepoint.begin |
| Work Request - Get Windows Update Details End | com.oraclecloud.osmh.getwindowsupdatedetails.end |
| Protected Database - Delete Begin | com.oraclecloud.autonomousrecoveryservice.deleteprotecteddatabase.begin |
| BDS Instance - Configure Install OS Patch End | com.oraclecloud.bds.cp.installospatch.end |
| Delete Workspace - End | com.oraclecloud.dataintegration.deletedisworkspace.end |
| Update Caching Rules Begin | com.oraclecloud.waf.updatecachingrules.begin |
| BDS Instance - AutoscaleRun - Scale Out | com.oraclecloud.bds.autoscale.cp.autoscaleout |
| OMA - Update Approval Template | com.oraclecloud.lockbox.updateapprovaltemplate |
| AlertRule - Delete | com.oraclecloud.budgets.deletealertrule |
| Delete NetworkFirewallPolicy | com.oraclecloud.networkfirewallservice.deletenetworkfirewallpolicy |
| Kafka Cluster - Delete Begin | com.oraclecloud.rawfkaapiprod.deletekafkacluster.begin |
| Delete Repository - End | com.oraclecloud.devopscoderepo.deleterepository.end |
| Function - Create | com.oraclecloud.functions.createfunction |
| Batch Context - Change Compartment Begin | com.oraclecloud.batch.changebatchcontextcompartment.begin |
| Work Request - Reboot End | com.oraclecloud.osmh.reboot.end |
| Job State Successful | com.oraclecloud.odms.jobstatesucceeded |
| DR Plan Execution - Delete End | com.oraclecloud.disasterrecovery.deletedrplanexecution.end |
| Appliance Export Job - Move | com.oraclecloud.datatransferservice.moveapplianceexportjob |
| Sensitive Column Delete | com.oraclecloud.datasafe.deletesensitivecolumn |
| MySQL - Create Channel Begin | com.oraclecloud.mysqlaas.createchannel.begin |
| SQL Firewall Collection Logs Purge - Begin | com.oraclecloud.datasafe.purgesqlcollectionlogs.begin |
| AccessPolicy - Update Begin | com.oraclecloud.servicemesh.updateaccesspolicy.begin |
| Service Configuration - Update | com.oraclecloud.weblogicmanagement.updateconfiguration |
| API - Create Begin | com.oraclecloud.apigateway.createapi.begin |
| Create Alert Policy - Begin | com.oraclecloud.datasafe.createalertpolicy.begin |
| Policy - Create | com.oraclecloud.identitycontrolplane.createpolicy |
| Db Node Snapshot - Mount Begin | com.oraclecloud.databaseservice.mountdbnodesnapshot.begin |
| DR Protection Group - Associate Begin | com.oraclecloud.disasterrecovery.associatedrprotectiongroup.begin |
| Key - Change Compartment Begin | com.oraclecloud.keymanagementservice.changekeycompartment.begin |
| Event - Create Software Source Event | com.oraclecloud.osmh.createevent.softwaresource.createsoftwaresource |
| Model Deployment - Delete End | com.oraclecloud.datascience.deletemodeldeployment.end |
| Pluggable database - Enable Database Management Service Begin | com.oraclecloud.databaseservice.enablepdbmanagement.begin |
| Change Waas Policy Compartment | com.oraclecloud.waf.changewaaspolicycompartment |
| Resource Schedule - Create End | com.oraclecloud.resourcescheduler.createschedule.end |
| Deployment - Create Begin | com.oraclecloud.apigateway.createdeployment.begin |
| Schedule Cascade Delete Project - end | com.oraclecloud.devopsproject.schedulecascadingprojectdeletion.end |
| Copy Boot Volume Backup End | com.oraclecloud.blockvolumes.copybootvolumebackup.end |
| Oracle managed datbase software update readiness check failed | com.oraclecloud.databaseservice.managedsoftwareupdatereadinesscheckfailed |
| Create Delegation Subscription - Begin | com.oraclecloud.delegateaccesscontrol.createdelegationsubscription.begin |
| DR Plan - Update End | com.oraclecloud.disasterrecovery.updatedrplan.end |
| Masking Policy Create - Begin | com.oraclecloud.datasafe.createmaskingpolicy.begin |
| Security Policy Deployment Refresh - Begin | com.oraclecloud.datasafe.refreshsecuritypolicydeployment.begin |
| Web Application Firewall - Delete Begin | com.oraclecloud.waf.deletewebappfirewall.begin |
| Global Autonomous Database - Patch Begin | com.oraclecloud.globaldb.patchshardeddatabase.begin |
| PathAnalyzerTest - Delete | com.oraclecloud.vnconfigadvisor.deletepathanalyzertest |
| VM Cluster - Change Compartment | com.oraclecloud.databaseservice.changevmclustercompartment |
| Create Global Accelerator End | com.oraclecloud.gax.public.api.createglobalaccelerator.end |
| MySQL - Stop HeatWave Cluster Begin | com.oraclecloud.mysqlaas.stopheatwavecluster.begin |
| Create Alert Policy Rule - Begin | com.oraclecloud.datasafe.createalertpolicyrule.begin |
| Database - Create End | com.oraclecloud.postgresql.createdbsystem.end |
| Database - Modify DbManagement Begin | com.oraclecloud.databaseservice.modifydbmanagement.begin |
| Database Tools Connection - Change Compartment End | com.oraclecloud.dbtoolsserviceapi.changedatabasetoolsconnectioncompartment.end |
| Delete Global Accelerator End | com.oraclecloud.gax.public.api.deleteglobalaccelerator.end |
| Work Request - Remove Content Begin | com.oraclecloud.osmh.removecontent.begin |
| Event - Create Reboot Succeeded Event | com.oraclecloud.osmh.createevent.reboot.rebootsucceeded |
| Autoscaling Configuration - Update Policy | com.oraclecloud.autoscaling.updateautoscalingpolicy |
| Verification Email - Send | com.oraclecloud.identitycontrolplane.sendverificationemail |
| Update Workspace - Begin | com.oraclecloud.dataintegration.updateworkspace.begin |
| SMTP Credential - Delete | com.oraclecloud.identitycontrolplane.deletesmtpcredential |
| Autonomous Data Guard Association - Create End | com.oraclecloud.databaseservice.createautonomousdataguardassociation.end |
| Exadata Infrastructure - Change Compartment | com.oraclecloud.databaseservice.changeexadatainfrastructurecompartment |
| Language - Update Project End | com.oraclecloud.aiservicelanguage.updateproject.end |
| Global Autonomous Database - Stop End | com.oraclecloud.globaldb.stopshardeddatabase.end |
| Security Policy Report Delete - Begin | com.oraclecloud.datasafe.deletesecuritypolicyreport.begin |
| Protected Database - Create End | com.oraclecloud.autonomousrecoveryservice.createprotecteddatabase.end |
| External Non-Container Database - Disable Stack Monitoring Service End | com.oraclecloud.databaseservice.disablestackmonitoringforexternalnoncontainerdatabase.end |
| Alert Generated | com.oraclecloud.datasafe.generateauditalert |
| Data Guard Update Config - Begin | com.oraclecloud.databaseservice.updatedataguardconfig.begin |
| Peer - Create Peer Begin | com.oraclecloud.blockchain.createpeer.begin |
| Work Request - List Windows Update End | com.oraclecloud.osmh.listwindowsupdate.end |
| Update Iot DomainGroup - Begin | com.oraclecloud.iot.updateiotdomaingroup.begin |
| MySQL - Update HeatWave Cluster End | com.oraclecloud.mysqlaas.updateheatwavecluster.end |
| Scheduled Job - Run Now | com.oraclecloud.osms.runscheduledjobnow |
| External MySQL DB System - Disable Database Management End | com.oraclecloud.databasemanagement.externalmysqlresource.dbsystem.disablemgmt.end |
| BDS Lake Configuration Instance - Delete Lake Configuration Begin | com.oraclecloud.bds.cp.deletebdslakeconfiguration.begin |
| Import Inventory End | com.oraclecloud.cloudbridge.importinventory.end |
| Package - Update | com.oraclecloud.datatransferservice.detachdevicesfromtransferpackage |
| DeployPipeline - Delete End | com.oraclecloud.devopsdeploy.deletedeploypipeline.end |
| Label - Upsert | com.oraclecloud.logginganalytics.upsertlabel |
| Database - Delete End | com.oraclecloud.postgresql.deletedbsystem.end |
| OCI Cache Cluster - Delete End | com.oraclecloud.redisservice.deleterediscluster.end |
| User - Delete | com.oraclecloud.identitycontrolplane.deleteuser |
| Protection Policy - Delete End | com.oraclecloud.autonomousrecoveryservice.deleteprotectionpolicy.end |
| KeyVersion - Create End | com.oraclecloud.keymanagementservice.createkeyversion.end |
| App Configuration Export - End | com.oraclecloud.appconfiguration.exportappconfiguration.end |
| Create Property | com.oraclecloud.appconfiguration.createproperty |
| Service Instance - Create End | com.oraclecloud.zerolatency.createzerolatency.end |
| Close - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.closedelegatedresourceaccessrequest |
| Alert UpdateAll - Begin | com.oraclecloud.datasafe.alertsupdate.begin |
| Refresh Data Guard Health Status - Begin | com.oraclecloud.databaseservice.dataguardrefreshhealthstatus.begin |
| Data Guard Switchover - Begin | com.oraclecloud.databaseservice.dataguardswitchover.begin |
| Entitlement - Delete | com.oraclecloud.oraclerovingedgeinfrastructure.deleteentitlement |
| Fusion Environment Family - Update End | com.oraclecloud.fusionapps.updatefusionenvironmentfamily.end |
| Create Volume Backup End | com.oraclecloud.blockvolumes.createvolumebackup.end |
| Batch Job - Pause End | com.oraclecloud.batch.pausebatchjob.end |
| Subscription - Create | com.oraclecloud.notification.createsubscription |
| Budget - Update | com.oraclecloud.budgets.updatebudget |
| Disabled Target Alert Policy Association | com.oraclecloud.datasafe.disabledtargetalertpolicyassociation |
| BDS Lake Configuration Instance - Update Lake Configuration Begin | com.oraclecloud.bds.cp.updatebdslakeconfiguration.begin |
| Speech - Failed Transcription Job | com.oraclecloud.aiservicespeech.failedtranscriptionjob |
| Stream Cdn Config - Delete | com.oraclecloud.mediaservices.deletestreamcdnconfig |
| BuildPipeline - Delete Begin | com.oraclecloud.devopsbuild.deletebuildpipeline.begin |
| Assetsource - Update End | com.oraclecloud.cloudbridge.updateassetsource.end |
| Instance - Change Compartment | com.oraclecloud.apiplatform.changeapiplatforminstancecompartment |
| Managed Instance - Install All Package Updates | com.oraclecloud.osms.installallpackageupdatesonmanagedinstance |
| DFI Cluster: Create End | com.oraclecloud.dataflowinteractive.createinteractivecluster.end |
| Pluggable Database - Refresh End | com.oraclecloud.databaseservice.pluggabledatabase.refresh.end |
| BuildPipelineStage - Create End | com.oraclecloud.devopsbuild.createbuildpipelinestage.end |
| Entitlement - Create | com.oraclecloud.datatransferservice.createtransferapplianceentitlement |
| Update Global Accelerator Listener End | com.oraclecloud.gax.public.api.updatelistener.end |
| Work Request - Install Enhancement Windows Updates End | com.oraclecloud.osmh.installenhancementwindowsupdates.end |
| Batch Task Profile - Change Compartment Begin | com.oraclecloud.batch.changebatchtaskprofilecompartment.begin |
| Service Instance - Start Begin | com.oraclecloud.zerolatency.startzerolatency.begin |
| Distributed Autonomous Database - Configure GSMs End | com.oraclecloud.globaldb.configuredistributedautonomousdatabasegsms.end |
| Job - Move | com.oraclecloud.datatransferservice.movetransferjob |
| MySQL - Delete Backup Begin | com.oraclecloud.mysqlaas.deletebackup.begin |
| Distributed Database - Generate GSM Certificate Signing Request Begin | com.oraclecloud.globaldb.generatedistributeddatabasegsmcertificatesigningrequest.begin |
| Security Policy Deploy - Begin | com.oraclecloud.datasafe.deploysecuritypolicydeployment.begin |
| Software Source - Update | com.oraclecloud.osms.updatesoftwaresource |
| MeshIngressGatewayRouteTable - Change Compartment End | com.oraclecloud.servicemesh.changeingressgatewayroutetablecompartment.end |
| Database Tools Private Endpoint - Update Begin | com.oraclecloud.dbtoolsserviceapi.updatedatabasetoolsprivateendpoint.begin |
| WebLogic Domain - Install Latest Patches Begin | com.oraclecloud.weblogicmanagement.installlatestpatchesonwlsdomain.begin |
| Autonomous Data Guard Association - Failover Begin | com.oraclecloud.databaseservice.failoverautonomousdataguardassociation.begin |
| Task Execution- Exceeded Expected Duration | com.oraclecloud.dataintegration.exceededexpectedduration |
| Task Execution- Failed Concurrent Execution Attempt | com.oraclecloud.dataintegration.failedconcurrentexecutionattempt |
| Data Exchange - Update Begin | com.oraclecloud.dataexchange.updatedataexchange.begin |
| Job Resume Begin | com.oraclecloud.odms.resumejob.begin |
| SQL Firewall Collection Update - Begin | com.oraclecloud.datasafe.updatesqlcollection.begin |
| DFI Cluster: Delete End | com.oraclecloud.dataflowinteractive.deleteinteractivecluster.end |
| Update Mount Target | com.oraclecloud.filestorage.updatemounttarget |
| BDS Lake Configuration Instance - Create Lake Configuration Begin | com.oraclecloud.bds.cp.createbdslakeconfiguration.begin |
| Batch Task Profile - Update | com.oraclecloud.batch.updatebatchtaskprofile |
| Delete Expired Snapshot | com.oraclecloud.filestorage.deleteexpiredsnapshot |
| Protection Policy - Create Begin | com.oraclecloud.autonomousrecoveryservice.createprotectionpolicy.begin |
| OMA - Update Resource Settings | com.oraclecloud.lockbox.updatelockbox |
| BDS Instance - Add Worker Node End | com.oraclecloud.bds.cp.addnode.end |
| Custom Content - Import | com.oraclecloud.logginganalytics.importcustomcontent |
| Autonomous Container Database - Maintenance Reminder | com.oraclecloud.databaseservice.autonomous.container.database.maintenance.reminder |
| External MySQL Connector - Update Begin | com.oraclecloud.databasemanagement.externalmysqlresource.connector.update.begin |
| Fleet - Update Begin | com.oraclecloud.javamanagementservice.updatefleet.begin |
| MySQL - Delete DB System Begin | com.oraclecloud.mysqlaas.deletedbsystem.begin |
| VMware Solution - Replace ESXi Host End | com.oraclecloud.vmwaresolution.replacehost.end |
| Instance Pool - Create Begin | com.oraclecloud.computemanagement.createinstancepool.begin |
| Create Policy-based Snapshot | com.oraclecloud.filestorage.createpolicybasedsnapshot |
| Label - Delete | com.oraclecloud.logginganalytics.deletelabel |
| Language - Create Model End | com.oraclecloud.aiservicelanguage.createmodel.end |
| VM Cluster Network - Add DB Server Network End | com.oraclecloud.databaseservice.adddbservervmclusternetwork.end |
| VM Cluster Network - Remove DB Server Network End | com.oraclecloud.databaseservice.removedbservervmclusternetwork.end |
| Distributed Autonomous Database - Create Begin | com.oraclecloud.globaldb.createdistributedautonomousdatabase.begin |
| VM Cluster Network - Terminate End | com.oraclecloud.databaseservice.deletevmclusternetwork.end |
| Autonomous VM Cluster - Maintenance End | com.oraclecloud.databaseservice.autonomousvmclustermaintenance.end |
| Event - Repositories Matched | com.oraclecloud.osmh.event.reposmatched |
| Pipeline Run - Timeout | com.oraclecloud.datascience.timeoutpipelinerun |
| BDS Instance - Create NodeBackup Configuration | com.oraclecloud.bds.cp.createnodebackupconfig |
| OCI Cache Cluster - Change Compartment Begin | com.oraclecloud.redisservice.changeredisclustercompartment.begin |
| Update Volume Kms Key Begin | com.oraclecloud.blockvolumes.updatevolumekmskey.begin |
| DataRefresh - Complete | com.oraclecloud.analyticswarehouse.pipeline.datarefresh.complete |
| Global Autonomous Database - Upload Signed Certificate And Generate Wallet Begin | com.oraclecloud.globaldb.uploadsignedcertificateandgeneratewallet.begin |
| Instance Pool - Pre Termination Begin | com.oraclecloud.computemanagement.instancepoolpreterminationaction.begin |
| BDS Instance - AutoscaleRun - Scale Down | com.oraclecloud.bds.autoscale.cp.autoscaledown |
| Managed Instance - Install Windows Enhancement Updates | com.oraclecloud.osmh.installenhancementwindowsupdates |
| Deployment - Update | com.oraclecloud.devopsdeploy.updatedeployment |
| Cache Database - Generate Diagnostics End | com.oraclecloud.zerolatency.generatezerolatencydatabasediagnostics.end |
| Lustre File System - Change Compartment End | com.oraclecloud.lustrefilestorage.changelustrefilesystemcompartment.end |
| Index - Drop Begin | com.oraclecloud.nosql.dropindex.begin |
| VirtualService - Update End | com.oraclecloud.servicemesh.updatevirtualservice.end |
| Masking Policy Update - End | com.oraclecloud.datasafe.updatemaskingpolicy.end |
| MySQL - Start HeatWave Cluster End | com.oraclecloud.mysqlaas.startheatwavecluster.end |
| Work Request - Install All Windows Updates End | com.oraclecloud.osmh.installallwindowsupdates.end |
| Security Policy Deployment Refresh - End | com.oraclecloud.datasafe.refreshsecuritypolicydeployment.end |
| BDS Instance - Delete Nodes Backups End | com.oraclecloud.bds.cp.deletenodesbackups.end |
| Instance - Create Instance Begin | com.oraclecloud.blockchain.createplatforminstance.begin |
| Work Request - Update Software Source Begin | com.oraclecloud.osmh.updatesoftwaresource.begin |
| Work Request - Switch Snap Channel End | com.oraclecloud.osmh.switchsnapchannel.end |
| Kafka Config - Delete | com.oraclecloud.rawfkaapiprod.deletekafkaclusterconfig |
| Pipeline Run - Cancel End | com.oraclecloud.datascience.cancelpipelinerun.end |
| Update Global Accelerator Ruleset End | com.oraclecloud.gax.public.api.updateruleset.end |
| Lustre File System - Delete End | com.oraclecloud.lustrefilestorage.deletelustrefilesystem.end |
| Create Waas Policy End | com.oraclecloud.waf.createwaaspolicy.end |
| Batch Job - Unpause Begin | com.oraclecloud.batch.unpausebatchjob.begin |
| Distributed Database - Add GDSCTL Node End | com.oraclecloud.globaldb.adddistributeddatabasegdscontrolnode.end |
| Cache Database - Start Replication Agent End | com.oraclecloud.zerolatency.startreplicationagent.end |
| Delete NetworkFirewall End | com.oraclecloud.networkfirewallservice.deletenetworkfirewall.end |
| Cluster Network - Terminate Begin | com.oraclecloud.computemanagement.terminateclusternetwork.begin |
| Identity Provider - Update | com.oraclecloud.identitycontrolplane.updateidentityprovider |
| Database Tools Private Endpoint - Change Compartment Begin | com.oraclecloud.dbtoolsserviceapi.changedatabasetoolsprivateendpointcompartment.begin |
| Change Protection Mode Begin | com.oraclecloud.databaseservice.changeprotectionmode.begin |
| Update Global Accelerator Hostname Begin | com.oraclecloud.gax.public.api.updatehostname.begin |
| Database Tools Connection - Create Begin | com.oraclecloud.dbtoolsserviceapi.createdatabasetoolsconnection.begin |
| Fusion Environment - Refresh Begin | com.oraclecloud.fusionapps.fusionenvironmentrefresh.begin |
| Managed Instance Group - Change Compartment | com.oraclecloud.osms.changemanagedinstancegroupcompartment |
| Work Request - Sync Metadata End | com.oraclecloud.osmh.syncmetadata.end |
| Entitlement - Delete | com.oraclecloud.datatransferservice.deletetransferapplianceentitlement |
| Work Request - Update Bug Fix End | com.oraclecloud.osmh.updatebugfix.end |
| Gateway - Update Begin | com.oraclecloud.apigateway.updategateway.begin |
| Autonomous Cloud VM Cluster - Update Begin | com.oraclecloud.databaseservice.autonomous.autonomouscloudvmcluster.update.begin |
| Delegate Access Control Customer Alert | com.oraclecloud.delegateaccesscontrol.customeralert |
| Distributed Autonomous Database - Generate GSM Certificate Signing Request Begin | com.oraclecloud.globaldb.generatedistributedautonomousdatabasegsmcertificatesigningrequest.begin |
| Language - Detect Sentiments | com.oraclecloud.aiservicelanguage.detectlanguagesentiments |
| Distributed Database - Configure GSMs End | com.oraclecloud.globaldb.configuredistributeddatabasegsms.end |
| Migration - Delete Begin | com.oraclecloud.applicationmigration.deletemigration.begin |
| Desktop Pool - Stop | com.oraclecloud.ocidesktopservice.stopdesktoppool |
| External Pluggable Database - Disable Stack Monitoring Service Begin | com.oraclecloud.databaseservice.disablestackmonitoringforexternalpluggabledatabase.begin |
| Network Address List - Create End | com.oraclecloud.waf.createnetworkaddresslist.end |
| Model Deployment - Deactivate End | com.oraclecloud.datascience.deactivatemodeldeployment.end |
| Data Exchange - Delete End | com.oraclecloud.dataexchange.deletedataexchange.end |
| MySQL - Stop DB System Begin | com.oraclecloud.mysqlaas.stopdbsystem.begin |
| Batch Task Environment - Create | com.oraclecloud.batch.createbatchtaskenvironment |
| ContainerScanResult - Delete | com.oraclecloud.vulnerabilityscanning.deletecontainerscanresult |
| Task Schedule- Last Trigger Event | com.oraclecloud.dataintegration.taskschedulelasttrigger |
| Renew Delegated Resource Access Request Bastion Session | com.oraclecloud.delegateaccesscontrol.renewdelegatedresourceaccessrequestbastionsession |
| Appliance Export Job - Update | com.oraclecloud.datatransferservice.updateapplianceexportjob |
| GGS Pipeline - Deleting | com.oraclecloud.goldengate.pipeline.statedeleting |
| Delete Property | com.oraclecloud.appconfiguration.deleteproperty |
| Ingest Time Rule - Update | com.oraclecloud.logginganalytics.updateingesttimerule |
| Kafka Cluster - Update End | com.oraclecloud.rawfkaapiprod.updatekafkacluster.end |
| Media Workflow Job - Delete begin | com.oraclecloud.mediaservices.deletemediaworkflowjob.begin |
| My Password Request - Create Or Reset | com.oraclecloud.identitycontrolplane.createorresetmypasswordrequest |
| Oracle managed database software update reminder | com.oraclecloud.databaseservice.managedsoftwareupdatereminder |
| Recovery Service Subnet - Change Compartment Begin | com.oraclecloud.autonomousrecoveryservice.changerecoveryservicesubnetcompartment.begin |
| Data Lake - Delete End | com.oraclecloud.datalake.deletedatalake.end |
| Fusion Environment - Create End | com.oraclecloud.fusionapps.createfusionenvironment.end |
| Web Application Acceleration Policy - Change Compartment End | com.oraclecloud.waa.changewebappaccelerationpolicycompartment.end |
| Delete Global Accelerator Listener End | com.oraclecloud.gax.public.api.deletelistener.end |
| Group - Add User To | com.oraclecloud.identitycontrolplane.addusertogroup |
| Asset - Create End | com.oraclecloud.dataexchange.createasset.end |
| Instance - Delete Begin | com.oraclecloud.omh.deleteomhinstance.begin |
| Process Automation Instance - Update Begin | com.oraclecloud.processautomation.updateopainstance.begin |
| Application Data Platform - PodDb Create Begin | com.oraclecloud.applicationdataplatform.createpoddb.begin |
| Create Volume Group Begin | com.oraclecloud.blockvolumes.createvolumegroup.begin |
| Source Event Types - Add | com.oraclecloud.logginganalytics.addsourceeventtypes |
| Waf Policy - Create Begin | com.oraclecloud.waf.createwebappfirewallpolicy.begin |
| Instance - Create Begin | com.oraclecloud.apiplatform.createapiplatforminstance.begin |
| Detection Rule - Create | com.oraclecloud.logginganalytics.createscheduledtask |
| Fusion Environment - Maintenance Extended | com.oraclecloud.fusionappsinternal.fusionenvironmentmaintenanceextended |
| Topic - Move | com.oraclecloud.notification.movetopic |
| Discovery Schedule - Delete | com.oraclecloud.cloudbridge.deletediscoveryschedule |
| Lustre File System - Delete Begin | com.oraclecloud.lustrefilestorage.deletelustrefilesystem.begin |
| Cache Database - Stop Replication Agent End | com.oraclecloud.zerolatency.stopreplicationagent.end |
| Boot Volume - Attach End | com.oraclecloud.computeapi.attachbootvolume.end |
| GGS Pipeline - Stopped | com.oraclecloud.goldengate.pipeline.statestopped |
| Stream Distribution Channel - Create | com.oraclecloud.mediaservices.createstreamdistributionchannel |
| App Configuration Create - Begin | com.oraclecloud.appconfiguration.createappconfiguration.begin |
| Idp User - Create | com.oraclecloud.identitycontrolplane.createidpuser |
| Application Data Platform - PodDb Patch Begin | com.oraclecloud.applicationdataplatform.createpoddbpatch.begin |
| Autonomous Database - Update DB Tools Begin | com.oraclecloud.databaseservice.updateautonomousdatabasetools.begin |
| Autonomous VM Cluster - Information | com.oraclecloud.databaseservice.autonomous.vmcluster.information |
| Connection - Create End | com.oraclecloud.devopsbuild.createconnection.end |
| Ingest Time Rule - Enable | com.oraclecloud.logginganalytics.enableingesttimerule |
| VMware Solution - List Supported Host Shapes | com.oraclecloud.vmwaresolution.listsupportedhostshapes |
| Language - Update Model Endpoint End | com.oraclecloud.aiservicelanguage.updatemodelendpoint.end |
| MySQL - Update DB System Begin | com.oraclecloud.mysqlaas.updatedbsystem.begin |
| Alert Policy Target Association Patch - End | com.oraclecloud.datasafe.patchtargetalertpolicyassociation.end |
| ODA Instance - Change Compartment Begin | com.oraclecloud.digitalassistant.changeodacompartment.begin |
| Update Delegation Control - End | com.oraclecloud.delegateaccesscontrol.updatedelegationcontrol.end |
| Reset Password | com.oraclecloud.identitysignon.resetpasswordandauthenticate |
| BDS Lake Configuration Instance - Activate Lake Configuration End | com.oraclecloud.bds.cp.activatebdslakeconfiguration.end |
| Create Delegation Control - Begin | com.oraclecloud.delegateaccesscontrol.createdelegationcontrol.begin |
| OSN - Update OSN Begin | com.oraclecloud.blockchain.updateosn.begin |
| VMware Solution - Create SDDC Begin | com.oraclecloud.vmwaresolution.createsddc.begin |
| Exascale Database Storage Vault - Create End | com.oraclecloud.databaseservice.createexascaledbstoragevault.end |
| Language - Update Model | com.oraclecloud.aiservicelanguage.updatemodel |
| Kafka Cluster - Create Begin | com.oraclecloud.rawfkaapiprod.createkafkacluster.begin |
| Capacity Reservation - Update reservation end | com.oraclecloud.computeapi.updatecomputecapacityreservation.end |
| Auth Token - Update | com.oraclecloud.identitycontrolplane.updateauthtoken |
| WebLogic Domain - Set Restart Order | com.oraclecloud.weblogicmanagement.setrestartorder |
| VLAN - Create | com.oraclecloud.virtualnetwork.createvlan |
| Create Mount Target | com.oraclecloud.filestorage.createmounttarget |
| Job - Create End | com.oraclecloud.oracleresourcemanager.createjob.end |
| Autonomous Database - Update Autonomous Database Scheduled Operations End | com.oraclecloud.databaseservice.updateautonomousdatabasescheduledoperations.end |
| Masking Policy Delete - End | com.oraclecloud.datasafe.deletemaskingpolicy.end |
| Subnet - Delete | com.oraclecloud.virtualnetwork.deletesubnet |
| KeyVersion Usage Limit | com.oraclecloud.keymanagementservice.keyversionusagelimit |
| Capacity Reservation - Update reservation begin | com.oraclecloud.computeapi.updatecomputecapacityreservation.begin |
| GGS Pipeline - Start Pipeline End | com.oraclecloud.goldengate.startpipeline.end |
| UpdateProject - end | com.oraclecloud.devopsproject.updateproject.end |
| DR Plan Execution - Retry End | com.oraclecloud.disasterrecovery.retrydrplanexecution.end |
| MySQL - Start DB System End | com.oraclecloud.mysqlaas.startdbsystem.end |
| FsuCycle - Delete End | com.oraclecloud.fsu.deletecycle.end |
| Imaging - Move | com.oraclecloud.computeimagingapi.moveimage |
| Batch Context - Delete End | com.oraclecloud.batch.deletebatchcontext.end |
| Web Application Acceleration Policy - Update Begin | com.oraclecloud.waa.updatewebappaccelerationpolicy.begin |
| External MySQL DB System - Enable Database Management Begin | com.oraclecloud.databasemanagement.externalmysqlresource.dbsystem.enablemgmt.begin |
| Distributed Autonomous Database - Configure Sharding Begin | com.oraclecloud.globaldb.configuredistributedautonomousdatabasesharding.begin |
| Work Request - Set Software Sources Begin | com.oraclecloud.osmh.setsoftwaresources.begin |
| Global Autonomous Database - Upload Signed Certificate And Generate Wallet End | com.oraclecloud.globaldb.uploadsignedcertificateandgeneratewallet.end |
| DeployEnvironment - Update Begin | com.oraclecloud.devopsdeploy.updatedeployenvironment.begin |
| Update NetworkFirewall Begin | com.oraclecloud.networkfirewallservice.updatenetworkfirewall.begin |
| Media Workflow - Create | com.oraclecloud.mediaservices.createmediaworkflow |
| Source - Delete | com.oraclecloud.logginganalytics.deletesource |
| Model Deployment - Activate End | com.oraclecloud.datascience.activatemodeldeployment.end |
| DR Plan Execution - CreateSwitchoverPreCheck Begin | com.oraclecloud.disasterrecovery.createswitchoverprecheckdrplanexecution |
| ZPR Policy - Update Begin | com.oraclecloud.zpr.updatezprpolicy.begin |
| ZPR Configuration - Update Begin | com.oraclecloud.zpr.updateconfiguration.begin |
| ZPR Configuration - Update End | com.oraclecloud.zpr.updateconfiguration.end |
| ZPR Policy - Update End | com.oraclecloud.zpr.updatezprpolicy.end |
| Global Autonomous Database - Fetch Connection String | com.oraclecloud.globaldb.fetchconnectionstring |
| DeployStage - Delete Begin | com.oraclecloud.devopsdeploy.deletedeploystage.begin |
| Service Instance - Update End | com.oraclecloud.zerolatency.updatezerolatency.end |
| Update Repository | com.oraclecloud.devopscoderepo.updaterepository |
| Price List - Create | com.oraclecloud.subscriptionpricingservice.createpricelist |
| Update Iot DomainGroup - End | com.oraclecloud.iot.updateiotdomaingroup.end |
| Integration Instance - Delete Begin | com.oraclecloud.integration.deleteintegrationinstance.begin |
| Event - Update | com.oraclecloud.osmh.updateevent |
| MySQL - Upgrade DB System - Update Crash Recovery Begin | com.oraclecloud.mysqlaas.updatecrashrecoveryforupgrade.begin |
| Waf Policy - Delete Begin | com.oraclecloud.waf.deletewebappfirewallpolicy.begin |
| Database Software Image - Move Begin | com.oraclecloud.databaseservice.movedatabasesoftwareimage.begin |
| Network Security Group - Change Compartment | com.oraclecloud.virtualnetwork.changenetworksecuritygroupcompartment |
| Delete Snapshot | com.oraclecloud.filestorage.deletesnapshot |
| Work Request - Install Module Profiles Begin | com.oraclecloud.osmh.installmoduleprofiles.begin |
| RevCycleEnvironment - Create Begin | com.oraclecloud.ircscontrolplaneapi.createrevcycleenvironment.begin |
| Update Export Set | com.oraclecloud.filestorage.updateexportset |
| Work Request - Get Windows Update Details Begin | com.oraclecloud.osmh.getwindowsupdatedetails.begin |
| Cancel Cascade Delete Project - end | com.oraclecloud.devopsproject.cancelscheduledcascadingprojectdeletion.end |
| AI Data Platform - Create End | com.oraclecloud.aidataplatform.createaidataplatform.end |
| VirtualDeployment - Update Begin | com.oraclecloud.servicemesh.updatevirtualdeployment.begin |
| Service Instance - Change Compartment Begin | com.oraclecloud.zerolatency.changezerolatencycompartment.begin |
| HostScanTarget - ChangeCompartment | com.oraclecloud.vulnerabilityscanning.changehostscantargetcompartment |
| Lustre File System - Create Begin | com.oraclecloud.lustrefilestorage.createlustrefilesystem.begin |
| Work Request - Update Vulnerability Begin | com.oraclecloud.osmh.updatevulnerability.begin |
| BDS Instance - Update Replace Configuration Begin | com.oraclecloud.bds.cp.updatereplaceconfig.begin |
| Fusion Environment Family - Terminate End | com.oraclecloud.fusionapps.terminatefusionenvironmentfamily.end |
| DeployPipeline - Create Begin | com.oraclecloud.devopsdeploy.createdeploypipeline.begin |
| Instance Console Connection - Create Begin | com.oraclecloud.computeapi.createinstanceconsoleconnection.begin |
| Process Instance - Delete Begin | com.oraclecloud.processautomation.deleteopainstance.begin |
| OAuth Client Credential - Create | com.oraclecloud.identitycontrolplane.createoauthclientcredential |
| DRG Attachment - Create | com.oraclecloud.virtualnetwork.createdrgattachment |
| Ping Monitor - Update | com.oraclecloud.healthchecks.updatepingmonitor |
| Notebook Session - Activate End | com.oraclecloud.datascience.activatenotebooksession.end |
| Media Workflow Job - Create end | com.oraclecloud.mediaservices.mediaworkflowjob.end |
| VMware Solution - Delete Cluster End | com.oraclecloud.vmwaresolution.deletecluster.end |
| Fleet - Change Compartment Begin | com.oraclecloud.javamanagementservice.changefleetcompartment.begin |
| Web Application Acceleration Policy - Create Begin | com.oraclecloud.waa.createwebappaccelerationpolicy.begin |
| MySQL - Update Channel Begin | com.oraclecloud.mysqlaas.updatechannel.begin |
| Unified Audit Policy Create - Begin | com.oraclecloud.datasafe.createunifiedauditpolicy.begin |
| Autonomous Database - Upgrade Database Version Begin | com.oraclecloud.databaseservice.upgradeautonomousdatabasedbversion.begin |
| Change Boot Volume Compartment End | com.oraclecloud.blockvolumes.changebootvolumecompartment.end |
| Work Request - Import Content End | com.oraclecloud.osmh.importcontent.end |
| MySQL - Update Channel End | com.oraclecloud.mysqlaas.updatechannel.end |
| Security Policy Report Update - End | com.oraclecloud.datasafe.refreshsecuritypolicyreport.end |
| Global Autonomous Database - Create End | com.oraclecloud.globaldb.createshardeddatabase.end |
| User State - Update | com.oraclecloud.identitycontrolplane.updateuserstate |
| Local Peering Gateway - Delete Begin | com.oraclecloud.virtualnetwork.deletelocalpeeringgateway.begin |
| VM Cluster - Terminate End | com.oraclecloud.databaseservice.deletevmcluster.end |
| Unified Audit Policy Definition Update - Begin | com.oraclecloud.datasafe.updateunifiedauditpolicydefinition.begin |
| RevCycleEnvironmentGroup - Create Begin | com.oraclecloud.ircscontrolplaneapi.createrevcycleenvironmentgroup.begin |
| Assetsource - Delete End | com.oraclecloud.cloudbridge.deleteassetsource.end |
| Software Source - Remove Package | com.oraclecloud.osms.removepackagesfromsoftwaresource |
| Exadb VM Cluster - Terminate Virtual Machine End | com.oraclecloud.databaseservice.exadbvmclusterterminatevirtualmachine.end |
| Db Node Snapshot - Create end | com.oraclecloud.databaseservice.createdbnodesnapshot.end |
| Web Application Acceleration - Create End | com.oraclecloud.waa.createwebappacceleration.end |
| DeployStage - Delete End | com.oraclecloud.devopsdeploy.deletedeploystage.end |
| Autoscaling Configuration - Change Compartment | com.oraclecloud.autoscaling.changeautoscalingconfigurationcompartment |
| BuildPipelineStage - Update Begin | com.oraclecloud.devopsbuild.updatebuildpipelinestage.begin |
| Distributed Autonomous Database - Add GDSCTL Node Begin | com.oraclecloud.globaldb.adddistributedautonomousdatabasegdscontrolnode.begin |
| Pricing Rule - Create | com.oraclecloud.subscriptionpricingservice.createpricingrule |
| ODA Instance - Delete End | com.oraclecloud.digitalassistant.deleteodainstance.end |
| Security Policy Configuration Delete - End | com.oraclecloud.datasafe.deletesecuritypolicyconfig.end |
| BDS Instance - AutoscaleRun - Replace Node | com.oraclecloud.bds.autoscale.cp.autoscalerunreplacenode |
| Instance Pool - Stop Action Begin | com.oraclecloud.computemanagement.stopinstancepool.begin |
| Pipeline Run - Cancel Begin | com.oraclecloud.datascience.cancelpipelinerun.begin |
| Boot Volume - Detach End | com.oraclecloud.computeapi.detachbootvolume.end |
| SQL Firewall Collection Auto Create | com.oraclecloud.datasafe.autocreatesqlcollection |
| Delete Iot Domain - End | com.oraclecloud.iot.deleteiotdomain.end |
| Autonomous Data Guard Association - Create Begin | com.oraclecloud.databaseservice.createautonomousdataguardassociation.begin |
| Task Execution- Exceeded Throttling Limit | com.oraclecloud.dataintegration.exceededthrottlinglimit |
| Fleet - Update End | com.oraclecloud.javamanagementservice.updatefleet.end |
| GGS Pipeline - Delete Pipeline Begin | com.oraclecloud.goldengate.deletepipeline.begin |
| Autonomous Database - Rotate Encryption Key Begin | com.oraclecloud.databaseservice.rotateautonomousdatabaseencryptionkey.begin |
| External Pluggable Database - Enable Stack Monitoring Service Begin | com.oraclecloud.databaseservice.enablestackmonitoringforexternalpluggabledatabase.begin |
| Access Request - Reject | com.oraclecloud.operatorcontrol.rejectaccessrequest |
| ContainerScanRecipes - Update Begin | com.oraclecloud.vulnerabilityscanning.updatecontainerscanrecipe.begin |
| Instance Pool - Stop Action End | com.oraclecloud.computemanagement.stopinstancepool.end |
| Delete Address List | com.oraclecloud.waf.deleteaddresslist |
| Work Request - Update Other Begin | com.oraclecloud.osmh.updateother.begin |
| MySQL - Start DB System Begin | com.oraclecloud.mysqlaas.startdbsystem.begin |
| Import Inventory Begin | com.oraclecloud.cloudbridge.importinventory.begin |
| BDS Instance - Configure Add Kafka Begin | com.oraclecloud.bds.cp.addkafka.begin |
| Private Service Access - Change Compartment Begin | com.oraclecloud.privateserviceaccess.changeprivateserviceaccesscompartment.begin |
| MeshIngressGatewayRouteTable - Change Compartment Begin | com.oraclecloud.servicemesh.changeingressgatewayroutetablecompartment.begin |
| Network Source - Create | com.oraclecloud.identitycontrolplane.createnetworksource |
| VirtualDeployment - Delete Begin | com.oraclecloud.servicemesh.deletevirtualdeployment.begin |
| Exadata Infrastructure - Delete End | com.oraclecloud.databaseservice.deleteexadatainfrastructure.end |
| MySQL - Update Configuration | com.oraclecloud.mysqlaas.updateconfiguration |
| BDS Lake Configuration Instance - Deactivate Lake Configuration End | com.oraclecloud.bds.cp.deactivatebdslakeconfiguration.end |
| Oracle managed database software update failed | com.oraclecloud.databaseservice.managedsoftwareupdatefailed |
| App Configuration Export - Begin | com.oraclecloud.appconfiguration.exportappconfiguration.begin |
| Event - Create Sysadmin Failed Event | com.oraclecloud.osmh.createevent.sysadmin.failed |
| Unified Audit Policy Delete - End | com.oraclecloud.datasafe.deleteunifiedauditpolicy.end |
| ContainerScanTarget - Delete Begin | com.oraclecloud.vulnerabilityscanning.deletecontainerscantarget.begin |
| MySQL - Automatic Recovery Begin | com.oraclecloud.mysqlaas.automaticrecovery.begin |
| MySQL - Create DB System Begin | com.oraclecloud.mysqlaas.createdbsystem.begin |
| External Container Database - Disable Stack Monitoring Service End | com.oraclecloud.databaseservice.disablestackmonitoringforexternalcontainerdatabase.end |
| BDS Instance - Terminate Begin | com.oraclecloud.bds.cp.terminateinstance.begin |
| Key - Backup Begin | com.oraclecloud.keymanagementservice.backupkey.begin |
| Distributed Autonomous Database - Configure Sharding End | com.oraclecloud.globaldb.configuredistributedautonomousdatabasesharding.end |
| Deregister Target Database - Begin | com.oraclecloud.datasafe.deregisterdatasafetarget.begin |
| BDS Instance - List Resource Principal Configurations | com.oraclecloud.bds.cp.listresourceprincipalconfiguration |
| WebLogic Domain - Update Credential | com.oraclecloud.weblogicmanagement.updatewlsdomaincredential |
| Event - Create Update Packages Event | com.oraclecloud.osmh.createevent.softwareupdate.updatepackages |
| OSN - Create OSN Begin | com.oraclecloud.blockchain.createosn.begin |
| DR Plan Execution - CreateStopDrillPreCheck End | com.oraclecloud.disasterrecovery.createstopdrillprecheckdrplanexecution.end |
| DR Protection Group - Disassociate Begin | com.oraclecloud.disasterrecovery.disassociatedrprotectiongroup.begin |
| BDS Instance - Configure Cloud SQL End | com.oraclecloud.bds.cp.addcloudsql.end |
| Work Request - Update Enhancement End | com.oraclecloud.osmh.updateenhancement.end |
| Audit Profile Update - End | com.oraclecloud.datasafe.updateauditprofile.end |
| Migration - Delete End | com.oraclecloud.applicationmigration.deletemigration.end |
| Device - Create | com.oraclecloud.datatransferservice.addtransferdevice |
| Batch Context - Stop | com.oraclecloud.batch.stopbatchcontext |
| Bastion - Create Bastion End | com.oraclecloud.bastion.createbastion.end |
| Delete Delegation Control - Begin | com.oraclecloud.delegateaccesscontrol.deletedelegationcontrol.begin |
| Language - Create Model Endpoint | com.oraclecloud.aiservicelanguage.createmodelendpoint |
| Product - Update | com.oraclecloud.subscriptionpricingservice.updateproduct |
| Delete Global Accelerator Hostname End | com.oraclecloud.gax.public.api.deletehostname.end |
| Mesh - Change Compartment End | com.oraclecloud.servicemesh.changemeshcompartment.end |
| Private Service Access - Create End | com.oraclecloud.privateserviceaccess.createprivateserviceaccess.end |
| Preferences - Update | com.oraclecloud.logginganalytics.updatepreferences |
| NAT Gateway - Change Compartment | com.oraclecloud.natgateway.changenatgatewaycompartment |
| Managed Instance - List Windows Update | com.oraclecloud.osmh.listwindowsupdate |
| Autonomous Database - Critical | com.oraclecloud.databaseservice.autonomous.database.critical |
| Oci Control Center - Create Catalog | com.oraclecloud.ocicontrolcentercp.createoccavailabilitycatalog |
| Oci Control Center - Create Capacity Request | com.oraclecloud.ocicontrolcentercp.createocccapacityrequest |
| Oci Control Center - Patch Capacity Request | com.oraclecloud.ocicontrolcentercp.patchocccapacityrequest |
| Oci Control Center - Update Capacity Request | com.oraclecloud.ocicontrolcentercp.updateocccapacityrequest |
| Oci Control Center - Delete Capacity Request | com.oraclecloud.ocicontrolcentercp.deleteocccapacityrequest |
| Oci Control Center - Update Internal Capacity Request | com.oraclecloud.ocicontrolcentercp.updateinternalocccapacityrequest |
| Oci Control Center - Delete Catalog | com.oraclecloud.ocicontrolcentercp.deleteoccavailabilitycatalog |
| Oci Control Center - Update Catalog | com.oraclecloud.ocicontrolcentercp.updateoccavailabilitycatalog |
| Oci Control Center - Patch Internal Capacity Request | com.oraclecloud.ocicontrolcentercp.patchinternalocccapacityrequest |
| Exadata Infrastructure - Configuration File Download | com.oraclecloud.databaseservice.downloadexadatainfrastructureconfigfile |
| Group - Remove User From | com.oraclecloud.identitycontrolplane.removeuserfromgroup |
| AI Data Platform - Create Begin | com.oraclecloud.aidataplatform.createaidataplatform.begin |
| Update Certificate | com.oraclecloud.waf.updatecertificate |
| Database - Disable DbManagement Begin | com.oraclecloud.databaseservice.disabledbmanagement.begin |
| Vault - Change Compartment End | com.oraclecloud.keymanagementservice.changevaultcompartment.end |
| BDS Api Key Instance - Create Api Key Begin | com.oraclecloud.bds.cp.createbdsapikey.begin |
| Instance Configuration - Update | com.oraclecloud.computemanagement.updateinstanceconfiguration |
| Autonomous Database - Update Autonomous Database Scheduled Operations Begin | com.oraclecloud.databaseservice.updateautonomousdatabasescheduledoperations.begin |
| Change Compartment NetworkFirewallPolicy | com.oraclecloud.networkfirewallservice.changenetworkfirewallpolicycompartment |
| Pluggable Database - Inplace Restore Begin | com.oraclecloud.databaseservice.pluggabledatabase.inplacerestore.begin |
| Access Request - Auto Approve | com.oraclecloud.operatorcontrol.autoapproveaccessrequest |
| Global Autonomous Database - Configure Sharding Begin | com.oraclecloud.globaldb.configuresharding.begin |
| Cluster - Update End | com.oraclecloud.clustersapi.updatecluster.end |
| Mesh - Change Compartment Begin | com.oraclecloud.servicemesh.changemeshcompartment.begin |
| Autonomous Container Database - Update End | com.oraclecloud.databaseservice.autonomous.container.database.instance.update.end |
| Cache Database - Delete End | com.oraclecloud.zerolatency.deletezerolatencydatabase.end |
| Language - Delete Model Endpoint | com.oraclecloud.aiservicelanguage.deletemodelendpoint |
| Distributed Autonomous Database - Start End | com.oraclecloud.globaldb.startdistributedautonomousdatabase.end |
| Move Workspace - End | com.oraclecloud.dataintegration.moveworkspace.end |
| DR Plan Execution - Pause End | com.oraclecloud.disasterrecovery.pausedrplanexecution.end |
| Delete Iot DomainGroup - End | com.oraclecloud.iot.deleteiotdomaingroup.end |
| Distributed Database - Configure Sharding End | com.oraclecloud.globaldb.configuredistributeddatabasesharding.end |
| Application Data Platform - PodDb Delete Begin | com.oraclecloud.applicationdataplatform.deletepoddb.begin |
| Security List - Change Compartment | com.oraclecloud.virtualnetwork.changesecuritylistcompartment |
| Audit Policy Retrieve - End | com.oraclecloud.datasafe.retrieveauditpolicies.end |
| Biometric - Cancel Schedule Delete Biometric Store | com.oraclecloud.aibiometriccpprod.canceleddeletebiometricstore |
| Biometric - Change Biometric Store Compartment | com.oraclecloud.aibiometriccpprod.changebiometricstorecompartment |
| Biometric - Create Biometric Store | com.oraclecloud.aibiometriccpprod.createbiometricstore |
| Biometric - Get Biometric Store | com.oraclecloud.aibiometriccpprod.getbiometricstore |
| Biometric - List Biometric Store | com.oraclecloud.aibiometriccpprod.listbiometricstores |
| Biometric - Schedule Delete Biometric Store | com.oraclecloud.aibiometriccpprod.scheduleddeletebiometricstore |
| Biometric - Update Biometric Store | com.oraclecloud.aibiometriccpprod.updatebiometricstore.begin |
| Language - Create Model | com.oraclecloud.aiservicelanguage.createmodel |
| Budget - Create | com.oraclecloud.budgets.createbudget |
| Security Assessment Finding Risk Update - End | com.oraclecloud.datasafe.updatefinding.end |
| Delete Boot Volume Backup End | com.oraclecloud.blockvolumes.deletebootvolumebackup.end |
| Visual Builder Studio - Delete Instance - end | com.oraclecloud.vbstudioinst.deletevbsinstance.end |
| Key - Cancel Deletion End | com.oraclecloud.keymanagementservice.cancelkeydeletion.end |
| Database - Update End | com.oraclecloud.databaseservice.updatedatabase.end |
| BDS Instance - AutoscaleRun - Terminate Cluster | com.oraclecloud.bds.autoscale.cp.autoscalerunterminatecluster |
| Security Policy Create - Begin | com.oraclecloud.datasafe.createsecuritypolicy.begin |
| Work Request - List Packages Begin | com.oraclecloud.osmh.listpackages.begin |
| VMware Solution - Replace ESXi Host Begin | com.oraclecloud.vmwaresolution.replacehost.begin |
| Audit Policy Retrieve - Begin | com.oraclecloud.datasafe.retrieveauditpolicies.begin |
| Vault - Backup Begin | com.oraclecloud.keymanagementservice.backupvault.begin |
| Sensitive Data Model Referential Relation Delete - End | com.oraclecloud.datasafe.deletereferentialrelation.end |
| Model - Delete | com.oraclecloud.datascience.deletemodel |
| BuildPipelineStage - Create Begin | com.oraclecloud.devopsbuild.createbuildpipelinestage.begin |
| DeployEnvironment - Delete Begin | com.oraclecloud.devopsdeploy.deletedeployenvironment.begin |
| Mesh - Delete End | com.oraclecloud.servicemesh.deletemesh.end |
| Node - Enable Administrator Shell Access Begin | com.oraclecloud.zerolatency.enableadminshellaccess.begin |
| Reject Delegated Resource Access Request - End | com.oraclecloud.delegateaccesscontrol.rejectdelegatedresourceaccessrequest.end |
| Create NetworkFirewall End | com.oraclecloud.networkfirewallservice.createnetworkfirewall.end |
| Cluster - Delete End | com.oraclecloud.clustersapi.deletecluster.end |
| Instance - Start Instance End | com.oraclecloud.blockchain.startplatforminstance.end |
| Automatic Key Rotation - End | com.oraclecloud.keymanagementservice.autokeyrotate.end |
| Support Account - Link | com.oraclecloud.identitycontrolplane.linksupportaccount |
| Distributed Autonomous Database - Upload Signed Certificate And Generate Wallet Begin | com.oraclecloud.globaldb.uploaddistributedautonomousdatabasesignedcertificateandgeneratewallet.begin |
| VM Cluster - Patch Begin | com.oraclecloud.databaseservice.patchvmcluster.begin |
| Autonomous Database - Rotate Encryption Key End | com.oraclecloud.databaseservice.rotateautonomousdatabaseencryptionkey.end |
| Delete NetworkFirewall Begin | com.oraclecloud.networkfirewallservice.deletenetworkfirewall.begin |
| ContainerScanRecipe - ChangeCompartment | com.oraclecloud.vulnerabilityscanning.changecontainerscanrecipecompartment |
| Event - Profile Updated | com.oraclecloud.osmh.event.profileupdated |
| Managed Instance - Update | com.oraclecloud.weblogicmanagement.updatemanagedinstance |
| Create Alert Policy Rule - End | com.oraclecloud.datasafe.createalertpolicyrule.end |
| Key - Disable End | com.oraclecloud.keymanagementservice.disablekey.end |
| Get Protected Database Configuration End | com.oraclecloud.autonomousrecoveryservice.fetchprotecteddatabaseconfiguration.end |
| Exadata Infrastructure - Create End | com.oraclecloud.databaseservice.createexadatainfrastructure.end |
| Namespace - Onboard | com.oraclecloud.logginganalytics.onboardnamespace |
| Remediated - Problem | com.oraclecloud.cloudguard.problemremediated |
| Database Software Image - Create End | com.oraclecloud.databaseservice.createdatabasesoftwareimage.end |
| Log Group - Update | com.oraclecloud.logginganalytics.updateloganalyticsloggroup |
| Media Workflow - Update | com.oraclecloud.mediaservices.updatemediaworkflow |
| Vault - Backup End | com.oraclecloud.keymanagementservice.backupvault.end |
| Distributed Autonomous Database - Start Begin | com.oraclecloud.globaldb.startdistributedautonomousdatabase.begin |
| Console History - Delete | com.oraclecloud.computeapi.deleteconsolehistory |
| Container Instance - Create Container Instance End | com.oraclecloud.containerinstances.createcontainerinstance.end |
| Scheduled Report Generated | com.oraclecloud.datasafe.scheduledreportcomplete |
| Volume - Detach End | com.oraclecloud.computeapi.detachvolume.end |
| Integration Instance - Create End | com.oraclecloud.integration.createintegrationinstance.end |
| Instance - Delete Instance End | com.oraclecloud.blockchain.deleteplatforminstance.end |
| Instance Pool - Update End | com.oraclecloud.computemanagement.updateinstancepool.end |
| Desktop - Stop | com.oraclecloud.ocidesktopservice.stopdesktop |
| HostCisBenchmarkScanResult - ChangeCompartment | com.oraclecloud.vulnerabilityscanning.changehostcisbenchmarkscanresultcompartment |
| Notebook Session - Create Begin | com.oraclecloud.datascience.createnotebooksession.begin |
| ODA Instance - Update | com.oraclecloud.digitalassistant.updateodainstance |
| Database Software Image - Delete End | com.oraclecloud.databaseservice.deletedatabasesoftwareimage.end |
| Scheduled Job - Skip Next Execution | com.oraclecloud.osms.skipnextscheduledjobexecution |
| Work Request - Update Ksplice Kernel End | com.oraclecloud.osmh.updateksplicekernel.end |
| Global Autonomous Database - Create Begin | com.oraclecloud.globaldb.createshardeddatabase.begin |
| Add Stack - Begin | com.oraclecloud.dataintelligencefoundation.addstack.begin |
| Delete Private Endpoint - End | com.oraclecloud.datasafe.deletedatasafeprivateendpoint.end |
| DB Node - Error | com.oraclecloud.databaseservice.dbnode.error |
| Batch Job - Unpause End | com.oraclecloud.batch.unpausebatchjob.end |
| BDS Instance - Restart Node Begin | com.oraclecloud.bds.cp.restartbdsnode.begin |
| Event - Create Update Ksplice Userspace Event | com.oraclecloud.osmh.createevent.kspliceupdate.updatekspliceuserspace |
| Delete Global Accelerator Hostname Begin | com.oraclecloud.gax.public.api.deletehostname.begin |
| VirtualDeployment - Create End | com.oraclecloud.servicemesh.createvirtualdeployment.end |
| Cloud VM Cluster - Critical | com.oraclecloud.databaseservice.cloudvmcluster.critical |
| Distributed Autonomous Database - Create End | com.oraclecloud.globaldb.createdistributedautonomousdatabase.end |
| Function - Update | com.oraclecloud.functions.updatefunction |
| Identity Provider Group - Delete | com.oraclecloud.identitycontrolplane.deleteidentityprovidergroup |
| SQL Firewall Collection Create - End | com.oraclecloud.datasafe.createsqlcollection.end |
| Work Request - Update Ksplice Userspace Begin | com.oraclecloud.osmh.updatekspliceuserspace.begin |
| BuildPipelineStage - Delete Begin | com.oraclecloud.devopsbuild.deletebuildpipelinestage.begin |
| Cache Database - Open Begin | com.oraclecloud.zerolatency.openzerolatencydatabase.begin |
| Protection Policy - Update Begin | com.oraclecloud.autonomousrecoveryservice.updateprotectionpolicy.begin |
| Create Delegation Subscription - End | com.oraclecloud.delegateaccesscontrol.createdelegationsubscription.end |
| Pipeline Run - Succeeded | com.oraclecloud.datascience.succeededpipelinerun |
| MeshIngressGatewayRouteTable - Create End | com.oraclecloud.servicemesh.createingressgatewayroutetable.end |
| Autonomous Database - Long-term Backup Will Expire In 30 Days | com.oraclecloud.databaseservice.autonomous.database.backup.longtermbackupexpiresinamonth.reminder |
| Event - Reboot Required | com.oraclecloud.osmh.event.rebootrequired |
| Delete Delegation Control - End | com.oraclecloud.delegateaccesscontrol.deletedelegationcontrol.end |
| Change Volume Group Compartment | com.oraclecloud.blockvolumes.changevolumegroupcompartment |
| Delete Volume Backup Policy Assignment | com.oraclecloud.blockvolumes.deletevolumebackuppolicyassignment |
| SQL Firewall Policy Cleanup | com.oraclecloud.datasafe.cleanupsqlfirewallpolicy |
| DR Plan Execution - Update End | com.oraclecloud.disasterrecovery.updatedrplanexecution.end |
| Object Storage Link Sync Job - Stop Export Job | com.oraclecloud.lustrefilestorage.stopexporttoobject |
| Compartments - Delete Compartment | com.oraclecloud.compartments.deletecompartment |
| Work Request - Install All Security Windows Updates End | com.oraclecloud.osmh.installsecuritywindowsupdates.end |
| Model Deployment - Update Begin | com.oraclecloud.datascience.updatemodeldeployment.begin |
| Instance - Live Migration Begin | com.oraclecloud.computeapi.livemigrate.begin |
| Instance Console Connection - Delete Begin | com.oraclecloud.computeapi.deleteinstanceconsoleconnection.begin |
| External Non-Container Database - Enable Stack Monitoring Service End | com.oraclecloud.databaseservice.enablestackmonitoringforexternalnoncontainerdatabase.end |
| Protected Database - Delete End | com.oraclecloud.autonomousrecoveryservice.deleteprotecteddatabase.end |
| Audit Profile Retention Update - Begin | com.oraclecloud.datasafe.changeretention.begin |
| Deployment - Change Compartment End | com.oraclecloud.apigateway.changedeploymentcompartment.end |
| Preferences - Remove | com.oraclecloud.logginganalytics.removepreferences |
| Node - Stop End | com.oraclecloud.zerolatency.stopzerolatencynode.end |
| Exadb VM Cluster - Update Begin | com.oraclecloud.databaseservice.updateexadbvmcluster.begin |
| Autonomous Data Guard Association - Switchover Begin | com.oraclecloud.databaseservice.switchoverautonomousdataguardassociation.begin |
| Security Policy Configuration Create - Begin | com.oraclecloud.datasafe.createsecuritypolicyconfig.begin |
| Subscription - Delete | com.oraclecloud.notification.deletesubscription |
| VirtualServiceRouteTable - Update End | com.oraclecloud.servicemesh.updatevirtualserviceroutetable.end |
| App Configuration Update - Begin | com.oraclecloud.appconfiguration.updateappconfiguration.begin |
| Work Request - List Snaps End | com.oraclecloud.osmh.listsnaps.end |
| BuildRun - Update | com.oraclecloud.devopsbuild.updatebuildrun |
| Change Delegation Control Compartment - End | com.oraclecloud.delegateaccesscontrol.changedelegationcontrolcompartment.end |
| Service Instance - Start Server Begin | com.oraclecloud.zerolatency.starttimestenserver.begin |
| Audit Archive Retrieval Delete - Begin | com.oraclecloud.datasafe.deleteauditarchiveretrieval.begin |
| Unified Audit Policy Update - End | com.oraclecloud.datasafe.updateunifiedauditpolicy.end |
| Scheduled Job - Execute Scheduled Job Failed | com.oraclecloud.osmh.executescheduledjob.failed |
| Security Policy Update - Begin | com.oraclecloud.datasafe.updatesecuritypolicy.begin |
| Get Rpst - Delegated Resource Access Request | com.oraclecloud.delegateaccesscontrol.getdelegatedresourceaccessrequestrpst |
| Language - Detect Topic Labels | com.oraclecloud.aiservicelanguage.detectlanguagetopiclabels |
| Instance Pool - Attach Load Balancer Begin | com.oraclecloud.computemanagement.attachloadbalancer.begin |
| Gateway - Delete End | com.oraclecloud.apigateway.deletegateway.end |
| Instance - Stop Instance Begin | com.oraclecloud.blockchain.stopplatforminstance.begin |
| Application Data Platform - PodDb Backup End | com.oraclecloud.applicationdataplatform.createpoddbbackup.end |
| Audit Trail Collection Free Limit Warning | com.oraclecloud.datasafe.auditcollectionwarning |
| Sensitive Type Update - Begin | com.oraclecloud.datasafe.updatesensitivetype.begin |
| DHCP Options - Change Compartment | com.oraclecloud.virtualnetwork.changedhcpoptionscompartment |
| Update Alert Policy Rule - Begin | com.oraclecloud.datasafe.updatealertpolicyrule.begin |
| Global Autonomous Database - Validate Network End | com.oraclecloud.globaldb.validatenetwork.end |
| Lookup Data - Update | com.oraclecloud.logginganalytics.updatelookupdata |
| DeployArtifact - Create End | com.oraclecloud.devopsdeploy.createdeployartifact.end |
| VirtualService - Change Compartment End | com.oraclecloud.servicemesh.changevirtualservicecompartment.end |
| Exadb VM Cluster - Information | com.oraclecloud.databaseservice.exadbvmcluster.information |
| Exadb VM Cluster - Critical | com.oraclecloud.databaseservice.exadbvmcluster.critical |
| Autonomous Container Database - Add Standby End | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.createstandby.end |
| Autonomous Container Database - Reinstate End | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.reinstate.end |
| Database - Migrate to KMS Key End | com.oraclecloud.databaseservice.migratedatabasekmskey.end |
| Delete Global Accelerator SslCipherSuite Begin | com.oraclecloud.gax.public.api.deletesslciphersuite.begin |
| Autonomous Container Database - Switchover End | com.oraclecloud.databaseservice.autonomous.container.database.dataguard.switchover.end |
| Work Request - Install Packages Begin | com.oraclecloud.osmh.installpackages.begin |
| Work Request - Remove Packages Begin | com.oraclecloud.osmh.removepackages.begin |
| Cluster Namespace - Delete End | com.oraclecloud.mcp.deleteclusternamespace.end |
| Release Recalled Data - Begin | com.oraclecloud.logginganalytics.releaserecalleddata.begin |
| Disable Archiving | com.oraclecloud.logginganalytics.disablearchiving |
| Recall Archived Data - Begin | com.oraclecloud.logginganalytics.recallarchiveddata |
| Assign Encryption Key - End | com.oraclecloud.logginganalytics.assignencryptionkey.end |
| Purge Storage Data - Begin | com.oraclecloud.logginganalytics.purgestoragedata.begin |
| Assign Encryption Key - Begin | com.oraclecloud.logginganalytics.assignencryptionkey.begin |
| Release Recalled Data - End | com.oraclecloud.logginganalytics.releaserecalleddata.end |
| Enable Archiving | com.oraclecloud.logginganalytics.enablearchiving |
| Purge Storage Data - End | com.oraclecloud.logginganalytics.purgestoragedata.end |
| Recall Archived Data - End | com.oraclecloud.logginganalytics.recallarchiveddata.end |
| Masking Health Check Begin | com.oraclecloud.datasafe.generatehealthreport.begin |
| Security Assessment Baseline Template Findings Update - Begin | com.oraclecloud.datasafe.patchfindings.begin |
| Delete Target Database Group - Begin | com.oraclecloud.datasafe.deletetargetdatabasegroup.begin |
| Security Assessment Baseline Template Findings Update - End | com.oraclecloud.datasafe.patchfindings.end |
| Change Target Database Group Compartment - Begin | com.oraclecloud.datasafe.changetargetdatabasegroupcompartment.begin |
| Delete Security Assessment - Begin | com.oraclecloud.datasafe.deletesecurityassessment.begin |
| Masking Health Check Delete End | com.oraclecloud.datasafe.deletemaskingpolicyhealthreport.end |
| Sensitive Type Group Update - End | com.oraclecloud.datasafe.updatesensitivetypegroup.end |
| Create Target Database Group - End | com.oraclecloud.datasafe.createtargetdatabasegroup.end |
| Security Assessment Template Apply - Begin | com.oraclecloud.datasafe.applysecurityassessmenttemplate.begin |
| Update Target Database Group - End | com.oraclecloud.datasafe.updatetargetdatabasegroup.end |
| Create Target Database Group - Begin | com.oraclecloud.datasafe.createtargetdatabasegroup.begin |
| Target Database - State Change | com.oraclecloud.datasafe.statechangetargetdatabase |
| Sensitive Type Group Update - Begin | com.oraclecloud.datasafe.updatesensitivetypegroup.begin |
| Sensitive Type Group Patch - Begin | com.oraclecloud.datasafe.patchgroupedsensitivetypes.begin |
| Update Target Database Group - Begin | com.oraclecloud.datasafe.updatetargetdatabasegroup.begin |
| Security Assessment Template Checks Update - End | com.oraclecloud.datasafe.patchchecks.end |
| Security Assessment Template Remove - Begin | com.oraclecloud.datasafe.removesecurityassessmenttemplate.begin |
| Refresh Target Database Group - Begin | com.oraclecloud.datasafe.refreshtargetdatabasegroup.begin |
| Sensitive Type Group Patch - End | com.oraclecloud.datasafe.patchgroupedsensitivetypes.end |
| Security Assessment Template Checks Update - Begin | com.oraclecloud.datasafe.patchchecks.begin |
| Sensitive Type Group Delete - End | com.oraclecloud.datasafe.deletesensitivetypegroup.end |
| Masking Health Check End | com.oraclecloud.datasafe.generatehealthreport.end |
| Masking Health Check Delete Begin | com.oraclecloud.datasafe.deletemaskingpolicyhealthreport.begin |
| Delete Target Database Group - End | com.oraclecloud.datasafe.deletetargetdatabasegroup.end |
| Security Assessment Template Remove - End | com.oraclecloud.datasafe.removesecurityassessmenttemplate.end |
| Change Target Database Group Compartment - End | com.oraclecloud.datasafe.changetargetdatabasegroupcompartment.end |
| Security Assessment Template Apply - End | com.oraclecloud.datasafe.applysecurityassessmenttemplate.end |
| Sensitive Type Group Create - Begin | com.oraclecloud.datasafe.createsensitivetypegroup.begin |
| Refresh Target Database Group - End | com.oraclecloud.datasafe.refreshtargetdatabasegroup.end |
| Sensitive Type Group Create - End | com.oraclecloud.datasafe.createsensitivetypegroup.end |
| Delete Security Assessment - End | com.oraclecloud.datasafe.deletesecurityassessment.end |
| Sensitive Type Group Delete - Begin | com.oraclecloud.datasafe.deletesensitivetypegroup.begin |
| Managed Instance Group - Detach Managed Instances | com.oraclecloud.osmh.detachmanagedinstancesfrommanagedinstancegroup |
| Managed Instance Group - Attach Software Sources | com.oraclecloud.osmh.attachsoftwaresourcestomanagedinstancegroup |
| Scheduled Job - Update | com.oraclecloud.osmh.updatescheduledjob |
| Managed Instance - Update Packages | com.oraclecloud.osmh.updatepackagesonmanagedinstance |
| Managed Instance Group - Install Module Stream Profile | com.oraclecloud.osmh.installmodulestreamprofileonmanagedinstancegroup |
| Lifecycle Stage - Detach Managed Instances | com.oraclecloud.osmh.detachmanagedinstancesfromlifecyclestage |
| Managed Instance - Install Windows Updates | com.oraclecloud.osmh.installwindowsupdatesonmanagedinstance |
| Managed Instance - Remove Module Stream Profile | com.oraclecloud.osmh.removemodulestreamprofilefrommanagedinstance |
| Managed Instance Group - Delete | com.oraclecloud.osmh.deletemanagedinstancegroup |
| Managed Instance - Detach Software Sources | com.oraclecloud.osmh.detachsoftwaresourcesfrommanagedinstance |
| Managed Instance Group - Detach Software Sources | com.oraclecloud.osmh.detachsoftwaresourcesfrommanagedinstancegroup |
| Managed Instance - Update | com.oraclecloud.osmh.updatemanagedinstance |
| Managed Instance Group - Attach Managed Instances | com.oraclecloud.osmh.attachmanagedinstancestomanagedinstancegroup |
| Managed Instance - Attach Profile | com.oraclecloud.osmh.attachprofiletomanagedinstance |
| Managed Instance - Update All Packages | com.oraclecloud.osmh.updateallpackagesonmanagedinstancesincompartment |
| Managed Instance - Install Module Stream Profile | com.oraclecloud.osmh.installmodulestreamprofileonmanagedinstance |
| Scheduled Job - Run Now | com.oraclecloud.osmh.runscheduledjobnow |
| Lifecycle Environment - Update | com.oraclecloud.osmh.updatelifecycleenvironment |
| Software Sources - Change Availability | com.oraclecloud.osmh.changeavailabilityofsoftwaresources |
| Lifecycle Stage - Attach Managed Instances | com.oraclecloud.osmh.attachmanagedinstancestolifecyclestage |
| Scheduled Job - Change Compartment | com.oraclecloud.osmh.changescheduledjobcompartment |
| Managed Instance - Manage Module Stream | com.oraclecloud.osmh.managemodulestreamsonmanagedinstance |
| Managed Instance Group - Create | com.oraclecloud.osmh.createmanagedinstancegroup |
| Managed Instance - Install All Windows Updates | com.oraclecloud.osmh.installallwindowsupdatesonmanagedinstancesincompartment |
| Software Sources - Create | com.oraclecloud.osmh.createsoftwaresource |
| Lifecycle Environment - Create | com.oraclecloud.osmh.createlifecycleenvironment |
| Managed Instance Group - Install Packages | com.oraclecloud.osmh.installpackagesonmanagedinstancegroup |
| Managed Instance - Refresh Software Sources | com.oraclecloud.osmh.refreshsoftwareonmanagedinstance |
| Managed Instance Group - Update | com.oraclecloud.osmh.updatemanagedinstancegroup |
| Managed Instance - Delete | com.oraclecloud.osmh.deletemanagedinstance |
| Scheduled Job - Create | com.oraclecloud.osmh.createscheduledjob |
| Software Sources - Update | com.oraclecloud.osmh.updatesoftwaresource |
| Managed Instance Group - Update All Packages | com.oraclecloud.osmh.updateallpackagesonmanagedinstancegroup |
| Managed Instance Group - Change Compartment | com.oraclecloud.osmh.changemanagedinstancegroupcompartment |
| Lifecycle Environment - Delete | com.oraclecloud.osmh.deletelifecycleenvironment |
| Lifecycle Stage - Promote Software Source | com.oraclecloud.osmh.promotesoftwaresourcetolifecyclestage |
| Managed Instance Group - Remove Module Stream Profile | com.oraclecloud.osmh.removemodulestreamprofilefrommanagedinstancegroup |
| Managed Instance Group - Remove Packages | com.oraclecloud.osmh.removepackagesfrommanagedinstancegroup |
| Software Sources - Add Packages | com.oraclecloud.osmh.addpackagestosoftwaresource |
| Software Source - Delete | com.oraclecloud.osmh.deletesoftwaresource |
| Managed Instance - Install Packages | com.oraclecloud.osmh.installpackagesonmanagedinstance |
| Managed Instance - Remove Packages | com.oraclecloud.osmh.removepackagesfrommanagedinstance |
| Managed Instance - Attach Software Sources | com.oraclecloud.osmh.attachsoftwaresourcestomanagedinstance |
| Managed Instance - Switch Module Stream | com.oraclecloud.osmh.switchmodulestreamonmanagedinstance |
| Managed Instance - Disable Module Stream | com.oraclecloud.osmh.disablemodulestreamonmanagedinstance |
| Software Sources - Change Compartment | com.oraclecloud.osmh.changesoftwaresourcecompartment |
| Scheduled Job - Delete | com.oraclecloud.osmh.deletescheduledjob |
| Managed Instance - Enable Module Stream | com.oraclecloud.osmh.enablemodulestreamonmanagedinstance |
| Masking Report Delete - Begin | com.oraclecloud.datasafe.deletemaskingreport.begin |
| Sensitive Types Export Create - End | com.oraclecloud.datasafe.createsensitivetypesexport.end |
| Masking Report Delete - End | com.oraclecloud.datasafe.deletemaskingreport.end |
| Sensitive Types Export Update - End | com.oraclecloud.datasafe.updatesensitivetypesexport.end |
| Sensitive Types Export Update - Begin | com.oraclecloud.datasafe.updatesensitivetypesexport.begin |
| Sensitive Types Export Create - Begin | com.oraclecloud.datasafe.createsensitivetypesexport.begin |
| Managed Instance Group - Disable Module Stream | com.oraclecloud.osmh.disablemodulestreamonmanagedinstancegroup |
| Managed Instance Group - Enable Module Stream | com.oraclecloud.osmh.enablemodulestreamonmanagedinstancegroup |
| Cluster Namespace Profile - Delete End | com.oraclecloud.mcp.deleteclusternamespaceprofile.end |
| Cluster Namespace Profile - Create Begin | com.oraclecloud.mcp.createclusternamespaceprofile.begin |
| Cluster Attachment - Create Begin | com.oraclecloud.mcp.createclusterattachment.begin |
| Cluster Namespace Profile Version - Delete Begin | com.oraclecloud.mcp.deleteclusternamespaceprofileversion.begin |
| Cluster Namespace Profile Version - Create End | com.oraclecloud.mcp.createclusternamespaceprofileversion.end |
| Cluster Namespace - Create End | com.oraclecloud.mcp.createclusternamespace.end |
| Cluster Namespace Profile Version - Update Begin | com.oraclecloud.mcp.updateclusternamespaceprofileversion.begin |
| Cluster Namespace Profile - Create End | com.oraclecloud.mcp.createclusternamespaceprofile.end |
| Cluster Attachment - Update Begin | com.oraclecloud.mcp.updateclusterattachment.begin |
| Cluster Attachment - Create End | com.oraclecloud.mcp.createclusterattachment.end |
| Cluster Namespace - Delete Begin | com.oraclecloud.mcp.deleteclusternamespace.begin |
| Cluster Namespace Profile - Update Begin | com.oraclecloud.mcp.updateclusternamespaceprofile.begin |
| Cluster Attachment - Update End | com.oraclecloud.mcp.updateclusterattachment.end |
| Cluster Namespace Profile Version - Create Begin | com.oraclecloud.mcp.createclusternamespaceprofileversion.begin |
| Cluster Namespace Profile Version - Update End | com.oraclecloud.mcp.updateclusternamespaceprofileversion.end |
| Cluster Namespace - Create Begin | com.oraclecloud.mcp.createclusternamespace.begin |
| Cluster Attachment - Delete Begin | com.oraclecloud.mcp.deleteclusterattachment.begin |
| Cluster Attachment - Delete End | com.oraclecloud.mcp.deleteclusterattachment.end |
| Cluster Namespace Profile - Update End | com.oraclecloud.mcp.updateclusternamespaceprofile.end |
| Cluster Namespace - Update End | com.oraclecloud.mcp.updateclusternamespace.end |
| Cluster Namespace - Update Begin | com.oraclecloud.mcp.updateclusternamespace.begin |
| Cluster Namespace Profile - Delete Begin | com.oraclecloud.mcp.deleteclusternamespaceprofile.begin |
| Cluster Namespace Profile Version - Delete End | com.oraclecloud.mcp.deleteclusternamespaceprofileversion.end |
| Create Global Accelerator SslCipherSuite Begin | com.oraclecloud.gax.public.api.createsslciphersuite.begin |
| Work Request - Install Packages End | com.oraclecloud.osmh.installpackages.end |
| Cloud Exadata Infrastructure - Update End | com.oraclecloud.databaseservice.updatecloudexadatainfrastructure.end |
| External Pluggable Database - Change Compartment Begin | com.oraclecloud.databaseservice.changeexternalpluggabledatabasecompartment.begin |
| Cloud Exadata Infrastructure - VM Maintenance End | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancevm.end |
| Cloud Exadata Infrastructure - Maintenance End | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenance.end |
| ML Application Implementation - Change compartment End | com.oraclecloud.datascience.changemlapplicationimplementationcompartment.end |
| Cloud Exadata Infrastructure - Maintenance Begin | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenance.begin |
| ML Application - Delete End | com.oraclecloud.datascience.deletemlapplication.end |
| Autonomous Database - Free Database Automatic Stop Reminder | com.oraclecloud.databaseservice.freeautonomousdatabasestopreminder |
| ML Application Implementation- Create | com.oraclecloud.datascience.createmlapplicationimplementation |
| External Pluggable Database - Disable Database Management Service End | com.oraclecloud.databaseservice.disabledatabasemanagementserviceforexternalpluggabledatabase.end |
| External Container Database - Scan Pluggable Databases Begin | com.oraclecloud.databaseservice.scanexternalcontainerdatabasepluggabledatabases.begin |
| Database - Rotate KMS Key Begin | com.oraclecloud.databaseservice.rotatedatabasekmskey.begin |
| Application Virtual IP (VIP) - Create End | com.oraclecloud.databaseservice.createapplicationvip.end |
| DB Home - Update End | com.oraclecloud.databaseservice.updatedbhome.end |
| ExaCompute VmAction - Refresh Smart NicInfo | com.oraclecloud.exacompute.exacomputevmactionrefreshsmartnicinfo |
| External Database Connector - Create Begin | com.oraclecloud.databaseservice.createexternaldatabaseconnector.begin |
| Update Global Accelerator Backend End | com.oraclecloud.gax.public.api.updatebackend.end |
| ML Application Instance View - Update | com.oraclecloud.datascience.updatemlapplicationinstanceview |
| ExaCompute VmInstance - Generate SshKey | com.oraclecloud.exacompute.generatexxacomputevminstancesshkey |
| Cloud VM Cluster - Terminate Virtual Machine End | com.oraclecloud.databaseservice.cloudvmclusterterminatevirtualmachine.end |
| External Database Connector - Delete Begin | com.oraclecloud.databaseservice.deleteexternaldatabaseconnector.begin |
| External Database Connector - Delete End | com.oraclecloud.databaseservice.deleteexternaldatabaseconnector.end |
| Autonomous Database - Rename End | com.oraclecloud.databaseservice.renameautonomousdatabase.end |
| Autonomous Database - Free Database Automatic Termination Reminder | com.oraclecloud.databaseservice.freeautonomousdatabaseterminationreminder |
| ML Application Implementation - Update Begin | com.oraclecloud.datascience.updatemlapplicationimplementation.begin |
| Autonomous Database - Auto Scaling Enabled | com.oraclecloud.databaseservice.autonomousdatabaseautoscaleenabled |
| Cloud Exadata Infrastructure - DB Server Maintenance Begin | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancedbserver.begin |
| Database - Rotate KMS Key End | com.oraclecloud.databaseservice.rotatedatabasekmskey.end |
| Data Guard Association - Create Begin | com.oraclecloud.databaseservice.createdataguardassociation.begin |
| ExaCompute VmInstance - Update | com.oraclecloud.exacompute.updateexacomputevminstance |
| Cancel Global Accelerator WorkRequest | com.oraclecloud.gax.public.api.cancelworkrequest |
| Cloud VM Cluster - Update Begin | com.oraclecloud.databaseservice.updatecloudvmcluster.begin |
| DB System - Terminate End | com.oraclecloud.databaseservice.terminatedbsystem.end |
| External Pluggable Database - Create | com.oraclecloud.databaseservice.createexternalpluggabledatabase |
| ML Application Instance - Update Begin | com.oraclecloud.datascience.updatemlapplicationinstance.begin |
| External Non-Container Database - Delete End | com.oraclecloud.databaseservice.deleteexternalnoncontainerdatabase.end |
| DB System - Terminate Begin | com.oraclecloud.databaseservice.terminatedbsystem.begin |
| External Non-Container Database - Update End | com.oraclecloud.databaseservice.updateexternalnoncontainerdatabase.end |
| ML Application Instance - Create End | com.oraclecloud.datascience.createmlapplicationinstance.end |
| ML Application - Delete Begin | com.oraclecloud.datascience.deletemlapplication.begin |
| Create Global Accelerator BackendSet Begin | com.oraclecloud.gax.public.api.createbackendset.begin |
| ML Application Implementation - Delete End | com.oraclecloud.datascience.deletemlapplicationimplementation.end |
| Autonomous Database - Start Begin | com.oraclecloud.databaseservice.startautonomousdatabase.begin |
| Autonomous Database - Restart Begin | com.oraclecloud.databaseservice.restartautonomousdatabase.begin |
| Autonomous Database - Manual Refresh End | com.oraclecloud.databaseservice.manualrefresh.end |
| Update Global Accelerator SslCipherSuite Begin | com.oraclecloud.gax.public.api.updatesslciphersuite.begin |
| ML Application Instance - Delete End | com.oraclecloud.datascience.deletemlapplicationinstance.end |
| External Container Database - Enable Database Management Service End | com.oraclecloud.databaseservice.enabledatabasemanagementserviceforexternalcontainerdatabase.end |
| Exadata Infrastructure - Maintenance Rescheduled | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancerescheduled |
| Exadata Infrastructure - Virtual Machines Maintenance Begin | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancevm.begin |
| Exadata Infrastructure - Virtual Machines Maintenance End | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancevm.end |
| Exadata Infrastructure - Database Server Maintenance Begin | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancedbserver.begin |
| Exadata Infrastructure - Database Server Maintenance End | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancedbserver.end |
| Exadata Infrastructure - Maintenance Reminder | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancereminder |
| Exadata Infrastructure - Maintenance Scheduled | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancescheduled |
| Exadata Infrastructure - Maintenance Begin | com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.begin |
| Exadata Infrastructure - Maintenance End | com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.end |
| Cloud Exadata Infrastructure - Maintenance Reminder | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancereminder |
| Exadata Infrastructure - Maintenance Method Change | com.oraclecloud.databaseservice.exaccinfrastructuremaintenancemethodchange |
| Delete Global Accelerator Backend Begin | com.oraclecloud.gax.public.api.deletebackend.begin |
| Pluggable Database - Create Begin | com.oraclecloud.databaseservice.createpluggabledatabase.begin |
| External Database Connector - Update Begin | com.oraclecloud.databaseservice.updateexternaldatabaseconnector.begin |
| Autonomous Database - Scheduled Stop Autonomous Database End | com.oraclecloud.databaseservice.scheduledstopautonomousdatabase.end |
| Autonomous Database - Stop End | com.oraclecloud.databaseservice.stopautonomousdatabase.end |
| External Container Database - Disable Database Management Service Begin | com.oraclecloud.databaseservice.disabledatabasemanagementserviceforexternalcontainerdatabase.begin |
| Data Guard Association - Failover Begin | com.oraclecloud.databaseservice.failoverdataguardassociation.begin |
| Cloud VM Cluster - Create Begin | com.oraclecloud.databaseservice.createcloudvmcluster.begin |
| Start Pluggable Database - End | com.oraclecloud.databaseservice.startpluggabledatabase.end |
| Cloud Exadata Infrastructure - Update Begin | com.oraclecloud.databaseservice.updatecloudexadatainfrastructure.begin |
| ML Application Instance View - Change compartment End | com.oraclecloud.datascience.changemlapplicationinstanceviewcompartment.end |
| Cloud Exadata Infrastructure - Maintenance Method Change | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancemethodchange |
| Autonomous Container Database - Restart End | com.oraclecloud.databaseservice.restartautonomouscontainerdatabase.end |
| External Non-Container Database - Disable Database Management Service Begin | com.oraclecloud.databaseservice.disabledatabasemanagementserviceforexternalnoncontainerdatabase.begin |
| Autonomous Database - Terminate Begin | com.oraclecloud.databaseservice.deleteautonomousdatabase.begin |
| Cloud Exadata Infrastructure - Maintenance Scheduled | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancescheduled |
| Cloud VM Cluster - Update IORM Configuration End | com.oraclecloud.databaseservice.updatecloudvmclusteriormconfig.end |
| DB System - Update Begin | com.oraclecloud.databaseservice.updatedbsystem.begin |
| Cloud VM Cluster - Change Compartment Begin | com.oraclecloud.databaseservice.changecloudvmclustercompartment.begin |
| Pluggable Database - Create End | com.oraclecloud.databaseservice.createpluggabledatabase.end |
| Autonomous Database - Patch Level Update End | com.oraclecloud.databaseservice.updateautonomousdatabasepatchlevel.end |
| Autonomous Database - Scheduled Start Autonomous Database End | com.oraclecloud.databaseservice.scheduledstartautonomousdatabase.end |
| Autonomous Database -Patch Level Update Begin | com.oraclecloud.databaseservice.updateautonomousdatabasepatchlevel.begin |
| Autonomous Database - Rename Begin | com.oraclecloud.databaseservice.renameautonomousdatabase.begin |
| Application Virtual IP (VIP) - Delete Begin | com.oraclecloud.databaseservice.deleteapplicationvip.begin |
| ML Application Instance View - Trigger End | com.oraclecloud.datascience.triggermlapplicationinstanceviewflow.end |
| Put ML Application Package | com.oraclecloud.datascience.putmlapplicationpackage |
| Data Guard Association - Reinstate Begin | com.oraclecloud.databaseservice.reinstatedataguardassociation.begin |
| Database - Create Backup Begin | com.oraclecloud.databaseservice.backupdatabase.begin |
| Autonomous Database - Manual Refresh Begin | com.oraclecloud.databaseservice.manualrefresh.begin |
| Cloud VM Cluster - Add Virtual Machine Begin | com.oraclecloud.databaseservice.cloudvmclusteraddvirtualmachine.begin |
| ML Application Implementation - Delete Begin | com.oraclecloud.datascience.deletemlapplicationimplementation.begin |
| ML Application Instance - Update End | com.oraclecloud.datascience.updatemlapplicationinstance.end |
| Delete Global Accelerator SslCipherSuite End | com.oraclecloud.gax.public.api.deletesslciphersuite.end |
| Cloud Exadata Infrastructure - IB Switch Maintenance End | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenanceibswitch.end |
| Autonomous Database - Free Database Automatically Terminated | com.oraclecloud.databaseservice.freeautonomousdatabaseterminated |
| External Pluggable Database - Enable Database Management Service Begin | com.oraclecloud.databaseservice.enabledatabasemanagementserviceforexternalpluggabledatabase.begin |
| Pluggable Database - Delete Begin | com.oraclecloud.databaseservice.deletepluggabledatabase.begin |
| Security Assessment Compare - Begin | com.oraclecloud.datasafe.comparesecurityassessment.begin |
| Distributed Autonomous Database - Add GDSCTL Node End | com.oraclecloud.globaldb.adddistributedautonomousdatabasegdscontrolnode.end |
| Cloud Exadata Infrastructure - Storage Server Maintenance End | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancestorageservers.end |
| Create Global Accelerator Backend Begin | com.oraclecloud.gax.public.api.createbackend.begin |
| Database - Delete Backup Begin | com.oraclecloud.databaseservice.deletebackup.begin |
| Update Global Accelerator SslCipherSuite End | com.oraclecloud.gax.public.api.updatesslciphersuite.end |
| External Container Database - Enable Database Management Service Begin | com.oraclecloud.databaseservice.enabledatabasemanagementserviceforexternalcontainerdatabase.begin |
| Cloud Exadata Infrastructure - Change Compartment Begin | com.oraclecloud.databaseservice.changecloudexadatainfrastructurecompartment.begin |
| External Non-Container Database - Update Begin | com.oraclecloud.databaseservice.updateexternalnoncontainerdatabase.begin |
| Autonomous Database - Generate Wallet | com.oraclecloud.databaseservice.generateautonomousdatabasewallet |
| External Container Database - Delete End | com.oraclecloud.databaseservice.deleteexternalcontainerdatabase.end |
| DB System - Update IORM End | com.oraclecloud.databaseservice.updateiormconfig.end |
| Pluggable Database - Remote Clone End | com.oraclecloud.databaseservice.pluggabledatabase.remoteclone.end |
| Autonomous Database - Start End | com.oraclecloud.databaseservice.startautonomousdatabase.end |
| Autonomous Database - Restart End | com.oraclecloud.databaseservice.restartautonomousdatabase.end |
| Autonomous Database - Update BackUp Retention Period End | com.oraclecloud.databaseservice.updateautonomousdatabasebackupretentionperiod.end |
| Autonomous Database - Update Schedule Time For Db Version Upgrade End | com.oraclecloud.databaseservice.updatescheduledtimefordbupgrade.end |
| ML Application Instance View - Recover End | com.oraclecloud.datascience.recovermlapplicationinstanceview.end |
| Update Global Accelerator Backend Begin | com.oraclecloud.gax.public.api.updatebackend.begin |
| Enable ML Application Instance View Trigger | com.oraclecloud.datascience.enablemlapplicationinstanceviewtrigger |
| External Container Database - Update End | com.oraclecloud.databaseservice.updateexternalcontainerdatabase.end |
| External Pluggable Database - Enable Database Management Service End | com.oraclecloud.databaseservice.enabledatabasemanagementserviceforexternalpluggabledatabase.end |
| Autonomous Database - Scheduled Start Autonomous Database Begin | com.oraclecloud.databaseservice.scheduledstartautonomousdatabase.begin |
| Autonomous Database - Update BackUp Retention Period Begin | com.oraclecloud.databaseservice.updateautonomousdatabasebackupretentionperiod.begin |
| Autonomous Database - Update Schedule Time For Db Version Upgrade Begin | com.oraclecloud.databaseservice.updatescheduledtimefordbupgrade.begin |
| Autonomous Database - Scheduled Stop Autonomous Database Begin | com.oraclecloud.databaseservice.scheduledstopautonomousdatabase.begin |
| Cloud Exadata Infrastructure - Maintenance Rescheduled With Reason | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancerescheduledwithreason |
| Create Global Accelerator BackendSet End | com.oraclecloud.gax.public.api.createbackendset.end |
| Update Global Accelerator BackendSet Begin | com.oraclecloud.gax.public.api.updatebackendset.begin |
| External Non-Container Database - Delete Begin | com.oraclecloud.databaseservice.deleteexternalnoncontainerdatabase.begin |
| Data Guard Association - Switchover End | com.oraclecloud.databaseservice.switchoverdataguardassociation.end |
| Stop Pluggable Database - Begin | com.oraclecloud.databaseservice.stoppluggabledatabase.begin |
| ML Application Instance View - Change compartment Begin | com.oraclecloud.datascience.changemlapplicationinstanceviewcompartment.begin |
| Cloud Exadata Infrastructure - Create End | com.oraclecloud.databaseservice.createcloudexadatainfrastructure.end |
| ML Application Instance View - Trigger Begin | com.oraclecloud.datascience.triggermlapplicationinstanceviewflow.begin |
| Cloud VM Cluster - Update End | com.oraclecloud.databaseservice.updatecloudvmcluster.end |
| Create Global Accelerator Backend End | com.oraclecloud.gax.public.api.createbackend.end |
| DB Home - Update Begin | com.oraclecloud.databaseservice.updatedbhome.begin |
| Pluggable Database - Delete End | com.oraclecloud.databaseservice.deletepluggabledatabase.end |
| Create Global Accelerator SslCipherSuite End | com.oraclecloud.gax.public.api.createsslciphersuite.end |
| Disable ML Application Instance View Trigger | com.oraclecloud.datascience.disablemlapplicationinstanceviewtrigger |
| External Non-Container Database - Change Compartment Begin | com.oraclecloud.databaseservice.changeexternalnoncontainerdatabasecompartment.begin |
| Cloud Exadata Infrastructure - Delete Begin | com.oraclecloud.databaseservice.deletecloudexadatainfrastructure.begin |
| Cloud VM Cluster - Add Virtual Machine End | com.oraclecloud.databaseservice.cloudvmclusteraddvirtualmachine.end |
| Cloud Exadata Infrastructure - Maintenance Custom Action Time Out Begin | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenancecustomactiontime.begin |
| Pluggable Database - Local Clone Begin | com.oraclecloud.databaseservice.pluggabledatabase.localclone.begin |
| ML Application Instance - Change compartment Begin | com.oraclecloud.datascience.changemlapplicationinstancecompartment.begin |
| Autonomous Database - Update Compute Model End | com.oraclecloud.databaseservice.updateautonomousdatabasecomputemodel.end |
| Stop Pluggable Database - End | com.oraclecloud.databaseservice.stoppluggabledatabase.end |
| Cloud Exadata Infrastructure - IB Switch Maintenance Begin | com.oraclecloud.databaseservice.cloudexadatainfrastructuremaintenanceibswitch.begin |
| Start Pluggable Database - Begin | com.oraclecloud.databaseservice.startpluggabledatabase.begin |
| Delete Global Accelerator Backend End | com.oraclecloud.gax.public.api.deletebackend.end |
| Pluggable Database - Local Clone End | com.oraclecloud.databaseservice.pluggabledatabase.localclone.end |
| External Container Database - Update Begin | com.oraclecloud.databaseservice.updateexternalcontainerdatabase.begin |
| Autonomous Container Database - Restart Begin | com.oraclecloud.databaseservice.restartautonomouscontainerdatabase.begin |
| ML Application - Create | com.oraclecloud.datascience.createmlapplication |
| Autonomous Container Database - Terminate End | com.oraclecloud.databaseservice.terminateautonomouscontainerdatabase.end |
| External Container Database - Create | com.oraclecloud.databaseservice.createexternalcontainerdatabase |
| DB System - Update End | com.oraclecloud.databaseservice.updatedbsystem.end |
| Database - Delete Backup End | com.oraclecloud.databaseservice.deletebackup.end |
| Autonomous Database - Stop Begin | com.oraclecloud.databaseservice.stopautonomousdatabase.begin |
| ML Application - Update | com.oraclecloud.datascience.updatemlapplication |
| Data Guard Association - Switchover Begin | com.oraclecloud.databaseservice.switchoverdataguardassociation.begin |
| Autonomous Database - Update Begin | com.oraclecloud.databaseservice.updateautonomousdatabase.begin |
| Cloud VM Cluster - Delete End | com.oraclecloud.databaseservice.deletecloudvmcluster.end |
| Autonomous Database - Register Autonomous Database With Datasafe | com.oraclecloud.databaseservice.deregisterautonomousdatabasedatasafe.end |
| Autonomous Database - Auto Scaling Disabled | com.oraclecloud.databaseservice.autonomousdatabaseautoscaledisabled |
| Autonomous Database - Register Autonomous Database With Datasafe | com.oraclecloud.databaseservice.registerautonomousdatabasedatasafe.end |
| Autonomous Database - Register Autonomous Database With Datasafe | com.oraclecloud.databaseservice.registerautonomousdatabasedatasafe.begin |
| Autonomous Database - Deregister Autonomous Database With Datasafe | com.oraclecloud.databaseservice.deregisterautonomousdatabasedatasafe.begin |
| Data Guard Association - Reinstate End | com.oraclecloud.databaseservice.reinstatedataguardassociation.end |
| Autonomous Container Database - Change Compartment | com.oraclecloud.databaseservice.changeautonomouscontainerdatabasecompartment |
| Cloud Exadata Infrastructure - Configure Exascale Begin | com.oraclecloud.databaseservice.configureexascalecloudexadatainfrastructure.begin |
| Cloud Exadata Infrastructure - Configure Exascale End | com.oraclecloud.databaseservice.configureexascalecloudexadatainfrastructure.end |
| Cloud Exadata Infrastructure - Add Storage Capacity Begin | com.oraclecloud.databaseservice.addstoragecapacitycloudexadatainfrastructure.begin |
| External Pluggable Database - Update End | com.oraclecloud.databaseservice.updateexternalpluggabledatabase.end |
| Autonomous Database - Change Compartment End | com.oraclecloud.databaseservice.changeautonomousdatabasecompartment.end |
| Cloud VM Cluster - Update IORM Configuration Begin | com.oraclecloud.databaseservice.updatecloudvmclusteriormconfig.begin |
| Database - Migrate to KMS Key Begin | com.oraclecloud.databaseservice.migratedatabasekmskey.begin |
