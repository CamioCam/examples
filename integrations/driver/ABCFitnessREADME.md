## Initial Setup 

### How to Run the ABC Fitness Driver

There are 3 options for running the ABC Fitness driver:

1) Docker [Recommended]
   - Docker is recommended because it requires less set up but still provides the adavantages of containerization. Docker 
   will ensure that driver remains running and comes back online in case of unexpected errors or interruptions such as 
   restarts of the machine running the driver.
2) Helm
   - Recommended only for people who want to run the driver in an existing kubernetes cluster. Significantly more work 
   to set up than Docker. Provides similar resilience to errors and interruptions.
3) Python [Not Recommended]
   - The driver can be ran directly via Python. This is not recommended on its own since unexpected errors or 
   interruptions could halt the execution of the driver.

### Install Requirements

- If you are running the driver using Docker or Helm, you will need to install Docker
   - [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) - for command line use only
   - Or [Docker Desktop](https://docs.docker.com/get-docker/) - for an interactive desktop app as well as command line
   - Alternatively, you can install Docker using the provided [bash installation script](./install_docker.sh). **Note 
   that this script runs apt-get update and apt-get install**.
- If you are going to run the driver using the provided Helm chart, you will also need:
   - A running [Kubernetes](https://kubernetes.io/docs/setup/) cluster such as [MicroK8s](https://microk8s.io/docs/getting-started)
   - [Helm](https://helm.sh/docs/intro/install/)
- Alternatively, you can run the driver directly as Python code. To do so you will need to:
   - Install the [apt requirements](./apt_requirements.txt)
   - Install the Python [requirements](./requirements.txt) using [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/#ensure-you-can-run-pip-from-the-command-line)

## Quick Install with Docker

If docker is already installed, and you have cloned this repository, then you can use the provided quick install script, 
`abc_fitness_quick_install_docker.sh`, to run the Camio ABC Fitness driver. The quick install script:

1. Populates the config file with your credentials
2. Builds the docker image
3. Runs the driver using docker compose

First retrieve your credentials. You can generate a Camio API token on [this page](https://camio.com/settings/integrations).

You can retrieve your ABC Fitness API key and ID by signing in [here](https://abcfinancial.3scale.net/docs). You may
need to contact ABC.

Then, run from within this directory (`camio-integrations/driver`).

```
bash abc_fitness_quick_install_docker.sh [APP_KEY] [APP_ID] [CLUB_ID] [CAMIO_API_TOKEN]
```

**NOTE**: The quick install uses the `linux-amd64` driver image by default. If you would like to run the `linux-arm64` 
driver image instead, change the image in the [docker compose file](./abc-fitness-docker-compose.yaml) to 
`us-central1-docker.pkg.dev/camiologger/public-containers/camio-integration-driver-abc-fitness:latest-linux-arm64`.

### Re-Run the Quick Install

If you need to re-run the quick install, first take down the running docker compose:

```
docker compose -f abc-fitness-docker-compose.yaml down
```

Then run the quick install script again. Note that only one backup config file will be kept.

## Run the Driver using Docker (Non-Quick Install)

### Create a Config File

If you have not cloned this repository, copy or download the file [production config file](./configs/production/abc_fitness_config.yaml). 
Enter your values into the config file. The `credentials` values are all required in order for the driver to 
contact the ABC Fitness and Camio API.

You can retrieve your ABC Fitness credentials [here](https://abcfinancial.3scale.net/docs). You may
need to contact ABC.

#### Required config values:

| Field | Description | Default |
| --- | --- | --- |
| credentials.app_key | Your app key provided by ABC Fitness for calling the ABC Fitness API | None |
| credentials.app_id | Your app id provided by ABC Fitness for calling the ABC Fitness API | None | 
| credentials.club_id | The club id (number) provided by ABC Fitness for calling the ABC Fitness API | None |
| credentials.camio_api_token | A token for calling the Camio API, generated on [this page](https://camio.com/settings/integrations) | None |

#### Optional config values of note:

| Field | Description | Default |
| --- | --- | --- |
| log_level | The base level of logs that will be printed in the driver container. 10 (DEBUG), 20 (INFO), 30 (WARNING), 40 (ERR0R), 50 (CRITICAL) | 10 (INFO logs and up) |
| requests.events.polling_interval | How frequently to request the check in information from the ABC Fitness API. Defaults to every 12 hours. | 43200 (seconds) |
| requests.events.get_member_info | If true, makes a request to the ABC Fitness API to fetch the member information for each checkin event. Enables Camio to send tailgating notifications to members by retrieving the member email. | true |

### Start the Docker Container

Run the driver container using the [docker compose file](./abc-fitness-docker-compose.yaml). Documentation on 
[docker compose up](https://docs.docker.com/reference/cli/docker/compose/up/).

If you have not cloned this repository, copy or download the docker compose file. Make sure to change 
`./configs/production` in the docker compose file to the path of your config file from the previous step.

Run this command from the directory containing the docker compose.

```
docker compose -f abc-fitness-docker-compose.yaml up -d
```

**NOTE**: The docker compose uses the `linux-amd64` driver image by default. If you would like to run the `linux-arm64` 
driver image instead, change the image in the [docker compose](./abc-fitness-docker-compose.yaml) to 
`us-central1-docker.pkg.dev/camiologger/public-containers/camio-integration-driver-abc-fitness:latest-linux-arm64`.

## Run the Driver Using Helm

### Create a Values File

If you have not cloned this repository, copy or download the [values file](./helm/camio-abc-fitness/values.yaml). 
Enter your credentials into the values file.

The `credentials` values
are all required in order for the driver to contact the ABC Fitness and Camio APIs. You can generate a Camio API token on 
[this page](https://camio.com/settings/integrations). 

#### Required values:

| Field | Description | Default |
| --- | --- | --- |
| credentials.app_key | Your app key provided by ABC Fitness for calling the ABC Fitness API | None |
| credentials.app_id | Your app id provided by ABC Fitness for calling the ABC Fitness API | None | 
| credentials.club_id | The club id (number) provided by ABC Fitness for calling the ABC Fitness API | None |
| credentials.camio_api_token | A token for calling the Camio API, generated on [this page](https://camio.com/settings/integrations) | None |

#### Optional values of note:

| Field | Description | Default |
| --- | --- | --- |
| log_level | The base level of logs that will be printed in the driver container. 10 (DEBUG), 20 (INFO), 30 (WARNING), 40 (ERR0R), 50 (CRITICAL) | 10 (INFO logs and up) |
| requests.events.polling_interval | How frequently to request the check in information from the ABC Fitness API. Defaults to every 12 hours. | 43200 (seconds) |
| requests.events.get_member_info | If true, makes a request to the ABC Fitness API to fetch the member information for each checkin event. Enables Camio to send tailgating notifications to members by retrieving the member email. | true |
| container.image | The Camio ABC Fitness driver container image. Default to the amd-64 image. Can be changed to the arm64 image or to a custom image. | us-central1-docker.pkg.dev/camiologger/public-containers/camio-integration-driver-abc-fitness:latest-linux-amd64 |

### Install the Helm Chart

Run this command from the directory with your values.yaml file.

```
helm install camio-abc-fitness oci://us-central1-docker.pkg.dev/camiologger/helm/camio-abc-fitness --version 1.0.1 -f values.yaml -n camio --create-namespace
```

## Run the Driver Using Python [Not Recommended]

Running the driver using python is a good method for testing your credentials but is not recommended for long term
deployment.

### Fill out the Config File

Fill out the config file the same way as for the [docker deployment](#create-a-config-file).

### Run the Driver

```
python3 app/abc_fitness.py --config configs/production/abc_fitness_config.yaml
```

# Uninstall

### Docker

```
docker compose -f abc-fitness-docker-compose.yaml down
```

### Helm 

```
helm uninstall camio-abc-fitness-driver helm/camio-abc-fitness-1.0.0.tgz -f helm/camio-abc-fitness/values.yaml -n camio
```

### Python

Control-C (Ctrl+C) to cancel the execution of the python file.

# Custom Image Instructions

The following is instructions for building your own Camio ABC Fitness driver image. You may want to create a custom image 
if:
- You want to modify the driver code
- You want to changes to the driver dockerfile such as the base image etc.
- You need an image for a platform that is not provided
- You want the driver image uploaded to your own image registry

## Clone this Repository

Refer to the GitHub documentation on [how to clone a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

## Create the Docker Driver Image

### Build the Docker Image

Run from within this directory (`camio-integrations/driver`).

```
docker build -t camio-integration-driver-abc-fitness:latest -f abc-fitnessDockerfile .
```

#### Make sure that the image's platform matches the platform where you will be running the docker compose

If the platforms are different, [specify the platform](https://docs.docker.com/reference/cli/docker/buildx/build/#platform) 
to use in the build command. Here is an example specifying `linux/amd64`.

```
docker build -t camio-integration-driver-abc-fitness:latest --platform linux/amd64 -f abc-fitnessDockerfile .
```

### [Optional] Push the Docker Image to a Registry

You can upload the `camio-integration-driver-abc-fitness` image to a Docker image registry if desired. Some options for image
repositories are [Docker Hub](https://docs.docker.com/docker-hub/repos/create/) and cloud providers such as 
[Google Cloud](https://cloud.google.com/artifact-registry) or [AWS](https://aws.amazon.com/ecr/). Once you have a 
respository set up, you can push to that registry as follows:

```
docker tag camio-integration-driver-abc-fitness:latest $REPOSITORY_IMAGE_NAME:latest
docker push $REPOSITORY_IMAGE_NAME:latest
```

**NOTE**: If using Helm, it is recommended to push the docker image to a registry.

## Create a Helm Chart

Below are the instructions for creating/pushing a custom Camio ABC Fitness driver Helm chart. First you will need to have
either followed the custom docker image instructions above unless you want to use the provided docker images.

### Ensure that Your Cluster Has Access to the Driver Image

If you are using the provided docker images, there is nothing to do for this step.

If using a local docker image, you will need to make that docker image available to your kubernetes cluster. You may
be able to push the local image directly to your clusters available images. For example, here is how you do so using 
[MicroK8s](https://microk8s.io/docs/registry-images#working-with-locally-built-images-without-a-registry).

If you uploaded your docker image to a non-local docker image registry you will need to ensure that your cluster can pull
from that registry. If the registry is publicly available, then most likely you can just use the image in the install 
directions below with no problem. [MicroK8s documentation](https://microk8s.io/docs/registry-public) on using public 
registries. Using a private registry will depend on the registry and the type of kubernetes cluster.


### Create the Helm Chart

Once you've made any desired changes to the Chart files, create the Helm chart tgz file by running:

```
helm package helm/camio-abc-fitness
```

### [Optional] Upload the Helm Chart

Upload the Helm chart to a [repository](https://helm.sh/docs/topics/chart_repository/) if desired. Cloud providers such 
as GCP's [Artifact Registry](https://cloud.google.com/artifact-registry/docs/helm/manage-charts) can [host repositories](https://helm.sh/docs/topics/registries/#use-hosted-registries).