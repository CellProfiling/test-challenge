FROM python:3.6
WORKDIR /app
COPY . ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install .
ENTRYPOINT ["testchallenge"]
CMD ["example_solution.csv", "example_prediction.csv"]
