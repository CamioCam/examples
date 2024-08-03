# Helm Charts for PACS Drivers

This folder contains the files for managing the K8s Helm charts for the Camio incoming integration drivers.

# Helm Chart Components Information

## The chart directory (camio-INTEGRATION)

Contains all files required for the chart. Any files not required for packaging the chart should stay outside the directory.

### Chart.yaml

Contains the information on the chart once packaged, such as the name and version.

### values.yaml

Contains all DEFAULT configurations for the chart once packaged. 
These are the configurations that will be set when someone installs the chart from the repository without any modifications made. 
These values are applied to the various template files of the chart package through templating.

### templates

A folder containing the various YAML files for the different components of the K8s deployment to be built, 
and any other files to be templated such as the `NOTES.txt` file.

### NOTES.txt

Contains the text that will be displayed to the user on the command line upon installation of this chart. 
This file can be templated in the same way as the K8s resource YAMLs.

## Outside of the chart directory

### camio-INTEGRATION-modified-values.yaml

A values YAML you can use to modify the default values of the chart for installation testing. 
Feel free to create as many YAMLs for values testing as you desire.

# Working with the Helm Chart

## Pre-repository:

### Packaging:

```
helm package [CHART_PATH]
```

The chart path should point to the **directory** containing the **Chart.yaml** file.

This will create a `.tgz` packaged version of the chart, named like so:

```
[CHART_NAME]-[CHART_VERSION].tgz
```

Here's an example:

```
$ cd helm  # Always run commands from this directory

$ cat camio-INTEGRATION/Chart.yaml

name: camio-INTEGRATION
description: A helm chart for the Camio INTEGRATION driver
version: 1.9.0
apiVersion: v1

$ helm package camio-INTEGRATION

$ ls

/camio-INTEGRATION      camio-INTEGRATION-1.9.0.tgz     ...
```

### Testing / Debugging the templating:

```
helm template [CHART_PACKAGE] [FLAGS] [OPTIONS]
```

This command allows you to output the results of templating for the chart performed on installation. 

You can use the same flags and options you would use on a regular installation. 
Here's an example of applying a custom values file:

```
helm template [CHART_PACKAGE] -f modified-values.yaml
```

The output will contain the text of all files in /templates, so I would suggest directing the output to a file instead of the command line, like so:

```
helm template [CHART_PACKAGE] [FLAGS] [OPTIONS] > templating-results
```

This command generally has the same flags and options as the installation command. 

You can find more options by using the `--help`/`-h` flag or by looking at Helm's online documentation.

### Installation from local package

To install locally run the following command:

```
helm install [RELEASE_NAME] [CHART_PACKAGE] [FLAGS] [OPTIONS]
```

with the `RELEASE_NAME` being the name the deployment will appear as in Helm.

Simply apply custom values from a YAML file with the -f flag like so:

```
helm install [RELEASE_NAME] [CHART_PACKAGE] -f [CUSTOM_VALUES.yaml]
```

Or apply custom values through the command with the --set flag like so:

```
helm install [RELEASE_NAME] [CHART_PACKAGE] --set [KEY]=[VALUE],[KEY]=[VALUE],...
```

And install to a specific namespace with the -n flag like so:

```
helm install [RELEASE_NAME] [CHART_PACKAGE] -n [NAMESPACE]
```

You can find more options by using the `--help`/`-h` flag or by looking at Helm's online documentation.

### Pushing a chart to a repository:

Helm's documentation on [repositories](https://helm.sh/docs/topics/chart_repository/).

### Installing from the repository:

If necessary, add the repository:

```
helm repo add [REPO NAME] [REPO URL]
helm repo list
```

To install a chart from the repository, run the following command:

```
helm install [RELEASE_NAME] [CHART NAME/URL] --version [CHART_VERSION]
```

with the `RELEASE_NAME` being the name the deployment will appear as in Helm.

Simply apply custom values from a YAML file with the -f flag like so:

```
helm install [RELEASE_NAME] \
    [CHART NAME/URL] \
    --version [CHART_VERSION] \
    -f [CUSTOM_VALUES.yaml]
```

Or apply custom values through the command with the --set flag like so:

```
helm install [RELEASE_NAME] \
    [CHART NAME/URL] \
    --version [CHART_VERSION] \
    --set [KEY]=[VALUE],[KEY]=[VALUE],...
```

And install to a specific namespace with the -n flag like so:

```
helm install [RELEASE_NAME] \
    [CHART NAME/URL] \
    --version [CHART_VERSION] \
    -n [NAMESPACE]
```

You can find more options by using the `--help`/`-h` flag or by looking at Helm's online documentation.

