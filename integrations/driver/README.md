# Camio Integration Drivers

Camio Integration drivers continuously poll an external integration's API for information to forward into the Camio 
system. 

## Repo Structure

### app

Contains base and extended driver classes, schemas, utils. This is where to add the code for a new integration driver.

### configs

Contains configs used for testing and for production deployment.

### helm

Contains a directory for each integration's helm chart, templates, and default values.

## Running Tests

Each driver's `app/{{integration_name}}.py` file should contain unittests that extend the base class of unittests from 
`app/base.py`. The base class tests will fail but any specific integration's tests should pass given a test config 
file exists in `configs/test` which contains valid test credentials.

## Creating a New Integration Driver

1. Create a new file in `app` called `{{integration_name}}.py` that extends the base driver
2. Override all necessary methods from the base class
3. Add tests in `{{integration_name}}.py` that extend the base tests and override any necessary methods
4. Add a test config in `configs/test` for values to pass into the test driver when running your unittests
5. Build the docker image for the driver
6. Create a docker compose for the integration driver using the image created in the previous step
    - It is a good idea to test the docker compose before proceeding to make the helm chart. Run:
    `docker compose -f {{integration_name}}-docker-compose.yaml up`
7. Convert the docker compose to a helm chart (make sure the resulting directory goes into `helm/camio-{{integration_name}}`)
    - Ex: `kompose convert -c -o helm/camio-[INTEGRATION] -f [INTEGRATION]-docker-compose.yaml --volumes configMap --controller deployment`
8. Upload your helm chart to a repository if desired
9. Install your helm chart in a cluster
    - If using helm version `3.8+` run: `helm install camio-{{integration_name}} [CHART NAME/URL] --version VERSION [-n camio] [--create-namespace]`