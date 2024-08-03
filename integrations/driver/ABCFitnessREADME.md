## Initial Setup 

### Clone this Repositroy

Refer to the GitHub documentation on [how to clone a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

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
   - Alternatively, you can install Docker using the provided [bash installation script](./install_docker.sh) 
- If you are going to run the driver using the provided Helm chart, you will also need:
   - A running [Kubernetes](https://kubernetes.io/docs/setup/) cluster such as [MicroK8s](https://microk8s.io/docs/getting-started)
   - [Helm](https://helm.sh/docs/intro/install/)
   - A docker image [registry/repository](https://docs.docker.com/guides/docker-concepts/the-basics/what-is-a-registry/)
   that your cluster can pull from
- Alternatively, you can run the driver directly as Python code. To do so you will need to:
   - Install the [apt requirements](./apt_requirements.txt)
   - Install the Python [requirements](./requirements.txt) using [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/#ensure-you-can-run-pip-from-the-command-line)

## Quick Install with Docker

If docker is already installed, you can use the provided quick install script, `abc_fitness_quick_install.sh`, to run
the Camio ABC Fitness driver. The quick install script:

1. Populates the config file with your credentials
2. Builds the docker image
3. Runs the driver using docker compose

First retrieve your credentials. You can generate a Camio API token on [this page](https://camio.com/settings/integrations).

You can retrieve your ABC Fitness API key and ID by signing in [here](https://abcfinancial.3scale.net/docs). You may
need to contact ABC.

Then, run from within this directory (`examples/integrations/driver`).

```
bash abc_fitness_quick_install.sh [APP_KEY] [APP_ID] [CLUB_ID] [CAMIO_API_TOKEN]
```

### Re-Run the Quick Install

If you need to re-run the quick install, first take down the running docker compose:

```
docker compose -f abc-fitness-docker-compose.yaml down
```

Then run the quick install script again. Note that only one backup config file will be kept.

## Create the Driver Image [Helm/Docker Setup]

### Build the Docker Image

Run from within this directory (`examples/integrations/driver`).

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

You can upload the `camio-integration-driver-abc-fitness` to a Docker image registry if desired. Some options for image
repositories are [Docker Hub](https://docs.docker.com/docker-hub/repos/create/) and cloud providers such as 
[Google Cloud](https://cloud.google.com/artifact-registry) or [AWS](https://aws.amazon.com/ecr/). Once you have a 
respository set up, you can push to that registry as follows:

```
docker tag camio-integration-driver-abc-fitness:latest $REPOSITORY_IMAGE_NAME:latest
docker push $REPOSITORY_IMAGE_NAME:latest
```

**NOTE**: If using Helm, it is recommended to push the docker image to a registry.

## Run the Driver Using Docker

### Fill out the Config File

Enter your values in the [production config file](./configs/production/abc_fitness_config.yaml). The `credentials` values
are all required in order for the driver to contact the ABC Fitness and Camio API.

You can generate a Camio API token on [this page](https://camio.com/settings/integrations).

You can retrieve your ABC Fitness API key and ID by signing in [here](https://abcfinancial.3scale.net/docs). You may
need to contact ABC.

### Start the Docker Container

Run the docker container using the [docker compose file](./abc-fitness-docker-compose.yaml). Make sure to change the 
docker image if you've uploaded your docker image to a non-local registry. Documentation on [docker compose up](https://docs.docker.com/reference/cli/docker/compose/up/).

Run this command from within this directory (`examples/integrations/driver`).

```
docker compose -f abc-fitness-docker-compose.yaml up -d
```

## Run the Driver Using Helm

### Ensure that Your Cluster Has Access to the Driver Image

If using a local docker image, you will need to make that docker image available to your kubernetes cluster. You may
be able to push the local image directly to your clusters available images. For example, here is how you do so using 
[MicroK8s](https://microk8s.io/docs/registry-images#working-with-locally-built-images-without-a-registry).

If you uploaded your image to a non-local docker image registry you will need to ensure that your cluster can pull
from that registry. If the registry is publicly available, then most likely you can just use the image in the install 
directions below with no problem. [MiroK8s documentation](https://microk8s.io/docs/registry-public) on using public 
registries. Using a private registry will depend on the registry and the type of kubernetes cluster.


### Create the Helm Chart

Create the Helm chart tgz file.

```
helm package helm/camio-abc-fitness
```

### Fill out the Values File

Enter your desired values in the [values file](./helm/abc_fitness_values.yaml). The `credentials` values
are all required in order for the driver to contact the ABC Fitness and Camio API. You can generate a Camio API token on 
[this page](https://camio.com/settings/integrations). You can retrieve your ABC Fitness API 
key and ID by signing in [here](https://abcfinancial.3scale.net/docs). You may need to contact ABC.

Make sure to change `container.image` to the image your cluster can access.

### Install the Helm Chart

Run this command from within this directory (`examples/integrations/driver`).

```
helm install camio-abc-fitness-driver helm/camio-abc-fitness-1.0.0.tgz -f helm/abc_fitness_values.yaml -n camio --create-namespace
```

## Run the Driver Using Python [Not Recommended]

Running the driver using python is a good method for testing your credentials but is not recommended for long term
deployment.

### Fill out the Config File

Enter your values in the [production config file](./configs/production/abc_fitness_config.yaml). The `credentials` values
are all required in order for the driver to contact the ABC Fitness and Camio API.

You can generate a Camio API token on [this page](https://camio.com/settings/integrations).

You can retrieve your ABC Fitness `app_key`, `app_id` and `club_id` by signing in [here](https://abcfinancial.3scale.net/docs). You may
need to contact ABC.

### Run the Driver

Run this command from within this directory (`examples/integrations/driver`).

```
python3 app/abc_fitness.py --config configs/production/abc_fitness_config.yaml
```

## Uninstall

Run these commands from within this directory (`examples/integrations/driver`).

### Docker

```
docker compose -f abc-fitness-docker-compose.yaml down
```

### Helm 

```
helm uninstall camio-abc-fitness-driver helm/camio-abc-fitness-1.0.0.tgz -f helm/abc_fitness_values.yaml -n camio
```

### Python

Control-C (Ctrl+C) to cancel the execution of the python file.