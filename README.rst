netconf-checker
===============

Ed Crewe June 2017

A tool to load, commit check and diff vendor router/switch configs


Features
--------

The tool provides a number of utility functions for checking bulk network device configurations.

The tool enables use of vendor specific configuration format for Juniper or Cisco
in time it should also allow the same features for more standard YANG files and deal with any of the formats yaml, json or xml that they can be written in.

Configurations can be loaded and commit checked against real devices, virtual networks or single device vendor OS VMs, eg. Juniper Olive or Cisco iOS.

Two sets of configurations can also be checked against each other, so providing a full data diff to confirm what configuration changes have occurred between two deployments of device configuration files.

This combination of features should cater for quickly confirming if a new set of configurations is Ok, and if it is no longer successfully committing to the devices,
what changes have occurred between it and the devices that may have caused it to fail.

If real devices connection details are provided then a diff can also be done between the config state of the running devices and the new configuration files.
So what are you actually going to be changing on a set of devices.

Clearly all these features are available by manually logging in to each device individually and commit checking or diffing the new configuration file, but this tool provides for a scenario
where you are deploying a whole topology to a set of devices, eg. maybe 20 or more devices in a leaf and spine topology etc.
You need to check the whole set of configurations is good, and manual approaches are too time consuming.

Disclaimers
-----------

This tool is not meant to be a substitute for any form of SDN or central configuration management tool approach to this problem.

With full SDN the local configuration data is no longer relevant, since the Control Plane is centrally managed.

With a central config management tool the desired config and actual device state config are both held in a central data store that can conform network state to desired config
in an automated manner. So diffs of the two, checking of commit validation etc. are already embedded in the automation system.

So this tool is purely for aiding a more manual push management of configuration approach. 
