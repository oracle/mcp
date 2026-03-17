# JMS Tool Test Report

Date: 2026-03-17

Target fleet:

```text
ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq
```

Target compartment:

```text
ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq
```

This report was produced from a live rerun of all 9 JMS tools through `fastmcp.Client(mcp)`.

## 1. `list_fleets`

Status: `ok`

Input:

```json
{
  "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
  "sort_order": "ASC",
  "sort_by": "displayName",
  "limit": 10
}
```

Output:

```json
[
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguia7iry2zw5zygfmqejmaessuuzbll2im7kdqxgp5rwgzna",
    "display_name": "Test2",
    "description": "Test2",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiavs2et3qpq2klmgurnigpbqya3sbr5m3otqntlzgupk6a",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiaj3zfojeftftvgji2mw4fu7smsfz2g2d43fyx2lmu66da"
    },
    "operation_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiavs2et3qpq2klmgurnigpbqya3sbr5m3otqntlzgupk6a",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiajoc4aj43veuw6fpvqymbi5fxiki62ekpwmwy3ldp3ada"
    },
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2026-02-10T09:27:25.338000Z",
    "lifecycle_state": "FAILED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "kwickram",
        "CreatedOn": "2026-02-10T09:27:24.860Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguia3txn7ennnkfbdzlceq4j5nyj5s4z7piy7c4icbn6prfa",
    "display_name": "auto-move-managed-instance-A",
    "description": "autotest fleet",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguia7uexc2le75lji7xl26qjrpkqnzqv7sszlmouktxcbi7q",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiazf652yp5zdpmbr4s7narowmw3nyap2jykdxy4z4lx2gq"
    },
    "operation_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguia7uexc2le75lji7xl26qjrpkqnzqv7sszlmouktxcbi7q",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiath6unzwkgzlgqarrguaborwbam6husaexgfhfh4gip3a"
    },
    "is_advanced_features_enabled": false,
    "is_export_setting_enabled": false,
    "time_created": "2023-06-08T16:12:37.330000Z",
    "lifecycle_state": "FAILED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "klevytsk",
        "CreatedOn": "2023-06-08T16:12:36.173Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguialuyracd2pi6zqjxg2z5n2i7lv5ywkrjjwkfhavpi6twa",
    "display_name": "fleet-20250613-1315",
    "description": "Test fleet created by SQE",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiaunp4y53xiohb5hqvasykcqdjroukjnhvfaexyqqixwfq",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiavnauazecrpuf7s5o4vzfxygzy2e2uefp2ll5kkiimgpq"
    },
    "operation_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiaunp4y53xiohb5hqvasykcqdjroukjnhvfaexyqqixwfq",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiaejedobtl2mmcx4biucxr46lqiehtbshjqnnt46zmsifa"
    },
    "is_advanced_features_enabled": false,
    "is_export_setting_enabled": false,
    "time_created": "2025-06-13T05:15:46.987000Z",
    "lifecycle_state": "FAILED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "kwickram",
        "CreatedOn": "2025-06-13T05:15:46.402Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiaovou2nqghvburhlmoy42gzk62vvtzak4zzz2i5nhlmxa",
    "display_name": "fleet-20251014-0910_test-incubator_canary",
    "description": "Testing fleet-20251014-0910_test-incubator_canary",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiabmgw3bckpm63xiujmh6fkmkdwqiu4s23mytbx767j6eq",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiad4ltos3e6vgjwu7imnqiyv46li7i6ekgbjxys4ki2z2a"
    },
    "operation_log": null,
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2025-10-14T09:12:34.940000Z",
    "lifecycle_state": "FAILED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "jmstest-canaryuser-iad",
        "CreatedOn": "2025-10-14T09:12:34.660Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiatzxyg3gkpuwcqffkpaiwminrjxtxdyduwbhnrlwsi3hq",
    "display_name": "fleet-20251016-1325_test-null_canary",
    "description": "Testing fleet-20251016-1325_test-null_canary",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiayml34lgbdsqxadrtei5hzxkmkg3sxcannmjytx6e4dla",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguia55hr5yvk4zfxcremzz6q24grrsjocsj2vcs6lkr3toka"
    },
    "operation_log": null,
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2025-10-16T13:25:52.653000Z",
    "lifecycle_state": "FAILED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "jmstest-canaryuser-iad",
        "CreatedOn": "2025-10-16T13:25:52.110Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiaxjjqturjxfb7ffgiwe7ozx2qomqftw55swvv6e2nvllq",
    "display_name": "fleet-20251017-0834_test-null_canary",
    "description": "Testing fleet-20251017-0834_test-null_canary",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguia7yo6e5f6pw5hpylhfsiro5lwh7ps5rj3ue7jclwlkm2a",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguia7olcl6ppvivnqtpilylgtaemtszmsmgppozf5t7qapfq"
    },
    "operation_log": null,
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2025-10-17T08:34:59.591000Z",
    "lifecycle_state": "FAILED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "jmstest-canaryuser-iad",
        "CreatedOn": "2025-10-17T08:34:59.345Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiame4obzlb2r4micfk7vr5qhjdjaxb5s62a4ehmdqrneaq",
    "display_name": "fleet-20251216-0835_test-null_canary",
    "description": "Testing fleet-20251216-0835_test-null_canary",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiao2v4e5xec4yeu5zo46bfwwgbqm7ntfnwmj7mdyio2t3a",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguia3g2ogwthju5jsvef2qipkl7dv2ufym63eyhkzhhtugxq"
    },
    "operation_log": null,
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2025-12-16T08:35:37.365000Z",
    "lifecycle_state": "DELETED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "jmstest-canaryuser-iad",
        "CreatedOn": "2025-12-16T08:35:37.100Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiarvjb6ikdnmwgy27wvx6gyzszcpp2qn23k4mnhnjyzk6a",
    "display_name": "fleet-20251216-1434_test-null_canary",
    "description": "Testing fleet-20251216-1434_test-null_canary",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiaked7r3fqtylyru2zosqdmigywgajqcwqv4j7o2ehpofq",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiawezvurunu63y534hjza5e6ebcy56kfe2z4rgx3cb4yfq"
    },
    "operation_log": null,
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2025-12-16T14:34:38.887000Z",
    "lifecycle_state": "DELETED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "jmstest-canaryuser-iad",
        "CreatedOn": "2025-12-16T14:34:38.639Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguial2nqjd7hahr5qz2laytp2qcnjfcjmcjsylhrh4egwaia",
    "display_name": "fleet-20251216-2034_test-null_canary",
    "description": "Testing fleet-20251216-2034_test-null_canary",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiacugfanyfx7rnaq6wcngvdkp7t7lqjxjlfdfkrwqvrn2a",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiatep563wid7ucmpjavtsmi4v35uv6myiu4bu2dlcol2jq"
    },
    "operation_log": null,
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2025-12-16T20:34:51.004000Z",
    "lifecycle_state": "DELETED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "jmstest-canaryuser-iad",
        "CreatedOn": "2025-12-16T20:34:50.735Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiahxduzprvifslhei6lczre6axawn7pou5hx6h5l7d2pva",
    "display_name": "fleet-20251217-0234_test-null_canary",
    "description": "Testing fleet-20251217-0234_test-null_canary",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": null,
    "approximate_library_vulnerability_count": null,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguiay2c6dklzrc4gg3epv4v4vjedcug4t5b3kvx23yzsayba",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiak4g3fucg7xvgun63tlu44bubw22rzx3ycxdn3zykx3sa"
    },
    "operation_log": null,
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2025-12-17T02:34:31.877000Z",
    "lifecycle_state": "DELETED",
    "defined_tags": {
      "Oracle-Tags": {
        "CreatedBy": "jmstest-canaryuser-iad",
        "CreatedOn": "2025-12-17T02:34:31.584Z"
      }
    },
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  }
]
```

## 2. `get_fleet`

Status: `ok`

Input:

```json
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq"
}
```

Output:

```json
{
  "id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq",
  "display_name": "jms10-bpn-k8s",
  "description": "JMS 10 Test Fleet",
  "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
  "approximate_jre_count": 0,
  "approximate_installation_count": 0,
  "approximate_application_count": 0,
  "approximate_managed_instance_count": 0,
  "approximate_java_server_count": 0,
  "approximate_library_count": null,
  "approximate_library_vulnerability_count": null,
  "inventory_log": {
    "namespace": null,
    "bucket_name": null,
    "object_name": null,
    "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguia2k7mytdyr4gmci4pklhmsm4ftb5uwecr3q2ep5jzfiuq",
    "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguian5ex7u5otwik5adoq6n65fbbwdu6yfarknbzo4uyyxma"
  },
  "operation_log": {
    "namespace": null,
    "bucket_name": null,
    "object_name": null,
    "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguia2k7mytdyr4gmci4pklhmsm4ftb5uwecr3q2ep5jzfiuq",
    "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguiaxmmcot7l6pynst3mc3d6abrvc3ol6qd7fv3rkp4f66fq"
  },
  "is_advanced_features_enabled": true,
  "is_export_setting_enabled": false,
  "time_created": "2025-09-25T09:42:20.123000Z",
  "lifecycle_state": "FAILED",
  "defined_tags": {
    "Oracle-Tags": {
      "CreatedBy": "bbanathu",
      "CreatedOn": "2025-09-25T09:42:19.695Z"
    }
  },
  "freeform_tags": {},
  "system_tags": {
    "orcl-cloud": {
      "free-tier-retained": "false"
    }
  }
}
```

## 3. `list_jms_plugins`

Status: `ok`

Input:

```json
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq",
  "sort_order": "DESC",
  "sort_by": "timeLastSeen",
  "limit": 10
}
```

Output:

```json
[
  {
    "id": "ocid1.jmsplugin.oc1.iad.aaaaaaaasu4rloal4nryx2u4cqkukktit7d527infdokv4fmax3cqda6kqea",
    "agent_id": "ocid1.managementagent.oc1.iad.amaaaaaa6cijguia6q6c7ces7dz3tw7nf3unz5ofmhccxcpcp7lchjpccraq",
    "agent_type": "OMA",
    "lifecycle_state": "DELETED",
    "availability_status": "NOT_AVAILABLE",
    "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "hostname": "192.168.29.249",
    "os_family": "MACOS",
    "os_architecture": "x86_64",
    "os_distribution": "UNKNOWN",
    "plugin_version": "10.0.476",
    "time_registered": "2025-09-25T15:18:39.681000Z",
    "time_last_seen": null,
    "defined_tags": {},
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  },
  {
    "id": "ocid1.jmsplugin.oc1.iad.aaaaaaaaebraeu2tvhcqh6jlxh6hymw24wsk3acyl2t7l6p2kjdlhd4le3oa",
    "agent_id": "ocid1.managementagent.oc1.iad.amaaaaaa6cijguiaqdlpx5c77d5cdmpcjko6w7s453dydft7ht4ovv53jcea",
    "agent_type": "UNKNOWN_ENUM_VALUE",
    "lifecycle_state": "DELETED",
    "availability_status": "NOT_AVAILABLE",
    "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq",
    "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
    "hostname": "jms-k8s-cluster",
    "os_family": "LINUX",
    "os_architecture": "amd64",
    "os_distribution": "OL8",
    "plugin_version": "10.0.476.7",
    "time_registered": "2025-09-25T10:17:09.383000Z",
    "time_last_seen": null,
    "defined_tags": {},
    "freeform_tags": {},
    "system_tags": {
      "orcl-cloud": {
        "free-tier-retained": "false"
      }
    }
  }
]
```

## 4. `get_jms_plugin`

Status: `ok`

Input:

```json
{
  "jms_plugin_id": "ocid1.jmsplugin.oc1.iad.aaaaaaaasu4rloal4nryx2u4cqkukktit7d527infdokv4fmax3cqda6kqea"
}
```

Output:

```json
{
  "id": "ocid1.jmsplugin.oc1.iad.aaaaaaaasu4rloal4nryx2u4cqkukktit7d527infdokv4fmax3cqda6kqea",
  "agent_id": "ocid1.managementagent.oc1.iad.amaaaaaa6cijguia6q6c7ces7dz3tw7nf3unz5ofmhccxcpcp7lchjpccraq",
  "agent_type": "OMA",
  "lifecycle_state": "DELETED",
  "availability_status": "NOT_AVAILABLE",
  "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq",
  "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq",
  "hostname": "192.168.29.249",
  "os_family": "MACOS",
  "os_architecture": "x86_64",
  "os_distribution": "UNKNOWN",
  "plugin_version": "10.0.476",
  "time_registered": "2025-09-25T15:18:39.681000Z",
  "time_last_seen": null,
  "defined_tags": {},
  "freeform_tags": {},
  "system_tags": {
    "orcl-cloud": {
      "free-tier-retained": "false"
    }
  }
}
```

## 5. `list_installation_sites`

Status: `ok`

Input:

```json
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq",
  "limit": 10
}
```

Output:

```json
[]
```

## 6. `get_fleet_agent_configuration`

Status: `ok`

Input:

```json
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq"
}
```

Output:

```json
{
  "jre_scan_frequency_in_minutes": 1440,
  "java_usage_tracker_processing_frequency_in_minutes": 60,
  "work_request_validity_period_in_days": 14,
  "agent_polling_interval_in_minutes": 10,
  "is_collecting_managed_instance_metrics_enabled": true,
  "is_collecting_usernames_enabled": true,
  "is_capturing_ip_address_and_fqdn_enabled": null,
  "is_libraries_scan_enabled": null,
  "linux_configuration": {
    "include_paths": [
      "/usr/java",
      "/usr/lib/jvm",
      "/usr/lib64/graalvm",
      "/opt"
    ],
    "exclude_paths": []
  },
  "windows_configuration": {
    "include_paths": [
      "${ProgramFiles}\\Java",
      "${ProgramFiles(x86)}\\Java",
      "C:\\Oracle"
    ],
    "exclude_paths": []
  },
  "mac_os_configuration": {
    "include_paths": [
      "/Library/Java",
      "/Library/Internet Plug-Ins/",
      "/Library/Oracle"
    ],
    "exclude_paths": []
  },
  "time_last_modified": "2025-09-26T06:26:12.058000Z"
}
```

## 7. `get_fleet_advanced_feature_configuration`

Status: `ok`

Input:

```json
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq"
}
```

Output:

```json
{
  "analytic_namespace": "ideq4gu7gs6j",
  "analytic_bucket_name": "jms_ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq",
  "lcm": {
    "is_enabled": true,
    "post_installation_actions": null
  },
  "crypto_event_analysis": {
    "is_enabled": true,
    "summarized_events_log": {
      "log_group_id": "ocid1.loggroup.oc1.iad.amaaaaaa6cijguia2k7mytdyr4gmci4pklhmsm4ftb5uwecr3q2ep5jzfiuq",
      "log_id": "ocid1.log.oc1.iad.amaaaaaa6cijguia75rkcwb43ccw2ne6q32p44x26tav3d5ncnytdcr4zwva"
    }
  },
  "advanced_usage_tracking": {
    "is_enabled": true
  },
  "jfr_recording": {
    "is_enabled": true
  },
  "performance_tuning_analysis": {
    "is_enabled": true
  },
  "java_migration_analysis": {
    "is_enabled": true
  },
  "time_last_modified": "2025-09-26T06:14:05.652000Z"
}
```

## 8. `summarize_resource_inventory`

Status: `ok`

Input:

```json
{
  "compartment_id": "ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq"
}
```

Output:

```json
{
  "active_fleet_count": 0,
  "managed_instance_count": 0,
  "jre_count": 0,
  "installation_count": 0,
  "application_count": 0
}
```

## 9. `summarize_managed_instance_usage`

Status: `ok`

Input:

```json
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiafufahiluczeesffxgqqkwiz6odgjmzudesgosz2cn7uq",
  "limit": 10
}
```

Output:

```json
[]
```

