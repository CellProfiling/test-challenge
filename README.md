# test-challenge
Scripts to set up test challenge.

## Install

- Download the project.
```
git clone https://github.com/CellProfiling/test-challenge.git
cd test-challenge
```
- Installing the Python package will also install a script for scoring.
```
pip3 install .
```

## Run

- Run program and see help.
```
testchallenge --help
```
- Run program and score a submission that has provided a prediction csv file.
```
testchallenge example_solution.csv example_prediction.csv
```
- Run program and score a submission and save results to json.
```
testchallenge example_solution.csv example_prediction.csv -O results.json
```

## Docker

- Build the docker image.
```
docker build -t proteinatlas/test-challenge:latest .
```
- Run the docker container with default example solutions.
```
docker run --rm proteinatlas/test-challenge:latest
```
- Run the docker container with your own solution and prediction files located in a host directory called `solutions` in your home directory.
```
docker run --rm \
  -v ~/solutions:/app/solutions \
  proteinatlas/test-challenge:latest solutions/solution.csv solutions/prediction.csv
```
- Run the docker container with your own solutions and save to json.
```
docker run --rm \
  -v ~/solutions:/app/solutions \
  proteinatlas/test-challenge:latest solutions/solution.csv solutions/prediction.csv \
  -O solutions/results.json
```
